from typing import Any

import typesense

from app.config import Settings
from app.models import ENRICHED_FIELDS_KEY, MetadataDocument, MetadataDocumentUpdate


class DocumentNotFound(Exception):
    """Le document demandé n'existe pas dans la collection."""


class DocumentAlreadyExists(Exception):
    """Un document porte déjà cet identifiant."""


class TypesenseService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = typesense.Client(
            {
                "nodes": [
                    {
                        "host": settings.typesense_host,
                        "port": settings.typesense_port,
                        "protocol": settings.typesense_protocol,
                    }
                ],
                "api_key": settings.typesense_api_key,
                "connection_timeout_seconds": 5,
            }
        )

    @property
    def documents(self):
        return self.client.collections[self.settings.typesense_collection].documents

    def ensure_collection(self) -> dict[str, Any]:
        schema = {
            "name": self.settings.typesense_collection,
            "fields": [
                {"name": "title", "type": "string"},
                {"name": "description", "type": "string", "optional": True},
                {"name": "content", "type": "string", "optional": True},
                {"name": "source_type", "type": "string", "facet": True},
                {"name": "source_name", "type": "string", "facet": True},
                {"name": "source_path", "type": "string", "optional": True},
                {"name": "enriched_fields", "type": "string[]", "optional": True},
                {"name": "format", "type": "string", "facet": True},
                {"name": "language", "type": "string", "facet": True, "optional": True},
                {"name": "tags", "type": "string[]", "facet": True, "optional": True},
                {"name": "updated_at", "type": "int64", "optional": True},
            ],
            "default_sorting_field": "updated_at",
        }
        try:
            return self.client.collections[schema["name"]].retrieve()
        except typesense.exceptions.ObjectNotFound:
            return self.client.collections.create(schema)

    def search(self, query: str, page: int = 1, per_page: int = 20) -> dict[str, Any]:
        self.ensure_collection()
        return self.documents.search(
            {
                "q": query or "*",
                "query_by": "title,description,content,tags,source_name",
                "facet_by": "source_type,source_name,format,language,tags",
                "page": page,
                "per_page": per_page,
            }
        )

    def get(self, document_id: str) -> dict[str, Any]:
        self.ensure_collection()
        try:
            return self.documents[document_id].retrieve()
        except typesense.exceptions.ObjectNotFound as error:
            raise DocumentNotFound(document_id) from error

    def create(self, document: MetadataDocument) -> dict[str, Any]:
        self.ensure_collection()
        try:
            return self.documents.create(_to_payload(document))
        except typesense.exceptions.ObjectAlreadyExists as error:
            raise DocumentAlreadyExists(document.id) from error

    def update(self, document_id: str, changes: MetadataDocumentUpdate) -> dict[str, Any]:
        """Applique une mise \u00e0 jour partielle et marque les champs touch\u00e9s comme enrichis."""
        existing = self.get(document_id)
        payload = _to_partial_payload(changes)
        payload[ENRICHED_FIELDS_KEY] = _mark_enriched(existing, payload)
        try:
            return self.documents[document_id].update(payload)
        except typesense.exceptions.ObjectNotFound as error:
            raise DocumentNotFound(document_id) from error

    def delete(self, document_id: str) -> dict[str, Any]:
        self.ensure_collection()
        try:
            return self.documents[document_id].delete()
        except typesense.exceptions.ObjectNotFound as error:
            raise DocumentNotFound(document_id) from error

    def replace(self, document: MetadataDocument) -> dict[str, Any]:
        """Remplace un document depuis l'API : les champs fournis deviennent enrichis."""
        self.ensure_collection()
        payload = _to_payload(document)
        existing = self._get_or_none(document.id) or {}
        provided = {field: None for field in document.model_fields_set}
        payload[ENRICHED_FIELDS_KEY] = _mark_enriched(existing, provided)
        return self.documents.upsert(payload)

    def index(self, document: MetadataDocument) -> dict[str, Any]:
        """\u00c9crit un document issu d'un connecteur sans \u00e9craser les enrichissements.

        Les champs list\u00e9s dans ``enriched_fields`` ont \u00e9t\u00e9 \u00e9crits via l'API : ils
        appartiennent \u00e0 l'utilisateur et sont report\u00e9s tels quels. Tout le reste est
        r\u00e9\u00e9crit depuis la source, qui en reste propri\u00e9taire.
        """
        self.ensure_collection()
        payload = _to_payload(document)
        existing = self._get_or_none(document.id)
        if existing is not None:
            enriched = _enriched_fields(existing)
            for field in enriched:
                if field in existing:
                    payload[field] = existing[field]
            payload[ENRICHED_FIELDS_KEY] = enriched
        else:
            payload.pop(ENRICHED_FIELDS_KEY, None)
        return self.documents.upsert(payload)

    def _get_or_none(self, document_id: str) -> dict[str, Any] | None:
        try:
            return self.get(document_id)
        except DocumentNotFound:
            return None


def _enriched_fields(document: dict[str, Any]) -> list[str]:
    return list(document.get(ENRICHED_FIELDS_KEY) or [])


def _mark_enriched(existing: dict[str, Any], written: dict[str, Any]) -> list[str]:
    """Ajoute les champs \u00e9crits via l'API \u00e0 ceux d\u00e9j\u00e0 marqu\u00e9s comme enrichis."""
    touched = set(written) - {"id", ENRICHED_FIELDS_KEY}
    return sorted(set(_enriched_fields(existing)) | touched)


def _to_payload(document: MetadataDocument) -> dict[str, Any]:
    payload = document.model_dump(mode="json", exclude_none=True)
    if document.updated_at:
        payload["updated_at"] = int(document.updated_at.timestamp())
    return payload


def _to_partial_payload(changes: MetadataDocumentUpdate) -> dict[str, Any]:
    payload = changes.model_dump(mode="json", exclude_unset=True)
    payload.pop("id", None)
    if changes.updated_at is not None:
        payload["updated_at"] = int(changes.updated_at.timestamp())
    else:
        payload.pop("updated_at", None)
    return payload

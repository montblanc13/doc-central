from typing import Any

import typesense

from app.config import Settings
from app.models import MetadataDocument, MetadataDocumentUpdate


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
        self.ensure_collection()
        try:
            return self.documents[document_id].update(_to_partial_payload(changes))
        except typesense.exceptions.ObjectNotFound as error:
            raise DocumentNotFound(document_id) from error

    def delete(self, document_id: str) -> dict[str, Any]:
        self.ensure_collection()
        try:
            return self.documents[document_id].delete()
        except typesense.exceptions.ObjectNotFound as error:
            raise DocumentNotFound(document_id) from error

    def upsert(self, document: MetadataDocument) -> dict[str, Any]:
        self.ensure_collection()
        return self.documents.upsert(_to_payload(document))


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

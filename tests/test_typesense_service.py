"""Vérifie les appels envoyés à Typesense (verbe, endpoint, corps) sans serveur réel."""

from datetime import UTC, datetime

import pytest
import typesense

from app.config import Settings
from app.connectors.base import document_id
from app.models import MetadataDocument, MetadataDocumentUpdate
from app.services import DocumentAlreadyExists, DocumentNotFound, TypesenseService

DOC_ID = document_id("local-files", "notes.md")
COLLECTION = "/collections/documents"
DOCUMENTS = f"{COLLECTION}/documents"


class RecordingApiCall:
    """Remplace la couche HTTP du client Typesense et journalise les appels."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.bodies: dict[str, dict] = {}
        self.responses: dict[str, dict] = {}
        self.errors: dict[str, Exception] = {}

    def _record(self, verb: str, endpoint: str, body: dict | None = None) -> dict:
        key = f"{verb} {endpoint}"
        self.calls.append((verb, endpoint))
        if body is not None:
            self.bodies[key] = body
        error = self.errors.get(key)
        if error is not None:
            raise error
        return self.responses.get(key, {"endpoint": endpoint})

    def get(self, endpoint, *args, **kwargs):
        return self._record("GET", endpoint)

    def post(self, endpoint, *args, **kwargs):
        return self._record("POST", endpoint, kwargs.get("body"))

    def patch(self, endpoint, *args, **kwargs):
        return self._record("PATCH", endpoint, kwargs.get("body"))

    def delete(self, endpoint, *args, **kwargs):
        return self._record("DELETE", endpoint)


@pytest.fixture
def api_call() -> RecordingApiCall:
    return RecordingApiCall()


@pytest.fixture
def service(api_call: RecordingApiCall) -> TypesenseService:
    service = TypesenseService(Settings(typesense_collection="documents"))
    # Collections et Documents capturent l'ApiCall à la construction : on remplace
    # ses méthodes sur place plutôt que l'objet lui-même.
    real_api_call = service.client.api_call
    for verb in ("get", "post", "patch", "delete"):
        setattr(real_api_call, verb, getattr(api_call, verb))
    return service


@pytest.fixture
def document() -> MetadataDocument:
    return MetadataDocument(id=DOC_ID, title="Notes")


def _existing(api_call: RecordingApiCall, **fields) -> None:
    """Simule un document déjà présent dans la collection."""
    api_call.responses[f"GET {DOCUMENTS}/{DOC_ID}"] = {"id": DOC_ID, **fields}


def _absent(api_call: RecordingApiCall) -> None:
    api_call.errors[f"GET {DOCUMENTS}/{DOC_ID}"] = typesense.exceptions.ObjectNotFound()


# --- endpoints ----------------------------------------------------------------


def test_create_posts_to_documents_endpoint(service, api_call, document):
    service.create(document)
    assert ("POST", f"{DOCUMENTS}/") in api_call.calls


def test_create_translates_conflict(service, api_call, document):
    api_call.errors[f"POST {DOCUMENTS}/"] = typesense.exceptions.ObjectAlreadyExists()
    with pytest.raises(DocumentAlreadyExists):
        service.create(document)


def test_update_patches_the_document_endpoint(service, api_call):
    _existing(api_call)
    service.update(DOC_ID, MetadataDocumentUpdate(title="Notes v2"))
    assert ("PATCH", f"{DOCUMENTS}/{DOC_ID}") in api_call.calls


def test_update_translates_missing_document(service, api_call):
    _absent(api_call)
    with pytest.raises(DocumentNotFound):
        service.update(DOC_ID, MetadataDocumentUpdate(title="Notes v2"))


def test_delete_calls_the_document_endpoint(service, api_call):
    service.delete(DOC_ID)
    assert ("DELETE", f"{DOCUMENTS}/{DOC_ID}") in api_call.calls


def test_delete_translates_missing_document(service, api_call):
    api_call.errors[f"DELETE {DOCUMENTS}/{DOC_ID}"] = typesense.exceptions.ObjectNotFound()
    with pytest.raises(DocumentNotFound):
        service.delete(DOC_ID)


def test_get_translates_missing_document(service, api_call):
    _absent(api_call)
    with pytest.raises(DocumentNotFound):
        service.get(DOC_ID)


# --- fusion des enrichissements -----------------------------------------------


def test_update_marks_touched_fields_as_enriched(service, api_call):
    _existing(api_call)
    service.update(DOC_ID, MetadataDocumentUpdate(description="À la main", tags=["perso"]))
    body = api_call.bodies[f"PATCH {DOCUMENTS}/{DOC_ID}"]
    assert body["enriched_fields"] == ["description", "tags"]


def test_update_accumulates_enriched_fields(service, api_call):
    _existing(api_call, enriched_fields=["tags"])
    service.update(DOC_ID, MetadataDocumentUpdate(description="À la main"))
    body = api_call.bodies[f"PATCH {DOCUMENTS}/{DOC_ID}"]
    assert body["enriched_fields"] == ["description", "tags"]


def test_index_preserves_enriched_fields(service, api_call):
    """Le cas qui motive la fusion : ré-indexer ne doit pas perdre une édition."""
    _existing(api_call, description="À la main", tags=["perso"], enriched_fields=["description"])
    service.index(MetadataDocument(id=DOC_ID, title="Notes", description="", tags=[]))
    body = api_call.bodies[f"POST {DOCUMENTS}/"]
    assert body["description"] == "À la main"
    assert body["enriched_fields"] == ["description"]


def test_index_overwrites_fields_owned_by_the_source(service, api_call):
    _existing(api_call, title="Ancien titre", enriched_fields=["description"])
    service.index(MetadataDocument(id=DOC_ID, title="Nouveau titre"))
    assert api_call.bodies[f"POST {DOCUMENTS}/"]["title"] == "Nouveau titre"


def test_index_of_an_unknown_document_carries_no_marker(service, api_call, document):
    _absent(api_call)
    service.index(document)
    assert "enriched_fields" not in api_call.bodies[f"POST {DOCUMENTS}/"]


def test_index_ignores_a_marker_sent_by_a_connector(service, api_call):
    """enriched_fields est un champ système : seul le service le décide."""
    _absent(api_call)
    service.index(MetadataDocument(id=DOC_ID, title="Notes", enriched_fields=["title"]))
    assert "enriched_fields" not in api_call.bodies[f"POST {DOCUMENTS}/"]


def test_replace_marks_the_provided_fields(service, api_call):
    _existing(api_call)
    service.replace(MetadataDocument(id=DOC_ID, title="Notes", description="À la main"))
    body = api_call.bodies[f"POST {DOCUMENTS}/"]
    assert body["enriched_fields"] == ["description", "title"]


# --- conversion des charges utiles --------------------------------------------


def test_payload_converts_updated_at_to_timestamp():
    from app.services.typesense import _to_partial_payload, _to_payload

    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    payload = _to_payload(MetadataDocument(id=DOC_ID, title="Notes", updated_at=moment))
    assert payload["updated_at"] == int(moment.timestamp())

    partial = _to_partial_payload(MetadataDocumentUpdate(updated_at=moment))
    assert partial == {"updated_at": int(moment.timestamp())}


def test_partial_payload_keeps_only_provided_fields():
    from app.services.typesense import _to_partial_payload

    assert _to_partial_payload(MetadataDocumentUpdate(title="Notes v2")) == {"title": "Notes v2"}
    assert _to_partial_payload(MetadataDocumentUpdate()) == {}

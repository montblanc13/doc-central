"""Vérifie que le service appelle bien Typesense (verbe + endpoint) sans serveur réel."""

from datetime import UTC, datetime

import pytest
import typesense

from app.config import Settings
from app.models import MetadataDocument, MetadataDocumentUpdate
from app.services import DocumentAlreadyExists, DocumentNotFound, TypesenseService

DOC_ID = "local-files:/data/notes.md"


class RecordingApiCall:
    """Remplace la couche HTTP du client Typesense et journalise les appels."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.errors: dict[str, Exception] = {}

    def _record(self, verb: str, endpoint: str, **_kwargs) -> dict:
        self.calls.append((verb, endpoint))
        error = self.errors.get(f"{verb} {endpoint}")
        if error is not None:
            raise error
        return {"endpoint": endpoint}

    def get(self, endpoint, *args, **kwargs):
        return self._record("GET", endpoint, **kwargs)

    def post(self, endpoint, *args, **kwargs):
        return self._record("POST", endpoint, body=kwargs.get("body"))

    def patch(self, endpoint, *args, **kwargs):
        return self._record("PATCH", endpoint, body=kwargs.get("body"))

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


def test_create_posts_to_documents_endpoint(service, api_call, document):
    service.create(document)
    assert ("POST", "/collections/documents/documents/") in api_call.calls


def test_create_translates_conflict(service, api_call, document):
    api_call.errors["POST /collections/documents/documents/"] = (
        typesense.exceptions.ObjectAlreadyExists()
    )
    with pytest.raises(DocumentAlreadyExists):
        service.create(document)


def test_update_patches_the_document_endpoint(service, api_call):
    service.update(DOC_ID, MetadataDocumentUpdate(title="Notes v2"))
    assert ("PATCH", f"/collections/documents/documents/{DOC_ID}") in api_call.calls


def test_update_translates_missing_document(service, api_call):
    api_call.errors[f"PATCH /collections/documents/documents/{DOC_ID}"] = (
        typesense.exceptions.ObjectNotFound()
    )
    with pytest.raises(DocumentNotFound):
        service.update(DOC_ID, MetadataDocumentUpdate(title="Notes v2"))


def test_delete_calls_the_document_endpoint(service, api_call):
    service.delete(DOC_ID)
    assert ("DELETE", f"/collections/documents/documents/{DOC_ID}") in api_call.calls


def test_delete_translates_missing_document(service, api_call):
    api_call.errors[f"DELETE /collections/documents/documents/{DOC_ID}"] = (
        typesense.exceptions.ObjectNotFound()
    )
    with pytest.raises(DocumentNotFound):
        service.delete(DOC_ID)


def test_get_translates_missing_document(service, api_call):
    api_call.errors[f"GET /collections/documents/documents/{DOC_ID}"] = (
        typesense.exceptions.ObjectNotFound()
    )
    with pytest.raises(DocumentNotFound):
        service.get(DOC_ID)


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

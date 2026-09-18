import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_typesense
from app.main import app
from app.services import DocumentAlreadyExists, DocumentNotFound


class FakeTypesenseService:
    """Remplace Typesense en mémoire pour tester la couche API."""

    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    def search(self, query: str, page: int = 1, per_page: int = 20) -> dict:
        return {"found": len(self.store), "hits": [{"document": d} for d in self.store.values()]}

    def get(self, document_id: str) -> dict:
        if document_id not in self.store:
            raise DocumentNotFound(document_id)
        return self.store[document_id]

    def create(self, document) -> dict:
        if document.id in self.store:
            raise DocumentAlreadyExists(document.id)
        payload = document.model_dump(mode="json", exclude_none=True)
        self.store[document.id] = payload
        return payload

    def update(self, document_id: str, changes) -> dict:
        if document_id not in self.store:
            raise DocumentNotFound(document_id)
        written = changes.model_dump(mode="json", exclude_unset=True)
        document = self.store[document_id]
        document.update(written)
        document["enriched_fields"] = sorted(
            set(document.get("enriched_fields") or []) | set(written)
        )
        return document

    def delete(self, document_id: str) -> dict:
        if document_id not in self.store:
            raise DocumentNotFound(document_id)
        return self.store.pop(document_id)

    def replace(self, document) -> dict:
        payload = document.model_dump(mode="json", exclude_none=True)
        existing = self.store.get(document.id, {})
        payload["enriched_fields"] = sorted(
            set(existing.get("enriched_fields") or []) | (document.model_fields_set - {"id"})
        )
        self.store[document.id] = payload
        return payload

    def index(self, document) -> dict:
        payload = document.model_dump(mode="json", exclude_none=True)
        existing = self.store.get(document.id)
        if existing is None:
            payload.pop("enriched_fields", None)
        else:
            enriched = existing.get("enriched_fields") or []
            payload.update({f: existing[f] for f in enriched if f in existing})
            payload["enriched_fields"] = enriched
        self.store[document.id] = payload
        return payload


@pytest.fixture
def service() -> FakeTypesenseService:
    return FakeTypesenseService()


@pytest.fixture
def client(service: FakeTypesenseService):
    app.dependency_overrides[get_typesense] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

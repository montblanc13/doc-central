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
        self.store[document_id].update(changes.model_dump(mode="json", exclude_unset=True))
        return self.store[document_id]

    def delete(self, document_id: str) -> dict:
        if document_id not in self.store:
            raise DocumentNotFound(document_id)
        return self.store.pop(document_id)

    def upsert(self, document) -> dict:
        payload = document.model_dump(mode="json", exclude_none=True)
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

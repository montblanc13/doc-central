import pytest

DOC_ID = "local-files:/data/notes.md"


@pytest.fixture
def payload() -> dict:
    return {
        "id": DOC_ID,
        "title": "Notes",
        "description": "Notes de réunion",
        "source_type": "local",
        "source_name": "local-files",
        "format": "markdown",
    }


def test_create_document(client, payload):
    response = client.post("/api/documents", json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == "Notes"


def test_create_duplicate_returns_409(client, payload):
    client.post("/api/documents", json=payload)
    response = client.post("/api/documents", json=payload)
    assert response.status_code == 409


def test_create_rejects_empty_title(client, payload):
    response = client.post("/api/documents", json={**payload, "title": ""})
    assert response.status_code == 422


def test_read_document(client, payload):
    client.post("/api/documents", json=payload)
    response = client.get(f"/api/documents/{DOC_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == DOC_ID


def test_read_missing_document_returns_404(client):
    assert client.get("/api/documents/absent").status_code == 404


def test_patch_updates_only_provided_fields(client, payload):
    client.post("/api/documents", json=payload)
    response = client.patch(f"/api/documents/{DOC_ID}", json={"title": "Notes v2"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Notes v2"
    assert body["description"] == "Notes de réunion"


def test_patch_without_field_returns_400(client, payload):
    client.post("/api/documents", json=payload)
    response = client.patch(f"/api/documents/{DOC_ID}", json={})
    assert response.status_code == 400


def test_patch_missing_document_returns_404(client):
    assert client.patch("/api/documents/absent", json={"title": "x"}).status_code == 404


def test_put_replaces_document(client, payload, service):
    client.post("/api/documents", json=payload)
    response = client.put(f"/api/documents/{DOC_ID}", json={**payload, "description": ""})
    assert response.status_code == 200
    assert service.store[DOC_ID]["description"] == ""


def test_put_rejects_id_mismatch(client, payload):
    response = client.put(f"/api/documents/{DOC_ID}", json={**payload, "id": "autre"})
    assert response.status_code == 400


def test_delete_document(client, payload, service):
    client.post("/api/documents", json=payload)
    response = client.delete(f"/api/documents/{DOC_ID}")
    assert response.status_code == 204
    assert DOC_ID not in service.store


def test_delete_missing_document_returns_404(client):
    assert client.delete("/api/documents/absent").status_code == 404

from app.config import Settings
from app.connectors.google_drive import GoogleDriveConnector


class FakeRequest:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeFiles:
    def __init__(self):
        self.list_calls = []
        self.exports = {}

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        if len(self.list_calls) == 1:
            return FakeRequest(
                {
                    "files": [
                        {
                            "id": "doc-1",
                            "name": "Compte rendu",
                            "mimeType": "application/vnd.google-apps.document",
                            "createdTime": "2026-09-19T10:00:00Z",
                            "modifiedTime": "2026-09-20T10:00:00Z",
                            "webViewLink": "https://drive.google.com/file/d/doc-1/view",
                        }
                    ],
                    "nextPageToken": "page-2",
                }
            )
        return FakeRequest({"files": [{"id": "sheet-1", "name": "Budget.csv", "mimeType": "text/csv"}]})

    def export(self, *, fileId, mimeType):
        return FakeRequest(self.exports[(fileId, mimeType)])


class FakeService:
    def __init__(self):
        self.files_resource = FakeFiles()
        self.files_resource.exports["doc-1", "text/plain"] = b"Bonjour Drive"

    def files(self):
        return self.files_resource


class FakeAIService:
    def summarize(self, *, title, description, content):
        return f"Résumé de {title}"


def test_authenticate_reuses_an_injected_service():
    service = FakeService()
    GoogleDriveConnector(Settings(), service=service).authenticate()


def test_extracts_pages_and_exports_google_documents():
    service = FakeService()
    settings = Settings(google_drive_folder_id="folder-1")
    documents = list(
        GoogleDriveConnector(settings, service=service, ai_service=FakeAIService()).extract()
    )

    assert [document.id for document in documents] == ["google-drive:doc-1", "google-drive:sheet-1"]
    assert documents[0].content == "Bonjour Drive"
    assert documents[0].format == "google-doc"
    assert documents[0].summary == "Résumé de Compte rendu"
    assert documents[0].source_uri == "https://drive.google.com/file/d/doc-1/view"
    assert service.files_resource.list_calls[0]["q"] == "trashed = false and 'folder-1' in parents"
    assert service.files_resource.list_calls[1]["pageToken"] == "page-2"


def test_keeps_drive_metadata_for_files_without_export_support():
    service = FakeService()
    settings = Settings(google_drive_folder_id="folder-1")
    document = list(GoogleDriveConnector(settings, service=service).extract())[1]
    assert document.metadata["drive_file_id"] == "sheet-1"
    assert document.content == ""

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from googleapiclient.errors import HttpError

from app.config import Settings
from app.connectors.base import document_id
from app.models import MetadataDocument
from app.services.ai import AIService

LOGGER = logging.getLogger(__name__)

GOOGLE_DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
GOOGLE_MIME_TYPES = {
    "application/vnd.google-apps.document": ("text/plain", "google-doc"),
    "application/vnd.google-apps.spreadsheet": ("text/csv", "google-sheet"),
    "application/vnd.google-apps.presentation": ("text/plain", "google-slide"),
}
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class GoogleDriveConnector:
    """Extrait les fichiers visibles par un compte Google Drive authentifié."""

    def __init__(
        self,
        settings: Settings,
        service: Any | None = None,
        ai_service: AIService | None = None,
    ) -> None:
        self.settings = settings
        self._service = service
        self.ai_service = ai_service

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = self._build_service()
        return self._service

    def authenticate(self) -> None:
        """Crée ou rafraîchit le jeton OAuth sans parcourir ni indexer Drive."""
        if self._service is None:
            self._service = self._build_service()

    def extract(self) -> Iterator[MetadataDocument]:
        page_token: str | None = None
        query = "trashed = false"
        folder_id = (self.settings.google_drive_folder_id or "").strip()
        if folder_id:
            folder_id = folder_id.replace("'", "\\'")
            query += f" and '{folder_id}' in parents"

        while True:
            response = (
                self.service.files()
                .list(
                    q=query,
                    spaces="drive",
                    pageSize=self.settings.google_drive_page_size,
                    pageToken=page_token,
                    orderBy="modifiedTime desc",
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields=(
                        "nextPageToken,files("
                        "id,name,mimeType,description,createdTime,modifiedTime,"
                        "webViewLink,parents,size,md5Checksum)"
                    ),
                )
                .execute()
            )
            for item in response.get("files", []):
                yield self._to_document(item)

            page_token = response.get("nextPageToken")
            if not page_token:
                return

    def _to_document(self, item: dict[str, Any]) -> MetadataDocument:
        file_id = item["id"]
        mime_type = item.get("mimeType", "application/octet-stream")
        content = self._content(item)
        name = item.get("name") or file_id
        description = item.get("description") or ""
        summary = ""
        if self.ai_service is not None and (content.strip() or description.strip()):
            summary = self.ai_service.summarize(
                title=name,
                description=description,
                content=content,
            )
        source_name = self.settings.google_drive_source_name
        return MetadataDocument(
            id=document_id(source_name, file_id),
            title=name,
            description=description,
            summary=summary,
            content=content,
            source_type="google-drive",
            source_name=source_name,
            source_uri=item.get("webViewLink") or f"https://drive.google.com/open?id={file_id}",
            format=self._format(item),
            access="authenticated",
            created_at=_parse_datetime(item.get("createdTime")),
            updated_at=_parse_datetime(item.get("modifiedTime")),
            metadata={
                "drive_file_id": file_id,
                "mime_type": mime_type,
                "parents": item.get("parents", []),
                "size_bytes": _int_or_none(item.get("size")),
                "md5_checksum": item.get("md5Checksum"),
            },
        )

    def _content(self, item: dict[str, Any]) -> str:
        mime_type = item.get("mimeType")
        export = GOOGLE_MIME_TYPES.get(mime_type)
        if not export:
            return ""
        export_mime_type, _ = export
        try:
            payload = self.service.files().export(
                fileId=item["id"], mimeType=export_mime_type
            ).execute()
        except HttpError as error:  # Google can reject exports by size or permission.
            LOGGER.warning("Impossible d'exporter le fichier Drive %s: %s", item["id"], error)
            return ""
        if isinstance(payload, bytes):
            return payload.decode("utf-8", errors="replace")
        return str(payload)

    @staticmethod
    def _format(item: dict[str, Any]) -> str:
        mime_type = item.get("mimeType")
        if mime_type == FOLDER_MIME_TYPE:
            return "folder"
        if mime_type in GOOGLE_MIME_TYPES:
            return GOOGLE_MIME_TYPES[mime_type][1]
        suffix = Path(item.get("name", "")).suffix.removeprefix(".").lower()
        return suffix or "unknown"

    def _build_service(self) -> Any:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        credentials_path = Path(self.settings.google_drive_credentials_file)
        token_path = Path(self.settings.google_drive_token_file)
        credentials = None
        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(token_path), [GOOGLE_DRIVE_READONLY_SCOPE]
            )
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Fichier OAuth Google Drive introuvable: {credentials_path}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), [GOOGLE_DRIVE_READONLY_SCOPE]
            )
            credentials = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(credentials.to_json(), encoding="utf-8")
        return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _int_or_none(value: str | None) -> int | None:
    return int(value) if value is not None else None

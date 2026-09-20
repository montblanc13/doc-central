from typing import Any, Literal

import typesense

from app.config import Settings
from app.models import MetadataDocument

SortField = Literal["title", "updated_at", "source_name", "format"]
SortOrder = Literal["asc", "desc"]


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

    def ensure_collection(self) -> dict[str, Any]:
        schema = {
            "name": self.settings.typesense_collection,
            "fields": [
                {"name": "title", "type": "string"},
                {"name": "description", "type": "string", "optional": True},
                {"name": "summary", "type": "string", "optional": True},
                {"name": "content", "type": "string", "optional": True},
                {"name": "source_type", "type": "string", "facet": True},
                {"name": "source_name", "type": "string", "facet": True},
                {"name": "format", "type": "string", "facet": True},
                {"name": "language", "type": "string", "facet": True, "optional": True},
                {"name": "tags", "type": "string[]", "facet": True, "optional": True},
                {"name": "updated_at", "type": "int64", "optional": True},
            ],
        }
        try:
            collection = self.client.collections[schema["name"]]
            existing = collection.retrieve()
            fields = existing.get("fields", [])
            if not any(field.get("name") == "summary" for field in fields):
                collection.update(
                    {"fields": [{"name": "summary", "type": "string", "optional": True}]}
                )
            return existing
        except typesense.exceptions.ObjectNotFound:
            return self.client.collections.create(schema)

    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        format_filter: str | None = None,
        sort_by: SortField | None = None,
        sort_order: SortOrder = "asc",
    ) -> dict[str, Any]:
        self.ensure_collection()
        parameters: dict[str, Any] = {
            "q": query or "*",
            "query_by": "title,description,summary,content,tags,source_name",
            "facet_by": "source_type,source_name,format,language,tags",
            "page": page,
            "per_page": per_page,
        }
        if format_filter:
            parameters["filter_by"] = f"format:={self._quote_filter_value(format_filter)}"
        if sort_by:
            parameters["sort_by"] = f"{sort_by}:{sort_order}"

        return self.client.collections[self.settings.typesense_collection].documents.search(
            parameters
        )

    @staticmethod
    def _quote_filter_value(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("`", "\\`")
        return f"`{escaped}`"

    def upsert(self, document: MetadataDocument) -> dict[str, Any]:
        self.ensure_collection()
        payload = document.model_dump(mode="json", exclude_none=True)
        if document.updated_at:
            payload["updated_at"] = int(document.updated_at.timestamp())
        return self.client.collections[self.settings.typesense_collection].documents.upsert(payload)

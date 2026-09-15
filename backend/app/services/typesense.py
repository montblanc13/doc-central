from typing import Any

import typesense

from app.config import Settings
from app.models import MetadataDocument


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
        return self.client.collections[self.settings.typesense_collection].documents.search(
            {
                "q": query or "*",
                "query_by": "title,description,content,tags,source_name",
                "facet_by": "source_type,source_name,format,language,tags",
                "page": page,
                "per_page": per_page,
            }
        )

    def upsert(self, document: MetadataDocument) -> dict[str, Any]:
        self.ensure_collection()
        payload = document.model_dump(mode="json", exclude_none=True)
        if document.updated_at:
            payload["updated_at"] = int(document.updated_at.timestamp())
        return self.client.collections[self.settings.typesense_collection].documents.upsert(payload)

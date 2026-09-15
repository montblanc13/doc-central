from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MetadataDocument(BaseModel):
    """Format canonique produit par tous les connecteurs."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    content: str = ""
    source_type: str = "unknown"
    source_name: str = "unknown"
    source_uri: HttpUrl | str | None = None
    format: str = "unknown"
    language: str | None = None
    tags: list[str] = Field(default_factory=list)
    access: str = "unknown"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

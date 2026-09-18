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


class MetadataDocumentUpdate(BaseModel):
    """Mise à jour partielle : seuls les champs fournis sont appliqués."""

    model_config = ConfigDict(extra="allow")

    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    content: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    source_uri: HttpUrl | str | None = None
    format: str | None = None
    language: str | None = None
    tags: list[str] | None = None
    access: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

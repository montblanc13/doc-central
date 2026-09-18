from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ID_PATTERN = r"^[A-Za-z0-9._:-]+$"
"""Un identifiant est opaque : ni « / », ni chemin, pour rester un segment d'URL."""

ENRICHED_FIELDS_KEY = "enriched_fields"
"""Champs écrits via l'API, que la ré-indexation d'une source ne doit pas écraser."""


class MetadataDocument(BaseModel):
    """Format canonique produit par tous les connecteurs."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1, max_length=128, pattern=ID_PATTERN)
    title: str = Field(min_length=1)
    description: str = ""
    content: str = ""
    source_type: str = "unknown"
    source_name: str = "unknown"
    source_path: str = ""
    source_uri: HttpUrl | str | None = None
    format: str = "unknown"
    language: str | None = None
    tags: list[str] = Field(default_factory=list)
    access: str = "unknown"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    enriched_fields: list[str] = Field(
        default_factory=list,
        description="Champs appartenant à l'utilisateur. Géré par le service, en lecture seule.",
    )


class MetadataDocumentUpdate(BaseModel):
    """Mise à jour partielle : seuls les champs fournis sont appliqués."""

    model_config = ConfigDict(extra="allow")

    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    content: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    source_path: str | None = None
    source_uri: HttpUrl | str | None = None
    format: str | None = None
    language: str | None = None
    tags: list[str] | None = None
    access: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

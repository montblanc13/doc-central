from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from app.models import MetadataDocument


class Connector(Protocol):
    """Contrat minimal d'un connecteur de source."""

    def extract(self) -> Iterable[MetadataDocument]:
        """Extrait des documents normalisés."""


def document_id(source: str, path: Path) -> str:
    return f"{source}:{path.resolve()}"

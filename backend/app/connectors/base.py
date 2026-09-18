import hashlib
from collections.abc import Iterable
from typing import Protocol

from app.models import MetadataDocument

ID_LENGTH = 32


class Connector(Protocol):
    """Contrat minimal d'un connecteur de source."""

    def extract(self) -> Iterable[MetadataDocument]:
        """Extrait des documents normalisés."""


def document_id(source_name: str, source_path: str) -> str:
    """Identifiant opaque et déterministe.

    L'identifiant n'expose ni l'arborescence de la source ni son nom : la
    source et le chemin restent des champs du document (``source_name`` et
    ``source_path``). Le calcul est déterministe pour qu'une ré-indexation
    mette à jour le document existant au lieu d'en créer un doublon.

    Args:
        source_name: nom logique de la source, p. ex. ``local-files``.
        source_path: clé native du document dans la source, p. ex. un chemin
            relatif à la racine du connecteur.
    """
    digest = hashlib.sha256(f"{source_name}\0{source_path}".encode())
    return digest.hexdigest()[:ID_LENGTH]

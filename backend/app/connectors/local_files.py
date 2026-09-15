import csv
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

from app.connectors.base import document_id
from app.models import MetadataDocument


class LocalFileConnector:
    """Extrait les premiers formats simples depuis un dossier local."""

    supported_suffixes: ClassVar[set[str]] = {".txt", ".md", ".markdown", ".json", ".csv"}

    def __init__(self, root: Path, source_name: str = "local-files") -> None:
        self.root = root
        self.source_name = source_name

    def extract(self) -> Iterator[MetadataDocument]:
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.suffix.lower() in self.supported_suffixes:
                yield self._extract_file(path)

    def _extract_file(self, path: Path) -> MetadataDocument:
        stat = path.stat()
        updated_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
        suffix = path.suffix.lower()

        if suffix == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            title = str(raw.get("title", path.stem)) if isinstance(raw, dict) else path.stem
            content = json.dumps(raw, ensure_ascii=False, indent=2)
        elif suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            title = path.stem
            content = json.dumps(rows, ensure_ascii=False, indent=2)
        else:
            content = path.read_text(encoding="utf-8", errors="replace")
            title = next((line.removeprefix("# ").strip() for line in content.splitlines() if line.startswith("# ")), path.stem)

        return MetadataDocument(
            id=document_id(self.source_name, path),
            title=title,
            content=content,
            source_type="file",
            source_name=self.source_name,
            source_uri=path.resolve().as_uri(),
            format=suffix.removeprefix(".") or "unknown",
            updated_at=updated_at,
            metadata={"path": str(path.resolve()), "size_bytes": stat.st_size},
        )

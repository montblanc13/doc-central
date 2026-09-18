from pathlib import Path

from app.connectors import LocalFileConnector
from app.connectors.base import document_id
from app.models import ID_PATTERN, MetadataDocument


def test_id_is_deterministic():
    assert document_id("local-files", "notes.md") == document_id("local-files", "notes.md")


def test_id_differs_per_source():
    assert document_id("local-files", "notes.md") != document_id("drive", "notes.md")


def test_id_differs_per_path():
    assert document_id("local-files", "a.md") != document_id("local-files", "b.md")


def test_id_leaks_neither_source_nor_path():
    generated = document_id("local-files", "dossier/notes.md")
    assert "local-files" not in generated
    assert "notes" not in generated
    assert "/" not in generated


def test_id_is_accepted_by_the_canonical_contract():
    generated = document_id("local-files", "dossier/notes.md")
    assert MetadataDocument(id=generated, title="Notes").id == generated
    assert ID_PATTERN


def test_connector_id_is_independent_of_the_root_location(tmp_path: Path):
    ids = []
    for parent in ("machine-a", "machine-b"):
        root = tmp_path / parent / "sources"
        (root / "dossier").mkdir(parents=True)
        (root / "dossier" / "notes.md").write_text("# Notes\n", encoding="utf-8")
        documents = list(LocalFileConnector(root).extract())
        assert len(documents) == 1
        ids.append(documents[0].id)
        assert documents[0].source_path == "dossier/notes.md"
        assert documents[0].source_name == "local-files"

    assert ids[0] == ids[1], "un même fichier doit garder le même id d'une machine à l'autre"

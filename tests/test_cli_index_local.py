"""Le CLI d'ingestion doit passer par index(), la seule écriture qui préserve
les enrichissements. Un retour à upsert/replace reperdrait les éditions."""

from pathlib import Path

import pytest

from app.cli import index_local


class SpyService:
    def __init__(self, *_args) -> None:
        self.indexed: list[str] = []

    def ensure_collection(self) -> dict:
        return {}

    def index(self, document) -> dict:
        self.indexed.append(document.id)
        return {}

    def replace(self, document) -> dict:  # pragma: no cover - ne doit pas être appelé
        raise AssertionError("le CLI ne doit pas remplacer un document")


@pytest.fixture
def sources(tmp_path: Path) -> Path:
    root = tmp_path / "sources"
    root.mkdir()
    (root / "notes.md").write_text("# Notes\n", encoding="utf-8")
    return root


def test_cli_indexes_through_the_merging_write(monkeypatch, sources, tmp_path, capsys):
    spy = SpyService()
    monkeypatch.setattr(index_local, "TypesenseService", lambda *_: spy)
    monkeypatch.setattr(index_local.sys, "argv", ["index_local", str(sources)])
    monkeypatch.chdir(tmp_path)

    index_local.main()

    assert len(spy.indexed) == 1
    assert "1 document(s)" in capsys.readouterr().out


def test_service_no_longer_exposes_a_blind_upsert():
    from app.services import TypesenseService

    assert not hasattr(TypesenseService, "upsert")

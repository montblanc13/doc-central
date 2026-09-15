import json
import sys
from pathlib import Path

from app.config import get_settings
from app.connectors import LocalFileConnector
from app.services import TypesenseService


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/sources")
    output_dir = Path("data/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)
    connector = LocalFileConnector(root)
    service = TypesenseService(get_settings())
    service.ensure_collection()

    count = 0
    with (output_dir / "documents.jsonl").open("w", encoding="utf-8") as handle:
        for document in connector.extract():
            handle.write(json.dumps(document.model_dump(mode="json"), ensure_ascii=False) + "\n")
            service.upsert(document)
            count += 1
    print(f"{count} document(s) indexé(s) depuis {root}")


if __name__ == "__main__":
    main()

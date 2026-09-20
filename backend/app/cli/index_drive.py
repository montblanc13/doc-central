import json
from pathlib import Path

from app.config import get_settings
from app.connectors import GoogleDriveConnector
from app.services import TypesenseService, get_ai_service


def main() -> None:
    settings = get_settings()
    output_dir = Path("data/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)
    connector = GoogleDriveConnector(settings, ai_service=get_ai_service(settings))
    service = TypesenseService(settings)
    service.ensure_collection()

    count = 0
    output_path = output_dir / "google-drive.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for document in connector.extract():
            handle.write(json.dumps(document.model_dump(mode="json"), ensure_ascii=False) + "\n")
            service.upsert(document)
            count += 1
    print(f"{count} document(s) indexé(s) depuis Google Drive")


if __name__ == "__main__":
    main()

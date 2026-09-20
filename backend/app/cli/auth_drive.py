from app.config import get_settings
from app.connectors import GoogleDriveConnector


def main() -> None:
    settings = get_settings()
    GoogleDriveConnector(settings).authenticate()
    print(f"Jeton Google Drive prêt : {settings.google_drive_token_file}")


if __name__ == "__main__":
    main()

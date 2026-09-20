from typing import Any, Protocol

from app.config import Settings

SUMMARY_INSTRUCTIONS = """Tu résumes des documents pour un moteur de recherche documentaire.
Produis un résumé fidèle de 2 à 4 phrases, sans titre, sans liste et sans Markdown.
N'invente aucune information. Utilise la langue principale du document."""


class AIService(Protocol):
    """Contrat d'un service capable de résumer un document."""

    def summarize(self, *, title: str, description: str, content: str) -> str:
        """Retourne un résumé sémantique du document."""


class AIServiceError(RuntimeError):
    """Erreur de configuration ou d'appel d'un fournisseur LLM."""


class OpenAIService:
    """Résumé via l'API Responses d'OpenAI."""

    def __init__(
        self,
        api_key: str,
        model: str,
        max_input_chars: int = 20000,
        max_output_tokens: int = 180,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise AIServiceError("OPENAI_API_KEY est requis avec AI_PROVIDER=openai")
        self.model = model
        self.max_input_chars = max_input_chars
        self.max_output_tokens = max_output_tokens
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self.client = client

    def summarize(self, *, title: str, description: str, content: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=SUMMARY_INSTRUCTIONS,
            input=_summary_input(title, description, content, self.max_input_chars),
            max_output_tokens=self.max_output_tokens,
            store=False,
        )
        return response.output_text.strip()


class AnthropicService:
    """Résumé via l'API Messages d'Anthropic."""

    def __init__(
        self,
        api_key: str,
        model: str,
        max_input_chars: int = 20000,
        max_output_tokens: int = 180,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise AIServiceError("ANTHROPIC_API_KEY est requis avec AI_PROVIDER=anthropic")
        self.model = model
        self.max_input_chars = max_input_chars
        self.max_output_tokens = max_output_tokens
        if client is None:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
        self.client = client

    def summarize(self, *, title: str, description: str, content: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_output_tokens,
            system=SUMMARY_INSTRUCTIONS,
            messages=[
                {
                    "role": "user",
                    "content": _summary_input(title, description, content, self.max_input_chars),
                }
            ],
        )
        return "".join(
            block.text for block in message.content if getattr(block, "type", "") == "text"
        ).strip()


def get_ai_service(settings: Settings) -> AIService | None:
    provider = settings.ai_provider.strip().lower()
    if provider in {"", "none", "off", "disabled"}:
        return None
    if provider == "openai":
        return OpenAIService(
            api_key=settings.openai_api_key or "",
            model=settings.openai_model,
            max_input_chars=settings.ai_max_input_chars,
            max_output_tokens=settings.ai_max_output_tokens,
        )
    if provider == "anthropic":
        return AnthropicService(
            api_key=settings.anthropic_api_key or "",
            model=settings.anthropic_model,
            max_input_chars=settings.ai_max_input_chars,
            max_output_tokens=settings.ai_max_output_tokens,
        )
    raise AIServiceError(f"Fournisseur AI_PROVIDER inconnu: {settings.ai_provider}")


def _summary_input(title: str, description: str, content: str, max_chars: int) -> str:
    source = content.strip() or description.strip()
    if not source:
        return f"Titre du document : {title}"
    return f"Titre du document : {title}\n\nContenu :\n{source[:max_chars]}"

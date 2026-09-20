from types import SimpleNamespace

from app.services.ai import AnthropicService, OpenAIService


class FakeOpenAIResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text="Résumé OpenAI")


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeOpenAIResponses()


class FakeAnthropicMessages:
    def create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="Résumé Anthropic")])


class FakeAnthropicClient:
    def __init__(self):
        self.messages = FakeAnthropicMessages()


def test_openai_service_uses_responses_api():
    client = FakeOpenAIClient()
    service = OpenAIService("key", "gpt-test", client=client)

    assert service.summarize(title="Titre", description="", content="Contenu") == "Résumé OpenAI"
    assert client.responses.calls[0]["model"] == "gpt-test"
    assert client.responses.calls[0]["store"] is False


def test_anthropic_service_uses_messages_api():
    service = AnthropicService("key", "claude-test", client=FakeAnthropicClient())

    assert service.summarize(title="Titre", description="", content="Contenu") == "Résumé Anthropic"

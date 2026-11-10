
from types import SimpleNamespace

import pytest

from rag.llm_service import GeminiGenerationService


class FakeModels:
    """Simulates Gemini's text-generation API."""

    def __init__(self):
        self.calls = []
        self.response_text = "RAG combines retrieval and generation."
        self.error = None

    def generate_content(
        self,
        model,
        contents,
        config
    ):

        self.calls.append({
            "model": model,
            "contents": contents,
            "config": config
        })

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            text=self.response_text
        )


class FakeClient:

    def __init__(self):
        self.models = FakeModels()


@pytest.fixture
def generation_setup():

    client = FakeClient()

    service = GeminiGenerationService(
        client=client,
        model="test-model",
        max_output_tokens=512
    )

    return service, client


def test_generate_answer(generation_setup):

    service, _ = generation_setup

    answer = service.generate_answer(
        question="What is RAG?",
        context="RAG combines retrieval and generation."
    )

    assert answer == "RAG combines retrieval and generation."


def test_generation_request_contains_question_and_context(
    generation_setup
):

    service, client = generation_setup

    service.generate_answer(
        question="What is RAG?",
        context="RAG uses retrieved documents."
    )

    request = client.models.calls[0]

    assert request["model"] == "test-model"
    assert "What is RAG?" in request["contents"]
    assert "RAG uses retrieved documents." in request["contents"]

    assert (
        request["config"].max_output_tokens == 512
    )

    assert (
        request["config"].system_instruction
        == service.SYSTEM_INSTRUCTION
    )


def test_empty_context_does_not_call_gemini(
    generation_setup
):

    service, client = generation_setup

    answer = service.generate_answer(
        question="What is RAG?",
        context="   "
    )

    assert "couldn't find relevant information" in answer

    assert len(client.models.calls) == 0


def test_empty_question_rejected(generation_setup):

    service, _ = generation_setup

    with pytest.raises(ValueError):
        service.generate_answer(
            question="   ",
            context="Some document content."
        )


def test_non_string_question_rejected(generation_setup):

    service, _ = generation_setup

    with pytest.raises(TypeError):
        service.generate_answer(
            question=123,
            context="Some document content."
        )


def test_non_string_context_rejected(generation_setup):

    service, _ = generation_setup

    with pytest.raises(TypeError):
        service.generate_answer(
            question="What is RAG?",
            context=123
        )


def test_empty_gemini_response_rejected(generation_setup):

    service, client = generation_setup

    client.models.response_text = "   "

    with pytest.raises(RuntimeError):
        service.generate_answer(
            question="What is RAG?",
            context="RAG combines retrieval and generation."
        )


def test_gemini_api_error_handled(generation_setup):

    service, client = generation_setup

    client.models.error = ValueError(
        "Simulated API error"
    )

    with pytest.raises(RuntimeError):
        service.generate_answer(
            question="What is RAG?",
            context="Some document content."
        )


@pytest.mark.parametrize(
    "invalid_tokens",
    [0, -1, 1.5, True]
)
def test_invalid_output_tokens_rejected(
    invalid_tokens
):

    client = FakeClient()

    with pytest.raises(ValueError):
        GeminiGenerationService(
            client=client,
            max_output_tokens=invalid_tokens
        )

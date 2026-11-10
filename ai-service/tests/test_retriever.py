
import pytest

from rag.retriever import Retriever


class FakeEmbeddingService:
    """Simulates the Gemini embedding service."""

    def __init__(self):
        self.received_query = None

    def embed_query(self, query):
        self.received_query = query
        return [1.0, 0.0, 0.0]


class FakeVectorStore:
    """Simulates the USearch vector store."""

    def __init__(self):
        self.received_embedding = None
        self.received_top_k = None

        self.results = [
            {
                "id": 1,
                "text": "RAG combines retrieval with generation.",
                "metadata": {
                    "source": "rag.pdf",
                    "page": 1
                },
                "distance": 0.1
            }
        ]

    def search(self, query_embedding, top_k=5):
        self.received_embedding = query_embedding
        self.received_top_k = top_k

        return self.results


@pytest.fixture
def retriever_setup():

    embedding_service = FakeEmbeddingService()
    vector_store = FakeVectorStore()

    retriever = Retriever(
        embedding_service,
        vector_store
    )

    return retriever, embedding_service, vector_store


def test_retrieve_document_chunks(retriever_setup):

    retriever, embedding_service, vector_store = retriever_setup

    results = retriever.retrieve(
        "What is RAG?",
        top_k=3
    )

    assert len(results) == 1

    assert embedding_service.received_query == "What is RAG?"

    assert vector_store.received_embedding == [1.0, 0.0, 0.0]

    assert vector_store.received_top_k == 3


def test_retrieve_uses_default_top_k(retriever_setup):

    retriever, _, vector_store = retriever_setup

    retriever.retrieve("Explain RAG")

    assert vector_store.received_top_k == 5


def test_empty_query_rejected(retriever_setup):

    retriever, _, _ = retriever_setup

    with pytest.raises(ValueError):
        retriever.retrieve("   ")


def test_non_string_query_rejected(retriever_setup):

    retriever, _, _ = retriever_setup

    with pytest.raises(TypeError):
        retriever.retrieve(123)


@pytest.mark.parametrize(
    "invalid_top_k",
    [0, -1, 1.5, True]
)
def test_invalid_top_k_rejected(
    retriever_setup,
    invalid_top_k
):

    retriever, _, _ = retriever_setup

    with pytest.raises(ValueError):
        retriever.retrieve(
            "What is RAG?",
            top_k=invalid_top_k
        )


def test_format_context(retriever_setup):

    retriever, _, _ = retriever_setup

    results = retriever.retrieve("What is RAG?")

    context = retriever.format_context(results)

    assert "Document 1" in context
    assert "Source: rag.pdf" in context
    assert "Page: 1" in context
    assert "RAG combines retrieval with generation." in context


def test_format_context_without_page(retriever_setup):

    retriever, _, _ = retriever_setup

    results = [
        {
            "text": "Sample document content.",
            "metadata": {
                "source": "sample.txt"
            }
        }
    ]

    context = retriever.format_context(results)

    assert "Source: sample.txt" in context
    assert "Page:" not in context


def test_empty_results_return_empty_context(retriever_setup):

    retriever, _, _ = retriever_setup

    context = retriever.format_context([])

    assert context == ""


def test_empty_document_text_is_skipped(retriever_setup):

    retriever, _, _ = retriever_setup

    results = [
        {
            "text": "   ",
            "metadata": {"source": "empty.txt"}
        }
    ]

    context = retriever.format_context(results)

    assert context == ""

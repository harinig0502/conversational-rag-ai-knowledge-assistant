
import numpy as np
import pytest

from rag.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path):
    """
    Create a temporary vector store for each test.
    """

    return VectorStore(
        dimension=3,
        storage_dir=tmp_path
    )


def test_add_chunks(vector_store):

    chunks = [
        {
            "text": "Python is a programming language.",
            "metadata": {"source": "python.txt"},
            "embedding": [1.0, 0.0, 0.0]
        },
        {
            "text": "Machine learning uses data.",
            "metadata": {"source": "ml.txt"},
            "embedding": [0.0, 1.0, 0.0]
        }
    ]

    ids = vector_store.add_chunks(chunks)

    assert len(ids) == 2
    assert vector_store.count == 2


def test_search_returns_similar_chunks(vector_store):

    chunks = [
        {
            "text": "Python programming basics.",
            "metadata": {"source": "python.txt"},
            "embedding": [1.0, 0.0, 0.0]
        },
        {
            "text": "Cooking recipes.",
            "metadata": {"source": "cooking.txt"},
            "embedding": [0.0, 1.0, 0.0]
        },
        {
            "text": "Python software development.",
            "metadata": {"source": "development.txt"},
            "embedding": [0.9, 0.1, 0.0]
        }
    ]

    vector_store.add_chunks(chunks)

    results = vector_store.search(
        query_embedding=[1.0, 0.0, 0.0],
        top_k=2
    )

    assert len(results) == 2

    assert (
        results[0]["text"]
        == "Python programming basics."
    )

    assert results[0]["distance"] <= results[1]["distance"]


def test_metadata_is_preserved(vector_store):

    chunks = [
        {
            "text": "Sample document.",
            "metadata": {
                "source": "sample.pdf",
                "page": 2
            },
            "embedding": [1.0, 0.0, 0.0]
        }
    ]

    vector_store.add_chunks(chunks)

    results = vector_store.search(
        [1.0, 0.0, 0.0],
        top_k=1
    )

    assert results[0]["metadata"]["source"] == "sample.pdf"
    assert results[0]["metadata"]["page"] == 2


def test_empty_store_returns_no_results(vector_store):

    results = vector_store.search(
        [1.0, 0.0, 0.0],
        top_k=3
    )

    assert results == []


def test_save_and_restore(vector_store):

    chunks = [
        {
            "text": "Persistent document content.",
            "metadata": {"source": "saved.txt"},
            "embedding": [1.0, 0.0, 0.0]
        }
    ]

    vector_store.add_chunks(chunks)

    assert vector_store.index_path.exists()
    assert vector_store.metadata_path.exists()

    # Open the same storage directory again
    restored_store = VectorStore(
        dimension=3,
        storage_dir=vector_store.storage_dir
    )

    assert restored_store.count == 1

    results = restored_store.search(
        [1.0, 0.0, 0.0],
        top_k=1
    )

    assert len(results) == 1
    assert results[0]["text"] == "Persistent document content."


def test_wrong_embedding_dimension_rejected(vector_store):

    chunks = [
        {
            "text": "Invalid vector.",
            "metadata": {},
            "embedding": [1.0, 0.0]
        }
    ]

    with pytest.raises(ValueError):
        vector_store.add_chunks(chunks)


def test_invalid_top_k_rejected(vector_store):

    with pytest.raises(ValueError):
        vector_store.search(
            [1.0, 0.0, 0.0],
            top_k=0
        )


def test_empty_chunks(vector_store):

    result = vector_store.add_chunks([])

    assert result == []
    assert vector_store.count == 0

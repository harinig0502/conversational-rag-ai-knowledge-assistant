
from types import SimpleNamespace

import numpy as np
import pytest

from rag.embedding_service import EmbeddingService


class FakeModels:

    def __init__(self):
        self.calls = []

    def embed_content(
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

        dimension = config.output_dimensionality

        values = [
            float(index + 1)
            for index in range(dimension)
        ]

        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(values=values)
                for _ in contents
            ]
        )


class FakeClient:

    def __init__(self):
        self.models = FakeModels()


@pytest.fixture
def embedding_setup():

    client = FakeClient()

    service = EmbeddingService(
        client=client,
        output_dimensionality=768,
        batch_size=2
    )

    return service, client


def test_document_embeddings(embedding_setup):

    service, _ = embedding_setup

    result = service.embed_texts([
        "This is a document.",
        "This is another document."
    ])

    assert result.shape == (2, 768)

    norms = np.linalg.norm(result, axis=1)

    assert np.allclose(norms, 1.0, atol=1e-5)


def test_batch_processing(embedding_setup):

    service, client = embedding_setup

    service.embed_texts([
        "Document one.",
        "Document two.",
        "Document three."
    ])

    # Batch size is 2, so 3 inputs require 2 requests.
    assert len(client.models.calls) == 2


def test_query_embedding(embedding_setup):

    service, client = embedding_setup

    result = service.embed_query(
        "What is retrieval augmented generation?"
    )

    assert result.shape == (768,)

    last_call = client.models.calls[-1]

    assert (
        last_call["config"].task_type
        == "RETRIEVAL_QUERY"
    )


def test_document_metadata(embedding_setup):

    service, _ = embedding_setup

    chunks = [
        {
            "text": "Sample document content.",
            "metadata": {
                "source": "sample.txt",
                "chunk_index": 1
            }
        }
    ]

    result = service.embed_documents(chunks)

    assert len(result) == 1

    assert result[0]["metadata"]["source"] == "sample.txt"

    assert len(result[0]["embedding"]) == 768


def test_empty_input(embedding_setup):

    service, _ = embedding_setup

    result = service.embed_texts([])

    assert result.shape == (0, 768)


def test_empty_query_rejected(embedding_setup):

    service, _ = embedding_setup

    with pytest.raises(ValueError):
        service.embed_query("   ")

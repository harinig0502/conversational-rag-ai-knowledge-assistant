
from rag.chunking import split_text, chunk_documents


def test_short_text():

    text = "This is a short document."

    chunks = split_text(text)

    assert len(chunks) == 1
    assert chunks[0][0] == text


def test_long_text():

    text = " ".join(
        f"word{i}" for i in range(300)
    )

    chunks = split_text(
        text,
        chunk_size=100,
        chunk_overlap=20
    )

    assert len(chunks) > 1

    for chunk, start, end in chunks:
        assert len(chunk) <= 100
        assert end > start


def test_empty_text():

    chunks = split_text("")

    assert chunks == []


def test_document_metadata():

    documents = [
        {
            "text": "This is a document for testing.",
            "metadata": {
                "source": "sample.txt",
                "file_type": "txt"
            }
        }
    ]

    chunks = chunk_documents(documents)

    assert len(chunks) == 1

    assert chunks[0]["metadata"]["source"] == "sample.txt"

    assert chunks[0]["metadata"]["chunk_index"] == 1


def test_invalid_chunk_settings():

    try:
        split_text("Hello world", 100, 100)
    except ValueError:
        return

    raise AssertionError("Expected ValueError was not raised.")

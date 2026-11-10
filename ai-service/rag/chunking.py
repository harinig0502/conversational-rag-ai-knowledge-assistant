
def split_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[tuple[str, int, int]]:
    """
    Split text into smaller chunks with overlapping content.

    Returns:
        A list of tuples containing:
        (chunk_text, start_position, end_position)
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if chunk_overlap < 0:
        raise ValueError("Chunk overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be smaller than chunk size."
        )

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + chunk_size, text_length)

        # Prefer splitting at a natural text boundary
        if end < text_length:

            search_start = start + int(
                (end - start) * 0.75
            )

            separators = [
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                " "
            ]

            boundary = -1
            separator_length = 0

            for separator in separators:

                position = text.rfind(
                    separator,
                    search_start,
                    end
                )

                if position > boundary:
                    boundary = position
                    separator_length = len(separator)

            if boundary != -1:
                end = boundary + separator_length

        chunk = text[start:end].strip()

        if chunk:
            chunks.append((chunk, start, end))

        if end >= text_length:
            break

        # Move backwards to preserve overlapping context
        next_start = max(
            end - chunk_overlap,
            start + 1
        )

        # Avoid beginning in the middle of a word
        while (
            next_start < end
            and not text[next_start].isspace()
        ):
            next_start += 1

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[dict]:
    """
    Split extracted documents into chunks.

    Preserves original metadata and adds chunk information.
    """

    all_chunks = []

    for document in documents:

        text = document.get("text", "")

        if not isinstance(text, str):
            raise TypeError("Document text must be a string.")

        metadata = document.get("metadata", {})

        if not isinstance(metadata, dict):
            raise TypeError("Document metadata must be a dictionary.")

        text_chunks = split_text(
            text,
            chunk_size,
            chunk_overlap
        )

        for index, (chunk, start, end) in enumerate(
            text_chunks,
            start=1
        ):

            chunk_metadata = metadata.copy()

            chunk_metadata.update({
                "chunk_index": index,
                "chunk_start": start,
                "chunk_end": end,
                "chunk_size": len(chunk)
            })

            all_chunks.append({
                "text": chunk,
                "metadata": chunk_metadata
            })

    return all_chunks

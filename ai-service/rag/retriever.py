
class Retriever:
    """
    Retrieve relevant document chunks for a user query.

    Connects:
    - EmbeddingService
    - VectorStore
    """

    def __init__(
        self,
        embedding_service,
        vector_store
    ):

        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict]:
        """
        Convert a user query into an embedding
        and retrieve the most relevant document chunks.
        """

        if not isinstance(query, str):
            raise TypeError(
                "Query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "Query cannot be empty."
            )

        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or top_k <= 0
        ):
            raise ValueError(
                "top_k must be a positive integer."
            )

        # Step 1: Convert the question into an embedding
        query_embedding = (
            self.embedding_service.embed_query(query)
        )

        # Step 2: Search the vector database
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k
        )

        return results

    def format_context(
        self,
        results: list[dict]
    ) -> str:
        """
        Format retrieved document chunks into
        readable context for the Gemini LLM.
        """

        if not isinstance(results, list):
            raise TypeError(
                "Results must be provided as a list."
            )

        if not results:
            return ""

        context_parts = []

        for index, result in enumerate(
            results,
            start=1
        ):

            if not isinstance(result, dict):
                raise TypeError(
                    "Each retrieval result must be a dictionary."
                )

            text = result.get("text", "")

            if not isinstance(text, str):
                raise TypeError(
                    "Retrieved text must be a string."
                )

            if not text.strip():
                continue

            metadata = result.get("metadata", {})

            if not isinstance(metadata, dict):
                raise TypeError(
                    "Retrieved metadata must be a dictionary."
                )

            source = metadata.get(
                "source",
                "Unknown source"
            )

            source_info = f"Source: {source}"

            page = metadata.get("page")

            if page is not None:
                source_info += f", Page: {page}"

            context_parts.append(
                f"[Document {index}]\n"
                f"{source_info}\n"
                f"Content:\n{text.strip()}"
            )

        return "\n\n".join(context_parts)


import os
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load environment variables from ai-service/.env
AI_SERVICE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(
    dotenv_path=AI_SERVICE_DIR / ".env"
)


class EmbeddingService:
    """
    Generate and normalize text embeddings using Gemini.

    Supports:
    1. Document embeddings
    2. User query embeddings
    3. Batch processing
    4. Vector normalization
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        output_dimensionality: int | None = None,
        batch_size: int = 32,
        client: Any | None = None
    ):

        # Read API key from environment
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY")
        )

        if client is None and not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Add your API key to ai-service/.env."
            )

        # Configure embedding model
        self.model = (
            model
            or os.getenv(
                "GEMINI_EMBEDDING_MODEL",
                "gemini-embedding-001"
            )
        )

        # Configure vector dimensions
        dimension_value = (
            output_dimensionality
            if output_dimensionality is not None
            else os.getenv(
                "GEMINI_EMBEDDING_DIMENSION",
                "768"
            )
        )

        try:
            self.output_dimensionality = int(
                dimension_value
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Embedding dimension must be an integer."
            ) from error

        if not 128 <= self.output_dimensionality <= 3072:
            raise ValueError(
                "Embedding dimension must be between "
                "128 and 3072."
            )

        # Configure batch size
        if batch_size <= 0:
            raise ValueError(
                "Batch size must be greater than zero."
            )

        self.batch_size = batch_size

        # Initialize Gemini client
        self.client = (
            client
            if client is not None
            else genai.Client(api_key=self.api_key)
        )

    def _normalize_vector(
        self,
        values: Sequence[float]
    ) -> np.ndarray:
        """
        Convert an embedding into a normalized
        NumPy float32 vector.
        """

        vector = np.asarray(
            values,
            dtype=np.float32
        )

        if vector.shape != (
            self.output_dimensionality,
        ):
            raise ValueError(
                "Unexpected embedding dimension. "
                f"Expected {self.output_dimensionality}, "
                f"received {vector.size}."
            )

        norm = float(np.linalg.norm(vector))

        if not np.isfinite(norm) or norm == 0:
            raise ValueError(
                "Embedding contains an invalid or zero vector."
            )

        return (vector / norm).astype(np.float32)

    def embed_texts(
        self,
        texts: Sequence[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        title: str | None = None
    ) -> np.ndarray:
        """
        Generate embeddings for multiple text inputs.

        Returns:
            A NumPy array with shape:
            (number_of_texts, embedding_dimensions)
        """

        if isinstance(texts, str):
            raise TypeError(
                "Pass a list of texts, not a single string."
            )

        texts = list(texts)

        if not texts:
            return np.empty(
                (0, self.output_dimensionality),
                dtype=np.float32
            )

        cleaned_texts = []

        for index, text in enumerate(texts):

            if not isinstance(text, str):
                raise TypeError(
                    f"Text at position {index} must be a string."
                )

            text = text.strip()

            if not text:
                raise ValueError(
                    f"Text at position {index} is empty."
                )

            cleaned_texts.append(text)

        # Validate retrieval task
        supported_tasks = {
            "RETRIEVAL_DOCUMENT",
            "RETRIEVAL_QUERY"
        }

        if task_type not in supported_tasks:
            raise ValueError(
                f"Unsupported task type: {task_type}"
            )

        if title and task_type != "RETRIEVAL_DOCUMENT":
            raise ValueError(
                "Title can only be used for document embeddings."
            )

        all_embeddings = []

        # Process texts in batches
        for start in range(
            0,
            len(cleaned_texts),
            self.batch_size
        ):

            batch = cleaned_texts[
                start:start + self.batch_size
            ]

            config_values = {
                "task_type": task_type,
                "output_dimensionality": (
                    self.output_dimensionality
                )
            }

            if title:
                config_values["title"] = title

            config = types.EmbedContentConfig(
                **config_values
            )

            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=config
                )

            except Exception as error:
                raise RuntimeError(
                    "Gemini embedding request failed "
                    f"for batch starting at item {start + 1}."
                ) from error

            response_embeddings = response.embeddings

            if (
                response_embeddings is None
                or len(response_embeddings) != len(batch)
            ):
                raise RuntimeError(
                    "Gemini returned an unexpected number "
                    "of embeddings."
                )

            for embedding in response_embeddings:

                if embedding.values is None:
                    raise RuntimeError(
                        "Gemini returned an empty embedding."
                    )

                normalized_vector = self._normalize_vector(
                    embedding.values
                )

                all_embeddings.append(
                    normalized_vector
                )

        return np.stack(
            all_embeddings
        ).astype(np.float32)

    def embed_documents(
        self,
        chunks: list[dict],
        title: str | None = None
    ) -> list[dict]:
        """
        Generate embeddings for document chunks.

        Preserves the original text and metadata.
        Adds an embedding field to each chunk.
        """

        if not chunks:
            return []

        for index, chunk in enumerate(chunks):

            if not isinstance(chunk, dict):
                raise TypeError(
                    f"Chunk at position {index} must be a dictionary."
                )

            if "text" not in chunk:
                raise ValueError(
                    f"Chunk at position {index} has no text field."
                )

            metadata = chunk.get("metadata", {})

            if not isinstance(metadata, dict):
                raise TypeError(
                    "Chunk metadata must be a dictionary."
                )

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = self.embed_texts(
            texts,
            task_type="RETRIEVAL_DOCUMENT",
            title=title
        )

        embedded_chunks = []

        for chunk, vector in zip(
            chunks,
            embeddings
        ):

            embedded_chunk = {
                **chunk,
                "metadata": chunk.get(
                    "metadata", {}
                ).copy(),
                "embedding": vector.tolist()
            }

            embedded_chunks.append(
                embedded_chunk
            )

        return embedded_chunks

    def embed_query(
        self,
        query: str
    ) -> np.ndarray:
        """
        Generate an embedding for a user question.

        Uses RETRIEVAL_QUERY for semantic retrieval.
        """

        embeddings = self.embed_texts(
            [query],
            task_type="RETRIEVAL_QUERY"
        )

        return embeddings[0]

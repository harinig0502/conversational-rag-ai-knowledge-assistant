
import json
from pathlib import Path

import numpy as np
from usearch.index import Index


class VectorStore:
    """
    Store document embeddings using USearch.

    Features:
    1. Add document chunks and their embeddings.
    2. Search for similar document chunks.
    3. Preserve document text and metadata.
    4. Save the vector index to disk.
    5. Restore the index when the application restarts.
    """

    def __init__(
        self,
        dimension: int = 768,
        storage_dir: str | Path | None = None
    ):

        if dimension <= 0:
            raise ValueError(
                "Embedding dimension must be greater than zero."
            )

        self.dimension = dimension

        # Set the default storage directory
        if storage_dir is None:
            storage_dir = (
                Path(__file__).resolve().parents[1]
                / "storage"
                / "usearch"
            )

        self.storage_dir = Path(storage_dir)

        self.index_path = (
            self.storage_dir / "documents.usearch"
        )

        self.metadata_path = (
            self.storage_dir / "metadata.json"
        )

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Restore an existing index or create a new one
        index_exists = self.index_path.exists()
        metadata_exists = self.metadata_path.exists()

        if index_exists != metadata_exists:
            raise RuntimeError(
                "Vector index and metadata files are incomplete. "
                "Both files must exist together."
            )

        if index_exists and metadata_exists:

            self.index = Index.restore(
                str(self.index_path)
            )

            if self.index.ndim != self.dimension:
                raise ValueError(
                    "Stored index dimension does not match "
                    f"the configured dimension of {self.dimension}."
                )

            self.metadata = json.loads(
                self.metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(self.metadata, dict):
                raise ValueError(
                    "Stored metadata must be a JSON object."
                )

        else:

            self.index = Index(
                ndim=self.dimension,
                metric="cos",
                dtype="f32"
            )

            self.metadata = {}

        # Generate the next unique vector ID
        existing_ids = [
            int(key)
            for key in self.metadata
        ]

        self.next_id = max(
            existing_ids,
            default=0
        ) + 1

    @property
    def count(self) -> int:
        """Return the number of stored document chunks."""

        return len(self.metadata)

    def add_chunks(
        self,
        chunks: list[dict]
    ) -> list[int]:
        """
        Add document chunks and embeddings to USearch.

        Each chunk must contain:
        - text
        - metadata
        - embedding

        Returns:
            A list of generated vector IDs.
        """

        if not isinstance(chunks, list):
            raise TypeError(
                "Chunks must be provided as a list."
            )

        if not chunks:
            return []

        prepared_vectors = []
        prepared_metadata = []

        # Validate every chunk before inserting anything
        for position, chunk in enumerate(chunks):

            if not isinstance(chunk, dict):
                raise TypeError(
                    f"Chunk at position {position} "
                    "must be a dictionary."
                )

            text = chunk.get("text")

            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    f"Chunk at position {position} "
                    "has empty or invalid text."
                )

            metadata = chunk.get("metadata", {})

            if not isinstance(metadata, dict):
                raise TypeError(
                    f"Metadata at position {position} "
                    "must be a dictionary."
                )

            if "embedding" not in chunk:
                raise ValueError(
                    f"Chunk at position {position} "
                    "has no embedding."
                )

            vector = np.asarray(
                chunk["embedding"],
                dtype=np.float32
            )

            if vector.shape != (self.dimension,):
                raise ValueError(
                    f"Chunk at position {position} has "
                    f"an invalid embedding dimension. "
                    f"Expected {self.dimension}, "
                    f"received {vector.size}."
                )

            if not np.all(np.isfinite(vector)):
                raise ValueError(
                    f"Chunk at position {position} "
                    "contains invalid embedding values."
                )

            prepared_vectors.append(vector)

            prepared_metadata.append({
                "text": text,
                "metadata": metadata.copy()
            })

        # Generate unique integer IDs
        vector_ids = list(
            range(
                self.next_id,
                self.next_id + len(prepared_vectors)
            )
        )

        keys = np.asarray(
            vector_ids,
            dtype=np.uint64
        )

        vectors = np.stack(
            prepared_vectors
        ).astype(np.float32)

        # Insert vectors into USearch
        self.index.add(
            keys,
            vectors
        )

        # Store the corresponding text and metadata
        for vector_id, item in zip(
            vector_ids,
            prepared_metadata
        ):

            self.metadata[str(vector_id)] = item

        self.next_id += len(vector_ids)

        # Persist the updated index and metadata
        self.save()

        return vector_ids

    def search(
        self,
        query_embedding: list | np.ndarray,
        top_k: int = 5
    ) -> list[dict]:
        """
        Find the most similar document chunks.

        Args:
            query_embedding: Embedding of the user question.
            top_k: Maximum number of results to return.

        Returns:
            Matching document chunks with distance scores.
            Smaller cosine distances indicate greater similarity.
        """

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_vector = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        if query_vector.shape != (self.dimension,):
            raise ValueError(
                "Query embedding has an invalid dimension. "
                f"Expected {self.dimension}, "
                f"received {query_vector.size}."
            )

        if not np.all(np.isfinite(query_vector)):
            raise ValueError(
                "Query embedding contains invalid values."
            )

        if not self.metadata:
            return []

        result_count = min(
            top_k,
            len(self.metadata)
        )

        # Search the vector index
        matches = self.index.search(
            query_vector,
            result_count
        )

        results = []

        for vector_id, distance in zip(
            matches.keys,
            matches.distances
        ):

            item = self.metadata.get(
                str(int(vector_id))
            )

            if item is None:
                continue

            results.append({
                "id": int(vector_id),
                "text": item["text"],
                "metadata": item["metadata"],
                "distance": float(distance)
            })

        return results

    def save(self) -> None:
        """
        Save the vector index and metadata to disk.
        """

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Save the USearch index
        self.index.save(
            str(self.index_path)
        )

        # Write metadata to a temporary file first
        temporary_path = (
            self.metadata_path.with_suffix(".json.tmp")
        )

        temporary_path.write_text(
            json.dumps(
                self.metadata,
                ensure_ascii=False,
                indent=4
            ),
            encoding="utf-8"
        )

        # Replace the old metadata file
        temporary_path.replace(
            self.metadata_path
        )

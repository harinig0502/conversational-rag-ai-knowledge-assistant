
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from rag.document_loader import load_document
from rag.chunking import chunk_documents
from rag.embedding_service import EmbeddingService
from rag.vector_store import VectorStore
from rag.retriever import Retriever
from rag.llm_service import GeminiGenerationService


# --------------------------------------------------
# 1. Application configuration
# --------------------------------------------------

AI_SERVICE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = (
    AI_SERVICE_DIR / "storage" / "uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


# --------------------------------------------------
# 2. Initialize FastAPI
# --------------------------------------------------

app = FastAPI(
    title="Conversational RAG AI Service",
    description=(
        "An AI knowledge assistant that answers "
        "questions using uploaded documents."
    ),
    version="1.0.0"
)


# --------------------------------------------------
# 3. Initialize AI components
# --------------------------------------------------

embedding_service = EmbeddingService()

vector_store = VectorStore(
    dimension=768
)

retriever = Retriever(
    embedding_service=embedding_service,
    vector_store=vector_store
)

llm_service = GeminiGenerationService()


# --------------------------------------------------
# 4. Chat request model
# --------------------------------------------------

class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=2000
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10
    )


# --------------------------------------------------
# 5. Root endpoint
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Welcome to Conversational RAG AI Service",
        "status": "running",
        "version": "1.0.0"
    }


# --------------------------------------------------
# 6. Health check endpoint
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "Conversational RAG AI Service",
        "indexed_chunks": vector_store.count
    }


# --------------------------------------------------
# 7. Document upload endpoint
# --------------------------------------------------

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    filename = Path(
        file.filename or "uploaded_file"
    ).name

    extension = Path(filename).suffix.lower()

    # Validate file format
    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Upload PDF, DOCX or TXT files."
            )
        )

    # Read uploaded file with a size limit
    content = await file.read(
        MAX_UPLOAD_SIZE + 1
    )

    if not content:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_UPLOAD_SIZE:

        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 10 MB limit."
        )

    # Generate a unique storage filename
    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    saved_path = UPLOAD_DIR / unique_filename

    try:

        # Save uploaded document
        saved_path.write_bytes(content)

        # Extract document text
        documents = load_document(
            str(saved_path)
        )

        if not documents:

            raise HTTPException(
                status_code=400,
                detail="No readable text found in the document."
            )

        # Preserve the original uploaded filename
        for document in documents:

            document["metadata"]["source"] = filename

        # Split extracted text into chunks
        chunks = chunk_documents(
            documents,
            chunk_size=1000,
            chunk_overlap=200
        )

        if not chunks:

            raise HTTPException(
                status_code=400,
                detail="Document did not produce any text chunks."
            )

        # Generate Gemini embeddings
        embedded_chunks = (
            embedding_service.embed_documents(chunks)
        )

        # Save vectors and metadata in USearch
        vector_ids = vector_store.add_chunks(
            embedded_chunks
        )

        return {
            "message": "Document uploaded and indexed successfully.",
            "filename": filename,
            "chunks_indexed": len(vector_ids),
            "vector_ids": vector_ids
        }

    except HTTPException:
        raise

    except RuntimeError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        ) from error

    except (ValueError, TypeError) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed. "
                "Check the server terminal for details."
            )
        ) from error


# --------------------------------------------------
# 8. Chat endpoint
# --------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        # Retrieve relevant document chunks
        results = retriever.retrieve(
            query=request.question,
            top_k=request.top_k
        )

        # Format retrieved chunks into context
        context = retriever.format_context(
            results
        )

        # Generate answer using Gemini
        answer = llm_service.generate_answer(
            question=request.question,
            context=context
        )

        # Collect unique document sources
        sources = []
        seen_sources = set()

        for result in results:

            metadata = result.get(
                "metadata", {}
            )

            source = metadata.get(
                "source",
                "Unknown source"
            )

            page = metadata.get("page")

            source_key = (source, page)

            if source_key not in seen_sources:

                source_info = {
                    "source": source
                }

                if page is not None:
                    source_info["page"] = page

                sources.append(source_info)

                seen_sources.add(source_key)

        return {
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(results)
        }

    except RuntimeError as error:

        raise HTTPException(
            status_code=502,
            detail=str(error)
        ) from error

    except (ValueError, TypeError) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail="Unable to process the question."
        ) from error


from pathlib import Path

import pymupdf
from docx import Document


def load_document(file_path: str) -> list[dict]:
    """
    Extract text from PDF, DOCX, and TXT files.

    Returns:
        A list of dictionaries containing extracted text
        and document metadata.
    """

    path = Path(file_path)

    # 1. Check whether the file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    file_extension = path.suffix.lower()

    documents = []

    # 2. Extract text from PDF files
    if file_extension == ".pdf":

        with pymupdf.open(path) as pdf:

            for page_number, page in enumerate(pdf, start=1):

                text = page.get_text("text").strip()

                if text:
                    documents.append({
                        "text": text,
                        "metadata": {
                            "source": path.name,
                            "file_type": "pdf",
                            "page": page_number
                        }
                    })

    # 3. Extract text from Word documents
    elif file_extension == ".docx":

        doc = Document(path)

        paragraphs = []

        # Extract paragraphs
        for paragraph in doc.paragraphs:

            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        # Extract tables
        for table in doc.tables:

            for row in table.rows:

                row_text = " | ".join(
                    cell.text.strip()
                    for cell in row.cells
                )

                if row_text.strip():
                    paragraphs.append(row_text)

        text = "\n".join(paragraphs)

        if text:
            documents.append({
                "text": text,
                "metadata": {
                    "source": path.name,
                    "file_type": "docx",
                    "page": None
                }
            })

    # 4. Extract text from TXT files
    elif file_extension == ".txt":

        text = path.read_text(
            encoding="utf-8-sig"
        ).strip()

        if text:
            documents.append({
                "text": text,
                "metadata": {
                    "source": path.name,
                    "file_type": "txt",
                    "page": None
                }
            })

    # 5. Reject unsupported file formats
    else:
        raise ValueError(
            f"Unsupported file format: {file_extension}"
        )

    return documents

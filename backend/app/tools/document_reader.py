from pathlib import Path

from docx import Document
from pypdf import PdfReader


class LocalDocumentReader:
    async def read(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".txt":
            return path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".pdf":
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        if suffix == ".docx":
            return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
        raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")


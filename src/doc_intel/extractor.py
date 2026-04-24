"""PDF text extraction with Unicode normalization and safe truncation."""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass

import fitz

from doc_intel.errors import ExtractionError, PDFError

logger = logging.getLogger(__name__)

# Bound prompt size for API cost and context limits (characters, not bytes).
DEFAULT_MAX_CHARS = 20_000


@dataclass(frozen=True)
class ExtractOutcome:
    text: str
    warnings: list[str]


def extract_pdf_text(
    data: bytes,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> ExtractOutcome:
    """
    Extract plain text from PDF bytes.

    Raises PDFError on open/read failures or password-protected documents.
    Raises ExtractionError when no non-empty text could be extracted.
    """
    if not data:
        raise PDFError("The file is empty.")

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        logger.exception("Failed to open PDF")
        raise PDFError("Could not read this PDF. It may be corrupt or not a valid PDF.") from exc

    try:
        if doc.needs_pass:
            raise PDFError("This PDF is password-protected. Remove the password and try again.")

        parts: list[str] = []
        for page_index in range(len(doc)):
            page = doc[page_index]
            try:
                page_text = page.get_text("text") or ""
            except Exception as exc:
                logger.warning("Page %s text extraction failed: %s", page_index, exc)
                page_text = ""
            parts.append(page_text.strip())
        raw = "\n\n".join(p for p in parts if p)
    finally:
        doc.close()

    if not raw.strip():
        raise ExtractionError(
            "No readable text was found in this PDF. It may be image-only or use unsupported fonts."
        )

    normalized = unicodedata.normalize("NFC", raw)
    warnings: list[str] = []

    if len(normalized) > max_chars:
        truncated = normalized[:max_chars]
        warnings.append(
            f"Text was truncated to {max_chars} characters for analysis; document may be longer."
        )
        return ExtractOutcome(text=truncated, warnings=warnings)

    return ExtractOutcome(text=normalized, warnings=warnings)

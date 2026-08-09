"""Vision-based OCR fallback when PDFs have no extractable text layer."""

from __future__ import annotations

import base64
import logging
import time
from typing import Callable

import fitz
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from doc_intel.errors import ExtractionError, OpenAIClientError, PDFError
from doc_intel.prompts import SYSTEM_OCR

logger = logging.getLogger(__name__)

MAX_OCR_PAGES = 3
RENDER_DPI = 144
MAX_RETRIES = 2
BASE_DELAY_SECONDS = 1.0

ProgressCb = Callable[[str], None] | None


def _noop_stage(_: str) -> None:
    return None


def render_pdf_page_pngs(data: bytes, *, max_pages: int = MAX_OCR_PAGES) -> list[bytes]:
    """Render the first *max_pages* pages of a PDF to PNG bytes."""
    if not data:
        raise PDFError("The file is empty.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        logger.exception("Failed to open PDF for OCR")
        raise PDFError("Could not read this PDF. It may be corrupt or not a valid PDF.") from exc

    try:
        if doc.needs_pass:
            raise PDFError("This PDF is password-protected. Remove the password and try again.")
        if len(doc) == 0:
            raise ExtractionError("PDF has no pages to OCR.")

        images: list[bytes] = []
        zoom = RENDER_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        page_count = min(len(doc), max_pages)
        for i in range(page_count):
            page = doc[i]
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            images.append(pix.tobytes("png"))
        return images
    finally:
        doc.close()


def vision_ocr_pdf(
    client: OpenAI,
    data: bytes,
    *,
    model: str,
    max_pages: int = MAX_OCR_PAGES,
    on_stage: ProgressCb = None,
) -> tuple[str, list[str]]:
    """
    OCR PDF pages via OpenAI vision.

    Returns (text, warnings). Raises OpenAIClientError / PDFError / ExtractionError.
    """
    stage = on_stage or _noop_stage
    stage("Rendering pages for OCR…")
    images = render_pdf_page_pngs(data, max_pages=max_pages)
    warnings: list[str] = []
    if len(images) >= max_pages:
        warnings.append(
            f"OCR limited to first {max_pages} pages for demo cost control."
        )

    stage("Running vision OCR…")
    page_texts: list[str] = []
    for idx, png in enumerate(images):
        b64 = base64.standard_b64encode(png).decode("ascii")
        content = [
            {
                "type": "text",
                "text": f"Extract all readable text from page {idx + 1} of this document.",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            },
        ]
        text = _chat_vision_text(client, model=model, content=content)
        if text.strip():
            page_texts.append(text.strip())

    joined = "\n\n".join(page_texts).strip()
    if not joined:
        raise ExtractionError(
            "Vision OCR found no readable text. The scan may be too low-quality."
        )
    return joined, warnings


def _chat_vision_text(
    client: OpenAI,
    *,
    model: str,
    content: list[dict],
) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_OCR},
        {"role": "user", "content": content},
    ]
    retryable = (RateLimitError, APITimeoutError, APIConnectionError)
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=4096,
            )
            text = (completion.choices[0].message.content or "").strip()
            return text
        except retryable as exc:
            last_error = exc
            logger.warning("Vision OCR transient error (attempt %s): %s", attempt + 1, exc)
            if attempt < MAX_RETRIES:
                time.sleep(BASE_DELAY_SECONDS * (2**attempt))
                continue
            break
        except AuthenticationError as exc:
            raise OpenAIClientError(
                "Invalid OPENAI_API_KEY. Update .env or Streamlit secrets with a valid key."
            ) from exc
        except APIError as exc:
            logger.exception("Vision OCR API error")
            raise OpenAIClientError(
                "The AI service returned an error during OCR. Try again later."
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected vision OCR error")
            raise OpenAIClientError(
                "Could not complete vision OCR. Please try again."
            ) from exc

    raise OpenAIClientError(
        "The AI service is busy or timed out during OCR. Please try again in a moment."
    ) from last_error

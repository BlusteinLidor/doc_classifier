"""Orchestrate PDF extraction and multi-step structured AI parsing."""

from __future__ import annotations

import logging
import os
import time
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI

from doc_intel.errors import ExtractionError, OpenAIClientError, PDFError
from doc_intel.extractor import extract_pdf_text
from doc_intel.models import (
    ContractExtraction,
    DocType,
    DocumentKindResult,
    InvoiceExtraction,
    ProcessingResult,
    ReceiptExtraction,
    StructuredExtraction,
)
from doc_intel.normalize import normalize_structured
from doc_intel.ocr import vision_ocr_pdf
from doc_intel.openai_client import DEFAULT_MODEL, create_client, parse_structured
from doc_intel.prompts import (
    SYSTEM_CLASSIFY,
    SYSTEM_CONTRACT,
    SYSTEM_INVOICE,
    SYSTEM_RECEIPT,
    build_classify_user_message,
    build_extraction_user_message,
)

logger = logging.getLogger(__name__)

CLASSIFY_EXCERPT_CHARS = 4_000
ProgressCb = Callable[[str], None] | None


def _get_api_key() -> str:
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise OpenAIClientError(
            "Missing OPENAI_API_KEY. Set it in .env locally or in Streamlit secrets."
        )
    return key


def _stage(on_stage: ProgressCb, message: str) -> None:
    if on_stage is not None:
        on_stage(message)


def process_pdf_bytes(
    filename: str,
    data: bytes,
    *,
    model: str = DEFAULT_MODEL,
    on_stage: ProgressCb = None,
    enable_ocr: bool = True,
) -> ProcessingResult:
    """
    Extract text from PDF bytes, classify document kind, then parse structured fields.

    Returns ProcessingResult with success=False and error_message on recoverable failures.
    """
    started = time.perf_counter()
    warnings: list[str] = []
    used_ocr = False
    client: OpenAI | None = None

    def _latency_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    def _fail(
        message: str,
        *,
        preview: str = "",
        doc_type: DocType | None = None,
        classification_note: str | None = None,
    ) -> ProcessingResult:
        return ProcessingResult(
            filename=filename,
            success=False,
            doc_type=doc_type,
            classification_confidence_note=classification_note,
            raw_text_preview=preview,
            error_message=message,
            warnings=warnings,
            latency_ms=_latency_ms(),
            used_ocr=used_ocr,
        )

    def _ensure_client() -> OpenAI:
        nonlocal client
        if client is None:
            client = create_client(_get_api_key())
        return client

    # --- Text extraction (with optional vision OCR fallback) ---
    text = ""
    try:
        _stage(on_stage, "Reading PDF text…")
        outcome = extract_pdf_text(data)
        text = outcome.text
        warnings.extend(outcome.warnings)
    except PDFError as exc:
        logger.info("PDF error for %s: %s", filename, exc)
        return _fail(str(exc))
    except ExtractionError as extract_exc:
        if not enable_ocr:
            return _fail(str(extract_exc))
        try:
            text, ocr_warnings = vision_ocr_pdf(
                _ensure_client(), data, model=model, on_stage=on_stage
            )
            warnings.extend(ocr_warnings)
            warnings.append(
                "Used vision OCR because the PDF had no extractable text layer."
            )
            used_ocr = True
        except OpenAIClientError as exc:
            return _fail(f"{extract_exc} OCR fallback failed: {exc}")
        except (PDFError, ExtractionError) as exc:
            return _fail(str(exc))

    preview = text[:2000] + ("…" if len(text) > 2000 else "")

    try:
        api_client = _ensure_client()
    except OpenAIClientError as exc:
        return _fail(str(exc), preview=preview)

    # --- Classification ---
    _stage(on_stage, "Classifying document type…")
    excerpt = text[:CLASSIFY_EXCERPT_CHARS]
    classify_user = build_classify_user_message(filename, excerpt)

    try:
        kind_result = parse_structured(
            api_client,
            model=model,
            system_prompt=SYSTEM_CLASSIFY,
            user_message=classify_user,
            response_model=DocumentKindResult,
        )
    except OpenAIClientError as exc:
        return _fail(str(exc), preview=preview)

    doc_type = kind_result.kind
    classification_note = kind_result.confidence_note

    if doc_type == "unknown":
        _stage(on_stage, "Document type unknown — skipping field extraction.")
        return ProcessingResult(
            filename=filename,
            success=True,
            doc_type="unknown",
            classification_confidence_note=classification_note,
            structured=None,
            raw_text_preview=preview,
            warnings=warnings
            + ["Classified as unknown; structured extraction was skipped."],
            latency_ms=_latency_ms(),
            used_ocr=used_ocr,
        )

    # --- Type-specific extraction ---
    _stage(on_stage, "Extracting structured fields…")
    extraction_user = build_extraction_user_message(filename, text)
    schema_map: dict[str, tuple[type[StructuredExtraction], str]] = {
        "invoice": (InvoiceExtraction, SYSTEM_INVOICE),
        "contract": (ContractExtraction, SYSTEM_CONTRACT),
        "receipt": (ReceiptExtraction, SYSTEM_RECEIPT),
    }
    response_model, system_prompt = schema_map[doc_type]

    try:
        structured = parse_structured(
            api_client,
            model=model,
            system_prompt=system_prompt,
            user_message=extraction_user,
            response_model=response_model,
        )
        structured = normalize_structured(structured)
    except OpenAIClientError as exc:
        return _fail(
            str(exc),
            preview=preview,
            doc_type=doc_type,
            classification_note=classification_note,
        )

    _stage(on_stage, "Done.")
    return ProcessingResult(
        filename=filename,
        success=True,
        doc_type=doc_type,
        classification_confidence_note=classification_note,
        structured=structured,
        raw_text_preview=preview,
        warnings=warnings,
        latency_ms=_latency_ms(),
        used_ocr=used_ocr,
    )

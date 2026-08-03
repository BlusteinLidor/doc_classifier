"""Orchestrate PDF extraction and two-step structured AI parsing."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from doc_intel.errors import ExtractionError, OpenAIClientError, PDFError
from doc_intel.extractor import extract_pdf_text
from doc_intel.models import (
    ContractExtraction,
    DocumentKindResult,
    InvoiceExtraction,
    ProcessingResult,
)
from doc_intel.openai_client import DEFAULT_MODEL, create_client, parse_structured
from doc_intel.prompts import (
    SYSTEM_CLASSIFY,
    SYSTEM_CONTRACT,
    SYSTEM_INVOICE,
    build_classify_user_message,
    build_extraction_user_message,
)

logger = logging.getLogger(__name__)

CLASSIFY_EXCERPT_CHARS = 4_000


def _get_api_key() -> str:
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise OpenAIClientError(
            "Missing OPENAI_API_KEY. Set it in .env locally or in Streamlit secrets."
        )
    return key


def process_pdf_bytes(
    filename: str,
    data: bytes,
    *,
    model: str = DEFAULT_MODEL,
) -> ProcessingResult:
    """
    Extract text from PDF bytes, classify document kind, then parse structured fields.

    Returns ProcessingResult with success=False and error_message on recoverable failures.
    """
    warnings: list[str] = []

    try:
        outcome = extract_pdf_text(data)
        text = outcome.text
        warnings.extend(outcome.warnings)
    except PDFError as exc:
        logger.info("PDF error for %s: %s", filename, exc)
        return ProcessingResult(
            filename=filename,
            success=False,
            error_message=str(exc),
            warnings=warnings,
        )
    except ExtractionError as exc:
        logger.info("Extraction error for %s: %s", filename, exc)
        return ProcessingResult(
            filename=filename,
            success=False,
            error_message=str(exc),
            raw_text_preview="",
            warnings=warnings,
        )

    preview = text[:2000] + ("…" if len(text) > 2000 else "")

    try:
        api_key = _get_api_key()
        client = create_client(api_key)
    except OpenAIClientError as exc:
        return ProcessingResult(
            filename=filename,
            success=False,
            raw_text_preview=preview,
            error_message=str(exc),
            warnings=warnings,
        )

    excerpt = text[:CLASSIFY_EXCERPT_CHARS]
    classify_user = build_classify_user_message(filename, excerpt)

    try:
        kind_result = parse_structured(
            client,
            model=model,
            system_prompt=SYSTEM_CLASSIFY,
            user_message=classify_user,
            response_model=DocumentKindResult,
        )
    except OpenAIClientError as exc:
        return ProcessingResult(
            filename=filename,
            success=False,
            raw_text_preview=preview,
            error_message=str(exc),
            warnings=warnings,
        )

    doc_type = kind_result.kind
    extraction_user = build_extraction_user_message(filename, text)

    try:
        if doc_type == "invoice":
            structured = parse_structured(
                client,
                model=model,
                system_prompt=SYSTEM_INVOICE,
                user_message=extraction_user,
                response_model=InvoiceExtraction,
            )
        else:
            structured = parse_structured(
                client,
                model=model,
                system_prompt=SYSTEM_CONTRACT,
                user_message=extraction_user,
                response_model=ContractExtraction,
            )
    except OpenAIClientError as exc:
        return ProcessingResult(
            filename=filename,
            success=False,
            doc_type=doc_type,
            raw_text_preview=preview,
            error_message=str(exc),
            warnings=warnings,
        )

    return ProcessingResult(
        filename=filename,
        success=True,
        doc_type=doc_type,
        structured=structured,
        raw_text_preview=preview,
        warnings=warnings,
    )

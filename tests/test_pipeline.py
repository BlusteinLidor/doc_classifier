"""Pipeline tests with mocked OpenAI structured parse."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import fitz
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from doc_intel.errors import ExtractionError  # noqa: E402
from doc_intel.models import (  # noqa: E402
    ContractExtraction,
    DocumentKindResult,
    InvoiceExtraction,
    ReceiptExtraction,
)
from doc_intel.pipeline import process_pdf_bytes  # noqa: E402


def _make_text_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture()
def invoice_pdf() -> bytes:
    return _make_text_pdf(
        "INVOICE\nVendor: Acme\nInvoice number: INV-1\n"
        "Total amount: 100.00 USD\nDate: 2025-03-15"
    )


def test_process_invoice_surfaces_confidence_and_latency(
    invoice_pdf: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    calls: list[str] = []

    def fake_parse(
        client: Any,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        response_model: type,
    ) -> Any:
        if response_model is DocumentKindResult:
            return DocumentKindResult(
                kind="invoice",
                confidence_note="Contains invoice number and total due",
            )
        if response_model is InvoiceExtraction:
            return InvoiceExtraction(
                vendor="Acme",
                invoice_number="INV-1",
                total_amount="100.00 USD",
                invoice_date="2025-03-15",
            )
        raise AssertionError(f"Unexpected model {response_model}")

    stages: list[str] = []

    with (
        patch("doc_intel.pipeline.create_client", return_value=MagicMock()),
        patch("doc_intel.pipeline.parse_structured", side_effect=fake_parse),
    ):
        result = process_pdf_bytes(
            "inv.pdf",
            invoice_pdf,
            on_stage=stages.append,
            enable_ocr=False,
        )

    assert result.success
    assert result.doc_type == "invoice"
    assert result.classification_confidence_note == "Contains invoice number and total due"
    assert result.latency_ms is not None and result.latency_ms >= 0
    assert isinstance(result.structured, InvoiceExtraction)
    assert result.structured.total_amount_value == pytest.approx(100.0)
    assert result.structured.invoice_date_iso == "2025-03-15"
    assert any("Classifying" in s for s in stages)
    assert any("Extracting" in s for s in stages)


def test_process_unknown_skips_extraction(
    invoice_pdf: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_parse(
        client: Any,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        response_model: type,
    ) -> Any:
        if response_model is DocumentKindResult:
            return DocumentKindResult(kind="unknown", confidence_note="Random memo")
        raise AssertionError("Should not extract fields for unknown")

    with (
        patch("doc_intel.pipeline.create_client", return_value=MagicMock()),
        patch("doc_intel.pipeline.parse_structured", side_effect=fake_parse),
    ):
        result = process_pdf_bytes("memo.pdf", invoice_pdf, enable_ocr=False)

    assert result.success
    assert result.doc_type == "unknown"
    assert result.structured is None
    assert any("unknown" in w.lower() for w in result.warnings)


def test_process_receipt(invoice_pdf: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_parse(
        client: Any,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        response_model: type,
    ) -> Any:
        if response_model is DocumentKindResult:
            return DocumentKindResult(kind="receipt", confidence_note="Sales receipt")
        if response_model is ReceiptExtraction:
            return ReceiptExtraction(
                merchant="Harbor Corner Market",
                total_amount="20.84 USD",
                receipt_date="2025-06-18",
            )
        raise AssertionError(f"Unexpected {response_model}")

    with (
        patch("doc_intel.pipeline.create_client", return_value=MagicMock()),
        patch("doc_intel.pipeline.parse_structured", side_effect=fake_parse),
    ):
        result = process_pdf_bytes("rcp.pdf", invoice_pdf, enable_ocr=False)

    assert result.success
    assert result.doc_type == "receipt"
    assert isinstance(result.structured, ReceiptExtraction)
    assert result.structured.total_amount_value == pytest.approx(20.84)


def test_process_contract(invoice_pdf: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_parse(
        client: Any,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        response_model: type,
    ) -> Any:
        if response_model is DocumentKindResult:
            return DocumentKindResult(kind="contract")
        if response_model is ContractExtraction:
            return ContractExtraction(
                title="Service Agreement",
                effective_date="2025-01-01",
                end_date="2025-12-31",
            )
        raise AssertionError(f"Unexpected {response_model}")

    with (
        patch("doc_intel.pipeline.create_client", return_value=MagicMock()),
        patch("doc_intel.pipeline.parse_structured", side_effect=fake_parse),
    ):
        result = process_pdf_bytes("ctr.pdf", invoice_pdf, enable_ocr=False)

    assert result.success and result.doc_type == "contract"
    assert isinstance(result.structured, ContractExtraction)
    assert result.structured.effective_date_iso == "2025-01-01"


def test_ocr_fallback_when_no_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    # Empty-ish: PDF with no text layer
    doc = fitz.open()
    doc.new_page()
    empty_pdf = doc.tobytes()
    doc.close()

    def fake_parse(
        client: Any,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        response_model: type,
    ) -> Any:
        if response_model is DocumentKindResult:
            return DocumentKindResult(kind="invoice", confidence_note="OCR invoice")
        if response_model is InvoiceExtraction:
            return InvoiceExtraction(vendor="Scanned Co", total_amount="50")
        raise AssertionError(str(response_model))

    with (
        patch("doc_intel.pipeline.create_client", return_value=MagicMock()),
        patch("doc_intel.pipeline.parse_structured", side_effect=fake_parse),
        patch(
            "doc_intel.pipeline.vision_ocr_pdf",
            return_value=("INVOICE\nVendor: Scanned Co\nTotal: 50", ["ocr limited"]),
        ),
        patch(
            "doc_intel.pipeline.extract_pdf_text",
            side_effect=ExtractionError("No readable text"),
        ),
    ):
        result = process_pdf_bytes("scan.pdf", empty_pdf, enable_ocr=True)

    assert result.success
    assert result.used_ocr is True
    assert any("vision OCR" in w for w in result.warnings)

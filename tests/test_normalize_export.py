"""Unit tests for amount/date normalization and export helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from doc_intel.export import (  # noqa: E402
    branded_export_basename,
    results_to_csv_bytes,
    results_to_json_bytes,
    single_result_to_json_bytes,
)
from doc_intel.models import (  # noqa: E402
    ContractExtraction,
    InvoiceExtraction,
    ProcessingResult,
    ReceiptExtraction,
)
from doc_intel.normalize import (  # noqa: E402
    normalize_structured,
    parse_amount_value,
    parse_date_iso,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2104.83 USD", 2104.83),
        ("₪4,797", 4797.0),
        ("1.234,56", 1234.56),
        ("1,234.56", 1234.56),
        ("total 20.84", 20.84),
        (None, None),
        ("", None),
    ],
)
def test_parse_amount_value(raw: str | None, expected: float | None) -> None:
    result = parse_amount_value(raw)
    if expected is None:
        assert result is None
    else:
        assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2025-03-15", "2025-03-15"),
        ("12/01/2025", "2025-01-12"),
        ("15.03.2025", "2025-03-15"),
        ("not a date", None),
        (None, None),
    ],
)
def test_parse_date_iso(raw: str | None, expected: str | None) -> None:
    assert parse_date_iso(raw) == expected


def test_normalize_invoice_fills_numeric_and_iso() -> None:
    inv = InvoiceExtraction(
        vendor="Acme",
        total_amount="1,250.50 USD",
        invoice_date="15/03/2025",
    )
    out = normalize_structured(inv)
    assert isinstance(out, InvoiceExtraction)
    assert out.total_amount_value == pytest.approx(1250.50)
    assert out.invoice_date_iso == "2025-03-15"


def test_normalize_contract_dates() -> None:
    ctr = ContractExtraction(
        title="Agreement",
        effective_date="2025-01-01",
        end_date="31/12/2025",
    )
    out = normalize_structured(ctr)
    assert isinstance(out, ContractExtraction)
    assert out.effective_date_iso == "2025-01-01"
    assert out.end_date_iso == "2025-12-31"


def test_normalize_receipt() -> None:
    rcp = ReceiptExtraction(merchant="Shop", total_amount="20.84", receipt_date="2025-06-18")
    out = normalize_structured(rcp)
    assert isinstance(out, ReceiptExtraction)
    assert out.total_amount_value == pytest.approx(20.84)
    assert out.receipt_date_iso == "2025-06-18"


def test_export_json_and_csv_include_confidence() -> None:
    results = [
        ProcessingResult(
            filename="a.pdf",
            success=True,
            doc_type="invoice",
            classification_confidence_note="Has invoice number and total due",
            structured=InvoiceExtraction(
                vendor="Northwind",
                total_amount="100",
                total_amount_value=100.0,
                currency="USD",
            ),
            latency_ms=1234,
            used_ocr=False,
        ),
        ProcessingResult(
            filename="b.pdf",
            success=True,
            doc_type="unknown",
            classification_confidence_note="Unrelated memo",
            warnings=["Classified as unknown; structured extraction was skipped."],
            latency_ms=500,
        ),
    ]
    payload = json.loads(results_to_json_bytes(results).decode("utf-8"))
    assert payload[0]["classification_confidence_note"]
    assert payload[0]["latency_ms"] == 1234
    assert payload[1]["doc_type"] == "unknown"

    one = json.loads(single_result_to_json_bytes(results[0]).decode("utf-8"))
    assert one["filename"] == "a.pdf"

    csv_text = results_to_csv_bytes(results).decode("utf-8-sig")
    assert "classification_confidence_note" in csv_text
    assert "extracted_vendor" in csv_text
    assert "Northwind" in csv_text
    assert branded_export_basename().startswith("extraction_")


def test_document_kind_accepts_receipt_and_unknown() -> None:
    from doc_intel.models import DocumentKindResult

    assert DocumentKindResult(kind="receipt").kind == "receipt"
    assert DocumentKindResult(kind="unknown").kind == "unknown"

"""Post-extraction normalization for amounts and dates."""

from __future__ import annotations

import re

from doc_intel.models import (
    ContractExtraction,
    InvoiceExtraction,
    ReceiptExtraction,
    StructuredExtraction,
)

_ISO_DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})-(\d{1,2})-(\d{1,2})\b")
_DMY_SLASH_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](20\d{2}|19\d{2})\b")

# Longest number-like runs after stripping currency symbols.
_amount_chunk_re = re.compile(r"[-+]?(?:\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)")


def parse_amount_value(raw: str | None) -> float | None:
    """Best-effort parse of a monetary string to float."""
    if not raw or not str(raw).strip():
        return None
    text = (
        str(raw)
        .strip()
        .replace("₪", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
    )
    chunks = list(_amount_chunk_re.finditer(text))
    if not chunks:
        return None
    # Prefer the longest match; if ties, take the last (usually the total).
    best = max(chunks, key=lambda m: (len(m.group(0)), m.start()))
    token = best.group(0).replace(" ", "").strip()
    if not token:
        return None

    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            # 1.234,56 European
            token = token.replace(".", "").replace(",", ".")
        else:
            # 1,234.56 US
            token = token.replace(",", "")
    elif "," in token:
        parts = token.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            token = f"{parts[0].replace('.', '')}.{parts[1]}"
        else:
            token = token.replace(",", "")
    elif token.count(".") > 1:
        # 1.234.567 European thousands without decimals
        token = token.replace(".", "")

    try:
        return float(token)
    except ValueError:
        return None


def parse_date_iso(raw: str | None) -> str | None:
    """Best-effort parse to YYYY-MM-DD."""
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()

    m = _ISO_DATE_RE.search(text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_ymd(y, mo, d):
            return f"{y:04d}-{mo:02d}-{d:02d}"

    m = _DMY_SLASH_RE.search(text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        # Prefer DMY when day > 12
        if d > 12 and _valid_ymd(y, mo, d):
            return f"{y:04d}-{mo:02d}-{d:02d}"
        if mo > 12 and _valid_ymd(y, d, mo):
            return f"{y:04d}-{d:02d}-{mo:02d}"
        # Ambiguous: assume DMY (IL-friendly)
        if _valid_ymd(y, mo, d):
            return f"{y:04d}-{mo:02d}-{d:02d}"

    return None


def _valid_ymd(year: int, month: int, day: int) -> bool:
    if month < 1 or month > 12 or day < 1 or day > 31:
        return False
    if month in (4, 6, 9, 11) and day > 30:
        return False
    if month == 2 and day > 29:
        return False
    return 1900 <= year <= 2100


def normalize_structured(obj: StructuredExtraction) -> StructuredExtraction:
    """Fill numeric amount and ISO date fields when missing and parseable."""
    if isinstance(obj, InvoiceExtraction):
        data = obj.model_dump()
        if data.get("total_amount_value") is None:
            data["total_amount_value"] = parse_amount_value(data.get("total_amount"))
        if not data.get("invoice_date_iso"):
            data["invoice_date_iso"] = parse_date_iso(data.get("invoice_date"))
        return InvoiceExtraction.model_validate(data)

    if isinstance(obj, ContractExtraction):
        data = obj.model_dump()
        if not data.get("effective_date_iso"):
            data["effective_date_iso"] = parse_date_iso(data.get("effective_date"))
        if not data.get("end_date_iso"):
            data["end_date_iso"] = parse_date_iso(data.get("end_date"))
        return ContractExtraction.model_validate(data)

    if isinstance(obj, ReceiptExtraction):
        data = obj.model_dump()
        if data.get("total_amount_value") is None:
            data["total_amount_value"] = parse_amount_value(data.get("total_amount"))
        if not data.get("receipt_date_iso"):
            data["receipt_date_iso"] = parse_date_iso(data.get("receipt_date"))
        return ReceiptExtraction.model_validate(data)

    return obj

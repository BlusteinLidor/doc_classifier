"""Post-extraction normalization for amounts and dates."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from doc_intel.models import StructuredExtraction

_ISO_DATE_RE = re.compile(r"\b(20\d{2}|19\d{2})-(\d{1,2})-(\d{1,2})\b")
_DMY_SLASH_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](20\d{2}|19\d{2})\b")

# Longest number-like runs after stripping currency symbols.
_amount_chunk_re = re.compile(r"[-+]?(?:\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)")

# ISO date field endings map to display field by stripping _iso.
_ISO_SUFFIX = "_iso"
_VALUE_SUFFIX = "_value"

_SYMBOL_BY_CODE = {
    "USD": "$",
    "ILS": "₪",
    "EUR": "€",
    "GBP": "£",
}

_CURRENCY_IN_AMOUNT: dict[str, re.Pattern[str]] = {
    "USD": re.compile(r"\$|USD|US\$", re.I),
    "ILS": re.compile(r"₪|ILS|NIS|ש[\"״']?\s*ח", re.I),
    "EUR": re.compile(r"€|EUR", re.I),
    "GBP": re.compile(r"£|GBP", re.I),
}

_CURRENCY_TOKEN_RE = re.compile(
    r"₪|\$|€|£|\bUSD\b|\bUS\$\b|\bILS\b|\bNIS\b|\bEUR\b|\bGBP\b|ש[\"״']?\s*ח",
    re.I,
)

_MONEY_AMOUNT_KEYS = (
    "total_amount",
    "amount_due",
    "amount",
    "subtotal",
    "tax_amount",
    "net_pay",
    "gross_pay",
    "closing_balance",
    "opening_balance",
    "unit_price",
    "line_total",
)


def detect_currency_code(*texts: object | None) -> str | None:
    """Best-effort currency code from free text."""
    for raw in texts:
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        if "₪" in text or re.search(r"\bILS\b|\bNIS\b|ש[\"״']?\s*ח", text, re.I):
            return "ILS"
        if "$" in text or re.search(r"\bUSD\b|\bUS\$\b", text, re.I):
            return "USD"
        if "€" in text or re.search(r"\bEUR\b", text, re.I):
            return "EUR"
        if "£" in text or re.search(r"\bGBP\b", text, re.I):
            return "GBP"
        code = re.sub(r"[^A-Za-z]", "", text).upper()
        if code in _SYMBOL_BY_CODE:
            return code
    return None


def strip_currency_markers(amount: str) -> str:
    """Remove currency symbols/codes; collapse whitespace."""
    cleaned = _CURRENCY_TOKEN_RE.sub(" ", amount)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Clean trailing/leading punctuation left after stripping codes
    cleaned = cleaned.strip(" ·-/")
    return cleaned


def amount_includes_currency(amount: str, currency: str) -> bool:
    """True when *amount* already shows the same currency (code or symbol)."""
    amt = amount.strip()
    cur = currency.strip()
    if not amt or not cur:
        return False
    if cur.upper() in amt.upper() or cur in amt:
        return True
    code = re.sub(r"[^A-Za-z]", "", cur).upper() or detect_currency_code(cur) or ""
    pattern = _CURRENCY_IN_AMOUNT.get(code)
    if pattern and pattern.search(amt):
        return True
    if ("₪" in cur or code == "ILS") and "₪" in amt:
        return True
    if ("$" in cur or code == "USD") and "$" in amt:
        return True
    return bool(re.search(rf"(?:^|\s){re.escape(cur)}(?:\s|$)", amt, re.I))


def format_money_display(
    amount: object | None,
    currency: object | None = None,
) -> str:
    """
    Single clean money string — prefer symbol once (e.g. ₪4,797 or $2,104.83).
    Never emits 'USD USD' or '₪4797 ILS'.
    """
    amt = "" if amount is None else str(amount).strip()
    cur = "" if currency is None else str(currency).strip()
    if not amt and not cur:
        return ""
    code = detect_currency_code(cur, amt)
    num = strip_currency_markers(amt) if amt else ""
    if not num:
        return _SYMBOL_BY_CODE.get(code or "", code or cur)
    if code and code in _SYMBOL_BY_CODE:
        return f"{_SYMBOL_BY_CODE[code]}{num}"
    if code:
        return f"{num} {code}"
    return num


def compose_amount_with_currency(
    amount: object | None,
    currency: object | None,
) -> str:
    """Combine amount + currency once (prefer symbol form)."""
    return format_money_display(amount, currency)


def parse_amount_value(raw: str | None) -> float | None:
    """Best-effort parse of a monetary string to float."""
    if not raw or not str(raw).strip():
        return None
    text = strip_currency_markers(str(raw).strip())
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


def _fill_iso_and_amounts(data: dict[str, Any]) -> dict[str, Any]:
    """For any field ending in _iso or _value, fill from sibling display field."""
    keys = list(data.keys())
    for key in keys:
        if key.endswith(_ISO_SUFFIX) and not data.get(key):
            source = key[: -len(_ISO_SUFFIX)]
            if source in data:
                data[key] = parse_date_iso(
                    data[source] if isinstance(data[source], str) else None
                )
        elif key.endswith(_VALUE_SUFFIX) and data.get(key) is None:
            source = key[: -len(_VALUE_SUFFIX)]
            if source in data and data[source] is not None:
                raw = data[source]
                data[key] = parse_amount_value(str(raw) if raw is not None else None)
    return data


def _normalize_money_display(data: dict[str, Any]) -> dict[str, Any]:
    """Rewrite money strings so currency appears once (prefer symbol form)."""
    code = detect_currency_code(
        data.get("currency"),
        *(data.get(k) for k in _MONEY_AMOUNT_KEYS if data.get(k) is not None),
    )
    if code:
        data["currency"] = code

    for key in _MONEY_AMOUNT_KEYS:
        if key not in data or data[key] is None:
            continue
        raw = data[key]
        if not isinstance(raw, (str, int, float)):
            continue
        data[key] = format_money_display(raw, code or data.get("currency"))

    # Nested line items / named amounts
    for list_key in ("line_items", "items", "deductions", "amounts_mentioned"):
        rows = data.get(list_key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            for cell in ("unit_price", "line_total", "amount", "total"):
                if row.get(cell) is not None and isinstance(
                    row[cell], (str, int, float)
                ):
                    row[cell] = format_money_display(
                        row[cell], code or data.get("currency")
                    )
    return data


def normalize_structured(obj: StructuredExtraction) -> StructuredExtraction:
    """Fill numeric amount and ISO date fields when missing and parseable."""
    if not isinstance(obj, BaseModel):
        return obj
    data = _fill_iso_and_amounts(obj.model_dump())
    data = _normalize_money_display(data)
    return type(obj).model_validate(data)  # type: ignore[return-value]

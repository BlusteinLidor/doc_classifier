"""Serialize processing results to JSON and CSV (UTF-8)."""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from typing import Any

from doc_intel.models import ProcessingResult

# Stable column order for mixed batches (helps Excel pivot).
_STABLE_EXTRACTED_KEYS = [
    "vendor",
    "merchant",
    "invoice_number",
    "receipt_number",
    "title",
    "buyer",
    "invoice_date",
    "invoice_date_iso",
    "receipt_date",
    "receipt_date_iso",
    "effective_date",
    "effective_date_iso",
    "end_date",
    "end_date_iso",
    "total_amount",
    "total_amount_value",
    "currency",
    "tax_id",
    "payment_method",
    "governing_law",
    "parties",
    "key_terms_summary",
    "line_items",
    "items",
    "confidence_notes",
]


def _flatten_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def branded_export_basename(prefix: str = "extraction") -> str:
    """Return filename stem like extraction_2026-08-04."""
    return f"{prefix}_{date.today().isoformat()}"


def results_to_json_bytes(results: list[ProcessingResult]) -> bytes:
    payload = [r.model_dump(mode="json") for r in results]
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def single_result_to_json_bytes(result: ProcessingResult) -> bytes:
    return json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2).encode(
        "utf-8"
    )


def results_to_csv_bytes(
    results: list[ProcessingResult],
    *,
    utf8_bom: bool = True,
    preview_max_chars: int = 2000,
) -> bytes:
    """Flatten each result to one CSV row; nested fields JSON-encoded. BOM helps Excel with Hebrew."""
    rows: list[dict[str, str]] = []
    for r in results:
        row: dict[str, str] = {
            "filename": r.filename,
            "success": str(r.success).lower(),
            "doc_type": r.doc_type or "",
            "classification_confidence_note": r.classification_confidence_note or "",
            "error_message": r.error_message or "",
            "warnings": " | ".join(r.warnings),
            "latency_ms": "" if r.latency_ms is None else str(r.latency_ms),
            "used_ocr": str(r.used_ocr).lower(),
        }
        preview = r.raw_text_preview.replace("\r\n", "\n")
        if len(preview) > preview_max_chars:
            preview = preview[:preview_max_chars] + "…"
        row["raw_text_preview"] = preview
        if r.structured is not None:
            for key, val in r.structured.model_dump().items():
                row[f"extracted_{key}"] = _flatten_value(val)
        rows.append(row)

    base = [
        "filename",
        "success",
        "doc_type",
        "classification_confidence_note",
        "error_message",
        "warnings",
        "latency_ms",
        "used_ocr",
        "raw_text_preview",
    ]
    if not rows:
        fieldnames = base
    else:
        all_keys: set[str] = set()
        for row in rows:
            all_keys.update(row.keys())
        stable_extras = [
            f"extracted_{k}"
            for k in _STABLE_EXTRACTED_KEYS
            if f"extracted_{k}" in all_keys
        ]
        other_extras = sorted(
            k for k in all_keys if k not in base and k not in stable_extras
        )
        fieldnames = [k for k in base if k in all_keys] + stable_extras + other_extras

    buf = io.StringIO()
    if utf8_bom:
        buf.write("\ufeff")
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue().encode("utf-8")

"""Serialize processing results to JSON and CSV (UTF-8)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from doc_intel.models import ProcessingResult


def _flatten_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def results_to_json_bytes(results: list[ProcessingResult]) -> bytes:
    payload = [r.model_dump(mode="json") for r in results]
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


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
            "error_message": r.error_message or "",
            "warnings": " | ".join(r.warnings),
        }
        preview = r.raw_text_preview.replace("\r\n", "\n")
        if len(preview) > preview_max_chars:
            preview = preview[:preview_max_chars] + "…"
        row["raw_text_preview"] = preview
        if r.structured is not None:
            for key, val in r.structured.model_dump().items():
                row[f"extracted_{key}"] = _flatten_value(val)
        rows.append(row)

    if not rows:
        fieldnames = [
            "filename",
            "success",
            "doc_type",
            "error_message",
            "warnings",
            "raw_text_preview",
        ]
    else:
        base = [
            "filename",
            "success",
            "doc_type",
            "error_message",
            "warnings",
            "raw_text_preview",
        ]
        all_keys: set[str] = set()
        for row in rows:
            all_keys.update(row.keys())
        extras = sorted(k for k in all_keys if k not in base)
        fieldnames = [k for k in base if k in all_keys] + extras

    buf = io.StringIO()
    if utf8_bom:
        buf.write("\ufeff")
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue().encode("utf-8")

"""Persistence for automatic ingestion outputs and logs."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from doc_intel.models import ProcessingResult


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_auto_result(output_dir: str, result: ProcessingResult) -> None:
    base = Path(output_dir)
    _ensure_dir(base)
    stem = Path(result.filename).stem
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = base / f"{stem}_{ts}.json"
    json_path.write_text(
        json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    csv_path = base / "auto_results.csv"
    row = {
        "timestamp_utc": ts,
        "filename": result.filename,
        "success": str(result.success).lower(),
        "doc_type": result.doc_type or "",
        "error_message": result.error_message or "",
        "warnings": " | ".join(result.warnings),
        "latency_ms": str(result.document_metadata.latency_ms)
        if result.document_metadata and result.document_metadata.latency_ms is not None
        else "",
        "request_id": result.request_id or "",
    }
    write_header = not csv_path.exists()
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

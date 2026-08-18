"""Simple in-memory metrics helpers."""

from __future__ import annotations

from dataclasses import dataclass

from doc_intel.models import ProcessingResult


@dataclass(frozen=True)
class BatchSummary:
    total: int
    success: int
    failed: int
    invoices: int
    contracts: int
    avg_latency_ms: int


def summarize_results(results: list[ProcessingResult]) -> BatchSummary:
    total = len(results)
    success = sum(1 for r in results if r.success)
    failed = total - success
    invoices = sum(1 for r in results if r.doc_type == "invoice")
    contracts = sum(1 for r in results if r.doc_type == "contract")
    latencies = [
        r.document_metadata.latency_ms
        for r in results
        if r.document_metadata and r.document_metadata.latency_ms is not None
    ]
    avg_latency_ms = int(sum(latencies) / len(latencies)) if latencies else 0
    return BatchSummary(
        total=total,
        success=success,
        failed=failed,
        invoices=invoices,
        contracts=contracts,
        avg_latency_ms=avg_latency_ms,
    )

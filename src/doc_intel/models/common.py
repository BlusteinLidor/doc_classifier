"""Shared Pydantic models for document extraction."""

from __future__ import annotations

from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    page_count: int | None = None
    extraction_mode: str | None = None
    token_usage_total: int | None = None
    latency_ms: int | None = None

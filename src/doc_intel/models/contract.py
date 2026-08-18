"""Contract-specific structured extraction models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContractParty(BaseModel):
    name: str | None = None
    role: str | None = Field(default=None, description="e.g. employer, contractor, buyer.")


class ContractExtraction(BaseModel):
    title: str | None = None
    parties: list[ContractParty] = Field(default_factory=list)
    effective_date: str | None = None
    end_date: str | None = None
    governing_law: str | None = None
    key_terms_summary: str | None = Field(
        default=None,
        description="Brief summary of main obligations or terms.",
    )
    confidence_notes: str | None = None
    normalized_effective_date: str | None = None
    normalized_end_date: str | None = None
    party_count: int | None = None

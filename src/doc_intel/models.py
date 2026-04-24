"""Pydantic schemas for structured extraction and UI transport."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DocumentKindResult(BaseModel):
    """First-step classification from a text excerpt."""

    kind: Literal["invoice", "contract"] = Field(
        description="Whether the document is primarily an invoice or a contract."
    )
    confidence_note: str | None = Field(
        default=None,
        description="Short optional note on why this classification was chosen.",
    )


class InvoiceLineItem(BaseModel):
    description: str | None = None
    quantity: str | None = None
    unit_price: str | None = None
    line_total: str | None = None


class InvoiceExtraction(BaseModel):
    vendor: str | None = Field(default=None, description="Supplier or vendor name.")
    invoice_number: str | None = None
    invoice_date: str | None = Field(
        default=None,
        description="Invoice date as shown (any locale, e.g. Hebrew calendar text).",
    )
    total_amount: str | None = None
    currency: str | None = Field(
        default=None,
        description="Currency code or symbol, e.g. ILS, USD, ₪.",
    )
    tax_id: str | None = Field(
        default=None,
        description="VAT or tax identification if present.",
    )
    buyer: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence_notes: str | None = None


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


class ProcessingResult(BaseModel):
    """Per-file outcome for Streamlit and export."""

    filename: str
    success: bool
    doc_type: Literal["invoice", "contract"] | None = None
    structured: InvoiceExtraction | ContractExtraction | None = None
    raw_text_preview: str = ""
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)

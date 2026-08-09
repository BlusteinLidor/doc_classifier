"""Pydantic schemas for structured extraction and UI transport."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DocType = Literal["invoice", "contract", "receipt", "unknown"]


class DocumentKindResult(BaseModel):
    """First-step classification from a text excerpt."""

    kind: DocType = Field(
        description=(
            "Document kind: invoice, contract, receipt, or unknown when none fit."
        )
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
    invoice_date_iso: str | None = Field(
        default=None,
        description="Normalized date as YYYY-MM-DD when reasonably clear.",
    )
    total_amount: str | None = None
    total_amount_value: float | None = Field(
        default=None,
        description="Numeric total when parseable from total_amount.",
    )
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
    effective_date_iso: str | None = Field(
        default=None,
        description="Normalized effective date as YYYY-MM-DD when clear.",
    )
    end_date: str | None = None
    end_date_iso: str | None = Field(
        default=None,
        description="Normalized end date as YYYY-MM-DD when clear.",
    )
    governing_law: str | None = None
    key_terms_summary: str | None = Field(
        default=None,
        description="Brief summary of main obligations or terms.",
    )
    confidence_notes: str | None = None


class ReceiptExtraction(BaseModel):
    merchant: str | None = Field(default=None, description="Store or merchant name.")
    receipt_number: str | None = None
    receipt_date: str | None = None
    receipt_date_iso: str | None = Field(
        default=None,
        description="Normalized date as YYYY-MM-DD when clear.",
    )
    total_amount: str | None = None
    total_amount_value: float | None = Field(
        default=None,
        description="Numeric total when parseable from total_amount.",
    )
    currency: str | None = None
    payment_method: str | None = Field(
        default=None,
        description="Cash, card, transfer, etc. if mentioned.",
    )
    items: list[InvoiceLineItem] = Field(
        default_factory=list,
        description="Purchased items when listed.",
    )
    confidence_notes: str | None = None


StructuredExtraction = InvoiceExtraction | ContractExtraction | ReceiptExtraction


class ProcessingResult(BaseModel):
    """Per-file outcome for Streamlit and export."""

    filename: str
    success: bool
    doc_type: DocType | None = None
    classification_confidence_note: str | None = None
    structured: StructuredExtraction | None = None
    raw_text_preview: str = ""
    error_message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    latency_ms: int | None = Field(
        default=None,
        description="End-to-end processing time in milliseconds.",
    )
    used_ocr: bool = Field(
        default=False,
        description="True when vision OCR was used because PDF had no embedded text.",
    )

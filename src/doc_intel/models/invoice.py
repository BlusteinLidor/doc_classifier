"""Invoice-specific structured extraction models."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    normalized_date: str | None = None
    normalized_total_amount: float | None = None
    normalized_currency_code: str | None = None

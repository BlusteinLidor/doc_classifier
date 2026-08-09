"""Pydantic schemas for structured extraction and UI transport."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DocType = Literal[
    "invoice",
    "credit_note",
    "receipt",
    "quote",
    "purchase_order",
    "delivery_note",
    "contract",
    "bank_statement",
    "payslip",
    "utility_bill",
    "tax_document",
    "correspondence",
    "other",
    "unknown",
]


class DocumentKindResult(BaseModel):
    """First-step classification from a text excerpt."""

    kind: DocType = Field(
        description=(
            "Document kind among the supported business types, "
            "other for readable business content that does not fit, "
            "or unknown when unreadable / not a document."
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
    due_date: str | None = None
    due_date_iso: str | None = None
    total_amount: str | None = None
    total_amount_value: float | None = Field(
        default=None,
        description="Numeric total when parseable from total_amount.",
    )
    subtotal: str | None = None
    tax_amount: str | None = None
    tax_rate: str | None = None
    currency: str | None = Field(
        default=None,
        description="Currency code or symbol, e.g. ILS, USD, ₪.",
    )
    tax_id: str | None = Field(
        default=None,
        description="VAT or tax identification if present.",
    )
    buyer: str | None = None
    payment_terms: str | None = None
    po_reference: str | None = None
    bank_details: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence_notes: str | None = None


class CreditNoteExtraction(BaseModel):
    vendor: str | None = None
    credit_note_number: str | None = None
    credit_date: str | None = None
    credit_date_iso: str | None = None
    original_invoice_ref: str | None = None
    buyer: str | None = None
    total_amount: str | None = None
    total_amount_value: float | None = None
    currency: str | None = None
    tax_id: str | None = None
    reason: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence_notes: str | None = None


class ContractParty(BaseModel):
    name: str | None = None
    role: str | None = Field(default=None, description="e.g. employer, contractor, buyer.")


class ContractExtraction(BaseModel):
    title: str | None = None
    contract_number: str | None = None
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
    payment_terms: str | None = None
    duration_or_term: str | None = None
    auto_renewal: str | None = None
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
    subtotal: str | None = None
    tax_amount: str | None = None
    currency: str | None = None
    payment_method: str | None = Field(
        default=None,
        description="Cash, card, transfer, etc. if mentioned.",
    )
    store_address: str | None = None
    card_last4: str | None = None
    items: list[InvoiceLineItem] = Field(
        default_factory=list,
        description="Purchased items when listed.",
    )
    confidence_notes: str | None = None


class QuoteExtraction(BaseModel):
    vendor: str | None = None
    buyer: str | None = None
    quote_number: str | None = None
    quote_date: str | None = None
    quote_date_iso: str | None = None
    valid_until: str | None = None
    valid_until_iso: str | None = None
    total_amount: str | None = None
    total_amount_value: float | None = None
    currency: str | None = None
    tax_id: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence_notes: str | None = None


class PurchaseOrderExtraction(BaseModel):
    buyer: str | None = None
    vendor: str | None = None
    po_number: str | None = None
    po_date: str | None = None
    po_date_iso: str | None = None
    ship_to: str | None = None
    total_amount: str | None = None
    total_amount_value: float | None = None
    currency: str | None = None
    delivery_date: str | None = None
    delivery_date_iso: str | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence_notes: str | None = None


class DeliveryNoteExtraction(BaseModel):
    shipper: str | None = None
    recipient: str | None = None
    delivery_note_number: str | None = None
    delivery_date: str | None = None
    delivery_date_iso: str | None = None
    order_reference: str | None = None
    ship_to: str | None = None
    items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence_notes: str | None = None


class StatementLine(BaseModel):
    date: str | None = None
    description: str | None = None
    amount: str | None = None
    balance: str | None = None


class BankStatementExtraction(BaseModel):
    bank_name: str | None = None
    account_holder: str | None = None
    account_mask: str | None = Field(
        default=None,
        description="Masked or partial account number as shown.",
    )
    period_start: str | None = None
    period_start_iso: str | None = None
    period_end: str | None = None
    period_end_iso: str | None = None
    opening_balance: str | None = None
    closing_balance: str | None = None
    currency: str | None = None
    transactions: list[StatementLine] = Field(default_factory=list)
    confidence_notes: str | None = None


class NamedAmount(BaseModel):
    name: str | None = None
    amount: str | None = None


class PayslipExtraction(BaseModel):
    employer: str | None = None
    employee: str | None = None
    period: str | None = None
    pay_date: str | None = None
    pay_date_iso: str | None = None
    gross_pay: str | None = None
    net_pay: str | None = None
    net_pay_value: float | None = None
    currency: str | None = None
    deductions: list[NamedAmount] = Field(default_factory=list)
    confidence_notes: str | None = None


class UtilityBillExtraction(BaseModel):
    provider: str | None = None
    account_number: str | None = None
    customer_name: str | None = None
    service_address: str | None = None
    service_period: str | None = None
    bill_date: str | None = None
    bill_date_iso: str | None = None
    due_date: str | None = None
    due_date_iso: str | None = None
    amount_due: str | None = None
    amount_due_value: float | None = None
    currency: str | None = None
    meter_reading: str | None = None
    confidence_notes: str | None = None


class TaxDocumentExtraction(BaseModel):
    authority: str | None = None
    document_title: str | None = None
    taxpayer_name: str | None = None
    tax_id: str | None = None
    tax_period: str | None = None
    document_date: str | None = None
    document_date_iso: str | None = None
    amount: str | None = None
    amount_value: float | None = None
    currency: str | None = None
    reference_number: str | None = None
    summary: str | None = None
    confidence_notes: str | None = None


class CorrespondenceExtraction(BaseModel):
    sender: str | None = None
    recipient: str | None = None
    letter_date: str | None = None
    letter_date_iso: str | None = None
    subject: str | None = None
    reference_number: str | None = None
    summary: str | None = None
    confidence_notes: str | None = None


class GenericExtraction(BaseModel):
    """Fallback fields for unclassified readable business documents."""

    title: str | None = None
    organizations: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    key_dates: list[str] = Field(default_factory=list)
    reference_ids: list[str] = Field(default_factory=list)
    amounts_mentioned: list[str] = Field(default_factory=list)
    summary: str | None = None
    language_hint: str | None = None
    confidence_notes: str | None = None


StructuredExtraction = (
    InvoiceExtraction
    | CreditNoteExtraction
    | ReceiptExtraction
    | QuoteExtraction
    | PurchaseOrderExtraction
    | DeliveryNoteExtraction
    | ContractExtraction
    | BankStatementExtraction
    | PayslipExtraction
    | UtilityBillExtraction
    | TaxDocumentExtraction
    | CorrespondenceExtraction
    | GenericExtraction
)


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

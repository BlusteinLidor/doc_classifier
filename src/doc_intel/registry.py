"""Document-type registry: schema, prompt, UI field layout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import get_args

from doc_intel.models import (
    BankStatementExtraction,
    ContractExtraction,
    CorrespondenceExtraction,
    CreditNoteExtraction,
    DeliveryNoteExtraction,
    DocType,
    GenericExtraction,
    InvoiceExtraction,
    PayslipExtraction,
    PurchaseOrderExtraction,
    QuoteExtraction,
    ReceiptExtraction,
    StructuredExtraction,
    TaxDocumentExtraction,
    UtilityBillExtraction,
)
from doc_intel.prompts import EXTRACTION_PROMPTS


@dataclass(frozen=True)
class TypeSpec:
    """Per-type extraction + display metadata."""

    schema: type[StructuredExtraction]
    system_prompt: str
    # Scalar field keys preferred for hero display (first non-empty wins).
    highlight_fields: tuple[str, ...] = ()
    # Maps list field name → renderer kind.
    list_fields: dict[str, str] = field(default_factory=dict)
    # Prefer these scalar keys first in the field panel (then remaining model fields).
    primary_fields: tuple[str, ...] = ()
    family: str = "other"  # money | logistics | agreement | hr | tax | other


TYPE_REGISTRY: dict[str, TypeSpec] = {
    "invoice": TypeSpec(
        schema=InvoiceExtraction,
        system_prompt=EXTRACTION_PROMPTS["invoice"],
        highlight_fields=("total_amount", "currency"),
        list_fields={"line_items": "line_items"},
        primary_fields=(
            "vendor",
            "buyer",
            "invoice_number",
            "invoice_date",
            "invoice_date_iso",
            "due_date",
            "due_date_iso",
            "subtotal",
            "tax_amount",
            "tax_rate",
            "total_amount",
            "total_amount_value",
            "currency",
            "tax_id",
            "payment_terms",
            "po_reference",
            "bank_details",
        ),
        family="money",
    ),
    "credit_note": TypeSpec(
        schema=CreditNoteExtraction,
        system_prompt=EXTRACTION_PROMPTS["credit_note"],
        highlight_fields=("total_amount", "currency"),
        list_fields={"line_items": "line_items"},
        primary_fields=(
            "vendor",
            "buyer",
            "credit_note_number",
            "credit_date",
            "credit_date_iso",
            "original_invoice_ref",
            "total_amount",
            "total_amount_value",
            "currency",
            "tax_id",
            "reason",
        ),
        family="money",
    ),
    "receipt": TypeSpec(
        schema=ReceiptExtraction,
        system_prompt=EXTRACTION_PROMPTS["receipt"],
        highlight_fields=("total_amount", "currency"),
        list_fields={"items": "line_items"},
        primary_fields=(
            "merchant",
            "receipt_number",
            "receipt_date",
            "receipt_date_iso",
            "subtotal",
            "tax_amount",
            "total_amount",
            "total_amount_value",
            "currency",
            "payment_method",
            "store_address",
            "card_last4",
        ),
        family="money",
    ),
    "quote": TypeSpec(
        schema=QuoteExtraction,
        system_prompt=EXTRACTION_PROMPTS["quote"],
        highlight_fields=("total_amount", "currency"),
        list_fields={"line_items": "line_items"},
        primary_fields=(
            "vendor",
            "buyer",
            "quote_number",
            "quote_date",
            "quote_date_iso",
            "valid_until",
            "valid_until_iso",
            "total_amount",
            "total_amount_value",
            "currency",
            "tax_id",
        ),
        family="money",
    ),
    "purchase_order": TypeSpec(
        schema=PurchaseOrderExtraction,
        system_prompt=EXTRACTION_PROMPTS["purchase_order"],
        highlight_fields=("total_amount", "currency"),
        list_fields={"line_items": "line_items"},
        primary_fields=(
            "buyer",
            "vendor",
            "po_number",
            "po_date",
            "po_date_iso",
            "ship_to",
            "delivery_date",
            "delivery_date_iso",
            "total_amount",
            "total_amount_value",
            "currency",
        ),
        family="logistics",
    ),
    "delivery_note": TypeSpec(
        schema=DeliveryNoteExtraction,
        system_prompt=EXTRACTION_PROMPTS["delivery_note"],
        highlight_fields=("delivery_note_number",),
        list_fields={"items": "line_items"},
        primary_fields=(
            "shipper",
            "recipient",
            "delivery_note_number",
            "delivery_date",
            "delivery_date_iso",
            "order_reference",
            "ship_to",
        ),
        family="logistics",
    ),
    "contract": TypeSpec(
        schema=ContractExtraction,
        system_prompt=EXTRACTION_PROMPTS["contract"],
        highlight_fields=("title",),
        list_fields={"parties": "parties"},
        primary_fields=(
            "title",
            "contract_number",
            "effective_date",
            "effective_date_iso",
            "end_date",
            "end_date_iso",
            "governing_law",
            "payment_terms",
            "duration_or_term",
            "auto_renewal",
            "key_terms_summary",
        ),
        family="agreement",
    ),
    "bank_statement": TypeSpec(
        schema=BankStatementExtraction,
        system_prompt=EXTRACTION_PROMPTS["bank_statement"],
        highlight_fields=("closing_balance", "currency"),
        list_fields={"transactions": "transactions"},
        primary_fields=(
            "bank_name",
            "account_holder",
            "account_mask",
            "period_start",
            "period_start_iso",
            "period_end",
            "period_end_iso",
            "opening_balance",
            "closing_balance",
            "currency",
        ),
        family="money",
    ),
    "payslip": TypeSpec(
        schema=PayslipExtraction,
        system_prompt=EXTRACTION_PROMPTS["payslip"],
        highlight_fields=("net_pay", "currency"),
        list_fields={"deductions": "named_amounts"},
        primary_fields=(
            "employer",
            "employee",
            "period",
            "pay_date",
            "pay_date_iso",
            "gross_pay",
            "net_pay",
            "net_pay_value",
            "currency",
        ),
        family="hr",
    ),
    "utility_bill": TypeSpec(
        schema=UtilityBillExtraction,
        system_prompt=EXTRACTION_PROMPTS["utility_bill"],
        highlight_fields=("amount_due", "currency"),
        primary_fields=(
            "provider",
            "customer_name",
            "account_number",
            "service_address",
            "service_period",
            "bill_date",
            "bill_date_iso",
            "due_date",
            "due_date_iso",
            "amount_due",
            "amount_due_value",
            "currency",
            "meter_reading",
        ),
        family="money",
    ),
    "tax_document": TypeSpec(
        schema=TaxDocumentExtraction,
        system_prompt=EXTRACTION_PROMPTS["tax_document"],
        highlight_fields=("amount", "currency"),
        primary_fields=(
            "authority",
            "document_title",
            "taxpayer_name",
            "tax_id",
            "tax_period",
            "document_date",
            "document_date_iso",
            "amount",
            "amount_value",
            "currency",
            "reference_number",
            "summary",
        ),
        family="tax",
    ),
    "correspondence": TypeSpec(
        schema=CorrespondenceExtraction,
        system_prompt=EXTRACTION_PROMPTS["correspondence"],
        highlight_fields=("subject",),
        primary_fields=(
            "sender",
            "recipient",
            "letter_date",
            "letter_date_iso",
            "subject",
            "reference_number",
            "summary",
        ),
        family="other",
    ),
    "other": TypeSpec(
        schema=GenericExtraction,
        system_prompt=EXTRACTION_PROMPTS["other"],
        highlight_fields=("title",),
        list_fields={
            "organizations": "strings",
            "people": "strings",
            "key_dates": "strings",
            "reference_ids": "strings",
            "amounts_mentioned": "strings",
        },
        primary_fields=("title", "summary", "language_hint"),
        family="other",
    ),
}

# Types that take part in classification / extraction (excludes unknown).
EXTRACTABLE_DOC_TYPES: frozenset[str] = frozenset(TYPE_REGISTRY.keys())


def get_type_spec(doc_type: str) -> TypeSpec | None:
    return TYPE_REGISTRY.get(doc_type)


def assert_registry_complete() -> None:
    """Raise if any DocType (except unknown) lacks a registry entry or prompt."""
    for kind in get_args(DocType):
        if kind == "unknown":
            continue
        if kind not in TYPE_REGISTRY:
            raise AssertionError(f"DocType {kind!r} missing from TYPE_REGISTRY")
        if kind not in EXTRACTION_PROMPTS:
            raise AssertionError(f"DocType {kind!r} missing from EXTRACTION_PROMPTS")

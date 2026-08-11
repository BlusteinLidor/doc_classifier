"""Streamlit UI: bilingual demo, field cards, samples, export."""

from __future__ import annotations

import html
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

# Allow running without `pip install -e .` during development
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from doc_intel.export import (
    branded_export_basename,
    results_to_csv_bytes,
    results_to_json_bytes,
    single_result_to_json_bytes,
)
from doc_intel.models import ProcessingResult, StructuredExtraction
from doc_intel.pipeline import process_pdf_bytes
from doc_intel.registry import get_type_spec

load_dotenv()


def _sync_streamlit_secrets() -> None:
    """Copy Streamlit Cloud secrets into env for the OpenAI client."""
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return
    if secret_key and not os.environ.get("OPENAI_API_KEY", "").strip():
        os.environ["OPENAI_API_KEY"] = str(secret_key).strip()


_sync_streamlit_secrets()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SAMPLES_DIR = _ROOT / "samples"
_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_FILES_PER_RUN = 3
_FEATURED_SAMPLE_EN = "sample_invoice_en.pdf"
_FEATURED_SAMPLE_HE = "sample_invoice_he.pdf"

# (filename, teaser_en, teaser_he, button_en, button_he, featured)
# shown filtered by UI language: EN → English/USD docs, HE → Hebrew/ILS docs
_SAMPLE_DOCS: list[tuple[str, str, str, str, str, bool]] = [
    (
        "sample_invoice_en.pdf",
        "USD totals · vendor & line items",
        "USD totals · vendor & line items",
        "Invoice ⭐",
        "Invoice ⭐",
        True,
    ),
    (
        "sample_invoice_he.pdf",
        "₪ amounts · Hebrew vendor (featured)",
        "סכומים ₪ · ספק בעברית (מומלץ)",
        "חשבונית ⭐",
        "חשבונית ⭐",
        True,
    ),
    (
        "sample_contract_en.pdf",
        "Two parties · governing law",
        "Two parties · governing law",
        "Service agreement",
        "Service agreement",
        False,
    ),
    (
        "sample_contract_he.pdf",
        "Hebrew parties · key terms",
        "צדדים בעברית · תנאים עיקריים",
        "הסכם שירותים",
        "הסכם שירותים",
        False,
    ),
    (
        "sample_receipt_en.pdf",
        "Merchant slip · payment method",
        "Merchant slip · payment method",
        "Receipt",
        "Receipt",
        False,
    ),
    (
        "sample_receipt_he.pdf",
        "Hebrew merchant · ₪ total",
        "בית עסק בעברית · סה״כ ₪",
        "קבלה",
        "קבלה",
        False,
    ),
    (
        "sample_quote_en.pdf",
        "Proposal · validity period",
        "Proposal · validity period",
        "Quote",
        "Quote",
        False,
    ),
    (
        "sample_purchase_order_en.pdf",
        "Buyer PO · line items",
        "Buyer PO · line items",
        "Purchase order",
        "Purchase order",
        False,
    ),
    (
        "sample_bank_statement_en.pdf",
        "Period · balances & transactions",
        "Period · balances & transactions",
        "Bank statement",
        "Bank statement",
        False,
    ),
]


def _sample_locale(filename: str) -> str | None:
    name = filename.lower()
    if name.endswith("_he.pdf"):
        return "he"
    if name.endswith("_en.pdf"):
        return "en"
    return None


def _samples_for_ui_lang() -> list[tuple[str, str, str, str, str, bool]]:
    lang = "he" if _is_he() else "en"
    return [s for s in _SAMPLE_DOCS if _sample_locale(s[0]) == lang]


def _featured_sample() -> str:
    return _FEATURED_SAMPLE_HE if _is_he() else _FEATURED_SAMPLE_EN

_UI: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Document Intelligence — Portfolio Demo",
        "brand": "AI Document Intelligence",
        "brand_he_sub": "בינה מלאכותית למסמכים",
        "value": "Upload a PDF. Get type + key fields in seconds.",
        "chip_types": "Invoice · Quote · PO · Contract · Receipt · Bank · more",
        "chip_lang": "Hebrew / English",
        "chip_time": "Usually 15–45 sec",
        "how_title": "How it works",
        "step1": "1. Upload or pick a sample",
        "step2": "2. Classify document type",
        "step3": "3. Extract structured fields",
        "lang_label": "Language",
        "samples_title": "Try a sample (no upload needed)",
        "upload_title": "Or upload your own PDFs",
        "upload_help": "Demo limit: max {max_files} files, {max_mb} MB each · text PDFs preferred; image-only PDFs use vision OCR",
        "analyze": "Analyze documents",
        "empty_title": "Ready when you are",
        "empty_body": "Click a **sample** for the fastest demo, or upload PDFs and press **Analyze documents**.",
        "empty_hint": "Best with text PDFs. Image-only scans use vision OCR (slower, first 3 pages).",
        "empty_fields": "You'll get: document type, key fields, confidence notes, and JSON/CSV export.",
        "results": "Results",
        "ready": "Ready — key fields extracted",
        "clear": "Clear results",
        "analyze_another": "Analyze another",
        "download_json": "Download JSON",
        "download_csv": "Download CSV",
        "batch_table": "Batch overview",
        "classification": "Classification",
        "confidence": "Why this classification",
        "extraction_notes": "Extraction notes",
        "original_pdf": "Original PDF",
        "extracted_data": "Extracted data",
        "text_preview": "Text preview (extracted)",
        "json_raw": "Raw JSON",
        "warnings": "Warnings",
        "latency": "Processed in {sec:.1f}s",
        "used_ocr": "Vision OCR used",
        "per_doc_json": "Download this JSON",
        "copy_value": "Copy",
        "no_pdf": "PDF bytes not available for preview.",
        "no_text": "No text extracted.",
        "no_fields": "No structured fields returned.",
        "unknown_ok": "Classified as unknown — no type-specific fields extracted.",
        "footer_tech": "Tech: Streamlit · OpenAI structured outputs · PyMuPDF · Pydantic V2",
        "footer_limits": "Portfolio demo · sample data only · max {max_files} files / {max_mb} MB · OCR on image PDFs",
        "about": "About this demo",
        "about_body": "Portfolio demonstration only — not a client production system. No accounts or stored documents.",
        "summary_ok": "{ok} of {total} OK",
        "eta": "Usually 15–45 seconds depending on OpenAI.",
        "stage_start": "Starting…",
        "failed": "Failed",
        "ok": "OK",
        "line_items": "Line items",
        "parties": "Parties",
        "key_terms": "Key terms",
        "items": "Items",
        "transactions": "Transactions",
        "deductions": "Deductions",
        "col_file": "File",
        "col_type": "Type",
        "col_summary": "Summary",
        "col_status": "Status",
        "auto_run": "Run featured demo",
        "running_demo": "Running featured sample…",
        "skip_auto": "Skip",
    },
    "he": {
        "page_title": "בינה מלאכותית למסמכים — הדגמה",
        "brand": "בינה מלאכותית למסמכים",
        "brand_he_sub": "AI Document Intelligence",
        "value": "העלו PDF. קבלו סוג מסמך ושדות מפתח תוך שניות.",
        "chip_types": "חשבונית · הצעה · הזמנה · חוזה · קבלה · ועוד",
        "chip_lang": "עברית / אנגלית",
        "chip_time": "בדרך כלל 15–45 שנ׳",
        "how_title": "איך זה עובד",
        "step1": "1. העלאה או דוגמה",
        "step2": "2. סיווג סוג מסמך",
        "step3": "3. חילוץ שדות מובנים",
        "lang_label": "שפה",
        "samples_title": "נסו דוגמה (בלי העלאה)",
        "upload_title": "או העלו PDF משלכם",
        "upload_help": "מגבלת הדגמה: עד {max_files} קבצים, {max_mb} מ״ב · מומלץ PDF עם טקסט; סריקות משתמשות ב-OCR",
        "analyze": "נתח מסמכים",
        "empty_title": "מוכנים להתחיל",
        "empty_body": "לחצו על **דוגמה** להדגמה המהירה, או העלו PDF ולחצו **נתח מסמכים**.",
        "empty_hint": "עובד הכי טוב עם PDF עם שכבת טקסט. סריקות תמונה עוברות OCR (איטי יותר, 3 עמודים ראשונים).",
        "empty_fields": "תקבלו: סוג מסמך, שדות מפתח, הערות ביטחון וייצוא JSON/CSV.",
        "results": "תוצאות",
        "ready": "מוכן — שדות מפתח חולצו",
        "clear": "נקה תוצאות",
        "analyze_another": "נתח עוד",
        "download_json": "הורד JSON",
        "download_csv": "הורד CSV",
        "batch_table": "סקירת האצווה",
        "classification": "סיווג",
        "confidence": "מדוע סווג כך",
        "extraction_notes": "הערות חילוץ",
        "original_pdf": "PDF מקורי",
        "extracted_data": "נתונים שחולצו",
        "text_preview": "תצוגת טקסט (חולץ)",
        "json_raw": "JSON גולמי",
        "warnings": "אזהרות",
        "latency": "עובד בתוך {sec:.1f} שנ׳",
        "used_ocr": "נעשה שימוש ב-OCR",
        "per_doc_json": "הורד JSON של מסמך זה",
        "copy_value": "העתק",
        "no_pdf": "אין נתוני PDF לתצוגה.",
        "no_text": "לא חולץ טקסט.",
        "no_fields": "לא הוחזרו שדות מובנים.",
        "unknown_ok": "סווג כלא ידוע — לא חולצו שדות ספציפיים.",
        "footer_tech": "טכנולוגיה: Streamlit · OpenAI · PyMuPDF · Pydantic V2",
        "footer_limits": "הדגמת תיק עבודות · נתוני דוגמה · עד {max_files} קבצים / {max_mb} מ״ב · OCR לסריקות",
        "about": "על ההדגמה",
        "about_body": "הדגמה לתיק עבודות בלבד — לא מערכת לקוח. ללא חשבונות וללא שמירת מסמכים.",
        "summary_ok": "{ok} מתוך {total} הצליחו",
        "eta": "בדרך כלל 15–45 שניות, תלוי ב-OpenAI.",
        "stage_start": "מתחיל…",
        "failed": "נכשל",
        "ok": "תקין",
        "line_items": "פריטי שורה",
        "parties": "צדדים",
        "key_terms": "תנאים עיקריים",
        "items": "פריטים",
        "transactions": "תנועות",
        "deductions": "ניכויים",
        "col_file": "קובץ",
        "col_type": "סוג",
        "col_summary": "סיכום",
        "col_status": "סטטוס",
        "auto_run": "הדגמה מומלצת",
        "running_demo": "מריץ דוגמה מומלצת…",
        "skip_auto": "דלג",
    },
}

# Bilingual field labels: en / he
_FIELD_LABELS: dict[str, tuple[str, str]] = {
    "vendor": ("Vendor", "ספק"),
    "buyer": ("Buyer", "לקוח"),
    "merchant": ("Merchant", "בית עסק"),
    "provider": ("Provider", "ספק שירות"),
    "employer": ("Employer", "מעסיק"),
    "employee": ("Employee", "עובד"),
    "shipper": ("Shipper", "שולח"),
    "recipient": ("Recipient", "נמען"),
    "sender": ("Sender", "שולח"),
    "customer_name": ("Customer", "לקוח"),
    "account_holder": ("Account holder", "בעל חשבון"),
    "bank_name": ("Bank", "בנק"),
    "authority": ("Authority", "רשות"),
    "taxpayer_name": ("Taxpayer", "נישום"),
    "invoice_number": ("Invoice #", "מס׳ חשבונית"),
    "credit_note_number": ("Credit note #", "מס׳ זיכוי"),
    "receipt_number": ("Receipt #", "מס׳ קבלה"),
    "quote_number": ("Quote #", "מס׳ הצעה"),
    "po_number": ("PO #", "מס׳ הזמנה"),
    "delivery_note_number": ("Delivery note #", "מס׳ תעודת משלוח"),
    "contract_number": ("Contract #", "מס׳ חוזה"),
    "reference_number": ("Reference #", "אסמכתא"),
    "account_number": ("Account #", "מס׳ חשבון"),
    "account_mask": ("Account", "חשבון"),
    "invoice_date": ("Invoice date", "תאריך חשבונית"),
    "invoice_date_iso": ("Date (ISO)", "תאריך (ISO)"),
    "credit_date": ("Credit date", "תאריך זיכוי"),
    "credit_date_iso": ("Credit (ISO)", "זיכוי (ISO)"),
    "receipt_date": ("Receipt date", "תאריך קבלה"),
    "receipt_date_iso": ("Date (ISO)", "תאריך (ISO)"),
    "quote_date": ("Quote date", "תאריך הצעה"),
    "quote_date_iso": ("Quote (ISO)", "הצעה (ISO)"),
    "po_date": ("PO date", "תאריך הזמנה"),
    "po_date_iso": ("PO (ISO)", "הזמנה (ISO)"),
    "delivery_date": ("Delivery date", "תאריך משלוח"),
    "delivery_date_iso": ("Delivery (ISO)", "משלוח (ISO)"),
    "effective_date": ("Effective date", "תאריך תחילה"),
    "effective_date_iso": ("Effective (ISO)", "תחילה (ISO)"),
    "end_date": ("End date", "תאריך סיום"),
    "end_date_iso": ("End (ISO)", "סיום (ISO)"),
    "due_date": ("Due date", "תאריך לתשלום"),
    "due_date_iso": ("Due (ISO)", "לתשלום (ISO)"),
    "bill_date": ("Bill date", "תאריך חשבון"),
    "bill_date_iso": ("Bill (ISO)", "חשבון (ISO)"),
    "letter_date": ("Letter date", "תאריך מכתב"),
    "letter_date_iso": ("Letter (ISO)", "מכתב (ISO)"),
    "pay_date": ("Pay date", "תאריך תשלום"),
    "pay_date_iso": ("Pay (ISO)", "תשלום (ISO)"),
    "document_date": ("Document date", "תאריך מסמך"),
    "document_date_iso": ("Document (ISO)", "מסמך (ISO)"),
    "valid_until": ("Valid until", "בתוקף עד"),
    "valid_until_iso": ("Valid until (ISO)", "תוקף (ISO)"),
    "period_start": ("Period start", "תחילת תקופה"),
    "period_start_iso": ("Period start (ISO)", "תחילה (ISO)"),
    "period_end": ("Period end", "סוף תקופה"),
    "period_end_iso": ("Period end (ISO)", "סיום (ISO)"),
    "period": ("Period", "תקופה"),
    "service_period": ("Service period", "תקופת שירות"),
    "tax_period": ("Tax period", "תקופת מס"),
    "total_amount": ("Total", "סה״כ"),
    "total_amount_value": ("Total (numeric)", "סה״כ (מספר)"),
    "subtotal": ("Subtotal", "לפני מע״מ"),
    "tax_amount": ("Tax", "מס / מע״מ"),
    "tax_rate": ("Tax rate", "שיעור מס"),
    "amount_due": ("Amount due", "סכום לתשלום"),
    "amount_due_value": ("Amount due (numeric)", "לתשלום (מספר)"),
    "amount": ("Amount", "סכום"),
    "amount_value": ("Amount (numeric)", "סכום (מספר)"),
    "gross_pay": ("Gross pay", "ברוטו"),
    "net_pay": ("Net pay", "נטו"),
    "net_pay_value": ("Net (numeric)", "נטו (מספר)"),
    "opening_balance": ("Opening balance", "יתרת פתיחה"),
    "closing_balance": ("Closing balance", "יתרת סגירה"),
    "currency": ("Currency", "מטבע"),
    "tax_id": ("Tax ID", "ח.פ / ע.מ"),
    "payment_method": ("Payment", "אמצעי תשלום"),
    "payment_terms": ("Payment terms", "תנאי תשלום"),
    "po_reference": ("PO reference", "אסמכתת הזמנה"),
    "original_invoice_ref": ("Original invoice", "חשבונית מקור"),
    "order_reference": ("Order ref", "אסמכתת הזמנה"),
    "ship_to": ("Ship to", "כתובת משלוח"),
    "service_address": ("Service address", "כתובת שירות"),
    "store_address": ("Store address", "כתובת חנות"),
    "bank_details": ("Bank details", "פרטי בנק"),
    "card_last4": ("Card last4", "4 ספרות אחרונות"),
    "meter_reading": ("Meter", "מד"),
    "governing_law": ("Governing law", "דין חל"),
    "duration_or_term": ("Duration", "משך"),
    "auto_renewal": ("Auto renewal", "חידוש אוטומטי"),
    "key_terms_summary": ("Key terms", "תנאים עיקריים"),
    "title": ("Title", "כותרת"),
    "subject": ("Subject", "נושא"),
    "document_title": ("Document title", "כותרת מסמך"),
    "summary": ("Summary", "סיכום"),
    "reason": ("Reason", "סיבה"),
    "language_hint": ("Language", "שפה"),
    "confidence_notes": ("Notes", "הערות"),
}

_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "invoice": ("Invoice", "חשבונית"),
    "credit_note": ("Credit note", "זיכוי"),
    "receipt": ("Receipt", "קבלה"),
    "quote": ("Quote", "הצעת מחיר"),
    "purchase_order": ("Purchase order", "הזמנת רכש"),
    "delivery_note": ("Delivery note", "תעודת משלוח"),
    "contract": ("Contract", "חוזה"),
    "bank_statement": ("Bank statement", "דף חשבון"),
    "payslip": ("Payslip", "תלוש שכר"),
    "utility_bill": ("Utility bill", "חשבון שירות"),
    "tax_document": ("Tax document", "מסמך מס"),
    "correspondence": ("Correspondence", "מכתב"),
    "other": ("Other", "אחר"),
    "unknown": ("Unknown", "לא ידוע"),
}

_FAMILY_BY_TYPE: dict[str, str] = {
    "invoice": "money",
    "credit_note": "money",
    "receipt": "money",
    "quote": "money",
    "bank_statement": "money",
    "utility_bill": "money",
    "purchase_order": "logistics",
    "delivery_note": "logistics",
    "contract": "agreement",
    "payslip": "hr",
    "tax_document": "tax",
    "correspondence": "other",
    "other": "other",
    "unknown": "unknown",
}

st.set_page_config(
    page_title="Document Intelligence — Portfolio Demo",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_PAGE_STYLE = """
<style>
:root {
  --di-ink: #0f3d3e;
  --di-teal: #1a6b6c;
  --di-sand: #f4f1ea;
  --di-accent: #c45c26;
  --di-card: #ffffff;
  --di-muted: #5a6a6a;
  --di-border: #d5ddd8;
}
.block-container { padding-top: 1.25rem; max-width: 1200px; }
html, body, [data-testid="stAppViewContainer"] {
  background: linear-gradient(165deg, #f7f5f0 0%, #e8f0ef 45%, #f4f1ea 100%);
}
.di-hero {
  background: linear-gradient(135deg, #0f3d3e 0%, #1a6b6c 55%, #245a4a 100%);
  color: #f8faf9; border-radius: 16px; padding: 1.5rem 1.75rem;
  margin-bottom: 1.1rem; box-shadow: 0 8px 28px rgba(15,61,62,0.18);
}
.di-hero h1 {
  margin: 0 0 0.35rem 0; font-size: 1.85rem; font-weight: 700;
  letter-spacing: -0.02em; font-family: "Segoe UI", "Arial Hebrew", Tahoma, sans-serif;
}
.di-hero .sub {
  opacity: 0.88; font-size: 0.95rem; margin-bottom: 0.55rem;
}
.di-hero .value { font-size: 1.1rem; margin: 0.4rem 0 0.85rem 0; max-width: 36rem; }
.di-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.di-chip {
  background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
  border-radius: 999px; padding: 0.28rem 0.75rem; font-size: 0.82rem;
}
.di-steps {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem;
  margin: 0.85rem 0 0.4rem 0;
}
@media (max-width: 720px) {
  .di-steps { grid-template-columns: 1fr; }
}
.di-step {
  background: rgba(255,255,255,0.1); border-radius: 10px;
  padding: 0.55rem 0.7rem; font-size: 0.88rem;
}
.di-empty {
  background: var(--di-card); border: 1px solid var(--di-border); border-radius: 14px;
  padding: 1.15rem 1.25rem; margin: 0.75rem 0 1rem 0;
}
.di-empty h3 { margin: 0 0 0.4rem 0; color: var(--di-ink); }
.di-empty p { margin: 0.35rem 0; color: var(--di-muted); }
.di-summary {
  background: #e8f5f2; border: 1px solid #b7d9d1; border-radius: 12px;
  padding: 0.85rem 1.1rem; margin-bottom: 0.85rem; color: var(--di-ink);
}
.di-field-card {
  background: var(--di-card); border: 1px solid var(--di-border);
  border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 0.65rem;
  direction: inherit;
}
.di-field-row {
  display: grid; grid-template-columns: minmax(7rem, 32%) 1fr;
  gap: 0.35rem 0.75rem; padding: 0.35rem 0;
  border-bottom: 1px solid #eef1ef; font-size: 0.95rem;
}
.di-field-row:last-child { border-bottom: none; }
.di-label { color: var(--di-muted); font-weight: 600; font-size: 0.82rem; }
.di-value { color: var(--di-ink); font-weight: 600; word-break: break-word; }
.di-hero-amount {
  font-size: 1.55rem; font-weight: 750; color: var(--di-accent); margin: 0.25rem 0 0.5rem 0;
}
.di-hero-title {
  font-size: 1.2rem; font-weight: 700; color: var(--di-ink); margin: 0.2rem 0 0.5rem 0;
}
.doc-badge {
  display: inline-block; font-size: 1.15rem; font-weight: 700;
  letter-spacing: 0.02em; padding: 0.4rem 0.9rem; border-radius: 8px;
  margin: 0.25rem 0 0.55rem 0;
}
.doc-badge-invoice, .doc-badge-credit_note, .doc-badge-receipt,
.doc-badge-quote, .doc-badge-bank_statement, .doc-badge-utility_bill,
.doc-badge-money { background: #dbeafe; color: #1e3a8a; }
.doc-badge-purchase_order, .doc-badge-delivery_note,
.doc-badge-logistics { background: #d1fae5; color: #065f46; }
.doc-badge-contract, .doc-badge-agreement { background: #dcfce7; color: #14532d; }
.doc-badge-payslip, .doc-badge-hr { background: #f3e8ff; color: #6b21a8; }
.doc-badge-tax_document, .doc-badge-tax { background: #fef3c7; color: #92400e; }
.doc-badge-correspondence, .doc-badge-other, .doc-badge-unknown { background: #f3f4f6; color: #374151; }
.di-party-chip {
  display: inline-block; background: #eef6f5; border: 1px solid #c5ddd9;
  border-radius: 8px; padding: 0.25rem 0.55rem; margin: 0.15rem 0.2rem 0.15rem 0;
  font-size: 0.88rem;
}
.di-footer {
  margin-top: 1.75rem; padding-top: 0.85rem; border-top: 1px solid var(--di-border);
  color: var(--di-muted); font-size: 0.85rem;
}
.di-rtl { direction: rtl; text-align: right; unicode-bidi: plaintext;
  font-family: "Segoe UI", "Arial Hebrew", Tahoma, sans-serif; }
.sample-featured button {
  border: 2px solid #1a6b6c !important;
}
div[data-testid="stVerticalBlock"] > div:has(.di-hero) { margin-bottom: 0; }
</style>
"""


def _t(key: str, **kwargs: Any) -> str:
    lang = st.session_state.get("ui_lang", "en")
    text = _UI.get(lang, _UI["en"]).get(key) or _UI["en"].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


def _is_he() -> bool:
    return st.session_state.get("ui_lang", "en") == "he"


def _field_label(key: str) -> str:
    pair = _FIELD_LABELS.get(key)
    if not pair:
        return key.replace("_", " ").title()
    en, he = pair
    return f"{he} / {en}" if _is_he() else f"{en} / {he}"


def _type_label(doc_type: str | None) -> str:
    if not doc_type:
        doc_type = "unknown"
    pair = _TYPE_LABELS.get(doc_type, (doc_type, doc_type))
    return pair[1] if _is_he() else pair[0]


def _load_sample(filename: str) -> bytes:
    path = _SAMPLES_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Sample not found: {path}")
    return path.read_bytes()


def _render_pdf_preview(data: bytes, filename: str) -> None:
    if hasattr(st, "pdf"):
        st.pdf(data, height=520)
    else:
        st.warning("PDF preview requires a newer Streamlit version.")
        st.download_button(
            label=f"Download {filename}",
            data=data,
            file_name=filename,
            mime="application/pdf",
            key=f"pdf_dl_{filename}",
        )


def _doc_type_badge_html(doc_type: str | None) -> str:
    dt = doc_type or "unknown"
    family = _FAMILY_BY_TYPE.get(dt, "other")
    label = _type_label(dt)
    return (
        f'<div class="doc-badge doc-badge-{html.escape(dt)} doc-badge-{html.escape(family)}">'
        f"{html.escape(label)}</div>"
    )


def _value_in_preview(value: str | None, preview: str) -> bool:
    if not value or not preview:
        return False
    v = value.strip()
    return len(v) >= 2 and v in preview


def _field_rows_html(
    pairs: list[tuple[str, str | None]],
    *,
    preview: str = "",
) -> str:
    rows: list[str] = []
    for key, val in pairs:
        if val is None or str(val).strip() == "":
            continue
        grounded = _value_in_preview(str(val), preview)
        mark = " ✓" if grounded else ""
        rows.append(
            f'<div class="di-field-row">'
            f'<div class="di-label">{html.escape(_field_label(key))}</div>'
            f'<div class="di-value">{html.escape(str(val))}{html.escape(mark)}</div>'
            f"</div>"
        )
    if not rows:
        return ""
    dir_cls = " di-rtl" if _is_he() else ""
    return f'<div class="di-field-card{dir_cls}">' + "".join(rows) + "</div>"


def _render_structured_cards(
    obj: StructuredExtraction,
    *,
    result: ProcessingResult,
) -> None:
    preview = result.raw_text_preview or ""
    dir_cls = " di-rtl" if _is_he() else ""
    data = obj.model_dump()
    doc_type = result.doc_type or "other"
    spec = get_type_spec(doc_type)

    list_keys = set(spec.list_fields.keys()) if spec else set()
    skip = {"confidence_notes"}
    primary = list(spec.primary_fields) if spec else []
    highlight = list(spec.highlight_fields) if spec else []

    hero_parts = [
        str(data[k])
        for k in highlight
        if data.get(k) is not None and str(data[k]).strip() != ""
    ]
    hero = " ".join(hero_parts).strip()
    if hero:
        is_title = bool(highlight and highlight[0] in ("title", "subject"))
        cls = "di-hero-title" if is_title else "di-hero-amount"
        st.markdown(
            f'<div class="{cls}{dir_cls}">{html.escape(hero)}</div>',
            unsafe_allow_html=True,
        )

    ordered: list[str] = []
    for k in primary:
        if k in list_keys or k in skip:
            continue
        val = data.get(k)
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        if isinstance(val, (list, dict)):
            continue
        ordered.append(k)
    for k, val in data.items():
        if k in ordered or k in list_keys or k in skip:
            continue
        if val is None or isinstance(val, (list, dict)):
            continue
        if isinstance(val, str) and not val.strip():
            continue
        ordered.append(k)

    pairs: list[tuple[str, str | None]] = [
        (k, None if data[k] is None else str(data[k])) for k in ordered
    ]
    html_block = _field_rows_html(pairs, preview=preview)
    if html_block:
        st.markdown(html_block, unsafe_allow_html=True)

    copy_candidates = [
        (k, None if data.get(k) is None else str(data.get(k)))
        for k in (highlight + primary)[:5]
        if k not in list_keys and data.get(k) is not None
    ]
    _render_copy_row(copy_candidates, key_prefix=f"cp_{result.filename}_{doc_type}")

    list_fields: dict[str, str] = dict(spec.list_fields) if spec else {}
    if not list_fields:
        # Fallback: detect list fields on the model dump.
        for k, val in data.items():
            if isinstance(val, list) and val:
                list_fields[k] = "line_items"

    for key, kind in list_fields.items():
        raw = data.get(key) or []
        if not isinstance(raw, list) or not raw:
            continue
        label = {
            "line_items": "line_items",
            "items": "items",
            "parties": "parties",
            "transactions": "transactions",
            "deductions": "deductions",
        }.get(key, key)
        st.markdown(f"**{_t(label) if label in _UI['en'] else _field_label(key)}**")

        if kind == "parties":
            chips = []
            for p in raw:
                if not isinstance(p, dict):
                    continue
                name = p.get("name") or "—"
                role = f" ({p['role']})" if p.get("role") else ""
                chips.append(
                    f'<span class="di-party-chip">{html.escape(str(name) + role)}</span>'
                )
            if chips:
                st.markdown(
                    f'<div class="{dir_cls.strip()}">' + "".join(chips) + "</div>",
                    unsafe_allow_html=True,
                )
        elif kind == "strings":
            chips = [
                f'<span class="di-party-chip">{html.escape(str(v))}</span>'
                for v in raw
                if v
            ]
            if chips:
                st.markdown(
                    f'<div class="{dir_cls.strip()}">' + "".join(chips) + "</div>",
                    unsafe_allow_html=True,
                )
        elif kind == "transactions":
            table = [
                {
                    "date": (row.get("date") or "") if isinstance(row, dict) else "",
                    "description": (row.get("description") or "")
                    if isinstance(row, dict)
                    else "",
                    "amount": (row.get("amount") or "") if isinstance(row, dict) else "",
                    "balance": (row.get("balance") or "") if isinstance(row, dict) else "",
                }
                for row in raw
            ]
            st.dataframe(table, use_container_width=True, hide_index=True)
        elif kind == "named_amounts":
            table = [
                {
                    "name": (row.get("name") or "") if isinstance(row, dict) else "",
                    "amount": (row.get("amount") or "") if isinstance(row, dict) else "",
                }
                for row in raw
            ]
            st.dataframe(table, use_container_width=True, hide_index=True)
        else:
            table = [
                {
                    "description": (row.get("description") or "")
                    if isinstance(row, dict)
                    else "",
                    "quantity": (row.get("quantity") or "")
                    if isinstance(row, dict)
                    else "",
                    "unit_price": (row.get("unit_price") or "")
                    if isinstance(row, dict)
                    else "",
                    "line_total": (row.get("line_total") or "")
                    if isinstance(row, dict)
                    else "",
                }
                for row in raw
            ]
            st.dataframe(table, use_container_width=True, hide_index=True)

    notes = data.get("confidence_notes")
    if notes:
        st.info(f"{_t('extraction_notes')}: {notes}")


def _render_copy_row(
    fields: list[tuple[str, str | None]],
    *,
    key_prefix: str,
) -> None:
    present = [(k, v) for k, v in fields if v]
    if not present:
        return
    cols = st.columns(len(present))
    for col, (key, val), i in zip(cols, present, range(len(present))):
        with col:
            st.code(str(val), language=None)
            st.caption(f"{_field_label(key)} · {_t('copy_value')}")


def _batch_summary_row(r: ProcessingResult) -> dict[str, str]:
    if not r.success:
        summary = r.error_message or _t("failed")
        status = _t("failed")
    elif r.doc_type == "unknown" and r.structured is None:
        summary = _t("unknown_ok")
        status = _t("ok")
    elif r.structured is not None:
        data = r.structured.model_dump()
        spec = get_type_spec(r.doc_type or "other")
        keys: list[str] = []
        if spec:
            keys.extend(spec.highlight_fields)
            keys.extend(spec.primary_fields[:3])
        parts: list[str] = []
        seen: set[str] = set()
        for k in keys:
            v = data.get(k)
            if v is None or isinstance(v, (list, dict)):
                continue
            s = str(v).strip()
            if s and s not in seen:
                seen.add(s)
                parts.append(s)
            if len(parts) >= 3:
                break
        if not parts and data.get("summary"):
            parts.append(str(data["summary"]))
        if not parts and data.get("title"):
            parts.append(str(data["title"]))
        summary = " · ".join(parts) if parts else "—"
        status = _t("ok")
    else:
        summary = "—"
        status = _t("ok")
    return {
        _t("col_file"): r.filename,
        _t("col_type"): _type_label(r.doc_type),
        _t("col_summary"): summary,
        _t("col_status"): status,
    }




def _process_file_list(files: list[tuple[str, bytes]]) -> None:
    """Run the pipeline on (name, bytes) pairs and store results in session state."""
    if not files:
        return
    if len(files) > _MAX_FILES_PER_RUN:
        st.error(
            f"Demo limit: analyze at most {_MAX_FILES_PER_RUN} files per run."
            if not _is_he()
            else f"מגבלת הדגמה: עד {_MAX_FILES_PER_RUN} קבצים בהרצה."
        )
        return

    results: list[ProcessingResult] = []
    blobs: dict[str, bytes] = {}
    progress_slot = st.empty()
    progress_slot.progress(0.0, text=_t("stage_start"))
    status = st.empty()
    status.caption(_t("eta"))

    n = len(files)
    for idx, (name, data) in enumerate(files):
        if len(data) > _MAX_FILE_BYTES:
            results.append(
                ProcessingResult(
                    filename=name,
                    success=False,
                    error_message=(
                        f"File exceeds demo size limit "
                        f"({_MAX_FILE_BYTES // (1024 * 1024)} MB)."
                    ),
                )
            )
            continue

        blobs[name] = data
        progress_slot.progress(idx / max(n, 1), text=f"{name}…")

        stage_box = st.empty()

        def _on_stage(msg: str, _box=stage_box, _name=name) -> None:
            _box.info(f"**{_name}** — {msg}")

        with st.status(f"Processing **{name}**", expanded=True) as s:
            s.write(_t("eta"))
            result = process_pdf_bytes(name, data, on_stage=_on_stage)
            if result.success:
                s.update(label=f"Done: **{name}**", state="complete")
                if result.latency_ms is not None:
                    s.write(_t("latency", sec=result.latency_ms / 1000))
            else:
                s.update(label=f"Issue: **{name}**", state="error")
                if result.error_message:
                    s.write(result.error_message)
            results.append(result)

        stage_box.empty()
        progress_slot.progress((idx + 1) / n, text=f"{idx + 1}/{n}")

    st.session_state["last_results"] = results
    st.session_state["pdf_blobs"] = blobs
    progress_slot.empty()
    status.empty()


def _render_hero() -> None:
    rtl = ' style="direction:rtl;text-align:right;"' if _is_he() else ""
    st.markdown(
        f"""
        <div class="di-hero"{rtl}>
          <h1>{html.escape(_t("brand"))}</h1>
          <div class="sub">{html.escape(_t("brand_he_sub"))}</div>
          <p class="value">{html.escape(_t("value"))}</p>
          <div class="di-chips">
            <span class="di-chip">{html.escape(_t("chip_types"))}</span>
            <span class="di-chip">{html.escape(_t("chip_lang"))}</span>
            <span class="di-chip">{html.escape(_t("chip_time"))}</span>
          </div>
          <div class="di-steps">
            <div class="di-step">{html.escape(_t("step1"))}</div>
            <div class="di-step">{html.escape(_t("step2"))}</div>
            <div class="di-step">{html.escape(_t("step3"))}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sample_buttons() -> None:
    samples = _samples_for_ui_lang()
    st.markdown(f"**{_t('samples_title')}**")
    cols = st.columns(max(len(samples), 1))
    for col, sample in zip(cols, samples):
        filename, teaser_en, teaser_he, btn_en, btn_he, featured = sample
        with col:
            label = btn_he if _is_he() else btn_en
            teaser = teaser_he if _is_he() else teaser_en
            if st.button(
                label,
                key=f"sample_{filename}",
                use_container_width=True,
                type="primary" if featured else "secondary",
            ):
                try:
                    data = _load_sample(filename)
                except FileNotFoundError:
                    st.error(
                        f"Sample missing: {filename}. "
                        "Regenerate with scripts/generate_samples.py."
                    )
                    return
                st.session_state["featured_prompt_dismissed"] = True
                _process_file_list([(filename, data)])
                st.rerun()
            st.caption(teaser)


def _render_empty_state() -> None:
    rtl = " di-rtl" if _is_he() else ""
    st.markdown(
        f"""
        <div class="di-empty{rtl}">
          <h3>{html.escape(_t("empty_title"))}</h3>
          <p>{html.escape(_t("empty_body").replace("**", ""))}</p>
          <p>{html.escape(_t("empty_fields"))}</p>
          <p><em>{html.escape(_t("empty_hint"))}</em></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_results(results: list[ProcessingResult], blobs: dict[str, bytes]) -> None:
    ok = sum(1 for r in results if r.success)
    total = len(results)
    type_counts: dict[str, int] = {}
    for r in results:
        if r.doc_type:
            type_counts[r.doc_type] = type_counts.get(r.doc_type, 0) + 1
    type_bits = " · ".join(
        f"{_type_label(k)}: {v}" for k, v in sorted(type_counts.items())
    )
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    lat_txt = ""
    if latencies:
        lat_txt = " · " + _t("latency", sec=sum(latencies) / 1000)

    rtl = " di-rtl" if _is_he() else ""
    st.markdown(
        f"""
        <div class="di-summary{rtl}">
          <strong>{html.escape(_t("ready"))}</strong><br/>
          {html.escape(_t("summary_ok", ok=ok, total=total))}
          {(" · " + html.escape(type_bits)) if type_bits else ""}
          {html.escape(lat_txt)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        st.download_button(
            _t("download_json"),
            data=results_to_json_bytes(results),
            file_name=f"{branded_export_basename()}.json",
            mime="application/json",
            key="dl_json_all",
        )
    with c2:
        st.download_button(
            _t("download_csv"),
            data=results_to_csv_bytes(results),
            file_name=f"{branded_export_basename()}.csv",
            mime="text/csv",
            key="dl_csv_all",
        )
    with c3:
        if st.button(_t("clear"), key="clear_results", use_container_width=True):
            st.session_state["last_results"] = []
            st.session_state["pdf_blobs"] = {}
            st.rerun()
    with c4:
        if st.button(
            _t("analyze_another"),
            key="analyze_another",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["last_results"] = []
            st.session_state["pdf_blobs"] = {}
            st.rerun()

    st.markdown(f"### {_t('results')}")

    if len(results) > 1:
        st.markdown(f"**{_t('batch_table')}**")
        st.dataframe(
            [_batch_summary_row(r) for r in results],
            use_container_width=True,
            hide_index=True,
        )

    multi = len(results) > 1
    for r in results:
        with st.expander(r.filename, expanded=not multi):
            blob = blobs.get(r.filename)
            meta_bits: list[str] = []
            if r.latency_ms is not None:
                meta_bits.append(_t("latency", sec=r.latency_ms / 1000))
            if r.used_ocr:
                meta_bits.append(_t("used_ocr"))
            if meta_bits:
                st.caption(" · ".join(meta_bits))

            if not r.success:
                st.error(r.error_message or "Processing failed.")
                if r.warnings:
                    st.caption(f"{_t('warnings')}: " + " · ".join(r.warnings))
                err_left, err_right = st.columns(2)
                with err_left:
                    st.markdown(f"**{_t('original_pdf')}**")
                    if blob:
                        _render_pdf_preview(blob, r.filename)
                    else:
                        st.caption(_t("no_pdf"))
                with err_right:
                    st.markdown(f"**{_t('text_preview')}**")
                    if r.raw_text_preview:
                        st.text_area(
                            "preview",
                            r.raw_text_preview,
                            height=280,
                            label_visibility="collapsed",
                            key=f"err_prev_{r.filename}",
                        )
                    else:
                        st.caption(_t("no_text"))
                continue

            st.markdown(f"**{_t('classification')}**")
            st.markdown(_doc_type_badge_html(r.doc_type), unsafe_allow_html=True)
            if r.classification_confidence_note:
                st.info(f"{_t('confidence')}: {r.classification_confidence_note}")

            st.download_button(
                _t("per_doc_json"),
                data=single_result_to_json_bytes(r),
                file_name=f"{Path(r.filename).stem}_extraction.json",
                mime="application/json",
                key=f"dl_one_{r.filename}",
            )

            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown(f"**{_t('original_pdf')}**")
                if blob:
                    _render_pdf_preview(blob, r.filename)
                else:
                    st.caption(_t("no_pdf"))

            with c_right:
                st.markdown(f"**{_t('extracted_data')}**")
                if r.warnings:
                    st.caption(f"{_t('warnings')}: " + " · ".join(r.warnings))
                if r.doc_type == "unknown":
                    st.warning(_t("unknown_ok"))
                elif r.structured is not None:
                    _render_structured_cards(r.structured, result=r)
                    with st.expander(_t("json_raw")):
                        st.json(r.structured.model_dump())
                else:
                    st.warning(_t("no_fields"))

            if r.raw_text_preview:
                with st.expander(_t("text_preview")):
                    st.text(r.raw_text_preview)


def _render_footer() -> None:
    with st.expander(_t("about"), expanded=False):
        st.write(_t("about_body"))
        st.caption(
            _t(
                "footer_limits",
                max_files=_MAX_FILES_PER_RUN,
                max_mb=_MAX_FILE_BYTES // (1024 * 1024),
            )
        )
        st.caption(_t("footer_tech"))
    st.markdown(
        f'<div class="di-footer">{html.escape(_t("footer_tech"))}<br/>'
        f'{html.escape(_t("footer_limits", max_files=_MAX_FILES_PER_RUN, max_mb=_MAX_FILE_BYTES // (1024 * 1024)))}'
        f"</div>",
        unsafe_allow_html=True,
    )


def _run_featured_demo() -> None:
    """One-click featured sample for the active UI language."""
    featured = _featured_sample()
    try:
        data = _load_sample(featured)
    except FileNotFoundError:
        st.error(
            f"Sample missing: {featured}. "
            "Regenerate with scripts/generate_samples.py."
        )
        return
    st.session_state["featured_prompt_dismissed"] = True
    with st.spinner(_t("running_demo")):
        _process_file_list([(featured, data)])
    st.rerun()


def main() -> None:
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "en"

    st.markdown(_PAGE_STYLE, unsafe_allow_html=True)

    # Language toggle
    lang_cols = st.columns([6, 2, 2])
    with lang_cols[1]:
        if st.button("EN", key="lang_en", use_container_width=True):
            st.session_state["ui_lang"] = "en"
            st.rerun()
    with lang_cols[2]:
        if st.button("עב", key="lang_he", use_container_width=True):
            st.session_state["ui_lang"] = "he"
            st.rerun()

    _render_hero()

    results_early: list[ProcessingResult] = st.session_state.get("last_results", [])
    if not results_early and not st.session_state.get("featured_prompt_dismissed"):
        f1, f2 = st.columns([3, 1])
        with f1:
            st.info(
                ("מומלץ: הרץ את חשבונית הדוגמה בעברית (₪) להדגמה מלאה.")
                if _is_he()
                else "Recommended: run the featured English invoice (USD) for a full demo."
            )
        with f2:
            if st.button(
                _t("auto_run"),
                key="run_featured",
                type="primary",
                use_container_width=True,
            ):
                _run_featured_demo()
        s1, s2 = st.columns([3, 1])
        with s2:
            if st.button(_t("skip_auto"), key="skip_featured", use_container_width=True):
                st.session_state["featured_prompt_dismissed"] = True
                st.rerun()

    _render_sample_buttons()

    st.markdown("---")
    st.markdown(f"**{_t('upload_title')}**")
    st.caption(
        _t(
            "upload_help",
            max_files=_MAX_FILES_PER_RUN,
            max_mb=_MAX_FILE_BYTES // (1024 * 1024),
        )
    )

    uploaded = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    col_run, _ = st.columns([1, 4])
    with col_run:
        run = st.button(
            _t("analyze"),
            type="primary",
            disabled=not uploaded,
            use_container_width=True,
        )

    if run and uploaded:
        st.session_state["featured_prompt_dismissed"] = True
        files_list = list(uploaded)[:_MAX_FILES_PER_RUN]
        if len(uploaded) > _MAX_FILES_PER_RUN:
            st.warning(
                f"Only the first {_MAX_FILES_PER_RUN} files will be analyzed (demo limit)."
            )
        prepared: list[tuple[str, bytes]] = [
            (f.name, f.getvalue()) for f in files_list
        ]
        _process_file_list(prepared)
        st.rerun()

    results: list[ProcessingResult] = st.session_state.get("last_results", [])
    blobs = st.session_state.get("pdf_blobs", {})

    if not results:
        _render_empty_state()
        _render_footer()
        return

    _render_results(results, blobs)
    _render_footer()


if __name__ == "__main__":
    main()

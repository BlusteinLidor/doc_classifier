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
from doc_intel.models import (
    ContractExtraction,
    InvoiceExtraction,
    ProcessingResult,
    ReceiptExtraction,
    StructuredExtraction,
)
from doc_intel.pipeline import process_pdf_bytes

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
_FEATURED_SAMPLE = "sample_invoice_he.pdf"

# (filename, teaser_en, teaser_he, button_en, button_he, featured)
_SAMPLE_DOCS: list[tuple[str, str, str, str, str, bool]] = [
    (
        "sample_invoice_en.pdf",
        "USD totals · vendor & line items",
        "סכומים בדולר · ספק ופריטים",
        "English invoice",
        "חשבונית אנגלית",
        False,
    ),
    (
        "sample_invoice_he.pdf",
        "₪ amounts · Hebrew vendor (featured)",
        "סכומים ₪ · ספק בעברית (מומלץ)",
        "Hebrew invoice ⭐",
        "חשבונית בעברית ⭐",
        True,
    ),
    (
        "sample_contract_en.pdf",
        "Two parties · governing law",
        "שני צדדים · דין חל",
        "English contract",
        "חוזה באנגלית",
        False,
    ),
    (
        "sample_contract_he.pdf",
        "Hebrew parties · key terms",
        "צדדים בעברית · תנאים עיקריים",
        "Hebrew contract",
        "חוזה בעברית",
        False,
    ),
    (
        "sample_receipt_en.pdf",
        "Merchant slip · payment method",
        "קבלה · אמצעי תשלום",
        "English receipt",
        "קבלה באנגלית",
        False,
    ),
]

_UI: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Document Intelligence — Portfolio Demo",
        "brand": "AI Document Intelligence",
        "brand_he_sub": "בינה מלאכותית למסמכים",
        "value": "Upload a PDF. Get type + key fields in seconds.",
        "chip_types": "Invoice · Contract · Receipt",
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
        "chip_types": "חשבונית · חוזה · קבלה",
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
    "invoice_number": ("Invoice #", "מס׳ חשבונית"),
    "invoice_date": ("Invoice date", "תאריך חשבונית"),
    "invoice_date_iso": ("Date (ISO)", "תאריך (ISO)"),
    "total_amount": ("Total", "סה״כ"),
    "total_amount_value": ("Total (numeric)", "סה״כ (מספר)"),
    "currency": ("Currency", "מטבע"),
    "tax_id": ("Tax ID", "ח.פ / ע.מ"),
    "title": ("Title", "כותרת"),
    "effective_date": ("Effective date", "תאריך תחילה"),
    "effective_date_iso": ("Effective (ISO)", "תחילה (ISO)"),
    "end_date": ("End date", "תאריך סיום"),
    "end_date_iso": ("End (ISO)", "סיום (ISO)"),
    "governing_law": ("Governing law", "דין חל"),
    "key_terms_summary": ("Key terms", "תנאים עיקריים"),
    "merchant": ("Merchant", "בית עסק"),
    "receipt_number": ("Receipt #", "מס׳ קבלה"),
    "receipt_date": ("Receipt date", "תאריך קבלה"),
    "receipt_date_iso": ("Date (ISO)", "תאריך (ISO)"),
    "payment_method": ("Payment", "אמצעי תשלום"),
    "confidence_notes": ("Notes", "הערות"),
}

_TYPE_LABELS: dict[str, tuple[str, str]] = {
    "invoice": ("Invoice", "חשבונית"),
    "contract": ("Contract", "חוזה"),
    "receipt": ("Receipt", "קבלה"),
    "unknown": ("Unknown", "לא ידוע"),
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
.doc-badge-invoice { background: #dbeafe; color: #1e3a8a; }
.doc-badge-contract { background: #dcfce7; color: #14532d; }
.doc-badge-receipt { background: #fef3c7; color: #92400e; }
.doc-badge-unknown { background: #f3f4f6; color: #374151; }
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
    css_map = {
        "invoice": "doc-badge-invoice",
        "contract": "doc-badge-contract",
        "receipt": "doc-badge-receipt",
        "unknown": "doc-badge-unknown",
    }
    css = css_map.get(dt, "doc-badge-unknown")
    label = _type_label(dt)
    return f'<div class="doc-badge {css}">{html.escape(label)}</div>'


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

    if isinstance(obj, InvoiceExtraction):
        amount = obj.total_amount or ""
        cur = obj.currency or ""
        hero = f"{amount} {cur}".strip()
        if hero:
            st.markdown(
                f'<div class="di-hero-amount{dir_cls}">{html.escape(hero)}</div>',
                unsafe_allow_html=True,
            )
        html_block = _field_rows_html(
            [
                ("vendor", obj.vendor),
                ("invoice_number", obj.invoice_number),
                ("invoice_date", obj.invoice_date),
                ("invoice_date_iso", obj.invoice_date_iso),
                ("total_amount", obj.total_amount),
                (
                    "total_amount_value",
                    None
                    if obj.total_amount_value is None
                    else str(obj.total_amount_value),
                ),
                ("currency", obj.currency),
                ("tax_id", obj.tax_id),
                ("buyer", obj.buyer),
            ],
            preview=preview,
        )
        if html_block:
            st.markdown(html_block, unsafe_allow_html=True)
        _render_copy_row(
            [
                ("vendor", obj.vendor),
                ("invoice_number", obj.invoice_number),
                ("total_amount", obj.total_amount),
            ],
            key_prefix=f"cp_{result.filename}_inv",
        )
        if obj.line_items:
            st.markdown(f"**{_t('line_items')}**")
            table = [
                {
                    "description": li.description or "",
                    "quantity": li.quantity or "",
                    "unit_price": li.unit_price or "",
                    "line_total": li.line_total or "",
                }
                for li in obj.line_items
            ]
            st.dataframe(table, use_container_width=True, hide_index=True)
        if obj.confidence_notes:
            st.info(f"{_t('extraction_notes')}: {obj.confidence_notes}")

    elif isinstance(obj, ContractExtraction):
        if obj.title:
            st.markdown(
                f'<div class="di-hero-title{dir_cls}">{html.escape(obj.title)}</div>',
                unsafe_allow_html=True,
            )
        if obj.parties:
            st.markdown(f"**{_t('parties')}**")
            chips = []
            for p in obj.parties:
                name = p.name or "—"
                role = f" ({p.role})" if p.role else ""
                chips.append(
                    f'<span class="di-party-chip">{html.escape(name + role)}</span>'
                )
            st.markdown(
                f'<div class="{dir_cls.strip()}">' + "".join(chips) + "</div>",
                unsafe_allow_html=True,
            )
        html_block = _field_rows_html(
            [
                ("effective_date", obj.effective_date),
                ("effective_date_iso", obj.effective_date_iso),
                ("end_date", obj.end_date),
                ("end_date_iso", obj.end_date_iso),
                ("governing_law", obj.governing_law),
            ],
            preview=preview,
        )
        if html_block:
            st.markdown(html_block, unsafe_allow_html=True)
        if obj.key_terms_summary:
            st.markdown(f"**{_t('key_terms')}**")
            st.markdown(
                f'<div class="di-field-card{dir_cls}">'
                f"{html.escape(obj.key_terms_summary)}</div>",
                unsafe_allow_html=True,
            )
        _render_copy_row(
            [
                ("title", obj.title),
                ("governing_law", obj.governing_law),
            ],
            key_prefix=f"cp_{result.filename}_ctr",
        )
        if obj.confidence_notes:
            st.info(f"{_t('extraction_notes')}: {obj.confidence_notes}")

    elif isinstance(obj, ReceiptExtraction):
        amount = obj.total_amount or ""
        cur = obj.currency or ""
        hero = f"{amount} {cur}".strip()
        if hero:
            st.markdown(
                f'<div class="di-hero-amount{dir_cls}">{html.escape(hero)}</div>',
                unsafe_allow_html=True,
            )
        html_block = _field_rows_html(
            [
                ("merchant", obj.merchant),
                ("receipt_number", obj.receipt_number),
                ("receipt_date", obj.receipt_date),
                ("receipt_date_iso", obj.receipt_date_iso),
                ("total_amount", obj.total_amount),
                (
                    "total_amount_value",
                    None
                    if obj.total_amount_value is None
                    else str(obj.total_amount_value),
                ),
                ("currency", obj.currency),
                ("payment_method", obj.payment_method),
            ],
            preview=preview,
        )
        if html_block:
            st.markdown(html_block, unsafe_allow_html=True)
        _render_copy_row(
            [
                ("merchant", obj.merchant),
                ("receipt_number", obj.receipt_number),
                ("total_amount", obj.total_amount),
            ],
            key_prefix=f"cp_{result.filename}_rcp",
        )
        if obj.items:
            st.markdown(f"**{_t('items')}**")
            table = [
                {
                    "description": li.description or "",
                    "quantity": li.quantity or "",
                    "unit_price": li.unit_price or "",
                    "line_total": li.line_total or "",
                }
                for li in obj.items
            ]
            st.dataframe(table, use_container_width=True, hide_index=True)
        if obj.confidence_notes:
            st.info(f"{_t('extraction_notes')}: {obj.confidence_notes}")


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
    elif r.doc_type == "unknown":
        summary = _t("unknown_ok")
        status = _t("ok")
    elif isinstance(r.structured, InvoiceExtraction):
        parts = [p for p in [r.structured.vendor, r.structured.total_amount] if p]
        summary = " · ".join(parts) if parts else "—"
        status = _t("ok")
    elif isinstance(r.structured, ContractExtraction):
        title = r.structured.title or "—"
        n = len(r.structured.parties)
        summary = f"{title} ({n} parties)" if n else title
        status = _t("ok")
    elif isinstance(r.structured, ReceiptExtraction):
        parts = [p for p in [r.structured.merchant, r.structured.total_amount] if p]
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
    st.markdown(f"**{_t('samples_title')}**")
    cols = st.columns(len(_SAMPLE_DOCS))
    for col, sample in zip(cols, _SAMPLE_DOCS):
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
    """One-click featured sample (Hebrew invoice)."""
    try:
        data = _load_sample(_FEATURED_SAMPLE)
    except FileNotFoundError:
        st.error(
            f"Sample missing: {_FEATURED_SAMPLE}. "
            "Regenerate with scripts/generate_samples.py."
        )
        return
    st.session_state["featured_prompt_dismissed"] = True
    with st.spinner(_t("running_demo")):
        _process_file_list([(_FEATURED_SAMPLE, data)])
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
                ("מומלץ: הרץ את חשבונית הדוגמה בעברית להדגמה מלאה.")
                if _is_he()
                else "Recommended: run the featured Hebrew invoice for a full demo."
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

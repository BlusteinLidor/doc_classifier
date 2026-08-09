"""Generate synthetic sample PDFs for the portfolio demo (no real PII)."""

from __future__ import annotations

import logging
from pathlib import Path

import fitz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[1]
_SAMPLES = _ROOT / "samples"

# Arial Unicode MS / David often unavailable on CI; use built-in fonts +
# embed Hebrew via a system TTF if present, else fall back to Latin-only note.
_HEBREW_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\arialuni.ttf"),
    Path(r"C:\Windows\Fonts\david.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
]


def _find_unicode_font() -> Path | None:
    for path in _HEBREW_FONT_CANDIDATES:
        if path.is_file():
            return path
    return None


def _write_page(doc: fitz.Document, lines: list[tuple[str, float]], fontfile: Path | None) -> None:
    page = doc.new_page(width=595, height=842)  # A4
    y = 72.0
    for text, size in lines:
        if fontfile is not None:
            page.insert_text(
                (72, y),
                text,
                fontsize=size,
                fontname="uni",
                fontfile=str(fontfile),
            )
        else:
            page.insert_text((72, y), text, fontsize=size, fontname="helv")
        y += size * 1.6


def generate_invoice_en(out: Path) -> None:
    doc = fitz.open()
    lines: list[tuple[str, float]] = [
        ("INVOICE", 18),
        ("", 12),
        ("Vendor: Northwind Supplies Ltd.", 11),
        ("Buyer: Acme Demo Co.", 11),
        ("Invoice number: INV-DEMO-1042", 11),
        ("Invoice date: 2025-03-15", 11),
        ("Tax ID: 512345678", 11),
        ("", 11),
        ("Line items:", 12),
        ("  Consulting services  x 10 hrs  @ 150.00  = 1500.00", 10),
        ("  Software license     x 1       @ 299.00  = 299.00", 10),
        ("", 11),
        ("Subtotal: 1799.00 USD", 11),
        ("VAT (17%): 305.83 USD", 11),
        ("Total amount: 2104.83 USD", 12),
        ("Currency: USD", 11),
        ("", 11),
        ("(Synthetic portfolio sample — not a real invoice.)", 9),
    ]
    _write_page(doc, lines, None)
    doc.save(out)
    doc.close()
    logger.info("Wrote %s", out)


def generate_invoice_he(out: Path, fontfile: Path | None) -> None:
    doc = fitz.open()
    lines: list[tuple[str, float]] = [
        ("חשבונית מס", 18),
        ("", 12),
        ("ספק: חברת דוגמה בע״מ", 11),
        ("לקוח: לקוח הדגמה בע״מ", 11),
        ("מספר חשבונית: INV-HE-2201", 11),
        ("תאריך: 12/01/2025", 11),
        ("ע.מ / ח.פ: 514567890", 11),
        ("", 11),
        ("פריטים:", 12),
        ("  שירותי ייעוץ אוטומציה  —  8 שעות  ×  ₪400  =  ₪3200", 10),
        ("  הטמעת מערכת             —  1 יחידה ×  ₪900  =  ₪900", 10),
        ("", 11),
        ("סה״כ לפני מע״מ: ₪4100", 11),
        ("מע״מ 17%: ₪697", 11),
        ("סה״כ לתשלום: ₪4797", 12),
        ("מטבע: ILS", 11),
        ("", 11),
        ("(מסמך דוגמה לתיק עבודות — אינו מסמך אמיתי.)", 9),
    ]
    if fontfile is None:
        logger.warning(
            "No Unicode TTF found; Hebrew invoice will use ASCII transliteration fallback."
        )
        lines = [
            ("INVOICE (Hebrew sample — font fallback)", 16),
            ("", 12),
            ("Vendor: Dogma Demo Ltd. (HE)", 11),
            ("Buyer: Lakoach Demo Ltd. (HE)", 11),
            ("Invoice number: INV-HE-2201", 11),
            ("Invoice date: 12/01/2025", 11),
            ("Tax ID: 514567890", 11),
            ("", 11),
            ("Line items:", 12),
            ("  Automation consulting  8 hrs x 400 ILS = 3200", 10),
            ("  System setup           1 x 900 ILS = 900", 10),
            ("", 11),
            ("Subtotal: 4100 ILS", 11),
            ("VAT 17%: 697 ILS", 11),
            ("Total amount: 4797 ILS", 12),
            ("Currency: ILS", 11),
            ("", 11),
            ("(Synthetic portfolio sample — not a real invoice.)", 9),
        ]
        _write_page(doc, lines, None)
    else:
        _write_page(doc, lines, fontfile)
    doc.save(out)
    doc.close()
    logger.info("Wrote %s", out)


def generate_contract_en(out: Path) -> None:
    doc = fitz.open()
    lines: list[tuple[str, float]] = [
        ("SERVICE AGREEMENT", 18),
        ("", 12),
        ("Title: Website Automation Support Agreement", 11),
        ("", 11),
        ("Parties:", 12),
        ("  1. Provider: BrightOps Consulting LLC (contractor)", 11),
        ("  2. Client: Harbor Bakery Inc. (client)", 11),
        ("", 11),
        ("Effective date: 2025-01-01", 11),
        ("End date: 2025-12-31", 11),
        ("Governing law: State of Delaware, USA", 11),
        ("", 11),
        ("Key terms:", 12),
        ("  The Provider shall deliver monthly automation reports,", 10),
        ("  maintain the Client's lead-intake scripts, and respond to", 10),
        ("  priority tickets within two business days. Fees are billed", 10),
        ("  monthly in advance. Either party may terminate with 30 days", 10),
        ("  written notice. Confidential information remains protected", 10),
        ("  for two years after termination.", 10),
        ("", 11),
        ("(Synthetic portfolio sample — not a real contract.)", 9),
    ]
    _write_page(doc, lines, None)
    doc.save(out)
    doc.close()
    logger.info("Wrote %s", out)


def generate_contract_he(out: Path, fontfile: Path | None) -> None:
    doc = fitz.open()
    lines: list[tuple[str, float]] = [
        ("הסכם שירותים", 18),
        ("", 12),
        ("כותרת: הסכם תמיכה באוטומציה עסקית", 11),
        ("", 11),
        ("צדדים:", 12),
        ("  1. ספק: חברת ברייטאופס ייעוץ בע״מ (קבלן)", 11),
        ("  2. לקוח: מאפיית הנמל בע״מ (לקוח)", 11),
        ("", 11),
        ("תאריך תחילה: 01/01/2025", 11),
        ("תאריך סיום: 31/12/2025", 11),
        ("דין חל: מדינת ישראל", 11),
        ("", 11),
        ("תנאים עיקריים:", 12),
        ("  הספק יספק דוחות אוטומציה חודשיים, יתחזק", 10),
        ("  סקריפטים לקליטת לידים, ויגיב לפניות דחופות", 10),
        ("  תוך שני ימי עסקים. התשלום חודשי מראש.", 10),
        ("  כל צד רשאי לבטל בהודעה של 30 יום.", 10),
        ("  סודיות נשמרת למשך שנתיים לאחר סיום ההסכם.", 10),
        ("", 11),
        ("(מסמך דוגמה לתיק עבודות — אינו חוזה אמיתי.)", 9),
    ]
    if fontfile is None:
        logger.warning("No Unicode TTF; Hebrew contract uses Latin fallback.")
        lines = [
            ("SERVICE AGREEMENT (Hebrew sample — font fallback)", 16),
            ("", 12),
            ("Title: Business Automation Support Agreement (HE)", 11),
            ("Parties:", 12),
            ("  1. Provider: BrightOps Consulting Ltd. (contractor)", 11),
            ("  2. Client: Namal Bakery Ltd. (client)", 11),
            ("Effective date: 01/01/2025", 11),
            ("End date: 31/12/2025", 11),
            ("Governing law: State of Israel", 11),
            ("Key terms: Monthly automation reports; 2-day ticket SLA;", 10),
            ("  monthly fees; 30-day termination; 2-year confidentiality.", 10),
            ("(Synthetic portfolio sample — not a real contract.)", 9),
        ]
        _write_page(doc, lines, None)
    else:
        _write_page(doc, lines, fontfile)
    doc.save(out)
    doc.close()
    logger.info("Wrote %s", out)


def generate_receipt_en(out: Path) -> None:
    doc = fitz.open()
    lines: list[tuple[str, float]] = [
        ("SALES RECEIPT", 18),
        ("", 12),
        ("Merchant: Harbor Corner Market", 11),
        ("Receipt number: RCP-88421", 11),
        ("Date: 2025-06-18", 11),
        ("", 11),
        ("Items:", 12),
        ("  Espresso beans 250g     1 x 12.50  = 12.50", 10),
        ("  Oat milk cartons        2 x  3.40  =  6.80", 10),
        ("", 11),
        ("Subtotal: 19.30 USD", 11),
        ("Tax: 1.54 USD", 11),
        ("Total amount: 20.84 USD", 12),
        ("Currency: USD", 11),
        ("Payment method: Visa ****4219", 11),
        ("", 11),
        ("(Synthetic portfolio sample — not a real receipt.)", 9),
    ]
    _write_page(doc, lines, None)
    doc.save(out)
    doc.close()
    logger.info("Wrote %s", out)


def main() -> None:
    _SAMPLES.mkdir(parents=True, exist_ok=True)
    font = _find_unicode_font()
    if font:
        logger.info("Using Unicode font: %s", font)
    generate_invoice_en(_SAMPLES / "sample_invoice_en.pdf")
    generate_invoice_he(_SAMPLES / "sample_invoice_he.pdf", font)
    generate_contract_en(_SAMPLES / "sample_contract_en.pdf")
    generate_contract_he(_SAMPLES / "sample_contract_he.pdf", font)
    generate_receipt_en(_SAMPLES / "sample_receipt_en.pdf")
    logger.info("All samples written to %s", _SAMPLES)


if __name__ == "__main__":
    main()

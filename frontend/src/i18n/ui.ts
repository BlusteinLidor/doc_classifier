export type Lang = "en" | "he";

export const UI: Record<Lang, Record<string, string>> = {
  en: {
    page_title: "AI Document Intelligence",
    brand: "AI Document Intelligence",
    brand_sub: "בינה מלאכותית למסמכים",
    value: "Upload a PDF. Get the type and key fields in seconds.",
    auto_run: "Run featured demo",
    hero_hint: "Uses the Hebrew invoice sample — no upload needed",
    skip_auto: "Browse samples",
    samples_title: "Try a sample",
    samples_desc: "One click. No file required.",
    upload_title: "Or upload your own PDFs",
    upload_help:
      "Demo limit: max {max_files} files, {max_mb} MB each · text PDFs preferred; image-only use vision OCR",
    upload_cta: "Choose PDF files",
    upload_drop: "Drop PDFs here or choose files",
    analyze: "Analyze documents",
    stage_extract: "Extract text",
    stage_classify: "Classify type",
    stage_structure: "Structure fields",
    processing: "Processing…",
    eta: "Usually 15–45 seconds depending on OpenAI.",
    results: "Results",
    ready: "Ready — key fields extracted",
    summary_ok: "{ok} of {total} OK",
    clear: "Clear results",
    analyze_another: "Analyze another",
    download_json: "Download JSON",
    download_csv: "Download CSV",
    per_doc_json: "This JSON",
    classification: "Classification",
    confidence: "Why this classification",
    extraction_notes: "Extraction notes",
    original_pdf: "Original PDF",
    extracted_data: "Extracted data",
    text_preview: "Text preview",
    json_raw: "Raw JSON",
    warnings: "Warnings",
    latency: "Processed in {sec:.1f}s",
    used_ocr: "Vision OCR used",
    no_pdf: "PDF not available for preview.",
    no_fields: "No structured fields returned.",
    unknown_ok: "Classified as unknown — no type-specific fields extracted.",
    failed: "Failed",
    ok: "OK",
    line_items: "Line items",
    parties: "Parties",
    key_terms: "Key terms",
    items: "Items",
    col_file: "File",
    col_type: "Type",
    col_summary: "Summary",
    col_status: "Status",
    batch_table: "Batch overview",
    footer_tech: "Tech: React · FastAPI · OpenAI · PyMuPDF · Pydantic V2",
    footer_limits:
      "Portfolio demo · sample data only · max {max_files} files / {max_mb} MB · OCR on image PDFs",
    about: "About this demo",
    about_body:
      "Portfolio demonstration only — not a client production system. No accounts or stored documents.",
    empty: "Pick a sample above or upload PDFs to start.",
    topbar_run: "Run demo",
    desc: "Description",
    qty: "Qty",
    unit_price: "Unit price",
    line_total: "Total",
  },
  he: {
    page_title: "בינה מלאכותית למסמכים",
    brand: "בינה מלאכותית למסמכים",
    brand_sub: "AI Document Intelligence",
    value: "העלו PDF. קבלו סוג מסמך ושדות מפתח תוך שניות.",
    auto_run: "הדגמה מומלצת",
    hero_hint: "משתמש בחשבונית לדוגמה בעברית — בלי העלאה",
    skip_auto: "עיינו בדוגמאות",
    samples_title: "נסו דוגמה",
    samples_desc: "לחיצה אחת. בלי קובץ.",
    upload_title: "או העלו PDF משלכם",
    upload_help:
      "מגבלת הדגמה: עד {max_files} קבצים, {max_mb} מ״ב · מומלץ PDF עם טקסט; סריקות משתמשות ב-OCR",
    upload_cta: "בחרו קבצי PDF",
    upload_drop: "גררו PDF לכאן או בחרו קבצים",
    analyze: "נתח מסמכים",
    stage_extract: "חילוץ טקסט",
    stage_classify: "סיווג סוג",
    stage_structure: "שדות מובנים",
    processing: "מעבד…",
    eta: "בדרך כלל 15–45 שניות, תלוי ב-OpenAI.",
    results: "תוצאות",
    ready: "מוכן — שדות מפתח חולצו",
    summary_ok: "{ok} מתוך {total} הצליחו",
    clear: "נקה תוצאות",
    analyze_another: "נתח עוד",
    download_json: "הורד JSON",
    download_csv: "הורד CSV",
    per_doc_json: "JSON של מסמך זה",
    classification: "סיווג",
    confidence: "מדוע סווג כך",
    extraction_notes: "הערות חילוץ",
    original_pdf: "PDF מקורי",
    extracted_data: "נתונים שחולצו",
    text_preview: "תצוגת טקסט",
    json_raw: "JSON גולמי",
    warnings: "אזהרות",
    latency: "עובד בתוך {sec:.1f} שנ׳",
    used_ocr: "נעשה שימוש ב-OCR",
    no_pdf: "אין PDF לתצוגה.",
    no_fields: "לא הוחזרו שדות מובנים.",
    unknown_ok: "סווג כלא ידוע — לא חולצו שדות ספציפיים.",
    failed: "נכשל",
    ok: "תקין",
    line_items: "פריטי שורה",
    parties: "צדדים",
    key_terms: "תנאים עיקריים",
    items: "פריטים",
    col_file: "קובץ",
    col_type: "סוג",
    col_summary: "סיכום",
    col_status: "סטטוס",
    batch_table: "סקירת האצווה",
    footer_tech: "טכנולוגיה: React · FastAPI · OpenAI · PyMuPDF · Pydantic V2",
    footer_limits:
      "הדגמת תיק עבודות · נתוני דוגמה · עד {max_files} קבצים / {max_mb} מ״ב · OCR לסריקות",
    about: "על ההדגמה",
    about_body:
      "הדגמה לתיק עבודות בלבד — לא מערכת לקוח. ללא חשבונות וללא שמירת מסמכים.",
    empty: "בחרו דוגמה למעלה או העלו PDF כדי להתחיל.",
    topbar_run: "הדגמה",
    desc: "תיאור",
    qty: "כמות",
    unit_price: "מחיר",
    line_total: "סה״כ",
  },
};

export const FIELD_LABELS: Record<string, [string, string]> = {
  vendor: ["Vendor", "ספק"],
  buyer: ["Buyer", "לקוח"],
  invoice_number: ["Invoice #", "מס׳ חשבונית"],
  invoice_date: ["Invoice date", "תאריך חשבונית"],
  invoice_date_iso: ["Date (ISO)", "תאריך (ISO)"],
  total_amount: ["Total", "סה״כ"],
  total_amount_value: ["Total (numeric)", "סה״כ (מספר)"],
  currency: ["Currency", "מטבע"],
  tax_id: ["Tax ID", "ח.פ / ע.מ"],
  title: ["Title", "כותרת"],
  effective_date: ["Effective date", "תאריך תחילה"],
  effective_date_iso: ["Effective (ISO)", "תחילה (ISO)"],
  end_date: ["End date", "תאריך סיום"],
  end_date_iso: ["End (ISO)", "סיום (ISO)"],
  governing_law: ["Governing law", "דין חל"],
  key_terms_summary: ["Key terms", "תנאים עיקריים"],
  merchant: ["Merchant", "בית עסק"],
  receipt_number: ["Receipt #", "מס׳ קבלה"],
  receipt_date: ["Receipt date", "תאריך קבלה"],
  receipt_date_iso: ["Date (ISO)", "תאריך (ISO)"],
  payment_method: ["Payment", "אמצעי תשלום"],
};

export const TYPE_LABELS: Record<string, [string, string]> = {
  invoice: ["Invoice", "חשבונית"],
  contract: ["Contract", "חוזה"],
  receipt: ["Receipt", "קבלה"],
  unknown: ["Unknown", "לא ידוע"],
};

export function t(
  lang: Lang,
  key: string,
  vars?: Record<string, string | number>,
): string {
  let text = UI[lang][key] ?? UI.en[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      // Support simple {key} and {key:.1f}
      text = text.replace(new RegExp(`\\{${k}(?::[^}]*)?\\}`, "g"), String(v));
    }
  }
  return text;
}

export function fieldLabel(lang: Lang, key: string): string {
  const pair = FIELD_LABELS[key];
  if (!pair) return key.replace(/_/g, " ");
  const [en, he] = pair;
  return lang === "he" ? `${he} / ${en}` : `${en} / ${he}`;
}

export function typeLabel(lang: Lang, docType: string | null | undefined): string {
  const dt = docType || "unknown";
  const pair = TYPE_LABELS[dt] ?? [dt, dt];
  return lang === "he" ? pair[1] : pair[0];
}

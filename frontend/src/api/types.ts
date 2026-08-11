export type DocType =
  | "invoice"
  | "credit_note"
  | "receipt"
  | "quote"
  | "purchase_order"
  | "delivery_note"
  | "contract"
  | "bank_statement"
  | "payslip"
  | "utility_bill"
  | "tax_document"
  | "correspondence"
  | "other"
  | "unknown";

export interface LineItem {
  description?: string | null;
  quantity?: string | null;
  unit_price?: string | null;
  line_total?: string | null;
}

export interface ContractParty {
  name?: string | null;
  role?: string | null;
}

export interface StatementLine {
  date?: string | null;
  description?: string | null;
  amount?: string | null;
  balance?: string | null;
}

export interface NamedAmount {
  name?: string | null;
  amount?: string | null;
}

/** Loose structured payload; FieldPanel uses doc_type + known keys. */
export type StructuredExtraction = Record<string, unknown>;

export interface ProcessingResult {
  filename: string;
  success: boolean;
  doc_type?: DocType | null;
  classification_confidence_note?: string | null;
  structured?: StructuredExtraction | null;
  raw_text_preview?: string;
  error_message?: string | null;
  warnings?: string[];
  latency_ms?: number | null;
  used_ocr?: boolean;
}

export interface SampleMeta {
  filename: string;
  teaser_en: string;
  teaser_he: string;
  label_en: string;
  label_he: string;
  featured: boolean;
  kind: string;
}

export type StreamEvent =
  | { type: "file_start"; filename: string; index: number; total: number }
  | { type: "stage"; filename: string; message: string }
  | { type: "result"; result: ProcessingResult }
  | { type: "done"; results: ProcessingResult[] }
  | { type: "error"; message: string };

export interface HealthInfo {
  status: string;
  featured_sample: string;
  featured_samples?: { en: string; he: string };
  max_files: number;
  max_mb: number;
}

export type ListRenderer = "line_items" | "parties" | "transactions" | "named_amounts" | "strings";

export interface TypeUiSpec {
  family: string;
  highlightFields: string[];
  primaryFields: string[];
  listFields: Record<string, ListRenderer>;
}

export const TYPE_UI_SPECS: Record<string, TypeUiSpec> = {
  invoice: {
    family: "money",
    highlightFields: ["total_amount", "currency"],
    primaryFields: [
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
    ],
    listFields: { line_items: "line_items" },
  },
  credit_note: {
    family: "money",
    highlightFields: ["total_amount", "currency"],
    primaryFields: [
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
    ],
    listFields: { line_items: "line_items" },
  },
  receipt: {
    family: "money",
    highlightFields: ["total_amount", "currency"],
    primaryFields: [
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
    ],
    listFields: { items: "line_items" },
  },
  quote: {
    family: "money",
    highlightFields: ["total_amount", "currency"],
    primaryFields: [
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
    ],
    listFields: { line_items: "line_items" },
  },
  purchase_order: {
    family: "logistics",
    highlightFields: ["total_amount", "currency"],
    primaryFields: [
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
    ],
    listFields: { line_items: "line_items" },
  },
  delivery_note: {
    family: "logistics",
    highlightFields: ["delivery_note_number"],
    primaryFields: [
      "shipper",
      "recipient",
      "delivery_note_number",
      "delivery_date",
      "delivery_date_iso",
      "order_reference",
      "ship_to",
    ],
    listFields: { items: "line_items" },
  },
  contract: {
    family: "agreement",
    highlightFields: ["title"],
    primaryFields: [
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
    ],
    listFields: { parties: "parties" },
  },
  bank_statement: {
    family: "money",
    highlightFields: ["closing_balance", "currency"],
    primaryFields: [
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
    ],
    listFields: { transactions: "transactions" },
  },
  payslip: {
    family: "hr",
    highlightFields: ["net_pay", "currency"],
    primaryFields: [
      "employer",
      "employee",
      "period",
      "pay_date",
      "pay_date_iso",
      "gross_pay",
      "net_pay",
      "net_pay_value",
      "currency",
    ],
    listFields: { deductions: "named_amounts" },
  },
  utility_bill: {
    family: "money",
    highlightFields: ["amount_due", "currency"],
    primaryFields: [
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
    ],
    listFields: {},
  },
  tax_document: {
    family: "tax",
    highlightFields: ["amount", "currency"],
    primaryFields: [
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
    ],
    listFields: {},
  },
  correspondence: {
    family: "other",
    highlightFields: ["subject"],
    primaryFields: [
      "sender",
      "recipient",
      "letter_date",
      "letter_date_iso",
      "subject",
      "reference_number",
      "summary",
    ],
    listFields: {},
  },
  other: {
    family: "other",
    highlightFields: ["title"],
    primaryFields: ["title", "summary", "language_hint"],
    listFields: {
      organizations: "strings",
      people: "strings",
      key_dates: "strings",
      reference_ids: "strings",
      amounts_mentioned: "strings",
    },
  },
};

export function typeFamily(docType: string | null | undefined): string {
  if (!docType) return "other";
  return TYPE_UI_SPECS[docType]?.family ?? (docType === "unknown" ? "unknown" : "other");
}

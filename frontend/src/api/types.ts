export type DocType = "invoice" | "contract" | "receipt" | "unknown";

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

export interface InvoiceExtraction {
  vendor?: string | null;
  buyer?: string | null;
  invoice_number?: string | null;
  invoice_date?: string | null;
  invoice_date_iso?: string | null;
  total_amount?: string | null;
  total_amount_value?: number | null;
  currency?: string | null;
  tax_id?: string | null;
  line_items?: LineItem[];
  confidence_notes?: string | null;
}

export interface ContractExtraction {
  title?: string | null;
  parties?: ContractParty[];
  effective_date?: string | null;
  effective_date_iso?: string | null;
  end_date?: string | null;
  end_date_iso?: string | null;
  governing_law?: string | null;
  key_terms_summary?: string | null;
  confidence_notes?: string | null;
}

export interface ReceiptExtraction {
  merchant?: string | null;
  receipt_number?: string | null;
  receipt_date?: string | null;
  receipt_date_iso?: string | null;
  total_amount?: string | null;
  total_amount_value?: number | null;
  currency?: string | null;
  payment_method?: string | null;
  items?: LineItem[];
  confidence_notes?: string | null;
}

export type StructuredExtraction =
  | InvoiceExtraction
  | ContractExtraction
  | ReceiptExtraction;

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
  max_files: number;
  max_mb: number;
}

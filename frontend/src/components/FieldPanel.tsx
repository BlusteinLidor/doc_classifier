import type { LineItem, ProcessingResult, StructuredExtraction } from "../api/types";
import type { Lang } from "../i18n/ui";
import { fieldLabel, t, typeLabel } from "../i18n/ui";

function isInvoice(s: StructuredExtraction): s is import("../api/types").InvoiceExtraction {
  return "invoice_number" in s || "vendor" in s || "line_items" in s;
}

function isContract(s: StructuredExtraction): s is import("../api/types").ContractExtraction {
  return "parties" in s || "governing_law" in s || "title" in s;
}

function isReceipt(s: StructuredExtraction): s is import("../api/types").ReceiptExtraction {
  return "merchant" in s || "receipt_number" in s || "payment_method" in s;
}

function FieldRows({
  lang,
  pairs,
}: {
  lang: Lang;
  pairs: [string, string | number | null | undefined][];
}) {
  const rows = pairs.filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== "");
  if (!rows.length) return null;
  return (
    <div className="field-card">
      {rows.map(([key, val], i) => (
        <div
          key={key}
          className="field-row"
          style={{ animationDelay: `${i * 0.04}s` }}
        >
          <div className="field-label">{fieldLabel(lang, key)}</div>
          <div className="field-value">{String(val)}</div>
        </div>
      ))}
    </div>
  );
}

function LineItemsTable({
  lang,
  items,
}: {
  lang: Lang;
  items: LineItem[];
}) {
  if (!items.length) return null;
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>{t(lang, "desc")}</th>
          <th>{t(lang, "qty")}</th>
          <th>{t(lang, "unit_price")}</th>
          <th>{t(lang, "line_total")}</th>
        </tr>
      </thead>
      <tbody>
        {items.map((li, i) => (
          <tr key={i}>
            <td>{li.description ?? ""}</td>
            <td>{li.quantity ?? ""}</td>
            <td>{li.unit_price ?? ""}</td>
            <td>{li.line_total ?? ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function FieldPanel({
  lang,
  result,
}: {
  lang: Lang;
  result: ProcessingResult;
}) {
  const s = result.structured;
  if (!s) {
    if (result.doc_type === "unknown") {
      return <div className="info-box">{t(lang, "unknown_ok")}</div>;
    }
    return <div className="info-box">{t(lang, "no_fields")}</div>;
  }

  if (result.doc_type === "invoice" || isInvoice(s)) {
    const inv = s as import("../api/types").InvoiceExtraction;
    const hero = [inv.total_amount, inv.currency].filter(Boolean).join(" ");
    return (
      <>
        {hero && <div className="hero-amount">{hero}</div>}
        <FieldRows
          lang={lang}
          pairs={[
            ["vendor", inv.vendor],
            ["invoice_number", inv.invoice_number],
            ["invoice_date", inv.invoice_date],
            ["invoice_date_iso", inv.invoice_date_iso],
            ["total_amount", inv.total_amount],
            ["total_amount_value", inv.total_amount_value],
            ["currency", inv.currency],
            ["tax_id", inv.tax_id],
            ["buyer", inv.buyer],
          ]}
        />
        {inv.line_items && inv.line_items.length > 0 && (
          <>
            <p className="panel-label">{t(lang, "line_items")}</p>
            <LineItemsTable lang={lang} items={inv.line_items} />
          </>
        )}
        {inv.confidence_notes && (
          <div className="info-box">
            {t(lang, "extraction_notes")}: {inv.confidence_notes}
          </div>
        )}
      </>
    );
  }

  if (result.doc_type === "contract" || isContract(s)) {
    const c = s as import("../api/types").ContractExtraction;
    return (
      <>
        {c.title && <div className="hero-title">{c.title}</div>}
        {c.parties && c.parties.length > 0 && (
          <>
            <p className="panel-label">{t(lang, "parties")}</p>
            <div className="party-chips">
              {c.parties.map((p, i) => (
                <span key={i} className="party-chip">
                  {p.name ?? "—"}
                  {p.role ? ` (${p.role})` : ""}
                </span>
              ))}
            </div>
          </>
        )}
        <FieldRows
          lang={lang}
          pairs={[
            ["effective_date", c.effective_date],
            ["effective_date_iso", c.effective_date_iso],
            ["end_date", c.end_date],
            ["end_date_iso", c.end_date_iso],
            ["governing_law", c.governing_law],
          ]}
        />
        {c.key_terms_summary && (
          <>
            <p className="panel-label">{t(lang, "key_terms")}</p>
            <div className="field-card">
              <div className="field-row">
                <div className="field-value" style={{ gridColumn: "1 / -1" }}>
                  {c.key_terms_summary}
                </div>
              </div>
            </div>
          </>
        )}
        {c.confidence_notes && (
          <div className="info-box">
            {t(lang, "extraction_notes")}: {c.confidence_notes}
          </div>
        )}
      </>
    );
  }

  if (result.doc_type === "receipt" || isReceipt(s)) {
    const r = s as import("../api/types").ReceiptExtraction;
    const hero = [r.total_amount, r.currency].filter(Boolean).join(" ");
    return (
      <>
        {hero && <div className="hero-amount">{hero}</div>}
        <FieldRows
          lang={lang}
          pairs={[
            ["merchant", r.merchant],
            ["receipt_number", r.receipt_number],
            ["receipt_date", r.receipt_date],
            ["receipt_date_iso", r.receipt_date_iso],
            ["total_amount", r.total_amount],
            ["total_amount_value", r.total_amount_value],
            ["currency", r.currency],
            ["payment_method", r.payment_method],
          ]}
        />
        {r.items && r.items.length > 0 && (
          <>
            <p className="panel-label">{t(lang, "items")}</p>
            <LineItemsTable lang={lang} items={r.items} />
          </>
        )}
        {r.confidence_notes && (
          <div className="info-box">
            {t(lang, "extraction_notes")}: {r.confidence_notes}
          </div>
        )}
      </>
    );
  }

  return <div className="info-box">{t(lang, "no_fields")}</div>;
}

export function summaryLine(lang: Lang, r: ProcessingResult): string {
  if (!r.success) return r.error_message || t(lang, "failed");
  if (r.doc_type === "unknown") return t(lang, "unknown_ok");
  const s = r.structured;
  if (!s) return "—";
  if (r.doc_type === "invoice" || isInvoice(s)) {
    const inv = s as import("../api/types").InvoiceExtraction;
    return [inv.vendor, inv.total_amount].filter(Boolean).join(" · ") || "—";
  }
  if (r.doc_type === "contract" || isContract(s)) {
    const c = s as import("../api/types").ContractExtraction;
    const n = c.parties?.length ?? 0;
    const title = c.title || "—";
    return n ? `${title} (${n} parties)` : title;
  }
  if (r.doc_type === "receipt" || isReceipt(s)) {
    const rec = s as import("../api/types").ReceiptExtraction;
    return [rec.merchant, rec.total_amount].filter(Boolean).join(" · ") || "—";
  }
  return typeLabel(lang, r.doc_type);
}

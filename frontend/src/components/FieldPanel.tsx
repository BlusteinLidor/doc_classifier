import type {
  ContractParty,
  LineItem,
  NamedAmount,
  ProcessingResult,
  StatementLine,
  StructuredExtraction,
  TypeUiSpec,
} from "../api/types";
import { TYPE_UI_SPECS } from "../api/types";
import type { Lang } from "../i18n/ui";
import { fieldLabel, looksHebrew, t, typeLabel } from "../i18n/ui";

const SKIP_KEYS = new Set(["confidence_notes"]);

/** Amount fields that are often paired with a separate `currency` highlight. */
const MONEY_HIGHLIGHT_KEYS = new Set([
  "total_amount",
  "amount_due",
  "amount",
  "closing_balance",
  "net_pay",
  "opening_balance",
  "gross_pay",
  "subtotal",
  "tax_amount",
]);

const SYMBOL_BY_CODE: Record<string, string> = {
  USD: "$",
  ILS: "₪",
  EUR: "€",
  GBP: "£",
};

const CURRENCY_TOKEN_RE =
  /₪|\$|€|£|\bUSD\b|\bUS\$\b|\bILS\b|\bNIS\b|\bEUR\b|\bGBP\b|ש["״']?\s*ח/gi;

/** Regexes for symbols/codes already embedded in an amount string. */
const CURRENCY_IN_AMOUNT: Record<string, RegExp> = {
  USD: /\$|USD|US\$/i,
  ILS: /₪|ILS|NIS|ש["״']?\s*ח/,
  EUR: /€|EUR/i,
  GBP: /£|GBP/i,
};

export function detectCurrencyCode(
  ...texts: Array<string | null | undefined>
): string | null {
  for (const raw of texts) {
    if (!raw?.trim()) continue;
    const text = raw.trim();
    if (/₪|\bILS\b|\bNIS\b|ש["״']?\s*ח/i.test(text)) return "ILS";
    if (/\$|\bUSD\b|\bUS\$/i.test(text)) return "USD";
    if (/€|\bEUR\b/i.test(text)) return "EUR";
    if (/£|\bGBP\b/i.test(text)) return "GBP";
    const code = text.toUpperCase().replace(/[^A-Z]/g, "");
    if (code in SYMBOL_BY_CODE) return code;
  }
  return null;
}

export function stripCurrencyMarkers(amount: string): string {
  return amount
    .replace(CURRENCY_TOKEN_RE, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^[\s·\-/]+|[\s·\-/]+$/g, "");
}

/** True when `amount` already shows the same currency as `currency` (symbol or code). */
export function amountIncludesCurrency(amount: string, currency: string): boolean {
  const amt = amount.trim();
  const cur = currency.trim();
  if (!amt || !cur) return false;
  if (amt.toUpperCase().includes(cur.toUpperCase())) return true;
  const code = detectCurrencyCode(cur) ?? cur.toUpperCase().replace(/[^A-Z]/g, "");
  const re = CURRENCY_IN_AMOUNT[code];
  if (re?.test(amt)) return true;
  if ((cur.includes("₪") || code === "ILS") && /₪/.test(amt)) return true;
  if ((cur.includes("$") || code === "USD") && /\$/.test(amt)) return true;
  try {
    return new RegExp(
      `(?:^|\\s)${cur.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?:\\s|$)`,
      "i",
    ).test(amt);
  } catch {
    return false;
  }
}

/**
 * Prefer a single symbol form: ₪4,797 or $2,104.83 — never "USD USD" or "₪4797 ILS".
 */
export function formatMoneyDisplay(
  amount: string | number | null | undefined,
  currency?: string | null,
): string {
  const amt =
    amount === null || amount === undefined ? "" : String(amount).trim();
  const cur = currency?.trim() ?? "";
  if (!amt && !cur) return "";
  const code = detectCurrencyCode(cur, amt);
  const num = amt ? stripCurrencyMarkers(amt) : "";
  if (!num) return (code && SYMBOL_BY_CODE[code]) || code || cur;
  if (code && SYMBOL_BY_CODE[code]) return `${SYMBOL_BY_CODE[code]}${num}`;
  if (code) return `${num} ${code}`;
  return num;
}

/** Alias kept for callers / tests */
export function composeAmountWithCurrency(
  amount: string | number | null | undefined,
  currency: string | null | undefined,
): string {
  return formatMoneyDisplay(amount, currency);
}

function asRecord(s: StructuredExtraction): Record<string, unknown> {
  return s as Record<string, unknown>;
}

function isEmpty(v: unknown): boolean {
  if (v === null || v === undefined) return true;
  if (typeof v === "string" && v.trim() === "") return true;
  if (Array.isArray(v) && v.length === 0) return true;
  return false;
}

function scalarString(v: unknown): string | number | null {
  if (v === null || v === undefined) return null;
  if (typeof v === "string" || typeof v === "number") return v;
  if (typeof v === "boolean") return String(v);
  return null;
}

function defaultSpec(s: Record<string, unknown>): TypeUiSpec {
  const primary = Object.keys(s).filter(
    (k) => !SKIP_KEYS.has(k) && !Array.isArray(s[k]),
  );
  const listFields: TypeUiSpec["listFields"] = {};
  for (const [k, v] of Object.entries(s)) {
    if (!Array.isArray(v) || !v.length) continue;
    if (typeof v[0] === "string") listFields[k] = "strings";
    else if (v[0] && typeof v[0] === "object" && "role" in (v[0] as object))
      listFields[k] = "parties";
    else if (v[0] && typeof v[0] === "object" && "balance" in (v[0] as object))
      listFields[k] = "transactions";
    else if (v[0] && typeof v[0] === "object" && "name" in (v[0] as object))
      listFields[k] = "named_amounts";
    else listFields[k] = "line_items";
  }
  return {
    family: "other",
    highlightFields: primary.slice(0, 2),
    primaryFields: primary,
    listFields,
  };
}

function TextDirValue({
  lang,
  value,
  className,
}: {
  lang: Lang;
  value: string;
  className?: string;
}) {
  const hebrew = looksHebrew(value);
  const dir = hebrew ? "rtl" : lang === "he" && !/[A-Za-z]/.test(value) ? "rtl" : "auto";
  return (
    <div className={className} dir={dir} lang={hebrew ? "he" : undefined}>
      {value}
    </div>
  );
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
    <div className={`field-card${lang === "he" ? " field-card-rtl" : ""}`}>
      {rows.map(([key, val], i) => (
        <div
          key={key}
          className="field-row"
          style={{ animationDelay: `${i * 0.04}s` }}
        >
          <div className="field-label" dir={lang === "he" ? "rtl" : "ltr"}>
            {fieldLabel(lang, key)}
          </div>
          <TextDirValue lang={lang} value={String(val)} className="field-value" />
        </div>
      ))}
    </div>
  );
}

function LineItemsTable({
  lang,
  items,
  currency,
}: {
  lang: Lang;
  items: LineItem[];
  currency?: string | null;
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
            <td dir={looksHebrew(li.description ?? "") ? "rtl" : "auto"}>
              {li.description ?? ""}
            </td>
            <td>{li.quantity ?? ""}</td>
            <td>
              {li.unit_price != null && String(li.unit_price).trim()
                ? formatMoneyDisplay(li.unit_price, currency)
                : ""}
            </td>
            <td>
              {li.line_total != null && String(li.line_total).trim()
                ? formatMoneyDisplay(li.line_total, currency)
                : ""}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TransactionsTable({
  lang,
  rows,
  currency,
}: {
  lang: Lang;
  rows: StatementLine[];
  currency?: string | null;
}) {
  if (!rows.length) return null;
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>{t(lang, "date")}</th>
          <th>{t(lang, "desc")}</th>
          <th>{t(lang, "amount")}</th>
          <th>{t(lang, "balance")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td>{row.date ?? ""}</td>
            <td>{row.description ?? ""}</td>
            <td>
              {row.amount != null && String(row.amount).trim()
                ? formatMoneyDisplay(row.amount, currency)
                : ""}
            </td>
            <td>
              {row.balance != null && String(row.balance).trim()
                ? formatMoneyDisplay(row.balance, currency)
                : ""}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function NamedAmountsTable({
  lang,
  rows,
  currency,
}: {
  lang: Lang;
  rows: NamedAmount[];
  currency?: string | null;
}) {
  if (!rows.length) return null;
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>{t(lang, "name")}</th>
          <th>{t(lang, "amount")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            <td>{row.name ?? ""}</td>
            <td>
              {row.amount != null && String(row.amount).trim()
                ? formatMoneyDisplay(row.amount, currency)
                : ""}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function StringChips({ values }: { values: string[] }) {
  if (!values.length) return null;
  return (
    <div className="party-chips">
      {values.map((v, i) => (
        <span key={i} className="party-chip">
          {v}
        </span>
      ))}
    </div>
  );
}

function heroText(spec: TypeUiSpec, data: Record<string, unknown>): string {
  const fields = spec.highlightFields;
  const currency = typeof data.currency === "string" ? data.currency : null;

  if (fields.some((k) => MONEY_HIGHLIGHT_KEYS.has(k))) {
    const amountKey = fields.find((k) => MONEY_HIGHLIGHT_KEYS.has(k));
    if (amountKey) {
      const amount = data[amountKey];
      const composed = formatMoneyDisplay(
        typeof amount === "string" || typeof amount === "number" ? amount : null,
        currency,
      );
      if (composed) return composed;
    }
  }

  const parts = fields
    .filter((k) => k !== "currency")
    .map((k) => data[k])
    .filter((v) => typeof v === "string" || typeof v === "number")
    .map(String)
    .filter((s) => s.trim() !== "");
  return parts.join(" ").trim();
}

function displayScalar(
  key: string,
  value: string | number,
  currency: string | null,
): string {
  if (MONEY_HIGHLIGHT_KEYS.has(key)) {
    return formatMoneyDisplay(value, currency);
  }
  if (key === "currency") {
    return detectCurrencyCode(String(value)) ?? String(value);
  }
  return String(value);
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

  const data = asRecord(s);
  const docType = result.doc_type || "other";
  const spec = TYPE_UI_SPECS[docType] ?? defaultSpec(data);
  const currency =
    typeof data.currency === "string"
      ? data.currency
      : detectCurrencyCode(
          ...Object.entries(data)
            .filter(([k]) => MONEY_HIGHLIGHT_KEYS.has(k))
            .map(([, v]) => (typeof v === "string" ? v : null)),
        );

  const listKeys = new Set(Object.keys(spec.listFields));
  const hasMoneyField = Object.keys(data).some(
    (k) => MONEY_HIGHLIGHT_KEYS.has(k) && !isEmpty(data[k]),
  );

  const orderedScalars: string[] = [];
  for (const k of spec.primaryFields) {
    if (listKeys.has(k) || SKIP_KEYS.has(k)) continue;
    // Currency is folded into amount display when an amount field exists
    if (k === "currency" && hasMoneyField) continue;
    if (!isEmpty(data[k]) && scalarString(data[k]) !== null) orderedScalars.push(k);
  }
  for (const k of Object.keys(data)) {
    if (orderedScalars.includes(k) || listKeys.has(k) || SKIP_KEYS.has(k)) continue;
    if (k === "currency" && hasMoneyField) continue;
    if (!isEmpty(data[k]) && scalarString(data[k]) !== null) orderedScalars.push(k);
  }

  const pairs: [string, string | number | null | undefined][] = orderedScalars.map(
    (k) => {
      const raw = scalarString(data[k]);
      if (raw === null) return [k, null];
      return [k, displayScalar(k, raw, currency)];
    },
  );

  const hero = heroText(spec, data);
  const isTitleHero =
    spec.highlightFields[0] === "title" || spec.highlightFields[0] === "subject";

  return (
    <div className={lang === "he" ? "fields-he" : undefined} dir={lang === "he" ? "rtl" : "ltr"}>
      {hero &&
        (isTitleHero ? (
          <div className="hero-title" dir={looksHebrew(hero) ? "rtl" : "auto"}>
            {hero}
          </div>
        ) : (
          <div className="hero-amount" dir="auto">
            {hero}
          </div>
        ))}
      <FieldRows lang={lang} pairs={pairs} />
      {Object.entries(spec.listFields).map(([key, kind]) => {
        const raw = data[key];
        if (!Array.isArray(raw) || !raw.length) return null;
        const labelKey =
          key === "line_items"
            ? "line_items"
            : key === "items"
              ? "items"
              : key === "parties"
                ? "parties"
                : key === "transactions"
                  ? "transactions"
                  : key === "deductions"
                    ? "deductions"
                    : key === "organizations"
                      ? "organizations"
                      : key === "people"
                        ? "people"
                        : key === "key_dates"
                          ? "key_dates"
                          : key === "reference_ids"
                            ? "reference_ids"
                            : key === "amounts_mentioned"
                              ? "amounts_mentioned"
                              : key;
        return (
          <div key={key}>
            <p className="panel-label">{t(lang, labelKey) || fieldLabel(lang, key)}</p>
            {kind === "line_items" && (
              <LineItemsTable
                lang={lang}
                items={raw as LineItem[]}
                currency={currency}
              />
            )}
            {kind === "parties" && (
              <div className="party-chips">
                {(raw as ContractParty[]).map((p, i) => {
                  const label = `${p.name ?? "—"}${p.role ? ` (${p.role})` : ""}`;
                  return (
                    <span
                      key={i}
                      className="party-chip"
                      dir={looksHebrew(label) ? "rtl" : "auto"}
                    >
                      {label}
                    </span>
                  );
                })}
              </div>
            )}
            {kind === "transactions" && (
              <TransactionsTable
                lang={lang}
                rows={raw as StatementLine[]}
                currency={currency}
              />
            )}
            {kind === "named_amounts" && (
              <NamedAmountsTable
                lang={lang}
                rows={raw as NamedAmount[]}
                currency={currency}
              />
            )}
            {kind === "strings" && <StringChips values={raw as string[]} />}
          </div>
        );
      })}
      {typeof data.confidence_notes === "string" && data.confidence_notes && (
        <div className="info-box" dir={looksHebrew(data.confidence_notes) ? "rtl" : "auto"}>
          {t(lang, "extraction_notes")}: {data.confidence_notes}
        </div>
      )}
    </div>
  );
}

export function summaryLine(lang: Lang, r: ProcessingResult): string {
  if (!r.success) return r.error_message || t(lang, "failed");
  if (r.doc_type === "unknown" && !r.structured) return t(lang, "unknown_ok");
  const s = r.structured;
  if (!s) return "—";
  const data = asRecord(s);
  const docType = r.doc_type || "other";
  const spec = TYPE_UI_SPECS[docType];
  const currency = typeof data.currency === "string" ? data.currency : null;

  const pick = (...keys: string[]) =>
    keys
      .map((k) => data[k])
      .filter((v) => typeof v === "string" || typeof v === "number")
      .map(String)
      .filter(Boolean);

  if (spec) {
    const moneyKey = spec.highlightFields.find((k) => MONEY_HIGHLIGHT_KEYS.has(k));
    if (moneyKey) {
      const money = formatMoneyDisplay(
        typeof data[moneyKey] === "string" || typeof data[moneyKey] === "number"
          ? (data[moneyKey] as string | number)
          : null,
        currency,
      );
      const rest = pick(
        ...spec.highlightFields.filter(
          (k) => k !== moneyKey && k !== "currency",
        ),
        ...spec.primaryFields
          .filter(
            (k) =>
              k !== moneyKey &&
              k !== "currency" &&
              k !== "total_amount_value" &&
              !MONEY_HIGHLIGHT_KEYS.has(k),
          )
          .slice(0, 2),
      );
      const unique = [...new Set([money, ...rest].filter(Boolean))].slice(0, 3);
      if (unique.length) return unique.join(" · ");
    }
    const parts = pick(
      ...spec.highlightFields.filter((k) => k !== "currency"),
      ...spec.primaryFields.filter((k) => k !== "currency").slice(0, 3),
    );
    const unique = [...new Set(parts)].slice(0, 3);
    if (unique.length) return unique.join(" · ");
  }

  if (typeof data.summary === "string" && data.summary) return data.summary;
  if (typeof data.title === "string" && data.title) return data.title;
  return typeLabel(lang, r.doc_type);
}

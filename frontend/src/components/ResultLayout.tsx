import { downloadExport, downloadJsonLocal, samplePdfUrl } from "../api/client";
import type { ProcessingResult } from "../api/types";
import { typeFamily } from "../api/types";
import type { Lang } from "../i18n/ui";
import { displayFilename, looksHebrew, t, typeLabel } from "../i18n/ui";
import { FieldPanel, summaryLine } from "./FieldPanel";

interface Props {
  lang: Lang;
  results: ProcessingResult[];
  pdfUrls: Record<string, string>;
  onClear: () => void;
}

function PdfPreview({
  url,
  filename,
  noPdfLabel,
}: {
  url?: string;
  filename: string;
  noPdfLabel: string;
}) {
  if (!url) {
    return <p className="meta-caption">{noPdfLabel}</p>;
  }
  return <iframe className="pdf-frame" title={filename} src={url} />;
}

export function ResultLayout({ lang, results, pdfUrls, onClear }: Props) {
  const ok = results.filter((r) => r.success).length;
  const total = results.length;
  const latencies = results
    .map((r) => r.latency_ms)
    .filter((v): v is number => v != null);
  const latSec =
    latencies.length > 0
      ? (latencies.reduce((a, b) => a + b, 0) / 1000).toFixed(1)
      : null;

  return (
    <section className="section" id="results">
      <div className="results-header">
        <div className="results-summary">
          <strong>{t(lang, "ready")}</strong>
          <span>
            {t(lang, "summary_ok", { ok, total })}
            {latSec != null ? ` · ${t(lang, "latency", { sec: latSec })}` : ""}
          </span>
        </div>
        <div className="results-actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => void downloadExport(results, "json")}
          >
            {t(lang, "download_json")}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => void downloadExport(results, "csv")}
          >
            {t(lang, "download_csv")}
          </button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClear}>
            {t(lang, "clear")}
          </button>
          <button type="button" className="btn btn-primary btn-sm" onClick={onClear}>
            {t(lang, "analyze_another")}
          </button>
        </div>
      </div>

      <h2 className="section-title">{t(lang, "results")}</h2>

      {results.length > 1 && (
        <>
          <p className="panel-label">{t(lang, "batch_table")}</p>
          <table className="batch-table">
            <thead>
              <tr>
                <th>{t(lang, "col_file")}</th>
                <th>{t(lang, "col_type")}</th>
                <th>{t(lang, "col_summary")}</th>
                <th>{t(lang, "col_status")}</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.filename}>
                  <td dir="auto">{displayFilename(lang, r.filename)}</td>
                  <td>{typeLabel(lang, r.doc_type)}</td>
                  <td dir={looksHebrew(summaryLine(lang, r)) ? "rtl" : "auto"}>
                    {summaryLine(lang, r)}
                  </td>
                  <td>{r.success ? t(lang, "ok") : t(lang, "failed")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {results.map((r) => {
        const url = pdfUrls[r.filename] ?? samplePdfUrl(r.filename);
        const meta: string[] = [];
        if (r.latency_ms != null) {
          meta.push(
            t(lang, "latency", { sec: (r.latency_ms / 1000).toFixed(1) }),
          );
        }
        if (r.used_ocr) meta.push(t(lang, "used_ocr"));
        const dt = r.doc_type || "unknown";
        const family = typeFamily(dt);

        return (
          <article key={r.filename} className="result-card">
            <h3
              style={{ margin: "0 0 0.25rem", fontSize: "1.05rem" }}
              dir="auto"
            >
              {displayFilename(lang, r.filename)}
            </h3>
            {meta.length > 0 && (
              <p className="meta-caption">{meta.join(" · ")}</p>
            )}

            {!r.success ? (
              <>
                <div className="error-box">
                  {r.error_message || t(lang, "failed")}
                </div>
                {r.warnings && r.warnings.length > 0 && (
                  <p className="meta-caption">
                    {t(lang, "warnings")}: {r.warnings.join(" · ")}
                  </p>
                )}
                <div className="split">
                  <div>
                    <p className="panel-label">{t(lang, "original_pdf")}</p>
                    <PdfPreview
                      url={url}
                      filename={r.filename}
                      noPdfLabel={t(lang, "no_pdf")}
                    />
                  </div>
                  <div>
                    <p className="panel-label">{t(lang, "text_preview")}</p>
                    <pre
                      className="pre-json pre-text"
                      style={{ background: "var(--ink-soft)" }}
                      dir={looksHebrew(r.raw_text_preview || "") ? "rtl" : "ltr"}
                    >
                      {r.raw_text_preview || "—"}
                    </pre>
                  </div>
                </div>
              </>
            ) : (
              <>
                <p className="panel-label">{t(lang, "classification")}</p>
                <div className={`doc-badge ${dt} family-${family}`}>
                  {typeLabel(lang, dt)}
                </div>
                {r.classification_confidence_note && (
                  <div
                    className="info-box"
                    dir={
                      looksHebrew(r.classification_confidence_note) ? "rtl" : "auto"
                    }
                  >
                    <span dir={lang === "he" ? "rtl" : "ltr"}>
                      {t(lang, "confidence")}:{" "}
                    </span>
                    {r.classification_confidence_note}
                  </div>
                )}
                <div style={{ marginBottom: "0.75rem" }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => downloadJsonLocal(r)}
                  >
                    {t(lang, "per_doc_json")}
                  </button>
                </div>
                {r.warnings && r.warnings.length > 0 && (
                  <p className="meta-caption">
                    {t(lang, "warnings")}: {r.warnings.join(" · ")}
                  </p>
                )}
                <div className="split">
                  <div>
                    <p className="panel-label">{t(lang, "original_pdf")}</p>
                    <PdfPreview
                      url={url}
                      filename={r.filename}
                      noPdfLabel={t(lang, "no_pdf")}
                    />
                  </div>
                  <div>
                    <p className="panel-label">{t(lang, "extracted_data")}</p>
                    <FieldPanel lang={lang} result={r} />
                    {r.structured && (
                      <details className="details">
                        <summary>{t(lang, "json_raw")}</summary>
                        <pre className="pre-json">
                          {JSON.stringify(r.structured, null, 2)}
                        </pre>
                      </details>
                    )}
                    {r.raw_text_preview && (
                      <details className="details">
                        <summary>{t(lang, "text_preview")}</summary>
                        <pre
                          className="pre-json pre-text"
                          style={{ background: "var(--ink-soft)" }}
                          dir={looksHebrew(r.raw_text_preview) ? "rtl" : "ltr"}
                        >
                          {r.raw_text_preview}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </>
            )}
          </article>
        );
      })}
    </section>
  );
}

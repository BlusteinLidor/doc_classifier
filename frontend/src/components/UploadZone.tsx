import { useCallback, useRef, useState } from "react";
import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

interface Props {
  lang: Lang;
  busy: boolean;
  maxFiles: number;
  maxMb: number;
  onAnalyze: (files: File[]) => void;
}

export function UploadZone({ lang, busy, maxFiles, maxMb, onAnalyze }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [drag, setDrag] = useState(false);

  const takeFiles = useCallback(
    (list: FileList | File[] | null) => {
      if (!list) return;
      const pdfs = Array.from(list)
        .filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"))
        .slice(0, maxFiles);
      setFiles(pdfs);
    },
    [maxFiles],
  );

  return (
    <section className="section" id="upload">
      <h2 className="section-title">{t(lang, "upload_title")}</h2>
      <p className="section-desc">
        {t(lang, "upload_help", { max_files: maxFiles, max_mb: maxMb })}
      </p>
      <div
        className={`upload-zone${drag ? " drag" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          takeFiles(e.dataTransfer.files);
        }}
      >
        <p>{t(lang, "upload_drop")}</p>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          {t(lang, "upload_cta")}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          onChange={(e) => takeFiles(e.target.files)}
        />
        {files.length > 0 && (
          <p className="upload-files">
            {files.map((f) => f.name).join(" · ")}
          </p>
        )}
      </div>
      <div style={{ marginTop: "0.85rem" }}>
        <button
          type="button"
          className="btn btn-primary"
          disabled={busy || files.length === 0}
          onClick={() => onAnalyze(files)}
        >
          {t(lang, "analyze")}
        </button>
      </div>
    </section>
  );
}

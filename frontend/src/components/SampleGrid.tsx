import type { SampleMeta } from "../api/types";
import { typeFamily } from "../api/types";
import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

interface Props {
  lang: Lang;
  samples: SampleMeta[];
  busy: boolean;
  onSelect: (filename: string) => void;
}

export function SampleGrid({ lang, samples, busy, onSelect }: Props) {
  return (
    <section className="section" id="samples">
      <h2 className="section-title">{t(lang, "samples_title")}</h2>
      <p className="section-desc">{t(lang, "samples_desc")}</p>
      <div className="sample-grid">
        {samples.map((s) => {
          const label = lang === "he" ? s.label_he : s.label_en;
          const teaser = lang === "he" ? s.teaser_he : s.teaser_en;
          const family = typeFamily(s.kind);
          return (
            <button
              key={s.filename}
              type="button"
              className={`sample-card${s.featured ? " featured" : ""}`}
              disabled={busy}
              onClick={() => onSelect(s.filename)}
            >
              <span className={`sample-kind ${s.kind} family-${family}`}>{s.kind}</span>
              <p className="sample-label">{label}</p>
              <p className="sample-teaser">{teaser}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

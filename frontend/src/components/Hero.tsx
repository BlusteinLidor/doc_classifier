import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

interface Props {
  lang: Lang;
  busy: boolean;
  onRunFeatured: () => void;
  onBrowseSamples: () => void;
}

export function Hero({ lang, busy, onRunFeatured, onBrowseSamples }: Props) {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-stack" aria-hidden="true">
        <div className="paper-sheet s1">
          <div className="paper-accent" />
          <div className="paper-lines" />
        </div>
        <div className="paper-sheet s2">
          <div className="paper-lines" />
        </div>
        <div className="paper-sheet s3">
          <div className="paper-lines" />
        </div>
      </div>
      <div className="hero-copy">
        <p className="hero-sub">{t(lang, "brand_sub")}</p>
        <h1 id="hero-title">{t(lang, "brand")}</h1>
        <p className="hero-value">{t(lang, "value")}</p>
        <div className="hero-cta">
          <button
            type="button"
            className="btn btn-primary"
            onClick={onRunFeatured}
            disabled={busy}
          >
            {t(lang, "auto_run")}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBrowseSamples}
            disabled={busy}
          >
            {t(lang, "skip_auto")}
          </button>
        </div>
        <p className="hero-hint">{t(lang, "hero_hint")}</p>
      </div>
    </section>
  );
}

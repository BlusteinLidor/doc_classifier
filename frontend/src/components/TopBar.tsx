import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";
import { LangToggle } from "./LangToggle";

interface Props {
  lang: Lang;
  scrolled: boolean;
  busy: boolean;
  onLangChange: (lang: Lang) => void;
  onRunDemo: () => void;
  showRun: boolean;
}

export function TopBar({
  lang,
  scrolled,
  busy,
  onLangChange,
  onRunDemo,
  showRun,
}: Props) {
  return (
    <header className={`topbar${scrolled ? " scrolled" : ""}`}>
      <div className="topbar-brand">{t(lang, "brand")}</div>
      <div className="topbar-actions">
        <LangToggle lang={lang} onChange={onLangChange} />
        {showRun && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onRunDemo}
            disabled={busy}
          >
            {t(lang, "topbar_run")}
          </button>
        )}
      </div>
    </header>
  );
}

import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";
import {
  DemoSettings,
  type IncomingIntervalMs,
} from "./DemoSettings";
import { LangToggle } from "./LangToggle";

interface Props {
  lang: Lang;
  scrolled: boolean;
  busy: boolean;
  onLangChange: (lang: Lang) => void;
  onRunDemo: () => void;
  showRun: boolean;
  settingsOpen: boolean;
  intervalMs: IncomingIntervalMs;
  onSettingsOpenChange: (open: boolean) => void;
  onIntervalChange: (ms: IncomingIntervalMs) => void;
}

export function TopBar({
  lang,
  scrolled,
  busy,
  onLangChange,
  onRunDemo,
  showRun,
  settingsOpen,
  intervalMs,
  onSettingsOpenChange,
  onIntervalChange,
}: Props) {
  return (
    <header className={`topbar${scrolled ? " scrolled" : ""}`}>
      <div className="topbar-start">
        <DemoSettings
          lang={lang}
          open={settingsOpen}
          intervalMs={intervalMs}
          onOpenChange={onSettingsOpenChange}
          onIntervalChange={onIntervalChange}
        />
        <div className="topbar-brand">{t(lang, "brand")}</div>
      </div>
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

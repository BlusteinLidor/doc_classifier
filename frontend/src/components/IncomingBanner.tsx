import type { Lang } from "../i18n/ui";
import { displayFilename, t } from "../i18n/ui";

export type IncomingSource = "desktop" | "drive" | "whatsapp";

interface Props {
  lang: Lang;
  filename: string;
  source: IncomingSource;
  visible: boolean;
}

function sourceLabel(lang: Lang, source: IncomingSource): string {
  if (source === "desktop") return t(lang, "incoming_source_desktop");
  if (source === "drive") return t(lang, "incoming_source_drive");
  return t(lang, "incoming_source_whatsapp");
}

export function IncomingBanner({ lang, filename, source, visible }: Props) {
  if (!visible) return null;

  return (
    <div className="incoming-banner" role="status" aria-live="polite">
      <div className="incoming-banner-pulse" aria-hidden="true" />
      <div className="incoming-banner-body">
        <span className="incoming-banner-kicker">{t(lang, "incoming_title")}</span>
        <strong className="incoming-banner-file">
          {displayFilename(lang, filename)}
        </strong>
        <span className="incoming-banner-source">
          {t(lang, "incoming_via", { source: sourceLabel(lang, source) })}
        </span>
      </div>
    </div>
  );
}

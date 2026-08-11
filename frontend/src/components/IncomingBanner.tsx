import type { Lang } from "../i18n/ui";
import { displayFilename, t } from "../i18n/ui";

export type IncomingSource = "desktop" | "drive" | "whatsapp";

interface Props {
  lang: Lang;
  filename: string;
  source: IncomingSource;
  visible: boolean;
  onOpen: () => void;
}

function sourceLabel(lang: Lang, source: IncomingSource): string {
  if (source === "desktop") return t(lang, "incoming_source_desktop");
  if (source === "drive") return t(lang, "incoming_source_drive");
  return t(lang, "incoming_source_whatsapp");
}

export function IncomingBanner({
  lang,
  filename,
  source,
  visible,
  onOpen,
}: Props) {
  if (!visible) return null;

  return (
    <button
      type="button"
      className="incoming-toast"
      onClick={onOpen}
      aria-label={t(lang, "incoming_click_hint")}
    >
      <span className="incoming-toast-pulse" aria-hidden="true" />
      <span className="incoming-toast-body">
        <span className="incoming-toast-kicker">{t(lang, "incoming_title")}</span>
        <strong className="incoming-toast-file">
          {displayFilename(lang, filename)}
        </strong>
        <span className="incoming-toast-source">
          {t(lang, "incoming_via", { source: sourceLabel(lang, source) })}
        </span>
        <span className="incoming-toast-hint">{t(lang, "incoming_click_hint")}</span>
      </span>
    </button>
  );
}

import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

interface Props {
  lang: Lang;
  onChange: (lang: Lang) => void;
}

export function LangToggle({ lang, onChange }: Props) {
  return (
    <div className="lang-toggle" role="group" aria-label={t(lang, "page_title")}>
      <button
        type="button"
        className={lang === "en" ? "active" : ""}
        onClick={() => onChange("en")}
      >
        EN
      </button>
      <button
        type="button"
        className={lang === "he" ? "active" : ""}
        onClick={() => onChange("he")}
      >
        עב
      </button>
    </div>
  );
}

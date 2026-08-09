import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

interface Props {
  lang: Lang;
  maxFiles: number;
  maxMb: number;
}

export function Footer({ lang, maxFiles, maxMb }: Props) {
  return (
    <footer className="footer">
      <p>
        {t(lang, "footer_limits", { max_files: maxFiles, max_mb: maxMb })}
        <br />
        {t(lang, "footer_tech")}
      </p>
    </footer>
  );
}

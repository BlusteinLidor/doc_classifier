import { useEffect, useRef } from "react";
import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

/** Interval between incoming demo documents (ms). 0 = never. */
export type IncomingIntervalMs = 0 | 20000 | 45000 | 60000 | 120000;

export const INCOMING_INTERVAL_OPTIONS: {
  value: IncomingIntervalMs;
  labelKey: string;
}[] = [
  { value: 0, labelKey: "settings_interval_never" },
  { value: 20000, labelKey: "settings_interval_20s" },
  { value: 45000, labelKey: "settings_interval_45s" },
  { value: 60000, labelKey: "settings_interval_1m" },
  { value: 120000, labelKey: "settings_interval_2m" },
];

interface Props {
  lang: Lang;
  open: boolean;
  intervalMs: IncomingIntervalMs;
  onOpenChange: (open: boolean) => void;
  onIntervalChange: (ms: IncomingIntervalMs) => void;
}

export function DemoSettings({
  lang,
  open,
  intervalMs,
  onOpenChange,
  onIntervalChange,
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    const onPointer = (e: MouseEvent) => {
      const target = e.target as Node;
      if (panelRef.current?.contains(target)) return;
      if (buttonRef.current?.contains(target)) return;
      onOpenChange(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
    };
  }, [open, onOpenChange]);

  return (
    <div className="demo-settings">
      <button
        ref={buttonRef}
        type="button"
        className={`settings-icon-btn${open ? " active" : ""}${intervalMs > 0 ? " armed" : ""}`}
        onClick={() => onOpenChange(!open)}
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={t(lang, "settings_aria")}
        title={t(lang, "settings_aria")}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      </button>

      {open && (
        <div
          ref={panelRef}
          className="settings-panel"
          role="dialog"
          aria-label={t(lang, "settings_title")}
        >
          <div className="settings-panel-header">
            <h2 className="settings-panel-title">{t(lang, "settings_title")}</h2>
          </div>
          <label className="settings-label" htmlFor="incoming-interval">
            {t(lang, "settings_interval_label")}
          </label>
          <p className="settings-hint">{t(lang, "settings_interval_hint")}</p>
          <select
            id="incoming-interval"
            className="settings-select"
            value={intervalMs}
            onChange={(e) =>
              onIntervalChange(Number(e.target.value) as IncomingIntervalMs)
            }
          >
            {INCOMING_INTERVAL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {t(lang, opt.labelKey)}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="btn btn-primary btn-sm settings-done"
            onClick={() => onOpenChange(false)}
          >
            {t(lang, "settings_done")}
          </button>
        </div>
      )}
    </div>
  );
}

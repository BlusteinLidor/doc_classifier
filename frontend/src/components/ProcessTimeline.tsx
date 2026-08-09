import type { Lang } from "../i18n/ui";
import { t } from "../i18n/ui";

export type TimelinePhase = "idle" | "extract" | "classify" | "structure" | "done";

interface Props {
  lang: Lang;
  phase: TimelinePhase;
  message: string;
  filename?: string;
}

function mapMessageToPhase(message: string): TimelinePhase | null {
  const m = message.toLowerCase();
  if (m.includes("done")) return "done";
  if (
    m.includes("classif") ||
    m.includes("type unknown") ||
    m.includes("document type")
  ) {
    return "classify";
  }
  if (m.includes("extract") || m.includes("field") || m.includes("structured")) {
    return "structure";
  }
  if (
    m.includes("read") ||
    m.includes("pdf") ||
    m.includes("ocr") ||
    m.includes("vision") ||
    m.includes("text")
  ) {
    return "extract";
  }
  return null;
}

export function phaseFromStageMessage(
  message: string,
  current: TimelinePhase,
): TimelinePhase {
  const mapped = mapMessageToPhase(message);
  if (!mapped) return current;
  const order: TimelinePhase[] = ["idle", "extract", "classify", "structure", "done"];
  if (order.indexOf(mapped) >= order.indexOf(current)) return mapped;
  return current;
}

export function ProcessTimeline({ lang, phase, message, filename }: Props) {
  const steps: { id: TimelinePhase; labelKey: string }[] = [
    { id: "extract", labelKey: "stage_extract" },
    { id: "classify", labelKey: "stage_classify" },
    { id: "structure", labelKey: "stage_structure" },
  ];

  const order: TimelinePhase[] = ["idle", "extract", "classify", "structure", "done"];
  const idx = order.indexOf(phase);

  return (
    <div className="timeline" id="processing">
      <p className="timeline-title">
        {t(lang, "processing")}
        {filename ? ` — ${filename}` : ""}
      </p>
      <p className="timeline-eta">{t(lang, "eta")}</p>
      <div className="timeline-steps">
        {steps.map((step, i) => {
          const stepIdx = order.indexOf(step.id);
          let cls = "timeline-step";
          if (phase === "done" || idx > stepIdx) cls += " done";
          else if (idx === stepIdx) cls += " active";
          return (
            <div key={step.id} className={cls}>
              {i + 1}. {t(lang, step.labelKey)}
            </div>
          );
        })}
      </div>
      <p className="timeline-msg">{message}</p>
    </div>
  );
}

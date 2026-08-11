import type { HealthInfo, ProcessingResult, SampleMeta, StreamEvent } from "./types";

async function parseSseStream(
  response: Response,
  onEvent: (ev: StreamEvent) => void,
): Promise<ProcessingResult[]> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  if (!response.body) {
    throw new Error("No response body from server.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResults: ProcessingResult[] = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part
        .split("\n")
        .map((l) => l.trim())
        .find((l) => l.startsWith("data:"));
      if (!line) continue;
      const json = line.slice(5).trim();
      if (!json) continue;
      try {
        const ev = JSON.parse(json) as StreamEvent;
        onEvent(ev);
        if (ev.type === "done") {
          finalResults = ev.results;
        }
        if (ev.type === "error") {
          throw new Error(ev.message);
        }
      } catch (err) {
        if (err instanceof SyntaxError) continue;
        throw err;
      }
    }
  }
  return finalResults;
}

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("Health check failed");
  return res.json() as Promise<HealthInfo>;
}

export async function fetchSamples(lang?: "en" | "he"): Promise<SampleMeta[]> {
  const qs = lang ? `?lang=${lang}` : "";
  const res = await fetch(`/api/samples${qs}`);
  if (!res.ok) throw new Error("Failed to load samples");
  return res.json() as Promise<SampleMeta[]>;
}

export function samplePdfUrl(filename: string): string {
  return `/api/samples/${encodeURIComponent(filename)}`;
}

export async function processSample(
  filename: string,
  onEvent: (ev: StreamEvent) => void,
): Promise<ProcessingResult[]> {
  const res = await fetch("/api/process/sample", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  return parseSseStream(res, onEvent);
}

export async function processUploads(
  files: File[],
  onEvent: (ev: StreamEvent) => void,
): Promise<ProcessingResult[]> {
  const form = new FormData();
  for (const f of files) {
    form.append("files", f, f.name);
  }
  const res = await fetch("/api/process", {
    method: "POST",
    body: form,
  });
  return parseSseStream(res, onEvent);
}

export async function downloadExport(
  results: ProcessingResult[],
  kind: "json" | "csv",
): Promise<void> {
  const res = await fetch(`/api/export/${kind}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ results }),
  });
  if (!res.ok) throw new Error(`Export ${kind} failed`);
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") || "";
  const match = /filename="?([^"]+)"?/.exec(cd);
  const name =
    match?.[1] ??
    `extraction.${kind === "json" ? "json" : "csv"}`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadJsonLocal(
  result: ProcessingResult,
  filename?: string,
): void {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename ?? `${result.filename.replace(/\.pdf$/i, "")}_extraction.json`;
  a.click();
  URL.revokeObjectURL(url);
}

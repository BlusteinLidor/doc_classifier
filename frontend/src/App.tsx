import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchHealth,
  processSample,
  processUploads,
  samplePdfUrl,
} from "./api/client";
import type { ProcessingResult, StreamEvent } from "./api/types";
import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import {
  phaseFromStageMessage,
  ProcessTimeline,
  type TimelinePhase,
} from "./components/ProcessTimeline";
import { ResultLayout } from "./components/ResultLayout";
import { TopBar } from "./components/TopBar";
import { UploadZone } from "./components/UploadZone";
import type { Lang } from "./i18n/ui";
import { t } from "./i18n/ui";

const FEATURED_DEFAULT = "sample_invoice_he.pdf";

export default function App() {
  const [lang, setLang] = useState<Lang>("he");
  const [scrolled, setScrolled] = useState(false);
  const [featured, setFeatured] = useState(FEATURED_DEFAULT);
  const [maxFiles, setMaxFiles] = useState(3);
  const [maxMb, setMaxMb] = useState(5);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<TimelinePhase>("idle");
  const [stageMsg, setStageMsg] = useState("");
  const [stageFile, setStageFile] = useState<string | undefined>();
  const [results, setResults] = useState<ProcessingResult[]>([]);
  const [pdfUrls, setPdfUrls] = useState<Record<string, string>>({});
  const blobUrlsRef = useRef<string[]>([]);
  const autoStarted = useRef(false);

  useEffect(() => {
    document.documentElement.lang = lang === "he" ? "he" : "en";
    document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
    document.title = t(lang, "page_title");
  }, [lang]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const health = await fetchHealth();
        setFeatured(health.featured_sample || FEATURED_DEFAULT);
        setMaxFiles(health.max_files);
        setMaxMb(health.max_mb);
      } catch {
        // Allow UI without API during static preview
      }
    })();
  }, []);

  useEffect(() => {
    return () => {
      for (const u of blobUrlsRef.current) URL.revokeObjectURL(u);
    };
  }, []);

  const clearBlobUrls = useCallback(() => {
    for (const u of blobUrlsRef.current) URL.revokeObjectURL(u);
    blobUrlsRef.current = [];
    setPdfUrls({});
  }, []);

  const handleStreamEvent = useCallback((ev: StreamEvent) => {
    if (ev.type === "file_start") {
      setStageFile(ev.filename);
      setPhase("extract");
      setStageMsg("");
    } else if (ev.type === "stage") {
      setStageFile(ev.filename);
      setStageMsg("");
      setPhase((prev) => phaseFromStageMessage(ev.message, prev));
    } else if (ev.type === "result") {
      setPhase("done");
    }
  }, []);

  const runProcess = useCallback(
    async (
      runner: (onEvent: (ev: StreamEvent) => void) => Promise<ProcessingResult[]>,
      urlMap?: Record<string, string>,
    ) => {
      setBusy(true);
      setResults([]);
      setPhase("extract");
      setStageMsg("");
      try {
        if (urlMap) {
          setPdfUrls((prev) => ({ ...prev, ...urlMap }));
        }
        const out = await runner(handleStreamEvent);
        setResults(out);
        setPhase("done");
        requestAnimationFrame(() => {
          document.getElementById("results")?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setResults([
          {
            filename: stageFile || "error",
            success: false,
            error_message: message,
          },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [handleStreamEvent, stageFile],
  );

  const runFeatured = useCallback(() => {
    const name = featured;
    void runProcess((onEvent) => processSample(name, onEvent), {
      [name]: samplePdfUrl(name),
    });
  }, [featured, runProcess]);

  const runUploads = useCallback(
    (files: File[]) => {
      const map: Record<string, string> = {};
      for (const f of files) {
        const url = URL.createObjectURL(f);
        blobUrlsRef.current.push(url);
        map[f.name] = url;
      }
      void runProcess((onEvent) => processUploads(files, onEvent), map);
    },
    [runProcess],
  );

  const clearResults = useCallback(() => {
    setResults([]);
    clearBlobUrls();
    setPhase("idle");
    setStageMsg("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [clearBlobUrls]);

  // ?demo=1 auto-starts featured document after 1s (for video capture)
  useEffect(() => {
    if (autoStarted.current) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "1") {
      autoStarted.current = true;
      const timer = window.setTimeout(() => {
        runFeatured();
      }, 1000);
      return () => window.clearTimeout(timer);
    }
  }, [runFeatured]);

  const browseUpload = () => {
    document.getElementById("upload")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="app">
      <div className="app-bg" aria-hidden="true" />
      <div className="app-inner">
        <TopBar
          lang={lang}
          scrolled={scrolled}
          busy={busy}
          onLangChange={setLang}
          onRunDemo={runFeatured}
          showRun={!busy && results.length === 0}
        />

        {results.length === 0 && !busy && (
          <Hero
            lang={lang}
            busy={busy}
            onRunFeatured={runFeatured}
            onBrowseUpload={browseUpload}
          />
        )}

        {busy && (
          <ProcessTimeline
            lang={lang}
            phase={phase}
            message={stageMsg}
            filename={stageFile}
          />
        )}

        {results.length > 0 && !busy && (
          <ResultLayout
            lang={lang}
            results={results}
            pdfUrls={pdfUrls}
            onClear={clearResults}
          />
        )}

        {!busy && (
          <>
            <UploadZone
              lang={lang}
              busy={busy}
              maxFiles={maxFiles}
              maxMb={maxMb}
              onAnalyze={runUploads}
            />
            {results.length === 0 && (
              <p className="empty-hint">{t(lang, "empty")}</p>
            )}
          </>
        )}

        <Footer lang={lang} maxFiles={maxFiles} maxMb={maxMb} />
      </div>
    </div>
  );
}

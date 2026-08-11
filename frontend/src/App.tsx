import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchHealth,
  processSample,
  processUploads,
  samplePdfUrl,
} from "./api/client";
import type { ProcessingResult, StreamEvent } from "./api/types";
import { type IncomingIntervalMs } from "./components/DemoSettings";
import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import {
  IncomingBanner,
  type IncomingSource,
} from "./components/IncomingBanner";
import {
  phaseFromStageMessage,
  ProcessTimeline,
  type TimelinePhase,
} from "./components/ProcessTimeline";
import { ResultLayout } from "./components/ResultLayout";
import { TopBar } from "./components/TopBar";
import { UploadZone } from "./components/UploadZone";
import type { Lang } from "./i18n/ui";
import { demoSamplesForLang, featuredSampleForLang, t } from "./i18n/ui";

const INCOMING_BANNER_MS = 2800;
const TOAST_DISMISS_AFTER_DONE_MS = 4500;
const FIRST_INCOMING_DELAY_MS = 2500;
const SOURCES: IncomingSource[] = ["desktop", "drive", "whatsapp"];

export default function App() {
  const [lang, setLang] = useState<Lang>("he");
  const [scrolled, setScrolled] = useState(false);
  const [maxFiles, setMaxFiles] = useState(3);
  const [maxMb, setMaxMb] = useState(5);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<TimelinePhase>("idle");
  const [stageMsg, setStageMsg] = useState("");
  const [stageFile, setStageFile] = useState<string | undefined>();
  const [results, setResults] = useState<ProcessingResult[]>([]);
  const [newestIndex, setNewestIndex] = useState<number | null>(null);
  const [pdfUrls, setPdfUrls] = useState<Record<string, string>>({});
  const blobUrlsRef = useRef<string[]>([]);
  const autoStarted = useRef(false);
  const stageFileRef = useRef<string | undefined>();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [intervalMs, setIntervalMs] = useState<IncomingIntervalMs>(0);
  const [incoming, setIncoming] = useState<{
    filename: string;
    source: IncomingSource;
  } | null>(null);

  const sampleIndexRef = useRef(0);
  const busyRef = useRef(false);
  const processingRef = useRef(false);
  const pendingIncomingRef = useRef(false);
  const intervalMsRef = useRef<IncomingIntervalMs>(0);
  const langRef = useRef<Lang>(lang);
  const scheduleTimerRef = useRef<number | null>(null);
  const bannerTimerRef = useRef<number | null>(null);
  const toastHideTimerRef = useRef<number | null>(null);
  const hasQueuedFirstRef = useRef(false);
  const runSampleRef = useRef<(name: string) => void>(() => undefined);
  const followNewDocRef = useRef(false);
  const resultsLenRef = useRef(0);
  const keepToastRef = useRef(false);

  const featured = featuredSampleForLang(lang);

  useEffect(() => {
    busyRef.current = busy;
  }, [busy]);

  useEffect(() => {
    intervalMsRef.current = intervalMs;
  }, [intervalMs]);

  useEffect(() => {
    langRef.current = lang;
    // Restart the language-scoped sample rotation when UI language changes
    sampleIndexRef.current = 0;
  }, [lang]);

  useEffect(() => {
    stageFileRef.current = stageFile;
  }, [stageFile]);

  useEffect(() => {
    resultsLenRef.current = results.length;
  }, [results.length]);

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
      if (scheduleTimerRef.current != null) {
        window.clearTimeout(scheduleTimerRef.current);
      }
      if (bannerTimerRef.current != null) {
        window.clearTimeout(bannerTimerRef.current);
      }
      if (toastHideTimerRef.current != null) {
        window.clearTimeout(toastHideTimerRef.current);
      }
    };
  }, []);

  const clearBlobUrls = useCallback(() => {
    for (const u of blobUrlsRef.current) URL.revokeObjectURL(u);
    blobUrlsRef.current = [];
    setPdfUrls({});
  }, []);

  const scrollToProcessing = useCallback(() => {
    followNewDocRef.current = true;
    requestAnimationFrame(() => {
      document.getElementById("processing")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    });
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

  const clearSchedule = useCallback(() => {
    if (scheduleTimerRef.current != null) {
      window.clearTimeout(scheduleTimerRef.current);
      scheduleTimerRef.current = null;
    }
  }, []);

  const runProcess = useCallback(
    async (
      runner: (onEvent: (ev: StreamEvent) => void) => Promise<ProcessingResult[]>,
      urlMap?: Record<string, string>,
    ) => {
      if (processingRef.current) return;
      processingRef.current = true;
      pendingIncomingRef.current = false;
      setBusy(true);
      setPhase("extract");
      setStageMsg("");
      try {
        if (urlMap) {
          setPdfUrls((prev) => ({ ...prev, ...urlMap }));
        }
        const out = await runner(handleStreamEvent);
        const baseLen = resultsLenRef.current;
        setResults((prev) => {
          const next = [...prev, ...out];
          setNewestIndex(next.length > 0 ? next.length - 1 : null);
          return next;
        });
        setPhase("done");
        const scrollToIdx =
          out.length > 0 ? baseLen + out.length - 1 : null;
        requestAnimationFrame(() => {
          if (followNewDocRef.current && scrollToIdx != null) {
            followNewDocRef.current = false;
            document.getElementById(`result-${scrollToIdx}`)?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          } else if (baseLen === 0) {
            followNewDocRef.current = false;
            document.getElementById("results")?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          } else {
            followNewDocRef.current = false;
          }
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setResults((prev) => {
          const failed: ProcessingResult = {
            filename: stageFileRef.current || "error",
            success: false,
            error_message: message,
          };
          const next = [...prev, failed];
          setNewestIndex(next.length - 1);
          return next;
        });
      } finally {
        setBusy(false);
        processingRef.current = false;
        // Keep the "new document" toast until processing finishes (for video demos)
        if (keepToastRef.current) {
          keepToastRef.current = false;
          if (toastHideTimerRef.current != null) {
            window.clearTimeout(toastHideTimerRef.current);
          }
          toastHideTimerRef.current = window.setTimeout(() => {
            toastHideTimerRef.current = null;
            setIncoming(null);
          }, TOAST_DISMISS_AFTER_DONE_MS);
        }
      }
    },
    [handleStreamEvent],
  );

  const runFeatured = useCallback(() => {
    const name = featured;
    void runProcess((onEvent) => processSample(name, onEvent), {
      [name]: samplePdfUrl(name),
    });
  }, [featured, runProcess]);

  const runSample = useCallback(
    (name: string) => {
      void runProcess((onEvent) => processSample(name, onEvent), {
        [name]: samplePdfUrl(name),
      });
    },
    [runProcess],
  );

  useEffect(() => {
    runSampleRef.current = runSample;
  }, [runSample]);

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
    setNewestIndex(null);
    clearBlobUrls();
    setPhase("idle");
    setStageMsg("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [clearBlobUrls]);

  const clearToastTimers = useCallback(() => {
    if (bannerTimerRef.current != null) {
      window.clearTimeout(bannerTimerRef.current);
      bannerTimerRef.current = null;
    }
    if (toastHideTimerRef.current != null) {
      window.clearTimeout(toastHideTimerRef.current);
      toastHideTimerRef.current = null;
    }
  }, []);

  const triggerIncoming = useCallback(() => {
    if (
      busyRef.current ||
      processingRef.current ||
      pendingIncomingRef.current ||
      intervalMsRef.current === 0
    ) {
      return;
    }

    pendingIncomingRef.current = true;
    const currentLang = langRef.current;
    const list = demoSamplesForLang(currentLang);
    const pool =
      list.length > 0 ? list : [featuredSampleForLang(currentLang)];
    const name = pool[sampleIndexRef.current % pool.length];
    sampleIndexRef.current = (sampleIndexRef.current + 1) % pool.length;
    const source = SOURCES[Math.floor(Math.random() * SOURCES.length)];

    setIncoming({ filename: name, source });
    setSettingsOpen(false);
    clearToastTimers();
    keepToastRef.current = true;
    followNewDocRef.current = true; // auto-scroll to processing for demos

    // Brief “detected” beat, then start processing; toast stays until done
    bannerTimerRef.current = window.setTimeout(() => {
      bannerTimerRef.current = null;
      runSampleRef.current(name);
    }, INCOMING_BANNER_MS);
  }, [clearToastTimers]);

  const scheduleNextIncoming = useCallback(
    (delayMs: number) => {
      clearSchedule();
      if (intervalMsRef.current === 0) return;
      scheduleTimerRef.current = window.setTimeout(() => {
        scheduleTimerRef.current = null;
        if (
          busyRef.current ||
          processingRef.current ||
          pendingIncomingRef.current
        ) {
          scheduleNextIncoming(1500);
          return;
        }
        triggerIncoming();
      }, delayMs);
    },
    [clearSchedule, triggerIncoming],
  );

  // Enable / disable auto-incoming timer
  useEffect(() => {
    if (intervalMs === 0) {
      clearSchedule();
      hasQueuedFirstRef.current = false;
      pendingIncomingRef.current = false;
      clearToastTimers();
      setIncoming(null);
      return;
    }

    if (!hasQueuedFirstRef.current) {
      hasQueuedFirstRef.current = true;
      scheduleNextIncoming(FIRST_INCOMING_DELAY_MS);
    }

    return () => {
      // only clear on interval change / unmount handled by intervalMs===0 branch
    };
  }, [intervalMs, scheduleNextIncoming, clearSchedule, clearToastTimers]);

  // After each finished run, queue the next arrival when demo mode is on
  useEffect(() => {
    if (intervalMs === 0) return;
    if (busy) return;
    if (pendingIncomingRef.current) return;
    if (!hasQueuedFirstRef.current) return;
    // Skip the initial "never processed" idle state — the enable effect schedules first arrival
    if (results.length === 0 && sampleIndexRef.current === 0) return;
    scheduleNextIncoming(intervalMs);
  }, [busy, intervalMs, results, scheduleNextIncoming]);

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

  const showProcessing = busy || Boolean(incoming);
  const processingTimeline = showProcessing ? (
    <ProcessTimeline
      lang={lang}
      phase={incoming && !busy ? "extract" : phase}
      message={stageMsg}
      filename={incoming?.filename ?? stageFile}
    />
  ) : null;

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
          showRun={!busy && results.length === 0 && intervalMs === 0}
          settingsOpen={settingsOpen}
          intervalMs={intervalMs}
          onSettingsOpenChange={setSettingsOpen}
          onIntervalChange={setIntervalMs}
        />

        {incoming && (
          <IncomingBanner
            lang={lang}
            filename={incoming.filename}
            source={incoming.source}
            visible
            onOpen={scrollToProcessing}
          />
        )}

        {results.length === 0 && !busy && !incoming && (
          <Hero
            lang={lang}
            busy={busy}
            onRunFeatured={runFeatured}
            onBrowseUpload={browseUpload}
          />
        )}

        {results.length > 0 ? (
          <ResultLayout
            lang={lang}
            results={results}
            pdfUrls={pdfUrls}
            onClear={clearResults}
            newestIndex={newestIndex}
            processingSlot={processingTimeline}
          />
        ) : (
          processingTimeline
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
            {results.length === 0 && !incoming && (
              <p className="empty-hint">{t(lang, "empty")}</p>
            )}
          </>
        )}

        <Footer lang={lang} maxFiles={maxFiles} maxMb={maxMb} />
      </div>
    </div>
  );
}

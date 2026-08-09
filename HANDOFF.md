# Portfolio handoff — document-classifier

Use this file when wiring the case study on the main website.
The live demo is **already deployed** and self-contained (React SPA + FastAPI on Railway).

## Pre-flight (verified)

| Check | Status |
|-------|--------|
| Live demo URL | https://doc-classifier-production-8376.up.railway.app |
| `GET /api/health` | `status: ok` · featured: Hebrew invoice · limits 3 files / 5 MB |
| One-click sample process | Returns `success` + structured invoice fields |
| Samples | 9 built-in PDFs (invoice / contract / receipt HE+EN, plus EN quote, PO, bank statement) |
| Auth | None (public demo, sample data only) |
| Repo | https://github.com/BlusteinLidor/doc_classifier · branch `master` |

**Website work required:** paste case-study copy, set `href` / `demoUrl` to the live URL, optional video poster. No backend or secret changes on the portfolio site.

---

## Case study fields (paste)

Paste into the portfolio `lib/i18n/he.ts` / `lib/i18n/en.ts` case studies
(replace the placeholder study and set `href` / `hrefLabel` to the live demo).

```text
id: document-classifier
demoUrl: https://doc-classifier-production-8376.up.railway.app
title_en: Automatic Document Analysis & Cataloging
title_he: ניתוח וקטלוג אוטומטי של מסמכים
problem_en: Small businesses bury invoices and contracts in shared drives — finding the right file or key fields takes minutes every time.
problem_he: עסקים קטנים שומרים חשבוניות וחוזים בתיקיות משותפות — איתור המסמך הנכון או השדות החשובים גוזל דקות בכל פעם.
solution_en: Documents land on your desktop, Google Drive, or WhatsApp. The tool detects them automatically, classifies the type, and extracts structured fields in Hebrew or English — including vision OCR for image-only PDFs.
solution_he: המסמכים מגיעים למחשב / לגוגל דרייב / לווטסאפ, הכלי מזהה את זה אוטומטית, ומנתח אותם. אין צורך לעשות שום פעולה ידנית.
result_en: Instant category plus human-readable fields — fewer misfiled docs and faster follow-up without manual retyping.
result_he: סיווג מיידי ושדות קריאים — פחות מסמכים שמוגשים לא נכון ומענה מהיר יותר בלי להקליד מחדש.
tech: React, FastAPI, OpenAI, PyMuPDF, Pydantic
hrefLabel_en: Try it live
hrefLabel_he: נסו בשידור חי
videoUrl:
poster:
```

### Suggested EN object (adapt to site types)

```ts
{
  id: "document-classifier",
  title: "Automatic Document Analysis & Cataloging",
  problem:
    "Small businesses bury invoices and contracts in shared drives — finding the right file or key fields takes minutes every time.",
  solution:
    "Documents land on your desktop, Google Drive, or WhatsApp. The tool detects them automatically, classifies the type, and extracts structured fields in Hebrew or English — including vision OCR for image-only PDFs.",
  result:
    "Instant category plus human-readable fields — fewer misfiled docs and faster follow-up without manual retyping.",
  tech: ["React", "FastAPI", "OpenAI", "PyMuPDF", "Pydantic"],
  href: "https://doc-classifier-production-8376.up.railway.app",
  hrefLabel: "Try it live",
  // videoUrl / poster optional
}
```

### Suggested HE object (adapt to site types)

```ts
{
  id: "document-classifier",
  title: "ניתוח וקטלוג אוטומטי של מסמכים",
  problem:
    "עסקים קטנים שומרים חשבוניות וחוזים בתיקיות משותפות — איתור המסמך הנכון או השדות החשובים גוזל דקות בכל פעם.",
  solution:
    "המסמכים מגיעים למחשב / לגוגל דרייב / לווטסאפ, הכלי מזהה את זה אוטומטית, ומנתח אותם. אין צורך לעשות שום פעולה ידנית.",
  result:
    "סיווג מיידי ושדות קריאים — פחות מסמכים שמוגשים לא נכון ומענה מהיר יותר בלי להקליד מחדש.",
  tech: ["React", "FastAPI", "OpenAI", "PyMuPDF", "Pydantic"],
  href: "https://doc-classifier-production-8376.up.railway.app",
  hrefLabel: "נסו בשידור חי",
}
```

---

## Integration notes for the website

1. **Link out** to the Railway URL (new tab). Do **not** iframe the demo unless you accept third-party cookies/headers as-is; the SPA already sets full UI chrome.
2. **CTA copy:** `Open live demo` / `לפתיחת ההדגמה` (or site-default “Live demo”).
3. **Video (optional):** open `https://doc-classifier-production-8376.up.railway.app/?demo=1` — auto-runs the featured Hebrew invoice with stage timeline. Full recording tips in [DEMO.md](DEMO.md).
4. **Expect 15–45s** per analysis (OpenAI). Mention “live demo” not “instant API” in surrounding copy if needed.
5. **Do not** put `OPENAI_API_KEY` in the website repo; the demo owns its secret on Railway.

---

## Ops (demo only — not the website)

| Item | Detail |
|------|--------|
| Deploy | Railway Dockerfile · healthcheck `GET /api/health` |
| Secret | `OPENAI_API_KEY` on the Railway service |
| Redeploy | After repo push / secret change: `railway redeploy` |
| Limits | Max 3 PDFs / run, 5 MB each; OCR first 3 pages |
| Stack docs | [README.md](README.md) · [DEMO.md](DEMO.md) |

---

## Quick visitor path (for QA or video)

1. Open the live URL.
2. Switch EN ↔ עב once so language toggle is visible on camera.
3. Click **Run featured demo** (or land with `?demo=1`).
4. Wait for stages → type badge + totals → **Download JSON**.
5. Footer states: portfolio demo · sample data only.

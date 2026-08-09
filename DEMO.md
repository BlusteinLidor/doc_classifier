# Portfolio demo — Document Intelligence

Public demo that classifies business PDFs (invoice, receipt, quote, PO, contract,
bank statement, and more — or **other** / **unknown**), extracts structured fields,
and supports vision OCR for image-only PDFs.

Built with a **React** UI and **FastAPI** over the `doc_intel` pipeline.

**Website paste-ready copy:** [HANDOFF.md](HANDOFF.md).

## Try it

**Live demo:** https://doc-classifier-production-8376.up.railway.app

1. Open the URL above.
2. Optionally switch **EN / עב**, then click **Run featured demo** (or `?demo=1`).
3. Wait for the stage timeline, then classification + extracted fields (usually 15–45 seconds).

No login. Sample data only — not a live client system.

**Reset:** use **Clear results** / **Analyze another**, or refresh the browser.

## Local run

```bash
pip install -e ".[dev]"
cd frontend && npm install && cd ..
cp .env.example .env   # set OPENAI_API_KEY

# Terminal 1
uvicorn backend.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Open http://127.0.0.1:5173 — video mode: `?demo=1`

Regenerate sample PDFs (optional):

```bash
python scripts/generate_samples.py
```

Run unit tests:

```bash
pytest
```

## Environment / secrets

| Name | Required | Where |
|------|----------|--------|
| `OPENAI_API_KEY` | Yes | Local: `.env`. Railway: service variable |

## Deploy

### Live host (Railway)

The public portfolio demo currently runs on Railway:

https://doc-classifier-production-8376.up.railway.app

- Multi-stage Dockerfile builds the React SPA and serves it from FastAPI
- Set `OPENAI_API_KEY` as a Railway service variable
- Healthcheck: `GET /api/health`
- Redeploy after secret changes: `railway redeploy`

Demo limits (cost / abuse): max **3** PDFs per run, **5 MB** each; OCR limited to first **3** pages.

## API surface (demo)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/health` | Health + demo limits |
| GET | `/api/samples` | Sample metadata |
| GET | `/api/samples/{filename}` | Sample PDF bytes |
| POST | `/api/process/sample` | Process built-in sample (SSE) |
| POST | `/api/process` | Upload PDFs (SSE) |
| POST | `/api/export/json` | Batch JSON download |
| POST | `/api/export/csv` | Batch CSV download |

## Notes

- Prefer text PDFs; image-only PDFs fall back to **vision OCR** (OpenAI).
- Types: invoice · credit_note · receipt · quote · purchase_order · delivery_note ·
  contract · bank_statement · payslip · utility_bill · tax_document · correspondence ·
  other · unknown.
- Model: `gpt-4o-mini` (see `src/doc_intel/openai_client.py`).

## Recording a short video

1. Open `/?demo=1` (or click **Run featured demo**).
2. Leave the language toggle visible; switch EN ↔ עב after results appear.
3. Show the type badge + total amount, then **Download JSON**.
4. End on the footer (portfolio demo · sample data only).

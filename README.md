# AI Document Intelligence

Classify invoice / contract / receipt / quote / PO / bank statement and more PDF types
(or other / unknown), extract structured fields (English / Hebrew), with vision OCR
fallback for image-only scans.

**Stack:** React + FastAPI · OpenAI · PyMuPDF · Pydantic V2

**Live portfolio demo:** https://doc-classifier-production-8376.up.railway.app

See [DEMO.md](DEMO.md) for the happy path, secrets, and deploy notes.
Handoff copy for the portfolio site is in [HANDOFF.md](HANDOFF.md).

## Setup

1. Python 3.10+ and Node.js 20+
2. Create a virtual environment and install the API:

   ```bash
   pip install -e ".[dev]"
   ```

3. Install the frontend:

   ```bash
   cd frontend && npm install && cd ..
   ```

4. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.

## Run (local)

Terminal 1 — API:

```bash
uvicorn backend.main:app --reload --port 8000
```

Terminal 2 — SPA (proxies `/api` to port 8000):

```bash
cd frontend && npm run dev
```

Open http://127.0.0.1:5173

Video-mode auto-demo: http://127.0.0.1:5173?demo=1

### Production-like (built SPA served by FastAPI)

```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app --port 8000
```

Open http://127.0.0.1:8000

## Samples

Sample PDFs live in `samples/`. Regenerate with:

```bash
python scripts/generate_samples.py
```

## Tests

```bash
pytest
```

## Legacy Streamlit UI

The original Streamlit app remains at `app/streamlit_app.py` for reference:

```bash
streamlit run app/streamlit_app.py
```

The portfolio demo and Railway deploy use the React + FastAPI stack.

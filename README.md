# AI Document Intelligence

Classify invoice/contract PDFs and extract structured fields (English / Hebrew) using OpenAI structured outputs and Streamlit.

**Live portfolio demo:** https://doc-classifier-production-8376.up.railway.app  

See [DEMO.md](DEMO.md) for the happy path, secrets, and deploy notes. Handoff copy for the portfolio site is in [HANDOFF.md](HANDOFF.md).

## Setup

1. Python 3.10+
2. Create a virtual environment and install:

   ```bash
   pip install -e .
   ```

3. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.

## Run

```bash
streamlit run app/streamlit_app.py
```

Sample PDFs live in `samples/`. Regenerate with `python scripts/generate_samples.py`.

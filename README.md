# AI Document Intelligence

Classify invoice/contract PDFs and extract structured fields (English / Hebrew) using OpenAI structured outputs and Streamlit.

**Portfolio demo** — see [DEMO.md](DEMO.md) for the public happy path, secrets, and Streamlit Cloud deploy.

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

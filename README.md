# AI Document Intelligence PoC

Extract structured data from invoice/contract PDFs using OpenAI structured outputs and Streamlit.

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

If imports fail without editable install, run from the project root with `pip install -e .` first.

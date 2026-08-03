# Portfolio demo — Document Intelligence

Public Streamlit demo that classifies invoices vs contracts and extracts structured fields.

## Try it

1. Open the public URL (see repo README or portfolio Selected Work once wired).
2. Click one of the **sample** buttons (English invoice, Hebrew invoice, or English contract).
3. Wait for classification + extracted fields (usually under a minute).

No login. Sample data only — not a live client system.

**Reset:** refresh the browser page.

## Local run

```bash
pip install -e .
# or: pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
streamlit run app/streamlit_app.py
```

Regenerate sample PDFs (optional):

```bash
python scripts/generate_samples.py
```

## Environment / secrets

| Name | Required | Where |
|------|----------|--------|
| `OPENAI_API_KEY` | Yes | Local: `.env`. Streamlit Community Cloud: **App settings → Secrets** |

Streamlit secrets example:

```toml
OPENAI_API_KEY = "sk-..."
```

## Deploy (Streamlit Community Cloud)

One-click (pre-filled):  
[Deploy on Streamlit Community Cloud](https://share.streamlit.io/deploy?repository=BlusteinLidor/doc_classifier&branch=master&mainModule=app/streamlit_app.py)

Manual steps:

1. Repo is on GitHub: `BlusteinLidor/doc_classifier` (public).
2. Open the link above (or [share.streamlit.io](https://share.streamlit.io) → **Create app**).
3. Confirm branch `master`, main file `app/streamlit_app.py`.
4. **Secrets** (required for classify/extract to work):

   ```toml
   OPENAI_API_KEY = "sk-..."
   ```

5. Deploy. Public HTTPS URL looks like `https://<app-name>.streamlit.app`.

After deploy, confirm with:

```text
https://share.streamlit.io/api/v2/apps/disambiguate?path=BlusteinLidor/doc_classifier/master/app/streamlit_app.py
```

Demo limits (cost / abuse): max **3** PDFs per run, **5 MB** each.

## Notes

- Text-based PDFs only (no OCR for scanned images).
- Model: `gpt-4o-mini` (see `src/doc_intel/openai_client.py`).

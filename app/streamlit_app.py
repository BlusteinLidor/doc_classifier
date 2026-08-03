"""Streamlit UI: upload PDFs, preview, structured results (RTL-aware), export."""

from __future__ import annotations

import html
import json
import logging
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Allow running without `pip install -e .` during development
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from doc_intel.export import results_to_csv_bytes, results_to_json_bytes
from doc_intel.models import ContractExtraction, InvoiceExtraction, ProcessingResult
from doc_intel.pipeline import process_pdf_bytes

load_dotenv()


def _sync_streamlit_secrets() -> None:
    """Copy Streamlit Cloud secrets into env for the OpenAI client."""
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return
    if secret_key and not os.environ.get("OPENAI_API_KEY", "").strip():
        os.environ["OPENAI_API_KEY"] = str(secret_key).strip()


_sync_streamlit_secrets()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_SAMPLES_DIR = _ROOT / "samples"
_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
_MAX_FILES_PER_RUN = 3

_SAMPLE_DOCS: list[tuple[str, str, str]] = [
    ("sample_invoice_en.pdf", "English invoice", "Try English invoice"),
    ("sample_invoice_he.pdf", "Hebrew invoice", "Try Hebrew invoice"),
    ("sample_contract_en.pdf", "English contract", "Try English contract"),
]

st.set_page_config(
    page_title="Document Intelligence — Portfolio Demo",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_PAGE_STYLE = """
<style>
.rtl-block { direction: rtl; text-align: right; unicode-bidi: plaintext;
  font-family: "Segoe UI", "Arial Hebrew", Tahoma, sans-serif;
  max-height: 420px; overflow: auto; padding: 0.5rem; border-radius: 6px;
  background: rgba(128,128,128,0.08); }
.demo-banner {
  background: #f0f4f8; border: 1px solid #c5d0dc; border-radius: 8px;
  padding: 0.75rem 1rem; margin-bottom: 1rem; }
.demo-banner strong { display: block; margin-bottom: 0.25rem; }
.doc-badge {
  display: inline-block; font-size: 1.35rem; font-weight: 700;
  letter-spacing: 0.02em; padding: 0.4rem 0.9rem; border-radius: 8px;
  margin: 0.35rem 0 0.75rem 0; }
.doc-badge-invoice { background: #dbeafe; color: #1e3a8a; }
.doc-badge-contract { background: #dcfce7; color: #14532d; }
.doc-badge-unknown { background: #f3f4f6; color: #374151; }
</style>
"""


def _structured_to_rtl_html(obj: InvoiceExtraction | ContractExtraction) -> str:
    data = obj.model_dump()
    parts: list[str] = ['<div class="rtl-block">']
    for key, val in data.items():
        if val is None or val == [] or val == {}:
            continue
        label = html.escape(str(key))
        if isinstance(val, list):
            items = []
            for item in val:
                if isinstance(item, dict):
                    items.append(html.escape(json.dumps(item, ensure_ascii=False)))
                else:
                    items.append(html.escape(str(item)))
            inner = "<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>"
            parts.append(f"<p><b>{label}</b>: {inner}</p>")
        else:
            parts.append(f"<p><b>{label}</b>: {html.escape(str(val))}</p>")
    parts.append("</div>")
    return "".join(parts)


def _render_pdf_preview(data: bytes, filename: str) -> None:
    if hasattr(st, "pdf"):
        st.pdf(data, height=560)
    else:
        st.warning("PDF preview requires a newer Streamlit version.")
        st.download_button(
            label=f"Download {filename}",
            data=data,
            file_name=filename,
            mime="application/pdf",
        )


def _doc_type_badge_html(doc_type: str | None) -> str:
    if doc_type == "invoice":
        label, css = "Invoice", "doc-badge-invoice"
    elif doc_type == "contract":
        label, css = "Contract", "doc-badge-contract"
    else:
        label, css = "Unknown type", "doc-badge-unknown"
    return f'<div class="doc-badge {css}">{html.escape(label)}</div>'


def _load_sample(filename: str) -> bytes:
    path = _SAMPLES_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Sample not found: {path}")
    return path.read_bytes()


def _process_file_list(files: list[tuple[str, bytes]]) -> None:
    """Run the pipeline on (name, bytes) pairs and store results in session state."""
    if not files:
        return
    if len(files) > _MAX_FILES_PER_RUN:
        st.error(f"Demo limit: analyze at most {_MAX_FILES_PER_RUN} files per run.")
        return

    results: list[ProcessingResult] = []
    blobs: dict[str, bytes] = {}
    progress_slot = st.empty()
    progress_slot.progress(0.0, text="Starting…")
    status = st.empty()

    n = len(files)
    for idx, (name, data) in enumerate(files):
        if len(data) > _MAX_FILE_BYTES:
            results.append(
                ProcessingResult(
                    filename=name,
                    success=False,
                    error_message=(
                        f"File exceeds demo size limit "
                        f"({_MAX_FILE_BYTES // (1024 * 1024)} MB)."
                    ),
                )
            )
            continue

        blobs[name] = data
        progress_slot.progress(idx / max(n, 1), text=f"Reading {name}…")
        status.info("Analyzing document structure…")

        with st.status(f"Processing **{name}**", expanded=True) as s:
            s.update(label=f"Extracting text: **{name}**", state="running")
            s.write("Extracting text from PDF…")
            s.write("Consulting AI for classification and fields…")
            result = process_pdf_bytes(name, data)
            if result.success:
                s.update(label=f"Done: **{name}**", state="complete")
            else:
                s.update(label=f"Issue: **{name}**", state="error")
            results.append(result)

        progress_slot.progress((idx + 1) / n, text=f"Finished {idx + 1} of {n}")
        status.empty()

    st.session_state["last_results"] = results
    st.session_state["pdf_blobs"] = blobs
    progress_slot.empty()


def _render_demo_banner() -> None:
    st.markdown(
        """
        <div class="demo-banner">
          <strong>Portfolio demo — sample data only.</strong>
          <span>No real client documents. Try a one-click sample below.</span>
          <div style="direction: rtl; margin-top: 0.35rem; font-size: 0.95rem;">
            הדגמה לתיק עבודות — נתוני דוגמה בלבד.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sample_buttons() -> None:
    st.markdown("**Try a sample (no upload needed)**")
    cols = st.columns(len(_SAMPLE_DOCS))
    for col, (filename, _label, button_label) in zip(cols, _SAMPLE_DOCS):
        with col:
            if st.button(button_label, key=f"sample_{filename}", use_container_width=True):
                try:
                    data = _load_sample(filename)
                except FileNotFoundError:
                    st.error(f"Sample missing: {filename}. Regenerate with scripts/generate_samples.py.")
                    return
                _process_file_list([(filename, data)])
                st.rerun()


def _render_results(results: list[ProcessingResult], blobs: dict[str, bytes]) -> None:
    st.subheader("Results")
    json_bytes = results_to_json_bytes(results)
    csv_bytes = results_to_csv_bytes(results)
    d1, d2, _ = st.columns([1, 1, 2])
    with d1:
        st.download_button(
            "Download JSON",
            data=json_bytes,
            file_name="extractions.json",
            mime="application/json",
        )
    with d2:
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name="extractions.csv",
            mime="text/csv",
        )

    for r in results:
        with st.expander(r.filename, expanded=True):
            blob = blobs.get(r.filename)
            if not r.success:
                st.error(r.error_message or "Processing failed.")
                if r.warnings:
                    st.caption("Warnings: " + " · ".join(r.warnings))
                err_left, err_right = st.columns(2)
                with err_left:
                    st.markdown("**Original PDF**")
                    if blob:
                        _render_pdf_preview(blob, r.filename)
                    else:
                        st.caption("PDF bytes not available for preview.")
                with err_right:
                    st.markdown("**Extracted text preview**")
                    if r.raw_text_preview:
                        st.text_area(
                            "preview",
                            r.raw_text_preview,
                            height=280,
                            label_visibility="collapsed",
                        )
                    else:
                        st.caption("No text extracted.")
                continue

            st.markdown("**Classification**")
            st.markdown(_doc_type_badge_html(r.doc_type), unsafe_allow_html=True)

            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown("**Original PDF**")
                if blob:
                    _render_pdf_preview(blob, r.filename)
                else:
                    st.caption("PDF bytes not available for preview.")

            with c_right:
                st.markdown("**Extracted data**")
                if r.warnings:
                    st.caption("Warnings: " + " · ".join(r.warnings))
                if r.structured is not None:
                    st.markdown("RTL view (Hebrew-friendly)")
                    st.markdown(_structured_to_rtl_html(r.structured), unsafe_allow_html=True)
                    st.markdown("**JSON**")
                    st.json(r.structured.model_dump())
                else:
                    st.warning("No structured fields returned.")

            if r.raw_text_preview:
                with st.expander("Text preview (extracted)"):
                    st.text(r.raw_text_preview)


def main() -> None:
    st.title("AI Document Intelligence")
    st.caption(
        "Classify invoices and contracts, then extract structured fields "
        "(English / Hebrew)."
    )

    st.markdown(_PAGE_STYLE, unsafe_allow_html=True)
    _render_demo_banner()
    _render_sample_buttons()

    st.markdown("---")
    st.markdown("**Or upload your own PDFs** (demo: max 3 files, 5 MB each)")

    uploaded = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    col_run, _ = st.columns([1, 4])
    with col_run:
        run = st.button(
            "Analyze documents",
            type="primary",
            disabled=not uploaded,
            use_container_width=True,
        )

    if run and uploaded:
        files_list = list(uploaded)[:_MAX_FILES_PER_RUN]
        if len(uploaded) > _MAX_FILES_PER_RUN:
            st.warning(
                f"Only the first {_MAX_FILES_PER_RUN} files will be analyzed (demo limit)."
            )
        prepared: list[tuple[str, bytes]] = [
            (f.name, f.getvalue()) for f in files_list
        ]
        _process_file_list(prepared)

    results: list[ProcessingResult] = st.session_state.get("last_results", [])
    blobs = st.session_state.get("pdf_blobs", {})

    if not results:
        st.info(
            "Click a **sample** above (fastest), or upload PDFs and click "
            "**Analyze documents**."
        )
        return

    _render_results(results, blobs)


if __name__ == "__main__":
    main()

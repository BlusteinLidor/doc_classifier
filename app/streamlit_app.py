"""Streamlit UI: upload PDFs, preview, structured results (RTL-aware), export."""

from __future__ import annotations

import html
import json
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Document Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_RTL_STYLE = """
<style>
.rtl-block { direction: rtl; text-align: right; unicode-bidi: plaintext;
  font-family: "Segoe UI", "Arial Hebrew", Tahoma, sans-serif;
  max-height: 420px; overflow: auto; padding: 0.5rem; border-radius: 6px;
  background: rgba(128,128,128,0.08); }
</style>
"""


def _structured_to_rtl_html(obj: InvoiceExtraction | ContractExtraction) -> str:
    data = obj.model_dump()
    parts: list[str] = [f'<div class="rtl-block">']
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


def main() -> None:
    st.title("AI Document Intelligence")
    st.caption("Extract structured data from invoices and contracts (English / Hebrew).")

    st.markdown(_RTL_STYLE, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )

    col_run, _ = st.columns([1, 4])
    with col_run:
        run = st.button("Analyze documents", type="primary", disabled=not uploaded)

    if run and uploaded:
        results: list[ProcessingResult] = []
        blobs: dict[str, bytes] = {}
        progress_slot = st.empty()
        progress_slot.progress(0.0, text="Starting…")
        status = st.empty()

        files_list = list(uploaded)
        n = len(files_list)
        for idx, f in enumerate(files_list):
            name = f.name
            data = f.getvalue()
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

    results: list[ProcessingResult] = st.session_state.get("last_results", [])
    blobs = st.session_state.get("pdf_blobs", {})

    if not results:
        st.info("Upload PDFs and click **Analyze documents** to see previews and extracted data.")
        return

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


if __name__ == "__main__":
    main()

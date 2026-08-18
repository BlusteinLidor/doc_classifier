from doc_intel.errors import PDFError
from doc_intel.extractor import extract_pdf_text


def test_extract_pdf_text_empty_bytes_raises() -> None:
    try:
        extract_pdf_text(b"")
        assert False, "Expected PDFError"
    except PDFError:
        assert True

from doc_intel.export import audit_report_json_bytes, results_to_csv_bytes
from doc_intel.models import ProcessingResult


def test_results_to_csv_bytes_has_header() -> None:
    result = ProcessingResult(filename="a.pdf", success=True, doc_type="invoice")
    csv_bytes = results_to_csv_bytes([result], utf8_bom=False)
    assert b"filename" in csv_bytes
    assert b"a.pdf" in csv_bytes


def test_audit_report_contains_summary() -> None:
    result = ProcessingResult(filename="a.pdf", success=False, error_message="boom")
    payload = audit_report_json_bytes([result]).decode("utf-8")
    assert '"summary"' in payload
    assert '"failed": 1' in payload

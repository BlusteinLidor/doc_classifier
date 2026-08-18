from pathlib import Path

from doc_intel.ingestion.local_source import list_new_local_pdfs


def test_list_new_local_pdfs_detects_new(tmp_path: Path) -> None:
    f = tmp_path / "x.pdf"
    f.write_bytes(b"%PDF-1.5 test")
    results = list_new_local_pdfs(str(tmp_path), {})
    assert len(results) == 1
    assert results[0][0] == "x.pdf"

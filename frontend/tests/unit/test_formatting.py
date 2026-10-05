from shared.utils.formatting import format_bytes, format_datetime, safe_filename


def test_format_bytes():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1023) == "1023 B"
    assert format_bytes(2048) == "2.0 KB"
    assert format_bytes(5 * 1024 * 1024) == "5.0 MB"
    assert format_bytes(None) == "-" and format_bytes(-1) == "-"


def test_format_datetime():
    assert format_datetime("2026-03-12T14:05:00Z") == "12 Mar 2026, 14:05"
    assert format_datetime("2026-03-12T14:05:00") == "12 Mar 2026, 14:05"
    assert format_datetime("2026-03-12T16:05:00+02:00") == "12 Mar 2026, 14:05"
    assert format_datetime(None) == "-" and format_datetime("garbage") == "-"


def test_safe_filename_strips_paths_and_oddities():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("C:\\x\\my cv (1).pdf") == "my_cv_1_.pdf"
    assert "/" not in safe_filename("a/b/c.pdf") and "\\" not in safe_filename("a\\b.pdf")
    assert safe_filename("") == "file.pdf" and safe_filename("...") == "file.pdf"
    assert safe_filename("r\u00e9sum\u00e9.pdf") == "resume.pdf"
    assert len(safe_filename("x" * 300 + ".pdf")) <= 100 and safe_filename("x" * 300 + ".pdf").endswith(".pdf")

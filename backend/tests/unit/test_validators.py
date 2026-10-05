import pytest

from app.internal.validators import (
    sanitize_filename,
    validate_github,
    validate_password,
    validate_username,
    validated_pdf_chunks,
)
from app.pkg.errors import PayloadTooLarge, ValidationFailed


def test_username_lowercased():
    assert validate_username("Alice_01") == "alice_01"


@pytest.mark.parametrize("bad", ["ab", "a" * 51, "bad name", "bad@name"])
def test_username_rejected(bad):
    with pytest.raises(ValueError):
        validate_username(bad)


def test_password_bounds_are_bytes():
    assert validate_password("12345678")
    with pytest.raises(ValueError):
        validate_password("short")
    assert validate_password("a" * 72)
    with pytest.raises(ValueError):
        validate_password("a" * 73)
    with pytest.raises(ValueError):  # 37 chars but 74 bytes
        validate_password("é" * 37)


def test_github():
    assert validate_github(None) is None
    assert validate_github("") is None
    assert validate_github("https://github.com/alice") == "https://github.com/alice"
    for bad in ("http://github.com/a", "https://evil.com/a", "https://github.com/"):
        with pytest.raises(ValueError):
            validate_github(bad)


def test_pdf_stream_ok_with_tiny_first_chunks():
    out = b"".join(validated_pdf_chunks([b"%P", b"DF-", b"1.4 rest"], 100))
    assert out == b"%PDF-1.4 rest"


def test_pdf_stream_rejects_non_pdf_even_if_declared():
    with pytest.raises(ValidationFailed):
        list(validated_pdf_chunks([b"GIF89a....."], 100))


@pytest.mark.parametrize("chunks", [[], [b""], [b"%PD"]])
def test_pdf_stream_rejects_empty_or_truncated(chunks):
    with pytest.raises(ValidationFailed):
        list(validated_pdf_chunks(chunks, 100))


def test_pdf_stream_too_large():
    with pytest.raises(PayloadTooLarge):
        list(validated_pdf_chunks([b"%PDF-" + b"x" * 10, b"y" * 100], 50))


def test_sanitize_filename():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("C:\\x\\cv.pdf") == "cv.pdf"
    assert sanitize_filename(None) == "resume.pdf"
    assert sanitize_filename("a\x00b.pdf") == "ab.pdf"
    assert len(sanitize_filename("a" * 400)) == 255

"""Pure input validation helpers used by DTOs and services."""

import re
from typing import Iterable, Iterator

from app.pkg.errors import PayloadTooLarge, ValidationFailed

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
GITHUB_PREFIX = "https://github.com/"
PASSWORD_MIN_BYTES = 8
PASSWORD_MAX_BYTES = 72  # bcrypt limit
PDF_MAGIC = b"%PDF-"


def validate_username(value: str) -> str:
    if not 3 <= len(value) <= 50:
        raise ValueError("username must be 3-50 characters")
    if not USERNAME_RE.match(value):
        raise ValueError("username may only contain letters, digits, '_', '.', '-'")
    return value.lower()


def validate_password(value: str) -> str:
    size = len(value.encode("utf-8"))
    if size < PASSWORD_MIN_BYTES:
        raise ValueError(f"password must be at least {PASSWORD_MIN_BYTES} bytes")
    if size > PASSWORD_MAX_BYTES:
        raise ValueError(f"password must be at most {PASSWORD_MAX_BYTES} bytes")
    return value


def validate_github(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if not value.startswith(GITHUB_PREFIX) or len(value) <= len(GITHUB_PREFIX):
        raise ValueError(f"github must be a {GITHUB_PREFIX} URL")
    if len(value) > 250:
        raise ValueError("github URL too long")
    return value


def validated_pdf_chunks(chunks: Iterable[bytes], max_bytes: int) -> Iterator[bytes]:
    """Pass chunks through while enforcing the %PDF- header and the size limit.

    Raises ValidationFailed (not a PDF / empty) or PayloadTooLarge while being iterated.
    """
    head = b""
    total = 0
    checked = False
    for chunk in chunks:
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            raise PayloadTooLarge(f"File too large. Maximum {max_bytes // (1024 * 1024)}MB allowed")
        if not checked:
            head += chunk
            if len(head) < len(PDF_MAGIC):
                continue
            if not head.startswith(PDF_MAGIC):
                raise ValidationFailed("Only PDF files are allowed")
            checked = True
            yield head
        else:
            yield chunk
    if not checked:
        raise ValidationFailed("Only PDF files are allowed")


def sanitize_filename(name: str | None) -> str:
    base = re.split(r"[\\/]", name or "")[-1]
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return (base or "resume.pdf")[:255]

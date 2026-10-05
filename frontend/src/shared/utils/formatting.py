"""Display formatting helpers."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional


def format_bytes(size: Optional[int]) -> str:
    if size is None or size < 0:
        return "-"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_datetime(value: Optional[str]) -> str:
    """ISO-8601 string -> '12 Mar 2026, 14:05' (UTC); '-' when missing/invalid."""
    parsed = parse_datetime(value)
    if parsed is None:
        return "-"
    return parsed.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M")


_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str, default: str = "file.pdf", max_length: int = 100) -> str:
    """Reduce an untrusted file name to a safe basename (no paths, no odd characters)."""
    base = (name or "").replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii")
    base = _UNSAFE.sub("_", base).strip("._")
    if not base:
        return default
    if len(base) > max_length:
        stem, dot, ext = base.rpartition(".")
        base = (stem[: max_length - len(ext) - 1] + "." + ext) if dot else base[:max_length]
    return base

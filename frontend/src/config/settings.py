"""Typed, validated runtime configuration (contract: docs/architecture/contracts.md section 3)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

# Directory that Flet serves as static assets (icons, and short-lived downloads).
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DOWNLOADS_SUBDIR = "downloads"

DEFAULT_BACKEND_URL = "http://backend:8000"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8001
DEFAULT_UPLOAD_TMP_DIR = "/tmp/uploads"
DEFAULT_REQUEST_TIMEOUT = 15.0
DEFAULT_MAX_UPLOAD_MB = 10


class ConfigError(RuntimeError):
    """Raised when the environment does not satisfy the configuration contract."""


@dataclass(frozen=True)
class Settings:
    backend_url: str
    flet_host: str
    flet_port: int
    flet_secret_key: str
    upload_tmp_dir: str
    request_timeout: float
    max_upload_mb: int
    open_browser: bool
    assets_dir: str

    @property
    def downloads_dir(self) -> str:
        return str(Path(self.assets_dir) / DOWNLOADS_SUBDIR)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def _parse_int(name: str, raw: str, minimum: int, maximum: int) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}, got {value}")
    return value


def _parse_timeout(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"REQUEST_TIMEOUT must be a number, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError("REQUEST_TIMEOUT must be greater than 0")
    return value


def _parse_backend_url(raw: str) -> str:
    url = raw.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        raise ConfigError(f"BACKEND_URL must start with http:// or https://, got {raw!r}")
    return url


def load_settings(
    env: Optional[Mapping[str, str]] = None, *, require_secret: bool = True
) -> Settings:
    """Build Settings from the environment. Fails clearly on invalid/missing values."""
    source = os.environ if env is None else env

    def get(name: str, default: str) -> str:
        value = source.get(name, "")
        return value.strip() if value and value.strip() else default

    secret = get("FLET_SECRET_KEY", "")
    if require_secret and not secret:
        raise ConfigError(
            "FLET_SECRET_KEY is required (Flet signs browser upload URLs with it). "
            "Set it to a long random string, e.g. `openssl rand -hex 32`."
        )

    return Settings(
        backend_url=_parse_backend_url(get("BACKEND_URL", DEFAULT_BACKEND_URL)),
        flet_host=get("FLET_HOST", DEFAULT_HOST),
        flet_port=_parse_int("FLET_PORT", get("FLET_PORT", str(DEFAULT_PORT)), 1, 65535),
        flet_secret_key=secret,
        upload_tmp_dir=get("UPLOAD_TMP_DIR", DEFAULT_UPLOAD_TMP_DIR),
        request_timeout=_parse_timeout(get("REQUEST_TIMEOUT", str(DEFAULT_REQUEST_TIMEOUT))),
        max_upload_mb=_parse_int("MAX_UPLOAD_MB", get("MAX_UPLOAD_MB", str(DEFAULT_MAX_UPLOAD_MB)), 1, 200),
        open_browser=get("FLET_OPEN_BROWSER", "false").lower() in {"1", "true", "yes"},
        assets_dir=str(ASSETS_DIR),
    )

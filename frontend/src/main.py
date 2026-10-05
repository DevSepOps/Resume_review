"""Entry point: starts the Flet web server. All app state is created per session in ``main(page)``."""
from __future__ import annotations

import logging
import os
import sys
from typing import Callable

import flet as ft

from app.router import SessionApp
from config.settings import ConfigError, Settings, load_settings
from shared.components.downloader import purge_downloads

logger = logging.getLogger("resume_review.frontend")


def make_session_handler(settings: Settings) -> Callable[[ft.Page], None]:
    """Return the per-session target. Nothing mutable is shared between sessions."""

    def main(page: ft.Page) -> None:
        SessionApp(page, settings).start()

    return main


def run() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        settings = load_settings()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(2)

    os.makedirs(settings.upload_tmp_dir, mode=0o700, exist_ok=True)
    purge_downloads(settings.downloads_dir)
    os.makedirs(settings.downloads_dir, exist_ok=True)
    # Flet reads these from the environment.
    os.environ.setdefault("FLET_SECRET_KEY", settings.flet_secret_key)
    os.environ.setdefault("FLET_MAX_UPLOAD_SIZE", str(settings.max_upload_bytes))

    logger.info("Starting frontend on %s:%s (backend %s)", settings.flet_host, settings.flet_port,
                settings.backend_url)
    ft.app(
        target=make_session_handler(settings),
        host=settings.flet_host,
        port=settings.flet_port,
        # view=None: serve only, never try to open a browser/desktop client.
        view=ft.AppView.WEB_BROWSER if settings.open_browser else None,
        assets_dir=settings.assets_dir,
        upload_dir=settings.upload_tmp_dir,
    )


if __name__ == "__main__":
    run()

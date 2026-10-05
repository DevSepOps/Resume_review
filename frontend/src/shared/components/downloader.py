"""Deliver server-side fetched bytes (an authenticated PDF) to the user.

Web: the PDF is written under ``<assets>/downloads/<random token>/<name>`` and offered through
a dialog button (a real user click, so popup blockers do not interfere). The unguessable
128-bit token acts as a short-lived capability URL; the file is deleted after ``ttl`` seconds.
Desktop: ``FilePicker.save_file`` writes to the chosen location.
"""
from __future__ import annotations

import logging
import os
import shutil
import threading
import uuid
from typing import Optional
from urllib.parse import quote

import flet as ft

from shared.utils.formatting import safe_filename

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 120


def purge_downloads(downloads_dir: str) -> None:
    """Remove leftovers from previous runs (called at startup)."""
    shutil.rmtree(downloads_dir, ignore_errors=True)


def stage_download(downloads_dir: str, filename: str, data: bytes) -> str:
    """Write ``data`` into a fresh random directory; return the token."""
    token = uuid.uuid4().hex
    target_dir = os.path.join(downloads_dir, token)
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, safe_filename(filename)), "wb") as handle:
        handle.write(data)
    return token


def remove_download(downloads_dir: str, token: str) -> None:
    shutil.rmtree(os.path.join(downloads_dir, token), ignore_errors=True)


def download_path(downloads_dir: str, token: str, filename: str) -> str:
    """Root-relative link, resolved by the browser against the page origin.

    ``page.url`` cannot be used: Flet derives it from the websocket URL (``ws://...``),
    which a browser tab cannot open and which ignores TLS termination at the proxy.
    """
    return f"/{os.path.basename(downloads_dir)}/{token}/{quote(filename)}"


class Downloader:
    def __init__(self, page: ft.Page, downloads_dir: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        self._page = page
        self._dir = downloads_dir
        self._ttl = ttl
        self._pending: Optional[bytes] = None
        self._picker: Optional[ft.FilePicker] = None
        if not page.web:
            self._picker = ft.FilePicker(on_result=self._on_saved)
            page.overlay.append(self._picker)

    def deliver(self, filename: str, data: bytes) -> None:
        name = safe_filename(filename)
        if self._picker is not None:
            self._pending = data
            self._picker.save_file(file_name=name, allowed_extensions=["pdf"])
            return
        token = stage_download(self._dir, name, data)
        timer = threading.Timer(self._ttl, remove_download, args=(self._dir, token))
        timer.daemon = True
        timer.start()
        self._show_dialog(name, download_path(self._dir, token, name))

    def _show_dialog(self, name: str, url: str) -> None:
        dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Your file is ready"),
            content=ft.Text(f"{name}\nThe link stays valid for {self._ttl // 60} minutes."),
            actions=[
                ft.FilledButton("Open PDF", icon=ft.Icons.OPEN_IN_NEW, url=url,
                                url_target=ft.UrlTarget.BLANK,
                                on_click=lambda _: self._page.close(dialog)),
                ft.TextButton("Close", on_click=lambda _: self._page.close(dialog)),
            ],
        )
        self._page.open(dialog)

    def _on_saved(self, event: ft.FilePickerResultEvent) -> None:
        data, self._pending = self._pending, None
        if event.path and data is not None:
            try:
                with open(event.path, "wb") as handle:
                    handle.write(data)
            except OSError:
                logger.exception("Could not save downloaded file")

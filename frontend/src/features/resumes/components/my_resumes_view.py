"""Candidate's own resumes: list, download, delete."""
from __future__ import annotations

import logging
from typing import Callable

import flet as ft

from features.resumes.components.resume_row import resume_row
from features.resumes.models import Resume
from features.resumes.services.resume_service import ResumeService
from shared.components.downloader import Downloader
from shared.components.panels import empty_panel, error_panel, loading_panel, page_header
from shared.components.snackbar import notify
from shared.lib.api_client import ApiError

logger = logging.getLogger(__name__)


class MyResumesView:
    def __init__(self, page: ft.Page, service: ResumeService, downloader: Downloader,
                 on_error: Callable[[ApiError], bool], go_upload: Callable[[], None]) -> None:
        self._page = page
        self._service = service
        self._downloader = downloader
        self._on_error = on_error  # returns True when it handled a session expiry
        self._go_upload = go_upload
        self.body = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def build(self) -> ft.Control:
        header = page_header(
            "My resumes", "Your uploaded PDFs, newest first.",
            [ft.FilledButton("Upload", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _e: self._go_upload())])
        self.body.controls = [loading_panel()]
        return ft.Column([header, ft.Divider(height=8, color=ft.Colors.TRANSPARENT), self.body],
                         expand=True, spacing=8)

    def load(self, _e=None) -> None:
        try:
            resumes = self._service.list_mine()
        except ApiError as exc:
            if self._on_error(exc):
                return
            self.body.controls = [error_panel(exc.message, self.load)]
        else:
            self.body.controls = [self._row(r) for r in resumes] or [self._empty()]
        self._page.update()

    def _empty(self) -> ft.Control:
        return empty_panel(ft.Icons.DESCRIPTION_OUTLINED, "No resumes yet",
                           "Upload a PDF to get started.",
                           ft.FilledButton("Upload your first resume", on_click=lambda _e: self._go_upload()))

    def _row(self, resume: Resume) -> ft.Control:
        return resume_row(resume, on_download=self._download, on_delete=self._confirm_delete)

    def _download(self, resume: Resume) -> None:
        try:
            name, data = self._service.download(resume.id, resume.file_name)
        except ApiError as exc:
            if not self._on_error(exc):
                notify(self._page, exc.message, error=True)
            return
        self._downloader.deliver(name, data)

    def _confirm_delete(self, resume: Resume) -> None:
        def confirm(_e) -> None:
            self._page.close(dialog)
            self._delete(resume)

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text("Delete this resume?"),
            content=ft.Text(f"\"{resume.file_name}\" will be permanently removed."),
            actions=[ft.TextButton("Cancel", on_click=lambda _e: self._page.close(dialog)),
                     ft.FilledButton("Delete", bgcolor=ft.Colors.RED_700, on_click=confirm)])
        self._page.open(dialog)

    def _delete(self, resume: Resume) -> None:
        try:
            self._service.delete(resume.id)
        except ApiError as exc:
            if not self._on_error(exc):
                notify(self._page, exc.message, error=True)
            return
        notify(self._page, "Resume deleted.")
        self.load()

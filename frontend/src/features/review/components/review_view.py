"""Expert / admin view: every uploaded resume with owner details."""
from __future__ import annotations

from typing import Callable, List

import flet as ft

from features.resumes.components.resume_row import resume_row
from features.resumes.models import Resume
from features.review.services.review_service import PAGE_SIZE, ReviewService
from shared.components.downloader import Downloader
from shared.components.panels import empty_panel, error_panel, loading_panel, page_header
from shared.components.snackbar import notify
from shared.lib.api_client import ApiError


class ReviewView:
    def __init__(self, page: ft.Page, service: ReviewService, downloader: Downloader,
                 on_error: Callable[[ApiError], bool]) -> None:
        self._page = page
        self._service = service
        self._downloader = downloader
        self._on_error = on_error
        self._resumes: List[Resume] = []
        self._more = False
        self.body = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def build(self) -> ft.Control:
        self.body.controls = [loading_panel()]
        return ft.Column([page_header("Review resumes", "Everything candidates have uploaded."), self.body],
                         expand=True, spacing=16)

    def load(self, _e=None) -> None:
        self._resumes, self._more = [], False
        self._fetch()

    def _load_more(self, _e=None) -> None:
        self._fetch()

    def _fetch(self) -> None:
        try:
            batch = self._service.list_all(skip=len(self._resumes), limit=PAGE_SIZE)
        except ApiError as exc:
            if self._on_error(exc):
                return
            self.body.controls = [error_panel(exc.message, self.load)]
            self._page.update()
            return
        self._resumes.extend(batch)
        self._more = len(batch) == PAGE_SIZE
        self._render()

    def _render(self) -> None:
        rows: List[ft.Control] = [resume_row(r, on_download=self._download, show_owner=True)
                                  for r in self._resumes]
        if not rows:
            rows = [empty_panel(ft.Icons.INBOX_OUTLINED, "Nothing to review yet",
                                "Resumes appear here as candidates upload them.")]
        elif self._more:
            rows.append(ft.Row([ft.OutlinedButton("Load more", on_click=self._load_more)],
                               alignment=ft.MainAxisAlignment.CENTER))
        self.body.controls = rows
        self._page.update()

    def _download(self, resume: Resume) -> None:
        try:
            name, data = self._service.download(resume.id, resume.file_name)
        except ApiError as exc:
            if not self._on_error(exc):
                notify(self._page, exc.message, error=True)
            return
        self._downloader.deliver(name, data)

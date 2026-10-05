"""Upload a PDF resume.

Web: the browser PUTs the file to Flet (signed URL) into UPLOAD_TMP_DIR; once progress hits 1.0
the file is forwarded to the backend server-side and the temp file is deleted.
Desktop: the picked file's local path is read directly.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Callable, Optional

import flet as ft

from features.resumes.services.resume_service import ResumeService
from shared.components.panels import MUTED, page_header
from shared.components.snackbar import notify
from shared.lib.api_client import ApiError
from shared.utils.formatting import format_bytes, safe_filename

logger = logging.getLogger(__name__)


def validate_pdf_choice(name: str, size: int, max_bytes: int) -> str:
    if not name.lower().endswith(".pdf"):
        return "Please choose a PDF file."
    if size <= 0:
        return "That file is empty."
    if size > max_bytes:
        return f"That file is too large (limit {format_bytes(max_bytes)})."
    return ""


class UploadView:
    def __init__(self, page: ft.Page, service: ResumeService, *, upload_dir: str, max_bytes: int,
                 on_error: Callable[[ApiError], bool], on_done: Callable[[], None]) -> None:
        self._page = page
        self._service = service
        self._upload_dir = os.path.realpath(upload_dir)
        self._max_bytes = max_bytes
        self._on_error = on_error
        self._on_done = on_done
        self._file: Optional[ft.FilePickerFile] = None
        self._staged: Optional[str] = None  # temp file name inside upload_dir (web)

        self.picker = ft.FilePicker(on_result=self._on_picked, on_upload=self._on_upload)
        self.file_label = ft.Text("No file selected", color=MUTED)
        self.error = ft.Text(color=ft.Colors.RED_300, visible=False, selectable=True)
        self.progress = ft.ProgressBar(visible=False)
        self.choose_button = ft.OutlinedButton("Choose PDF", icon=ft.Icons.ATTACH_FILE,
                                               on_click=self._choose)
        self.upload_button = ft.FilledButton("Upload", icon=ft.Icons.CLOUD_UPLOAD, disabled=True,
                                             on_click=self._start_upload)

    def build(self) -> ft.Control:
        self._page.overlay.append(self.picker)
        drop = ft.Container(
            ft.Column([ft.Icon(ft.Icons.PICTURE_AS_PDF, size=40, color=ft.Colors.RED_300), self.file_label,
                       ft.Text(f"PDF only, up to {format_bytes(self._max_bytes)}.", size=12, color=MUTED)],
                      horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=32, border_radius=16, alignment=ft.alignment.center,
            border=ft.border.all(1.5, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)))
        return ft.Column(
            [page_header("Upload a resume", "Share a PDF with our expert reviewers."), drop,
             self.error, self.progress,
             ft.Row([self.choose_button, self.upload_button], spacing=12)],
            spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def dispose(self) -> None:
        self._discard_staged()
        if self.picker in self._page.overlay:
            self._page.overlay.remove(self.picker)

    # -- picking ----------------------------------------------------------
    def _choose(self, _e=None) -> None:
        self.picker.pick_files(dialog_title="Choose a PDF resume", allow_multiple=False,
                               file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["pdf"])

    def _on_picked(self, event: ft.FilePickerResultEvent) -> None:
        if not event.files:
            return
        chosen = event.files[0]
        problem = validate_pdf_choice(chosen.name, chosen.size or 0, self._max_bytes)
        self._set_error(problem)
        self._file = None if problem else chosen
        self.file_label.value = "No file selected" if problem else f"{chosen.name}  ·  {format_bytes(chosen.size)}"
        self.upload_button.disabled = bool(problem)
        self._page.update()

    # -- uploading --------------------------------------------------------
    def _start_upload(self, _e=None) -> None:
        if self._file is None:
            return
        self._set_busy(True)
        if self._page.web:
            self._staged = f"{uuid.uuid4().hex}_{safe_filename(self._file.name)}"
            try:
                url = self._page.get_upload_url(self._staged, 600)
            except Exception:
                logger.exception("Could not create upload URL")
                self._fail("Uploads are not available right now.")
                return
            self.picker.upload([ft.FilePickerUploadFile(name=self._file.name, upload_url=url)])
        else:
            self._forward_path(self._file.path, self._file.name)

    def _on_upload(self, event: ft.FilePickerUploadEvent) -> None:
        if event.error:
            logger.warning("Browser upload failed: %s", event.error)
            self._fail("The upload did not complete. Please try again.")
        elif event.progress is not None and event.progress >= 1.0 and self._staged:
            staged, self._staged = self._staged, None
            self._forward_path(os.path.join(self._upload_dir, staged), self._file.name if self._file else staged,
                               delete_after=True)
        elif event.progress is not None:
            self.progress.value = event.progress
            self.progress.update()

    def _forward_path(self, path: Optional[str], name: str, delete_after: bool = False) -> None:
        try:
            if not path:
                raise OSError("no path")
            real = os.path.realpath(path)
            if delete_after and os.path.commonpath([real, self._upload_dir]) != self._upload_dir:
                raise OSError("path outside upload dir")
            if os.path.getsize(real) > self._max_bytes:
                self._fail(f"That file is too large (limit {format_bytes(self._max_bytes)}).")
                return
            with open(real, "rb") as handle:
                content = handle.read()
            self._service.upload(name, content)
        except ApiError as exc:
            if not self._on_error(exc):
                self._fail(exc.message)
            return
        except OSError:
            logger.exception("Could not read the selected file")
            self._fail("We could not read that file. Please choose it again.")
            return
        finally:
            if delete_after:
                self._remove(path)
        notify(self._page, "Resume uploaded.")
        self._on_done()

    # -- helpers ----------------------------------------------------------
    def _discard_staged(self) -> None:
        if self._staged:
            self._remove(os.path.join(self._upload_dir, self._staged))
            self._staged = None

    @staticmethod
    def _remove(path: Optional[str]) -> None:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass

    def _set_error(self, text: str) -> None:
        self.error.value = text
        self.error.visible = bool(text)

    def _fail(self, text: str) -> None:
        self._set_error(text)
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self.progress.visible = busy
        self.progress.value = None if busy else 0
        self.upload_button.disabled = busy or self._file is None
        self.choose_button.disabled = busy
        self._page.update()

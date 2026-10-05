"""One resume list row, reused by the candidate and reviewer views."""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from features.resumes.models import Resume
from shared.components.panels import MUTED
from shared.utils.formatting import format_bytes, format_datetime


def resume_row(resume: Resume, *, on_download: Callable[[Resume], None],
               on_delete: Optional[Callable[[Resume], None]] = None,
               show_owner: bool = False) -> ft.Control:
    meta = f"{format_bytes(resume.file_size)}  ·  Uploaded {format_datetime(resume.created_date)}"
    lines = [ft.Text(resume.file_name, weight=ft.FontWeight.W_600, max_lines=1,
                     overflow=ft.TextOverflow.ELLIPSIS)]
    if show_owner:
        owner = resume.username or "unknown"
        if resume.email:
            owner += f"  ·  {resume.email}"
        lines.append(ft.Text(owner, size=13, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS))
        if resume.github:
            lines.append(ft.Text(resume.github, size=12, color=MUTED, selectable=True, max_lines=1,
                                 overflow=ft.TextOverflow.ELLIPSIS))
    lines.append(ft.Text(meta, size=12, color=MUTED))
    actions = [ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Download", on_click=lambda _e: on_download(resume))]
    if on_delete:
        actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete",
                                     icon_color=ft.Colors.RED_300, on_click=lambda _e: on_delete(resume)))
    return ft.Container(
        ft.Row([ft.Icon(ft.Icons.PICTURE_AS_PDF, color=ft.Colors.RED_300, size=30),
                ft.Column(lines, spacing=2, expand=True), *actions],
               vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        padding=ft.padding.symmetric(12, 16), border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
        border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)),
    )

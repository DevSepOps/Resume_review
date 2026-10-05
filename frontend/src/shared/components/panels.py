"""Small layout building blocks: page header, loading / error / empty states."""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

MUTED = ft.Colors.with_opacity(0.65, ft.Colors.ON_SURFACE)


def page_header(title: str, subtitle: str = "", actions: Optional[list] = None) -> ft.Control:
    heading = ft.Column(
        [ft.Text(title, size=26, weight=ft.FontWeight.W_700),
         ft.Text(subtitle, size=14, color=MUTED, visible=bool(subtitle))],
        spacing=2, expand=True)
    return ft.Row([heading, *(actions or [])], vertical_alignment=ft.CrossAxisAlignment.START)


def loading_panel(text: str = "Loading...") -> ft.Control:
    return ft.Container(
        ft.Column([ft.ProgressRing(width=28, height=28, stroke_width=3), ft.Text(text, color=MUTED)],
                  horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        alignment=ft.alignment.center, padding=48)


def error_panel(message: str, on_retry: Optional[Callable] = None) -> ft.Control:
    controls = [ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.RED_300, size=36),
                ft.Text(message, text_align=ft.TextAlign.CENTER, selectable=True)]
    if on_retry:
        controls.append(ft.OutlinedButton("Try again", icon=ft.Icons.REFRESH, on_click=on_retry))
    return ft.Container(ft.Column(controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                        alignment=ft.alignment.center, padding=48)


def empty_panel(icon: str, title: str, hint: str = "", action: Optional[ft.Control] = None) -> ft.Control:
    controls = [ft.Icon(icon, size=44, color=MUTED), ft.Text(title, size=17, weight=ft.FontWeight.W_600),
                ft.Text(hint, color=MUTED, text_align=ft.TextAlign.CENTER, visible=bool(hint))]
    if action:
        controls.append(action)
    return ft.Container(ft.Column(controls, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        alignment=ft.alignment.center, padding=48)

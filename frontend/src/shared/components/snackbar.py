"""User feedback via a real ft.SnackBar."""
from __future__ import annotations

import flet as ft


def notify(page: ft.Page, message: str, *, error: bool = False) -> None:
    page.open(
        ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
            behavior=ft.SnackBarBehavior.FLOATING,
            show_close_icon=True,
            duration=5000 if error else 3000,
        )
    )

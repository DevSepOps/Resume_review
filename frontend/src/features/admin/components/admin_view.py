"""Admin screens: user management and platform statistics."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import flet as ft

from features.admin.services.admin_service import ROLES, AdminService
from shared.components.panels import MUTED, empty_panel, error_panel, loading_panel, page_header
from shared.components.snackbar import notify
from shared.lib.api_client import ApiError
from shared.utils.formatting import format_datetime


class UsersView:
    def __init__(self, page: ft.Page, service: AdminService, current_user_id: Optional[int],
                 on_error: Callable[[ApiError], bool]) -> None:
        self._page = page
        self._service = service
        self._me = current_user_id
        self._on_error = on_error
        self.search = ft.TextField(label="Search users", prefix_icon=ft.Icons.SEARCH, expand=True,
                                   border_radius=10, on_submit=self.load)
        self.role_filter = ft.Dropdown(
            label="Role", width=160, value="all", border_radius=10,
            options=[ft.dropdown.Option("all", "All roles")] + [ft.dropdown.Option(r, r.capitalize()) for r in ROLES],
            on_change=self.load)
        self.body = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def build(self) -> ft.Control:
        self.body.controls = [loading_panel()]
        return ft.Column([page_header("Users", "Manage roles and access."),
                          ft.Row([self.search, self.role_filter], spacing=12), self.body],
                         expand=True, spacing=16)

    def load(self, _e=None) -> None:
        role = None if self.role_filter.value in (None, "all") else self.role_filter.value
        try:
            users = self._service.list_users(search=self.search.value or "", role=role)
        except ApiError as exc:
            if self._on_error(exc):
                return
            self.body.controls = [error_panel(exc.message, self.load)]
        else:
            self.body.controls = [self._row(u) for u in users] or [
                empty_panel(ft.Icons.PEOPLE_OUTLINE, "No users match", "Try a different search or role.")]
        self._page.update()

    def _row(self, user: Dict[str, Any]) -> ft.Control:
        uid = user.get("id")
        is_me = uid == self._me
        role = ft.Dropdown(
            value=user.get("role"), width=140, dense=True, border_radius=8, disabled=is_me,
            tooltip="You cannot change your own role" if is_me else "Change role",
            options=[ft.dropdown.Option(r, r.capitalize()) for r in ROLES],
            on_change=lambda e, i=uid, prev=user.get("role"): self._change_role(e, i, prev))
        active = ft.Switch(value=bool(user.get("is_active")), disabled=is_me,
                           tooltip="Active" if user.get("is_active") else "Deactivated",
                           on_change=lambda e, i=uid: self._toggle(e, i))
        info = ft.Column(
            [ft.Text(user.get("username", ""), weight=ft.FontWeight.W_600, max_lines=1,
                     overflow=ft.TextOverflow.ELLIPSIS),
             ft.Text(user.get("email", ""), size=12, color=MUTED, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
             ft.Text(f"Joined {format_datetime(user.get('created_date'))}", size=11, color=MUTED)],
            spacing=2, expand=True)
        return ft.Container(
            ft.Row([ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=32, color=MUTED), info, role,
                    ft.Column([ft.Text("Active", size=10, color=MUTED), active], spacing=0,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER)],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, wrap=False),
            padding=ft.padding.symmetric(10, 16), border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)))

    def _change_role(self, event: ft.ControlEvent, user_id: int, previous: Optional[str]) -> None:
        try:
            self._service.set_role(user_id, event.control.value)
        except ApiError as exc:
            event.control.value = previous
            if not self._on_error(exc):
                notify(self._page, exc.message, error=True)
            self._page.update()
            return
        notify(self._page, "Role updated.")
        self.load()

    def _toggle(self, event: ft.ControlEvent, user_id: int) -> None:
        try:
            self._service.toggle_activation(user_id)
        except ApiError as exc:
            event.control.value = not event.control.value
            if not self._on_error(exc):
                notify(self._page, exc.message, error=True)
            self._page.update()
            return
        notify(self._page, "Access updated.")
        self.load()


class StatsView:
    def __init__(self, page: ft.Page, service: AdminService, on_error: Callable[[ApiError], bool]) -> None:
        self._page = page
        self._service = service
        self._on_error = on_error
        self.body = ft.Column(spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)

    def build(self) -> ft.Control:
        self.body.controls = [loading_panel()]
        return ft.Column([page_header("Platform stats", "A snapshot of activity."), self.body],
                         expand=True, spacing=16)

    def load(self, _e=None) -> None:
        try:
            stats = self._service.stats()
        except ApiError as exc:
            if self._on_error(exc):
                return
            self.body.controls = [error_panel(exc.message, self.load)]
        else:
            by_role: Dict[str, int] = stats.get("users_by_role") or {}
            tiles: List[ft.Control] = [
                self._tile("Users", stats.get("total_users", 0), ft.Icons.PEOPLE),
                self._tile("Resumes", stats.get("total_resumes", 0), ft.Icons.DESCRIPTION)]
            tiles += [self._tile(r.capitalize() + "s", by_role.get(r, 0), ft.Icons.BADGE_OUTLINED) for r in ROLES]
            self.body.controls = [ft.ResponsiveRow(
                [ft.Container(t, col={"xs": 6, "md": 4, "lg": 3}) for t in tiles], run_spacing=12, spacing=12)]
        self._page.update()

    @staticmethod
    def _tile(label: str, value: Any, icon: str) -> ft.Control:
        return ft.Container(
            ft.Column([ft.Icon(icon, color=MUTED), ft.Text(str(value), size=32, weight=ft.FontWeight.W_700),
                       ft.Text(label, color=MUTED)], spacing=4),
            padding=20, border_radius=14, bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)))

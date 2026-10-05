"""Per-session application controller: wires services, applies route guards, builds views."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Optional

import flet as ft

from app import navigation as nav
from app.session import Session
from config.settings import Settings
from features.admin.components.admin_view import StatsView, UsersView
from features.admin.services.admin_service import AdminService
from features.auth.components.login_view import LoginView
from features.auth.services.auth_service import AuthService
from features.resumes.components.my_resumes_view import MyResumesView
from features.resumes.components.upload_view import UploadView
from features.resumes.services.resume_service import ResumeService
from features.review.components.review_view import ReviewView
from features.review.services.review_service import ReviewService
from shared.components.animated_nav import AnimatedNav, NavEntry
from shared.components.downloader import Downloader
from shared.components.snackbar import notify
from shared.lib.api_client import ApiClient, ApiError

logger = logging.getLogger(__name__)

BG = "#0B1020"
CONTENT_MAX = 960


class SessionApp:
    """Everything here belongs to exactly one browser session (one ``ft.Page``)."""

    def __init__(self, page: ft.Page, settings: Settings,
                 transport: Any = None) -> None:
        self.page = page
        self.settings = settings
        self.session = Session()
        self.api = ApiClient(settings.backend_url, settings.request_timeout, self.session.tokens,
                             transport=transport)
        self.auth = AuthService(self.api, self.session)
        self.resumes = ResumeService(self.api)
        self.review = ReviewService(self.api)
        self.admin = AdminService(self.api)
        self.downloader = Downloader(page, settings.downloads_dir)
        self._view: Optional[Any] = None
        self._nav: Optional[AnimatedNav] = None
        self._content_box: Optional[ft.Container] = None

    # -- bootstrap --------------------------------------------------------
    def start(self) -> None:
        page = self.page
        page.title = "Resume Review"
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
        page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
        page.bgcolor = BG
        page.padding = 0
        page.on_route_change = self._on_route_change
        page.on_resized = self._on_resized
        page.on_disconnect = self._on_disconnect
        page.on_close = self._on_close
        page.go(nav.normalize(page.route))

    # -- routing ----------------------------------------------------------
    def _on_route_change(self, _e: Any = None) -> None:
        action, target = nav.resolve(self.page.route, self.session)
        if action == "redirect":
            if nav.normalize(self.page.route) != target:
                self.page.go(target)
                return
        self._dispose_view()
        path = target or nav.LOGIN
        try:
            if path == nav.LOGIN:
                controls = [self._build_login()]
            else:
                controls = [self._build_shell(path)]
        except Exception:
            logger.exception("Failed to build route %s", path)
            controls = [ft.Container(ft.Text("Something went wrong. Please reload the page."), padding=32)]
        self.page.views.clear()
        self.page.views.append(ft.View(route=path, controls=controls, padding=0, bgcolor=BG))
        self.page.update()
        self._mount_view()

    def _dispose_view(self) -> None:
        view, self._view = self._view, None
        self._nav = None
        self._content_box = None
        for hook in ("stop", "dispose"):
            fn = getattr(view, hook, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    logger.exception("View %s() failed", hook)

    def _mount_view(self) -> None:
        view = self._view
        if view is None:
            return
        start = getattr(view, "start", None)
        if callable(start):
            start()
        load = getattr(view, "load", None)
        if callable(load):
            load()

    # -- views ------------------------------------------------------------
    def _build_login(self) -> ft.Control:
        view = LoginView(self.page, self.auth, self._on_authenticated)
        self._view = view
        return view.build()

    def _build_view(self, path: str) -> Any:
        err = self.handle_api_error
        if path == nav.RESUMES:
            return MyResumesView(self.page, self.resumes, self.downloader, err, lambda: self.page.go(nav.UPLOAD))
        if path == nav.UPLOAD:
            return UploadView(self.page, self.resumes, upload_dir=self.settings.upload_tmp_dir,
                              max_bytes=self.settings.max_upload_bytes, on_error=err,
                              on_done=lambda: self.page.go(nav.RESUMES))
        if path == nav.REVIEW:
            return ReviewView(self.page, self.review, self.downloader, err)
        if path == nav.ADMIN_USERS:
            return UsersView(self.page, self.admin, (self.session.user or {}).get("id"), err)
        return StatsView(self.page, self.admin, err)

    def _build_shell(self, path: str) -> ft.Control:
        view = self._build_view(path)
        self._view = view
        spec = nav.ROUTES[path]
        self._nav = AnimatedNav(nav.nav_entries_for(self.session.role), spec.nav_key,
                                self._on_nav_select, self.page.width)
        self._content_box = ft.Container(view.build(), expand=True, padding=self._content_padding())
        header = ft.Container(
            ft.Row([ft.Row([ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.INDIGO_200),
                            ft.Text("Resume Review", size=16, weight=ft.FontWeight.W_700)], spacing=8),
                    ft.Text(f"{self.session.username} · {self.session.role}", size=12,
                            color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE))],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(14, 20))
        footer = ft.Container(ft.Row([self._nav], alignment=ft.MainAxisAlignment.CENTER),
                              padding=ft.padding.only(bottom=16, top=8))
        return ft.Column([header, self._content_box, footer], expand=True, spacing=0)

    def _content_padding(self) -> ft.Padding:
        width = self.page.width or 1280
        side = max(16.0, (width - CONTENT_MAX) / 2)
        return ft.padding.symmetric(vertical=8, horizontal=side)

    # -- callbacks --------------------------------------------------------
    def _on_authenticated(self, _role: str) -> None:
        self.page.go(nav.HOME)

    def _on_nav_select(self, entry: NavEntry) -> None:
        if entry.route:
            self.page.go(entry.route)
            return
        self.auth.logout()
        self.page.go(nav.LOGIN)

    def handle_api_error(self, error: ApiError) -> bool:
        """Return True if the error ended the session (the user was sent to login)."""
        if error.kind != "session_expired":
            return False
        self.session.clear()
        notify(self.page, error.message, error=True)
        self.page.go(nav.LOGIN)
        return True

    def _on_resized(self, _e: Any = None) -> None:
        width, height = self.page.width or 1280, self.page.height or 800
        if isinstance(self._view, LoginView):
            self._view.on_resize(width, height)
        if self._nav is not None and self._content_box is not None:
            self._nav.set_page_width(width)
            self._content_box.padding = self._content_padding()
            self.page.update()

    def _on_disconnect(self, _e: Any = None) -> None:
        stop = getattr(self._view, "stop", None)
        if callable(stop):
            stop()

    def _on_close(self, _e: Any = None) -> None:
        self._dispose_view()
        self.session.clear()
        self.api.close()

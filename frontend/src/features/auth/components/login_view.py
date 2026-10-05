"""Login / register card on an animated particle background."""
from __future__ import annotations

import logging
from typing import Callable, Dict, Optional

import flet as ft

from features.auth import validators
from features.auth.services.auth_service import AuthService
from shared.components.animated_background import ParticleBackground
from shared.lib.api_client import ApiError

logger = logging.getLogger(__name__)

MODE_LOGIN = "login"
MODE_REGISTER = "register"


def _field(label: str, *, password: bool = False, hint: Optional[str] = None, **kw) -> ft.TextField:
    return ft.TextField(
        label=label, hint_text=hint, password=password, can_reveal_password=password,
        border_radius=10, border_width=1.5, text_size=14, content_padding=ft.padding.symmetric(12, 14),
        focused_border_color=ft.Colors.BLUE_400, **kw,
    )


class LoginView:
    def __init__(self, page: ft.Page, auth: AuthService,
                 on_authenticated: Callable[[str], None]) -> None:
        self._page = page
        self._auth = auth
        self._on_authenticated = on_authenticated
        self._mode = MODE_LOGIN
        self._busy = False
        self._info = ""

        self.background = ParticleBackground(width=page.width or 1280, height=page.height or 800)
        self.username = _field("Username", autofocus=True, on_submit=self._submit)
        self.email = _field("Email", keyboard_type=ft.KeyboardType.EMAIL, on_submit=self._submit)
        self.password = _field("Password", password=True, on_submit=self._submit)
        self.confirm = _field("Confirm password", password=True, on_submit=self._submit)
        self.github = _field("GitHub profile (optional)", hint="https://github.com/you", on_submit=self._submit)
        self._fields: Dict[str, ft.TextField] = {
            "username": self.username, "email": self.email, "password": self.password,
            "confirm_password": self.confirm, "github": self.github,
        }
        self.title = ft.Text(size=24, weight=ft.FontWeight.W_700)
        self.subtitle = ft.Text(size=13, color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE))
        self.message = ft.Text(size=13, visible=False, selectable=True)
        self.submit_button = ft.FilledButton(height=44, expand=True, on_click=self._submit)
        self.spinner = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False)
        self.toggle_button = ft.TextButton(on_click=self._toggle_mode)

    # -- lifecycle --------------------------------------------------------
    def build(self) -> ft.Control:
        self._render_mode()
        card = ft.Container(
            padding=24, border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(spread_radius=2, blur_radius=45, color=ft.Colors.with_opacity(0.45, ft.Colors.BLACK)),
            content=ft.Column(
                [self.title, self.subtitle, ft.Container(height=4), self.username, self.email,
                 self.password, self.confirm, self.github, self.message,
                 ft.Row([self.submit_button, self.spinner], spacing=12),
                 ft.Row([self.toggle_button], alignment=ft.MainAxisAlignment.CENTER)],
                spacing=12, tight=True),
        )
        centered = ft.Column(
            [ft.ResponsiveRow([ft.Container(card, col={"xs": 12, "sm": 9, "md": 6, "lg": 4, "xl": 3})],
                              alignment=ft.MainAxisAlignment.CENTER)],
            expand=True, alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        return ft.Stack([self.background, ft.Container(centered, padding=16, expand=True)], expand=True)

    def start(self) -> None:
        """Begin the animation (call after the view is on the page)."""
        self._page.run_task(self.background.run)

    def stop(self) -> None:
        self.background.stop()

    def on_resize(self, width: float, height: float) -> None:
        self.background.resize(width, height)

    # -- state ------------------------------------------------------------
    def _render_mode(self) -> None:
        register = self._mode == MODE_REGISTER
        self.title.value = "Create your account" if register else "Welcome back"
        self.subtitle.value = ("Upload your resume and get expert feedback." if register
                               else "Sign in to manage your resumes.")
        for name in ("email", "confirm_password", "github"):
            self._fields[name].visible = register
        self.submit_button.text = "Create account" if register else "Sign in"
        self.toggle_button.text = "Already have an account? Sign in" if register else "New here? Create an account"
        self.password.autofill_hints = ft.AutofillHint.NEW_PASSWORD if register else ft.AutofillHint.PASSWORD
        self._show_message(self._info, error=False)

    def _show_message(self, text: str, *, error: bool) -> None:
        self.message.value = text
        self.message.visible = bool(text)
        self.message.color = ft.Colors.RED_300 if error else ft.Colors.GREEN_300

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.submit_button.disabled = busy
        self.toggle_button.disabled = busy
        self.spinner.visible = busy
        self._page.update()

    def _toggle_mode(self, _e=None) -> None:
        self._mode = MODE_REGISTER if self._mode == MODE_LOGIN else MODE_LOGIN
        self._info = ""
        self._clear_errors()
        self._render_mode()
        self._page.update()

    def _clear_errors(self) -> None:
        for field in self._fields.values():
            field.error_text = None

    def _apply_errors(self, errors: Dict[str, str]) -> None:
        self._clear_errors()
        for name, text in errors.items():
            self._fields[name].error_text = text

    # -- actions ----------------------------------------------------------
    def _submit(self, _e=None) -> None:
        if self._busy:
            return
        self._info = ""
        self._show_message("", error=False)
        if self._mode == MODE_LOGIN:
            errors = validators.validate_login(self.username.value or "", self.password.value or "")
        else:
            errors = validators.validate_registration(
                self.username.value or "", self.email.value or "", self.password.value or "",
                self.confirm.value or "", self.github.value or "")
        self._apply_errors(errors)
        if errors:
            self._page.update()
            return
        self._set_busy(True)
        try:
            if self._mode == MODE_LOGIN:
                role = self._auth.login(self.username.value, self.password.value)
                self.password.value = ""
                self._on_authenticated(role)
                return
            self._auth.register(self.username.value, self.email.value, self.password.value,
                                self.confirm.value, self.github.value)
            self._mode = MODE_LOGIN
            self._info = "Account created. You can sign in now."
            self.password.value = ""
            self.confirm.value = ""
            self._render_mode()
        except ApiError as exc:
            self._show_message(exc.message, error=True)
        except Exception:
            logger.exception("Unexpected error during auth")
            self._show_message("Something went wrong. Please try again.", error=True)
        finally:
            if self._page.session_id:  # session may have been torn down
                self._set_busy(False)

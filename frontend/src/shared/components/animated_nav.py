"""Animated bottom navigation pill (adapted from the animated_nav prototype, Flet 0.28.3).

Hover (desktop): the icon lifts out and the label slides in. The active item is always shown
in that "lifted" state with a soft highlight, so touch devices (no hover) still see where they
are. Items are plain ``ft.Container(ink=True, on_click=...)``: ``ink`` makes Flet render an
InkWell, which is focusable and activates with Enter/Space; a ``tooltip`` doubles as the
accessible label. Items are supplied by the caller; this module imports nothing from features.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import flet as ft

MAX_WIDTH = 590
HEIGHT = 56
GUTTER = 32  # page margin kept free on narrow screens

_ICON_REST = ft.Offset(0, 0)
_ICON_LIFT = ft.Offset(0, -1)
_LABEL_REST = ft.Offset(0, 1)
_LABEL_SHOW = ft.Offset(0, 0)


@dataclass(frozen=True)
class NavEntry:
    """One navigation item. ``route`` navigates; entries without a route are actions (logout)."""

    key: str
    label: str
    icon: str
    route: Optional[str] = None


def nav_width(page_width: Optional[float]) -> float:
    if not page_width or page_width <= 0:
        return MAX_WIDTH
    return max(200.0, min(MAX_WIDTH, page_width - GUTTER))


class NavItem(ft.Container):
    def __init__(self, entry: NavEntry, active: bool, on_select: Callable[[NavEntry], None]) -> None:
        self.entry = entry
        self.active = active
        self._icon = ft.Icon(entry.icon, color=ft.Colors.WHITE, size=22,
                             offset=_ICON_REST, opacity=1,
                             animate_offset=ft.Animation(400, ft.AnimationCurve.DECELERATE),
                             animate_opacity=ft.Animation(250, ft.AnimationCurve.DECELERATE))
        self._label = ft.Text(entry.label, size=11, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER,
                              max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, no_wrap=True,
                              weight=ft.FontWeight.W_600, offset=_LABEL_REST, opacity=0,
                              animate_offset=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                              animate_opacity=ft.Animation(400, ft.AnimationCurve.DECELERATE))
        super().__init__(
            content=ft.Stack([ft.Container(self._label, alignment=ft.alignment.center),
                              ft.Container(self._icon, alignment=ft.alignment.center)]),
            expand=True, height=HEIGHT - 8, border_radius=14, ink=True,
            tooltip=entry.label,
            bgcolor=ft.Colors.with_opacity(0.22, ft.Colors.WHITE) if active else None,
            on_hover=self._on_hover,
            on_click=lambda _e: on_select(entry),
            animate=ft.Animation(250, ft.AnimationCurve.DECELERATE),
        )
        self._apply(active)

    def _apply(self, lifted: bool) -> None:
        self._icon.offset = _ICON_LIFT if lifted else _ICON_REST
        self._icon.opacity = 0 if lifted else 1
        self._label.offset = _LABEL_SHOW if lifted else _LABEL_REST
        self._label.opacity = 1 if lifted else 0

    def _on_hover(self, event: ft.ControlEvent) -> None:
        self._apply(event.data == "true" or self.active)
        self.update()


class AnimatedNav(ft.Container):
    """Gradient pill with the given entries; ``active_key`` marks the current location."""

    def __init__(
        self,
        entries: Sequence[NavEntry],
        active_key: Optional[str],
        on_select: Callable[[NavEntry], None],
        page_width: Optional[float] = None,
        gradient_colors: Sequence[str] = ("#6366F1", "#8B5CF6", "#EC4899"),
    ) -> None:
        self.items: List[NavItem] = [NavItem(e, e.key == active_key, on_select) for e in entries]
        super().__init__(
            content=ft.Row(self.items, spacing=2, alignment=ft.MainAxisAlignment.SPACE_AROUND),
            width=nav_width(page_width), height=HEIGHT, padding=ft.padding.symmetric(horizontal=6, vertical=4),
            border_radius=18,
            gradient=ft.LinearGradient(list(gradient_colors), begin=ft.alignment.center_left,
                                       end=ft.alignment.center_right),
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.with_opacity(0.35, ft.Colors.BLACK),
                                offset=ft.Offset(0, 8)),
        )

    def set_page_width(self, page_width: Optional[float]) -> None:
        self.width = nav_width(page_width)

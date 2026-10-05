"""Route table, guards and role-based navigation (app layer: may import features)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Tuple

import flet as ft

from app.session import ROLE_ADMIN, ROLE_CANDIDATE, ROLE_EXPERT, Session
from shared.components.animated_nav import NavEntry

LOGIN = "/login"
RESUMES = "/resumes"
UPLOAD = "/upload"
REVIEW = "/review"
ADMIN_USERS = "/admin/users"
ADMIN_STATS = "/admin/stats"
HOME = RESUMES

ANY_ROLE: FrozenSet[str] = frozenset({ROLE_CANDIDATE, ROLE_EXPERT, ROLE_ADMIN})
REVIEWERS: FrozenSet[str] = frozenset({ROLE_EXPERT, ROLE_ADMIN})
ADMINS: FrozenSet[str] = frozenset({ROLE_ADMIN})


@dataclass(frozen=True)
class Route:
    path: str
    roles: Optional[FrozenSet[str]]  # None = public
    nav_key: Optional[str] = None


ROUTES = {r.path: r for r in (
    Route(LOGIN, None),
    Route(RESUMES, ANY_ROLE, "resumes"),
    Route(UPLOAD, ANY_ROLE, "upload"),
    Route(REVIEW, REVIEWERS, "review"),
    Route(ADMIN_USERS, ADMINS, "users"),
    Route(ADMIN_STATS, ADMINS, "stats"),
)}


def normalize(route: Optional[str]) -> str:
    path = (route or "/").split("?")[0].split("#")[0].rstrip("/") or "/"
    return path


def resolve(route: Optional[str], session: Session) -> Tuple[str, Optional[str]]:
    """Apply guards. Returns ("show", path) or ("redirect", path)."""
    path = normalize(route)
    spec = ROUTES.get(path)
    if spec is None:
        return "redirect", HOME if session.is_authenticated else LOGIN
    if spec.roles is None:
        return ("redirect", HOME) if session.is_authenticated else ("show", path)
    if not session.is_authenticated:
        return "redirect", LOGIN
    if session.role not in spec.roles:
        return "redirect", HOME
    return "show", path


def nav_entries_for(role: Optional[str]) -> List[NavEntry]:
    entries = [NavEntry("resumes", "Resumes", ft.Icons.FOLDER_OPEN, RESUMES),
               NavEntry("upload", "Upload", ft.Icons.UPLOAD_FILE, UPLOAD)]
    if role in REVIEWERS:
        entries.append(NavEntry("review", "Review", ft.Icons.RATE_REVIEW, REVIEW))
    if role in ADMINS:
        entries += [NavEntry("users", "Users", ft.Icons.PEOPLE, ADMIN_USERS),
                    NavEntry("stats", "Stats", ft.Icons.INSIGHTS, ADMIN_STATS)]
    entries.append(NavEntry("logout", "Logout", ft.Icons.LOGOUT, None))
    return entries

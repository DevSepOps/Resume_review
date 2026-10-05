"""Client-side validation mirroring the API contract (section 4, Users). The backend stays authoritative."""
from __future__ import annotations

import re
from typing import Dict

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
GITHUB_PREFIX = "https://github.com/"

Errors = Dict[str, str]


def validate_username(value: str) -> str:
    if not 3 <= len(value) <= 50:
        return "Use 3 to 50 characters."
    if not USERNAME_RE.match(value):
        return "Only letters, numbers, dots, dashes and underscores."
    return ""


def validate_email(value: str) -> str:
    return "" if EMAIL_RE.match(value) and len(value) <= 254 else "Enter a valid email address."


def validate_password(value: str) -> str:
    size = len(value.encode("utf-8"))
    if size < 8:
        return "Use at least 8 characters."
    if size > 72:
        return "Use at most 72 bytes (shorter password)."
    return ""


def validate_github(value: str) -> str:
    if value and not (value.startswith(GITHUB_PREFIX) and len(value) > len(GITHUB_PREFIX)):
        return "Must be a https://github.com/ link."
    return ""


def validate_login(username: str, password: str) -> Errors:
    errors: Errors = {}
    if not username.strip():
        errors["username"] = "Enter your username."
    if not password:
        errors["password"] = "Enter your password."
    return errors


def validate_registration(
    username: str, email: str, password: str, confirm_password: str, github: str = ""
) -> Errors:
    checks = {
        "username": validate_username(username.strip()),
        "email": validate_email(email.strip()),
        "password": validate_password(password),
        "github": validate_github(github.strip()),
    }
    errors = {field: msg for field, msg in checks.items() if msg}
    if "password" not in errors and password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."
    return errors

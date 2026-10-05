import pytest
from sqlalchemy import select

from app.cmd.create_admin import main
from app.internal.adapters.db.models import UserModel
from app.internal.entities import Role


def users(container):
    with container.session_scope() as s:
        return [(u.username, u.role) for u in s.scalars(select(UserModel).order_by(UserModel.id))]


def test_creates_admin_then_is_idempotent(container, monkeypatch, capsys):
    monkeypatch.setenv("ADMIN_PASSWORD", "Password123")
    args = ["--username", "Boss", "--email", "boss@example.com"]
    assert main(args, container=container) == 0
    assert "Created" in capsys.readouterr().out
    assert main(args, container=container) == 0
    assert "Promoted" in capsys.readouterr().out
    assert users(container) == [("boss", Role.ADMIN)]


def test_promotes_existing_candidate(container, client, monkeypatch, capsys):
    client.post("/users/register", json={
        "username": "alice", "email": "alice@example.com",
        "password": "Password123", "confirm_password": "Password123"})
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    assert main(["--username", "alice", "--email", "alice@example.com"], container=container) == 0
    assert users(container) == [("alice", Role.ADMIN)]
    # promoted admin can log in with the original password
    assert client.post("/users/login", json={"username": "alice", "password": "Password123"}).json()["role"] == "admin"


def test_invalid_input_returns_error(container, monkeypatch, capsys):
    monkeypatch.setenv("ADMIN_PASSWORD", "short")
    assert main(["--username", "boss", "--email", "b@example.com"], container=container) == 1
    assert "error" in capsys.readouterr().err

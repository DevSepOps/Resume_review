"""Admin bootstrap CLI (idempotent).

    python -m app.cmd.create_admin --username alice --email alice@example.com

Password: ADMIN_PASSWORD env var, otherwise prompted. Only needed when creating.
Existing users matching username or email are promoted to admin (and re-activated).
"""

import argparse
import getpass
import os
import sys
from typing import Optional, Sequence

from app.api.http.dependencies import Container
from app.pkg.config import get_settings
from app.pkg.errors import DomainError
from app.pkg.logger import setup_logging


def _read_password() -> str:
    password = os.environ.get("ADMIN_PASSWORD")
    if password:
        return password
    first = getpass.getpass("Admin password: ")
    if first != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    return first


def main(argv: Optional[Sequence[str]] = None, container: Optional[Container] = None) -> int:
    parser = argparse.ArgumentParser(description="Create or promote an admin user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args(argv)

    settings = container.settings if container else get_settings()
    setup_logging(settings.LOG_LEVEL)
    container = container or Container(settings)
    try:
        with container.session_scope() as session:
            user, created = container.admin_service(session).ensure_admin(
                args.username, args.email, _read_password
            )
    except DomainError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return 1
    print(f"{'Created' if created else 'Promoted'} admin user '{user.username}' (id={user.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

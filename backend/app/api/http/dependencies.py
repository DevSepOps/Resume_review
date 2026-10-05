"""Composition root: the ONLY module in api/ that imports adapters.

A Container wires adapters into services. It is stored on `app.state.container`
and created lazily, so importing the app never needs a database.
"""

from contextlib import contextmanager
from typing import Iterator, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.internal.adapters.db import (
    SqlResumeRepository,
    SqlRevokedTokenRepository,
    SqlUserRepository,
    create_db_engine,
    create_session_factory,
)
from app.internal.adapters.security import BcryptHasher, JwtTokenIssuer
from app.internal.adapters.storage import LocalFileStorage
from app.internal.entities import User
from app.internal.services import AdminService, AuthService, ResumeService
from app.pkg.config import Settings
from app.pkg.errors import Forbidden, ServiceUnavailable, Unauthorized
from app.pkg.logger import get_logger

log = get_logger(__name__)


class Container:
    def __init__(
        self,
        settings: Settings,
        engine: Optional[Engine] = None,
        hasher: Optional[BcryptHasher] = None,
    ) -> None:
        self.settings = settings
        self._engine = engine
        self._session_factory: Optional[sessionmaker[Session]] = None
        self._storage: Optional[LocalFileStorage] = None
        self.hasher = hasher or BcryptHasher()
        self.tokens = JwtTokenIssuer(settings.JWT_SECRET_KEY)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_db_engine(self.settings)
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            self._session_factory = create_session_factory(self.engine)
        return self._session_factory

    @property
    def storage(self) -> LocalFileStorage:
        if self._storage is None:
            self._storage = LocalFileStorage(self.settings.UPLOAD_DIR)
        return self._storage

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()

    def auth_service(self, session: Session) -> AuthService:
        return AuthService(
            SqlUserRepository(session),
            SqlRevokedTokenRepository(session),
            self.hasher,
            self.tokens,
            self.settings.ACCESS_TOKEN_TTL_SECONDS,
            self.settings.REFRESH_TOKEN_TTL_SECONDS,
        )

    def resume_service(self, session: Session) -> ResumeService:
        return ResumeService(
            SqlResumeRepository(session), self.storage, self.settings.max_upload_bytes
        )

    def admin_service(self, session: Session) -> AdminService:
        return AdminService(
            SqlUserRepository(session), SqlResumeRepository(session), self.hasher
        )

    def check_database(self) -> None:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            log.error("readiness check failed", extra={"error": type(exc).__name__})
            raise ServiceUnavailable("Database unavailable") from exc


# ---- FastAPI dependencies ----

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_session(container: Container = Depends(get_container)) -> Iterator[Session]:
    with container.session_scope() as session:
        yield session


def get_auth_service(
    container: Container = Depends(get_container), session: Session = Depends(get_session)
) -> AuthService:
    return container.auth_service(session)


def get_resume_service(
    container: Container = Depends(get_container), session: Session = Depends(get_session)
) -> ResumeService:
    return container.resume_service(session)


def get_admin_service(
    container: Container = Depends(get_container), session: Session = Depends(get_session)
) -> AdminService:
    return container.admin_service(session)


def get_access_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    if credentials is None:
        raise Unauthorized("Not authenticated")
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_access_token),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    return auth.authenticate_access_token(token)


def require_expert(user: User = Depends(get_current_user)) -> User:
    if not user.can_review_resumes():
        raise Forbidden("Not enough permissions. Expert role required.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin():
        raise Forbidden("Not enough permissions. Admin role required.")
    return user

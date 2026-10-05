"""SQLAlchemy implementations of the repository ports (ORM <-> entity mapping)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.internal.adapters.db.models import ResumeModel, RevokedTokenModel, UserModel
from app.internal.entities import Resume, Role, TokenClaims, User
from app.pkg.errors import Conflict


def _utc(value: Optional[datetime]) -> Optional[datetime]:
    """SQLite returns naive datetimes; treat them as UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _to_user(m: UserModel) -> User:
    return User(
        id=m.id,
        username=m.username,
        email=m.email,
        password_hash=m.password,
        github=m.github,
        role=m.role,
        is_active=m.is_active,
        created_date=_utc(m.created_date),
        updated_date=_utc(m.updated_date),
    )


def _to_resume(m: ResumeModel) -> Resume:
    return Resume(
        id=m.id,
        user_id=m.user_id,
        storage_key=m.file_path,
        file_name=m.file_name,
        file_size=m.file_size,
        mime_type=m.mime_type,
        created_date=_utc(m.created_date),
        updated_date=_utc(m.updated_date),
    )


class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, user_id: int) -> Optional[User]:
        m = self._s.get(UserModel, user_id)
        return _to_user(m) if m else None

    def get_by_username(self, username: str) -> Optional[User]:
        m = self._s.scalar(select(UserModel).where(UserModel.username == username))
        return _to_user(m) if m else None

    def get_by_username_or_email(self, username: str, email: str) -> Optional[User]:
        m = self._s.scalar(
            select(UserModel).where(
                or_(UserModel.username == username, UserModel.email == email)
            )
        )
        return _to_user(m) if m else None

    def exists_username_or_email(self, username: str, email: str) -> bool:
        return self.get_by_username_or_email(username, email) is not None

    def add(self, user: User) -> User:
        m = UserModel(
            username=user.username,
            email=user.email,
            password=user.password_hash,
            github=user.github,
            role=user.role,
            is_active=user.is_active,
        )
        self._s.add(m)
        try:
            self._s.commit()
        except IntegrityError as exc:  # concurrent duplicate
            self._s.rollback()
            raise Conflict("Username or Email already exists") from exc
        self._s.refresh(m)
        return _to_user(m)

    def update(self, user: User) -> User:
        m = self._s.get(UserModel, user.id)
        m.role = user.role
        m.is_active = user.is_active
        m.github = user.github
        m.password = user.password_hash
        self._s.commit()
        self._s.refresh(m)
        return _to_user(m)

    def list_users(
        self,
        skip: int,
        limit: int,
        role: Optional[Role] = None,
        search: Optional[str] = None,
    ) -> list[User]:
        q = select(UserModel).order_by(UserModel.id)
        if role is not None:
            q = q.where(UserModel.role == role)
        if search:
            like = f"%{search.lower()}%"
            q = q.where(
                or_(
                    func.lower(UserModel.username).like(like),
                    func.lower(UserModel.email).like(like),
                )
            )
        return [_to_user(m) for m in self._s.scalars(q.offset(skip).limit(limit))]

    def count(self) -> int:
        return self._s.scalar(select(func.count(UserModel.id))) or 0

    def count_by_role(self) -> dict[Role, int]:
        rows = self._s.execute(
            select(UserModel.role, func.count(UserModel.id)).group_by(UserModel.role)
        ).all()
        return {role: n for role, n in rows}


class SqlResumeRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, resume: Resume) -> Resume:
        m = ResumeModel(
            user_id=resume.user_id,
            file_path=resume.storage_key,
            file_name=resume.file_name,
            file_size=resume.file_size,
            mime_type=resume.mime_type,
        )
        self._s.add(m)
        self._s.commit()
        self._s.refresh(m)
        return _to_resume(m)

    def get(self, resume_id: int) -> Optional[Resume]:
        m = self._s.get(ResumeModel, resume_id)
        return _to_resume(m) if m else None

    def list_by_user(self, user_id: int) -> list[Resume]:
        q = select(ResumeModel).where(ResumeModel.user_id == user_id).order_by(ResumeModel.id.desc())  # newest first
        return [_to_resume(m) for m in self._s.scalars(q)]

    def list_with_owner(self, skip: int, limit: int) -> list[tuple[Resume, User]]:
        q = (
            select(ResumeModel, UserModel)
            .join(UserModel, ResumeModel.user_id == UserModel.id)
            .order_by(ResumeModel.id.desc())  # newest first
            .offset(skip)
            .limit(limit)
        )
        return [(_to_resume(r), _to_user(u)) for r, u in self._s.execute(q).all()]

    def delete(self, resume_id: int) -> None:
        m = self._s.get(ResumeModel, resume_id)
        if m is not None:
            self._s.delete(m)
            self._s.commit()

    def count(self) -> int:
        return self._s.scalar(select(func.count(ResumeModel.id))) or 0


class SqlRevokedTokenRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def revoke(self, claims: TokenClaims) -> bool:
        if self.is_revoked(claims.jti):
            return False
        self._s.add(
            RevokedTokenModel(
                jti=claims.jti,
                user_id=claims.user_id,
                token_type=claims.type.value,
                expires_at=claims.exp,
            )
        )
        try:
            self._s.commit()
        except IntegrityError:  # lost a race with a concurrent revoke of the same jti
            self._s.rollback()
            return False
        return True

    def is_revoked(self, jti: str) -> bool:
        return (
            self._s.scalar(
                select(RevokedTokenModel.id).where(RevokedTokenModel.jti == jti)
            )
            is not None
        )

    def purge_expired(self, now: datetime) -> int:
        deleted = (
            self._s.query(RevokedTokenModel)
            .filter(RevokedTokenModel.expires_at < now)
            .delete(synchronize_session=False)
        )
        self._s.commit()
        return deleted

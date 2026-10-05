"""Admin use cases: user management, stats, admin bootstrap."""

from typing import Callable, Optional

from app.internal.entities import Role, User
from app.internal.ports import PasswordHasher, ResumeRepository, UserRepository
from app.internal.validators import validate_password, validate_username
from app.pkg.errors import NotFound, ValidationFailed


class AdminService:
    def __init__(
        self,
        users: UserRepository,
        resumes: ResumeRepository,
        hasher: PasswordHasher,
    ) -> None:
        self._users = users
        self._resumes = resumes
        self._hasher = hasher

    def list_users(
        self, skip: int, limit: int, role: Optional[Role] = None, search: Optional[str] = None
    ) -> list[User]:
        return self._users.list_users(skip, limit, role, search)

    def set_role(self, actor: User, user_id: int, role: Role) -> User:
        if user_id == actor.id:
            raise ValidationFailed("Cannot change your own role")
        user = self._get(user_id)
        user.role = role
        return self._users.update(user)

    def toggle_activation(self, actor: User, user_id: int) -> User:
        if user_id == actor.id:
            raise ValidationFailed("Cannot deactivate yourself")
        user = self._get(user_id)
        user.is_active = not user.is_active
        return self._users.update(user)

    def stats(self) -> dict:
        by_role = self._users.count_by_role()
        return {
            "total_users": self._users.count(),
            "total_resumes": self._resumes.count(),
            "users_by_role": {r.value: by_role.get(r, 0) for r in Role},
        }

    def ensure_admin(
        self, username: str, email: str, get_password: Callable[[], str]
    ) -> tuple[User, bool]:
        """Idempotent bootstrap used by the create_admin CLI.

        Promotes (and re-activates) an existing user matching username or email;
        otherwise creates one. Returns (user, created).
        """
        try:
            username = validate_username(username)
        except ValueError as exc:
            raise ValidationFailed(str(exc)) from exc
        email = email.strip().lower()
        user = self._users.get_by_username_or_email(username, email)
        if user is not None:
            user.role = Role.ADMIN
            user.is_active = True
            return self._users.update(user), False
        try:
            password = validate_password(get_password())
        except ValueError as exc:
            raise ValidationFailed(str(exc)) from exc
        user = User(
            username=username,
            email=email,
            password_hash=self._hasher.hash(password),
            role=Role.ADMIN,
        )
        return self._users.add(user), True

    def _get(self, user_id: int) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFound("User not found")
        return user

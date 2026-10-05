"""User entity and role rules. Pure domain: no framework imports."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from app.internal.entities.resume import Resume


class Role(str, Enum):
    CANDIDATE = "candidate"
    EXPERT = "expert"
    ADMIN = "admin"


@dataclass
class User:
    username: str
    email: str
    password_hash: str
    role: Role = Role.CANDIDATE
    github: Optional[str] = None
    is_active: bool = True
    id: Optional[int] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    def can_review_resumes(self) -> bool:
        return self.role in (Role.EXPERT, Role.ADMIN)

    def can_delete(self, resume: Resume) -> bool:
        return self.is_admin() or resume.user_id == self.id

    def can_download(self, resume: Resume) -> bool:
        return self.can_review_resumes() or resume.user_id == self.id

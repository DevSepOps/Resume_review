import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Boolean,
    func,
    DateTime,
    Enum,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from passlib.context import CryptContext

# from CV.models import Resume

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(enum.Enum):
    CANDIDATE = "candidate"
    EXPERT = "expert"
    ADMIN = "admin"


class UsersModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(250), nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String(250), nullable=False, unique=True)
    github = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CANDIDATE, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
    resumes = relationship("Resume", back_populates="user")

    def hash_password(self, plain_password: str) -> str:
        """Hashing password"""
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verifying password"""
        return pwd_context.verify(plain_password, self.password)

    def set_password(self, plain_text: str) -> None:
        """Setting password"""
        self.password = self.hash_password(plain_text)


# class TokenModel(Base):
#     __tablename__ = "tokens"

#     user_id = Column(Integer, ForeignKey("users.id"))
#     id = Column(Integer, autoincrement=True, primary_key=True)
#     token = Column(String, nullable=False)
#     created_date = Column(DateTime, server_default=func.now(), nullable=False)

#     user = relationship("UsersModel", uselist=False)

from sqlalchemy import ForeignKey, String, Integer, Column, DateTime, func
from sqlalchemy.orm import relationship

# from users.models import UsersModel
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    created_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(
        DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
    user = relationship("UsersModel", back_populates="resumes")

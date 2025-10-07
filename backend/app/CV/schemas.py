from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ResumeBase(BaseModel):
    file_name: str
    file_size: int


class ResumeCreate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    id: int
    user_id: int
    file_path: str
    mime_type: str
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class ExpertResumeResponse(ResumeResponse):
    username: str
    email: str
    github: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    message: str
    resume: ResumeResponse

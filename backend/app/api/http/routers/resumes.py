from typing import Iterator
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.api.http.dependencies import (
    Container,
    get_container,
    get_current_user,
    get_resume_service,
    require_expert,
)
from app.internal.dto import (
    ExpertResumeResponse,
    MessageResponse,
    ResumeResponse,
    UploadResponse,
)
from app.internal.entities import User
from app.internal.services import ResumeService
from app.pkg.errors import PayloadTooLarge

router = APIRouter(prefix="/resumes", tags=["resumes"])

CHUNK = 64 * 1024
MULTIPART_OVERHEAD = 64 * 1024  # allowance for form boundaries/headers


def _read_chunks(upload: UploadFile) -> Iterator[bytes]:
    while chunk := upload.file.read(CHUNK):
        yield chunk


@router.post("/upload", status_code=201, response_model=UploadResponse)
def upload_resume(
    request: Request,
    resume: UploadFile = File(...),
    user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
    container: Container = Depends(get_container),
):
    limit = container.settings.max_upload_bytes
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit + MULTIPART_OVERHEAD:
        raise PayloadTooLarge(f"File too large. Maximum {container.settings.MAX_UPLOAD_MB}MB allowed")
    saved = service.upload(user, resume.filename, _read_chunks(resume))
    return UploadResponse(
        message="Resume uploaded successfully",
        resume=ResumeResponse.model_validate(saved),
    )


@router.get("/my-resumes", response_model=list[ResumeResponse])
def my_resumes(
    user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return service.list_mine(user)


@router.get("/expert/all", response_model=list[ExpertResumeResponse])
def expert_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_expert),
    service: ResumeService = Depends(get_resume_service),
):
    rows = service.list_for_experts(user, skip, limit)
    return [
        ExpertResumeResponse(
            **ResumeResponse.model_validate(r).model_dump(),
            username=owner.username,
            email=owner.email,
            github=owner.github,
        )
        for r, owner in rows
    ]


@router.get("/download/{resume_id}")
def download_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    resume, chunks = service.download(user, resume_id)
    return StreamingResponse(
        chunks,
        media_type=resume.mime_type,
        headers={
            "Content-Length": str(resume.file_size),
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(resume.file_name)}",
        },
    )


@router.delete("/{resume_id}", response_model=MessageResponse)
def delete_resume(
    resume_id: int,
    user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    service.delete(user, resume_id)
    return MessageResponse(detail="Resume deleted successfully")

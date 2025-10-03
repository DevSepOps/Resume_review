from typing import List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import aiofiles
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.auth.jwt_auth import get_authenticated_user
from app.auth.role_auth import get_expert_user
from app.users.models import UsersModel, UserRole
from app.CV.models import Resume
from app.CV.schemas import ResumeUploadResponse, ResumeResponse, ExpertResumeResponse

router = APIRouter(prefix="/resumes", tags=["resumes"])

RESUMES_DIR = Path("uploads/resumes")
RESUMES_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    resume: UploadFile = File(...),
    current_user: UsersModel = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    if resume.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are allowed"
        )
    
    file_extension = Path(resume.filename).suffix
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    unique_filename = f"{current_user.id}_{timestamp}{file_extension}"
    file_path = RESUMES_DIR / unique_filename

    file_size = 0
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await resume.read(8192)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > 10 * 1024 * 1024:
                    await f.close()
                    if file_path.exists():
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=400,
                        detail="File size too large. Maximum 10MB allowed."
                    )
                await f.write(chunk)
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="File upload failed")

    db_resume = Resume(
        user_id=current_user.id,
        file_path=str(file_path),
        file_name=resume.filename,
        file_size=file_size,
        mime_type=resume.content_type
    )
    
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    return ResumeUploadResponse(
        message="Resume uploaded successfully",
        resume=ResumeResponse.from_orm(db_resume)
    )

@router.get("/download/{resume_id}")
async def download_resume(
    resume_id: int,
    current_user: UsersModel = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Permission for CV owner
    if current_user.role not in [UserRole.EXPERT, UserRole.ADMIN] and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this resume")
    
    if not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=resume.file_path,
        filename=resume.file_name,
        media_type=resume.mime_type or "application/pdf"
    )

@router.get("/my-resumes", response_model=List[ResumeResponse])
async def get_my_resumes(
    current_user: UsersModel = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    return resumes

@router.get("/expert/all", response_model=List[ExpertResumeResponse])
async def get_all_resumes_expert(
    current_user: UsersModel = Depends(get_expert_user),
    db: Session = Depends(get_db)
):
    """Getting all CV's for experts"""
    resumes = db.query(Resume).options(joinedload(Resume.user)).all()
    
    response = []
    for resume in resumes:
        response.append(ExpertResumeResponse(
            id=resume.id,
            user_id=resume.user_id,
            file_name=resume.file_name,
            file_size=resume.file_size,
            file_path=resume.file_path,
            mime_type=resume.mime_type,
            created_date=resume.created_date,
            updated_date=resume.updated_date,
            username=resume.user.username,
            email=resume.user.email,
            github=resume.user.github
        ))
    return response

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: UsersModel = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}

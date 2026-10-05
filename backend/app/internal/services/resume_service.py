"""Resume use cases: upload, list, download, delete, expert listing."""

from typing import Iterable, Iterator

from app.internal.entities import PDF_MIME_TYPE, Resume, User
from app.internal.ports import FileStorage, ResumeRepository
from app.internal.validators import sanitize_filename, validated_pdf_chunks
from app.pkg.errors import Forbidden, NotFound


class ResumeService:
    def __init__(
        self, resumes: ResumeRepository, storage: FileStorage, max_upload_bytes: int
    ) -> None:
        self._resumes = resumes
        self._storage = storage
        self._max_bytes = max_upload_bytes

    def upload(self, user: User, filename: str | None, chunks: Iterable[bytes]) -> Resume:
        # Validation (magic bytes, size) runs while the stream is written; on failure
        # the storage adapter removes the partial file.
        key, size = self._storage.save(validated_pdf_chunks(chunks, self._max_bytes))
        try:
            return self._resumes.add(
                Resume(
                    user_id=user.id,
                    storage_key=key,
                    file_name=sanitize_filename(filename),
                    file_size=size,
                    mime_type=PDF_MIME_TYPE,
                )
            )
        except Exception:
            self._storage.delete(key)  # do not orphan the file, then re-raise as-is
            raise

    def list_mine(self, user: User) -> list[Resume]:
        return self._resumes.list_by_user(user.id)

    def download(self, user: User, resume_id: int) -> tuple[Resume, Iterator[bytes]]:
        resume = self._get(resume_id)
        if not user.can_download(resume):
            raise Forbidden("Not authorized to access this resume")
        if not self._storage.exists(resume.storage_key):
            raise NotFound("File not found on server")
        return resume, self._storage.iter_chunks(resume.storage_key)

    def delete(self, user: User, resume_id: int) -> None:
        resume = self._get(resume_id)
        if not user.can_delete(resume):
            raise Forbidden("Not authorized to delete this resume")
        self._resumes.delete(resume.id)
        self._storage.delete(resume.storage_key)

    def list_for_experts(self, user: User, skip: int, limit: int) -> list[tuple[Resume, User]]:
        if not user.can_review_resumes():
            raise Forbidden("Not enough permissions. Expert role required.")
        return self._resumes.list_with_owner(skip, limit)

    def _get(self, resume_id: int) -> Resume:
        resume = self._resumes.get(resume_id)
        if resume is None:
            raise NotFound("Resume not found")
        return resume

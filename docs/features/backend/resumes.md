# Resumes (Backend Module Doc)

## 1. Purpose
Candidates upload PDF resumes; experts/admins review them.

## 2. Entities
`Resume(id, user_id, storage_key, file_name, file_size, mime_type, created_date, updated_date)`. `mime_type` is always `application/pdf`.
Rules live on `User`: owner or admin may delete; owner, expert or admin may download.

## 3. Services (Use Cases)
`ResumeService`: `upload(user, filename, chunks)`, `list_mine`, `download(user, id)`, `delete(user, id)`, `list_for_experts(user, skip, limit)`.
Upload streams the body through `validated_pdf_chunks` into `FileStorage.save`; the DB row is added afterwards and the file is removed if that fails.

## 4. Ports
`ResumeRepository`, `FileStorage` (`save(chunks) -> (key, size)`, `exists`, `iter_chunks`, `delete`).

## 5. Adapters
`SqlResumeRepository` (table `resumes`, column `file_path` stores the storage key), `LocalFileStorage` (`<uuid4>.pdf` under `UPLOAD_DIR`,
partial file removed on any error, keys reduced to their basename).

## 6. API Endpoints
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/resumes/upload` | Bearer | multipart field `resume`; 201 `{message, resume}`; 400 not a PDF/empty; 413 too large |
| GET | `/resumes/my-resumes` | Bearer | own resumes |
| GET | `/resumes/download/{id}` | Bearer | owner/expert/admin; 403 otherwise; 404 if missing |
| DELETE | `/resumes/{id}` | Bearer | owner/admin; 403 otherwise |
| GET | `/resumes/expert/all` | expert/admin | `?skip=0&limit=50` (1-200), joined with owner username/email/github |

Responses never contain the storage path or key.

## 7. Validation Rules
File must start with `%PDF-` (client `Content-Type` is ignored); size <= `MAX_UPLOAD_MB` (default 10) checked while streaming
(plus an early `Content-Length` check) -> 413; file name sanitized (basename, control chars removed, <= 255 chars).
Note: Starlette spools the multipart body before the handler runs, so the proxy should also cap request body size.

## 8. Security Model
Server-generated file names (no user input in paths), role checks in services via entity rules, files served as `attachment`.

## 9. Testing Strategy
`tests/unit/test_resume_service.py` (fakes), `tests/integration/test_api.py` (magic bytes, 413 not 500, permissions, pagination, cleanup).

## 10. Future Improvements
Object storage adapter (S3) behind `FileStorage`, virus scanning, resume versions.

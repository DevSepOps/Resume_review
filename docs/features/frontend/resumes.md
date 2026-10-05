# Resumes: list, upload, download, delete (Frontend Feature Doc)

## 1. Overview
Candidates (and any role) manage their own PDFs: list, upload, download, delete.

## 2. UI/UX Flow
- `/resumes`: cards with file name, size ("2.0 KB"), "Uploaded 12 Mar 2026, 14:05" (from `created_date`), download and delete icons. Empty state with CTA; error state with "Try again".
- Delete asks for confirmation in a modal dialog.
- `/upload`: choose PDF -> client checks (.pdf, non-empty, <= `MAX_UPLOAD_MB`) -> Upload -> progress bar -> snackbar -> `/resumes`.
- Download: click -> dialog "Your file is ready" with an **Open PDF** button.

## 3. Data Flow
Upload (web): `FilePicker.pick_files` -> `page.get_upload_url(<uuid>_<safe name>, 600)` -> `FilePicker.upload` (browser PUTs to Flet into `UPLOAD_TMP_DIR`) -> `on_upload` progress 1.0 -> read file server-side -> `POST /resumes/upload` multipart `resume` -> delete temp file (always).
Upload (desktop): file path used directly.
Download: `GET /resumes/download/{id}` server-side -> bytes.

## 4. Components
`my_resumes_view.py`, `upload_view.py`, `resume_row.py`; shared `downloader.py`, `panels.py`, `snackbar.py`.

## 5. Services/API
`ResumeService`: `list_mine` (`GET /resumes/my-resumes`), `upload`, `delete` (`DELETE /resumes/{id}`), `download`.

## 6. Hooks
`view.build()` then `view.load()` after mount; `UploadView.dispose()` removes the picker and any staged temp file.

## 7. State Logic
`UploadView`: `_file`, `_staged` (temp name), busy flag. `MyResumesView`: body column replaced per state (loading/list/empty/error).

## 8. Edge Cases
Non-PDF / empty / too large (client and backend 400/413 mapped); upload error event -> generic message; session expiry mid-action -> redirect to login; malformed backend payload -> friendly error.

## 9. Security Considerations
**Download approach and its limitation.** An authenticated PDF cannot be linked directly from the browser (the browser has no token). The server fetches the bytes, writes them to `assets/downloads/<uuid4 hex>/<safe name>` and offers that URL.
The URL is a **capability link**: anyone who obtains it can fetch the file for 120 seconds, then the file is deleted (timer; the directory is also purged on startup). 128-bit random token, not guessable or listable.
Not suitable for highly sensitive documents on untrusted networks; use HTTPS (proxy). Desktop mode uses `FilePicker.save_file` instead. A popup-blocker-safe "Open PDF" button (a real user click) is used instead of `launch_url`.
Uploads use uuid-prefixed sanitized names, `realpath` containment check, 0700 temp dir, and deletion in `finally`.

## 10. Testing Strategy
`test_services.py`, `test_views.py`, `test_session_app.py` (staged upload forwarding and deletion), `test_components.py` (download staging/purge).

## 11. Future Improvements
Streaming large downloads, one-time-use tokens, upload drag-and-drop, preview.

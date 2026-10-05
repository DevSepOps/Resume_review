# Review (Frontend Feature Doc)

## 1. Overview
Experts and admins see every uploaded resume with owner username, email and GitHub, and can download.

## 2. UI/UX Flow
`/review`: list of cards (owner info shown), "Load more" when a page of 50 is full, empty and error states.

## 3. Data Flow
`ReviewView.load` -> `ReviewService.list_all(skip, limit)` -> `GET /resumes/expert/all?skip&limit` (limit clamped to 1..200). Download as in the resumes doc.

## 4. Components
`features/review/components/review_view.py`; reuses `resumes.components.resume_row` (`show_owner=True`).

## 5. Services/API
`ReviewService.list_all`, `ReviewService.download`.

## 6. Hooks
`build()` then `load()`.

## 7. State Logic
`_resumes` accumulates pages; `_more` true when the last page was full.

## 8. Edge Cases
403 for a candidate (also blocked by the route guard) -> friendly message; empty list; session expiry -> login.

## 9. Security Considerations
Backend enforces expert/admin; the UI guard is cosmetic. GitHub text is rendered as text (not HTML).

## 10. Testing Strategy
`test_views.py::test_review_view_paginates`, `test_services.py::test_review_list_*`, guards in `test_navigation.py`.

## 11. Future Improvements
Server-side search/filter, review comments (needs backend support).

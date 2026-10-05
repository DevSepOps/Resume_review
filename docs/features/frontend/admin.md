# Admin (Frontend Feature Doc)

## 1. Overview
Admins manage users and see platform statistics.

## 2. UI/UX Flow
- `/admin/users`: search box (Enter), role filter, rows with role dropdown and an Active switch. The admin's own row is disabled (backend also forbids self role change / self deactivation).
- `/admin/stats`: tiles for total users, total resumes, users per role.

## 3. Data Flow
`GET /admin/users?skip&limit&search&role`, `PATCH /admin/users/{id}/role {role}`, `PATCH /admin/users/{id}/activation`, `GET /admin/stats`. After a change the list is reloaded; on error the control reverts and a snackbar explains.

## 4. Components
`features/admin/components/admin_view.py`: `UsersView`, `StatsView`.

## 5. Services/API
`AdminService`: `list_users`, `set_role` (validates role), `toggle_activation`, `stats`.

## 6. Hooks
`build()` then `load()`.

## 7. State Logic
Filters live in the controls; no cached state.

## 8. Edge Cases
No matches; 403/409 from the backend; stale list after concurrent edits (reload after every change); first 100 users only (no pagination yet).

## 9. Security Considerations
Route guard + backend enforcement (`admin` only). Role values validated client-side against the allowed set before sending.

## 10. Testing Strategy
`test_views.py` (self-protection, revert on error, stats tiles), `test_services.py::test_admin_service_calls`.

## 11. Future Improvements
User pagination, confirmation before deactivating, audit trail view.

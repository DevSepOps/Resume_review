# Admin (Backend Module Doc)

## 1. Purpose
User management, platform statistics and the admin bootstrap CLI.

## 2. Entities
`User`, `Role`. `User.is_admin()` gates every `/admin/*` route.

## 3. Services (Use Cases)
`AdminService`: `list_users(skip, limit, role, search)`, `set_role(actor, id, role)` (not self), `toggle_activation(actor, id)` (not self),
`stats()`, `ensure_admin(username, email, get_password)` (CLI).

## 4. Ports
`UserRepository`, `ResumeRepository`, `PasswordHasher`.

## 5. Adapters
`SqlUserRepository`, `SqlResumeRepository`, `BcryptHasher`.

## 6. API Endpoints
| Method | Path | Result |
|---|---|---|
| GET | `/admin/users?skip&limit&role&search` | `[UserResponse]` (limit 1-1000, search is case-insensitive on username/email) |
| PATCH | `/admin/users/{id}/role` | `{role}` -> `UserResponse`; 400 own role; 404 |
| PATCH | `/admin/users/{id}/activation` | toggles `is_active`; 400 self |
| GET | `/admin/stats` | `{total_users, total_resumes, users_by_role:{candidate,expert,admin}}` (zero-filled) |

The old unauthenticated `/admin/make-admin/{id}` endpoint no longer exists.

CLI: `python -m app.cmd.create_admin --username <u> --email <e>` (password from `ADMIN_PASSWORD` or prompt; only asked when creating).
Idempotent: an existing user matching username or email is promoted to admin and re-activated, otherwise a new admin is created.

## 7. Validation Rules
Same username/password rules as registration are applied to the CLI input. `role` must be one of candidate|expert|admin.

## 8. Security Model
All routes require a valid access token of an active admin (403 otherwise). Admin creation is only possible with shell access to the backend.

## 9. Testing Strategy
`tests/unit/test_admin_service.py`, `tests/integration/test_api.py` (admin section), `tests/integration/test_create_admin.py`.

## 10. Future Improvements
Audit log of role/activation changes, hard delete of users with their resumes.

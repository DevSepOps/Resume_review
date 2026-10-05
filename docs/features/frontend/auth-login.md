# Auth: Login and Registration (Frontend Feature Doc)

## 1. Overview
Single card on an animated particle background. Two modes on the same card: **Sign in** (username + password) and
**Create account** (username, email, password, confirm, optional GitHub). Registered users are always `candidate`.

## 2. UI/UX Flow
1. `/login` shows "Welcome back". Enter submits from any field; the button is disabled with a spinner while the request runs.
2. "New here? Create an account" swaps fields in place (no navigation). Success returns to Sign in with "Account created. You can sign in now."
3. Success on sign in -> `/resumes`. Failure -> inline message under the fields (never a dialog or traceback).
4. Particles: 24 glowing dots twinkle; paused when leaving the route or when the client disconnects.

## 3. Data Flow
`LoginView` -> `AuthService.login` -> `ApiClient POST /users/login` (auth=False) -> tokens into the session `TokenPair`,
role into `Session`, then `GET /users/me` for the display name. Register: `POST /users/register`. Logout: `POST /users/logout`
with the refresh token, then local clear (always, even if the call fails).

## 4. Components
- `features/auth/components/login_view.py` `LoginView` (card, modes, submit)
- `shared/components/animated_background.py` `ParticleBackground` (single `update()` per 0.3 s tick)

## 5. Services/API
`features/auth/services/auth_service.py`: `login`, `register`, `logout`. Backend: `/users/login`, `/users/register`, `/users/me`, `/users/logout`.

## 6. Hooks
None (Flet has no hooks). Lifecycle: `build()` -> `start()` (`page.run_task(background.run)`) -> `stop()` (router, on route change/disconnect).

## 7. State Logic
`LoginView._mode` (login|register), `_busy`, `_info`. Tokens/role/user only in `app.session.Session`. Resize re-randomises particle positions.

## 8. Edge Cases
Double submit while busy is ignored; wrong password -> backend message; backend down -> "Cannot reach the server"; slow backend ->
timeout message after `REQUEST_TIMEOUT`; password > 72 bytes rejected client-side (bytes, not characters); inactive user -> 401 message from backend.

## 9. Security Considerations
Tokens never reach the browser; password fields cleared after use; username lower-cased before login; no credentials in logs; no rate limiting in the UI (backend responsibility; 429 is mapped to a friendly message).

## 10. Testing Strategy
`tests/unit/test_validators.py`, `test_services.py` (login/register/logout), `test_session_app.py` (login flow, inline errors, register toggle, animation stop, session isolation).

## 11. Future Improvements
Password strength meter, "reduce motion" switch for the particles, rate-limit hints from `Retry-After`.

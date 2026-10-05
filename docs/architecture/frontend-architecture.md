# Frontend Architecture

Flet 0.28.3 (Python) web app, served by Flet's FastAPI/uvicorn server on port 8001. The browser is a thin
Flutter-web client; **all Python code, tokens and backend calls run server-side** inside the Flet process.
Contract with the backend and infrastructure: [contracts.md](contracts.md).

## Layout

```
frontend/src/
  main.py                  entry: load config, ft.app(...); per-session handler factory
  app/                     composition: session state, route table + guards, SessionApp controller
    session.py             Session (tokens, user, role)           -- one per browser session
    navigation.py          routes, role guards, role-based nav entries
    router.py              SessionApp: wires services, builds views, handles route changes
  config/settings.py       typed env parsing (contract section 3), fails fast
  shared/                  generic building blocks; NEVER imports features/ or app/
    lib/api_client.py      httpx client: timeout, bearer, refresh-on-401, error mapping -> ApiError
    components/            animated_nav, animated_background, downloader, panels, snackbar
    utils/formatting.py    bytes/dates/safe_filename
  features/<name>/{components,services,validators.py,models.py}
    auth | resumes | review | admin
  assets/                  icons, manifest (served by Flet); assets/downloads/ = short-lived files
frontend/tests/unit/       pytest suite
```

Dependency rules (checked by review, not tooling):
`app -> features -> shared`; `shared` imports nothing above it; components never call HTTP directly - they use
their feature's `services/`; services only use `shared.lib.api_client`. One documented cross-feature edge:
`review` reuses `resumes.models` / `resumes.components.resume_row`.

## Per-session isolation

Flet runs the `target` once per browser session. `main.py` builds `make_session_handler(settings)`; the returned
`main(page)` creates a **new `SessionApp`** (new `Session`, `TokenPair`, `ApiClient`, services, `Downloader`, views).
The only process-wide object is the immutable `Settings` dataclass. There are no module-level mutable singletons, so
sessions cannot see each other's tokens or controls (covered by `test_two_sessions_do_not_share_state`).

## Security model

- Tokens live only in the server-side `TokenPair` (never `client_storage`, never sent to the browser, never logged).
- Refresh tokens rotate; refresh is serialised with a lock and retried once. If refresh fails the session is cleared
  and the user is sent to `/login`.
- Errors are mapped to friendly text; 5xx details and tracebacks are never displayed.
- Uploads: browser -> Flet via signed URL (`FLET_SECRET_KEY`), uuid-prefixed sanitized name inside `UPLOAD_TMP_DIR`
  (mode 0700), path re-validated with `realpath`, forwarded to the backend, temp file always deleted.
- Downloads: see [features/frontend/resumes.md](../features/frontend/resumes.md) (capability URL, 120 s TTL).
- Client-side validation mirrors the contract but the backend stays authoritative.
- The container runs as uid 10001, no hot reload, no desktop client.

## Routing and guards

`SessionApp._on_route_change` -> `navigation.resolve(route, session)` -> `show` or `redirect`.
Unauthenticated -> `/login`; authenticated on `/login` or unknown -> `/resumes`; wrong role -> `/resumes`.
Each navigation tears down the previous view (`stop()` / `dispose()`), builds a fresh `ft.View`, then calls the new
view's `start()` / `load()` after it is on the page.

| Route | Roles | View |
|-------|-------|------|
| `/login` | public | `LoginView` (sign in / register) |
| `/resumes` | all | `MyResumesView` |
| `/upload` | all | `UploadView` |
| `/review` | expert, admin | `ReviewView` |
| `/admin/users` | admin | `UsersView` |
| `/admin/stats` | admin | `StatsView` |

## Runtime configuration

See [runbook](../runbooks/frontend/frontend-app.md). Web server: `ft.app(view=None, host, port, assets_dir, upload_dir)`;
`view=None` makes Flet serve only (no browser/desktop launch); `FLET_FORCE_WEB_SERVER=true` is also set in the image.
`MAX_UPLOAD_MB` (optional, default 10) is a frontend addition for client-side checks and `FLET_MAX_UPLOAD_SIZE`.
`FLET_OPEN_BROWSER=true` opens a browser (local dev only).

## Known limitations

- Behind a reverse proxy Flet needs WebSocket upgrade on `/ws` and the same host for assets/downloads.
- Flet keeps sessions in memory: scale by sticky sessions (swarm/k8s) or a single replica.
- Hover/keyboard/touch behaviour of the animated nav is implemented per Flet docs but has only been verified by unit
  tests, not in a real browser.

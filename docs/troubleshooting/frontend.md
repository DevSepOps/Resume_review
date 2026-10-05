# Troubleshooting — Frontend

| Symptom | Cause | Fix |
|---------|-------|-----|
| Container exits immediately, log "FLET_SECRET_KEY is required" | Secret not provided | Set `FLET_SECRET_KEY` (`openssl rand -hex 32`) |
| Container exits with "Configuration error: ..." | Invalid `FLET_PORT`, `REQUEST_TIMEOUT`, `BACKEND_URL` (must start with http/https) | Fix the variable named in the message |
| Page loads but stays blank / grey, console shows WebSocket failure | Proxy not forwarding `/ws` upgrades | Enable WebSocket on the proxy; same host for `/` and `/ws` |
| Login says "Cannot reach the server" | `BACKEND_URL` wrong or backend down (the Flet server calls it, not the browser) | From the frontend container: `python -c "import urllib.request;print(urllib.request.urlopen('$BACKEND_URL/health').read())"` |
| "The server took too long to respond" | Backend slower than `REQUEST_TIMEOUT` | Check backend; raise `REQUEST_TIMEOUT` |
| Upload does nothing / "Uploads are not available right now" | Missing `FLET_SECRET_KEY` or `UPLOAD_TMP_DIR` not writable | Set the key; `ls -ld $UPLOAD_TMP_DIR` must be owned by uid 10001 |
| Upload stuck at 100% / "could not read that file" | Temp dir full or different from what Flet was started with | Check disk and that `UPLOAD_TMP_DIR` is unchanged after start |
| "That file is too large" | Above `MAX_UPLOAD_MB` (frontend) or backend `MAX_UPLOAD_MB` | Keep both values equal |
| Download dialog link shows the app instead of the PDF (404 fallback) | Link expired (120 s) or `assets/downloads` not writable | Click download again; check permissions on `/app/assets/downloads` |
| Signed out unexpectedly | Container restarted, or refresh token expired/revoked | Sign in again; sessions are in memory |
| Different users see each other's data | Must not happen (per-session `SessionApp`); if suspected, check for custom code using module globals | `pytest tests/unit/test_session_app.py` |
| Particles/nav animations laggy | Low-end device with CanvasKit | Reduce `DEFAULT_PARTICLES` in `animated_background.py` |
| Behind proxy, redirects/assets 404 | App served under a path prefix | Serve at the domain root (prefix mounting is not configured) |

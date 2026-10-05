# Backend Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Container exits: `ValidationError ... DATABASE_URL` / `JWT_SECRET_KEY` | Required settings missing | Set both env vars (contract section 2) |
| Exit with `JWT_SECRET_KEY must be at least 32 characters` | `ENVIRONMENT=production` with a short secret | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| Exit with `CORS_ORIGINS must list exact origins` | `*` used | List origins, e.g. `https://app.example.com` |
| Entrypoint: `database ... not reachable` | DB not up / wrong host in `DATABASE_URL` / network | Check `DATABASE_URL`, DB container health; raise `DB_WAIT_TIMEOUT` |
| `/ready` returns 503, `/health` 200 | DB unreachable or credentials wrong | Check DB and `DATABASE_URL`; logs show `readiness check failed` |
| `alembic upgrade` fails with `type "userrole" already exists` | Re-upgrading after `downgrade base`: the initial revision's downgrade does not drop the enum | `psql -c 'DROP TYPE userrole'` then upgrade again |
| `PermissionError` writing to `/app/data/uploads` | Volume not writable by uid 10001 | `chown 10001:10001` on the volume / use a named volume |
| Upload returns 413 | File larger than `MAX_UPLOAD_MB` (or proxy limit) | Raise `MAX_UPLOAD_MB`; also raise the proxy body limit |
| Upload returns 400 "Only PDF files are allowed" | File does not start with `%PDF-` (content type is ignored) | Upload a real PDF |
| 401 "Token has been revoked" right after refresh | The refresh token was already used (rotation) | Always store the newest refresh token; retry login |
| 401 for every request after deploy | `JWT_SECRET_KEY` changed or differs between replicas | Use one shared secret |
| Download 404 "File not found on server" | Uploads volume lost/not shared; legacy rows pointing to old paths | Restore the volume; rows from the old version reference files that were never on a persistent volume |
| Cannot log in with a password longer than 72 bytes | bcrypt limit; such passwords are rejected | Use a shorter password |
| 500 "Internal server error" | Unhandled exception | Find the JSON log line `unhandled error` (same time/path) for the traceback |
| `Admin role required` for the first user | No admin yet | `python -m app.cmd.create_admin --username ... --email ...` |

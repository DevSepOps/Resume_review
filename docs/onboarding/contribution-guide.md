# Contribution Guide

## Ground rules

1. **Contract first.** If a change touches an API, an environment variable, a port or a service name,
   update [contracts.md](../architecture/contracts.md) first, then the backend, frontend, Compose, Swarm and Helm together.
2. **Backend layering (Lich).** `entities` import nothing external. `services` use only entities, ports,
   dto, validators and `pkg.errors`. Only `api/http/dependencies.py` (the composition root) imports adapters.
   This check must return nothing:
   ```bash
   grep -rnE "^(from|import) .*(sqlalchemy|fastapi|adapters|jwt|bcrypt)" backend/app/internal/{entities,services,ports,dto,validators}
   ```
3. **Frontend layering.** `shared/` never imports `features/`. Views call services, and services call `shared/lib/api_client.py`.
   No module-level mutable state, because every browser session gets its own objects.
4. **Tests with every change.** Unit tests for entities, services and validators; integration tests for API flows.
   Write regression tests for bugs. Name tests `test_<thing>_should_<behaviour>`.
5. **Docs with every change.** Update the matching file under `docs/` (features, runbooks, troubleshooting)
   and append an entry to `agentlog.md` (WHEN · WHAT · WHY).
6. **No secrets in git.** Use `.env`, Ansible Vault, Kubernetes Secrets or `existingSecret`. Commit only `*.example` files.

## Pull requests

- Branch from `dev` and open the PR against `dev`. `main` is release-only.
- CI must pass: backend and frontend tests, image build, `helm lint`/`template`/`kubeconform`,
  `terraform fmt`/`validate` and `ansible-lint`.
- Releases are git tags `vX.Y.Z`. CI pushes images tagged `vX.Y.Z`, and `deploy.yml` deploys them after approval.

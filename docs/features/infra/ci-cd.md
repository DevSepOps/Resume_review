# CI/CD (GitHub Actions)

## 1. Purpose
Test, build, publish and deploy backend and frontend images, and statically validate Helm and infra code.

## 2. Architecture
| Workflow | Trigger | Jobs |
|----------|---------|------|
| `backend.yml` | push main/dev, tags `v*`, PR (paths `backend/**`, `deployments/docker/backend/**`) | `test` (Python 3.12, `pip install -r requirements-dev.txt`, `pytest --cov --cov-report=xml`, coverage artifact) -> `build` |
| `frontend.yml` | same with `frontend/**` | same |
| `helm.yml` | `deployments/helm/**` | `helm lint --strict`, `helm template | kubeconform` (pinned, checksum-verified) |
| `infra.yml` | `infra/**` | terraform `fmt -check`, `init -backend=false`, `validate` for `dev` and `dev-azure` (pinned 1.9.8); `ansible-playbook --syntax-check`, `ansible-lint` |
| `deploy.yml` | tag `v*`, manual dispatch | `wait-for-images` -> `deploy` (environment `production`, SSH) |

Image build: `docker/metadata-action` tags `sha-<7>` always, `latest` on the default branch, `vX.Y.Z` on tags, for `docker.io/sepehrmdn/resume-review-{backend,frontend}`. Pull requests build the image but do not log in or push (works for forks). Layer cache: `type=gha`.

## 3. Inputs (Variables)
Repository secrets: `DOCKER_USERNAME`, `DOCKER_PASSWORD` (Docker Hub access token, not the password). Environment `production` secrets: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`. Manual deploy input: `ref` (`vX.Y.Z` or `sha-<7>`).

## 4. Outputs
Images on Docker Hub, coverage artifacts (14 days), deploy log.

## 5. Security Rules
- Top-level `permissions: contents: read`; concurrency groups cancel superseded PR runs; deploys never run in parallel.
- No registry login or secrets on PRs.
- Deploy: SSH key auth only, `StrictHostKeyChecking=yes` against `DEPLOY_KNOWN_HOSTS` (`ssh-keyscan -H <ip>`, verify out of band), `ref` validated by strict regex before use in a remote command, key removed at the end, environment approval required.
- Actions are pinned to major versions; pinning to full commit SHAs (with Dependabot updates) is recommended for production hardening.

## 6. Deployment Steps
`docs/runbooks/infra/ci-cd.md`.

## 7. Rollback
Re-run `Deploy` manually with the previous `ref`.

## 8. Monitoring & Alerts
GitHub Actions failure notifications. Post-deploy health is enforced by `docker compose up --wait`.

## 9. Change History
- Replaced `backend-ci-cd.yml`/`frontend-ci-cd.yml` (no deploy, `:none` tags, login on PRs, unused postgres/QEMU, setup-python@v4, wrong image names, frontend untested).

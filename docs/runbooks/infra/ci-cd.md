# Runbook - CI/CD pipelines

## 1. Purpose
Operate the GitHub Actions pipelines: test, image publish, infra checks and production deploys.

## 2. How to Run
Pipelines run automatically (see `docs/features/infra/ci-cd.md`). Manual: Actions tab -> workflow -> Run workflow. Local dry run: `act` (installed in `infra/sandbox`).

Required GitHub configuration:

| Secret | Scope | Value |
|--------|-------|-------|
| `DOCKER_USERNAME` | repository | Docker Hub user (`sepehrmdn`) |
| `DOCKER_PASSWORD` | repository | Docker Hub access token with write scope (not the account password) |
| `DEPLOY_HOST` | environment `production` | public IP or DNS name of the host |
| `DEPLOY_USER` | environment `production` | `deploy` (created by the `common` role) |
| `DEPLOY_SSH_KEY` | environment `production` | private key whose public half is in `deploy_authorized_keys` (dedicated ed25519, no passphrase) |
| `DEPLOY_KNOWN_HOSTS` | environment `production` | output of `ssh-keyscan -H <host>`, verified out of band |

Create the `production` environment with required reviewers and (optionally) a tag-only deployment branch rule. Enable branch protection on `main` requiring the Backend/Frontend/Infra/Helm checks.

## 3. How to Deploy
1. Merge to `main`: images `sha-<7>` and `latest` are pushed.
2. Tag a release: `git tag v1.2.3 && git push origin v1.2.3`. Images `v1.2.3` are built; `Deploy` waits for both manifests, then pauses for environment approval, then pulls and runs `docker compose up -d --remove-orphans --wait` on the host with `TAG=v1.2.3`.
3. Manual/rollback: run `Deploy` with `ref` = previous tag.

The host must already be provisioned (`provision-vm.md`) and have `/opt/resume-review` cloned with a valid `deployments/docker/.env`.

## 4. Health Checks
Deploy job succeeds only if `compose up --wait` reports healthy services. Verify `https://<API_DOMAIN>/health`.

## 5. Monitoring
Workflow run history; enable email/Slack notifications on failed workflows.

## 6. Debugging
- Build fails on PR from fork: expected login is skipped; check `test` job logs.
- `denied: requested access` on push: wrong token scope or `DOCKER_USERNAME`.
- Deploy `Host key verification failed`: refresh `DEPLOY_KNOWN_HOSTS`.
- Deploy waits 20 min for images: the backend/frontend build for the tag failed or path-filtered; check those runs.
- Frontend workflow fails at install: `frontend/requirements-dev.txt` must exist (contract).
- Known gap: the root `.gitignore` ignores `.terraform.lock.hcl` and `group_vars/`; un-ignore `infra/ansible/inventories/*/group_vars/` (and keep `vault.yml` encrypted) so the inventory vars are committed.

## 7. Disaster Recovery
Rotate leaked secrets immediately (Docker token, deploy key: replace the key in `deploy_authorized_keys` and re-run `site.yml`). Re-run failed deploys from the Actions tab.

## 8. Ownership
DevOps / repository owner (DevSepOps).

## 9. Change History
- Initial runbook for the new workflow set.

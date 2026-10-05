# Workflows

## Day-to-day

| Task | Command |
|------|---------|
| Backend tests | `cd backend && pytest` |
| Frontend tests | `cd frontend && pytest` |
| New DB migration | `cd backend && alembic revision --autogenerate -m "<what>"`, review it, then `alembic upgrade head` |
| Check models match migrations | `cd backend && alembic check` |
| Build images locally | `cd deployments/docker && docker compose build` |
| Render the Helm chart | `helm template t deployments/helm/resume-review -f deployments/helm/resume-review/values-example.yaml` |

## Release → production (Compose VM)

1. Merge `dev` into `main`. CI pushes `sha-<7>` and `latest` images.
2. Tag the release: `git tag v1.2.3 && git push origin v1.2.3`. CI builds `v1.2.3` images.
3. `deploy.yml` waits for both images, then asks for approval in the `production` environment.
4. After approval it connects over SSH, checks out the tag, then runs `docker compose pull && docker compose up -d --wait`.

Details are in [runbooks/infra/ci-cd.md](../runbooks/infra/ci-cd.md).

## New server from scratch

`terraform apply` (see `infra/terraform/envs/dev`) → copy the outputs into the Ansible inventory →
`ansible-playbook playbooks/site.yml --ask-vault-pass`. See [runbooks/infra/provision-vm.md](../runbooks/infra/provision-vm.md).

## Kubernetes

See [runbooks/infra/helm-deploy.md](../runbooks/infra/helm-deploy.md).

# Ansible (roles common, docker, app_deploy)

## 1. Purpose
Turn a bare Ubuntu 24.04 host into a hardened Docker host and deploy the Compose stack from `deployments/docker`.

## 2. Architecture
```
site.yml   = common -> docker -> app_deploy      (first provisioning)
deploy.yml = app_deploy                          (new version / config change)
inventories/dev/hosts.yml            group app_servers (from terraform output)
inventories/dev/group_vars/all/main.yml       non-secret vars
inventories/dev/group_vars/all/vault.yml      secrets, ansible-vault encrypted (example file provided)
```
- `common`: apt update/safe-upgrade, base packages (incl. `acl`), unattended-upgrades, ufw (22/80/443, default deny incoming), `deploy` user + authorized keys, sshd drop-in `00-hardening.conf` (no password auth, no root login) with `sshd -t` validation before restart.
- `docker`: Docker apt key to `/etc/apt/keyrings/docker.asc`, `deb822_repository`, docker-ce, cli, containerd, buildx, compose plugin, daemon log rotation, docker group, service enabled. Idempotent (no get.docker.com script).
- `app_deploy`: git checkout of `app_version` to `/opt/resume-review`, renders `deployments/docker/.env` (mode 0600, keys mirror `.env.example`) and `proxy/secrets/htpasswd`, then `community.docker.docker_compose_v2` (`pull: always`, `remove_orphans`, `wait`).

## 3. Inputs (Variables)
Non-secret (`group_vars/all/main.yml`): `deploy_user`, `deploy_authorized_keys`, `app_repo_url`, `app_version`, `app_dir`, `compose_profiles`, `image_tag` (written as `TAG`), `app_domain`, `api_domain`, `grafana_domain`, `traefik_domain`, `portainer_domain`, `acme_email`, `app_environment`, `app_env_extra` (dict of extra `.env` keys).
Secret (vault): `vault_postgres_password`, `vault_jwt_secret_key` (>= 32 chars), `vault_flet_secret_key`, `vault_elastic_password`, `vault_grafana_admin_password`, `vault_traefik_htpasswd`.
Collections: `community.docker`, `community.general`, `ansible.posix` (`requirements.yml`).

## 4. Outputs
A running Compose project (`docker compose ps` on the host). `.env` is the single config artefact on the host.

## 5. Security Rules
- Secrets only in the ansible-vault file; tasks handling them use `no_log`. `.env` is 0600 owned by `deploy`.
- Key-only SSH; password auth disabled by a drop-in that sorts before cloud-init's.
- Members of the `docker` group are root-equivalent: only `deploy` is added.
- Docker-published ports bypass ufw; the cloud SG/NSG is the authoritative perimeter.
- Host key checking is on (documented in `ansible.cfg`); the Docker apt key is trusted via TLS download (Docker publishes no detached checksum).

## 6. Deployment Steps
`docs/runbooks/infra/provision-vm.md`.

## 7. Rollback
`ansible-playbook playbooks/deploy.yml -e app_version=<previous tag> -e image_tag=<previous tag>`. DB migrations are not reverted automatically (see backend runbook).

## 8. Monitoring & Alerts
`compose_profiles: [monitoring]` enables the ELK/Grafana profile. `docker_compose_v2 wait: true` fails the play when a service does not become healthy within `app_wait_timeout`.

## 9. Change History
- Replaced the legacy `IaC/ansible_playbook` (host group typo, python3.12 interpreter, placeholder cfg, scaffold roles, copy of a nonexistent compose file).
- Known gap: `.gitignore` ignores `group_vars/`; see CI/CD runbook.

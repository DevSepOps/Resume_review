# Ansible

Configures a fresh Ubuntu 24.04 host (from `infra/terraform`) and deploys the Docker Compose stack.

| Role | Does |
|------|------|
| `common` | apt update/upgrade, unattended-upgrades, ufw (22/80/443, default deny), `deploy` user + authorized keys, sshd key-only |
| `docker` | Docker CE from the official apt repo, compose plugin, log rotation, docker group |
| `app_deploy` | git checkout of `app_version` into `/opt/resume-review`, renders `deployments/docker/.env` from vault vars, `docker compose up` (pull always) |

## Run

```bash
cd infra/ansible
ansible-galaxy collection install -r requirements.yml
# 1. paste the terraform snippet into inventories/dev/hosts.yml
# 2. secrets
cp inventories/dev/group_vars/all/vault.yml.example inventories/dev/group_vars/all/vault.yml
$EDITOR inventories/dev/group_vars/all/vault.yml && ansible-vault encrypt inventories/dev/group_vars/all/vault.yml
# 3. first provisioning (uses the cloud login user, e.g. ubuntu)
ansible-playbook playbooks/site.yml --ask-vault-pass
# later: deploy a new version only
ansible-playbook playbooks/deploy.yml --ask-vault-pass -e app_version=v1.2.3 -e image_tag=v1.2.3
```

Offline checks: `ansible-playbook playbooks/site.yml --syntax-check` and `ansible-lint`.

Notes: Docker-published ports bypass ufw; the cloud security group / NSG is the authoritative perimeter.
The repo is assumed public (git over https). Run `playbooks/site.yml` as the cloud login user: it creates the `deploy` user.

WSL note: Ansible ignores `ansible.cfg` in world-writable directories (e.g. /mnt/c). Use `export ANSIBLE_CONFIG=$PWD/ansible.cfg` there.

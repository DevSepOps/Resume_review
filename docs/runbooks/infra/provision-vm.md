# Runbook - Provision a VM and deploy the stack

## 1. Purpose
Create a cloud VM with Terraform, configure it with Ansible and start the Compose stack. End-to-end flow:
`terraform output` -> Ansible inventory -> `app_deploy` renders `.env` -> `docker compose up`.

## 2. How to Run
Prerequisites: Terraform >= 1.6, Python venv with `ansible-core`, an SSH key pair, cloud credentials in your shell (never in files), DNS A records for `APP_DOMAIN`/`API_DOMAIN`/`TRAEFIK_DOMAIN` pointing to the new IP (after step 1).

```bash
# 1. infrastructure (AWS; Azure: envs/dev-azure + az login + ARM_SUBSCRIPTION_ID)
cd infra/terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars    # owner, key_name, admin_cidr
terraform init && terraform plan -out tfplan && terraform apply tfplan
terraform output ansible_inventory_snippet       # also: public_ip, ssh_command

# 2. inventory and secrets
cd ../../../ansible
$EDITOR inventories/dev/hosts.yml                # paste snippet (ansible_host, ansible_user)
$EDITOR inventories/dev/group_vars/all/main.yml  # domains, acme_email, deploy_authorized_keys, app_version
cp inventories/dev/group_vars/all/vault.yml.example inventories/dev/group_vars/all/vault.yml
$EDITOR inventories/dev/group_vars/all/vault.yml && ansible-vault encrypt inventories/dev/group_vars/all/vault.yml
ssh-keyscan -H <public_ip> >> ~/.ssh/known_hosts # verify the fingerprint out of band

# 3. configure + deploy
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/site.yml --ask-vault-pass
```
Generate secrets with `openssl rand -hex 32`; dashboard basic auth with `htpasswd -nbB admin '<pw>'`.

## 3. How to Deploy
New version: `ansible-playbook playbooks/deploy.yml --ask-vault-pass -e app_version=v1.2.3 -e image_tag=v1.2.3`, or let `deploy.yml` (GitHub) do it, see `ci-cd.md`.

## 4. Health Checks
`ssh <user>@<ip> 'cd /opt/resume-review/deployments/docker && docker compose ps'`; `curl -fsS https://<API_DOMAIN>/health` -> `{"status":"ok"}`; `/ready` checks the DB.

## 5. Monitoring
Enable `compose_profiles: [monitoring]` in `main.yml` and re-run `deploy.yml` (needs >= 8 GiB RAM in practice: ELK).

## 6. Debugging
- SSH unreachable: check `admin_cidr` matches your current IP, security group/NSG, key pair name.
- `Permission denied (publickey)`: wrong `ansible_user` (ubuntu / azureuser) or key; `ssh -vvv`.
- Ansible ignores `ansible.cfg` on /mnt/c (world-writable dir): `export ANSIBLE_CONFIG=$PWD/ansible.cfg`.
- Compose failures: `docker compose logs <service>`; a missing `.env` var aborts with `set X in .env`.
- Certificates not issued: DNS not pointing at the host, ports 80/443 blocked, or ACME rate limit (use `acme_ca_server` staging).

## 7. Disaster Recovery
State: restore from the remote backend (versioned). Data: Postgres and uploads live in Docker volumes on the host; back them up before `terraform destroy`/replace. Rebuild: apply Terraform, run `site.yml`, restore volumes.

## 8. Ownership
DevOps / repository owner (DevSepOps).

## 9. Change History
- Initial runbook for the refactored infra layout.

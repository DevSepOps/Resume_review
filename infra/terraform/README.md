# Terraform

Reusable modules plus one root configuration per environment.

```
modules/
  aws_network/    security group (22 from admin_cidr, 80/443 public)
  aws_compute/    Ubuntu 24.04 EC2 (gp3 encrypted root, IMDSv2, user_data bootstrap)
  azure_network/  vnet, subnet, NSG (same rules), static Standard public IP
  azure_compute/  Ubuntu 24.04 Linux VM, SSH key only
envs/
  dev/            AWS (default)
  dev-azure/      Azure
  stage/, prod/   README stubs: copy dev when needed
```

Modules contain no `provider` blocks and no credentials; the env owns providers.

## Quick start (AWS)

```bash
cd infra/terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars   # git-ignored; edit owner, key_name, admin_cidr
export AWS_PROFILE=<your-profile>              # or AWS_ACCESS_KEY_ID/... ; never put keys in code
terraform init
terraform plan -out tfplan
terraform apply tfplan
terraform output ansible_inventory_snippet
```

Azure: same in `envs/dev-azure`, authenticate with `az login` or `ARM_SUBSCRIPTION_ID/ARM_TENANT_ID/ARM_CLIENT_ID/ARM_CLIENT_SECRET`.

## State

`backend.tf` defaults to a **local** backend so `init` works immediately. State files can contain
sensitive data and are git-ignored. For shared use switch to the commented S3 (or azurerm) backend.

## Lock file

`.terraform.lock.hcl` pins provider hashes and should normally be committed. The repo `.gitignore`
currently ignores it, so CI runs `init -backend=false` and resolves `~> 5.0` / `~> 4.0` freshly.
Remove the ignore rule and commit the lock files from the first real `terraform init` to make builds reproducible.

## Checks

```bash
terraform fmt -check -recursive infra/terraform
terraform -chdir=infra/terraform/envs/dev init -backend=false && terraform -chdir=infra/terraform/envs/dev validate
```

# Terraform - AWS (aws_network, aws_compute, envs/dev)

## 1. Purpose
Provision one Ubuntu 24.04 EC2 host reachable over SSH (admin only) and HTTP/HTTPS (public) that Ansible then turns into the Docker Compose app host.

## 2. Architecture
```
envs/dev ──► module.network  (aws_network)  security group in the default VPC (or var.vpc_id)
         └─► module.compute  (aws_compute)  aws_instance + Canonical AMI data source
```
- Modules have no `provider` block and no credentials; `envs/dev/providers.tf` owns the provider (`region = var.region`, `default_tags` Project/Environment/Owner/ManagedBy).
- Instance: Ubuntu 24.04 LTS (latest Canonical AMI, `ignore_changes = [ami]` so a new AMI never replaces a running host), `t3.medium`, 30 GiB gp3 root volume, encrypted, IMDSv2 required.
- `user_data` (`modules/aws_compute/user_data.sh.tftpl`) only sets the hostname and installs python3; everything else is Ansible.
- State: `backend "local"` by default (init works immediately); S3 backend block is provided commented in `envs/dev/backend.tf`.

## 3. Inputs (Variables)
`envs/dev`:

| Variable | Type | Default | Notes |
|----------|------|---------|-------|
| `region` | string | `eu-west-2` | provider region |
| `project` / `environment` | string | `resume-review` / `dev` | tags and name prefix |
| `owner` | string | required | Owner tag |
| `key_name` | string | required | existing EC2 key pair |
| `admin_cidr` | string | required | SSH source, validated CIDR, `0.0.0.0/0` rejected |
| `instance_type` | string | `t3.medium` | stack needs >= 4 GiB RAM |
| `root_volume_size_gb` | number | `30` | 20-500 |
| `vpc_id`, `subnet_id` | string | `null` | default VPC / AWS-chosen subnet |
| `ssh_user` | string | `ubuntu` | outputs only |

Module inputs are documented with types, descriptions and validations in `modules/*/variables.tf`.

## 4. Outputs
`public_ip`, `ssh_command`, `ansible_inventory_snippet` (paste under `app_servers.hosts` in `infra/ansible/inventories/<env>/hosts.yml`). Module outputs: `security_group_id`, `vpc_id`, `instance_id`, `public_ip`, `private_ip`, `ami_id`.

## 5. Security Rules
- SSH (22) only from `admin_cidr`; 80/443 from anywhere; egress all.
- No credentials in code: use `AWS_PROFILE`, env vars, SSO or OIDC role. `*.tfvars` and state are git-ignored.
- IMDSv2 only, encrypted root volume, key-pair SSH only (no passwords).
- State may contain sensitive values: use the S3 backend (encrypted, versioned, private) for shared use.

## 6. Deployment Steps
See `docs/runbooks/infra/provision-vm.md`. Short form: copy `terraform.tfvars.example`, `terraform init`, `plan -out`, `apply`.

## 7. Rollback
`terraform destroy` removes the host and security group (data on the root volume is lost; back up first). To revert a code change: check out the previous commit and `terraform apply`.

## 8. Monitoring & Alerts
None at the infra layer (YAGNI). Use EC2 status checks / CloudWatch alarms if the host becomes critical; application monitoring is the `monitoring` compose profile.

## 9. Change History
- Replaced the legacy `IaC/` folder: fixed user_data path, credentials-as-args, missing SG/outputs, unpinned providers, tiny instance type.

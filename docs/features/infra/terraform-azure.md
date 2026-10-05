# Terraform - Azure (azure_network, azure_compute, envs/dev-azure)

## 1. Purpose
Provision one Ubuntu 24.04 Azure VM with a static public IP, reachable over SSH (admin only) and HTTP/HTTPS (public).

## 2. Architecture
```
envs/dev-azure ─► azurerm_resource_group
               ├─► module.network  (azure_network)  vnet, subnet, NSG (associated to subnet), static Standard public IP
               └─► module.compute  (azure_compute)  NIC + azurerm_linux_virtual_machine
```
- Resource group is owned by the env; modules receive `resource_group_name` and `location`.
- `azurerm ~> 4.0`; provider block with `features {}` only in the env; credentials come from `az login` or `ARM_*` env vars (`ARM_SUBSCRIPTION_ID` is mandatory in azurerm 4.x).
- VM: `Standard_B2s`, Canonical `ubuntu-24_04-lts`/`server`, Premium_LRS 30 GiB disk, `disable_password_authentication = true`, SSH public key only, `custom_data` = base64 of `user_data.sh.tftpl`.
- Admin username defaults to `azureuser`; reserved names (admin, root, ...) are rejected by validation.

## 3. Inputs (Variables)
| Variable | Type | Default | Notes |
|----------|------|---------|-------|
| `location` | string | `westeurope` | region |
| `project` / `environment` | string | `resume-review` / `dev` | names and tags |
| `owner` | string | required | tag |
| `ssh_public_key` | string | required | OpenSSH public key (validated prefix) |
| `admin_cidr` | string | required | SSH source; `0.0.0.0/0` rejected |
| `admin_username` | string | `azureuser` | |
| `vm_size` | string | `Standard_B2s` | needs >= 4 GiB RAM |
| `os_disk_size_gb` | number | `30` | 30-500 |

## 4. Outputs
`public_ip`, `ssh_command`, `ansible_inventory_snippet`. Module outputs: `subnet_id`, `public_ip_id`, `public_ip_address`, `nsg_id`, `vm_id`, `private_ip`, `admin_username`.

## 5. Security Rules
- NSG: 22 from `admin_cidr`, 80/443 from `Internet`; everything else denied by Azure default rules.
- No password authentication, no credentials in code, state and `*.tfvars` git-ignored.
- Use the commented `azurerm` backend (storage account with versioning, Azure AD auth) for shared state.

## 6. Deployment Steps
`docs/runbooks/infra/provision-vm.md` (Azure variant): `az login`, `export ARM_SUBSCRIPTION_ID=...`, copy tfvars, init/plan/apply in `envs/dev-azure`.

## 7. Rollback
`terraform destroy` (removes the whole resource group contents managed here; the public IP changes on re-create).

## 8. Monitoring & Alerts
None at the infra layer; add Azure Monitor alerts if the VM becomes critical.

## 9. Change History
- Replaced the legacy `azurerm_virtual_machine` (password auth, default password, `admin` username, no NSG/IP, unpinned provider).

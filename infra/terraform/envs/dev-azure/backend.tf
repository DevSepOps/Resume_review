# Default: local state (fine for a first run / experiments). `terraform init` works out of the box.
#
# For anything shared, switch to the azurerm backend:
#   1. Create a storage account + blob container once (versioning on, public access off).
#   2. Comment the `backend "local"` block, uncomment `backend "azurerm"`, fill the values.
#   3. Run `terraform init -migrate-state`.
# Backend blocks cannot use variables; auth comes from `az login` / ARM_* env vars (use_azuread_auth).
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }

  # backend "azurerm" {
  #   resource_group_name  = "<tfstate-rg>"
  #   storage_account_name = "<tfstateaccount>"
  #   container_name       = "tfstate"
  #   key                  = "resume-review/dev-azure/terraform.tfstate"
  #   use_azuread_auth     = true
  # }
}

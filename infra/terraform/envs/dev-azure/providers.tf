# Credentials are NEVER set here. Authenticate with `az login`, or export:
#   ARM_SUBSCRIPTION_ID, ARM_TENANT_ID, ARM_CLIENT_ID, ARM_CLIENT_SECRET (or ARM_USE_OIDC=true)
# azurerm 4.x requires the subscription id; ARM_SUBSCRIPTION_ID provides it.
provider "azurerm" {
  features {}
}

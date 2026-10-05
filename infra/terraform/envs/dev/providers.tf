# Credentials are NEVER set here. Use the standard AWS chain: AWS_PROFILE,
# AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars, SSO, or an instance/OIDC role.
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      Owner       = var.owner
      ManagedBy   = "terraform"
    }
  }
}

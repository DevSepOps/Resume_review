variable "name" {
  description = "Name prefix for the network resources (e.g. resume-review-dev)."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-]{1,40}$", var.name))
    error_message = "name must be 1-40 characters: letters, digits and hyphens only."
  }
}

variable "vpc_id" {
  description = "VPC to create the security group in. When null the account's default VPC in the provider region is used."
  type        = string
  default     = null
}

variable "admin_cidr" {
  description = "CIDR allowed to reach SSH (22), e.g. 203.0.113.10/32. Open-to-the-world values are rejected."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.admin_cidr))
    error_message = "admin_cidr must be a valid IPv4 CIDR block, e.g. 203.0.113.10/32."
  }

  validation {
    condition     = var.admin_cidr != "0.0.0.0/0"
    error_message = "admin_cidr must not be 0.0.0.0/0: SSH must never be open to the internet."
  }
}

variable "tags" {
  description = "Extra tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}

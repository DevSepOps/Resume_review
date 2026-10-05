variable "name" {
  description = "Name prefix for the network resources (e.g. resume-review-dev)."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-]{1,40}$", var.name))
    error_message = "name must be 1-40 characters: letters, digits and hyphens only."
  }
}

variable "resource_group_name" {
  description = "Existing resource group (created by the environment) that receives the network resources."
  type        = string
}

variable "location" {
  description = "Azure region, e.g. westeurope."
  type        = string
}

variable "vnet_cidr" {
  description = "Address space of the virtual network."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vnet_cidr))
    error_message = "vnet_cidr must be a valid IPv4 CIDR block."
  }
}

variable "subnet_cidr" {
  description = "Address range of the app subnet (must be inside vnet_cidr)."
  type        = string
  default     = "10.20.1.0/24"

  validation {
    condition     = can(cidrnetmask(var.subnet_cidr))
    error_message = "subnet_cidr must be a valid IPv4 CIDR block."
  }
}

variable "admin_cidr" {
  description = "CIDR allowed to reach SSH (22), e.g. 203.0.113.10/32. Open-to-the-world values are rejected."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.admin_cidr))
    error_message = "admin_cidr must be a valid IPv4 CIDR block, e.g. 203.0.113.10/32."
  }

  validation {
    condition     = !contains(["0.0.0.0/0", "*"], var.admin_cidr)
    error_message = "admin_cidr must not be open to the internet (0.0.0.0/0)."
  }
}

variable "tags" {
  description = "Extra tags applied to every resource in this module."
  type        = map(string)
  default     = {}
}

variable "name" {
  description = "VM name (also used as computer name and NIC prefix)."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]{0,62}$", var.name))
    error_message = "name must start with a letter and contain only letters, digits and hyphens (max 63)."
  }
}

variable "resource_group_name" {
  description = "Existing resource group for the VM."
  type        = string
}

variable "location" {
  description = "Azure region, e.g. westeurope."
  type        = string
}

variable "subnet_id" {
  description = "Subnet the NIC is attached to."
  type        = string
}

variable "public_ip_id" {
  description = "Public IP attached to the NIC. Null creates a private-only VM."
  type        = string
  default     = null
}

variable "vm_size" {
  description = "VM size. The full stack needs >= 4 GiB RAM."
  type        = string
  default     = "Standard_B2s"
}

variable "admin_username" {
  description = "Admin user. Azure reserves names such as admin, administrator, root."
  type        = string
  default     = "azureuser"

  validation {
    condition     = !contains(["admin", "administrator", "root", "guest", "user", "test", "azure"], lower(var.admin_username))
    error_message = "admin_username is reserved by Azure; use e.g. azureuser."
  }
}

variable "ssh_public_key" {
  description = "SSH public key (OpenSSH format, e.g. contents of ~/.ssh/id_ed25519.pub). Password login is disabled."
  type        = string

  validation {
    condition     = can(regex("^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp[0-9]+) ", var.ssh_public_key))
    error_message = "ssh_public_key must be an OpenSSH public key (ssh-rsa, ssh-ed25519 or ecdsa-*)."
  }
}

variable "os_disk_size_gb" {
  description = "OS disk size in GiB."
  type        = number
  default     = 30

  validation {
    condition     = var.os_disk_size_gb >= 30 && var.os_disk_size_gb <= 500
    error_message = "os_disk_size_gb must be between 30 and 500 (the Ubuntu image needs >= 30)."
  }
}

variable "tags" {
  description = "Extra tags applied to the VM, NIC and disk."
  type        = map(string)
  default     = {}
}

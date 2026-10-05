variable "location" {
  description = "Azure region."
  type        = string
  default     = "westeurope"
}

variable "project" {
  description = "Project tag value."
  type        = string
  default     = "resume-review"
}

variable "environment" {
  description = "Environment name (dev, stage, prod)."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner tag value (person or team)."
  type        = string
}

variable "ssh_public_key" {
  description = "OpenSSH public key for the admin user (contents of the .pub file)."
  type        = string
}

variable "admin_cidr" {
  description = "CIDR allowed to SSH to the VM, e.g. 203.0.113.10/32 (never 0.0.0.0/0)."
  type        = string
}

variable "admin_username" {
  description = "VM admin user (not a reserved name such as admin)."
  type        = string
  default     = "azureuser"
}

variable "vm_size" {
  description = "VM size."
  type        = string
  default     = "Standard_B2s"
}

variable "os_disk_size_gb" {
  description = "OS disk size in GiB."
  type        = number
  default     = 30
}

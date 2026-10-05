variable "name" {
  description = "Instance name (Name tag)."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-]{1,40}$", var.name))
    error_message = "name must be 1-40 characters: letters, digits and hyphens only."
  }
}

variable "instance_type" {
  description = "EC2 instance type. The full stack (backend, frontend, db, proxy, monitoring) needs >= 4 GiB RAM."
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of an EXISTING EC2 key pair used for SSH. No password login is configured."
  type        = string

  validation {
    condition     = length(var.key_name) > 0
    error_message = "key_name must not be empty."
  }
}

variable "security_group_ids" {
  description = "Security groups attached to the instance."
  type        = list(string)

  validation {
    condition     = length(var.security_group_ids) > 0
    error_message = "At least one security group id is required."
  }
}

variable "subnet_id" {
  description = "Subnet to launch into. Null lets AWS pick a default-VPC subnet."
  type        = string
  default     = null
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GiB (images, uploads and DB data live here)."
  type        = number
  default     = 30

  validation {
    condition     = var.root_volume_size_gb >= 20 && var.root_volume_size_gb <= 500
    error_message = "root_volume_size_gb must be between 20 and 500."
  }
}

variable "associate_public_ip" {
  description = "Assign a public IPv4 address to the instance."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Extra tags applied to the instance and its volumes."
  type        = map(string)
  default     = {}
}

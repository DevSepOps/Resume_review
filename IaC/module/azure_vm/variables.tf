variable "prefix" {
  default     = "tfvmex"
  type        = string
  description = "This is the machine prefix"
}

variable "location" {
  default = "West Europe"
}

variable "vm_size" {
  default = "Standard_DS1_v2"
}

variable "storage_os_disk" {
  default = "myosdisk1"
}

variable "hostname" {
  default = "hostname"
}

variable "admin_username" {
  default = "admin"
}

variable "admin_password" {
  default = "Password1234!"
}

variable "env" {
  default     = "dev"
  type        = string
  description = "environment name"
}

variable "client_id" {}

variable "client_secret" {}

variable "tenant_id" {}

variable "subscription_id" {}


variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "eu-west-2"
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

variable "key_name" {
  description = "Name of an existing EC2 key pair for SSH."
  type        = string
}

variable "admin_cidr" {
  description = "CIDR allowed to SSH to the host, e.g. 203.0.113.10/32 (never 0.0.0.0/0)."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size_gb" {
  description = "Root volume size in GiB."
  type        = number
  default     = 30
}

variable "vpc_id" {
  description = "VPC for the security group. Null uses the default VPC."
  type        = string
  default     = null
}

variable "subnet_id" {
  description = "Subnet for the instance. Null lets AWS choose a default-VPC subnet. Must belong to vpc_id when both are set."
  type        = string
  default     = null
}

variable "ssh_user" {
  description = "Login user of the AMI (Ubuntu images: ubuntu). Used only for the outputs."
  type        = string
  default     = "ubuntu"
}

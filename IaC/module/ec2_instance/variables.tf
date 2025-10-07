variable "ami" {
  default     = "ami-091f18e98bc129c4e"
  type        = string
  description = "This is the machine ami"
}
variable "instance_type" {
  default = "t2.micro"
}
variable "key_name" {}
variable "machine_name" {}
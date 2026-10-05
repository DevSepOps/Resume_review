output "security_group_id" {
  description = "ID of the app security group."
  value       = aws_security_group.app.id
}

output "vpc_id" {
  description = "VPC the security group lives in."
  value       = local.vpc_id
}

output "instance_id" {
  description = "EC2 instance id."
  value       = aws_instance.this.id
}

output "public_ip" {
  description = "Public IPv4 address (empty when associate_public_ip = false)."
  value       = aws_instance.this.public_ip
}

output "private_ip" {
  description = "Private IPv4 address."
  value       = aws_instance.this.private_ip
}

output "ami_id" {
  description = "AMI the instance was launched from."
  value       = aws_instance.this.ami
}

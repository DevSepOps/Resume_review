output "public_ip" {
  description = "Public IPv4 address of the app host."
  value       = module.compute.public_ip
}

output "ssh_command" {
  description = "SSH into the host (adjust the key path)."
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ${var.ssh_user}@${module.compute.public_ip}"
}

output "ansible_inventory_snippet" {
  description = "Paste into infra/ansible/inventories/<env>/hosts.yml under app_servers.hosts."
  value       = <<-EOT
    ${local.name}:
      ansible_host: ${module.compute.public_ip}
      ansible_user: ${var.ssh_user}
  EOT
}

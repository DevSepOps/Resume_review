output "public_ip" {
  description = "Static public IPv4 address of the app host."
  value       = module.network.public_ip_address
}

output "ssh_command" {
  description = "SSH into the VM (uses your default key or add -i)."
  value       = "ssh ${var.admin_username}@${module.network.public_ip_address}"
}

output "ansible_inventory_snippet" {
  description = "Paste into infra/ansible/inventories/<env>/hosts.yml under app_servers.hosts."
  value       = <<-EOT
    ${local.name}:
      ansible_host: ${module.network.public_ip_address}
      ansible_user: ${var.admin_username}
  EOT
}

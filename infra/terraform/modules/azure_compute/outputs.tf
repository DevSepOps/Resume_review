output "vm_id" {
  description = "ID of the Linux VM."
  value       = azurerm_linux_virtual_machine.this.id
}

output "private_ip" {
  description = "Private IPv4 address."
  value       = azurerm_network_interface.this.private_ip_address
}

output "admin_username" {
  description = "SSH admin user."
  value       = var.admin_username
}

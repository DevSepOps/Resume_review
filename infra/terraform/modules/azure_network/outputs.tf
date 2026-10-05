output "subnet_id" {
  description = "ID of the app subnet."
  value       = azurerm_subnet.app.id
}

output "public_ip_id" {
  description = "ID of the static public IP to attach to the VM NIC."
  value       = azurerm_public_ip.this.id
}

output "public_ip_address" {
  description = "Static public IPv4 address."
  value       = azurerm_public_ip.this.ip_address
}

output "nsg_id" {
  description = "ID of the network security group."
  value       = azurerm_network_security_group.app.id
}

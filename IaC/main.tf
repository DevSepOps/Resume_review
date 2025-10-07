module "EC2_instance" {
  source       = "./module/ec2_instance"
  key_name     = "key_pair_name"
  machine_name = "machine_name"
}

module "azure_vm" {
  source          = "./module/azure_vm/"
  tenant_id       = "tenant_id"
  client_secret   = "client_secret"
  client_id       = "client_id"
  subscription_id = "subscription_id"
}

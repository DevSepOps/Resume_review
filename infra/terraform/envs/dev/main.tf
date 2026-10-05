locals {
  name = "${var.project}-${var.environment}"
}

module "network" {
  source = "../../modules/aws_network"

  name       = local.name
  vpc_id     = var.vpc_id
  admin_cidr = var.admin_cidr
}

module "compute" {
  source = "../../modules/aws_compute"

  name                = local.name
  instance_type       = var.instance_type
  key_name            = var.key_name
  security_group_ids  = [module.network.security_group_id]
  subnet_id           = var.subnet_id
  root_volume_size_gb = var.root_volume_size_gb
}

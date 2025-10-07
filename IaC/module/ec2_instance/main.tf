resource "aws_instance" "ec2" {
  ami           = var.ami
  instance_type = var.instance_type
  key_name      = var.key_name
  user_data     = file("./module/ec2_instace/user_data.sh")
  tags = {
    Name         = var.machine_name
    Created_By   = local.Created_By
    service_name = local.service_name
    owner        = local.owner
  }
}
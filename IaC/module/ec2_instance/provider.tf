terraform {
  # backend "s3" {
  #   bucket = "mbucket_name"
  #   key    = "path/to/my/key"
  #   region = "bucket-region"
  # }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "eu-west-2" # Your region
}
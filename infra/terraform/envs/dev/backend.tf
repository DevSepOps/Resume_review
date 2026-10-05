# Default: local state (fine for a first run / experiments). `terraform init` works out of the box.
#
# For anything shared, switch to the S3 backend:
#   1. Create the bucket once (versioning + SSE enabled, public access blocked) and,
#      optionally, a DynamoDB table with hash key `LockID` for locking.
#   2. Comment the `backend "local"` block, uncomment the `backend "s3"` block, fill the values.
#   3. Run `terraform init -migrate-state`.
# Backend blocks cannot use variables; credentials come from the AWS environment, not from code.
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }

  # backend "s3" {
  #   bucket         = "<your-tfstate-bucket>"
  #   key            = "resume-review/dev/terraform.tfstate"
  #   region         = "eu-west-2"
  #   encrypt        = true
  #   dynamodb_table = "<your-lock-table>" # optional but recommended
  # }
}

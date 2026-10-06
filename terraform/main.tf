# Main Terraform configuration
# This file wires together all modules and creates shared resources

# Random suffix for unique bucket name if not provided
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Generate bucket name if not provided
locals {
  reports_bucket_name = var.reports_bucket_name != null ? var.reports_bucket_name : "eks-assessor-reports-${random_string.bucket_suffix.result}"
}

# Data source for current AWS account and caller identity
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# Common tags applied to all resources
locals {
  common_tags = merge(
    var.tags,
    {
      "terraform.workspace" = terraform.workspace
    }
  )
}
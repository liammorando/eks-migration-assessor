# VPC Configuration
# Uses terraform-aws-modules/vpc/aws for a well-architected VPC
# Single NAT Gateway (cost tradeoff: saves ~$45/month but creates AZ dependency)
# Two AZs for HA, public + private subnets

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for k, az in local.azs : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k, az in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 48)]

  # Single NAT Gateway (cost savings ~$45/month)
  # Tradeoff: if NAT GW AZ fails, private subnet traffic in that AZ is impacted
  # For production, consider enable_nat_gateway = true with one per AZ
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Subnet tags for Kubernetes load balancer integration
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "owned"
  }

  tags = local.common_tags
}

# Data source for available AZs
data "aws_availability_zones" "available" {
  state = "available"
}
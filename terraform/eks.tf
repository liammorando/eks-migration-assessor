# EKS Cluster Configuration
# Uses terraform-aws-modules/eks/aws for managed EKS
# NO Fargate profile: Fargate does not support EBS volumes (required for PVCs)
# One managed node group in private subnets
# Cluster endpoint: public access for kubectl, private for intra-cluster

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id                               = module.vpc.vpc_id
  subnet_ids                           = module.vpc.private_subnets
  cluster_endpoint_public_access       = true
  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access_cidrs = var.api_allowed_cidrs

  # Enable cluster creator admin permissions (creator gets admin access)
  enable_cluster_creator_admin_permissions = true

  # EKS Managed Node Group
  # NO Fargate profile: Fargate does not support EBS volumes (required for PVCs)
  eks_managed_node_group_defaults = {
    ami_type       = "AL2023_x86_64_STANDARD"
    instance_types = [var.node_instance_type]
  }

  eks_managed_node_groups = {
    assessor = {
      name           = "${var.cluster_name}-nodes"
      instance_types = [var.node_instance_type]

      capacity_type = "ON_DEMAND"

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      labels = {
        Environment = "dev"
        NodeGroup   = "assessor"
      }

      tags = local.common_tags
    }
  }

  tags = local.common_tags
}
# EKS Addons
# Managed EKS addons for core functionality
# Pod Identity Agent + EBS CSI Driver (IAM role via Pod Identity Association)
# VPC CNI, CoreDNS, Kube Proxy

# Get latest addon versions for the cluster's Kubernetes version
data "aws_eks_addon_version" "pod_identity_agent" {
  kubernetes_version = module.eks.cluster_version
  addon_name         = "eks-pod-identity-agent"
  most_recent        = true
}

data "aws_eks_addon_version" "ebs_csi_driver" {
  kubernetes_version = module.eks.cluster_version
  addon_name         = "aws-ebs-csi-driver"
  most_recent        = true
}

data "aws_eks_addon_version" "vpc_cni" {
  kubernetes_version = module.eks.cluster_version
  addon_name         = "vpc-cni"
  most_recent        = true
}

data "aws_eks_addon_version" "coredns" {
  kubernetes_version = module.eks.cluster_version
  addon_name         = "coredns"
  most_recent        = true
}

data "aws_eks_addon_version" "kube_proxy" {
  kubernetes_version = module.eks.cluster_version
  addon_name         = "kube-proxy"
  most_recent        = true
}

# Pod Identity Agent (required for Pod Identity Associations)
resource "aws_eks_addon" "pod_identity_agent" {
  cluster_name  = module.eks.cluster_name
  addon_name    = "eks-pod-identity-agent"
  addon_version = data.aws_eks_addon_version.pod_identity_agent.version

  # Resolve conflicts by overwriting
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = local.common_tags

  depends_on = [module.eks]
}

# EBS CSI Driver (required for PVCs on EKS)
# The IAM role is associated via Pod Identity in pod_identity.tf
resource "aws_eks_addon" "ebs_csi_driver" {
  cluster_name  = module.eks.cluster_name
  addon_name    = "aws-ebs-csi-driver"
  addon_version = data.aws_eks_addon_version.ebs_csi_driver.version

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  # The CSI driver needs IAM permissions via Pod Identity
  # See pod_identity.tf for the role association
  # NO service_account_role_arn - using Pod Identity instead

  tags = local.common_tags

  depends_on = [module.eks]
}

# VPC CNI (Amazon VPC CNI plugin for Kubernetes)
resource "aws_eks_addon" "vpc_cni" {
  cluster_name  = module.eks.cluster_name
  addon_name    = "vpc-cni"
  addon_version = data.aws_eks_addon_version.vpc_cni.version

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  configuration_values = jsonencode({
    enableNetworkPolicy = "true"
  })

  tags = local.common_tags

  depends_on = [module.eks]
}

# CoreDNS
resource "aws_eks_addon" "coredns" {
  cluster_name  = module.eks.cluster_name
  addon_name    = "coredns"
  addon_version = data.aws_eks_addon_version.coredns.version

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = local.common_tags

  depends_on = [module.eks]
}

# Kube Proxy
resource "aws_eks_addon" "kube_proxy" {
  cluster_name  = module.eks.cluster_name
  addon_name    = "kube-proxy"
  addon_version = data.aws_eks_addon_version.kube_proxy.version

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  tags = local.common_tags

  depends_on = [module.eks]
}

# EBS CSI Driver IAM role (referenced by addon above)
# Trust policy for Pod Identity (pods.eks.amazonaws.com)
resource "aws_iam_role" "ebs_csi_driver" {
  name = "${var.cluster_name}-ebs-csi-driver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "pods.eks.amazonaws.com"
      }
      Action = [
        "sts:AssumeRole",
        "sts:TagSession"
      ]
    }]
  })

  tags = local.common_tags
}

# Attach managed policy for EBS CSI Driver
resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  role       = aws_iam_role.ebs_csi_driver.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}
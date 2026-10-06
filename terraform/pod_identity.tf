# Pod Identity Associations
# EKS Pod Identity (replaces IRSA) for fine-grained IAM permissions
# Two associations:
# 1. EBS CSI Driver -> AmazonEBSCSIDriverPolicy (managed by AWS)
# 2. App (eks-assessor) -> Least privilege S3 access on reports bucket only

# EBS CSI Driver Pod Identity Association
# Service account: ebs-csi-controller-sa in kube-system
# Role: AmazonEBSCSIDriverPolicy (managed by AWS)
resource "aws_eks_pod_identity_association" "ebs_csi_driver" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = "ebs-csi-controller-sa"
  role_arn        = aws_iam_role.ebs_csi_driver.arn

  # Optional: tags for the association
  tags = local.common_tags
}

# App IAM Role - Least privilege S3 access on reports bucket only
# Used by the eks-assessor service account in namespace eks-assessor
resource "aws_iam_role" "app_pod_identity" {
  name = "${var.cluster_name}-app-pod-identity-role"

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

# Inline policy for least privilege S3 access on reports bucket only
resource "aws_iam_role_policy" "app_s3_access" {
  name = "${var.cluster_name}-app-s3-policy"
  role = aws_iam_role.app_pod_identity.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          "arn:${data.aws_partition.current.partition}:s3:::${local.reports_bucket_name}"
        ]
      },
      {
        Sid    = "AllowObjectOperations"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:${data.aws_partition.current.partition}:s3:::${local.reports_bucket_name}/*"
        ]
      }
    ]
  })
}

# App Pod Identity Association
# Service account: eks-assessor in namespace eks-assessor
resource "aws_eks_pod_identity_association" "app" {
  cluster_name    = module.eks.cluster_name
  namespace       = "eks-assessor"
  service_account = "eks-assessor"
  role_arn        = aws_iam_role.app_pod_identity.arn

  # Only create if variable is enabled
  count = var.create_app_pod_identity ? 1 : 0

  tags = local.common_tags
}
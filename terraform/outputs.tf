# Terraform Outputs
# Provides useful information after deployment (even though we don't apply)

output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "cluster_arn" {
  description = "ARN of the EKS cluster"
  value       = module.eks.cluster_arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing images"
  value       = aws_ecr_repository.assessor.repository_url
}

output "reports_bucket_name" {
  description = "S3 bucket name for reports"
  value       = aws_s3_bucket.reports.id
}

output "reports_bucket_arn" {
  description = "S3 bucket ARN for reports"
  value       = aws_s3_bucket.reports.arn
}

output "ebs_csi_driver_role_arn" {
  description = "IAM role ARN for EBS CSI driver (Pod Identity)"
  value       = aws_iam_role.ebs_csi_driver.arn
}

output "app_pod_identity_role_arn" {
  description = "IAM role ARN for the app Pod Identity (S3 access)"
  value       = aws_iam_role.app_pod_identity.arn
}

output "kubectl_config_command" {
  description = "Command to update kubeconfig for the cluster"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.region}"
}

output "storage_class_name" {
  description = "Storage class name for the overlay (standard for local, gp3 for EKS)"
  value       = "gp3"
}

output "node_group_name" {
  description = "Managed node group name"
  value       = "${var.cluster_name}-nodes"
}
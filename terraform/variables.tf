# Input variables for EKS Migration Assessor infrastructure
# All resources are tagged with common_tags for cost tracking and ownership

variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "eks-assessor"
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster (must be in STANDARD support)"
  type        = string
  default     = "1.30"
}

variable "node_instance_type" {
  description = "EC2 instance type for managed node group"
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "Desired number of nodes in the managed node group"
  type        = number
  default     = 1
}

variable "node_min_size" {
  description = "Minimum number of nodes in the managed node group"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes in the managed node group"
  type        = number
  default     = 3
}

variable "tags" {
  description = "Common tags applied to all resources for cost tracking"
  type        = map(string)
  default = {
    Project     = "eks-migration-assessor"
    Environment = "dev"
    ManagedBy   = "terraform"
    Owner       = "platform-team"
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "api_allowed_cidrs" {
  description = "List of CIDR blocks allowed to access the EKS cluster public endpoint. Must be explicitly set (no default to 0.0.0.0/0). Example: [\"203.0.113.10/32\"]"
  type        = list(string)
  default     = []
}

variable "create_app_pod_identity" {
  description = "Whether to create Pod Identity association for the app (requires EKS Pod Identity Agent addon). Does not require OIDC provider."
  type        = bool
  default     = true
}

variable "reports_bucket_name" {
  description = "Name for the S3 reports bucket (must be globally unique)"
  type        = string
  default     = null # Will generate a random suffix if not provided
}
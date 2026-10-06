# ECR Repository for the assessor image
# Scan on push for vulnerability detection
# Immutable tags to prevent accidental overwrites
# Tag pattern list to match git SHA tags (semver pattern)

resource "aws_ecr_repository" "assessor" {
  name                 = var.cluster_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.common_tags
}

# Lifecycle policy: keep last 10 images, delete untagged after 7 days
# Tag pattern list to match semantic version tags (v1.2.3) and git SHA tags (sha-abc123)
resource "aws_ecr_lifecycle_policy" "assessor" {
  repository = aws_ecr_repository.assessor.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus      = "tagged"
          tagPatternList = ["v*", "sha-*"]
          countType      = "imageCountMoreThan"
          countNumber    = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
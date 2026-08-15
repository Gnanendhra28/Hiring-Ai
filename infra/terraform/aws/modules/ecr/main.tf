resource "aws_ecr_repository" "backend" {
  name                 = "hiring-ai-backend-${var.environment}"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = "hiring-ai-frontend-${var.environment}"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_ecr_repository" "worker" {
  name                 = "hiring-ai-worker-${var.environment}"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

variable "environment" { type = string }

variable "image_tag_mutability" {
  type        = string
  default     = "MUTABLE"
  description = "Tag mutability setting for ECR repositories (MUTABLE or IMMUTABLE)"
}

output "ecr_backend_url" { value = aws_ecr_repository.backend.repository_url }
output "ecr_frontend_url" { value = aws_ecr_repository.frontend.repository_url }
output "ecr_worker_url" { value = aws_ecr_repository.worker.repository_url }

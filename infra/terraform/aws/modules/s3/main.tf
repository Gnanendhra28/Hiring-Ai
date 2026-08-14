resource "aws_s3_bucket" "documents" {
  bucket = "sthiring-documents-${var.environment}-${var.region}"

  tags = {
    Name        = "sthiring-documents-${var.environment}"
    Environment = var.environment
    Project     = "AI-Hiring-Platform"
  }
}

resource "aws_s3_bucket_public_access_block" "public_block" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

variable "environment" { type = string }
variable "region" { type = string }

output "s3_bucket_name" { value = aws_s3_bucket.documents.id }
output "s3_bucket_arn" { value = aws_s3_bucket.documents.arn }

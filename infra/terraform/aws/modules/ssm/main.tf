resource "aws_ssm_parameter" "db_url" {
  name        = "/hiring-ai/${var.environment}/DATABASE_URL"
  type        = "SecureString"
  value       = "postgresql://psqladmin:PLACEHOLDER@localhost:5432/hiring_db"
  description = "Database connection string for Hiring AI backend"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "secret_key" {
  name        = "/hiring-ai/${var.environment}/SECRET_KEY"
  type        = "SecureString"
  value       = "PLACEHOLDER_SECRET_KEY_MIN_32_BYTES_STAGING"
  description = "JWT Secret key for Hiring AI authentication"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "encryption_key" {
  name        = "/hiring-ai/${var.environment}/ENCRYPTION_KEY"
  type        = "SecureString"
  value       = "PLACEHOLDER_ENCRYPTION_KEY_MIN_32_BYTES"
  description = "Data encryption key"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "gemini_key" {
  name        = "/hiring-ai/${var.environment}/GEMINI_API_KEY"
  type        = "SecureString"
  value       = "PLACEHOLDER_GEMINI_API_KEY"
  description = "Google Gemini API Key for advisory recommendations"

  lifecycle {
    ignore_changes = [value]
  }
}

variable "environment" { type = string }

output "ssm_param_db_url" { value = aws_ssm_parameter.db_url.name }
output "ssm_param_secret_key" { value = aws_ssm_parameter.secret_key.name }

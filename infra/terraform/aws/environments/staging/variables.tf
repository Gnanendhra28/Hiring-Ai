variable "environment" {
  type        = string
  default     = "staging"
  description = "Target environment name"
}

variable "region" {
  type        = string
  default     = "ap-south-2"
  description = "AWS target deployment region"
}

variable "aws_profile" {
  type        = string
  default     = "hiring-ai-staging"
  description = "AWS CLI credentials profile name"
}

variable "db_password" {
  type        = string
  description = "Administrator password for Staging RDS PostgreSQL instance"
  sensitive   = true
}

variable "admin_cidr" {
  type        = string
  default     = "127.0.0.1/32"
  description = "Administrator IP CIDR for SSH access"
}

# Cost Guardrails
variable "enable_nat_gateway" {
  type        = bool
  default     = false
  description = "Cost Guardrail: Disable NAT Gateway to prevent ~$32/month fee"
}

variable "enable_alb" {
  type        = bool
  default     = false
  description = "Cost Guardrail: Disable AWS Application Load Balancer to prevent ~$18/month fee"
}

variable "multi_az" {
  type        = bool
  default     = false
  description = "Cost Guardrail: Disable RDS Multi-AZ to stay under AWS Free Tier limits"
}

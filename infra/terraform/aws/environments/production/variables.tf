variable "environment" {
  type        = string
  default     = "production"
  description = "Target environment name (production)"
}

variable "region" {
  type        = string
  default     = "ap-south-2"
  description = "AWS target deployment region"
}

variable "aws_profile" {
  type        = string
  default     = "hiring-ai-production"
  description = "AWS CLI credentials profile name for Production"
}

variable "db_password" {
  type        = string
  description = "Administrator password for Production RDS PostgreSQL instance"
  sensitive   = true
}

variable "admin_cidr" {
  type        = string
  default     = "127.0.0.1/32"
  description = "Administrator IP CIDR for restricted administrative access"
}

variable "production_domain" {
  type        = string
  default     = ""
  description = "Production FQDN domain name for HTTPS certificate termination"
}

# Networking CIDRs (Isolated 10.1.0.0/16 Production VPC)
variable "vpc_cidr" {
  type        = string
  default     = "10.1.0.0/16"
  description = "Production VPC CIDR block"
}

variable "public_subnet_cidr" {
  type        = string
  default     = "10.1.1.0/24"
  description = "Production Public Subnet A CIDR block"
}

variable "public_subnet_b_cidr" {
  type        = string
  default     = "10.1.2.0/24"
  description = "Production Public Subnet B CIDR block"
}

variable "private_subnet_a_cidr" {
  type        = string
  default     = "10.1.10.0/24"
  description = "Production Dedicated Private Subnet A CIDR block for RDS"
}

variable "private_subnet_b_cidr" {
  type        = string
  default     = "10.1.20.0/24"
  description = "Production Dedicated Private Subnet B CIDR block for RDS"
}

# Production Guardrails & Hardening Options
variable "backup_retention_period" {
  type        = number
  default     = 0
  description = "Automated daily snapshot backup retention in days"
}

variable "deletion_protection" {
  type        = bool
  default     = true
  description = "Enable RDS termination deletion protection"
}

variable "skip_final_snapshot" {
  type        = bool
  default     = false
  description = "Create final DB snapshot on deletion"
}

# Cost Guardrails
variable "enable_nat_gateway" {
  type        = bool
  default     = false
  description = "Cost Guardrail: Disable NAT Gateway to prevent ~$35/month fee per AZ"
}

variable "enable_alb" {
  type        = bool
  default     = false
  description = "Cost Guardrail: Disable AWS Application Load Balancer to prevent ~$20/month fee"
}

variable "multi_az" {
  type        = bool
  default     = false
  description = "Cost Guardrail: Single-AZ baseline for initial budget optimization"
}

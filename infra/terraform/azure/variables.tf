variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, production)"
  default     = "production"
}

variable "location" {
  type        = string
  description = "Azure region for resource deployment"
  default     = "East US"
}

variable "location_short" {
  type        = string
  description = "Short name for Azure region"
  default     = "eus"
}

variable "tenant_id" {
  type        = string
  description = "Azure Active Directory Tenant ID"
}

variable "db_password" {
  type        = string
  description = "Administrator password for Azure PostgreSQL Flexible Server"
  sensitive   = true
}

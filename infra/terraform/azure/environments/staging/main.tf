# Staging Environment Terraform Specification

module "staging_infrastructure" {
  source         = "../../"
  environment    = "staging"
  location       = var.location
  location_short = var.location_short
  tenant_id      = var.tenant_id
  db_password    = var.db_password
}

variable "location" {
  type        = string
  default     = "East US"
  description = "Azure region for staging deployment"
}

variable "location_short" {
  type        = string
  default     = "eus"
  description = "Short name for Azure region"
}

variable "tenant_id" {
  type        = string
  description = "Azure Active Directory Tenant ID"
}

variable "db_password" {
  type        = string
  description = "Administrator password for Staging Azure PostgreSQL Flexible Server"
  sensitive   = true
}

output "staging_resource_group_name" {
  value = module.staging_infrastructure.resource_group_name
}

output "staging_container_registry_login_server" {
  value = module.staging_infrastructure.container_registry_login_server
}

output "staging_postgresql_server_fqdn" {
  value = module.staging_infrastructure.postgresql_server_fqdn
}

output "staging_key_vault_uri" {
  value = module.staging_infrastructure.key_vault_uri
}

output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "container_registry_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "postgresql_server_fqdn" {
  value = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "storage_account_name" {
  value = azurerm_storage_account.sa.name
}

output "service_bus_namespace_name" {
  value = azurerm_servicebus_namespace.sb.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.kv.vault_uri
}

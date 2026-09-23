output "api_url" {
  value = render_web_service.api.url
}

output "acuerdo_pages_url" {
  value = "https://${cloudflare_pages_project.acuerdo.subdomain}"
}

output "dns_records" {
  description = "The records to create at Namecheap by hand when manage_dns is false."
  value = [
    { host = local.api_host, type = "CNAME", value = local.api_target },
    { host = local.acuerdo_host, type = "CNAME", value = local.acuerdo_target },
  ]
}

output "database_external_url" {
  description = "For ingestion from a workstation listed in db_admin_cidrs."
  value       = render_postgres.main.connection_info.external_connection_string
  sensitive   = true
}

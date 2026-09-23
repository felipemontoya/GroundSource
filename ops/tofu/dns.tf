# The two names, at Namecheap. One resource per record: this never reads or
# rewrites the rest of the zone, which holds records that are not this
# project's.

locals {
  api_target     = "${trimprefix(render_web_service.api.url, "https://")}."
  acuerdo_target = "${cloudflare_pages_project.acuerdo.subdomain}."

  # Host part relative to the zone: "groundsource.projects", "acuerdo".
  api_host     = trimsuffix(var.api_domain, ".${var.dns_zone}")
  acuerdo_host = trimsuffix(var.acuerdo_domain, ".${var.dns_zone}")
}

resource "namecheap_domain_host_record" "api" {
  count    = var.manage_dns ? 1 : 0
  domain   = var.dns_zone
  hostname = local.api_host
  type     = "CNAME"
  address  = local.api_target
  ttl      = 1800
}

resource "namecheap_domain_host_record" "acuerdo" {
  count    = var.manage_dns ? 1 : 0
  domain   = var.dns_zone
  hostname = local.acuerdo_host
  type     = "CNAME"
  address  = local.acuerdo_target
  ttl      = 1800
}

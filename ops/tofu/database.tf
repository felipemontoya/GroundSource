# The database, as its own service: the web service can be replaced, moved
# or scaled without touching it. Only the agreement is ingested here; the
# local test-bed documents never are.

resource "render_postgres" "main" {
  name          = "groundsource-db"
  plan          = var.db_plan
  region        = var.region
  version       = "17"
  database_name = "groundsource"
  database_user = "groundsource"
  disk_size_gb  = var.db_disk_gb

  ip_allow_list = [
    for cidr in var.db_admin_cidrs : {
      cidr_block  = cidr
      description = "ingestion workstation"
    }
  ]
}

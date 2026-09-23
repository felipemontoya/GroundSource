# --- secrets: set in .env as TF_VAR_<name>, never in a committed file ----

variable "state_passphrase" {
  description = "Encrypts the state and plans. At least 16 characters."
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "Key of the dedicated OpenAI project for this deployment."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account that owns the Pages projects. Needed only with enable_pages."
  type        = string
  default     = ""
}

variable "enable_pages" {
  description = <<-EOT
    Create the Cloudflare Pages project for the agreement's page. Turn it off
    to deploy the backend alone, before Cloudflare credentials exist; the
    API then accepts only the page's own domain as an origin.
  EOT
  type        = bool
  default     = true
}

# --- where the code comes from -------------------------------------------

variable "github_owner" {
  type    = string
  default = "felipemontoya"
}

variable "github_repo" {
  type    = string
  default = "GroundSource"
}

variable "branch" {
  description = "Branch that production deploys from."
  type        = string
  default     = "main"
}

# --- names ------------------------------------------------------------------

variable "api_domain" {
  type    = string
  default = "groundsource.projects.felipemontoya.co"
}

variable "acuerdo_domain" {
  type    = string
  default = "acuerdo.felipemontoya.co"
}

variable "dns_zone" {
  description = "The Namecheap domain the two names above live under."
  type        = string
  default     = "felipemontoya.co"
}

variable "manage_dns" {
  description = <<-EOT
    Create the CNAME records at Namecheap. Off by default: Namecheap grants
    API access only to accounts that meet its requirements, and only from an
    allowlisted IP. With it off, create the two records by hand from the
    `dns_records` output.
  EOT
  type        = bool
  default     = false
}

# --- sizing and cost --------------------------------------------------------

variable "region" {
  description = "Render region for the web service and the database. Same region keeps them on the private network."
  type        = string
  default     = "virginia"
}

variable "web_plan" {
  type    = string
  default = "starter"
}

variable "db_plan" {
  type    = string
  default = "basic_256mb"
}

variable "db_disk_gb" {
  type    = number
  default = 1
}

variable "db_admin_cidrs" {
  description = <<-EOT
    Addresses allowed to reach the database from outside Render, for running
    ingestion from a workstation. Empty closes external access entirely;
    open it for an ingestion and close it again.
  EOT
  type        = list(string)
  default     = []
}

variable "chat_model" {
  type    = string
  default = "gpt-6-luna"
}

variable "ask_daily_model_limit" {
  description = <<-EOT
    Model calls per UTC day before answers degrade to retrieval-only. The
    default is sized for USD 10/month on gpt-6-luna at USD 0.10 / 0.50 per
    million input / output tokens. Measured in production on 2026-09-23:
    ~7,700 input and ~890 output tokens per question, ~USD 0.0012, so
    USD 10 / 30 days / 0.0012 ≈ 275. One sample; recalibrate from
    `manage.py show_usage` after real traffic, and whenever chat_model
    changes.
  EOT
  type        = number
  default     = 250
}

variable "ask_per_client_limit" {
  description = "Questions per client per window."
  type        = number
  default     = 20
}

variable "ask_per_client_window_seconds" {
  type    = number
  default = 3600
}

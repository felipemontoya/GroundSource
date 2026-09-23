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

variable "chat_price_input_per_mtok" {
  description = "USD per million input tokens for chat_model; change with it."
  type        = number
  default     = 0.10
}

variable "chat_price_output_per_mtok" {
  description = "USD per million output tokens for chat_model; change with it."
  type        = number
  default     = 0.50
}

variable "chat_reasoning_effort" {
  description = "reasoning.effort for chat_model. gpt-6-luna: none, low or medium."
  type        = string
  default     = "low"
}

variable "chat_max_output_tokens" {
  description = <<-EOT
    Ceiling on one answer's output, reasoning included. Generous, so that
    an answer is never cut short: at 1,200 luna's reasoning used it all.
    Typical answers use 250–700. The monthly limits hold the bill.
  EOT
  type        = number
  default     = 8000
}

variable "ask_monthly_soft_limit_usd" {
  description = "Estimated monthly generation spend at which the backend logs a warning."
  type        = number
  default     = 10
}

variable "ask_monthly_hard_limit_usd" {
  description = "Estimated monthly generation spend at which answers become retrieval-only until next month."
  type        = number
  default     = 30
}

variable "ask_daily_model_limit" {
  description = <<-EOT
    Model calls per UTC day before answers degrade to retrieval-only: a
    burst guard, so one busy day cannot spend the month. The monthly hard
    limit is what holds the bill. On gpt-6-luna at effort low a question
    costs ~USD 0.001 (~7,700 input, ~250–700 output tokens, measured
    2026-09-23), and at most ~USD 0.005 if it used the whole output
    ceiling; 1,000 calls is ~USD 1 on a typical day, ~USD 5 at worst.
  EOT
  type        = number
  default     = 1000
}

variable "ask_per_client_limit" {
  description = <<-EOT
    Questions per client per window. High enough for a real conversation
    with the document; it stops scripts, not readers. The monthly limit,
    not this, holds the bill.
  EOT
  type        = number
  default     = 60
}

variable "ask_per_client_window_seconds" {
  type    = number
  default = 3600
}

# The backend: one instance, built from api/Dockerfile — the same image the
# local environment runs.

locals {
  # Every page allowed to call the API. Its own domain and its pages.dev
  # address, so the page works before and after DNS.
  cors_allowed_origins = join(",", concat(
    ["https://${var.acuerdo_domain}"],
    [for project in cloudflare_pages_project.acuerdo : "https://${project.subdomain}"],
  ))
}

resource "render_web_service" "api" {
  name   = "groundsource-api"
  plan   = var.web_plan
  region = var.region

  runtime_source = {
    docker = {
      repo_url        = "https://github.com/${var.github_owner}/${var.github_repo}"
      branch          = var.branch
      context         = "api"
      dockerfile_path = "api/Dockerfile"
      auto_deploy     = true
      # Only changes to the backend redeploy it.
      build_filter = {
        paths = ["api/**"]
      }
    }
  }

  # Migrations are a separate, observable step before the new version takes
  # traffic, not something the server does on start (api/docker-entrypoint.sh).
  pre_deploy_command = "python manage.py migrate --noinput"
  health_check_path  = "/health"

  custom_domains = [{ name = var.api_domain }]

  env_vars = {
    PORT             = { value = "8000" }
    RUN_MIGRATIONS   = { value = "0" }
    DATABASE_URL     = { value = render_postgres.main.connection_info.internal_connection_string }
    DJANGO_DEBUG     = { value = "0" }
    DJANGO_LOG_LEVEL = { value = "INFO" }
    # Generated and kept by Render; it never appears in this repository.
    DJANGO_SECRET_KEY = { generate_value = true }
    # The onrender.com name is added by the backend from RENDER_EXTERNAL_HOSTNAME.
    DJANGO_ALLOWED_HOSTS = { value = var.api_domain }
    # Short to begin with; raise once the domain is known to be right.
    DJANGO_HSTS_SECONDS  = { value = "3600" }
    CORS_ALLOWED_ORIGINS = { value = local.cors_allowed_origins }
    # Render's edge is Cloudflare, which overwrites this header.
    CLIENT_IP_HEADER = { value = "True-Client-IP" }

    OPENAI_API_KEY             = { value = var.openai_api_key }
    EMBEDDING_MODEL            = { value = "text-embedding-3-small" }
    EMBEDDING_DIMENSIONS       = { value = "1536" }
    CHAT_MODEL                 = { value = var.chat_model }
    CHAT_MAX_OUTPUT_TOKENS     = { value = tostring(var.chat_max_output_tokens) }
    CHAT_REASONING_EFFORT      = { value = var.chat_reasoning_effort }
    CHAT_PRICE_INPUT_PER_MTOK  = { value = tostring(var.chat_price_input_per_mtok) }
    CHAT_PRICE_OUTPUT_PER_MTOK = { value = tostring(var.chat_price_output_per_mtok) }
    PIPELINE_VERSION           = { value = "0.1.0" }

    ASK_MONTHLY_SOFT_LIMIT_USD    = { value = tostring(var.ask_monthly_soft_limit_usd) }
    ASK_MONTHLY_HARD_LIMIT_USD    = { value = tostring(var.ask_monthly_hard_limit_usd) }
    ASK_DAILY_MODEL_LIMIT         = { value = tostring(var.ask_daily_model_limit) }
    ASK_PER_CLIENT_LIMIT          = { value = tostring(var.ask_per_client_limit) }
    ASK_PER_CLIENT_WINDOW_SECONDS = { value = tostring(var.ask_per_client_window_seconds) }
  }

  lifecycle {
    # Render generated the value once; the configuration only asks for one
    # to exist. Without this every apply would propose replacing it.
    ignore_changes = [env_vars["DJANGO_SECRET_KEY"]]
  }
}

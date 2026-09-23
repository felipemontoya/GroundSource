# The agreement's page: a static build of pages/acuerdo, built and served
# by Cloudflare Pages from the same repository.

resource "cloudflare_pages_project" "acuerdo" {
  account_id        = var.cloudflare_account_id
  name              = "groundsource-acuerdo"
  production_branch = var.branch

  source = {
    type = "github"
    config = {
      owner                          = var.github_owner
      repo_name                      = var.github_repo
      production_branch              = var.branch
      production_deployments_enabled = true
      preview_deployment_setting     = "none"
      pr_comments_enabled            = false
      # Only changes to this page rebuild it.
      path_includes = ["pages/acuerdo/**"]
    }
  }

  build_config = {
    root_dir        = "pages/acuerdo"
    build_command   = "npm ci && npm run build"
    destination_dir = "dist"
  }

  deployment_configs = {
    production = {
      env_vars = {
        NODE_VERSION      = { type = "plain_text", value = "22" }
        VITE_API_BASE_URL = { type = "plain_text", value = "https://${var.api_domain}" }
      }
    }
  }
}

resource "cloudflare_pages_domain" "acuerdo" {
  account_id   = var.cloudflare_account_id
  project_name = cloudflare_pages_project.acuerdo.name
  name         = var.acuerdo_domain
}

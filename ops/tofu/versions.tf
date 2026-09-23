# GroundSource production infrastructure, as code.
#
# One backend (Render: web service + Postgres), one page per document
# (Cloudflare Pages), and optionally the DNS records that point the
# project's names at them (Namecheap). See ../README.md for the runbook.
#
# Every secret arrives through the environment, from the git-ignored
# ops/tofu/.env (template: .env.example). Nothing secret is written in
# these files: the repository is public.

terraform {
  required_version = "~> 1.12"

  required_providers {
    render = {
      source  = "render-oss/render"
      version = "~> 1.9"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.25"
    }
    namecheap = {
      source  = "namecheap/namecheap"
      version = "~> 2.9"
    }
  }

  # State lives in a Cloudflare R2 bucket through the S3 protocol. The
  # endpoint and credentials come from the environment (AWS_ENDPOINT_URL_S3,
  # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY), so the account id is not
  # written here. The bucket is created by hand once; see ../README.md.
  backend "s3" {
    bucket                      = "groundsource-tofu-state"
    key                         = "production/terraform.tfstate"
    region                      = "auto"
    use_path_style              = true
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
  }

  # State holds the database password and the OpenAI key in clear text
  # unless it is encrypted. It is, before it leaves this machine: a bucket
  # leak then exposes ciphertext only. Losing the passphrase loses the
  # state (not the infrastructure), so keep it in a password manager.
  encryption {
    key_provider "pbkdf2" "passphrase" {
      passphrase = var.state_passphrase
    }
    method "aes_gcm" "default" {
      keys = key_provider.pbkdf2.passphrase
    }
    state {
      method   = method.aes_gcm.default
      enforced = true
    }
    plan {
      method   = method.aes_gcm.default
      enforced = true
    }
  }
}

# Credentials come from RENDER_API_KEY and RENDER_OWNER_ID.
provider "render" {}

# Credentials come from CLOUDFLARE_API_TOKEN.
provider "cloudflare" {}

# Credentials come from NAMECHEAP_USER_NAME, NAMECHEAP_API_USER,
# NAMECHEAP_API_KEY and NAMECHEAP_CLIENT_IP. The provider refuses to start
# without them even when it manages nothing, so with manage_dns off it gets
# placeholders it never uses; null defers to the environment.
provider "namecheap" {
  user_name = var.manage_dns ? null : "unused"
  api_user  = var.manage_dns ? null : "unused"
  api_key   = var.manage_dns ? null : "unused"
}

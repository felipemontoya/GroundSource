"""Django settings for the GroundSource backend.

Deliberately minimal: this is the proof-of-concept skeleton, and the project
has not yet decided how pipeline stages map onto Django apps (see the open
decisions in ../AGENTS.md). Nothing here should be read as settling that.

Every environment-dependent value comes from an environment variable with
the same name locally and in deployment, because `dev/` and `ops/` share a
configuration contract.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Development default only. Deployment must supply DJANGO_SECRET_KEY; the
# check below makes a missing one fail at startup rather than silently
# running production on a known key.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-do-not-deploy")

DEBUG = _env_bool("DJANGO_DEBUG", False)

if not DEBUG and SECRET_KEY == "dev-only-insecure-key-do-not-deploy":
    raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is off")

ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,api")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.postgres",
    "django.contrib.staticfiles",
    "grounding",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "groundsource.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

ASGI_APPLICATION = "groundsource.asgi.application"
WSGI_APPLICATION = "groundsource.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "groundsource"),
        "USER": os.environ.get("POSTGRES_USER", "groundsource"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

# Spanish first, but the interface language is the page's concern, not the
# API's; this only affects Django's own messages.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- model providers -------------------------------------------------------
# Absent keys are not a startup error: ingestion and lexical retrieval work
# without them, and the API reports the degraded state rather than crashing.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))
CHAT_MODEL = os.environ.get("CHAT_MODEL", "gpt-6-luna")
CHAT_MAX_OUTPUT_TOKENS = int(os.environ.get("CHAT_MAX_OUTPUT_TOKENS", "1200"))

# Bumped whenever a change moves offsets or re-shapes the tree. Stored on
# every derived row so that stale artifacts are identifiable rather than
# indistinguishable from fresh ones.
PIPELINE_VERSION = os.environ.get("PIPELINE_VERSION", "0.1.0")

# Where ingested originals are mounted. Read-only by contract.
SOURCES_DIR = Path(os.environ.get("SOURCES_DIR", "/sources"))

# Retrieval shape. Each list is fused by reciprocal rank before the top
# RETRIEVAL_TOP_K survive into the prompt.
RETRIEVAL_CANDIDATES = int(os.environ.get("RETRIEVAL_CANDIDATES", "30"))
RETRIEVAL_TOP_K = int(os.environ.get("RETRIEVAL_TOP_K", "6"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO")},
}

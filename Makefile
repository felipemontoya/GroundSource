# Development and operations shortcuts.
#
# The stack itself is defined in dev/compose.yaml and the deployment in
# ops/tofu/; this file only saves typing the directory and the flags.
#
#   make dev-start    or    make dev start
#   make dev-stop     or    make dev stop
#   make tofu ARGS="plan"

COMPOSE := cd dev && docker compose

.DEFAULT_GOAL := help
.PHONY: help dev dev-start dev-stop tofu

# `make dev start` asks make for two goals, `dev` and `start`. Turn the
# second into a no-op so make does not fail looking for a `start` rule, and
# let `dev` dispatch to `dev-start`.
ifeq (dev,$(firstword $(MAKECMDGOALS)))
DEV_ACTION := $(word 2,$(MAKECMDGOALS))
ifneq (,$(DEV_ACTION))
$(eval $(DEV_ACTION):;@:)
endif
endif

help:
	@echo "make dev-start   build and start db, api and web, and wait until healthy"
	@echo "make dev-stop    stop and remove the containers; the data volumes are kept"
	@echo "make tofu ARGS=\"init|plan|apply|output\"   run OpenTofu on ops/tofu with ops/tofu/.env"

dev:
	@$(MAKE) --no-print-directory $(if $(DEV_ACTION),dev-$(DEV_ACTION),help)

# --build is cheap when nothing changed (every layer is cached) and saves
# chasing a stale image after requirements.txt or package.json moves.
dev-start:
	$(COMPOSE) up -d --build --wait --wait-timeout 300
	@echo ""
	@echo "  page    http://localhost:5173"
	@echo "  acuerdo http://localhost:5174"
	@echo "  api     http://localhost:8000/health"

# `down`, never `down -v`. The volumes hold the ingested documents and
# their embeddings, which cost time and money to regenerate. Wiping them is
# a deliberate reset, documented in dev/README.md, not a way to stop.
dev-stop:
	$(COMPOSE) down

# OpenTofu from its official image, pinned to the version ops/tofu expects,
# so nothing needs installing. Every credential comes from ops/tofu/.env,
# which is git-ignored; the container runs as the calling user so that
# .terraform/ and the lock file stay editable.
TOFU_IMAGE := ghcr.io/opentofu/opentofu:1.12.6

tofu:
	@test -f ops/tofu/.env || { echo "ops/tofu/.env is missing: copy ops/tofu/.env.example and fill it in"; exit 1; }
	docker run --rm -it -u $$(id -u):$$(id -g) -e HOME=/tmp \
		--env-file ops/tofu/.env -v $(CURDIR)/ops/tofu:/w -w /w \
		$(TOFU_IMAGE) $(ARGS)

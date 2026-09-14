# Development shortcuts.
#
# The stack itself is defined in dev/compose.yaml; this file only saves
# typing the directory and the flags.
#
#   make dev-start    or    make dev start
#   make dev-stop     or    make dev stop

COMPOSE := cd dev && docker compose

.DEFAULT_GOAL := help
.PHONY: help dev dev-start dev-stop

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

dev:
	@$(MAKE) --no-print-directory $(if $(DEV_ACTION),dev-$(DEV_ACTION),help)

# --build is cheap when nothing changed (every layer is cached) and saves
# chasing a stale image after requirements.txt or package.json moves.
dev-start:
	$(COMPOSE) up -d --build --wait --wait-timeout 300
	@echo ""
	@echo "  page    http://localhost:5173"
	@echo "  api     http://localhost:8000/health"

# `down`, never `down -v`. The volumes hold the ingested documents and
# their embeddings, which cost time and money to regenerate. Wiping them is
# a deliberate reset, documented in dev/README.md, not a way to stop.
dev-stop:
	$(COMPOSE) down

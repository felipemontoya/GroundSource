# The GroundSource page for the Final Agreement.
#
# Two targets from one file: `dev` runs the Vite dev server with the
# project's own node_modules inside the container, and `build` produces the
# static bundle that a static host serves. `../../ops/` consumes the same
# definition rather than writing a second one (see ../../AGENTS.md).

# --- shared base -----------------------------------------------------------
FROM node:22-alpine AS base
ENV CI=1
WORKDIR /app
COPY package.json package-lock.json* ./
# `npm ci` when a lockfile is present, `npm install` on the very first build
# before one exists. The lockfile is committed, so this normally takes the
# deterministic path.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# --- development server ----------------------------------------------------
FROM base AS dev
COPY . ./
EXPOSE 5174
CMD ["npm", "run", "dev"]

# --- static build ----------------------------------------------------------
FROM base AS build
COPY . ./
RUN npm run build
# The artifact is /app/dist. No server here on purpose: the deployment
# target for the page is a static host, not a container (see
# docs/planning/initial-thinking.md).

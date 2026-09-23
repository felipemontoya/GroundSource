# ADR-0003: Host the backend on Render, the pages on Cloudflare Pages, declared with OpenTofu

- **Status:** Accepted
- **Date:** 2026-09-22

## Context

The proof of concept works locally and is to be published on the open
web. `docs/planning/initial-thinking.md` §11 deferred the platform
decision to this point and gave the shape of the load: one small backend
whose time is spent waiting on the model, a database of tens of megabytes
(29 MB with the agreement ingested), and static pages.

Constraints at the time of deciding:

- One developer pays for everything personally. The project may later
  need outside funding, so the bill has to be predictable and explainable.
- The backend is central and single; the frontends are many — one static
  page per document or audience, each on its own origin.
- The database must be its own service, so that the backend can be
  replaced or scaled without moving the data.
- The repository is public: no secret can live in the tree.
- The infrastructure should be declared as code, in `ops/`.
- The domain `felipemontoya.co` is registered at Namecheap, and its DNS is
  served there.

Prices were checked on 2026-09-22.

## Decision

- **Backend:** a Render web service (Starter, USD 7/month, Virginia),
  built from `api/Dockerfile` — the same image the local stack runs — and
  redeployed on pushes that touch `api/`. Migrations run as Render's
  pre-deploy step.
- **Database:** Render Postgres 17 (Basic-256mb, about USD 6.30/month with
  1 GB), a separate service in the same region, reached over the private
  network. No external access except a temporary allowlist for ingestion.
- **Pages:** Cloudflare Pages, one project per page, built from the
  repository. The first is `pages/acuerdo/` at `acuerdo.felipemontoya.co`;
  the API is `groundsource.projects.felipemontoya.co`.
- **Infrastructure as code:** OpenTofu in `ops/tofu/`, with the official
  Render, Cloudflare and Namecheap providers. State lives in a Cloudflare
  R2 bucket and is encrypted by OpenTofu before upload. Every credential
  comes from the git-ignored `ops/tofu/.env`.
- **Spend:** a dedicated OpenAI project on prepaid credit with no
  auto-recharge, plus a daily cap on model calls in the backend sized for
  USD 10/month.

## Alternatives considered

- **Neon for the database (with Render for compute).** Free up to 100
  CU-hours a month and truly independent of the compute vendor. Rejected
  for now: the cost depends on scale-to-zero behaving, which others report
  it does not always do, and anything that polls the database (a health
  check) keeps it awake all month. Render Postgres costs about USD 6 more
  but is fixed, includes point-in-time recovery, and needs no second
  account. At this size, moving later is a dump and restore of minutes.
- **Railway or Fly.io for compute.** Comparable or cheaper, but billed by
  usage (Railway), or with a managed Postgres starting at USD 38 (Fly).
  Nothing either offers outweighs a fixed bill.
- **Supabase.** The free tier pauses after a week without activity, which
  is wrong for a public site; Pro is USD 25.
- **A VPS running the compose stack.** Cheapest in rent, but the database
  would not be an independent service, and server upkeep would become a
  second project.
- **Managed Kubernetes.** Already judged in §11: the smallest sensible
  cluster costs more than the application needs.
- **Render Blueprint (`render.yaml`) and wrangler instead of OpenTofu.** No
  state to keep, but it covers one vendor each, and the Pages custom
  domain and the DNS records would stay manual. **Terraform** instead of
  OpenTofu: same model, under the BSL rather than an open-source license,
  which fits an Apache-2.0 project worse.

## Consequences

- Expected cost is about USD 23 a month at most: USD 7 web, about USD 6.30
  database, and at most USD 10 of model calls.
- The API is cross-origin for every page, so the backend now carries a
  CORS allowlist (`django-cors-headers`), and adding a page is a change to
  `ops/tofu/` rather than to code.
- The state holds the OpenAI key and the database password. It is
  encrypted, and the passphrase is a single point of failure for the
  state (not for the infrastructure): lose it and the resources have to be
  re-imported.
- Some steps cannot be code: creating accounts, connecting GitHub to Render
  and to Cloudflare, creating the R2 bucket, and — unless Namecheap grants
  API access — the two DNS records. `ops/README.md` lists them.
- Ingestion runs from a workstation against the production database,
  through a temporary IP allowlist. The PDF never reaches the server.
- The per-client limit is counted in one process's memory. Running a second
  instance requires a shared cache first.
- Leaving Render means moving two services and re-pointing one CNAME. The
  image, the environment contract and the data are portable.

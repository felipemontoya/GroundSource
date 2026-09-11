# Initial thinking

**Status: first idea, not a plan.** This is what the project looks like in
one person's head today, written down so it can be argued with. Nothing in it
has been committed to, tried, or measured, and several sections rest on
figures nobody has verified. Treat every heading as a proposal with a
question mark after it.

It is a living document in the sense of `docs/README.md` — expected to be
rewritten as reality intervenes. Ideas that survive contact with code should
leave here and become ADRs; see
[Decisions that want an ADR](#decisions-that-want-an-adr). Ideas that turn out
to be wrong should be deleted outright rather than softened, since the point
of this file is to hold current thinking, not a record of past thinking. That
is what `docs/adrs/` is for.

**Prices and model identifiers below come from a scoping conversation on
2026-09-10 and are carried over as given. Re-verify before they influence
anything that costs money.**

Two companion documents argue with this one from opposite directions:
[`prior-art.md`](prior-art.md) asks which parts of it somebody has already
built, and [`adversarial-review.md`](adversarial-review.md) asks how the
whole thing gets hurt. Both are living documents; when a proposal here moves,
check whether it moves them too.

---

## 1. Where this is going, and what to build against

The release target is the Colombian Final Peace Agreement (Gobierno–FARC,
2016): long enough that almost nobody has read it, cited constantly by people
arguing from summaries, structured cleanly enough to anchor precisely, and
public. It is close to the ideal case for GroundSource.

It is a poor document to *develop* against. 310 pages means slow ingestion
loops, expensive re-indexing while the schema is still moving, and test
failures that take minutes to reproduce. Worse, every bug is politically
legible: debugging retrieval quality on contested text invites arguing about
the answer instead of fixing the pipeline.

So development proceeds against smaller documents and the agreement becomes
the thing the finished pipeline is pointed at.

### The document ladder

**Rung 1 — fixture.** A very small document (a handful of pages, tens of
numbered units) committed to `sources/` and used by the automated tests.
Requirements: public domain, trivially small, cleanly hierarchical, and
stable forever. Parsing, anchoring, and offset mapping are tested against it
on every run, in seconds.

**Rung 2 — development document.** A mid-size document (tens of pages) that
exercises real retrieval: enough units that ranking matters, enough
vocabulary that hybrid search earns its place, small enough to re-ingest in
under a minute. This is what a developer actually talks to while building.

**Rung 3 — target.** The peace agreement, ingested once the pipeline is
stable and the golden set exists.

### Selection criteria

For rungs 1 and 2, in priority order:

1. **Public domain or explicitly redistributable**, since it will be
   committed to a public repository.
2. **Clean numbered hierarchy** — articles, sections, numbered clauses —
   because structure-first chunking is the thing being exercised.
3. **Boring content.** A test fixture whose text provokes argument is a
   distraction; nobody should have opinions about the corpus used to verify
   offset arithmetic.
4. **Same shape as the target**: Spanish, legal register, article hierarchy,
   available as both HTML and PDF so the extraction path can be compared
   against a known-good rendering.
5. **Stable canonical URL**, so deep links do not rot mid-development.

### Candidates

| Rung | Candidate | Why | Against |
|---|---|---|---|
| 1 | Universal Declaration of Human Rights | ~5 pages, 30 numbered articles, official Spanish and English texts, public domain, will never change | Flat structure — no deep nesting to test paths like `3.2.2.1` |
| 1 | A single *decreto* or a short *ley* | Real legal shape, Spanish, nested numbering | Must confirm redistribution and pick a stable source |
| 2 | Colombian Constitution, one *título* | Spanish, deeply nested articles, public, familiar | A whole *título* may still be large; scoping needed |
| 2 | Ley 1581 de 2012 (data protection) | ~15 pages, clean articles, apolitical, Spanish legal register | Confirm canonical PDF location |
| 2 | One *punto* of the agreement (e.g. Punto 1, ~30 pages) | Identical structure, acronyms and extraction quirks to the target; zero surprise when scaling up | Politically charged, which rung 2 was meant to avoid |

Recommended: UDHR as the committed test fixture, one mid-size Spanish
*ley* as the development document, the agreement as the release target. The
last row is worth keeping in view anyway — ingesting a single *punto* late in
development is the cheapest possible rehearsal for the real thing.

**Open:** the specific rung-1 and rung-2 documents are not chosen. Pick them
before the ingestion code is written, since the shape of the fixture shapes
the parser.

### The line that must not blur

Whatever the document, the tool answers **what the text says**, not what has
happened since. For the agreement specifically, it does not answer *"what has
been implemented since 2016"* — that is a different question, with different
sources and a different evidence standard, and answering it would quietly
convert a citation tool into a commentary tool.

This is not only a prompt instruction. It needs to be visible in the
interface, enforced in the system prompt, and present in the evaluation set
as questions the system is expected to decline.

---

## 2. Delivery phases

A first sketch of a split, so that something end-to-end exists early and each
later phase adds one capability to a working system. Each phase names what it deliberately
does not do, because the failure mode here is building the impressive parts
of a pipeline that never answers a question.

### Phase 0 — proof of concept

One rung-1 document, ingested by a script, answerable over HTTP.

- Ingest: fetch, checksum, extract canonical text, parse the numbered
  hierarchy into units with character offsets.
- Store: Postgres with `pgvector` and a `tsvector` index.
- Retrieve: hybrid dense + lexical with rank fusion, top ~6 units.
- Answer: one non-streaming endpoint; quotations sliced from stored spans;
  every citation validated in code against the retrieved set.
- Interface: whatever is cheapest to call — `curl` and a bare page are fine.
- Environment: `docker compose up` brings the whole thing up.

Done when: a question returns an answer in which every claim carries a
citation that resolves to a real unit, no quotation was produced by the
model, and re-ingesting from scratch is a single command.

Not in this phase: streaming, conversation history, a designed interface,
deployment, the target document.

### Phase 1 — a usable web experience

- SSE streaming over ASGI, with the proxy-buffering path exercised locally.
- `Conversation` and `Message` models; chat logic in a transport-agnostic
  service function.
- A real page in `pages/`, Spanish interface.
- Rate limiting per IP and per session, and a hard provider spend cap, both
  before anything is publicly reachable.
- The rung-2 document ingested; a golden set started against it.

Done when: a stranger can use it without explanation, and the bill cannot
run away.

### Phase 2 — the target document

- Ingest the agreement behind the version guard.
- Golden set of 30–50 real questions, including loaded phrasings and
  questions the system must decline.
- Measure citation accuracy; pick the model tier on that evidence.
- Semantic cache of recurring questions with reviewed answers.
- Deploy, with the platform decision made at that point.

Done when: citation accuracy on the golden set is good enough to publish,
and the decline behavior holds under adversarial phrasing.

### Phase 3 — custody and the document viewer

The verification story, built once the tool has earned the traffic that makes
it matter. See the section below.

### Phase 4 — reach

Other channels, an FAQ surface for reviewed answers, possibly a second
document. Each is a separate decision, not an assumed continuation.

---

## 3. Target document: Acuerdo Final de Paz

Applies when rung 3 is reached; none of it blocks earlier work.

- **Use the 24 Nov 2016 version, 310 pages** — the renegotiated text that took
  effect after the plebiscite.
- Canonical PDF:
  `https://www.cancilleria.gov.co/sites/default/files/Fotos2016/12.11_1.2016nuevoacuerdofinal.pdf`
- **Do not use the 24 Aug 2016 version, 297 pages.** Indexing the superseded
  text would turn an anti-misinformation tool into a source of it.

**Ingest-time guard:** assert the page count and the checksum of the fetched
PDF before any preparation runs. A mismatch aborts ingestion loudly rather
than producing a plausible-looking index of the wrong document. The checksum
belongs in a manifest alongside the file in `sources/`, together with the
retrieval URL and date, so a reader can verify independently that the indexed
text is the official one.

Size: roughly 200–280k tokens — too large to stuff into context, which is
what makes retrieval the correct architecture rather than a premature
optimization.

**Redistribution:** the agreement is a public government document, which is
why committing it to `sources/` looks safe here. Confirm this explicitly
before the repository goes public, since the rule in `sources/README.md`
applies to every document, including this one.

---

## 4. Proposed stack

Settled at the project level (see `AGENTS.md`): Python, Django, PostgreSQL.
The rest is proposal.

| Layer | Proposal | Notes |
|---|---|---|
| Backend | Django 5 on **ASGI** (uvicorn or granian), async views | in `api/` |
| Database | PostgreSQL + `pgvector` + `tsvector` (`spanish`) | one database, no separate vector store |
| Frontend | Vite + React + Tailwind, static build | in `pages/`, one subdirectory |
| Hosting (frontend) | Cloudflare Pages or equivalent static host | see `ops/` |
| Streaming | **SSE**, not WebSockets | |
| LLM | provider-abstracted; start cheapest tier | see Model selection |
| Embeddings | one model, pinned, recorded per artifact | |
| Queue | django-tasks or RQ | needed only for the social-channel phase |
| Local environment | **Docker + Docker Compose** | in `dev/`; see Local environment |
| Deployment platform | **deferred** | decided when `ops/` is built; see Hosting |

### Local environment

Docker and Docker Compose, for consistency with the other projects running on
the same machine. One `docker compose up` in `dev/` should bring up Postgres
with `pgvector`, the Django backend on ASGI, and the page's dev server.

What that buys, beyond convenience:

- The `pgvector` and `spanish` full-text configuration is pinned in an image
  rather than being an undocumented step someone performed once.
- The SSE path can be exercised through a proxy locally, which is where the
  buffering gotcha below actually gets caught.
- The container image that runs locally is the same artifact a deployment
  target consumes, whatever that target turns out to be — which is what keeps
  the deferred hosting decision genuinely open.

Conventions: each service's Dockerfile lives next to the code it builds
(`api/Dockerfile`), while `dev/` holds only orchestration and seed data, so
that `ops/` can reference the same images without a second definition
drifting away from the first. Ingested sources and derived artifacts are
mounted, not baked into images.

### Rejected, with reasons worth keeping

- **Static hosts for the backend.** GitHub Pages and Cloudflare Pages serve
  static files; they cannot run Django. They remain candidates for `pages/`.
- **Cloudflare Workers Python.** Beta, and no workable Django/ORM story
  against Postgres.
- **Django Channels + Redis.** Token streaming is unidirectional. Async views
  with `StreamingHttpResponse` over ASGI cover it with no extra
  infrastructure. Revisit only if something genuinely bidirectional appears.

### Deployment gotcha

Disable proxy buffering — nginx `proxy_buffering off`, and the
`X-Accel-Buffering: no` response header — or SSE chunks accumulate and the
whole answer arrives at once. Belongs in `ops/` configuration and in a
`dev/` environment that reproduces the same path, or it will be discovered in
production.

---

## 5. Ingestion and preparation

One-time, idempotent, and scripted: a single reproducible command in `api/`,
never a notebook. Re-indexing must be repeatable by someone who did not write
it.

**Chunk by document structure, not by fixed token windows.** The agreement
has a clean numbered hierarchy (Punto 1–6, then 3.2.2.1 and deeper), which
is exactly the structural tree the project's vocabulary calls *units*.

Per-chunk metadata, in the terms this repo uses:

| Proposal | Repo vocabulary | Notes |
|---|---|---|
| `punto` (1–6) | unit path, level 1 | |
| `ruta_seccion` (`3.2.2.1`) | unit path, full | the anchor's human-readable part |
| `titulo` | unit title | |
| `pagina` | locator in the original | drives the `#page=N` deep link |
| `texto` | span text | sliced from the source, never model-authored |

Rules:

- Target ~500–800 tokens per chunk.
- Repeat the section heading at the start of every chunk so the embedding
  captures topical context.
- Expected scale: ~1,500 chunks, ~9 MB of vectors. That fits in Postgres
  cache on any instance; no HNSW tuning required at this size.

### Reconciling with the anchoring invariant

`AGENTS.md` requires the chain *original bytes → character offsets →
structural anchor → quoted span*. The scoping above stops at page plus
section path, which is enough to build a link but **not** enough to prove a
quotation was sliced rather than generated.

Proposal: keep `ruta_seccion` and `pagina` as the human-facing locator, and
additionally store character offsets into a canonical extracted text, with
the offset map back to the PDF retained. Quotations are then produced by
slicing that canonical text at recorded offsets. This is the difference
between a citation a user can click and a citation the system can verify.

Open: PDF text extraction rarely yields stable offsets for free. Deciding the
extraction tool is effectively deciding how trustworthy the anchors are.

### The extraction stage is not hand-rolled, and not yet decided

Turning a PDF into a structured tree with usable offsets is the hardest part
of this pipeline and the part most thoroughly solved by other people. The
working assumption is therefore a library rather than a bespoke parser; the
candidates and the criteria are in [`prior-art.md`](prior-art.md) §4.2.

The friction: those libraries recover structure with layout models, so
"parsing" becomes a model-backed pass, while invariant 7 in `AGENTS.md`
places parsing on the deterministic side of the line. Two constraints shrink
that problem to something manageable.

**The input is narrow.** Born-digital, cleanly numbered legal text with a
real text layer. No OCR, no scans, no recovered columns. That is the case
layout models handle most confidently, and it is also the case where plain
rules over the numbering may do most of the work unaided.

**The parse runs once.** For a released document, extraction happens a single
time and its output is stored as a checksummed artifact that the database
loads rather than owns. Anchor stability then comes from never re-deriving
the tree, which is a stronger guarantee than determinism: determinism
promises that a second run agrees with the first, while freezing the artifact
means there is no second run. Three rules keep that true — ingest loads an
existing artifact for a given source checksum and pipeline version unless
explicitly told to re-derive; a re-parse produces a new version with a diff
that a human reviews, never a silent replacement; and the artifact lives
outside the database, so that an empty database is a restore rather than a
re-derivation. Development is unaffected: the fixture and the development
document are re-parsed freely, and the freeze applies only to a document that
has been published.

A pleasant side effect is that the heavy document-AI dependency belongs to
the ingestion path only. Nothing in the serving image needs it, which is most
of what made it objectionable under the dependency rule in `AGENTS.md`.

**What cannot be settled from a desk.** Whether a layout model earns its
place over regexes across the numbering, and how much either approach
actually recovers, depends on what comes out of a real document. The decision
is empirical: run both against a rung-1 and a rung-2 candidate, look at the
tree and the offsets, and choose on the evidence. Until that has been done,
treat this section as the shape of the stage rather than a choice about it.

---

## 6. Source custody and the document viewer

**Not an early feature.** Phase 3. Recorded now because it changes how
ingestion stores things, and retrofitting custody onto a pipeline that never
tracked provenance is expensive.

The problem: a tool whose whole claim is *"go read the original"* is only as
credible as the reader's ability to confirm that the original really is the
original. Right now that rests on a government URL staying alive and serving
the same bytes forever, which is not a safe assumption.

### Acquisition and verification

- Fetch from the official source, once, and record the retrieval URL, the
  timestamp, the HTTP response headers, the byte size, and a SHA-256 digest.
- Store that record as a manifest in `sources/`, committed alongside the file
  so the digest is in version history and any later substitution is visible
  as a diff.
- Publish the digest in the interface with the exact command a reader can run
  to check it themselves. Verification a user cannot perform independently is
  decoration.
- Assert the digest at ingest time, and assert the document-specific guards
  on top of it — for the agreement, the 310-page check.

### Hosting the bytes locally

Serve the original from storage this project controls, so citation links
never depend on a government URL surviving a website redesign. Always show
both links: the local copy, and the official source that the digest was taken
from. The local copy is for reading; the official one is what makes the
local copy checkable.

This has a cost worth stating: mirroring means the project is redistributing
the document, so the redistribution check in `sources/README.md` is load
bearing, not a formality.

### A viewer better than `#page=N`

PDF deep links are the weakest part of the citation chain. `#page=143` lands
on a page, not a passage; behavior differs across viewers; nothing is
highlighted; and on a phone the experience is bad enough that most readers
will not verify at all — which defeats the purpose.

What the citation chain actually needs: a link that opens the document at the
exact quoted span, highlights it, and shows the surrounding context.

Options, roughly in order of preference:

1. **Generated HTML rendition.** Render the parsed tree at ingest time, one
   anchor per unit (`#3.2.2.1`), with the exact span highlighted via character
   offsets. Best linking, accessibility, and mobile behavior. Must be
   generated from the same canonical text the quotations are sliced from, so
   it is provably the document rather than a transcription of it. Downside:
   it does not *look* like the official artifact, which matters for a
   document people distrust.
2. **PDF.js with text-layer highlighting.** Keeps visual fidelity — the
   reader sees the real document — at the cost of mapping offsets onto the
   PDF text layer, which is where extraction inaccuracies become visible.
3. **Page images with an overlay.** Maximum fidelity, worst accessibility and
   search; a fallback for pages where extraction is unreliable.

Likely answer: the HTML rendition as the primary reading surface, with a
per-unit link into the PDF page for anyone who wants the artifact itself.
Both are anchored to the same offsets, so they cannot disagree.

Whatever is built, the rendition is derived data: regenerable from the source
plus the pipeline, never hand-corrected. A hand-edited rendition is a second
source of truth and quietly breaks the one promise the product makes.

---

## 7. Retrieval: hybrid, not vector-only

The text is dense with acronyms users quote verbatim — JEP, PNIS, ZVTN,
ECOMÚN, SIVJRNR. Dense embeddings handle these poorly; a user typing "ZVTN"
wants lexical matching.

- **Dense:** `pgvector`, cosine similarity.
- **Sparse:** Postgres full-text search, `spanish` dictionary, `tsvector` with
  a GIN index.
- **Fusion:** Reciprocal Rank Fusion.
- Return roughly the top 6 chunks.

Both halves live in the same database, which is the main reason the
"no separate vector store" choice is worth defending: one query planner, one
backup, one consistency story.

---

### Language: Spanish first, not Spanish only

The audience is Colombian and the documents are in Spanish, so Spanish is the
default everywhere it matters: the `spanish` full-text dictionary, Spanish
prompts, a Spanish interface, and an evaluation set written in Spanish with
the phrasings real users type.

Other languages should stay possible, and staying possible is cheap if two
rules hold from the start:

- **Language is a property of the document, not of the codebase.** Store it
  on the document and select the full-text configuration from that value.
  No `'spanish'` literal inline in a query.
- **Interface and prompt strings live outside the components that use them,**
  keyed by language, even while exactly one language exists.

That is the whole investment. Everything else — multilingual embeddings,
per-language evaluation sets, a language switch — can wait until a
non-Spanish document actually appears.

One rule is not deferrable, because it belongs to the grounding contract:
**quotations are always in the document's own language.** If a question
arrives in another language, the answer may be written in that language, but
the quoted span is reproduced verbatim in the original. Any translation is
labeled as interpretation and visually separated from the quotation — a
translated quote presented as the text is exactly the kind of murk this
project exists to remove.

---

## 8. Grounding and citation validation

This section is the product. The rest is plumbing.

- Answers cite as `Punto 5.1.2, pág. 143`, deep-linked to the official PDF
  with `#page=143`, so verification happens **outside** the tool.
- **Validate every citation in code.** Each section reference the model emits
  must match a chunk actually present in the retrieved set; otherwise the
  response is rejected and regenerated. Cheap models hallucinate section
  numbers, and this check is the single highest-value guardrail in the
  system.
- Quotations are sliced from stored spans, never reproduced by the model
  (`AGENTS.md`, invariant 4).
- When the retrieved chunks do not support an answer, the model says so
  rather than filling the gap from parametric knowledge.
- Neutral register throughout: the bot quotes the document, it does not argue
  about the agreement's merits.
- Where a passage genuinely admits competing readings, surface both with the
  text each rests on, per the grounding contract in `README.md`.

---

## 9. Model selection: measure, don't assume

Build a **golden set of 30–50 real questions** with the expected correct
section before choosing a model. Include:

- The loaded questions people actually ask — jail time, impunity, political
  eligibility, money.
- Adversarial phrasings that presuppose a false claim.
- Questions the system must **decline**: implementation status, opinion,
  prediction.

Measure citation accuracy, not answer fluency. Citation discipline is exactly
what the cheapest models fail at. If the cheapest tier fails the golden set,
step up — the cost delta is trivial next to a peace-agreement bot inventing
section numbers.

The earlier scoping proposed OpenAI (`gpt-5-nano`, falling back to
`gpt-5.6-luna`) with `text-embedding-3-small` for embeddings. Provider
selection remains listed as open in `AGENTS.md`, so treat those as the
starting candidates and keep the provider behind an interface: the evaluation
harness is what should decide, and swapping providers must not touch
retrieval or citation code.

Indexing embeddings for 310 pages costs cents, once. Re-embedding on a model
change is therefore not a constraint worth designing around.

---

## 10. Conversation model: other channels without building them yet

- `Conversation` and `Message` models with a `channel` field (`web`, and
  later others).
- **All chat logic lives in a service-layer function that knows nothing about
  HTTP.** The web view and any future webhook both call it. This is also what
  keeps `pages/` from becoming a second source of truth.
- A future webhook enqueues rather than answering inline, since social
  platforms require a fast acknowledgement.

**Budget warning:** Twitter/X write access is no longer free; the tier that
allows posting starts in the hundreds of USD per month. That phase is a real
budget decision, not a weekend feature. Other channels (Mastodon, WhatsApp,
an embeddable widget) may deliver the same reach for less and deserve
comparison before that bill is accepted.

---

## 11. Hosting and scale

**The platform decision is deferred to the `ops/` phase.** What follows is
the analysis that should feed it, not a choice.

### The shape of the load

The bottleneck is **not CPU or RAM**. Each turn is one embedding call
(~50 ms), one database query (~10 ms), then 5–15 seconds waiting on the LLM.
That wait is pure I/O: async Django holds hundreds of concurrent streams in
1–2 GB. Sizing this system by RAM overprovisions it by roughly 10x.

- **Phase 1 (0–1,000 conversations/day):** one 2 GB instance plus a small
  Postgres. ~$25–40/month all in.
- **Phase 2 (1,000–20,000/day):** two instances behind a load balancer, 4 GB
  database. ~$70–120/month hosting plus $30–300 LLM.
- **Phase 3 (viral spike):** the scenario that actually breaks things. A
  single share can 100x traffic in minutes.

### Candidate platforms

| Option | Phase 1 cost | Notes |
|---|---|---|
| PaaS (Render, Fly, Railway) | ~$12–35/mo | Load balancer and TLS included; least configuration |
| AWS (ECS/EC2 + RDS) | ~$70–100/mo | Gap is ALB, NAT, snapshots and configuration hours — not compute price |
| Managed Kubernetes (EKS/GKE/DOKS) | control plane $0–75/mo + nodes | Familiar ground, but the smallest sensible cluster costs more than the app needs |
| Self-hosted Kubernetes | cheap in rent, expensive in attention | Cluster upkeep becomes a second project |

Kubernetes is the most familiar option here and the natural destination if
this ever grows past one service, but running a cluster for a single Django
app plus a static site means maintaining infrastructure that is not the point
of the project right now. The reasonable position is to stay deployable to it
without paying for it yet.

### What that implies for code, today

Keep the application platform-agnostic so the decision stays cheap:

- Configuration through environment variables only; no platform-specific
  APIs in application code.
- The container image is the deployment unit, buildable and runnable
  identically in `dev/` and in whatever `ops/` selects.
- Postgres reached by URL, with no assumptions about who operates it.
- Nothing stateful on local disk that a second replica would not see.

**Database:** prefer fixed pricing (Render Basic, Supabase, DigitalOcean
managed ~$15). Neon's scale-to-zero billing suits bursty workloads; a public
chatbot never sleeps, so 0.5 CU always-on lands near $38/month — worse and
less predictable. Revisit only if traffic proves genuinely sporadic.

Phase 3 deserves a written plan before launch, not after: what degrades
first, what the cache absorbs, and what the tool says when it is over budget.
A static "too much traffic, here is the document" page is a better failure
mode than a card-draining one.

---

## 12. Cost guardrails: build before launch

Per-turn cost at ~5k input / ~400 output tokens, using the figures carried
over from the earlier scoping:

- cheapest tier ($0.05/$0.40 per 1M): ~$0.0004/turn → ~$4 per 10k turns
- fallback tier ($0.20/$1.20 per 1M): ~$0.0015/turn → ~$15 per 10k turns

At small scale the LLM is not the dominant cost; hosting is. That inverts
only under a spike — which is precisely when nobody is watching the console.

In priority order:

1. **A hard monthly spend limit at the provider.** The backstop that turns a
   catastrophe into an outage.
2. **Rate limiting** per IP, per session, and per channel account, from the
   first deploy. A public LLM endpoint without limits is a card-draining
   vector.
3. **Semantic cache** of the top ~50 recurring questions with human-reviewed
   answers. Most traffic will be the same handful of doubts; this cuts cost
   and raises answer consistency at the same time.

**The provider key never reaches the frontend.** All model calls proxy
through Django. `pages/` ships as static files to untrusted browsers.

---

## 13. What generalizes and what does not

Worth tracking, since GroundSource is meant to outlive this document.

**General to the product:**

- Structure-first chunking with anchors into the original.
- Hybrid dense + lexical retrieval with rank fusion.
- Code-side citation validation against the retrieved set.
- Abstention when the retrieved text does not support an answer.
- Golden-set evaluation measuring citation accuracy.
- Service-layer chat logic independent of transport.
- Source custody: checksum at ingest, a manifest in version history, a
  locally hosted copy shown alongside the official one.
- An anchor-precise reading surface, rather than whatever deep linking the
  original format happens to allow.
- Language as a property of the document: quotations always in the
  document's own language, translation labeled as interpretation.

**Specific to this document:**

- The `spanish` full-text dictionary as the *default*, and Spanish prompts,
  interface and evaluation set — the starting point, not a constraint baked
  into the schema.
- The `punto` / `ruta_seccion` hierarchy and the `#page=N` PDF deep link.
- The version guard on the 24 Nov 2016 text.
- The acronym set that motivates lexical retrieval.

The seam between these two is where the code should be split: a document
profile that carries the specifics, and a pipeline that carries the rest.
Getting that seam roughly right now is cheaper than extracting it later, but
it should not be over-engineered for a second document that does not exist.

---

## 14. Decisions that want an ADR

Candidates to promote out of this document once agreed, each currently a
proposal:

- ASGI plus SSE for streaming, and the rejection of Channels/WebSockets.
- Postgres as the single store, `pgvector` instead of a dedicated vector
  database.
- Hybrid retrieval with Reciprocal Rank Fusion.
- Anchoring strategy: character offsets into canonical text plus a page map.
- The extraction stage: which library (or none) parses the PDF, and the
  parse-once-and-freeze model that makes the choice survivable — see
  [`prior-art.md`](prior-art.md) §4.2.
- How far the unit model borrows from Akoma Ntoso: its element vocabulary,
  its identifier discipline, or neither — see [`prior-art.md`](prior-art.md)
  §4.1.
- LLM provider and the interface boundary that keeps it swappable.
- The document ladder: which fixture and development documents the pipeline
  is built against, and why the target is not one of them.
- Docker Compose as the local environment contract.
- The deployment platform, once `ops/` forces the question, including the
  conditions under which Kubernetes becomes worth its upkeep.
- Source custody: digest recorded at ingest, manifest committed, original
  mirrored locally and shown next to the official link.
- The reading surface: generated HTML rendition, PDF.js with a highlighted
  text layer, or both.
- Spanish-first with language carried per document, and the rule that
  quotations are never translated in place.

---

## 15. Open questions

Carried over:

- Whether to expose the semantic cache's reviewed answers as a browsable FAQ
  page — cheap, and plausibly high-value for the misinformation goal.
- Retention policy for stored conversations, and whether public transcripts
  are an asset or a liability.

Raised by this reshaping:

- Which documents occupy rungs 1 and 2 of the ladder. Needed before the
  ingestion code is written.
- Whether the fixture document's parsed tree is committed as a golden file,
  so parser regressions show up as a diff rather than as a failing assertion
  with no context.

- How character offsets survive PDF extraction, and which extractor makes
  anchors verifiable rather than merely plausible. Not answerable on paper:
  it needs a real document run through the candidates and the resulting tree
  inspected.
- What happens when the one frozen parse turns out to be wrong — a reviewed
  patch layer kept as a separate artifact, or re-parsing as the only
  permitted fix. Invariant 3 forbids hand-editing derived data, and a frozen
  tree is exactly the thing someone will want to hand-edit.
- Whether repository documentation stays English while the product is
  Spanish, and whether that split holds as contributors arrive.
- Which extraction path the HTML rendition is generated from, and how its
  fidelity to the official PDF is demonstrated rather than asserted.
- Whether the checksum and its verification command are surfaced in the
  interface itself or only in the repository.
- What the tool shows when it declines — a dead end reads as evasion, so
  declining well probably means routing the reader to the nearest relevant
  text anyway.
- Whether abuse of a politically charged public bot (coordinated adversarial
  prompting, screenshot farming of out-of-context answers) needs a mitigation
  beyond rate limiting.

# planning

Living documents: designs, roadmaps, interface sketches, open questions.

Unlike `../adrs/`, everything here is expected to drift and be corrected.
When code changes in a way that contradicts a document here, update the
document as part of the same change. A stale design document is worse than
no design document, because it will be trusted.

Suggested naming: `kebab-case-topic.md`. Date-stamp only documents that are
genuinely a snapshot (a review, a status report).

## What is here

- [`initial-thinking.md`](initial-thinking.md) — the plan: what to build,
  in what order, against which documents.
- [`adversarial-review.md`](adversarial-review.md) — the same plan read by
  people who want the project to fail. A threat model, not a verdict.
- [`prior-art.md`](prior-art.md) — what already exists in the open-source
  world, what to borrow, and what is left to build.

They cross-reference each other on purpose. A change to one that contradicts
another is not finished until both are updated.

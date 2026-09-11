# Architecture Decision Records

## Rules

- One decision per record. Filename `NNNN-kebab-case-title.md`, numbered
  sequentially from `0001`, never reused.
- **Records are immutable once accepted.** Do not rewrite history to match
  the present. The only edit permitted on an accepted record is changing its
  `Status` line to `Superseded by ADR-NNNN`.
- A reversed or revised decision becomes a new ADR that names what it
  supersedes, and the old record's status is updated to point at it.
- Write in the past/present tense of the moment of deciding. Include the
  alternatives that were considered and why they lost — that is usually the
  part that saves someone months later.

## Status values

- `Proposed` — written, not yet agreed.
- `Accepted` — in force. From here the record is immutable.
- `Superseded by ADR-NNNN` — replaced; kept for the record.
- `Rejected` — considered and declined. Kept, because "we thought about
  that and said no" is worth knowing.

## Template

Copy `0000-template.md`.

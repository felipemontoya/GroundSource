# ADR-0002: Apache License 2.0

- **Status:** Accepted
- **Date:** 2026-09-13

## Context

The repository is intended to become public, and until now carried no
license at all. Code published without a license is not open source: the
default is exclusive copyright, so nobody may copy, modify, or deploy it.
That silence was listed as an open decision in `README.md` and `AGENTS.md`.

Two things about this project shape the choice.

First, the repository will contain third-party material. `sources/` holds
original documents — government texts, laws, agreements — that are not the
project's to relicense. Whatever license covers the code has to be one that
can be stated as covering the code *only*, without implying a claim over
the documents beside it.

Second, the project's argument is about verifiability. A tool that asks
people to trust it because its output can be traced is in a weak position
if the tool itself cannot be inspected, forked, or run independently. An
audit that cannot end in "so run it yourself" is incomplete.

The project also expects outside contributions eventually, and expects to
be forked for other documents in other jurisdictions — that generalization
is a stated goal, not an accident.

## Decision

The code and documentation in this repository are licensed under the
Apache License, Version 2.0. The full text is in `LICENSE`, and `NOTICE`
records the scope limit: the license covers the code, not the documents
under `sources/`.

Copyright is attributed to "The GroundSource Authors" rather than to a
named individual or company, so that contributions accumulate without the
notice needing to be rewritten.

## Alternatives considered

- **MIT.** The obvious lightweight choice, and a real contender. Rejected
  for one missing clause: Apache 2.0 grants patent rights explicitly and
  terminates that grant for anyone who sues over patents. MIT is silent on
  patents, which leaves an ambiguity that a downstream adopter in an
  institutional setting has to resolve with a lawyer instead of a file.
- **BSD-3-Clause.** Same gap as MIT, with a non-endorsement clause that
  adds nothing here.
- **AGPL-3.0.** Attractive on principle: it would force anyone running a
  modified GroundSource as a network service to publish their changes,
  which speaks directly to a tool whose credibility rests on being
  inspectable. Rejected because it cuts against the goal of being adopted.
  A newsroom, an electoral authority, or a university that wants to run
  this for its own document is exactly the adopter this project wants, and
  many such organizations decline AGPL software by policy. Forcing them to
  choose between their policy and the tool loses more transparency than the
  copyleft would win.
- **Apache 2.0 with a CLA.** Rejected as premature. A contributor licence
  agreement is machinery for a project with contributors and a relicensing
  strategy; this has neither.
- **No license, published anyway.** Rejected: it is the current state by
  omission rather than by choice, and it makes the repository legally
  unusable while looking open.

## Consequences

- Anyone may run, modify, fork, and deploy this, including commercially,
  without asking. That is the point.
- Modified versions must carry prominent notices of what changed (Apache
  2.0 §4(b)), which fits a project that argues for traceability.
- A fork may be closed-source and may be used to produce unfaithful,
  badly-grounded, or deliberately slanted answers under a similar name.
  The license does not prevent this; only the trademark-like force of the
  project's name and its published evaluation results do, and neither
  exists yet. This is the accepted cost of the permissive choice.
- `NOTICE` is now load-bearing. Apache 2.0 §4(d) requires redistributors to
  carry it, which is what makes the `sources/` scope limit travel with the
  code. Deleting or emptying it would quietly drop that.
- Every source document added to `sources/` must still be checked for
  redistribution rights independently. The project's license says nothing
  about them, by design.
- New files do not need per-file license headers. The appendix form in
  `LICENSE` is available if one is ever wanted, but a `LICENSE` and
  `NOTICE` at the root are sufficient.

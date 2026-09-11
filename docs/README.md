# docs

Two kinds of documents live here, and they follow opposite rules.

## `adrs/` — immutable

Architecture Decision Records. An ADR captures one decision, the context it
was made in, and its consequences, as of the day it was written. Once a
record is accepted it is **not edited to reflect later reality**. When a
decision changes, write a new ADR and mark the old one superseded. The value
of an ADR is that it tells you what was believed at the time, so amending it
destroys the thing it exists for.

See `adrs/README.md` for numbering, status values, and the template.

## `planning/` — living

Planning notes, design documents, roadmaps, open questions, interface
sketches. These are expected to change as the code changes, and keeping them
current is part of the work: when an implementation diverges from a design
document here, update the document in the same change.

## Which one am I writing?

- A choice with alternatives that were weighed, which future readers will
  wonder about → ADR.
- A description of how something works or will work, which should track the
  code → planning.

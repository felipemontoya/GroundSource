# Prior art: what already exists, and what to take from it

**Status: survey, 2026-09-10.** A search of the open-source landscape for
projects that already do what `initial-thinking.md` proposes, in whole or in
part. It answers one question — *is this already built?* — and then argues
for two changes to the plan that follow from the answer.

This is a living document in the sense of `README.md` for this directory.
Projects move: stars, maintenance and feature sets below are as of the date
in the status line and should be re-checked before any of them is adopted.

---

## 0. The verdict

**Nothing duplicates GroundSource. Several projects duplicate parts of it,
and the parts they duplicate are the parts `initial-thinking.md` already
calls plumbing.**

Specifically: hybrid dense + lexical retrieval with rank fusion, chunking a
legal text by its articles, grounded-citation prompting, a PDF viewer that
highlights the cited passage, and refusal when nothing relevant is retrieved
are all available off the shelf, several times over. Phase 0 and much of
Phase 1 are commodity work.

What no project found here does is make the chain

```
original bytes → character offsets → structural anchor → quoted span
```

the product rather than an implementation detail. Nothing found slices
quotations from recorded offsets as a hard rule, validates emitted citations
in code against the retrieved set, records custody of the source so a reader
can verify the indexed bytes independently, or evaluates declining as a
first-class behaviour. That cluster — not the retrieval stack — is where the
remaining original work is.

---

## 1. Nearest whole products

| Project | License | Stack | What it already does | What it does not do |
|---|---|---|---|---|
| [kotaemon](https://github.com/Cinnamon/kotaemon) | permissive (confirm) | Gradio, pluggable vector stores | In-browser PDF viewer with highlighted citations and relevance scores; hybrid full-text + vector retrieval with reranking; multi-provider LLM | Citations are chunk-level previews, not spans sliced at recorded offsets; no citation validation; no custody; no structure-first legal parsing |
| [RAGFlow](https://github.com/infiniflow/ragflow) | Apache-2 (confirm) | Own platform, heavy | Layout-aware parsing of complex PDFs, tables and scans; "traceable citations"; large and active | A platform to operate, with its own opinions about everything; nothing of the Django/Postgres plan survives adopting it |
| [OpenContracts](https://github.com/JSv4/OpenContracts) | MIT | **Django + React + PostgreSQL + pgvector + Celery** | Span-level annotation anchored to PDF coordinates via AllenAI's PAWLS format; character-offset annotations for DOCX; agents required to cite the span they drew from; legal domain; MCP server | Built for corpus annotation and extraction by legal teams, not a public single-document chatbot; no custody story; adopting the span layer means adopting its data model, GraphQL API and permission system |
| [verbatim-rag](https://github.com/KRLabsOrg/verbatim-rag) | check | Python library | Extractive RAG: the model classifies which existing spans answer a question instead of generating prose — invariant 4 turned into an architecture | A component, not a product; no anchoring into an original artifact, no interface |
| [PaperQA2](https://github.com/future-house/paper-qa) | Apache-2 (confirm) | Python library | High-accuracy grounded citation QA, contextual summarisation before generation, strong evaluation record | Scientific literature across many papers; no reading surface anchored to the original; different unit of work |

**OpenContracts is the stack twin** and the only serious "fork it" candidate.
It is the one project that has already solved the problem this repo calls
anchoring, in the same language and framework, under a license that permits
reuse. See §5 for why the recommendation is still to borrow rather than
fork.

---

## 2. Nearest in intent

- **[LexIA Colombia](https://github.com/jost9804/lexia-colombia)** — Colombian
  legal RAG over the Código Sustantivo del Trabajo. Chunks *por artículo*,
  hybrid semantic + lexical retrieval with Reciprocal Rank Fusion, refuses
  with *"no encuentro fuente"* when nothing supports an answer, evaluated on
  recall@k and faithfulness. Single author, Streamlit + Supabase free tiers,
  no license stated. Not a base to build on, but useful evidence: the
  retrieval design proposed in `initial-thinking.md` §7 already works in
  Spanish legal register, on Colombian material, at demo quality.

- **[Constitucion.ai](https://www.constitucion.ai/)** (Universidad Central de
  Chile, 2023) — a chatbot over Chile's proposed constitution during the
  plebiscite, with its knowledge base published on GitHub. The closest match
  to the civic thesis in `README.md`. Explanation-oriented rather than
  quotation-oriented: it helps a reader understand the text, which is a
  different promise from showing them the text.

---

## 3. Searched for, not found

- **Anything over the Colombian Final Peace Agreement.** The Biblioteca
  Abierta del Proceso de Paz (BAPP) exists as a document archive, not as a
  queryable grounded agent. Searched in Spanish; the absence here is the
  strongest of the three.
- **Source custody as a feature.** Checksum recorded at ingest, manifest in
  version history, the original mirrored and shown beside the official link,
  and a verification command the reader can run. The idea circulates as
  advice (OWASP's RAG Security cheat sheet, scattered provenance write-ups)
  and as a commercial product, but no open-source implementation surfaced.
- **Evaluation sets that score declining.** Golden sets in this space measure
  faithfulness and retrieval recall. None found treats *questions the system
  must refuse* as a scored category, which is what `initial-thinking.md` §9
  proposes.

Absence of a search result is weak evidence. See §8.

---

## 4. Two things this survey changes in the plan

### 4.1 Adopt Akoma Ntoso as the structural vocabulary

[Akoma Ntoso](https://en.wikipedia.org/wiki/Akoma_Ntoso) is an OASIS open
standard (LegalDocML) for marking up legislative and judicial documents in
XML. It formalises exactly the tree this repo calls *units* — title,
chapter, article, paragraph, item, sub-item — and it is accompanied by
identifier frameworks, the European Legislation Identifier and LexML's URN
scheme, that give persistent identifiers to documents *and to fragments
within them*.

Why this matters here, beyond tidiness:

- **It is the anchor problem, already solved by people who had to solve it.**
  `AGENTS.md` states that anchors are part of the public API and must not
  change silently between runs. Akoma Ntoso separates an element's evolving
  identifier from its permanent one precisely because legislative text is
  renumbered while references to it must survive. That distinction is worth
  copying whether or not the XML is. *(Confirm the exact `eId`/`wId`
  semantics against the specification before relying on this.)*
- **It supplies naming, so the project does not invent one.** `punto`,
  `ruta_seccion` and the rest of §5 of `initial-thinking.md` are ad-hoc terms
  for concepts with standard names. Using the standard's vocabulary in the
  schema makes the document profile seam of §13 sharper and makes a second
  document cheaper.
- **It is an interoperability hedge.** A parsed tree expressible as Akoma
  Ntoso can be consumed by tooling nobody in this project has to write, and
  can be checked by someone who does not trust the parser.

What is *not* proposed:

- Not requiring Akoma Ntoso as an **input** format. Nobody publishes the
  Acuerdo Final in it; the canonical artifact is a PDF, and that does not
  change. Akoma Ntoso would be a target representation the parser produces,
  not a source it consumes.
- Not requiring schema-valid XML end to end. The cheap version is borrowing
  the element vocabulary and the identifier discipline for the internal unit
  model. Emitting real Akoma Ntoso is a later, separable step, and should be
  justified by an actual consumer rather than by standards-compliance as an
  end in itself.

The decision to record: **which parts of the standard the unit model
adopts** — vocabulary only, vocabulary plus identifier scheme, or full
serialisation — and the reasons for stopping where it stops.

### 4.2 Use an ingestion library rather than hand-rolling extraction

`initial-thinking.md` §5 already notes that "deciding the extraction tool is
effectively deciding how trustworthy the anchors are", and §15 leaves it
open. This survey sharpens it into a recommendation: **do not write the
PDF-to-structured-text stage from scratch.** It is the single hardest part
of the pipeline, it is where the offset invariant lives or dies, and it is
thoroughly addressed by existing work — [Docling](https://docling-project.github.io/docling/concepts/chunking/)
(structure-aware parsing with per-item provenance), [Chonkie](https://github.com/feyninc/chonkie)
(chunking strategies), and the PAWLS format that OpenContracts standardises
on for text-to-coordinate mapping.

Selection criteria, in priority order, derived from the invariants rather
than from feature lists:

1. **Offset provenance.** Does each extracted item carry a character range
   into a canonical text, or at minimum a page plus bounding box that a
   character range can be derived from and tested against? A library that
   returns clean text without provenance is disqualified regardless of how
   good the text is — invariant 2.
2. **Determinism.** Modern layout parsers are ML models. Invariant 7 requires
   parsing and anchoring to be deterministic and tested as such. Either the
   model version is pinned and the output proves reproducible on fixed
   input, or that invariant needs rewording before the library is adopted.
   This tension is real and should be resolved deliberately, not discovered
   in a flaky test.
3. **License and redistribution**, since the repository will be public.
4. **Dependency weight.** `AGENTS.md` forbids adding dependencies casually,
   and the heavier document-AI stacks pull in large model dependencies. The
   cost is paid by every contributor and every deployment.
5. **Spanish and legal shape** — accents, hyphenation across line breaks,
   numbered hierarchies, footnotes, tables.

The rung-1 fixture document exists for exactly this: whichever library is
chosen, it is judged by whether the parsed tree and the offsets survive a
committed golden file, not by its README. That makes §15's open question
about committing the fixture's parsed tree a prerequisite for this choice
rather than an independent one.

---

## 5. Borrow, do not fork

The recommendation is that GroundSource stays its own codebase and takes
three specific things from the projects above:

- **The span-anchoring data model from OpenContracts / PAWLS**, as prior art
  and possibly as a wire format. It was designed for portability between
  tools, which is the property that makes anchors checkable by something
  other than this project's own code.
- **An ingestion library for extraction**, per §4.2.
- **An extraction or verification component** — verbatim-rag's extractive
  approach, or [LettuceDetect](https://github.com/KRLabsOrg/LettuceDetect)'s
  span-level grounding verification — rather than hand-rolling the guardrail
  in §8 of `initial-thinking.md`.

The argument against forking OpenContracts, despite the stack match: its
purpose is corpus annotation and structured extraction for legal teams, and
its data model, GraphQL API and permission system come with that purpose.
GroundSource is one document, one public reader, one promise. Inheriting a
platform to obtain a span table is a bad trade, and the parts worth having
are readable without being adopted.

The argument *for* revisiting that later: if multi-document corpus support
(`AGENTS.md`, open decisions) ever becomes real, the calculus changes, and
this paragraph is the reminder to re-run it rather than assume the earlier
answer.

---

## 6. Where the remaining original work is

Stated plainly, so that effort goes to the parts that are not already
solved:

1. Offsets that survive PDF extraction well enough to **prove** a quotation
   was sliced rather than generated.
2. Source custody a reader can verify independently.
3. An anchor-precise reading surface, rather than `#page=N`.
4. A Spanish golden set that scores declines under adversarial phrasing.

Everything else in Phases 0 and 1 has been built by someone else, in public,
more than once. Building it anyway buys understanding of the system, which
is a legitimate reason, but it should be a chosen cost rather than an
assumed necessity.

---

## 7. Decisions that want an ADR

Added to the list in `initial-thinking.md` §14:

- **How far the unit model adopts Akoma Ntoso** — vocabulary, identifier
  scheme, or serialisation — and what is deliberately left out.
- **Which ingestion library performs extraction**, judged against the
  criteria in §4.2, including how the determinism tension with invariant 7 is
  resolved.
- **Whether anchors are expressed in a portable format** (PAWLS-like, or an
  Akoma Ntoso identifier scheme) or remain internal to this project.

---

## 8. Open questions

- Whether the peace agreement is ingestible into an Akoma Ntoso-shaped tree
  at all. It is a negotiated political agreement, not legislation; its
  hierarchy is clean but it was never drafted against a legislative schema.
  Trying the standard's vocabulary on the rung-1 fixture will not answer
  this, and a *punto* of the agreement may need to be parsed early, purely
  to find out.
- Whether any extraction library actually exposes character ranges into a
  canonical text, or whether that mapping has to be built on top of page and
  bounding-box provenance regardless — in which case the "use a library"
  recommendation shrinks to "use a library for layout, own the offsets".
- Whether the absence of a custody implementation in the open-source world
  reflects an unmet need or a solved-differently one, since digital
  preservation and evidence-handling communities have addressed the same
  problem outside the RAG context and were not searched here.

---

## 9. Method, and what this survey is worth

Conducted on 2026-09-10 by web search, not by a systematic sweep of package
registries or GitHub. Queries covered: grounded/verbatim citation RAG, PDF
highlight citation viewers, legal and legislative RAG, structure-aware
chunking, Akoma Ntoso, Spanish-language and Colombian legal chatbots,
peace-agreement tooling, and provenance/checksum practice in RAG.

Limits worth stating, since this document will be cited as a reason not to
look again:

- A finding of absence is weak. It is strongest for the peace-agreement
  search, which was run in Spanish and returned only archives and news, and
  weakest for the custody search, where a small unpublicised repository
  would not surface.
- License, maintenance status and feature claims above come from project
  documentation, not from reading the code. Anything in the table marked
  "confirm" has not been verified.
- Non-English, non-Spanish projects are almost certainly under-represented.

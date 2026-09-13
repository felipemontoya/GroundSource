# GroundSource

Talk to a document. Get the document's own words back.

GroundSource ingests a single source document, prepares it with a mix of
parsing and AI techniques, and exposes a backend API for a conversational
agent that knows that document deeply. Every answer the agent gives is
anchored to verbatim spans of the original text and to links that point
back at the exact place they came from.

## Why

Some documents matter enough that people argue about them without reading
them: bills, constitutional reforms, referendum texts, regulations, party
platforms, terms of service. Around those documents grows a second layer of
commentary — summaries, headlines, threads — that is often where the real
disagreement happens. Two people can hold opposite beliefs about what a
document says while neither has read the clause in question.

GroundSource is built for that situation. It does not try to tell anyone
what to think about a document. It tries to make it cheap to find out what
the document actually says, in its own words, with the surrounding context
attached, so that a disagreement can be about the text rather than about
competing retellings of it.

The working assumption: when a narrative is murky, the fastest route to
clarity is the primary source, quoted exactly and located precisely.

## What it does

- **Ingest** a source document (PDF, HTML, DOCX, plain text) and keep the
  original bytes immutable and addressable.
- **Parse** it into a structured representation: sections, articles,
  clauses, headings, footnotes, tables — with stable anchors and character
  offsets into the original.
- **Prepare** it with AI-assisted passes: segmentation, summarization per
  unit, terminology extraction, cross-reference resolution, and embeddings
  for retrieval.
- **Serve** a backend API for chat sessions against the prepared document.
- **Answer** questions through an agent whose job is grounding: retrieve the
  relevant spans, quote them verbatim, cite their anchors, and link back to
  the original.

## The grounding contract

This is the product. Everything else is plumbing.

1. **Quote, do not paraphrase silently.** Any claim about what the document
   says is accompanied by the verbatim span it rests on.
2. **Cite precisely.** Every quoted span carries an anchor (section /
   article / clause path plus character range) and a link that resolves to
   that location in the original document.
3. **Abstain when ungrounded.** If the document does not address a question,
   the agent says so instead of filling the gap from general knowledge.
4. **Mark the seams.** Interpretation, synthesis across clauses, and
   definitions pulled from outside the document are labeled as such and kept
   visually distinct from quotation.
5. **Show the neighborhood.** A quoted clause is offered with enough
   surrounding text that a reader can check whether the quote survives its
   context.
6. **Stay symmetric.** Where a clause genuinely supports more than one
   reading, the agent surfaces the competing readings and the text each one
   leans on, rather than picking a side.

## Non-goals

- Not a fact-checker: GroundSource does not rule on whether the document's
  claims are true, only on what it says.
- Not a political scorer: no left/right labels, no bias ratings, no
  endorsement or opposition.
- Not a general-purpose RAG chatbot: the unit of work is one document
  (or one coherent corpus), deeply prepared, not an open web index.
- Not a summarizer that replaces reading: summaries exist to route a reader
  to the text, never to stand in for it.

## How it works

```
source document
      │
      ▼
  ingestion ──────► immutable original + checksum + metadata
      │
      ▼
   parsing ───────► structural tree (sections, clauses) with offsets
      │
      ▼
 preparation ─────► per-unit summaries, terms, cross-refs, embeddings
      │
      ▼
    index ────────► retrieval over spans, anchored to the tree
      │
      ▼
  backend API ────► sessions, messages, retrieval, citations
      │
      ▼
    agent ────────► grounded answers: quote + anchor + link
```

The prepared artifacts are derived data. The original document is the only
source of truth, and any derived artifact can be regenerated from it.

## Status

Early. The repository currently holds the project's intent and its working
agreements; implementation follows. See `AGENTS.md` for the invariants that
code in this repo is expected to honor, and the open decisions listed
below.

## Open decisions

Settled: the backend is Python + Django over PostgreSQL, and the code is
licensed under Apache 2.0.

Still open:

- Frontend stack and hosting target — likely a statically hosted page built
  with a modern JavaScript toolchain, consuming the API over HTTP.
- Model providers for the preparation passes and for the chat agent.
- Vector storage: pgvector in the same database, or a dedicated index.
- Whether the first release ships a reference frontend or API only.

## License

[Apache License 2.0](LICENSE). Permissive, with an explicit patent grant and
a requirement that modifications be marked — which suits a tool whose whole
claim is that its output can be traced.

The license covers the code. It does not cover the documents in `sources/`:
those carry whatever terms their publisher attached, and `NOTICE` says so.
Each document's redistributability is checked before it is added, per
`sources/README.md`.

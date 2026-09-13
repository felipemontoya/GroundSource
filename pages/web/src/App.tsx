import { useCallback, useEffect, useRef, useState } from "react";

import { ask, fetchSources, type Answer, type SourceSummary } from "./api";
import { AnswerView } from "./AnswerView";

interface Turn {
  id: number;
  question: string;
  answer?: Answer;
  error?: string;
}

type Load =
  | { phase: "loading" }
  | { phase: "ready"; sources: SourceSummary[]; providerConfigured: boolean }
  | { phase: "failed"; detail: string };

export function App() {
  const [load, setLoad] = useState<Load>({ phase: "loading" });
  const [slug, setSlug] = useState<string>("");
  const [question, setQuestion] = useState("");
  // One transcript per document, never one shared transcript.
  //
  // A conversation is with a *document*, so it cannot outlive a change of
  // document. Two typesettings of the same text are two documents: they
  // paginate differently, so an answer's page numbers only mean anything
  // under the edition that produced them. Keying by slug means switching
  // the picker puts away one conversation and brings back another, instead
  // of re-labelling answers with a document that did not produce them.
  const [transcripts, setTranscripts] = useState<Record<string, Turn[]>>({});
  const [pending, setPending] = useState(false);
  const nextId = useRef(1);

  const turns = transcripts[slug] ?? [];

  useEffect(() => {
    const controller = new AbortController();
    fetchSources(controller.signal)
      .then((body) => {
        setLoad({
          phase: "ready",
          sources: body.sources,
          providerConfigured: body.provider_configured,
        });
        if (body.sources[0]) setSlug(body.sources[0].slug);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setLoad({
          phase: "failed",
          detail: error instanceof Error ? error.message : String(error),
        });
      });
    return () => controller.abort();
  }, []);

  const update = useCallback(
    (target: string, id: number, patch: Partial<Turn>) =>
      setTranscripts((previous) => ({
        ...previous,
        [target]: (previous[target] ?? []).map((turn) =>
          turn.id === id ? { ...turn, ...patch } : turn,
        ),
      })),
    [],
  );

  const submit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      const asked = question.trim();
      if (!asked || pending || !slug) return;

      // Captured now. If the picker moves while the request is in flight,
      // the answer still lands in the transcript of the document it was
      // actually asked of.
      const askedOf = slug;
      const id = nextId.current++;

      setTranscripts((previous) => ({
        ...previous,
        [askedOf]: [...(previous[askedOf] ?? []), { id, question: asked }],
      }));
      setQuestion("");
      setPending(true);

      try {
        const answer = await ask(askedOf, asked);
        update(askedOf, id, { answer });
      } catch (error: unknown) {
        update(askedOf, id, {
          error: error instanceof Error ? error.message : String(error),
        });
      } finally {
        setPending(false);
      }
    },
    [question, pending, slug, update],
  );

  const source =
    load.phase === "ready" ? load.sources.find((item) => item.slug === slug) : undefined;

  return (
    <main>
      <header>
        <h1>GroundSource</h1>
        <p className="tagline">Talk to a document. Get the document&rsquo;s own words back.</p>
      </header>

      {load.phase === "loading" && <p className="status">Loading&hellip;</p>}

      {load.phase === "failed" && (
        <>
          <p className="status bad">API unreachable</p>
          <pre>{load.detail}</pre>
        </>
      )}

      {load.phase === "ready" && load.sources.length === 0 && (
        <section>
          <p className="status bad">No document is ingested.</p>
          <p className="note">
            Run <code>docker compose exec api python manage.py ingest_source &lt;file&gt;</code> in{" "}
            <code>dev/</code>, then reload.
          </p>
        </section>
      )}

      {load.phase === "ready" && source && (
        <>
          <DocumentBar
            source={source}
            sources={load.sources}
            onSelect={setSlug}
            providerConfigured={load.providerConfigured}
          />

          <section className="transcript">
            {turns.length === 0 && (
              <p className="note">
                Ask something this document would know. Every claim comes back with the passage it
                rests on; when the document does not say, the answer says that instead.
              </p>
            )}
            {turns.map((turn) => (
              <article key={turn.id} className="turn">
                <p className="question">{turn.question}</p>
                {turn.error && <p className="status bad">{turn.error}</p>}
                {turn.answer && <AnswerView answer={turn.answer} expected={source} />}
                {!turn.answer && !turn.error && (
                  <p className="status">Reading the document&hellip;</p>
                )}
              </article>
            ))}
          </section>

          <form onSubmit={submit} className="composer">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={`Ask about ${source.edition || source.title}`}
              aria-label="Your question"
              disabled={pending}
            />
            <button type="submit" disabled={pending || !question.trim()}>
              {pending ? "Asking" : "Ask"}
            </button>
          </form>
        </>
      )}
    </main>
  );
}

function DocumentBar({
  source,
  sources,
  onSelect,
  providerConfigured,
}: {
  source: SourceSummary;
  sources: SourceSummary[];
  onSelect: (slug: string) => void;
  providerConfigured: boolean;
}) {
  return (
    <section className="docbar">
      <div className="docbar-row">
        {sources.length > 1 ? (
          <select
            value={source.slug}
            onChange={(event) => onSelect(event.target.value)}
            aria-label="Which document you are talking to"
          >
            {sources.map((item) => (
              <option key={item.slug} value={item.slug}>
                {item.edition ? `${item.title} — ${item.edition}` : item.title}
              </option>
            ))}
          </select>
        ) : (
          <strong>{source.title}</strong>
        )}
        {source.edition && sources.length <= 1 && (
          <span className="edition">{source.edition}</span>
        )}
      </div>
      <p className="provenance">
        {source.pages} pages · {source.units} units · {source.characters.toLocaleString()}{" "}
        characters · {source.extractor} · sha256 <code>{source.sha256.slice(0, 16)}…</code>
      </p>
      {sources.length > 1 && (
        <p className="note editions">
          Page numbers below belong to this edition. Another edition of the same text is a
          separate document with its own conversation.
        </p>
      )}
      {!providerConfigured && (
        <p className="warn">
          No model provider is configured, so nothing is generated and semantic matching is off.
          Questions still return the passages that match them lexically.
        </p>
      )}
      {providerConfigured && source.embedded_units === 0 && (
        <p className="warn">
          No embeddings stored yet. Run <code>manage.py embed_source {source.slug}</code> for
          semantic retrieval; until then matching is lexical only.
        </p>
      )}
    </section>
  );
}

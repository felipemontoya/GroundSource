import { useCallback, useEffect, useRef, useState } from "react";

import { ask, fetchSources, type Answer, type SourceSummary } from "./api";
import { AnswerView } from "./AnswerView";
import { useRoute } from "./routing";

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
  const [slug, navigate] = useRoute();
  const [question, setQuestion] = useState("");
  // One transcript per document, never one shared transcript.
  //
  // A conversation is with a *document*, so it cannot outlive a change of
  // document. Two editions of the same text are two documents: they
  // paginate differently, so an answer's page numbers only mean anything
  // under the edition that produced them.
  const [transcripts, setTranscripts] = useState<Record<string, Turn[]>>({});
  const [pending, setPending] = useState(false);
  const nextId = useRef(1);

  const turns = slug ? (transcripts[slug] ?? []) : [];

  useEffect(() => {
    const controller = new AbortController();
    fetchSources(controller.signal)
      .then((body) =>
        setLoad({
          phase: "ready",
          sources: body.sources,
          providerConfigured: body.provider_configured,
        }),
      )
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

      // Captured now. If the reader changes document while the request is
      // in flight, the answer lands in the transcript of the document it
      // was actually asked of.
      const askedOf = slug;
      const id = nextId.current++;

      setTranscripts((previous) => ({
        ...previous,
        [askedOf]: [...(previous[askedOf] ?? []), { id, question: asked }],
      }));
      setQuestion("");
      setPending(true);

      try {
        update(askedOf, id, { answer: await ask(askedOf, asked) });
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

  if (load.phase === "loading") {
    return (
      <Shell>
        <p className="status">Cargando&hellip;</p>
      </Shell>
    );
  }

  if (load.phase === "failed") {
    return (
      <Shell>
        <p className="status bad">No se pudo contactar la API</p>
        <pre>{load.detail}</pre>
      </Shell>
    );
  }

  if (load.sources.length === 0) {
    return (
      <Shell>
        <p className="status bad">No hay ningún documento cargado.</p>
        <p className="note">
          Ejecuta <code>docker compose exec api python manage.py ingest_source &lt;archivo&gt;</code>{" "}
          en <code>dev/</code> y recarga.
        </p>
      </Shell>
    );
  }

  // Root: the index. No document is chosen on the reader's behalf, because
  // choosing for them is exactly how someone ends up reading the wrong one.
  if (!slug) {
    return (
      <Shell>
        <Index sources={load.sources} onOpen={navigate} />
      </Shell>
    );
  }

  const source = load.sources.find((item) => item.slug === slug);

  if (!source) {
    return (
      <Shell>
        <p className="status bad">
          No hay ningún documento con el identificador <code>{slug}</code>.
        </p>
        <Index sources={load.sources} onOpen={navigate} />
      </Shell>
    );
  }

  return (
    <Shell>
      <DocumentBar source={source} providerConfigured={load.providerConfigured} onHome={navigate} />

      <section className="transcript">
        {turns.length === 0 && (
          <p className="note">
            Pregunta algo que este documento sepa. Cada afirmación vuelve con el pasaje en el que
            se apoya; cuando el documento no lo dice, la respuesta lo dice así.
          </p>
        )}
        {turns.map((turn) => (
          <article key={turn.id} className="turn">
            <p className="question">{turn.question}</p>
            {turn.error && <p className="status bad">{turn.error}</p>}
            {turn.answer && <AnswerView answer={turn.answer} expected={source} />}
            {!turn.answer && !turn.error && <p className="status">Leyendo el documento&hellip;</p>}
          </article>
        ))}
      </section>

      <form onSubmit={submit} className="composer">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={`Pregunta sobre ${source.nickname || source.edition || source.title}`}
          aria-label="Tu pregunta"
          disabled={pending}
        />
        <button type="submit" disabled={pending || !question.trim()}>
          {pending ? "Preguntando" : "Preguntar"}
        </button>
      </form>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main>
      <header>
        <h1>GroundSource</h1>
        <p className="tagline">
          Habla con un documento. Recibe las palabras del propio documento.
        </p>
      </header>
      {children}
    </main>
  );
}

function Index({
  sources,
  onOpen,
}: {
  sources: SourceSummary[];
  onOpen: (slug: string) => void;
}) {
  return (
    <section>
      <h2>Documentos</h2>
      <p className="note">
        Cada documento tiene su propia dirección y su propia conversación. Una edición distinta
        del mismo texto es otro documento: pagina distinto, y una cita señala una página de un
        archivo concreto.
      </p>
      <ul className="index">
        {sources.map((item) => (
          <li key={item.slug}>
            <a
              href={`/${item.slug}`}
              onClick={(event) => {
                // A real link, so it can be copied and shared; navigation
                // is intercepted only when the browser allows it.
                if (event.metaKey || event.ctrlKey || event.shiftKey) return;
                event.preventDefault();
                onOpen(item.slug);
              }}
            >
              {item.title}
            </a>
            {item.edition && <span className="edition">{item.edition}</span>}
            <span className="provenance">
              {item.pages} páginas · {item.units} unidades · {item.language} ·{" "}
              {item.embedded_units > 0 ? "con embeddings" : "sin embeddings"}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function DocumentBar({
  source,
  providerConfigured,
  onHome,
}: {
  source: SourceSummary;
  providerConfigured: boolean;
  onHome: (slug: string) => void;
}) {
  return (
    <section className="docbar">
      <div className="docbar-row">
        <strong>{source.title}</strong>
        {source.edition && <span className="edition">{source.edition}</span>}
        <a
          href="/"
          className="linkish"
          onClick={(event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey) return;
            event.preventDefault();
            onHome("");
          }}
        >
          todos los documentos
        </a>
      </div>
      <p className="provenance">
        {source.pages} páginas · {source.units} unidades ·{" "}
        {source.characters.toLocaleString("es")} caracteres · {source.extractor} · sha256{" "}
        <code>{source.sha256.slice(0, 16)}…</code>
      </p>
      {!providerConfigured && (
        <p className="warn">
          No hay proveedor de modelos configurado: no se genera ninguna respuesta y no hay
          búsqueda semántica. Las preguntas siguen devolviendo los pasajes que coinciden
          léxicamente.
        </p>
      )}
      {providerConfigured && source.embedded_units === 0 && (
        <p className="warn">
          Este documento aún no tiene embeddings. Ejecuta{" "}
          <code>manage.py embed_source {source.slug}</code> para búsqueda semántica; hasta
          entonces la coincidencia es sólo léxica.
        </p>
      )}
    </section>
  );
}

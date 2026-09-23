import { useCallback, useEffect, useRef, useState } from "react";

import { ask, fetchSources, type Answer, type SourceSummary } from "./api";
import { AnswerView } from "./AnswerView";
import { SOURCE_SLUG } from "./document";

interface Turn {
  id: number;
  question: string;
  answer?: Answer;
  error?: string;
}

type Load =
  | { phase: "loading" }
  | { phase: "ready"; source: SourceSummary; providerConfigured: boolean }
  | { phase: "missing" }
  | { phase: "failed"; detail: string };

/**
 * One document, one conversation.
 *
 * Unlike ../web, this page has no index and no routing: it only ever talks
 * to SOURCE_SLUG. If the API does not have that document, the page says so
 * rather than offering whatever else is loaded — a reader who came for the
 * agreement must never end up questioning a different file.
 */
export function App() {
  const [load, setLoad] = useState<Load>({ phase: "loading" });
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const nextId = useRef(1);

  useEffect(() => {
    const controller = new AbortController();
    fetchSources(controller.signal)
      .then((body) => {
        const source = body.sources.find((item) => item.slug === SOURCE_SLUG);
        setLoad(
          source
            ? { phase: "ready", source, providerConfigured: body.provider_configured }
            : { phase: "missing" },
        );
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
    (id: number, patch: Partial<Turn>) =>
      setTurns((previous) =>
        previous.map((turn) => (turn.id === id ? { ...turn, ...patch } : turn)),
      ),
    [],
  );

  const submit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      const asked = question.trim();
      if (!asked || pending) return;

      const id = nextId.current++;
      setTurns((previous) => [...previous, { id, question: asked }]);
      setQuestion("");
      setPending(true);

      try {
        update(id, { answer: await ask(SOURCE_SLUG, asked) });
      } catch (error: unknown) {
        update(id, { error: error instanceof Error ? error.message : String(error) });
      } finally {
        setPending(false);
      }
    },
    [question, pending, update],
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
        <p className="status bad">No se pudo contactar el servicio. Intenta de nuevo más tarde.</p>
        <pre>{load.detail}</pre>
      </Shell>
    );
  }

  if (load.phase === "missing") {
    return (
      <Shell>
        <p className="status bad">
          El servicio no tiene cargado el documento <code>{SOURCE_SLUG}</code>.
        </p>
      </Shell>
    );
  }

  const { source, providerConfigured } = load;
  const name = source.nickname || source.title;

  return (
    <Shell>
      <DocumentBar source={source} providerConfigured={providerConfigured} />

      <section className="transcript">
        {turns.length === 0 && (
          <p className="note">
            Pregunta algo sobre {name}. Cada afirmación vuelve con el pasaje en el que se apoya;
            cuando el texto no lo dice, la respuesta lo dice así.
          </p>
        )}
        {turns.map((turn) => (
          <article key={turn.id} className="turn">
            <p className="question">{turn.question}</p>
            {turn.error && <p className="status bad">{turn.error}</p>}
            {turn.answer && <AnswerView answer={turn.answer} expected={source} />}
            {!turn.answer && !turn.error && <p className="status">Leyendo {name}&hellip;</p>}
          </article>
        ))}
      </section>

      <form onSubmit={submit} className="composer">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={`Pregunta sobre ${name}`}
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
        <h1>El Acuerdo Final, en sus propias palabras</h1>
        <p className="tagline">
          Pregunta. La respuesta cita el texto del acuerdo del 24 de noviembre de 2016.
        </p>
      </header>
      {children}
    </main>
  );
}

function DocumentBar({
  source,
  providerConfigured,
}: {
  source: SourceSummary;
  providerConfigured: boolean;
}) {
  return (
    <section className="docbar">
      <div className="docbar-row">
        <strong>{source.title}</strong>
        {source.edition && <span className="edition">{source.edition}</span>}
      </div>
      <p className="provenance">
        {source.pages} páginas · {source.characters.toLocaleString("es")} caracteres · sha256{" "}
        <code>{source.sha256.slice(0, 16)}…</code>
      </p>
      {!providerConfigured && (
        <p className="warn">
          Las respuestas generadas no están disponibles en este momento. Las preguntas siguen
          devolviendo los pasajes del texto que coinciden.
        </p>
      )}
    </section>
  );
}

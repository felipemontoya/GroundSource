import { useState } from "react";

import type { Answer, Claim, Citation, SourceSummary } from "./api";

/**
 * Rendering rules that come from the grounding contract, not from taste:
 *
 * - Quotation is visually distinct from everything the model wrote, so a
 *   reader can tell at a glance which words are the document's.
 * - Interpretation is labelled where it happens, not disclaimed at the end.
 * - An abstention is presented as an answer, not as a failure state. Claims
 *   that come with an abstention are what the document does say on the
 *   topic, and are headed as such so they do not read as the answer.
 * - The retrieved passages stay reachable, so a reader can check what the
 *   answer chose not to use.
 * - An answer is never rendered under a document that did not produce it.
 *   Page numbers are a property of an edition, so showing an answer beneath
 *   the wrong one silently misattributes every citation in it.
 *
 * Quotations are never translated: they are the document's own text. The
 * statement above one is in the language of the question, so a Spanish
 * statement may well head an English quotation, and that is correct.
 * - An answer is never rendered under a document that did not produce it.
 *   Page numbers are a property of an edition, so showing an answer beneath
 *   the wrong one silently misattributes every citation in it.
 */
export function AnswerView({
  answer,
  expected,
}: {
  answer: Answer;
  expected: SourceSummary;
}) {
  const [showRetrieved, setShowRetrieved] = useState(false);
  const misattributed = answer.source.slug !== expected.slug;
  // The answer names its own source, so the nickname comes from it rather
  // than from whichever document the page has selected.
  const name = answer.source.nickname || "el documento";

  return (
    <div className="answer">
      {misattributed && (
        <p className="warn">
          Esta respuesta vino de <strong>{answer.source.edition || answer.source.title}</strong>,
          no del documento seleccionado. Sus rutas de sección y números de página se
          refieren a esa edición.
        </p>
      )}
      {answer.abstained && (
        <p className="abstention">
          <span className="label">{capitalize(name)} no responde a esto.</span>{" "}
          {answer.abstention_reason}
        </p>
      )}

      {answer.abstained && answer.claims.length > 0 && (
        <h3 className="related">
          Lo que sí dice {name} sobre el tema
        </h3>
      )}

      {answer.claims.map((claim, index) => (
        <ClaimView key={index} claim={claim} />
      ))}

      {answer.notes.length > 0 && (
        <ul className="notes">
          {answer.notes.map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      )}

      <p className="meta">
        <button type="button" className="linkish" onClick={() => setShowRetrieved((v) => !v)}>
          {showRetrieved ? "Ocultar" : "Ver"} los {answer.retrieved.length} pasajes considerados
        </button>
        {answer.model && <span className="dim"> · {answer.model}</span>}
        {answer.usage?.output_tokens != null && (
          <span className="dim"> · {answer.usage.output_tokens} tokens de salida</span>
        )}
      </p>

      {showRetrieved && (
        <ol className="retrieved">
          {answer.retrieved.map((unit) => (
            <li key={unit.unit_id}>
              <span className="anchor">
                {unit.path || unit.kind} · p.{unit.page_start} · [{unit.start_offset}:
                {unit.end_offset}]
              </span>
              <span className="preview">{unit.heading || unit.preview}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function ClaimView({ claim }: { claim: Claim }) {
  return (
    <div className={claim.supported ? "claim" : "claim unsupported"}>
      <p className="statement">
        {claim.kind === "interpretation" && <span className="tag">lectura entre cláusulas</span>}
        {claim.statement}
      </p>
      {!claim.supported && (
        <p className="warn">
          Ninguna cita de esta afirmación pudo resolverse, así que se muestra sin respaldo.
        </p>
      )}
      {claim.citations.map((citation) => (
        <CitationView key={`${citation.unit_id}-${citation.start_offset}`} citation={citation} />
      ))}
    </div>
  );
}

function CitationView({ citation }: { citation: Citation }) {
  const page =
    citation.page_start === citation.page_end
      ? `p. ${citation.page_start}`
      : `pp. ${citation.page_start}–${citation.page_end}`;

  return (
    <blockquote>
      <p>{citation.text}</p>
      <cite>
        {citation.path && <strong>{citation.path}</strong>} {page} · caracteres{" "}
        {citation.start_offset}–{citation.end_offset}
      </cite>
    </blockquote>
  );
}

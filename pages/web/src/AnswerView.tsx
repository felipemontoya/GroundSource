import { useState } from "react";

import type { Answer, Claim, Citation } from "./api";

/**
 * Rendering rules that come from the grounding contract, not from taste:
 *
 * - Quotation is visually distinct from everything the model wrote, so a
 *   reader can tell at a glance which words are the document's.
 * - Interpretation is labelled where it happens, not disclaimed at the end.
 * - An abstention is presented as an answer, not as a failure state.
 * - The retrieved passages stay reachable, so a reader can check what the
 *   answer chose not to use.
 */
export function AnswerView({ answer }: { answer: Answer }) {
  const [showRetrieved, setShowRetrieved] = useState(false);

  return (
    <div className="answer">
      {answer.abstained && (
        <p className="abstention">
          <span className="label">The document does not answer this.</span>{" "}
          {answer.abstention_reason}
        </p>
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
          {showRetrieved ? "Hide" : "Show"} the {answer.retrieved.length} passages considered
        </button>
        {answer.model && <span className="dim"> · {answer.model}</span>}
        {answer.usage?.output_tokens != null && (
          <span className="dim"> · {answer.usage.output_tokens} output tokens</span>
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

function ClaimView({ claim }: { claim: Claim }) {
  return (
    <div className={claim.supported ? "claim" : "claim unsupported"}>
      <p className="statement">
        {claim.kind === "interpretation" && <span className="tag">reading across clauses</span>}
        {claim.statement}
      </p>
      {!claim.supported && (
        <p className="warn">
          Every citation for this claim failed to resolve, so it is shown unsupported.
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
      ? `p.${citation.page_start}`
      : `pp.${citation.page_start}–${citation.page_end}`;

  return (
    <blockquote>
      <p>{citation.text}</p>
      <cite>
        {citation.path && <strong>{citation.path}</strong>} {page} · characters{" "}
        {citation.start_offset}–{citation.end_offset}
      </cite>
    </blockquote>
  );
}

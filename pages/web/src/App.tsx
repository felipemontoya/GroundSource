import { useEffect, useState } from "react";

import { fetchHealth, type Health } from "./api";

type State =
  | { phase: "loading" }
  | { phase: "loaded"; health: Health }
  | { phase: "unreachable"; detail: string };

export function App() {
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal)
      .then((health) => setState({ phase: "loaded", health }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          phase: "unreachable",
          detail: error instanceof Error ? error.message : String(error),
        });
      });
    return () => controller.abort();
  }, []);

  return (
    <main>
      <header>
        <h1>GroundSource</h1>
        <p className="tagline">Talk to a document. Get the document&rsquo;s own words back.</p>
      </header>

      <section>
        <h2>Stack</h2>
        <p className="note">
          This page holds no product code. It exists to show that the browser reaches the API and
          that the API reaches PostgreSQL with <code>pgvector</code> loaded.
        </p>
        {state.phase === "loading" && <p className="status">Checking the backend&hellip;</p>}
        {state.phase === "unreachable" && (
          <>
            <p className="status bad">API unreachable</p>
            <pre>{state.detail}</pre>
          </>
        )}
        {state.phase === "loaded" && <Checks health={state.health} />}
      </section>
    </main>
  );
}

function Checks({ health }: { health: Health }) {
  return (
    <>
      <p className={health.status === "ok" ? "status good" : "status bad"}>
        {health.service}: {health.status}
      </p>
      <ul className="checks">
        {Object.entries(health.checks).map(([name, check]) => {
          const { status, ...rest } = check;
          return (
            <li key={name}>
              <span className={status === "ok" ? "dot good" : "dot bad"} aria-hidden="true" />
              <span className="name">{name}</span>
              <span className="detail">
                {Object.entries(rest)
                  .map(([key, value]) => `${key}=${String(value)}`)
                  .join("  ")}
              </span>
            </li>
          );
        })}
      </ul>
    </>
  );
}

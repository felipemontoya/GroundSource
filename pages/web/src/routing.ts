/**
 * One document, one URL.
 *
 * `/` lists the available documents; `/<slug>` opens the conversation with
 * that one. This matters more than it looks: the link you share *is* the
 * document. Whoever receives it lands on the right conversation without
 * choosing from a list where they could pick the wrong one.
 *
 * No routing library: two routes do not justify a dependency (see
 * ../../AGENTS.md on adding them).
 */
import { useCallback, useEffect, useState } from "react";

/** The slug in the address bar, or "" at the root. */
function readSlug(): string {
  const path = window.location.pathname.replace(/^\/+|\/+$/g, "");
  return decodeURIComponent(path);
}

export function useRoute(): [string, (slug: string) => void] {
  const [slug, setSlug] = useState<string>(readSlug);

  // The browser's back button has to change document, not drop the reader
  // out of the application.
  useEffect(() => {
    const onPop = () => setSlug(readSlug());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((next: string) => {
    const url = next ? `/${encodeURIComponent(next)}` : "/";
    if (window.location.pathname !== url) {
      window.history.pushState({}, "", url);
    }
    setSlug(next);
  }, []);

  return [slug, navigate];
}

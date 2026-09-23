# pages/acuerdo

The public page for the 24 November 2016 Final Agreement. It talks to one
document only — the slug in `src/document.ts` — and has no index, no
routing and no way to reach any other source the backend holds.

It started as a copy of [`../web/`](../web/), the reference page, and is
expected to diverge: its framing, wording and design are for readers of the
agreement, not for exercising the pipeline. The answer rendering in
`src/AnswerView.tsx` follows the same grounding contract; change both when
the contract changes.

## Running it

Through the development environment:

```
cd ../../dev && docker compose up
```

Then <http://localhost:5174>. The dev server proxies `/api` to the backend,
as in `../web/`.

## Building for a static host

```
VITE_API_BASE_URL=https://groundsource.projects.felipemontoya.co npm run build
```

The output is `dist/`. The backend must list this page's origin in
`CORS_ALLOWED_ORIGINS`, and `src/document.ts` must name the slug the
agreement was ingested under in that backend.

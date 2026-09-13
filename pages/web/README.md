# pages/web

The reference page: a question box against one document, and an answer
rendered so that the reader can tell which words are the document's.

What the rendering is doing, and why, is in the docstring at the top of
`src/AnswerView.tsx` — quotation set apart typographically, anchors under
every quote, interpretation tagged where it happens, abstention presented
as an answer rather than an error.

Stack: Vite + React + TypeScript, static build. This follows the proposal in
`../../docs/planning/initial-thinking.md` §4, but the frontend framework is
still listed as an open decision in `../../AGENTS.md` — treat it as settled
only when an ADR says so. Tailwind was proposed alongside it and is
deliberately not here yet: one plain stylesheet is enough for a page with no
interface.

## Running it

Through the development environment, which is the supported path:

```
cd ../../dev && docker compose up
```

Then <http://localhost:5173>.

Directly, if Node 22+ is on the machine:

```
npm install
API_ORIGIN=http://localhost:8000 npm run dev
```

## Where the API lives

`src/api.ts` is the only file that knows. It defaults to the same-origin
path `/api`, which the dev server proxies to the backend; that keeps a real
reverse proxy in the path locally, which is where SSE buffering problems
surface. A build hosted on its own origin sets `VITE_API_BASE_URL` to the
backend's absolute origin instead — and the API will need CORS at that
point, which it does not have yet.

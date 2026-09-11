# pages

Frontend code. Statically hosted pages that talk to `../api/` over HTTP.

There is one page today, but the directory is plural by intent: several
distinct front ends — different audiences, different documents, different
framings — are expected to sit here over time, all speaking to the same
backend. Each page is its own subdirectory with its own build, so adding the
second one never requires moving the first.

No page is allowed to become a second source of truth. Anything a page needs
to render a grounded answer — spans, anchors, links — comes from the API.

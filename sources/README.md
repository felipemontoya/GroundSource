# sources

The original documents, as ingested. Nothing derived belongs here.

A file in this directory is treated as immutable: it is the ground that
every answer is traced back to. Corrections arrive as new files, never as
edits in place. Derived artifacts — parsed trees, summaries, embeddings —
are regenerable and are not committed.

This is deliberately the simplest thing that works while the project is
young. Sources may later move to object storage or the database, addressed
by checksum; the invariant that survives any such move is that the original
bytes are immutable and independently verifiable.

Before adding a document, check that redistributing it is permitted — this
repository is intended to become public.

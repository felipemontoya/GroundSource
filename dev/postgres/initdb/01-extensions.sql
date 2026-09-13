-- Runs once, on first initialisation of an empty data directory.
--
-- pgvector is created here rather than in a Django migration so that the
-- extension is a property of the environment, pinned in the image and the
-- init script, instead of an undocumented step someone performed once
-- (see docs/planning/initial-thinking.md, "Local environment").
CREATE EXTENSION IF NOT EXISTS vector;

-- Trigram matching backs lexical retrieval alongside tsvector; created now
-- so the first retrieval work does not need a second environment change.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- The Spanish text-search configuration ships with PostgreSQL. Asserting it
-- exists here turns a missing locale into a startup failure rather than a
-- silently bad index later.
DO $$
BEGIN
    PERFORM 1 FROM pg_ts_config WHERE cfgname = 'spanish';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'text search configuration "spanish" is missing';
    END IF;
END
$$;

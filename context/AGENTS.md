<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

<!-- END:nextjs-agent-rules -->

## Application Building Context

Read the following files in order before implementing or making any architectural decision:

1. `context/project-overview.md` — product definition, goals, features, and scope
2. `context/architecture-context.md` — system structure, boundaries, storage model, and invariants
3. `context/ui-context.md` — theme, colors, typography, canvas design, and component conventions
4. `context/code-standards.md` — implementation rules and conventions
5. `context/ai-workflow-rules.md` — development workflow, scoping rules, and delivery approach
6. `context/progress-tracker.md` — current phase, completed work, open questions, and next steps
7.`context/folder-archtecture.md` contains basic folder structure and its purpose.
8. `context/progress-tracker.md` — current phase, completed work, open questions, and next steps


If implementation changes the architecture, scope, or standards documented in the context files, update the relevant file before continuing.

---

## Backend CRAG / RAG — Do not misdiagnose retrieval failures

The Compliance Agent (Node 1) CRAG pipeline in `backend/services/rag/` is **working as designed** when you see:

- Multi-query generation, grading, reasoning trace, and `ComplianceResult` all behaving correctly **after** chunks are retrieved.

### Symptom that looks like “RAG is broken” (usually it is not)

- Logs: `Retrieved 0 unique chunks`, then `HARD STOP: No relevant policy chunks found`
- Test fails on `intervene=False` even though policy was just ingested

**This is often a pgvector search / index issue, not broken RAG logic.** Ingest can succeed while `match_policy_chunks` RPC returns empty.

### Root cause (documented May 2026)

- `policy_chunks` uses an **IVFFlat** index with `lists = 100` in `backend/migrations/001_create_policy_vectors.sql`.
- With a **tiny corpus** (1–few chunks in dev/tests), IVFFlat can return **no neighbors** even when rows exist.
- Do **not** rewrite grader, prompts, `compliance_service`, or multi-query logic for this without checking retrieval first.

### What to check before changing CRAG code

1. Confirm rows exist: `policy_chunks` has chunks for the expected `doc_name`.
2. Confirm RPC exists: `match_policy_chunks` (migrations `001` / `002`).
3. Run optional fix: `backend/migrations/004_fix_policy_vector_index.sql` on Supabase (`lists = 1` + `ANALYZE`).
4. Know the fallback: `backend/services/rag/retriever.py` logs `[Retriever] RPC empty - used local cosine fallback` and ranks in Python — intentional for small corpora.

### Safe changes vs unsafe changes

| Safe | Unsafe (without retrieval proof) |
|------|----------------------------------|
| Run migration `004`, re-ingest policy docs | Rewriting CRAG prompts or grader |
| Adjust `match_threshold` in `retriever.py` | Deleting “duplicate” RAG modules |
| Fix ingest/upsert embedding format | Assuming Strategy Agent broke Compliance |

### Ownership

- **Retrieval / pgvector:** `ingestor.py`, `retriever.py`, SQL migrations `001`–`004`
- **CRAG reasoning:** `compliance_service.py`, `grader.py`, `reranker.py`, `compliance_prompts.py`
- **Node 2 Strategy:** `services/strategy/` — does **not** use pgvector; uses `subscribers` + `interaction_events` only
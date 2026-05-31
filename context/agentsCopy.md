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

---

## Backend Writer / Reviewer / Dispatch (Nodes 3–5)

### Graph flow

`compliance` → `strategy` → `writer` ↔ `reviewer` (max 3 revisions) → `dispatch` → END

See [intervention_graph.py](backend/services/agents/intervention_graph.py).

### Ownership

| Layer | Files |
|-------|--------|
| Writer (Node 3) | `services/writer/writer_service.py`, `prompts/writer_prompts.py` |
| Reviewer (Node 4) | `services/meta_tribe/meta_tribe_service.py`, `prompts/reviewer_prompts.py` |
| Send tool | `services/tools/send_message.py` — **only** called from `dispatch_agent.py` |
| Resend | `utils/resend_client.py` |

### Rules

- Writer produces `MessageDraft` (subject, body_plain, body_html, cta_text, cta_url). **No emojis** in copy.
- Writer must **not** import Resend or Twilio — single delivery abstraction is `send_message`.
- Reviewer is **LLM-based** today. **TRIBE v2** (hook/engagement neural scoring) is future — see [backend/docs/FUTURE_TRIBE_V2.md](backend/docs/FUTURE_TRIBE_V2.md).
- Push and SMS send are skipped per spec; Email via Resend; Twilio is stub only.

### Resend env

```
RESEND_API_KEY=
RESEND_FROM_EMAIL=you@your-verified-domain.com   # NOT @gmail.com
TEST_RECIPIENT_EMAIL=movindsouza79@gmail.com
FORCE_EMAIL_CHANNEL=true   # tests
TEST_MODE=true             # sends to TEST_RECIPIENT_EMAIL
```

If `RESEND_FROM_EMAIL` is a personal inbox, code falls back to `onboarding@resend.dev`.

### Tests

- `python test_writer.py` — Node 3 isolated
- `python test_reviewer.py` — Node 4 isolated
- `python test.py` — full pipeline + email send
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
7. `context/folder-archtecture.md` — basic folder structure and its purpose
8. `agentic plan` — LangGraph intervention pipeline, Trigger.dev orchestration, and agent node specs

If implementation changes the architecture, scope, or standards documented in the context files, update the relevant file before continuing.

---

## North star — agentic intervention pipeline

RetentionOS ends in a **human-in-the-loop approvals queue** fed by an async multi-agent backend. The target architecture (see `agentic plan`) is:

| Node | Agent | Role | Frontend touchpoint |
|------|--------|------|---------------------|
| 1 | **Compliance** (CRAG) | Policy RAG gatekeeper; `should_intervene` | Approvals **reasoning** block; early terminate if false |
| 2 | **Strategy** | Channel + `scheduled_time` from user history | `agentAction.channel`, `send_at` |
| 3 | **Writer** | Draft message for channel + discount | `messagePreview` |
| 4 | **Meta Tribe** | Hook/tone reviewer; corrective loop (max 3) | Rejection feedback → re-draft before queue |
| — | **Trigger.dev** | Queue graph, retry, `wait.until(scheduled_time)`, dispatch | No direct UI; approvals arrive when graph finishes |

**ML ingress payload** (backend `InterventionPayload`):

```json
{ "user_id": 123, "best_discount": "10%", "expected_profit": 1400 }
```

**Planned FastAPI surface** (not all wired yet):

- `POST /api/interventions/start` — accept ML payload → Trigger.dev task → LangGraph (see agentic plan)
- `POST /api/compliance/check` — optional direct CRAG check (progress tracker)
- `POST /api/approvals/:id/status`, `PATCH /api/approvals/:id` — human approve / reject / edit copy
- WebSockets: `/ws/metrics`, `/ws/approvals`, `/ws/causal-model` (or env URLs)

Auth is out of scope (single company, no login).

---

## What is built (frontend)

Routes today: `/` (placeholder), `/overview`, `/approvals`, `/causal-model`. Shared dashboard shell: `(dashboard)/layout.tsx` (fixed sidebar + top nav + scrollable main). **Top nav title/subtitle is route-aware** via `usePathname()` (no search bar on any route).

### 1. Design theme setup

- Next.js App Router boilerplate; default SVG/CSS cleaned up.
- Tailwind CSS v4 in `globals.css` with tokens from `ui-context.md` (warm off-white, primary green, semantic state colors).
- shadcn/ui primitives, `lucide-react`, `cn()` in `lib/utils.ts`.
- App wrapped in `<TooltipProvider>`.
- Tailwind v4 opacity: hex literals in `@theme inline` (no broken opacity modifiers).
- Utilities: `.scroll-contain`, `.shadow-primary`, GPU-safe card hovers (`transform` only, no `box-shadow` transitions).

### 2. Dashboard overview (`/overview`)

- **Layout** — Reuses dashboard shell; main content scrolls inside `scroll-contain`.
- **KPI cards** — Saved revenue, net churn, AI precision; sparklines; data from `store/dashboard-store.ts` (mock).
- **Revenue flow chart** — Customer journey visualization (mock).
- **Alert center** — Fixed height, max 3 visible, “View all” expands in place (mock alerts from store).
- **Strategy cards** — Impact/effort grid with hover lift (mock strategies from store).
- **Store** — `store/dashboard-store.ts`; components subscribe directly (ready for live updates via hook only).
- **Hook** — `hooks/use-live-dashboard.ts` exists but is **not mounted** on layout or `/overview` yet.

### 3. Approvals (`/approvals`)

- **Master–detail layout** — Fixed-height container; list scrolls internally; layout does not grow when new items arrive.
- **List panel** — Pending count, policy stub button, selectable queue rows with done-state styling.
- **Detail view** — Agent action block, message preview/edit, reasoning + alternatives; Approve / Reject / Modify flows.
- **Store** — `store/approvals-store.ts`: append-only `addApproval()`, optimistic `setStatus()`, `updateMessagePreview()` (mock seed data).
- **Hook** — `hooks/use-live-approvals.ts` mounted on the page; WebSocket body is stubbed (`// PENDING: Live Data`).
- **Backend mapping (when live)** — Map graph output to `Approval`: `ComplianceResult.reasoning` → `reasoning.text`; `intervene` / confidence → list row; Writer output → `messagePreview`; Strategy → `agentAction.channel` / `send_at`. Shape in `backend/models/compliance_models.py` vs `store/approvals-store.ts`.

### 4. Causal model (`/causal-model`)

- **Metrics strip** — Model version, AUUC, calibration, coverage, drift, retrain time, outcomes; “Retrain now” stub (local loading state).
- **Row 1** — Top churn drivers (CSS bars), Qini curve (Recharts), calibration scatter (Recharts).
- **Row 2** — Uplift distribution (grouped bars), SHAP feature importance (horizontal bars), segment × treatment heatmap (CSS grid).
- **Row 3** — AUUC over time (area + target line), policy value (horizontal bars), confusion matrix (2×2 grid + metrics).
- **Row 4** — Lift decile chart, causal DAG (custom SVG), holdout outcomes (sparkline KPIs).
- **Store** — `store/causal-model-store.ts`; `setSnapshot(partial)` for live updates.
- **Hook** — `hooks/use-live-causal-model.ts` mounted on the page; WebSocket stubbed (`// PENDING: Live Data`).

---

## Backend status (integration context)

Current phase: **Agentic Backend Integration** (`context/progress-tracker.md`). FastAPI app: `backend/app.py` (`/health`, `/api/llm/invoke`, `/api/trigger/callback`).

### Done (Node 1 — Compliance / CRAG)

| Piece | Location |
|-------|----------|
| Policy vectors + `match_policy_chunks` RPC | `backend/migrations/001_*.sql`, `002_match_policy_chunks.sql` |
| Ingest, retrieve, rerank (Cohere + RRF), grade | `backend/services/rag/{ingestor,retriever,reranker,grader}.py` |
| 6-step CRAG orchestration | `backend/services/rag/compliance_service.py` |
| Pydantic models + prompts | `backend/models/compliance_models.py`, `backend/prompts/compliance_prompts.py` |
| LangGraph Node 1 (single-node graph, `should_intervene`) | `backend/services/agents/compliance_agent.py` |
| Supabase + LLM + Trigger clients | `backend/utils/{supabase_client,llm,trigger}.py` |
| E2E test (ingest → CRAG → graph) | `backend/test.py` |

`ComplianceResult` fields for UI: `intervene`, `reasoning`, `policy_source`, `confidence` (1–10).

### Not built yet (blocks full pipeline → approvals stream)

- LangGraph nodes 2–4 (Strategy, Writer, Meta Tribe corrective loop)
- Compiled full graph + max-3 loop fallback + `trim_messages`
- Trigger.dev task: `intervention_task.trigger` → graph → `wait.until` → dispatch mock
- `POST /api/interventions/start` and approval persistence APIs
- WebSocket/SSE publishers for dashboard, approvals, causal model

Frontend work should assume **hook/store-only** wiring until these exist; do not restructure approval or chart components for live data.

---

## Pending (frontend)

Ordered: **shared clients → live streams → approval actions → missing routes → polish**.

### A. Shared API / WebSocket layer (do first)

| Area | File(s) | What to do |
|------|---------|------------|
| HTTP client | `lib/api.ts` (create) | Typed `fetch` wrapper; base URL from `NEXT_PUBLIC_API_URL`; used by approve/PATCH/retrain |
| WebSocket factory | `lib/websocket.ts` (create) | Reconnect helper; no raw URLs in hooks |
| Env | `.env.local` | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_METRICS_URL`, `NEXT_PUBLIC_WS_APPROVALS_URL`, `NEXT_PUBLIC_WS_CAUSAL_MODEL_URL` |

### B. Live data — hooks/stores only (no UI rewrites)

| Area | File(s) | What to do |
|------|---------|------------|
| Dashboard metrics | `hooks/use-live-dashboard.ts`, `store/dashboard-store.ts` | WS → `updateMetrics` (etc.). **Mount** `useLiveDashboard()` in `(dashboard)/layout.tsx` or `/overview`. |
| Approvals queue | `hooks/use-live-approvals.ts`, `store/approvals-store.ts` | WS → `addApproval()` only (append-only; never mutate existing rows from stream). Payload mapper from backend graph state → `Approval`. |
| Causal model | `hooks/use-live-causal-model.ts`, `store/causal-model-store.ts` | WS → `setSnapshot(partial)`. |
| Approve / dismiss | `components/approvals/approval-detail-view.tsx` | `POST /api/approvals/:id/status`; rollback `setStatus()` on failure. |
| Edit copy | `approval-detail-view.tsx` | `PATCH /api/approvals/:id` for `messagePreview` after Save. |
| Retrain | `model-metrics-strip.tsx` | Wire “Retrain now” to FastAPI when endpoint exists. |

### C. Approvals — scale & sidebar

| Area | File(s) | What to do |
|------|---------|------------|
| Queue pagination | `components/approvals/approval-list-panel.tsx` | Virtual scroll or cursor pagination when volume grows. |
| Sidebar badge | `components/layout/sidebar.tsx` | Replace hardcoded `3` with pending count from `useApprovalsStore`. |

### D. Overview & global UX

| Area | What to do |
|------|------------|
| Agent pipeline viz | Processing stages + active agents on dashboard (product scope; needs backend agent status stream). |
| Refresh control | Reconnect WS or refetch snapshot when backend exists. |
| “Ask agent” | Presentational; connect when chat/settings spec exists. |
| Alert / strategy CTAs | Detail modals/drawers when specs exist. |
| Global UX | `loading.tsx` / `error.tsx`, skeletons before WS connects, error boundaries. |
| Accessibility | Keyboard shortcuts, master–detail focus, live region for new queue items. |

### E. Routes in sidebar — not implemented

No `app/(dashboard)/…/page.tsx` yet: `/customers`, `/designer`, `/campaigns` (404 until specs land).

### F. Product scope — later

- **Strategy creation** (`/create` or equivalent)
- **n8n-style intervention canvas**
- Live **stream processing** visualization (ties to agentic plan + overview)

---

## Architecture reminders (do not regress)

- Sidebar active state: `usePathname()` only — no client nav state.
- Live data: Zustand store + one hook per domain; components unchanged when WS connects.
- Static data: do not refetch on every render — use store or caching (`architecture-context.md`).
- Hover performance: `transform: translateY` + `will-change: transform`; no hover `box-shadow` transitions.
- Scroll performance: `.scroll-contain` on main and approval list scroll areas.
- New colors: hex in `@theme inline` in `globals.css`, not opaque `:root` refs for Tailwind v4.

---

## Reference

- Agent pipeline spec: `agentic plan`
- Feature specs: `context/feature-spec/01-design.md`, `02-overwpage.md`, `03-approval.md`
- Current phase & backend checklist: `context/progress-tracker.md`
- Compliance types: `backend/models/compliance_models.py`

# Progress Tracker

Update this file whenever the current phase, active feature, or implementation state changes.

## Current Phase

- **Approval API Implementation** — Backend endpoints for `/api/approvals` and `/api/interventions/start` to persist pending approvals.

## Current Goal

- Implement approval API endpoints (`POST /api/interventions/start`, `GET/PATCH /api/approvals`, `POST /api/approvals/:id/status`).
- Wire frontend WebSocket (`/ws/approvals`) to stream live approvals into Zustand store.
- Run full E2E tests with approvals in the queue (no auto-dispatch in production).
- Deploy to staging with human-in-the-loop enforcement.

## Completed

- Set up Next.js boilerplate
- Cleaned up boilerplate SVGs and CSS
- Initialized shadcn/ui and `cn()` utility
- Added all shadcn primitive components
- Configured `globals.css` with UI Context design tokens
- Fixed Tailwind v4 color mapping issues for opacity variants
- `/overview` layout and component planning
- `/overview` page implementation (sidebar, topnav, KPIs, flow chart, alert center, strategies)
- `/approvals` page implementation (master-detail split layout, rich data model, fixed layout container, live-data ready hook)
- Fixed sparkline/donut position to top-right corner in KPI cards
- Replaced `box-shadow` hover transitions with GPU-composited `transform: translateY` across all cards
- Added `scroll-contain` (CSS containment) to the main scrollable area to prevent sidebar repaint on scroll
- Built Agentic Backend Foundation: Python venv, FastAPI, LangChain, Supabase, and Trigger.dev initialization.
- Added `shadow-primary` utility in `globals.css` for green CTA button glow
- Applied `shadow-primary` to the "Ask agent" button in `top-navbar.tsx`
- `/causal-model` page implementation (metrics strip, 12 analytics panels, Recharts + custom SVG DAG)
- `store/causal-model-store.ts` and `hooks/use-live-causal-model.ts` (mock data, `setSnapshot` for live merge)
- Route-aware `top-navbar.tsx` (title/subtitle per route; no search bar)
- `npm run build` verified clean for `/causal-model` route
- CRAG Compliance Agent (Node 1): 6-step pipeline in `services/rag/compliance_service.py` (multi-query, pgvector retrieve, Cohere+RRF, grader, reasoning trace, verdict)
- RAG modules: `ingestor`, `retriever`, `reranker`, `grader` + `match_policy_chunks` RPC migration
- LangGraph Node 1: `services/agents/compliance_agent.py` (single-node graph, `should_intervene` flag)
- `backend/test.py` CRAG end-to-end test (ingest → pipeline → LangGraph → pass assertions)
- `backend/requirements.txt` for agentic backend dependencies
- Strategy Agent (Node 2): `services/strategy/strategy_service.py`, `strategy_agent.py`, `intervention_graph.py` (compliance → strategy conditional graph)
- DB migration `003_subscribers_and_interactions.sql` (subscribers + interaction_events, seed user_id 99)
- `backend/test.py` full pipeline test: compliance approval → strategy channel/timing → hard-stop path
- LTV/CFVS eligibility MVP: `backend/create_ltv_model.py`, `backend/services/ltv/ltv_service.py`, and `backend/models/ltv_models.py` integrate the `backend/models/LTV.py` prototype into the backend architecture with historical LTV, predictive 12-month LTV, default-risk penalty, and CFVS scoring
- Saved LTV model artifacts and metrics: `backend/artifacts/ltv/ltv_model.pkl`, `ltv_metadata.json`, `backend/metrics/ltv_model_metrics.json`, `ltv_model_report.md`, and `high_value_customers.csv`
- LTV FastAPI endpoints: `/api/ltv/metrics`, `/api/ltv/retrain`, and `/api/ltv/score`
- Churn prediction MVP: `backend/create_churn_model.py`, `backend/services/churn/churn_service.py`, and `backend/models/churn_models.py` train a stdlib logistic classifier over `bank.csv` using `deposit == "no"` as the churn proxy and excluding `duration`, `deposit`, and `contact`
- Saved churn model artifacts and metrics: `backend/artifacts/churn/churn_model.pkl`, `churn_metadata.json`, `backend/metrics/churn_model_metrics.json`, `churn_model_report.md`, and `high_risk_customers.csv`
- Churn FastAPI endpoints: `/api/churn/metrics`, `/api/churn/retrain`, and `/api/churn/score`
- Causal uplift MVP: stdlib X-learner-style service over `backend/data/bank.csv`, leakage exclusion for `duration`, treatment proxy `contact != "unknown"`, treatment optimizer, and FastAPI endpoints `/api/causal/snapshot`, `/api/causal/retrain`, `/api/causal/score`
- Saved causal model artifacts: `backend/artifacts/causal/uplift_artifacts.pkl` and `backend/artifacts/causal/uplift_metadata.json`
- Backend causal metrics bundle: `backend/metrics/uplift_model_metrics.json`, `uplift_model_report.md`, and `persuadable_customers.csv` generated from the saved `.pkl` artifact with AUUC, Qini, churn precision/recall/AUC-ROC, and profit-guarded persuadable ranking
- `/causal-model` live snapshot wiring: `hooks/use-live-causal-model.ts` fetches backend snapshot and `model-metrics-strip.tsx` calls the retrain endpoint
- `backend/test.py` full pipeline test: compliance → strategy → writer → reviewer → dispatch (Resend email)
- Message Writer (Node 3): `services/writer/writer_service.py`, HTML email template, `writer_agent.py`
- Meta Tribe Reviewer (Node 4): LLM hook reviewer in `services/meta_tribe/meta_tribe_service.py`, corrective loop (max 3 revisions)
- Unified delivery: `services/tools/send_message.py` + `utils/resend_client.py` (Resend); Twilio stub; push/SMS skipped
- Full LangGraph: `intervention_graph.py` — compliance → strategy → writer ↔ reviewer → dispatch
- Tests: `test_writer.py`, `test_reviewer.py`; email sent to `TEST_RECIPIENT_EMAIL` via Resend
- Future TRIBE v2 doc: `backend/docs/FUTURE_TRIBE_V2.md`

## In Progress

- **Human-in-the-loop (HITL) before send** — backend graph nodes 1–4 are done; production must **not** call `dispatch` until admin approves on frontend
- Trigger.dev `wait.until(scheduled_time)` + dispatch **after** approval

### Human-in-the-loop — intended production flow

| Step | Where | Status |
|------|--------|--------|
| 1. Agents draft intervention | LangGraph nodes 1–4 (compliance → strategy → writer ↔ reviewer) | **Done** (backend) |
| 2. Queue pending approval | Push to `/approvals` via WS or API | **Not wired** |
| 3. Admin reviews | Compliance reasoning, channel, `send_at`, message preview | **UI done** (mock data) |
| 4. Admin **edits message** | `approval-message-edit.tsx` → `updateMessagePreview()` / future `PATCH` | **UI done**; API pending |
| 5. Admin **Approve** or **Reject** | `approval-detail-view.tsx` | **UI done** (optimistic store); API pending |
| 6. Send to customer | `send_message` / Resend at `scheduled_time` | **Done in `test.py` only**; must run only after step 5 |

**Rule:** `backend/test.py` runs the full graph including dispatch for dev verification. Production: graph ends after reviewer → pending approval → admin accept (with optional copy tweaks) → then dispatch.

## Next Up

- Split intervention graph: **stop before `dispatch_agent`** in production; persist pending approval row
- `POST /api/interventions/start`, `GET/PATCH /api/approvals`, `POST /api/approvals/:id/status` (approve triggers send with edited `messagePreview`)
- WebSocket `/ws/approvals` → `frontend/hooks/use-live-approvals.ts` → `addApproval()`
- Run `004_fix_policy_vector_index.sql` on Supabase if RPC returns empty chunks (see Known Issues)
- Verify Resend domain for production `RESEND_FROM_EMAIL`
- TRIBE v2 hook/engagement scoring integration
- Connect dashboard / causal model WebSockets

## Pending (Live Data Integration)

- **Approvals WebSocket**: `hooks/use-live-approvals.ts` has a stubbed WebSocket block (`// PENDING: Live Data`). When the backend is ready, connect `ws.onmessage` to `store.addApproval()` — zero UI rewrites needed.
- **Dashboard Metrics WebSocket**: `hooks/use-live-dashboard.ts` has the same stub. Connect to `/ws/metrics` to stream KPI + alert updates into `dashboard-store.ts`.
- **Approval Action API**: `approval-row.tsx` calls `setStatus()` optimistically on the Zustand store. The API call stub (`// PENDING: POST /approvals/:id/status`) must be wired to the FastAPI backend.
- **Pagination on Approvals**: The queue currently renders all items. Marked with `// PENDING: Pagination` — add virtual scrolling or cursor-based pagination when data volume grows.
- **Causal Model WebSocket**: `hooks/use-live-causal-model.ts` now fetches `/api/causal/snapshot`; WebSocket streaming is still pending for continuous updates.
- **Retrain API**: `model-metrics-strip.tsx` calls `/api/causal/retrain` and merges the returned snapshot; background retraining via Inngest is still pending.
### Human-in-the-loop (frontend ↔ backend)

- **Approvals stream**: Backend finishes nodes 1–4 → emit pending approval (no customer email yet) → `use-live-approvals.ts` → `addApproval()`.
- **Admin message tweak**: Before Approve, admin edits subject/body in UI; `PATCH /api/approvals/:id` persists `messagePreview` for dispatch.
- **Approve**: `POST /api/approvals/:id/status` with `approved` → Trigger.dev waits until `scheduled_time` → `send_message` with **final** preview (including edits).
- **Reject**: `dismissed` — intervention never sent.

### Other live integration

- **Dashboard Metrics WebSocket**: `use-live-dashboard.ts` → `/ws/metrics` → `dashboard-store.ts`.
- **Pagination on Approvals**: Virtual scroll or cursor pagination when queue grows.
- **Causal Model WebSocket**: `use-live-causal-model.ts` → `setSnapshot()`.
- **Retrain API**: `model-metrics-strip.tsx` "Retrain now" → FastAPI when ready.

## Open Questions

- None currently.

## Known Issues / Operational Notes

### pgvector retrieval empty results (NOT a CRAG logic bug)

- **Symptom:** `Retrieved 0 unique chunks` → compliance hard-stops → looks like RAG failed.
- **Cause:** IVFFlat index on `policy_chunks` with `lists = 100` performs poorly when the table has very few rows (common in `test.py` and early dev). Ingest/upsert can succeed while `match_policy_chunks` RPC returns `[]`.
- **Fix:** Run `backend/migrations/004_fix_policy_vector_index.sql` on Supabase. `retriever.py` already falls back to local cosine similarity when RPC is empty (see log: `RPC empty - used local cosine fallback`).
- **Agent rule:** Do not refactor `compliance_service`, grader, or prompts for this symptom — verify `policy_chunks` row count and retrieval first. See `context/AGENTS.md` § Backend CRAG / RAG.

## Architecture Decisions

- **Routing-driven sidebar**: Sidebar active state is determined purely by `usePathname()` from `next/navigation`. No client state is needed — the active highlight is a deterministic function of the URL. This is the most correct and idiomatic approach in Next.js App Router.
- **Zustand for live data**: All dashboard data (KPIs, Alerts, Strategies) lives in `store/dashboard-store.ts`. Components consume this store directly. When live data is introduced (WebSocket/SSE), only the `hooks/use-live-dashboard.ts` hook needs to change — zero component rewrites.
- **GPU-safe hover animations**: All interactive cards use `transform: translateY` + `will-change: transform` for hover states. `box-shadow` and `background-color` transitions trigger browser paint cycles and were removed as a performance rule.
- **CSS Containment on scroll container**: The main scrollable `<main>` uses `contain: layout style` (via `.scroll-contain`) to create a paint containment boundary. This prevents the sidebar and topnav from being repainted when the main content scrolls.
- **`shadow-primary` in globals.css**: A one-purpose utility that adds a green ambient glow only to primary CTA elements. Kept separate from the base token system so it does not accidentally propagate to other green-colored elements (e.g., state badges).
- **Alert Center fixed height**: Fixed height with internal overflow scroll (max 3 items visible). "View All" toggles the visible count without unmounting the component, preserving scroll position.
- **CRAG vs retrieval failures**: Compliance CRAG orchestration (`compliance_service.py`) is separate from pgvector search (`retriever.py` + migrations). Zero retrieved chunks is treated as a retrieval/index problem first; Python cosine fallback in `retriever.py` is the approved dev workaround until `004` is applied or corpus grows.
- **Writer / Reviewer / Send**: Writer drafts only (`writer_service.py`); reviewer approves hooks (`meta_tribe_service.py` LLM today); `send_message` in dispatch only — writer must not call Resend/Twilio directly.
- **Human-in-the-loop before send**: LangGraph produces drafts; `/approvals` is the gate. Admin may edit `messagePreview` before Approve; dispatch runs only after approval at `scheduled_time`. Dev `test.py` bypasses this for E2E email tests.
- **Resend FROM address**: `RESEND_FROM_EMAIL` must be a verified domain (not @gmail.com). Tests use `onboarding@resend.dev` automatically if a personal inbox is configured.

### Resend email (operational)

- **TO:** `TEST_RECIPIENT_EMAIL` (e.g. movindsouza79@gmail.com) — recipient can be Gmail.
- **FROM:** Must be verified at resend.com/domains, or sandbox `onboarding@resend.dev`.

## Session Notes

- 2026-05-24 - GitHub user `YK1218` (`fs22ai007yashkdhasal@gmail.com`) integrated the LTV prototype into the RetentionOS backend architecture:
  - `backend/models/LTV.py` remains as the notebook-style source prototype.
  - `backend/create_ltv_model.py` trains the backend-safe LTV/CFVS model and writes artifacts plus metrics.
  - `backend/services/ltv/ltv_service.py` implements synthetic BFSI data generation, historical LTV, predictive LTV, default-risk modeling, CFVS scoring, tiering, and high-value export.
  - `backend/models/ltv_models.py` adds request/response schemas for LTV scoring and metrics.
  - `backend/artifacts/ltv/ltv_model.pkl` and `ltv_metadata.json` contain the saved LTV artifact.
  - `backend/metrics/ltv_model_metrics.json`, `ltv_model_report.md`, and `high_value_customers.csv` contain current LTV gate diagnostics.
  - `backend/app.py` exposes `/api/ltv/metrics`, `/api/ltv/retrain`, and `/api/ltv/score`.
- 2026-05-23 - GitHub user `YK1218` (`fs22ai007yashkdhasal@gmail.com`) added the backend churn model MVP:
  - `backend/create_churn_model.py` trains the model from `backend/data/bank.csv` and writes artifacts plus metrics.
  - `backend/services/churn/churn_service.py` implements the stdlib logistic churn classifier, scoring, metrics, and high-risk customer export.
  - `backend/models/churn_models.py` adds request/response schemas for churn scoring and metrics.
  - `backend/artifacts/churn/churn_model.pkl` and `churn_metadata.json` contain the saved churn model artifact.
  - `backend/metrics/churn_model_metrics.json`, `churn_model_report.md`, and `high_risk_customers.csv` contain current churn model diagnostics.
  - `backend/app.py` exposes `/api/churn/metrics`, `/api/churn/retrain`, and `/api/churn/score`.
- 2026-05-23 - GitHub user `YK1218` (`fs22ai007yashkdhasal@gmail.com`) added the backend causal metrics bundle:
  - `backend/metrics/causal_metrics.py` evaluates the saved `.pkl` uplift artifact and writes AUUC, Qini, churn precision/recall/AUC-ROC, uplift deciles, calibration, propensity, and profit-guardrail diagnostics.
  - `backend/metrics/x_learner_reference.py` documents the sklearn/XGBoost production X-Learner implementation path.
  - `backend/metrics/uplift_model_metrics.json`, `uplift_model_report.md`, and `persuadable_customers.csv` contain the current generated metrics and profit-approved persuadable list.
  - `backend/services/causal/uplift_service.py` now regenerates the metrics bundle whenever uplift artifacts are saved.
  - `README.md` now documents the backend metrics outputs.
- Dev server is running on `npm run dev` at port 3000.
- The overview route is at `/overview` (served by `app/(dashboard)/overview/page.tsx`).
- The causal model route is at `/causal-model` (served by `app/(dashboard)/causal-model/page.tsx`).
- Do not use `box-shadow` for hover effects — use `transform` only for perf.
- All new colors MUST be declared as hex values inside `@theme inline` in `globals.css`, not via `:root` var references.

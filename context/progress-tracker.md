# Progress Tracker

Update this file whenever the current phase, active feature, or implementation state changes.

## Current Phase

- Feature Development — Agentic Backend Integration

## Current Goal

- Build and connect the agentic workflow using LangGraph and Trigger.dev

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
- Causal uplift MVP: stdlib X-learner-style service over `backend/data/bank.csv`, leakage exclusion for `duration`, treatment proxy `contact != "unknown"`, treatment optimizer, and FastAPI endpoints `/api/causal/snapshot`, `/api/causal/retrain`, `/api/causal/score`
- `/causal-model` live snapshot wiring: `hooks/use-live-causal-model.ts` fetches backend snapshot and `model-metrics-strip.tsx` calls the retrain endpoint

## In Progress

- Writer + Meta Tribe Reviewer nodes + Trigger.dev task wrapper

## Next Up

- Run `004_fix_policy_vector_index.sql` on Supabase (recommended if RPC returns empty chunks despite ingest; see Known Issues above)
- Wire `POST /api/interventions/start` when full controller pipeline is ready
- Connect to live backend endpoints (WebSocket / SSE)

## Pending (Live Data Integration)

- **Approvals WebSocket**: `hooks/use-live-approvals.ts` has a stubbed WebSocket block (`// PENDING: Live Data`). When the backend is ready, connect `ws.onmessage` to `store.addApproval()` — zero UI rewrites needed.
- **Dashboard Metrics WebSocket**: `hooks/use-live-dashboard.ts` has the same stub. Connect to `/ws/metrics` to stream KPI + alert updates into `dashboard-store.ts`.
- **Approval Action API**: `approval-row.tsx` calls `setStatus()` optimistically on the Zustand store. The API call stub (`// PENDING: POST /approvals/:id/status`) must be wired to the FastAPI backend.
- **Pagination on Approvals**: The queue currently renders all items. Marked with `// PENDING: Pagination` — add virtual scrolling or cursor-based pagination when data volume grows.
- **Causal Model WebSocket**: `hooks/use-live-causal-model.ts` now fetches `/api/causal/snapshot`; WebSocket streaming is still pending for continuous updates.
- **Retrain API**: `model-metrics-strip.tsx` calls `/api/causal/retrain` and merges the returned snapshot; background retraining via Inngest is still pending.

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

## Session Notes

- Dev server is running on `npm run dev` at port 3000.
- The overview route is at `/overview` (served by `app/(dashboard)/overview/page.tsx`).
- The causal model route is at `/causal-model` (served by `app/(dashboard)/causal-model/page.tsx`).
- Do not use `box-shadow` for hover effects — use `transform` only for perf.
- All new colors MUST be declared as hex values inside `@theme inline` in `globals.css`, not via `:root` var references.

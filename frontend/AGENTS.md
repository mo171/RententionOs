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


If implementation changes the architecture, scope, or standards documented in the context files, update the relevant file before continuing.



---



## What is built (frontend)



Routes that exist today: `/` (placeholder), `/overview`, `/approvals`, `/causal-model`. Shared dashboard shell: `(dashboard)/layout.tsx` (fixed sidebar + top nav + scrollable main). Top nav title/subtitle is route-aware via `usePathname()` (no search bar on any route).



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



### 3. Approvals (`/approvals`)

- **Master–detail layout** — Fixed-height container; list scrolls internally; layout does not grow when new items arrive.

- **List panel** — Pending count, policy stub button, selectable queue rows with done-state styling.

- **Detail view** — Agent action block, message preview/edit, reasoning + alternatives; Approve / Reject / Modify flows.

- **Store** — `store/approvals-store.ts`: append-only `addApproval()`, optimistic `setStatus()`, `updateMessagePreview()` (mock seed data).

- **Hook** — `hooks/use-live-approvals.ts` mounted on the page; WebSocket body is stubbed (`// PENDING: Live Data`).



### 4. Causal model (`/causal-model`)

- **Metrics strip** — Model version, AUUC, calibration, coverage, drift, retrain time, outcomes; “Retrain now” stub (local loading state).
- **Row 1** — Top churn drivers (CSS bars), Qini curve (Recharts), calibration scatter (Recharts).
- **Row 2** — Uplift distribution (grouped bars), SHAP feature importance (horizontal bars), segment × treatment heatmap (CSS grid).
- **Row 3** — AUUC over time (area + target line), policy value (horizontal bars), confusion matrix (2×2 grid + metrics).
- **Row 4** — Lift decile chart, causal DAG (custom SVG), holdout outcomes (sparkline KPIs).
- **Store** — `store/causal-model-store.ts`; `setSnapshot(partial)` for live updates.
- **Hook** — `hooks/use-live-causal-model.ts` mounted on the page; WebSocket stubbed (`// PENDING: Live Data`).



---



## Pending



Work below is ordered: **backend integration first** (no UI rewrites needed for most items), then **missing routes**, then **polish**.



### A. After backend is connected (live data — hook/store only)



These are explicitly called out in `context/progress-tracker.md` and `context/project-overview.md`. UI components should not need structural changes.



| Area | File(s) | What to do |

|------|---------|------------|

| Dashboard metrics stream | `hooks/use-live-dashboard.ts`, `store/dashboard-store.ts` | Open WebSocket to `/ws/metrics` (or env `NEXT_PUBLIC_WS_METRICS_URL`). On message, call store updaters (e.g. `updateMetrics`). **Also mount** `useLiveDashboard()` in `(dashboard)/layout.tsx` or `/overview` — the hook exists but is not wired yet. |

| Approvals stream | `hooks/use-live-approvals.ts`, `store/approvals-store.ts` | Open WebSocket to `/ws/approvals`. On each message, `store.addApproval(approval)`. Store is append-only; existing rows are never mutated by the stream. |

| Approve / dismiss | `components/approvals/approval-detail-view.tsx` | Today `setStatus()` is optimistic only. Wire **Reject** and **Approve** to `POST /api/approvals/:id/status` (or equivalent FastAPI route). Roll back store on failure. |

| Edit intervention copy | `approval-detail-view.tsx` | **Save Changes** has `// PENDING: API call → PATCH /api/approvals/:id`. Persist `messagePreview` server-side after PATCH succeeds. |

| Shared API / WS clients | `lib/api.ts`, `lib/websocket.ts` (not created yet) | Add typed fetch helper and WebSocket factory per `context/folder-archtecture.md`; keep components free of raw URL strings. |

| Causal model stream | `hooks/use-live-causal-model.ts`, `store/causal-model-store.ts` | WebSocket → `setSnapshot()`. Charts bind to store arrays; no component rewrites. |
| Env | `.env.local` | `NEXT_PUBLIC_WS_METRICS_URL`, `NEXT_PUBLIC_WS_APPROVALS_URL`, `NEXT_PUBLIC_WS_CAUSAL_MODEL_URL`, `NEXT_PUBLIC_API_URL` (names TBD with backend). |



### B. Approvals — scale & sidebar sync



| Area | File(s) | What to do |

|------|---------|------------|

| Queue pagination | `components/approvals/approval-list-panel.tsx` | Renders full `items` array. Add cursor-based pagination or virtual scroll when volume grows (noted in progress tracker). |

| Sidebar badge | `components/layout/sidebar.tsx` | Approvals badge is hardcoded `3`. Drive from `useApprovalsStore` pending count once live data exists. |



### C. Overview — polish (mock data today)



| Area | What to do |

|------|------------|

| Top navbar title | `top-navbar.tsx` title is always “Overview”. Derive label from route (`usePathname`) or per-page metadata. |

| Refresh control | Refresh button has no handler; should reconnect WS or refetch snapshot when backend exists. |

| “Ask agent” / autonomous status | Presentational only; connect to agent chat or settings when product defines the flow. |

| Alert / strategy actions | Alert cards and strategy cards have CTAs without modals/drawers; add detail flows when specs exist. |

| Global UX | Error boundaries, route `loading.tsx` / `error.tsx`, skeleton states for first paint before WS connects. |

| Accessibility | Keyboard shortcuts, focus management on master–detail approvals, live region for new queue items. |



### D. Routes in sidebar — not implemented



Sidebar links exist but there is **no** `app/(dashboard)/…/page.tsx` for:



- `/customers`

- `/designer`

- `/campaigns`



Build these when feature specs land; until then links 404.



### E. Product scope not started (see `context/project-overview.md`)



- Live **data streaming** and **agent pipeline** visualization on the dashboard (processing stages, active agents).

- **Strategy creation** flow (no `/create` route in repo today).

- **n8n-style intervention canvas** (future).

- **Auth** — explicitly out of scope for now (single company, no login).



---



## Architecture reminders (do not regress)



- Sidebar active state: `usePathname()` only — no client nav state.

- Live dashboard data: Zustand store + single hook; components stay unchanged when WS is added.

- Hover performance: `transform: translateY` + `will-change: transform`; no hover `box-shadow` transitions.

- Scroll performance: `.scroll-contain` on main and approval list scroll areas.

- New colors: hex in `@theme inline` in `globals.css`, not opaque `:root` refs for Tailwind v4.



---



## Reference



- Feature specs: `context/feature-spec/01-design.md`, `02-overwpage.md`, `03-approval.md`

- Current phase: `context/progress-tracker.md`



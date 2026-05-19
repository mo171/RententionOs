# Progress Tracker

Update this file whenever the current phase, active feature, or implementation state changes.

## Current Phase

- Feature Development — `/approvals` page

## Current Goal

- Implement the `/approvals` page: append-only approval queue, fixed-height layout, real-time ready Zustand store, premium animations.

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
- Added `shadow-primary` utility in `globals.css` for green CTA button glow
- Applied `shadow-primary` to the "Ask agent" button in `top-navbar.tsx`

## In Progress

- None

## Next Up

- Connect to live backend endpoints (WebSocket / SSE)

## Pending (Live Data Integration)

- **Approvals WebSocket**: `hooks/use-live-approvals.ts` has a stubbed WebSocket block (`// PENDING: Live Data`). When the backend is ready, connect `ws.onmessage` to `store.addApproval()` — zero UI rewrites needed.
- **Dashboard Metrics WebSocket**: `hooks/use-live-dashboard.ts` has the same stub. Connect to `/ws/metrics` to stream KPI + alert updates into `dashboard-store.ts`.
- **Approval Action API**: `approval-row.tsx` calls `setStatus()` optimistically on the Zustand store. The API call stub (`// PENDING: POST /approvals/:id/status`) must be wired to the FastAPI backend.
- **Pagination on Approvals**: The queue currently renders all items. Marked with `// PENDING: Pagination` — add virtual scrolling or cursor-based pagination when data volume grows.

## Open Questions

- None currently.

## Architecture Decisions

- **Routing-driven sidebar**: Sidebar active state is determined purely by `usePathname()` from `next/navigation`. No client state is needed — the active highlight is a deterministic function of the URL. This is the most correct and idiomatic approach in Next.js App Router.
- **Zustand for live data**: All dashboard data (KPIs, Alerts, Strategies) lives in `store/dashboard-store.ts`. Components consume this store directly. When live data is introduced (WebSocket/SSE), only the `hooks/use-live-dashboard.ts` hook needs to change — zero component rewrites.
- **GPU-safe hover animations**: All interactive cards use `transform: translateY` + `will-change: transform` for hover states. `box-shadow` and `background-color` transitions trigger browser paint cycles and were removed as a performance rule.
- **CSS Containment on scroll container**: The main scrollable `<main>` uses `contain: layout style` (via `.scroll-contain`) to create a paint containment boundary. This prevents the sidebar and topnav from being repainted when the main content scrolls.
- **`shadow-primary` in globals.css**: A one-purpose utility that adds a green ambient glow only to primary CTA elements. Kept separate from the base token system so it does not accidentally propagate to other green-colored elements (e.g., state badges).
- **Alert Center fixed height**: Fixed height with internal overflow scroll (max 3 items visible). "View All" toggles the visible count without unmounting the component, preserving scroll position.

## Session Notes

- Dev server is running on `npm run dev` at port 3000.
- The overview route is at `/overview` (served by `app/(dashboard)/overview/page.tsx`).
- Do not use `box-shadow` for hover effects — use `transform` only for perf.
- All new colors MUST be declared as hex values inside `@theme inline` in `globals.css`, not via `:root` var references.

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

## Summary of commits goes here

### 1 Design-theme setup
- Initialized Next.js boilerplate and cleaned up default SVGs and CSS.
- Configured Tailwind CSS v4 in `globals.css` with exact design tokens from `ui-context.md` (warm off-white background, primary green button styles, semantic colors).
- Set up `shadcn/ui`, `lucide-react`, and the `cn()` utility.
- Added all shadcn primitive UI components.
- Wrapped application in `<TooltipProvider>` for component compatibility.
- Fixed Tailwind v4 opacity modifiers by explicitly declaring hex colors in the `@theme inline` block.

2. Dashboard overview page 
- Finished the `/overview` dashboard page with fixed layout (sidebar + topnav + scrollable main). All components and layouts are implemented using Tailwind CSS and shadcn/ui primitives. The page includes:
- **Fixed Sidebar** — static navigation (Overview, Strategies, Inbox, Insights, Settings) with current route highlighting via Next.js App Router pathname matching.
- **Fixed TopNavbar** — branding, workspace selector, AI chat trigger button, user profile dropdown.
- **KPI Cards** — summary metrics (Conversion, Revenue, LTV, Retention) with color-coded sparklines and trend indicators.
- **Customer Journey Flow** — visual diagram of acquisition > activation > retention > monetization steps with live indicators.
- **Alert Center** — critical alerts and anomalies (fixed height, "View All" toggle).
- **Strategies Grid** — interactive strategy cards with impact/effort scoring and shadow-glow hover effects.

**Performance and UX improvements:**
- All interactive cards use GPU-composited `transform: translateY` on hover (no `box-shadow` transitions).
- Main scrollable content uses `contain: layout style` via the `.scroll-contain` class to prevent sidebar repaint on scroll.
- Sidebar active state is driven purely by `usePathname()` from `next/navigation` — no client state needed.
- Added `will-change: transform` to interactive elements for smoother animation.
- Added a green ambient glow utility (`shadow-primary`) for CTA buttons.
- All color values are declared as hex literals in `@theme inline` to avoid Tailwind v4 opacity issues.

**Current state:**
- The `/overview` route is fully implemented and functional.
- All components are wired to `store/dashboard-store.ts` and display static mock data.
- The layout is responsive and tested on desktop viewport sizes.
- No lint errors or TypeScript issues.

**Next steps (outside scope of this session):**
- Connect to live backend endpoints (WebSocket/SSE) to populate metrics and alerts.
- Add modal/drawer flows for Strategy editing, Alert details, and Settings.
- Implement global error boundaries and loading states.
- Add keyboard shortcuts and accessibility improvements.
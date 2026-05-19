# UI Context

## Theme

Light-only. No dark mode.

The design language is a calm enterprise AI operating system with warm-neutral tones, subtle hierarchy, and workflow-oriented layouts.

This UI is intentionally quiet and analytical:
- high whitespace
- muted palette
- low contrast surfaces
- semantic accents only where needed

Primary product feel:
- enterprise retention intelligence
- autonomous agent dashboard
- workflow + analytics operating system

Design influences:
- Linear
- Notion AI
- Retool
- Stripe Dashboard (softened)
- Airtable Interfaces
- modern B2B AI tooling

Core principles:
- clarity over decoration
- subtle confidence
- premium enterprise restraint
- operational readability

All colors should be tokenized via CSS variables.

---

## Color System

### Base Surfaces

| Role | CSS Variable | Value |
|---|---|---|
| Page background | `--bg-base` | `#F7F5F0` |
| Main surface | `--bg-surface` | `#FFFFFF` |
| Elevated surface | `--bg-elevated` | `#FCFBF8` |
| Sidebar background | `--bg-sidebar` | `#F4F2ED` |
| Hover surface | `--bg-hover` | `#EFECE6` |

Warm off-white is used instead of cold gray.

---

### Borders

| Role | CSS Variable | Value |
|---|---|---|
| Default border | `--border-default` | `#E7E2D8` |
| Strong border | `--border-strong` | `#D7D0C5` |
| Divider | `--border-divider` | `#EEE9E0` |

Border rules:
- always subtle
- 1px only
- no aggressive outlines

---

### Typography Colors

| Role | CSS Variable | Value |
|---|---|---|
| Primary text | `--text-primary` | `#1F1E1A` |
| Secondary text | `--text-secondary` | `#6E6A62` |
| Muted text | `--text-muted` | `#9D988D` |
| Faint text | `--text-faint` | `#BDB7AA` |

No pure black.

---

## Accent Colors

### Primary Green

Used for:
- CTA buttons
- approvals
- live indicators
- autonomous state
- positive metrics

| Role | Variable | Value |
|---|---|---|
| Primary | `--accent-primary` | `#26B36A` |
| Soft background | `--accent-primary-dim` | `#E8F8EE` |
| Text | `--accent-primary-text` | `#198A50` |

---

### Purple / AI Logic

Used for:
- AI decisions
- uplift
- workflow logic
- branching systems

| Role | Variable | Value |
|---|---|---|
| Purple | `--accent-ai` | `#7C63FF` |
| Soft purple | `--accent-ai-dim` | `#F2EEFF` |
| Text | `--accent-ai-text` | `#6D54E8` |

---

### Blue / Monitoring

Used for:
- analytics
- tracking
- confidence states

| Role | Variable | Value |
|---|---|---|
| Blue | `--accent-info` | `#4D84FF` |
| Soft blue | `--accent-info-dim` | `#EDF3FF` |

---

### Risk / Alerts

#### High Risk

| Variable | Value |
|---|---|
| `--state-danger` | `#DF5B3D` |
| `--state-danger-dim` | `#FFF0EC` |

#### Medium Risk

| Variable | Value |
|---|---|
| `--state-warning` | `#D4A238` |
| `--state-warning-dim` | `#FFF8E6` |

#### Low Risk / Safe

| Variable | Value |
|---|---|
| `--state-safe` | `#29B06F` |
| `--state-safe-dim` | `#EBF8F1` |

---

## Typography

Primary font:
- Inter
- Geist Sans
- SF Pro Text equivalent

Tone:
- clean
- modern
- compact
- enterprise

---

### Font Roles

| Role | Style |
|---|---|
| App title | semibold |
| Section title | medium |
| Body text | regular |
| KPI metrics | semibold |
| Labels/meta | uppercase tracking-wide |

---

### Font Sizes

| Role | Class |
|---|---|
| App title | `text-lg` |
| Section heading | `text-base` |
| Card labels | `text-xs uppercase` |
| Body | `text-sm` |
| Table | `text-sm` |
| KPI numbers | `text-4xl` |

---

## Border Radius

Rounded but restrained.

| Context | Class |
|---|---|
| Chips | `rounded-full` |
| Buttons | `rounded-xl` |
| Cards | `rounded-2xl` |
| Panels | `rounded-2xl` |
| Modals | `rounded-3xl` |

No sharp corners.

---

## Shadows

Very soft.

Default:
```css
box-shadow: 0 1px 2px rgba(0,0,0,0.03);
```

Elevated:
```css
box-shadow: 0 4px 12px rgba(0,0,0,0.04);
```

No heavy shadows.

---

## Layout Architecture

Three-column enterprise shell.

### Structure

1. Left Sidebar
2. Main Workspace
3. Optional Right Context Panel

---

## Sidebar

Persistent fixed sidebar.

Approx width:
- 240px

Contains:
- logo
- version
- agent live card
- navigation
- user profile footer

Background:
```css
background: var(--bg-sidebar);
border-right: 1px solid var(--border-default);
```

---

### Sidebar Navigation

Items:
- icon
- label
- optional badge

Active item:
- subtle tinted background
- left accent marker

Example active:
```css
background: var(--bg-hover);
border-left: 2px solid var(--accent-primary);
```

---

### Sidebar Agent Card

Status card near top.

Contains:
- green dot
- agent live label
- actions saved/sent metrics

Card style:
- bordered
- rounded-xl
- subtle background

---

## Top Navigation

Height:
- 56px

Contains:
- page title
- contextual subtitle
- centered search
- refresh
- autonomous toggle
- CTA

---

### Search Input

Style:
- rounded-full
- icon left
- subtle border

```css
background: white;
border: 1px solid var(--border-default);
```

Shortcut hint:
small keyboard pill.

---

### Top Actions

Includes:
- autonomous toggle
- ask agent button

CTA:
green filled pill.

---

## Dashboard Cards

Used for:
- saved revenue
- churn rate
- AI precision

Card structure:
- small label
- large metric
- status chip
- sparkline

Card style:
```css
background: white;
border: 1px solid var(--border-default);
border-radius: 20px;
padding: 24px;
```

---

## Tables

Enterprise data table.

Characteristics:
- white surface
- row separators only
- no zebra striping

Used in customer prioritization.

Columns:
- customer
- plan
- MRR
- tenure
- risk
- uplift
- LTV
- action

---

### Table Row

Hover:
```css
background: var(--bg-hover);
```

Rows are spacious but dense enough for ops.

---

### Inline Progress Bars

Used for:
- risk
- uplift

Style:
- segmented mini bars
- semantic colors

Examples:
- red/orange for risk
- purple for uplift
- green for positive

---

## Chips / Badges

Extensive pill usage.

Examples:
- Live
- Email + CSM
- High Risk
- Education seq.
- Monitoring

Style:
```css
border-radius: 9999px;
padding: 4px 10px;
font-size: 12px;
font-weight: 500;
```

Background:
semantic dim colors.

---

## Workflow Builder

Core product area.

Built like React Flow / node graph editor.

---

### Canvas

Background:
- white/off-white
- dotted grid

```css
background-image: radial-gradient(circle, #E7E1D7 1px, transparent 1px);
background-size: 20px 20px;
```

---

### Canvas Layout

Left:
- action library

Center:
- workflow graph

Top:
- controls

---

### Action Library

Panel containing grouped blocks.

Groups:
- triggers
- logic
- actions

Block style:
- white cards
- subtle border
- rounded-xl

---

### Nodes

Node structure:
- icon
- title
- subtitle

Examples:
- Trigger
- Persuadable?
- Send Exec Check-in
- Track

Node styles:
- white cards
- semantic border/accent

Node categories:
- trigger = amber
- logic = purple
- action = green
- analytics = blue

---

### Edges

Style:
- curved
- smooth
- neutral gray

Thin strokes.

Conditional labels:
- true
- false

As floating pills.

---

### Canvas Controls

Top-left:
- zoom in
- zoom out
- fit

Minimal icon buttons.

---

## Charts

Chart types visible:
- sparkline
- sankey flow chart

---

### Sankey Style

Soft pastel blocks + flows.

Palette:
- purple
- green
- coral
- gray

Rounded containers.

Minimal labels.

No axis clutter.

---

## Alert Center

Right-side operational list.

Card structure:
- company
- issue summary
- risk badge
- actions

Actions:
- Ignore
- Approve

Card style:
- subtle border
- semantic left border

Example:
```css
border-left: 2px solid var(--state-danger);
```

---

## Buttons

### Primary

Green filled.

```css
background: var(--accent-primary);
color: white;
border-radius: 12px;
```

Used for:
- Run
- Ask Agent
- Approve

---

### Secondary

White surface.

```css
background: white;
border: 1px solid var(--border-default);
```

---

### Ghost

Text only or icon only.

Minimal hover tint.

---

## Inputs

Input style:
- subtle border
- white fill
- rounded-xl/full

Focus:
```css
outline: 2px solid rgba(38,179,106,0.15);
```

No neon glow.

---

## Icons

Library:
- Lucide React

Style:
- outline only
- muted stroke

Sizes:
- inline: `h-4 w-4`
- button: `h-5 w-5`
- feature icon: `h-8 w-8`

---

## Motion

Very restrained.

Transitions:
```css
transition: all 0.2s ease-out;
```

Hover:
- subtle tint
- slight border emphasis

No scale bounce.

---

## Spacing System

Spacing rhythm:
- 4
- 8
- 12
- 16
- 24
- 32

Cards:
- `p-6`

Sections:
- `gap-6`

Rows:
- compact but breathable

---

## Component Stack Recommendation

Best implementation stack:
- Next.js
- Tailwind
- shadcn/ui
- React Flow
- Recharts
- TanStack Table

---

## Tailwind Semantic Tokens

Use aliases only.

Recommended:
- `bg-base`
- `bg-surface`
- `bg-sidebar`
- `bg-hover`
- `border-default`
- `text-copy-primary`
- `text-copy-secondary`
- `text-copy-muted`
- `text-brand`
- `bg-brand-soft`
- `text-risk-high`
- `text-risk-medium`
- `text-risk-low`

Avoid raw Tailwind colors.

---

## Product Personality

Keywords:
- calm
- executive
- trustworthy
- autonomous
- analytical
- premium enterprise
- AI-native ops

This UI should feel like:
"an autonomous business intelligence operating system used by executives and revenue teams."
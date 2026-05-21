# Retention OS 

## Problem Statement
Early Risk Detection & Customer Prioritization:
Identify high-value customers showing early disengagement and
focus on those most likely to be retained.

Causal Uplift Segmentation & AI-Guided Actions:
Segment customers into stay, leave, and persuadable groups, then
select the most effective and resource-efficient intervention
for each customer.

## Overview
IDEA / SOLUTION:
RetentionOS is an AI-driven predictive customer
outreach platform that uses churn prediction, causal
uplift modeling, and profit-aware decision intelligence
to automatically identify persuadable customers and
execute personalized retention strategies.

Main Points of Interest -
• Built for Customer-Driven Industries: Banks, telecom,
subscription platforms, and digital services to detect
churn early and protect customer lifetime value.

• Automated Intelligent Retention: Identifies high-value
at-risk customers (LTV + churn), selects the best intervention strategy (uplifting models), and executes outreach across multiple channels. (agentic AI + web-hooks)

Unique Value Proposition (UVP)

RetentionOS moves beyond traditional churn prediction by
identifying persuadable customers and executing
profit-optimized retention actions using causal uplift
intelligence and AI-driven strategy decisions.

## Goals

1. Financial & Risk Intelligence:
    LTV-Based customer eligibility filtering with ML-driven churn risk detection
2. Casual Uplift Intelligence
    identifies customers who can actually be influenced by retention interventions
3. AI Strategy Decision Engine
    Agent-Baed reasoning selects the best retention strategy using churn risk, uplift score, and customer value
4. Context & Network Intelligence
    Uses knowesge graphs and influence modeling to detect hidden churn risks
5. Profit Guardrails & Market Awareness
    Ensures ROI-positive actions, using policy monitoring, and strategy simulation
6. Personalized Multi-Channel Outreach
    Automates targeted engagement via email, SMS, app notifications, or calls.


## Core User Flow

1. No authorization for now — single company streams customer data.
2. Streamed data is processed and displayed on the dashboard (`/overview`, `/causal-model`).
3. Actionable insights and agent activity are shown live.
4. ML pipeline selects high-value at-risk users and passes a payload to the **agentic intervention pipeline** (LangGraph).
5. **Human-in-the-loop (before any customer email):** Agents draft compliance reasoning, channel, schedule, and message copy. The intervention lands in **`/approvals`** — the admin reviews compliance reasoning, **edits the message if needed**, then **Approve** or **Reject**. No email/SMS/push is sent until the admin approves.
6. After approval, delivery runs at the strategy agent’s `scheduled_time` (Trigger.dev + Resend/Twilio).
7. Outcomes and metrics are shown back on the dashboard.


## Features

### Data Streaming

- continous data is streamed
- the proccessing of the stream data is shown live on web
- agents that are working is shown ive on web

### Financial & Risk Intelligence (LTV & CHURN)

-the data that is being stream is of customer who are doing various activities on the internet who are subscribed to bank subscriptions
-based on that thier LTV and churn are calculated
- to save computer power first ltv is calculated if user avg ltv is above a particualr level then only further processing of the user is done
- The ltv pipline gives avg ltv by historical ltv  and predictive ltv (using predictive ltv model) 
-if user above a partcicular ltv are shortlisted they go for further proccesing
-that user goes through churn prediction model 

### Casual Uplift Intelligence - Persudable intervention (VIMP)

- If user with high ltv and churn risk then they are sent to uplift model
- user with particular churn risk (moderate to high) are sent in this model
- we are using meta: x-leaener #multitreament model to predict the upliftment score 
of user in 5%,10%,15% and 20% 
- then after this the json output is given to Treatment Optmizer
- so the formula I used [Expected Profit=(uplift×CLV)−treatment cost] 
-pseudo code
-this happens in treatment optmizer 


```python
best_profit = -999999
best_treatment = None

for treatment in treatments:
    profit = uplift[treatment] * clv - cost[treatment]

    if profit > best_profit:
        best_profit = profit
        best_treatment = treatment

print("Best Treatment:", best_treatment)
print("Expected Profit:", best_profit)
```

- output 
```python
{
  "best_treatment": "discount_12",
  "expected_profit": 1420
}

```

## Intervention strategy (agentic pipeline)

After ML treatment optimization, selected users enter the **LangGraph intervention pipeline** (`backend/services/agents/intervention_graph.py`):

```python
{
  "user_id": 123,
  "best_discount": "10%",
  "expected_profit": 1400
}
```

| Step | Agent | Output |
|------|--------|--------|
| 1 | **Compliance** (CRAG) | Policy gate; `should_intervene` + reasoning trace |
| 2 | **Strategy** | Channel (`Email`, `SMS`, `Push Notification`) + `scheduled_time` from subscriber history |
| 3 | **Writer** | Draft message (HTML email template, CTA, no emojis) |
| 4 | **Meta Tribe** | Hook/tone review; corrective loop (max 3 revisions) |
| 5 | **Human approval** (`/approvals`) | Admin reviews reasoning, **tweaks message copy**, Approve or Reject — **required before send** |
| 6 | **Dispatch** | `send_message` (Resend for email; Twilio stub; push/SMS deferred) — only after admin Approve, at `scheduled_time` |

**Human-in-the-loop:** The frontend approvals queue is not optional polish — it is the production gate. Backend dev tests (`backend/test.py`) may run dispatch immediately; production must stop after node 4 and expose the draft to `/approvals` until an admin accepts (optionally with edited copy).

Future: TRIBE v2 neural hook scoring (`backend/docs/FUTURE_TRIBE_V2.md`); additional agents TBD.

### Future feature- n8n like canvas

- n8n like canvas
- in which user can make custom n8n like automation with our models and spin custom agents
-uses crew a.i

## Should Follow

### Frontend - all to 2026
 - nextjs- latest
 -shadcn-latest all shadcn compoenents will be availabe locally use that onyly has base varient and improvise on that
 -tailwind css -latest
 - best frontend strategies and method
 -components breakdown

### Backend -
- python - 3.10 - most stable
- fastapi -latest 2026
-langchain - latest
-langgraph  -latest
-inngest - latest

### Db
postgress sql- supabase
redis-any free version but important app should be fast 


## Success Criteria

1. agents working and personal message is reaching to end user\
2. mmodel predicting accurately 
3. functional and scalble (optmistic u.i)

## Pending

### Human-in-the-loop wiring (priority)

- **Approvals queue from backend:** When LangGraph finishes nodes 1–4, push a pending `Approval` to `/approvals` (WebSocket or REST) — **do not auto-dispatch** in production.
- **Admin edit before send:** `PATCH /api/approvals/:id` for `messagePreview` tweaks; dispatch uses the final edited copy.
- **Approve → send:** `POST /api/approvals/:id/status` with `approved` triggers Trigger.dev `wait.until(scheduled_time)` then `send_message`.
- **Reject:** No email to customer; item dismissed in queue.

### Live data & UX

- **Dashboard Metrics WebSocket** (`hooks/use-live-dashboard.ts`): `/ws/metrics` → `dashboard-store.ts`.
- **Approvals WebSocket** (`hooks/use-live-approvals.ts`): `/ws/approvals` → `store.addApproval()` (append-only).
- **Approval Action API** (`approval-detail-view.tsx`): Wire Approve/Reject and message PATCH to FastAPI.
- **Pagination / Virtual Scroll** (`approval-list-panel.tsx`): When queue volume grows.
- **`POST /api/interventions/start`:** ML payload → Trigger.dev → graph → pending approval record.

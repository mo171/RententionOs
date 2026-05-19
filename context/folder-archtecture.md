# RetentionOS Project Folder Structure

Production-grade folder conventions for:
- FastAPI backend
- LangChain + LangGraph agent workflows
- Supabase/Postgres
- Next.js frontend
- Real-time dashboard + intervention workflows

---

# Root Structure

```bash
retention-os/
├── backend/
├── frontend/
├── docs/
├── .env
├── docker-compose.yml
├── README.md
```

---

# Backend Structure (FastAPI + LangChain)

```bash
backend/
├── controllers/
├── models/
├── prompts/
├── routes/
├── services/
├── utils/
├── migrations/
├── main.py
├── requirements.txt
└── .env
```

Backend follows layered architecture:

Request Flow:

Route
→ Controller
→ Service
→ Utils / External Systems

---

## backend/routes/

```bash
routes/
├── example_routes.py
```

Purpose:
- Define API endpoints only
- Register route paths
- Minimal request parsing
- Call controller functions

Contains:
- API route definitions
- route decorators
- request/response wiring only

Should NOT contain:
- business logic
- SQL logic
- LangChain logic
- model inference logic

Example responsibility:

```python
@router.post("/predict-churn")
async def predict_churn(payload: ChurnRequest):
    return await churn_controller.predict(payload)
```

---

## backend/controllers/

```bash
controllers/
├── example_controller.py
```

Purpose:
- API orchestration layer
- Combines multiple services
- Converts service outputs into API responses

Contains:
- orchestration logic
- service composition
- response shaping
- websocket event management

Example:

Controller may:
1. receive request
2. call LTV service
3. call churn service
4. call uplift service
5. call treatment optimizer
6. return final result

Should NOT contain:
- raw SQL
- prompt definitions
- long utility functions

Think:
"connect multiple services into one workflow"

---

## backend/services/

```bash
services/
├── example_service.py
or 
├── example_service/example1_1.py and example1_2.py
```

Purpose:
Core business logic lives here.

Contains:
- ML model logic
- LangChain workflows
- scoring pipelines
- business rules
- optimization logic



This is where most code should exist.

Should contain:
- reusable domain logic


---

## backend/models/

```bash
models/
├── customer_models.py
├── intervention_models.py
├── websocket_models.py
├── response_models.py
```

Purpose:
Pydantic schemas only.

Contains:
- request schemas
- response schemas
- validation schemas
- internal typed contracts

Example:

```python
class ChurnRequest(BaseModel):
    user_id: int
    transaction_count: int
```

Rules:
- all API schemas go here
- strict typing
- validation before controller execution

Should NOT contain:
- business logic

---

## backend/prompts/

```bash
prompts/
├── rag_prompts.py
├── intervention_prompts.py
```

Purpose:
Central prompt registry.

Contains:
ALL prompts used by agents.

Examples:

RAG prompts:
- query rewrite prompt
- retrieval grading prompt
- relevance checking prompt
- reasoning prompt
- answer generation prompt

Intervention prompts:
- retention email prompt
- SMS prompt
- WhatsApp prompt
- corrective response prompt

Rules:
- keep prompts centralized
- avoid prompts scattered across services

Good:

```python
RETRIEVAL_GRADER_PROMPT = """
Grade relevance of retrieved chunks...
"""
```

Bad:
prompt strings inside service files.

---

## backend/utils/

```bash
utils/
├── llm.py
├── langchain_config.py
├── supabase_client.py
├── redis_client.py
├── logger.py
and so on
```

Purpose:
Infrastructure + shared utilities.

Contains:
- LLM initialization
- LangChain configuration
- database clients
- redis clients
- shared helper functions
- logging setup
- constants

Examples:

llm.py
- OpenAI/Anthropic model setup

langchain_config.py
- retrievers
- memory
- chains

supabase_client.py
- DB connection

Rules:
No business logic here.

This folder is infra only.

---

## backend/migrations/

```bash
migrations/
├── 001_create_customers.sql
├── 002_create_interventions.sql
├── 003_create_campaign_runs.sql
...
```

Purpose:
Raw SQL migrations.

Contains:
- schema changes
- indexes
- triggers
- constraints

Rules:
- one migration per schema change
- never manually mutate production DB

---

## backend/main.py

Purpose:
Application entry point.

Contains:
- FastAPI initialization
- middleware
- CORS
- route registration

Example:

```python
app.include_router(churn_router)
```

Should stay thin.

---

# Frontend Structure (Next.js)

```bash
frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   ├── store/
│   └── styles/
├── public/
└── package.json
```

---

## frontend/src/app/

```bash
app/
├── dashboard/
├── interventions/
├── analytics/
├── api/
├── layout.tsx
├── page.tsx
```

Purpose:
App router pages.

Contains:
- route pages
- layouts
- loading states
- error states

Should NOT contain:
- business logic

---

## frontend/src/components/

```bash
components/
├── ui/
├── dashboard/
├── charts/
├── tables/
├── layout/
```

Purpose:
Pure reusable UI.

Contains:
- cards
- buttons
- modals
- tables
- chart wrappers

Rules:
No business logic.

---

## frontend/src/features/

```bash
features/
├── churn/
├── interventions/
├── streaming/
├── analytics/
```

Purpose:
Feature-scoped logic.

Contains:
- feature components
- feature actions
- domain hooks

Example:
intervention feature:
- intervention table
- approval modal
- campaign actions

Think:
"business feature grouping"

---

## frontend/src/hooks/

```bash
hooks/
├── use-websocket.ts
├── use-churn-stream.ts
├── use-intervention.ts
```

Purpose:
React hooks only.

Contains:
- reusable frontend logic
- websocket subscriptions
- stateful UI logic
- fetch hook

---

## frontend/src/lib/

```bash
lib/
├── api.ts
├── supabase.ts
├── websocket.ts
├── utils.ts
```

Purpose:
Frontend utilities + client setup.

Contains:
- API client
- Supabase browser client
- websocket helpers
- helper functions

---

## frontend/src/store/

```bash
store/
├── dashboard-store.ts
├── intervention-store.ts
├── websocket-store.ts
```

- `trigger` — Long-running background jobs: AI design generation and spec generation.
- `lib` — Shared infrastructure: supabase client, access control helpers, and utilities.
- `lib/wesbscoket`- websocket connection and streaming

Purpose:
Global client state.

Contains:
Zustand stores for:
- dashboard filters
- selected customers
- live stream state
- intervention workflow state

---

## frontend/src/styles/

```bash
styles/
├── globals.css
```

Purpose:
Global styling tokens.

Contains:
- CSS variables
- theme tokens
- base styling

Rules:
No raw colors.
Use design tokens only.

---

# Important Rules

## Routes
Thin.

## Controllers
Combine services.

## Services
Business logic.

## Models
Pydantic only.

## Prompts
All prompts centralized.

## Utils
Infrastructure/config only.

## Components
UI only.(basic reusable u.i )

## Features
Domain grouping. and flow whole route compoents bulding bloacks and logic 

## Hooks
React hooks only.

## Store
Global frontend state.

---

# IMP

- the files.py or file.ts is just exampless no hard and fast rule that only that much file should be used 
- also u can use folder inside folder
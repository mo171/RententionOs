# Architecture Context


## Stack

| Layer                    | Technology                                        | Role                                                                                              |
| ------------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Framework                | Next.js 16 + TypeScript                           | Full-stack frontend with server/client boundaries, dashboard rendering, API integration           |
| UI                       | Tailwind CSS + shadcn/ui                          | Design system, dashboard components, tables, charts, workflow panels                              |
| State Management         | Zustand                                           | Lightweight client state for dashboard filters, live workflow state, selected customer sessions   |
| Charts / Analytics UI    | Recharts                                          | Churn graphs, uplift distributions, intervention ROI metrics, agent monitoring charts             |
| Auth                     | Supabase Auth                                     | Organization login, protected dashboard routes, session handling                                  |
| Backend API              | FastAPI                                           | Core backend APIs, model serving, intervention orchestration endpoints                            |
| AI / Agents              | LangChain + LangGraph                             | Agent workflows, message generation agents, tool orchestration, multi-step intervention pipelines |
| Workflow Orchestration   | Inngest                                           | Durable background jobs, async processing, scheduled retraining, campaign execution workflows     |
| ML Layer                 | Python (scikit-learn, XGBoost, EconML / CausalML) | Churn prediction, predictive LTV, uplift modeling (X-Learner / multi-treatment models)            |
| Database                 | Supabase PostgreSQL                               | Customers, interventions, runs, experiments, model metadata, campaign history                     |
| Cache / Realtime State   | Redis                                             | Live scoring cache, workflow states, temporary model outputs, streaming state                     |
| Event / Stream Ingestion | Webhooks + Inngest Events                         | Customer activity ingestion, pseudo-streaming for MVP, event triggers                             |
| File / Artifact Storage  | Supabase Storage                                  | Generated reports, exported campaign artifacts, model outputs, logs                               |
                  |
| Notifications / Outreach | Twilio + Resend                                   | SMS, WhatsApp/email intervention delivery                                                         |
| Background Queue Memory  | Redis Streams (optional phase 2)                  | Higher-throughput event pipelines if moving beyond webhook-style MVP                              |
| Deployment (Frontend)    | Vercel                                            | Next.js hosting and frontend deployment                                                           |
| Deployment (Backend)     | Railway / Render / VPS Docker                     | FastAPI, workers, Redis, orchestration services                                                   |
| Containerization         | Docker                                            | Environment consistency, backend services, deployment portability                                 |


## System Boundaries

- `hooks`- overall for frontend management and backend fetch 
- `hooks/api` —  request handlers: input validation,  checks, task triggering, and persistence.
- `trigger` — Long-running background jobs: AI design generation and spec generation.
- `lib` — Shared infrastructure: supabase client, access control helpers, and utilities.
- `lib/wesbscoket`- websocket connection and streaming
- `components` — UI composition: canvas surfaces, sidebars, dialogs, and interactive elements.
- `supabase postgress sql- give me migration sql command` — Database schema and generated client output.
- `store`- zustand store for storing and statemangement 

- ### no data (which dosent updates perodically or changes is triggerd) on the frontend should be fetched again and again used store or caching 





## Invariants

1. Request handlers do not run long-lived AI work — that belongs in background tasks.
2. Metadata and large generated artifacts are stored in separate layers.
3. Client components are used only where browser interactivity or real-time state requires them.


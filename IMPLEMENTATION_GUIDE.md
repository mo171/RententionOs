# RetentionOS Complete Integration Guide

## Architecture Overview

RetentionOS is a four-phase autonomous customer retention pipeline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PHASE 1: ML PIPELINE                             │
│                      (Gatekeeper Orchestrator)                         │
└─────────────────────────────────────────────────────────────────────────┘
    ↓
  Layer 2: LTV Eligibility Filter (score_ltv_customer)
  ├─ Historical LTV + Predictive 12-month LTV
  ├─ Threshold: > 0.2
  └─ Output: LTVScoreResponse
    ↓
  Layer 3: Churn Risk Filter (score_churn_customer)
  ├─ XGBoost churn probability
  ├─ Threshold: > 0.5 (high-risk)
  └─ Output: ChurnScoreResponse
    ↓
  Layer 4: Causal Uplift & Treatment Optimizer
  ├─ X-Learner meta-algorithm (M0, M1 models)
  ├─ Estimate CATE (Conditional Average Treatment Effect)
  ├─ Identify "Persuadables" (M1 > M0)
  ├─ Calculate: Expected Profit = (Uplift × LTV) - Cost
  ├─ Threshold: > 0
  └─ Output: CausalScoreResponse with best_treatment
    ↓
  Result: InterventionPayload (if all gates passed)

┌─────────────────────────────────────────────────────────────────────────┐
│               PHASE 2: AGENTIC INTERVENTION GRAPH                       │
│                    (LangGraph 4-Node Pipeline)                         │
└─────────────────────────────────────────────────────────────────────────┘
    ↓
  Node 1: Compliance Agent (CRAG)
  ├─ Input: InterventionPayload
  ├─ Process:
  │   1. Generate 3 multi-queries for policy retrieval
  │   2. Retrieve policy chunks (RAG with cosine fallback)
  │   3. Rerank & fuse (RRF algorithm)
  │   4. Grade relevance of chunks
  │   5. Generate reasoning trace (LLM chain-of-thought)
  │   6. Generate verdict (JSON)
  ├─ HARD STOP if no relevant chunks found
  └─ Output: ComplianceResult (intervene: bool, reasoning, confidence)
    ↓
  Node 2: Strategy Agent
  ├─ Input: payload, compliance_result, subscriber_profile
  ├─ Process:
  │   1. Fetch subscriber from Supabase
  │   2. Fetch interaction history (email, SMS, push opens/clicks)
  │   3. LLM decides: channel (Email, SMS, Push), scheduled_time (UTC ISO)
  │   4. Validate against opt-outs and timezone
  └─ Output: StrategyResult (channel, scheduled_time, reasoning, confidence)
    ↓
  Node 3: Message Writer
  ├─ Input: strategy_result, compliance_result, subscriber_profile
  ├─ Process:
  │   1. Generate message (LLM - gpt-4o for Email, gpt-4o-mini for others)
  │   2. Parse JSON: subject, body_plain, body_html, cta_text, cta_url
  │   3. Validate no emojis (regex check)
  │   4. Build decorative HTML (for Email)
  │   5. Return MessageDraft
  ├─ Supports revision loop (max 3 attempts)
  └─ Output: MessageDraft (channel, subject, body_plain, body_html, cta_*)
    ↓
  Node 4: Meta Tribe Reviewer
  ├─ Input: current_draft (MessageDraft)
  ├─ Process:
  │   1. LLM evaluates hook strength, urgency, CTA clarity
  │   2. Score 1-10, approve if >= 7 AND hook strong AND CTA clear
  │   3. Reject weak openings, missing CTAs, or emojis
  │   4. Return ReviewResult
  ├─ Revision loop: if rejected, go back to Node 3 (max 3 times)
  └─ Output: ReviewResult (approved: bool, score, feedback)
    ↓
  [PRODUCTION GATE]
  └─ Persist to Supabase pending_approvals table (status: pending)

┌─────────────────────────────────────────────────────────────────────────┐
│           PHASE 3: HUMAN-IN-THE-LOOP (HITL) & APPROVAL QUEUE           │
│                      (Next.js Frontend + WebSocket)                    │
└─────────────────────────────────────────────────────────────────────────┘
    ↓
  /approvals Page
  ├─ Displays: compliance reasoning, strategy choice, draft message
  ├─ Admin can: view → edit message → approve/reject
  ├─ WebSocket: real-time updates (/ws/approvals)
  └─ API Endpoints:
      ├─ GET /api/approvals → list all pending
      ├─ GET /api/approvals/{id} → fetch one
      ├─ PATCH /api/approvals/{id} → admin edits message
      ├─ POST /api/approvals/{id}/approve → trigger dispatch
      └─ POST /api/approvals/{id}/reject → mark rejected

┌─────────────────────────────────────────────────────────────────────────┐
│        PHASE 4: MULTI-CHANNEL DISPATCH (Twilio + Resend)               │
│              (Trigger.dev Orchestration for Scheduled Send)            │
└─────────────────────────────────────────────────────────────────────────┘
    ↓
  Dispatch Agent (triggered by approval)
  ├─ Input: approved MessageDraft + scheduled_time from strategy
  ├─ Channels:
  │   ├─ Email: Resend API
  │   ├─ WhatsApp: Twilio SDK
  │   ├─ SMS: Twilio SDK (skipped per spec)
  │   └─ Push: Skipped (stub)
  ├─ Timing: Trigger.dev schedules send at strategy_result.scheduled_time
  └─ Output: SendMessageResult (success, provider, message_id, error)

```

## Key Components & File Locations

### ML Pipeline (Phase 1)
- **Orchestrator**: `backend/services/gatekeeper/gatekeeper_pipeline.py`
  - Function: `process_gatekeeper_pipeline(customers, trigger_inngest=False)`
  - Returns: `List[InterventionPayload], Dict[stats]`
  - Statistics: LTV filter, churn filter, uplift filter, profit filter results

- **LTV Service**: `backend/services/ltv/ltv_service.py`
  - Function: `score_customer(customer) -> LTVScoreResponse`
  - Output: `is_eligible_for_retention`, `predictive_12m_ltv`

- **Churn Service**: `backend/services/churn/churn_service.py`
  - Function: `score_customer(customer) -> ChurnScoreResponse`
  - Output: `churn_probability`

- **Causal Uplift**: `backend/services/causal/uplift_service.py`
  - Function: `score_customer(customer, clv) -> CausalScoreResponse`
  - Output: `segment`, `uplift_score`, `best_treatment` (with expected_profit)

### Agentic Intervention (Phase 2)
- **Graph Definition**: `backend/services/agents/intervention_graph.py`
  - Functions:
    - `build_intervention_graph()` → dev graph (ends with dispatch)
    - `build_production_graph()` → prod graph (ends with persist_approval)
    - `run_intervention_graph(payload, production_mode) -> InterventionGraphState`

- **Nodes**:
  - **Compliance (Node 1)**: `backend/services/agents/compliance_agent.py`
    - Service: `backend/services/rag/compliance_service.py`
    - RAG: `backend/services/rag/retriever.py`, `reranker.py`, `grader.py`, `ingestor.py`
    - Prompts: `backend/prompts/compliance_prompts.py`
    - Output: `ComplianceResult(intervene, reasoning, policy_source, confidence)`

  - **Strategy (Node 2)**: `backend/services/agents/strategy_agent.py`
    - Service: `backend/services/strategy/strategy_service.py`
    - Prompts: `backend/prompts/strategy_prompts.py`
    - Output: `StrategyResult(channel, scheduled_time, reasoning, confidence)`

  - **Writer (Node 3)**: `backend/services/agents/writer_agent.py`
    - Service: `backend/services/writer/writer_service.py`
    - Prompts: `backend/prompts/writer_prompts.py`
    - Output: `MessageDraft(channel, subject, body_plain, body_html, cta_*)`

  - **Reviewer (Node 4)**: `backend/services/agents/reviewer_agent.py`
    - Service: `backend/services/meta_tribe/meta_tribe_service.py`
    - Prompts: `backend/prompts/reviewer_prompts.py`
    - Output: `ReviewResult(approved, score, feedback)`

  - **Dispatch**: `backend/services/agents/dispatch_agent.py`
    - Tool: `backend/services/tools/send_message.py`
    - Output: `SendMessageResult(success, channel, provider, message_id, error)`

  - **Persist to Supabase**: `backend/services/agents/persist_approval_agent.py`
    - Writes to `pending_approvals` table

### HITL Approval Queue (Phase 3)
- **API Routes**: `backend/api/approval_routes.py`
  - `GET /api/approvals` → list all (limit 50, ordered by created_at)
  - `GET /api/approvals/{id}` → fetch one
  - `PATCH /api/approvals/{id}` → edit message draft
  - `POST /api/approvals/{id}/approve` → approve + dispatch
  - `POST /api/approvals/{id}/reject` → reject

- **WebSocket**: `backend/api/websocket_routes.py`
  - Endpoint: `WS /ws/approvals`
  - Manager: `ConnectionManager` class with `broadcast()` method
  - Broadcast on: approval_created, approval_updated, approval_approved, approval_rejected

### Dispatch (Phase 4)
- **Send Tool**: `backend/services/tools/send_message.py`
  - Function: `send_message(draft, to_email, to_phone, test_mode) -> SendMessageResult`
  - Channels:
    - Email: `backend/utils/resend_client.py`
    - WhatsApp: `backend/utils/twilio_client.py`
    - SMS: `backend/utils/twilio_client.py` (skipped per spec)
    - Push: Stub (skipped)

- **Trigger.dev**: `backend/utils/trigger.py`
  - Mock client for scheduling send time
  - In production: integrate actual Trigger.dev SDK

### Models & Data
- **Pydantic Models**: `backend/models/`
  - `compliance_models.py`: `InterventionPayload`, `ComplianceResult`, `RelevanceGrade`
  - `strategy_models.py`: `SubscriberProfile`, `InteractionEvent`, `StrategyResult`, `InterventionGraphState`
  - `message_models.py`: `MessageDraft`, `ReviewResult`, `SendMessageResult`
  - `approval_models.py`: `ApprovalResponse` (for UI), `ApprovalMessageEdit`, `ApprovalStatusUpdate`
  - `ltv_models.py`, `churn_models.py`, `causal_models.py`: Response models for ML services

- **Synthetic Data**: `backend/scripts/generate_synthetic_data.py`
  - Generates 10,000 profiles (configurable)
  - Splits into 5 segments: Student (15%), Jan Dhan (25%), Salaried (40%), MSME (15%), HNI (5%)
  - Includes: job_change, relocation, upi_frequency_drop, app_login_decay flags

- **Database Migrations**: `backend/migrations/`
  - `005_gatekeeper_schema.sql`: LTV metrics, network edges, subscriber enhancements
  - `006_pending_approvals.sql`: pending_approvals table schema

### Inngest Workflow
- **Client**: `backend/inngest_client.py`
- **Routes**: `backend/api/inngest_routes.py`
- **Function**: `process_retention_workflow`
  - Trigger: `gatekeeper/process.retention` event
  - Payload: `InterventionPayload`
  - Execution: Runs full intervention graph (dev or prod based on env)
  - Output: Final state (either dispatch result or pending approval record)

## Data Flow: End-to-End Example

### 1. Customer Streams In
```json
{
  "id": 12345,
  "segment": "Salaried",
  "age": 35,
  "balance": 250000,
  "avg_monthly_income_inr": 80000,
  "upi_transaction_ratio": 0.6,
  "churn_flag": 1,
  ...
}
```

### 2. Gatekeeper Pipeline
```
LTV: score_ltv_customer → predictive_12m_ltv = 4500.0 ✓ (> 0.2)
Churn: score_churn_customer → churn_probability = 0.68 ✓ (> 0.5)
Uplift: score_causal_customer → segment = "Persuadables", uplift = 0.12, expected_profit = 1200 ✓
→ InterventionPayload {
    user_id: 12345,
    best_discount: "10%",
    expected_profit: 1200.0,
    ltv: 4500.0,
    churn_prob: 0.68,
    uplift_score: 0.12,
    segment: "Salaried"
  }
```

### 3. Inngest Triggers
```
inngest_client.send_sync({
  "name": "gatekeeper/process.retention",
  "data": {...InterventionPayload}
})
```

### 4. Intervention Graph Executes
```
Node 1: Compliance
  - Queries: ["Is 10% discount permitted?", "Can salaried customers get discounts?", ...]
  - Retrieve from policy (Union Bank CCD Policy)
  - Grade: [chunk1 (relevant), chunk2 (relevant), chunk3 (not relevant)]
  - Verdict: intervene=true, confidence=9
  → ComplianceResult

Node 2: Strategy
  - Fetch: subscriber profile (email, timezone, preferences)
  - History: [email_open 2h ago, push_click 5h ago]
  - Decision: channel=Email (preferred), scheduled_time=2026-05-31T22:00:00Z
  → StrategyResult

Node 3: Writer
  - Subject: "Your exclusive 10% retention offer"
  - Body: "We value your business. As a Salaried member, you're eligible..."
  - HTML: Decorative email template with green CTA button
  → MessageDraft

Node 4: Reviewer
  - Score: 8/10
  - Feedback: "Strong opening, clear CTA. Approved."
  - approved: true
  → ReviewResult

Node 5: Persist (Production)
  - Insert into Supabase pending_approvals table
  - status: "pending"
  - Broadcast via WebSocket: approval_created
```

### 5. Admin Reviews & Approves
```
Admin opens /approvals page
  - Sees compliance reasoning (policy grounding)
  - Sees strategy choice (Email at 22:00 IST)
  - Sees message preview
  - Optionally edits message body
  - Clicks "Approve"

API: POST /api/approvals/{id}/approve
  - send_message(draft, to_email="customer@example.com", test_mode=false)
  - Resend sends email immediately (or Trigger.dev schedules for 22:00)
  - WebSocket: approval_approved event
```

### 6. Message Delivered
```
Subscriber receives email:
  From: RetentionOS <onboarding@resend.dev> (or verified domain)
  Subject: Your exclusive 10% retention offer
  Body: HTML template with CTA link
  
Metrics tracked:
  - send_result.success = true
  - send_result.message_id = email_uuid
```

## Key Features

### Profit Guardrail
- **Formula**: Expected Profit = (Uplift × Customer LTV) − Intervention Cost
- **Threshold**: > $0 (configurable in gatekeeper)
- **Purpose**: Ensure ROI-positive interventions only

### Policy Grounding
- **Compliance Agent**: Uses RAG to justify interventions
- **Fallback**: Local cosine similarity if pgvector fails (for dev mode)
- **Hard Stop**: If zero relevant policy chunks found → intervene=false

### No Emojis Rule
- **Enforcement**: Regex check in writer and reviewer
- **Validation**: Checked during draft generation
- **Enforcement**: Reviewer rejects if emojis found

### Revision Loop
- **Max Revisions**: 3 (configurable in intervention_graph.py)
- **Trigger**: If reviewer score < 7 or feedback provided
- **Fallback**: After 3 rejections, use fallback template

### Data Simulation
- **10,000 Profiles**: Indian banking segments
- **Segments**:
  - Student (15%): Lower balance, high UPI drop
  - Jan Dhan (25%): Micro-transactions, churn-prone
  - Salaried (40%): Mid-tier, stable income
  - MSME (15%): High transaction volume
  - HNI (5%): Highest LTV, lowest churn
- **Flags**:
  - `job_change`: 1 if job change detected (0.1 probability)
  - `relocation`: 1 if moved (0.05 probability)
  - `upi_frequency_drop`: 0.0-0.9 (higher = more churn risk)
  - `app_login_decay`: 0.0-0.9 (higher = less engaged)

## Environment Variables

```bash
# LLM
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Email
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=hello@yourdomain.com

# WhatsApp
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=+1234567890

# Inngest
INNGEST_EVENT_KEY=...
INNGEST_SIGNING_KEY=...

# Trigger.dev
TRIGGER_API_KEY=tr_...

# Mode
PRODUCTION_MODE=false
TEST_MODE=true
FORCE_EMAIL_CHANNEL=false
```

## Running the Pipeline

### 1. Generate Synthetic Data
```bash
python backend/scripts/generate_synthetic_data.py
# → Creates backend/data/indian_bank_profiles.csv (10,000 rows)
```

### 2. Train ML Models (if needed)
```bash
python backend/create_ltv_model.py
python backend/create_xgboost_churn_model.py
python backend/create_xgboost_uplift_model.py
```

### 3. Ingest Policy Document
```bash
# Upload Union Bank CCD Policy to Supabase
python backend/services/rag/ingestor.py --file path/to/policy.pdf
```

### 4. Start Backend
```bash
uvicorn backend.app:app --reload --port 8000
```

### 5. Start Frontend
```bash
cd frontend && npm run dev
# → Opens http://localhost:3000/approvals
```

### 6. Trigger Gatekeeper Pipeline
```bash
# Via API
curl -X POST http://localhost:8000/api/interventions/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 12345,
    "best_discount": "10%",
    "expected_profit": 1200.0,
    "ltv": 4500.0,
    "churn_prob": 0.68,
    "uplift_score": 0.12,
    "segment": "Salaried"
  }'

# Or programmatically
from backend.services.gatekeeper.gatekeeper_pipeline import process_gatekeeper_pipeline
import pandas as pd

customers = pd.read_csv("backend/data/indian_bank_profiles.csv").head(100).to_dict("records")
payloads, stats = process_gatekeeper_pipeline(customers, trigger_inngest=True)
```

### 7. Monitor Approvals
- Open http://localhost:3000/approvals
- WebSocket auto-updates as new approvals arrive
- Click to review, edit, approve, or reject

## Testing

### Unit Tests
```bash
pytest backend/test_e2e_pipeline.py -v
```

### E2E Integration Test
```bash
python backend/test_e2e_pipeline.py
# Tests imports, models, services, graph structure, gatekeeper flow
```

### Manual Testing
1. Generate synthetic data
2. Run gatekeeper on sample (10-100 customers)
3. Trigger Inngest for one payload
4. Monitor graph execution (logs in terminal)
5. Check pending_approvals table (Supabase UI)
6. Approve via /approvals frontend
7. Verify email/SMS delivery (Resend/Twilio logs)

## Deployment Checklist

- [ ] Set all environment variables
- [ ] Run Supabase migrations (001-006)
- [ ] Train ML models and upload artifacts
- [ ] Ingest policy documents to Supabase
- [ ] Configure Inngest credentials
- [ ] Configure Trigger.dev for scheduled sends
- [ ] Set up Resend domain verification
- [ ] Configure Twilio WhatsApp sandbox (or production)
- [ ] Deploy backend (FastAPI + Inngest handlers)
- [ ] Deploy frontend (Next.js)
- [ ] Run smoke test: gatekeeper pipeline on 10 customers
- [ ] Run E2E test: full approval workflow
- [ ] Monitor logs and errors

## Future Enhancements

1. **TRIBE v2**: Replace LLM reviewer with neural salience scoring
2. **Multi-Treatment**: Extend causal model to 5-10 discount levels
3. **A/B Testing**: Route interventions to experiment groups
4. **Churn Prediction**: Real-time churn scoring (not batch)
5. **Network Effects**: Influence scoring via PageRank
6. **Multi-Channel Scoring**: LLM-based channel fit scoring
7. **Message Personalization**: Dynamic variable injection (customer name, etc.)
8. **Compliance Versioning**: Policy document version control and archiving
9. **Audit Trail**: Full compliance and decision logging
10. **Analytics Dashboard**: Real-time KPIs (approval rate, conversion, ROI)

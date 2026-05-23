# RetentionOS

![RetentionOS banner](assets/image.png)

AI-powered customer retention platform that predicts churn, identifies persuadable users with uplift modeling, and executes profit-optimized interventions automatically.

---

## Core Flow

```text
Customer Stream
   |
   v
LTV Filtering
   |
   v
Churn Prediction
   |
   v
Causal Uplift Modeling
   |
   v
Treatment Optimization
   |
   v
AI Intervention
   |
   v
Feedback Loop
```

---

## What Is Built

- Next.js dashboard with `/overview`, `/approvals`, and `/causal-model`.
- Zustand stores for dashboard, approvals, and causal model state.
- FastAPI backend in `backend/app.py`.
- CRAG compliance agent and strategy agent groundwork using LangGraph.
- Causal uplift MVP over `backend/data/bank.csv`.
- Causal dashboard snapshot API connected to the frontend causal model page.
- Retrain button wired to the backend causal retrain endpoint.

---

## Causal Uplift Model

The uplift MVP implements an X-learner-style flow for the Bank Marketing dataset:

- Outcome `Y`: `deposit == "yes"`
- Treatment proxy `T`: `contact != "unknown"`
- Covariates `X`: customer profile, banking attributes, campaign history, and previous outcome fields
- Leakage exclusion: `duration` is excluded because it is only known after contact starts
- Treatment optimizer: evaluates `discount_5`, `discount_10`, `discount_15`, and `discount_20`
- Profit formula: `expected_profit = uplift * clv - treatment_cost`

Important modeling caveat: `bank.csv` does not include true randomized discount assignment. The current MVP uses contact availability as a proxy for proactive outreach. This is useful for dashboard and integration development, but production causal validity needs real intervention assignment logs and post-intervention outcomes.

### Causal Files

```text
backend/models/causal_models.py
backend/services/causal/uplift_service.py
backend/services/causal/treatment_optimizer.py
frontend/hooks/use-live-causal-model.ts
frontend/components/causal-model/model-metrics-strip.tsx
frontend/lib/api.ts
```

### Causal API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/causal/snapshot` | Train/load cached uplift artifacts and return the dashboard snapshot |
| `POST` | `/api/causal/retrain` | Clear cached artifacts, retrain from `bank.csv`, and return a fresh snapshot |
| `POST` | `/api/causal/score` | Score one customer and return uplift, segment, and best treatment |

### Saved Model Artifacts

The causal model now persists trained artifacts under:

```text
backend/artifacts/causal/uplift_artifacts.pkl
backend/artifacts/causal/uplift_metadata.json
```

Model evaluation outputs are saved under:

```text
backend/metrics/uplift_model_metrics.json
backend/metrics/uplift_model_report.md
backend/metrics/persuadable_customers.csv
```

The metrics bundle includes AUUC, Qini coefficient, churn precision/recall/AUC-ROC, uplift deciles, calibration diagnostics, and the profit-guarded prioritized persuadable list. It is regenerated whenever causal artifacts are saved during retraining.

Runtime behavior:

```text
First snapshot/score request
   |
   v
Load saved artifact if it exists
   |
   v
If missing, train from bank.csv and save artifact
```

`POST /api/causal/retrain` always retrains from `bank.csv`, overwrites the saved artifact, refreshes the in-memory cache, and returns the latest dashboard snapshot.

---

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | Next.js 16, TypeScript |
| UI | Tailwind CSS, shadcn/ui |
| State | Zustand |
| Charts | Recharts |
| Backend | FastAPI |
| Agents | LangChain, LangGraph |
| ML MVP | Python stdlib X-learner-style implementation |
| ML Upgrade Path | pandas, numpy, scikit-learn, XGBoost, joblib |
| Database | Supabase PostgreSQL |
| Async Jobs | Inngest / Trigger-style task orchestration |
| Notifications | Twilio, Resend |

---

## Project Structure

```text
RetentionOs/
|-- backend/
|   |-- app.py
|   |-- data/
|   |   `-- bank.csv
|   |-- artifacts/
|   |   `-- causal/
|   |       |-- uplift_artifacts.pkl
|   |       `-- uplift_metadata.json
|   |-- models/
|   |   |-- causal_models.py
|   |   |-- compliance_models.py
|   |   `-- strategy_models.py
|   |-- services/
|   |   |-- causal/
|   |   |-- agents/
|   |   |-- rag/
|   |   `-- strategy/
|   |-- prompts/
|   |-- utils/
|   |-- migrations/
|   |-- requirements.txt
|   |-- requirements-ml.txt
|   `-- requirements-agentic.txt
|
|-- frontend/
|   |-- app/
|   |-- components/
|   |-- hooks/
|   |-- lib/
|   |-- store/
|   `-- package.json
|
|-- context/
|-- assets/
`-- README.md
```

---

## Run Locally

Use two terminals: one for the backend and one for the frontend.

### 1. Backend

From the repo root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

`backend/requirements.txt` is the default install for the FastAPI backend and causal model. The current causal MVP is stdlib-only beyond FastAPI/Pydantic. Optional packages live in separate files:

- `backend/requirements-ml.txt` for pandas, scikit-learn, XGBoost, and joblib
- `backend/requirements-agentic.txt` for LangGraph, RAG, Supabase, embeddings, and Cohere

Health check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
```

If port `8000` is already occupied, either stop the existing Python process or run on another port:

```powershell
netstat -ano | Select-String ':8000'
Stop-Process -Id <PID>

# or use another port
..\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```

When using another backend port, update `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

### 2. Frontend

From a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:3000/causal-model
```

The frontend defaults to `http://localhost:8000` for backend API calls. To override it, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### Optional Agentic/RAG Dependencies

Optional production ML stack:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ml.txt
```

Only install this stack when working on compliance RAG, LangGraph agents, Supabase, or embeddings:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-agentic.txt
```

On Python 3.14, current Supabase storage dependencies can try to compile `pyiceberg`, which requires Microsoft C++ Build Tools. For agentic/RAG work, Python 3.10-3.12 is the safer environment. The causal model does not require this optional stack.

---

## Run The Uplift Model

### Get Dashboard Snapshot

This trains or loads cached uplift artifacts and returns the exact payload consumed by the causal dashboard.

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/causal/snapshot
```

### Retrain The Model

This clears the in-process cache, retrains from `backend/data/bank.csv`, saves the model to `backend/artifacts/causal/uplift_artifacts.pkl`, writes metadata to `backend/artifacts/causal/uplift_metadata.json`, and returns a fresh dashboard snapshot.

```powershell
Invoke-WebRequest -UseBasicParsing -Method Post http://127.0.0.1:8000/api/causal/retrain
```

### Score One Customer

```powershell
$body = @{
  clv = 2000
  customer = @{
    age = 59
    job = "admin."
    marital = "married"
    education = "secondary"
    default = "no"
    balance = 2343
    housing = "yes"
    loan = "no"
    contact = "unknown"
    day = 5
    month = "may"
    campaign = 1
    pdays = -1
    previous = 0
    poutcome = "unknown"
  }
} | ConvertTo-Json

Invoke-WebRequest `
  -UseBasicParsing `
  -Method Post `
  -ContentType "application/json" `
  -Body $body `
  http://127.0.0.1:8000/api/causal/score
```

The scoring response includes:

- `uplift_score`
- `propensity`
- `baseline_stay_probability`
- `treated_stay_probability`
- causal segment: `Persuadables`, `Sure Things`, `Lost Causes`, or `Sleeping Dogs`
- ranked treatment recommendations with expected profit

---

## Environment Variables

The causal MVP can run from `bank.csv` without external keys.

Agentic/RAG features need:

```env
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
LANGCHAIN_API_KEY=
TRIGGER_API_KEY=
```

---

## Verification

Known verification status:

- Backend causal routes import and register successfully.
- `/api/causal/snapshot` returns a snapshot for 11,162 rows from `bank.csv`.
- Frontend production build passes with `npm.cmd run build`.
- `npm.cmd run lint` currently fails on pre-existing unrelated lint errors in approval/UI/mobile files.

---

## Development Rules

- Keep FastAPI route handlers thin.
- Put business logic in `backend/services`.
- Put API schemas in `backend/models`.
- Keep frontend business state in Zustand stores.
- Do not refetch stable data repeatedly from components.
- Exclude post-treatment leakage fields from model covariates.
- Long-running production retraining should move to background orchestration.

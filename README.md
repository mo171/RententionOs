# RetentionOS

![RetentionOS banner](assets/image.png)

AI-powered customer retention platform that predicts churn, identifies persuadable users using uplift modeling, and executes profit-optimized interventions automatically.

---

## Core Flow

```text
Customer Stream
   ↓
LTV Filtering
   ↓
Churn Prediction
   ↓
Uplift Modeling
   ↓
Treatment Optimization
   ↓
AI Intervention
   ↓
Feedback Loop
```

---

## Features

- Churn prediction
- Predictive + historical LTV
- Multi-treatment uplift modeling
- Profit optimization engine
- AI intervention generation
- Multi-channel outreach (Email, SMS, WhatsApp)
- Real-time analytics dashboard

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
| Async Jobs | Inngest |
| Database | Supabase PostgreSQL |
| Cache | Redis |
| Storage | Supabase Storage |
| Notifications | Twilio, Resend |
| Observability | LangSmith |

---

## Project Structure

```bash
retention-os/
├── backend/
│   ├── controllers/
│   ├── models/
│   ├── prompts/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── migrations/
│   └── main.py

├── frontend/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── hooks/
│       ├── lib/
│       └── store/
```

---

## Folder Responsibilities

### Backend
- **routes/** → API endpoints only  
- **controllers/** → workflow orchestration  
- **services/** → business logic  
- **models/** → Pydantic schemas  
- **prompts/** → centralized prompts  
- **utils/** → configs, DB, LLM, helpers  
- **migrations/** → SQL schema changes  

### Frontend
- **app/** → pages/layouts  
- **components/** → reusable UI  
- **features/** → domain modules  
- **hooks/** → React hooks  
- **lib/** → API clients/utils  
- **store/** → Zustand global state  

---

## Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

```env
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
REDIS_URL=
LANGCHAIN_API_KEY=
```

---

## Development Rules

- Thin routes
- Controllers orchestrate
- Services hold logic
- Centralized prompts
- No business logic in UI
- Long-running tasks use Inngest

---

## MVP Scope

- Customer streaming
- LTV scoring
- Churn prediction
- Uplift modeling
- Treatment optimizer
- AI interventions
- Analytics dashboard
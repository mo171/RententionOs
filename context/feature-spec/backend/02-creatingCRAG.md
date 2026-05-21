Read `AGENTS.md` before starting.

we are stilling amining towards the same goal of the previous prompt , we will build the correctice rag agent

follow the `agentic plan.md` for reference

the rag is used and the core feature of the compliance agent the node 1 that we are building 

### Node 1: Compliance Agent (The Gatekeeper)
- **Role**: Ensures the proposed intervention (e.g., a 10% discount) aligns with current company policies.
- **Mechanism (Corrective RAG - CRAG)**: 
  1. Generates a query based on the input (e.g., "Are 10% discounts allowed for user 123's segment?").
  2. Retrieves policy documents from Supabase `pgvector`.
  3. Uses a grading LLM to check if the retrieved docs are relevant.
  4. Decides `intervene: True/False` and provides a `reason`.
- **Outcome**: If False, the graph terminates early (no intervention). If True, proceeds to the next agent.

now I want you to write down the implementation plan for just this agent
how it will retreive the docs the chunks and evrything the agent should be (chain of taughts type)
my plan
-query (agentic query generation more than 1 query so more than 2 docs retrevied )
- chunks - 1000,200 overlap
- embedding model - huggiing face transformer model -offline sall-MiniLM-L6-v2 embeding model
- then the retrevied doc is re ranked using cohere rerank and fused given to llm
-then prompt which gives the reason basiccaly explanation (so that it can be used in showing the desciion making process same as cursor agents shows when perfomring action)
- then other prompts which takes everything main query fused doc or orignal doc according to you and give response to other agents 
-the reponse should be something like this 
{

    intervene: true,
    reasoning: "10% discount is allowed as per policy document 'policy_name ..'
}
and also do not miss the person whos data which we are checking means the subscriber who we are eventualy goinng to interven keep that data flow 

- setup the langgraph nodes with memory state (this also goes in services folder and then tell me what should go in coontrollers)
- setup the rag logic servies inside services folder creating one more rag folder 
- then connect the compliance agent to the langgraph
- pydantic model in models folder 
- prompts in prompt folder 
- remember the routes for this will be there in routes folder (do not forget the controller , middleware(we skip middleware like auth thing for this entire project) etc)
(## we wil write the main controller pipline ones all agents and flow are setup)



Here is the full implementation plan for your review:

CRAG Compliance Agent — Implementation Plan (Node 1)
Overview
Takes this ML pipeline output:

json
{ "user_id": 123, "best_discount": "10%", "expected_profit": 1400 }
Runs a Corrective RAG pipeline against company policy docs in Supabase pgvector, outputs:

json
{ "intervene": true, "reasoning": "10% discount allowed per policy doc 'discount_policy.pdf'...", "policy_source": "discount_policy" }
Chain of Thought Pipeline
INPUT: { user_id, best_discount, expected_profit }
  │
  ▼
STEP 1: MULTI-QUERY GENERATION
  └─ LLM generates 3 distinct policy search queries from the input
  │
  ▼
STEP 2: VECTOR RETRIEVAL (Supabase pgvector)
  └─ Run all 3 queries in parallel → top-3 chunks per query → up to 9 raw chunks
  │
  ▼
STEP 3: COHERE RERANK + RECIPROCAL RANK FUSION (RRF)
  └─ Cohere reranks all chunks against the primary query
  └─ RRF fuses 3 ranked lists into 1 → top-5 unique, high-confidence chunks
  │
  ▼
STEP 4: RELEVANCE GRADER
  └─ LLM grades each chunk: relevant | not_relevant (structured JSON)
  └─ Filters to only relevant chunks
  └─ If 0 relevant → HARD STOP (intervene: false, reason: "no policy found")
  │
  ▼
STEP 5: REASONING TRACE
  └─ LLM reads request + relevant chunks → produces verbose chain-of-thought
     (same style as Cursor showing agent reasoning — displayed in UI)
  │
  ▼
STEP 6: FINAL VERDICT (structured Pydantic output)
  └─ { intervene: bool, reasoning: str, policy_source: str }
  │
  ▼
OUTPUT → LangGraph state (subscriber data flows through untouched)
Chunking & Embedding
Setting	Value
Chunk size	1000 tokens
Overlap	200 tokens
Embedding	all-MiniLM-L6-v2 (HuggingFace, offline, 384-dim)
Vector store	Supabase pgvector
Metric	Cosine similarity
Folder Layout (what gets created)
backend/
├── migrations/
│   └── 001_create_policy_vectors.sql    # pgvector table + ivfflat index
├── models/
│   └── compliance_models.py             # Pydantic schemas + TypedDict state
├── prompts/
│   └── compliance_prompts.py            # All 4 prompts centralized
├── services/
│   ├── rag/
│   │   ├── ingestor.py                  # Chunk + embed + upsert to pgvector
│   │   ├── retriever.py                 # pgvector similarity search
│   │   ├── reranker.py                  # Cohere rerank + RRF fusion
│   │   ├── grader.py                    # Per-chunk relevance grading
│   │   └── compliance_service.py        # Orchestrates the full CRAG pipeline
│   └── agents/
│       └── compliance_agent.py          # LangGraph node wrapper
├── controllers/
│   └── compliance_controller.py         # Route → service, shapes response
└── routes/
    └── compliance_routes.py             # POST /api/compliance/check (thin)
Layer Responsibilities
Layer	Does
routes/	Parse HTTP request, call controller. Nothing else.
controllers/	Call compliance_service.run(), handle errors, return HTTP response
services/rag/	Full CRAG logic — 90% of code lives here
services/agents/	LangGraph node that calls service + updates graph state
models/	Pydantic schemas + ComplianceAgentState TypedDict
prompts/	All 4 prompts (multi-query, grader, reasoning, verdict)
New Dependencies Needed
sentence-transformers    # offline HuggingFace embeddings
cohere                   # rerank API
langchain-cohere         # LangChain wrapper
langchain-community      # WebBaseLoader for test scraping
beautifulsoup4           # HTML parsing
psycopg2-binary          # Postgres driver for pgvector
New .env key:

COHERE_API_KEY=your_cohere_api_key_here
Success Criteria (Test)
test.py will:

Scrape a real online policy doc (e.g., an open-source license or public terms page)
Ingest → chunk → embed → upsert into Supabase pgvector
Run full CRAG pipeline with payload { user_id: 99, best_discount: "15%", expected_profit: 800 }
Print full trace: queries generated → chunks retrieved → grades → reasoning → final verdict
Agent self-rates confidence (1–10 with explanation)
Pass criteria: Non-empty ComplianceResult returned, policy_source cited, reasoning is coherent.

IMPORTANT

Two things needed from you before I build:

Cohere API key — Free tier at cohere.com, needed for reranker. Get your key and add it to your .env as COHERE_API_KEY=...
Supabase pgvector — Run the migration SQL I'll provide on your Supabase dashboard to create the policy_chunks table.



### the susess criteria
in test file remove the exisiting code and write the code to test the compliance agent servies and funtion that we have written (user will be uploading doc from frontend or will be provided but for now write use a webscrapper loader which loads an online doc (find a small doc on internet and you only write the retrevie question show me the response given by the system created and rate it ))
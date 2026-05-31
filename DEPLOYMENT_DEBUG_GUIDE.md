# RetentionOS: Deployment & Debugging Guide

## Critical Integration Points

### 1. Inngest Webhook
- **URL**: `http://your-backend/api/inngest`
- **Configure in**: Inngest Dashboard
- **Trigger**: `gatekeeper/process.retention` events
- **Payload**: `InterventionPayload` (JSON)

### 2. Supabase Connection
- **Tables Required**:
  - `subscribers` (must have: user_id, full_name, email, phone, timezone, preferred_channel, opt_out_*)
  - `interaction_events` (must have: user_id, channel, event_type, sent_at)
  - `policy_chunks` (must have: chunk_text, embedding, doc_name)
  - `pending_approvals` (auto-managed by persist_approval_node)
  - `ltv_metrics` (optional, for tracking)
  - `subscriber_network_edges` (optional, for influence scoring)

### 3. WebSocket Broadcast
- **Connection**: Frontend `http://localhost:3000/approvals`
- **WebSocket**: `ws://localhost:8000/ws/approvals`
- **Message Format**:
  ```json
  {
    "type": "approval_created|approval_updated|approval_approved|approval_rejected",
    "data": {...ApprovalResponse}
  }
  ```

### 4. Resend Email Integration
- **Endpoint**: POST https://api.resend.com/emails
- **From Domain**: Must be verified (not @gmail.com)
- **Test Mode**: Falls back to `onboarding@resend.dev` or TEST_RECIPIENT_EMAIL

### 5. Twilio WhatsApp
- **SDK**: `twilio-python`
- **Sandbox**: Requires WhatsApp sender ID verification
- **Format**: Phone numbers as `whatsapp:+1234567890`

## Common Integration Failures & Fixes

### Error: "No relevant policy chunks found"
**Cause**: Policy document not ingested into Supabase  
**Fix**:
```bash
python backend/services/rag/ingestor.py --file union_bank_policy.pdf
# Verify: SELECT count(*) FROM policy_chunks;
```

### Error: "Subscriber not found for user_id=X"
**Cause**: Subscriber record missing from Supabase  
**Fix**:
```sql
-- Add test subscriber
INSERT INTO subscribers (user_id, full_name, email, phone, timezone, preferred_channel)
VALUES (12345, 'John Doe', 'john@example.com', '+919876543210', 'Asia/Kolkata', 'email');
```

### Error: "HARD STOP: Compliance intervene=false"
**Cause**: Zero relevant chunks found AND graded_chunks empty  
**Fix**:
1. Check policy ingestion
2. Try with a simpler query
3. Lower match_threshold in retriever.py
4. Check embedding model availability

### Error: "Channel 'WhatsApp' not recognized"
**Cause**: Strategy agent returned unexpected channel  
**Fix**:
- Verify ALLOWED_CHANNELS in strategy_service.py
- Check LLM prompt for channel choices
- Add channel normalization if needed

### Error: "Email send failed: RESEND_API_KEY not set"
**Cause**: Missing Resend API key in .env  
**Fix**:
```bash
echo "RESEND_API_KEY=re_your_actual_key" >> .env
# Test: python -c "from utils.resend_client import send_email; print('OK')"
```

### Error: "Approval stored but not broadcast via WebSocket"
**Cause**: No clients connected to WebSocket or asyncio issue  
**Fix**:
1. Open http://localhost:3000/approvals first
2. Check browser console for WebSocket errors
3. Verify FastAPI CORS settings
4. Check asyncio event loop in approval_routes.py

### Error: "LTV service returns None"
**Cause**: LTV model not trained or artifact missing  
**Fix**:
```bash
python backend/create_ltv_model.py
# Check: ls -la backend/artifacts/ltv/
```

### Error: "Churn model pickle file not found"
**Cause**: XGBoost churn model not trained  
**Fix**:
```bash
python backend/create_xgboost_churn_model.py
# Should create: backend/artifacts/churn/retentionos_churn_v1.pkl
```

### Error: "InterventionGraphState missing required field X"
**Cause**: Node output doesn't match expected state shape  
**Fix**:
1. Check node return statement
2. Verify all required fields in InterventionGraphState
3. Add missing fields to node output dict

### Error: "Test mode but message goes to real customer"
**Cause**: TEST_MODE=false in production .env  
**Fix**:
```bash
# Development
export TEST_MODE=true
export TEST_RECIPIENT_EMAIL=your-test-email@example.com

# Production (carefully!)
export TEST_MODE=false
# Ensure real Twilio/Resend credentials are set
```

## Debugging Workflows

### Trace a Single Customer Through Pipeline
```python
import os
os.environ["DEBUG"] = "true"  # If implemented

from backend.services.gatekeeper.gatekeeper_pipeline import process_gatekeeper_pipeline
import pandas as pd

# Load one customer
customer = pd.read_csv("backend/data/indian_bank_profiles.csv").iloc[0].to_dict()
customer["user_id"] = 12345  # Override with known ID

# Run through gatekeeper
payloads, stats = process_gatekeeper_pipeline([customer], trigger_inngest=False, dry_run=True)

# Check output
print(f"Payloads: {len(payloads)}")
if payloads:
    p = payloads[0]
    print(f"  user_id: {p.user_id}")
    print(f"  ltv: {p.ltv}")
    print(f"  churn_prob: {p.churn_prob}")
    print(f"  uplift_score: {p.uplift_score}")
    print(f"  expected_profit: {p.expected_profit}")
```

### Trace Through Intervention Graph (Mock)
```python
from backend.models.compliance_models import InterventionPayload
from backend.services.agents.intervention_graph import initial_graph_state

payload = InterventionPayload(
    user_id=12345,
    best_discount="10%",
    expected_profit=1200.0,
    ltv=4500.0,
    churn_prob=0.68,
    uplift_score=0.12,
    segment="Salaried"
)

# Create initial state
state = initial_graph_state(payload)

# Manually test compliance node
from backend.services.agents.compliance_agent import compliance_node
try:
    new_state = compliance_node(state)
    print(f"Compliance result: {new_state.get('compliance_result')}")
except Exception as e:
    print(f"Error in compliance node: {e}")
```

### Check RAG Pipeline
```python
from backend.services.rag.compliance_service import (
    generate_queries,
    retrieve_multi_query,
    rerank_and_fuse,
    grade_chunks,
)
from backend.models.compliance_models import InterventionPayload
from backend.utils.supabase_client import get_supabase_client

payload = InterventionPayload(
    user_id=12345,
    best_discount="10%",
    expected_profit=1200.0,
    segment="Salaried"
)

supabase = get_supabase_client()

# Step 1: Generate queries
queries = generate_queries(payload)
print(f"Generated {len(queries)} queries")

# Step 2: Retrieve
raw_chunks, query_grouped = retrieve_multi_query(queries, supabase)
print(f"Retrieved {len(raw_chunks)} chunks")

# Step 3: Rerank
fused = rerank_and_fuse("Is 10% discount permitted?", raw_chunks, query_grouped, top_n=5)
print(f"Fused to {len(fused)} chunks")

# Step 4: Grade
graded = grade_chunks("Is 10% discount permitted?", fused)
print(f"Graded {len(graded)} relevant chunks")
```

### Check Message Validation
```python
from backend.models.message_models import MessageDraft
from backend.services.writer.writer_service import validate_draft

draft = MessageDraft(
    channel="Email",
    subject="Your 10% offer",
    body_plain="Get 10% off today",
    body_html="<p>Get 10% off today</p>",
    cta_text="Claim",
    cta_url="https://app.example.com"
)

try:
    validated = validate_draft(draft, "10%")
    print("✓ Draft is valid")
except ValueError as e:
    print(f"✗ Validation failed: {e}")
```

### Monitor Inngest Execution
```bash
# In Inngest Dashboard:
1. Navigate to your app
2. Click "Functions"
3. Find "process-retention-workflow"
4. Click to see recent runs
5. Click a run to see:
   - Input payload
   - LangGraph state snapshots
   - Execution time
   - Any errors
```

### Check Supabase Pending Approvals
```sql
-- View all pending approvals
SELECT id, user_id, status, created_at, payload->>'best_discount' as discount
FROM pending_approvals
ORDER BY created_at DESC
LIMIT 10;

-- View details of one approval
SELECT * FROM pending_approvals WHERE id = 'uuid-here';

-- Check compliance reasoning
SELECT 
  id,
  user_id,
  compliance_result->>'intervene' as intervened,
  compliance_result->>'reasoning' as reason
FROM pending_approvals
WHERE status = 'pending';
```

### Monitor WebSocket Connections
```python
# In websocket_routes.py, add debug logging:

async def broadcast(self, message: dict):
    print(f"[WebSocket] Broadcasting to {len(self.active_connections)} clients")
    for connection in self.active_connections:
        try:
            await connection.send_text(json.dumps(message))
            print(f"  ✓ Sent to client")
        except Exception as e:
            print(f"  ✗ Error: {e}")
```

### Test Email Delivery (Resend)
```python
from backend.utils.resend_client import send_email

result = send_email(
    to="your-test-email@example.com",
    subject="Test from RetentionOS",
    html="<h1>Hello</h1>",
    text="Hello"
)

print(f"Email sent: {result['id']}")
# Check Resend dashboard for delivery status
```

### Test WhatsApp Delivery (Twilio)
```python
from backend.utils.twilio_client import send_whatsapp

result = send_whatsapp(
    to_phone="whatsapp:+919876543210",
    body="Hello from RetentionOS!"
)

print(f"WhatsApp sent: {result['sid']}")
# Check Twilio console for delivery status
```

## Performance Tuning

### Slow Compliance Checks
- **Issue**: RAG retrieval + LLM calls taking > 10s
- **Optimization**:
  - Reduce `top_k_per_query` in retrieve_multi_query (default 3)
  - Use faster model: `gpt-4o-mini` instead of `gpt-4o`
  - Pre-compute query embeddings

### Slow Strategy Decision
- **Issue**: Database queries for subscriber + interactions slow
- **Optimization**:
  - Add indexes to `subscribers(user_id)` and `interaction_events(user_id)`
  - Cache subscriber profiles (Redis)
  - Limit interaction history to recent 30 days

### Large Pending Approvals Queue
- **Issue**: /api/approvals response slow
- **Optimization**:
  - Add pagination (offset/limit in query)
  - Add filtering (status, created_at range)
  - Archive old approvals to separate table

## Production Deployment Checklist

- [ ] **Environment**
  - [ ] All .env variables set and verified
  - [ ] PRODUCTION_MODE=true
  - [ ] TEST_MODE=false
  - [ ] Appropriate log level (INFO for prod)

- [ ] **Database**
  - [ ] All migrations (001-006) run
  - [ ] Indexes created on hot tables
  - [ ] Backup strategy configured
  - [ ] Connection pooling enabled

- [ ] **LLM Models**
  - [ ] OpenAI API key valid
  - [ ] Model quotas sufficient (gpt-4o, gpt-4o-mini)
  - [ ] Rate limiting appropriate

- [ ] **External Services**
  - [ ] Resend API key valid + domain verified
  - [ ] Twilio account configured + WhatsApp approved
  - [ ] Inngest credentials valid
  - [ ] Trigger.dev account ready

- [ ] **Backend**
  - [ ] FastAPI running on port 8000 (or configured)
  - [ ] All routers registered (inngest, approval, intervention, websocket)
  - [ ] CORS configured for frontend domain
  - [ ] SSL/TLS enabled

- [ ] **Frontend**
  - [ ] Next.js app deployed
  - [ ] /approvals page accessible
  - [ ] WebSocket connection stable
  - [ ] API endpoints reachable

- [ ] **Monitoring**
  - [ ] Error logging configured
  - [ ] Application metrics collected
  - [ ] Alerts set up for failures
  - [ ] Health check endpoint (`GET /health`)

- [ ] **Testing**
  - [ ] E2E test passed
  - [ ] Manual approval flow tested
  - [ ] Email delivery verified
  - [ ] WhatsApp delivery verified
  - [ ] Compliance HARD STOP tested

- [ ] **Documentation**
  - [ ] Runbook created
  - [ ] On-call procedure documented
  - [ ] Common errors documented
  - [ ] Disaster recovery plan ready

## Support & Escalation

### Issue: Low approval rate (< 20%)
**Check**:
1. Compliance results (too strict?)
2. Expected profit calculations (too high threshold?)
3. ML model performance (drift?)
4. Policy document adequacy

### Issue: High message rejection rate (> 30%)
**Check**:
1. Writer prompt alignment
2. Reviewer scoring thresholds
3. Sample messages with real feedback
4. A/B test different prompts

### Issue: Delivery failures (> 5%)
**Check**:
1. Resend account status + sending limits
2. Twilio account status + message limits
3. Phone number formatting
4. Subscriber opt-out status

### Escalation Path
1. Check logs: `docker logs retention-os-backend`
2. Check Inngest dashboard for workflow failures
3. Check Supabase logs for database errors
4. Check third-party dashboards (Resend, Twilio, OpenAI)
5. Create incident ticket with: payload, stack trace, reproduction steps

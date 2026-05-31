-- 006_pending_approvals.sql

CREATE TABLE IF NOT EXISTS pending_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending | approved | dismissed
    payload JSONB NOT NULL,                 -- original InterventionPayload
    compliance_result JSONB,                -- ComplianceResult
    strategy_result JSONB,                  -- StrategyResult  
    message_draft JSONB,                    -- MessageDraft (admin may edit)
    review_result JSONB,                    -- ReviewResult
    graph_state JSONB,                      -- full InterventionGraphState snapshot
    reasoning_text TEXT,
    reasoning_bullets TEXT[],
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON pending_approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_created ON pending_approvals(created_at DESC);

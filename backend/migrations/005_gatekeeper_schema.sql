-- 005_gatekeeper_schema.sql

-- Add new columns to subscribers table for the Gatekeeper logic
ALTER TABLE subscribers
ADD COLUMN IF NOT EXISTS segment VARCHAR(50),
ADD COLUMN IF NOT EXISTS job_change INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS relocation INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS competitor_pricing_gap DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS upi_frequency_drop DECIMAL(5, 2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS network_influence_score DECIMAL(5, 4) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS is_hub_customer BOOLEAN DEFAULT FALSE;

-- Create an LTV tracking table
CREATE TABLE IF NOT EXISTS ltv_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    historical_ltv DECIMAL(10, 2) DEFAULT 0.0,
    predictive_ltv DECIMAL(10, 2) DEFAULT 0.0,
    cfvs_score INTEGER DEFAULT 0,
    is_eligible_for_retention BOOLEAN DEFAULT TRUE,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Index for LTV queries
CREATE INDEX IF NOT EXISTS idx_ltv_subscriber ON ltv_metrics(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_ltv_eligibility ON ltv_metrics(is_eligible_for_retention);

-- Create a table for Network relationships (transactions/edges for PageRank)
CREATE TABLE IF NOT EXISTS subscriber_network_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    target_subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    weight DECIMAL(5, 2) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_network_source ON subscriber_network_edges(source_subscriber_id);

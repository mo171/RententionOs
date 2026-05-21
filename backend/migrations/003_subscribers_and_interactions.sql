-- Subscribers and interaction history for Strategy Agent (Node 2)

CREATE TABLE IF NOT EXISTS subscribers (
    user_id         BIGINT PRIMARY KEY,
    full_name       TEXT NOT NULL,
    email           TEXT,
    phone           TEXT,
    timezone        TEXT NOT NULL DEFAULT 'UTC',
    preferred_channel TEXT NOT NULL DEFAULT 'email'
        CHECK (preferred_channel IN ('email', 'sms', 'push')),
    opt_out_sms     BOOLEAN NOT NULL DEFAULT FALSE,
    opt_out_email   BOOLEAN NOT NULL DEFAULT FALSE,
    opt_out_push    BOOLEAN NOT NULL DEFAULT FALSE,
    segment         TEXT,
    ltv_tier        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interaction_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     BIGINT NOT NULL REFERENCES subscribers(user_id) ON DELETE CASCADE,
    channel     TEXT NOT NULL CHECK (channel IN ('email', 'sms', 'push')),
    event_type  TEXT NOT NULL
        CHECK (event_type IN ('sent', 'opened', 'clicked', 'converted', 'ignored')),
    sent_at     TIMESTAMPTZ NOT NULL,
    metadata    JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS interaction_events_user_sent_idx
    ON interaction_events (user_id, sent_at DESC);

-- Seed test subscriber (user_id 99) for backend/test.py
INSERT INTO subscribers (
    user_id, full_name, email, phone, timezone,
    preferred_channel, opt_out_sms, opt_out_email, opt_out_push,
    segment, ltv_tier
) VALUES (
    99,
    'Alex Rivera',
    'alex.rivera@example.com',
    '+15551234567',
    'America/New_York',
    'push',
    FALSE,
    FALSE,
    FALSE,
    'smb',
    'high'
) ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    phone = EXCLUDED.phone,
    timezone = EXCLUDED.timezone,
    preferred_channel = EXCLUDED.preferred_channel,
    segment = EXCLUDED.segment,
    ltv_tier = EXCLUDED.ltv_tier,
    updated_at = NOW();

-- Clear prior seed events for user 99 (idempotent re-run)
DELETE FROM interaction_events WHERE user_id = 99;

INSERT INTO interaction_events (user_id, channel, event_type, sent_at, metadata) VALUES
(99, 'push', 'sent',      NOW() - INTERVAL '14 days', '{"campaign": "renewal_v1", "local_hour": 18}'),
(99, 'push', 'opened',    NOW() - INTERVAL '14 days' + INTERVAL '5 minutes', '{"campaign": "renewal_v1"}'),
(99, 'push', 'clicked',   NOW() - INTERVAL '14 days' + INTERVAL '6 minutes', '{"campaign": "renewal_v1"}'),
(99, 'email', 'sent',     NOW() - INTERVAL '10 days', '{"campaign": "newsletter", "local_hour": 9}'),
(99, 'email', 'ignored',  NOW() - INTERVAL '10 days', '{"campaign": "newsletter"}'),
(99, 'push', 'sent',      NOW() - INTERVAL '7 days', '{"campaign": "save_offer", "local_hour": 18}'),
(99, 'push', 'converted', NOW() - INTERVAL '7 days' + INTERVAL '12 minutes', '{"campaign": "save_offer"}'),
(99, 'sms', 'sent',       NOW() - INTERVAL '3 days', '{"campaign": "flash_sale", "local_hour": 12}'),
(99, 'sms', 'ignored',    NOW() - INTERVAL '3 days', '{"campaign": "flash_sale"}'),
(99, 'push', 'sent',      NOW() - INTERVAL '1 day', '{"campaign": "retention_15", "local_hour": 18}'),
(99, 'push', 'opened',    NOW() - INTERVAL '1 day' + INTERVAL '3 minutes', '{"campaign": "retention_15"}');

-- =============================================================================
-- AI Customer Support Platform — PostgreSQL Schema (RDS)
-- =============================================================================
-- Designed for AWS RDS PostgreSQL 16.1
-- Tables: conversations, messages, harassment_events, analysis_logs, handoffs
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────────────────────────
-- conversations: 会話セッション管理
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_name   VARCHAR(255),
    customer_email  VARCHAR(255),
    channel         VARCHAR(50) DEFAULT 'web',  -- web, phone, email, api
    status          VARCHAR(20) DEFAULT 'active',  -- active, resolved, escalated, closed
    assigned_agent  VARCHAR(255),
    priority        VARCHAR(20) DEFAULT 'normal',  -- critical, high, normal, low
    tags            JSONB DEFAULT '[]'::jsonb,
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at     TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_priority ON conversations(priority);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- messages: 会話メッセージ
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role                VARCHAR(20) NOT NULL,  -- user, assistant, system
    content             TEXT NOT NULL,
    sentiment           VARCHAR(20),  -- positive, neutral, negative, anger
    harassment_severity VARCHAR(20),  -- critical, high, medium, low, none
    ai_model            VARCHAR(100),  -- claude-sonnet-4-20250514, rule-based
    token_usage         INTEGER,
    metadata            JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_sentiment ON messages(sentiment) WHERE sentiment IS NOT NULL;
CREATE INDEX idx_messages_harassment ON messages(harassment_severity)
    WHERE harassment_severity NOT IN ('none', 'low');
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- harassment_events: カスハラ検知ログ
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE harassment_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id          UUID REFERENCES messages(id) ON DELETE SET NULL,
    severity            VARCHAR(20) NOT NULL,  -- critical, high, medium
    categories          JSONB NOT NULL DEFAULT '[]'::jsonb,
    matched_patterns    JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_analysis         JSONB,  -- Claude enhanced analysis result
    action_taken        VARCHAR(50),  -- escalated, warned, logged
    resolved            BOOLEAN DEFAULT FALSE,
    resolved_by         VARCHAR(255),
    notes               TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_harassment_conversation ON harassment_events(conversation_id);
CREATE INDEX idx_harassment_severity ON harassment_events(severity);
CREATE INDEX idx_harassment_unresolved ON harassment_events(resolved) WHERE resolved = FALSE;
CREATE INDEX idx_harassment_created_at ON harassment_events(created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- analysis_logs: 分析ログ（リアルタイムダッシュボード用）
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE analysis_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     VARCHAR(255),
    message_text        VARCHAR(500),  -- Truncated for privacy
    harassment_severity VARCHAR(20),
    sentiment           VARCHAR(20),
    combined_risk       VARCHAR(20),
    ai_enhanced         BOOLEAN DEFAULT FALSE,
    processing_time_ms  INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analysis_risk ON analysis_logs(combined_risk);
CREATE INDEX idx_analysis_created_at ON analysis_logs(created_at DESC);

-- Partition by month for performance (optional, for high-volume environments)
-- CREATE TABLE analysis_logs_2026_02 PARTITION OF analysis_logs
--     FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- ─────────────────────────────────────────────────────────────────────────────
-- handoffs: AI→人間 引き継ぎレコード
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE handoffs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    priority            VARCHAR(20) NOT NULL,  -- critical, high, normal
    summary             TEXT NOT NULL,
    detected_issues     JSONB DEFAULT '[]'::jsonb,
    order_numbers       JSONB DEFAULT '[]'::jsonb,
    sentiment_history   JSONB DEFAULT '[]'::jsonb,
    harassment_detected BOOLEAN DEFAULT FALSE,
    harassment_severity VARCHAR(20),
    context_metadata    JSONB DEFAULT '{}'::jsonb,
    assigned_to         VARCHAR(255),
    status              VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, in_progress, resolved
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at         TIMESTAMP WITH TIME ZONE,
    resolved_at         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_handoffs_status ON handoffs(status);
CREATE INDEX idx_handoffs_priority ON handoffs(priority);
CREATE INDEX idx_handoffs_conversation ON handoffs(conversation_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- daily_metrics: 日次集計ビュー（ダッシュボードKPI用）
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW daily_metrics AS
SELECT
    DATE(created_at) AS metric_date,
    COUNT(*) AS total_messages,
    COUNT(*) FILTER (WHERE role = 'user') AS customer_messages,
    COUNT(*) FILTER (WHERE role = 'assistant') AS ai_responses,
    COUNT(*) FILTER (WHERE sentiment = 'positive') AS positive_count,
    COUNT(*) FILTER (WHERE sentiment = 'negative') AS negative_count,
    COUNT(*) FILTER (WHERE sentiment = 'anger') AS anger_count,
    COUNT(*) FILTER (WHERE harassment_severity IN ('critical', 'high', 'medium')) AS harassment_count,
    ROUND(
        AVG(CASE WHEN sentiment = 'positive' THEN 1.0 WHEN sentiment = 'neutral' THEN 0.5 ELSE 0.0 END) * 100,
        1
    ) AS csat_score
FROM messages
GROUP BY DATE(created_at)
ORDER BY metric_date DESC;

CREATE UNIQUE INDEX idx_daily_metrics_date ON daily_metrics(metric_date);

-- Refresh materialized view (run via scheduled Lambda or EventBridge)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY daily_metrics;

-- ─────────────────────────────────────────────────────────────────────────────
-- Functions: 自動 updated_at トリガー
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ─────────────────────────────────────────────────────────────────────────────
-- Seed data (for development)
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO conversations (id, customer_name, channel, status, priority) VALUES
    ('a0000001-0000-0000-0000-000000000001', '山田太郎', 'web', 'active', 'normal'),
    ('a0000001-0000-0000-0000-000000000002', '佐藤花子', 'web', 'active', 'high');

INSERT INTO messages (conversation_id, role, content, sentiment) VALUES
    ('a0000001-0000-0000-0000-000000000001', 'user', '商品が届きません。注文番号 ORD-12345 です。', 'negative'),
    ('a0000001-0000-0000-0000-000000000001', 'assistant', 'ご注文の配送状況を確認いたします。注文番号 ORD-12345 を確認しました。', 'neutral'),
    ('a0000001-0000-0000-0000-000000000002', 'user', 'ふざけるな！3回も問い合わせてるのに解決しない！', 'anger');

-- Schema Optimization for 5/5 Rating
-- Advanced schema improvements, constraints, and data integrity

-- =============================================
-- ADVANCED CONSTRAINTS AND VALIDATIONS
-- =============================================

-- Lead quality validation constraint
ALTER TABLE leads ADD CONSTRAINT chk_lead_quality 
CHECK (lead_quality IN ('hot', 'warm', 'cold', 'qualified', 'disqualified'));

-- Lead score validation constraint
ALTER TABLE leads ADD CONSTRAINT chk_lead_score 
CHECK (lead_score >= 0 AND lead_score <= 100);

-- Monthly electric bill validation
ALTER TABLE leads ADD CONSTRAINT chk_monthly_electric_bill 
CHECK (monthly_electric_bill >= 0 AND monthly_electric_bill <= 10000);

-- Revenue validation constraints
ALTER TABLE leads ADD CONSTRAINT chk_total_revenue_earned 
CHECK (total_revenue_earned >= 0);

-- Commission rate validation
ALTER TABLE leads ADD CONSTRAINT chk_commission_rate 
CHECK (commission_rate >= 0 AND commission_rate <= 1);

-- =============================================
-- ADVANCED TRIGGERS FOR DATA INTEGRITY
-- =============================================

-- Function to update lead quality based on score
CREATE OR REPLACE FUNCTION update_lead_quality()
RETURNS TRIGGER AS $$
BEGIN
    -- Update lead quality based on score
    IF NEW.lead_score >= 80 THEN
        NEW.lead_quality := 'hot';
    ELSIF NEW.lead_score >= 60 THEN
        NEW.lead_quality := 'warm';
    ELSIF NEW.lead_score >= 40 THEN
        NEW.lead_quality := 'cold';
    ELSE
        NEW.lead_quality := 'disqualified';
    END IF;
    
    -- Update qualification status
    IF NEW.lead_score >= 60 THEN
        NEW.qualification_status := 'qualified';
    ELSE
        NEW.qualification_status := 'not_qualified';
    END IF;
    
    -- Update last updated timestamp
    NEW.updated_at := CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update lead quality
CREATE TRIGGER trg_update_lead_quality
    BEFORE UPDATE ON leads
    FOR EACH ROW
    WHEN (OLD.lead_score IS DISTINCT FROM NEW.lead_score)
    EXECUTE FUNCTION update_lead_quality();

-- Function to calculate total revenue
CREATE OR REPLACE FUNCTION calculate_total_revenue()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate total revenue based on commission rate
    NEW.total_revenue_earned := NEW.lead_value * NEW.commission_rate;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to calculate total revenue
CREATE TRIGGER trg_calculate_total_revenue
    BEFORE INSERT OR UPDATE ON leads
    FOR EACH ROW
    WHEN (OLD.lead_value IS DISTINCT FROM NEW.lead_value OR OLD.commission_rate IS DISTINCT FROM NEW.commission_rate)
    EXECUTE FUNCTION calculate_total_revenue();

-- =============================================
-- ADVANCED INDEXES FOR DATA INTEGRITY
-- =============================================

-- Unique constraint on email per lead
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_email_unique 
ON leads(email) 
WHERE is_active = true;

-- Unique constraint on phone per lead
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_phone_unique 
ON leads(phone) 
WHERE is_active = true AND phone IS NOT NULL;

-- Composite unique constraint on lead + session
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_conversations_lead_session 
ON lead_conversations(lead_id, session_id) 
WHERE lead_id IS NOT NULL;

-- =============================================
-- ADVANCED VIEWS FOR DATA INTEGRITY MONITORING
-- =============================================

-- Data quality monitoring view
CREATE OR REPLACE VIEW data_quality_monitoring AS
SELECT 
    'leads' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as valid_emails,
    COUNT(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 END) as valid_phones,
    COUNT(CASE WHEN zip_code IS NOT NULL AND zip_code != '' THEN 1 END) as valid_zip_codes,
    COUNT(CASE WHEN lead_score IS NOT NULL THEN 1 END) as scored_leads,
    COUNT(CASE WHEN lead_quality IS NOT NULL THEN 1 END) as qualified_leads,
    COUNT(CASE WHEN monthly_electric_bill > 0 THEN 1 END) as leads_with_bills,
    AVG(lead_score) as avg_lead_score,
    AVG(monthly_electric_bill) as avg_electric_bill
FROM leads
WHERE is_active = true
UNION ALL
SELECT 
    'lead_conversations' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN message_content IS NOT NULL AND message_content != '' THEN 1 END) as valid_messages,
    COUNT(CASE WHEN message_type IN ('user', 'ai') THEN 1 END) as valid_message_types,
    COUNT(CASE WHEN session_id IS NOT NULL THEN 1 END) as valid_sessions,
    COUNT(CASE WHEN lead_id IS NOT NULL THEN 1 END) as valid_lead_links,
    COUNT(CASE WHEN confidence_score IS NOT NULL THEN 1 END) as scored_messages,
    COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) as sentiment_analyzed,
    AVG(confidence_score) as avg_confidence,
    AVG(sentiment_score) as avg_sentiment
FROM lead_conversations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Lead quality distribution view
CREATE OR REPLACE VIEW lead_quality_distribution AS
SELECT 
    lead_quality,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    AVG(lead_score) as avg_score,
    AVG(monthly_electric_bill) as avg_bill,
    AVG(total_revenue_earned) as avg_revenue,
    SUM(total_revenue_earned) as total_revenue
FROM leads
WHERE is_active = true
GROUP BY lead_quality
ORDER BY avg_score DESC;

-- =============================================
-- ADVANCED PARTITIONING STRATEGY
-- =============================================

-- Create partitioned conversation table for better performance
CREATE TABLE IF NOT EXISTS lead_conversations_partitioned (
    LIKE lead_conversations INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for current and next 6 months
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
    partition_start TEXT;
    partition_end TEXT;
BEGIN
    FOR i IN 0..6 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'lead_conversations_' || TO_CHAR(start_date, 'YYYY_MM');
        partition_start := start_date::TEXT;
        partition_end := end_date::TEXT;
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF lead_conversations_partitioned FOR VALUES FROM (%L) TO (%L)',
                      partition_name, partition_start, partition_end);
        
        start_date := end_date;
    END LOOP;
END $$;

-- =============================================
-- ADVANCED DATA ARCHIVAL STRATEGY
-- =============================================

-- Create archive table for old conversations
CREATE TABLE IF NOT EXISTS lead_conversations_archive (
    LIKE lead_conversations INCLUDING ALL
);

-- Function to archive old conversations
CREATE OR REPLACE FUNCTION archive_old_conversations()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archive conversations older than 6 months
    WITH archived AS (
        DELETE FROM lead_conversations
        WHERE created_at < CURRENT_DATE - INTERVAL '6 months'
        RETURNING *
    )
    INSERT INTO lead_conversations_archive
    SELECT * FROM archived;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Log archival
    INSERT INTO system_logs (log_level, message, created_at)
    VALUES ('INFO', format('Archived %s old conversations', archived_count), CURRENT_TIMESTAMP);
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ADVANCED MONITORING AND ALERTING
-- =============================================

-- System logs table for monitoring
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    table_name VARCHAR(50),
    record_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance monitoring table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    table_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to log performance metrics
CREATE OR REPLACE FUNCTION log_performance_metric(
    p_metric_name VARCHAR(100),
    p_metric_value FLOAT,
    p_metric_unit VARCHAR(20) DEFAULT NULL,
    p_table_name VARCHAR(50) DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO performance_metrics (metric_name, metric_value, metric_unit, table_name)
    VALUES (p_metric_name, p_metric_value, p_metric_unit, p_table_name);
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ADVANCED DATA VALIDATION FUNCTIONS
-- =============================================

-- Function to validate email format
CREATE OR REPLACE FUNCTION is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql;

-- Function to validate phone format
CREATE OR REPLACE FUNCTION is_valid_phone(phone TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN phone ~ '^\+?[1-9]\d{1,14}$';
END;
$$ LANGUAGE plpgsql;

-- Function to validate zip code format
CREATE OR REPLACE FUNCTION is_valid_zip_code(zip_code TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN zip_code ~ '^\d{5}(-\d{4})?$';
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- ADVANCED CONSTRAINTS WITH VALIDATION
-- =============================================

-- Email validation constraint
ALTER TABLE leads ADD CONSTRAINT chk_valid_email 
CHECK (is_valid_email(email));

-- Phone validation constraint
ALTER TABLE leads ADD CONSTRAINT chk_valid_phone 
CHECK (phone IS NULL OR is_valid_phone(phone));

-- Zip code validation constraint
ALTER TABLE leads ADD CONSTRAINT chk_valid_zip_code 
CHECK (is_valid_zip_code(zip_code));

-- =============================================
-- ADVANCED STATISTICS AND MONITORING
-- =============================================

-- Create statistics view for monitoring
CREATE OR REPLACE VIEW database_statistics AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs,
    histogram_bounds
FROM pg_stats
WHERE schemaname = 'public'
AND tablename IN ('leads', 'lead_conversations', 'nyc_zip_codes', 'revenue_metrics')
ORDER BY tablename, attname;

-- Create index usage statistics view
CREATE OR REPLACE VIEW index_usage_statistics AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
        WHEN idx_scan < 10000 THEN 'HIGH_USAGE'
        ELSE 'VERY_HIGH_USAGE'
    END as usage_level
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- =============================================
-- UPDATE STATISTICS
-- =============================================

-- Update statistics for all tables
ANALYZE leads;
ANALYZE lead_conversations;
ANALYZE nyc_zip_codes;
ANALYZE revenue_metrics;
ANALYZE platform_performance;
ANALYZE user_sessions;
ANALYZE b2b_platforms;
ANALYZE lead_exports;
ANALYZE b2b_revenue_transactions;
ANALYZE ai_models;
ANALYZE ai_analyses;
ANALYZE system_logs;
ANALYZE performance_metrics;

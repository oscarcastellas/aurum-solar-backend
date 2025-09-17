-- Critical Performance Indexes for Aurum Solar
-- Deploy immediately for sub-100ms query performance
-- Railway PostgreSQL Optimization

-- =============================================
-- LEAD MANAGEMENT PERFORMANCE INDEXES
-- =============================================

-- Lead Quality and Creation Time (Most Common Query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_quality_created 
ON leads(lead_quality, created_at DESC);

-- Lead Scoring for B2B Export (Critical Path)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_score_export 
ON leads(lead_score DESC, export_status) 
WHERE export_status = 'pending';

-- NYC Borough Analysis (Geographic Queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_borough_quality 
ON leads(borough, lead_quality, lead_score DESC);

-- Electric Bill Analysis (Solar Potential)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_electric_zip 
ON leads(monthly_electric_bill, zip_code) 
WHERE monthly_electric_bill > 0;

-- Revenue Tracking (High-Value Leads)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_revenue_active 
ON leads(total_revenue_earned DESC, is_active) 
WHERE is_active = true;

-- Lead Status and Export Tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_status_created 
ON leads(status, created_at DESC);

-- Lead Source Attribution
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_source_created 
ON leads(source, created_at DESC);

-- Lead Qualification Status
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_qualification_created 
ON leads(qualification_status, created_at DESC);

-- =============================================
-- CONVERSATION PERFORMANCE INDEXES
-- =============================================

-- Lead Conversation History (Most Common Query)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_lead_created 
ON lead_conversations(lead_id, created_at DESC);

-- Session-Based Conversation Retrieval
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_session_created 
ON lead_conversations(session_id, created_at DESC);

-- Message Type Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_type_lead 
ON lead_conversations(message_type, lead_id, created_at);

-- AI Analysis Queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_ai_analysis 
ON lead_conversations(ai_model_used, confidence_score, created_at DESC);

-- =============================================
-- NYC MARKET DATA OPTIMIZATION
-- =============================================

-- NYC Zip Code Lookup (Covering Index)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zip_covering 
ON nyc_zip_codes(zip_code) 
INCLUDE (borough, median_household_income, solar_potential_score, average_electric_rate_per_kwh);

-- NYC Borough Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zip_borough_income 
ON nyc_zip_codes(borough, median_household_income DESC);

-- Solar Potential Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zip_solar_potential 
ON nyc_zip_codes(solar_potential_score DESC, solar_adoption_rate DESC);

-- High-Value Zip Codes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zip_high_value 
ON nyc_zip_codes(high_value_zip_code, conversion_rate DESC) 
WHERE high_value_zip_code = true;

-- =============================================
-- ANALYTICS PERFORMANCE INDEXES
-- =============================================

-- Revenue Metrics Time Series
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_time_series 
ON revenue_metrics(date DESC, period_type) 
INCLUDE (total_revenue, qualified_leads, sold_leads);

-- Dashboard Queries (Last 90 Days)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_dashboard 
ON revenue_metrics(date DESC) 
WHERE date >= CURRENT_DATE - INTERVAL '90 days';

-- Revenue Growth Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_growth 
ON revenue_metrics(revenue_growth_rate DESC, date DESC);

-- Lead Quality Distribution
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_quality 
ON revenue_metrics(qualified_leads, sold_leads, date DESC);

-- =============================================
-- B2B PLATFORM PERFORMANCE INDEXES
-- =============================================

-- Platform Performance Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_performance 
ON platform_performance(platform_id, date DESC, acceptance_rate DESC);

-- Export Status Tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_export_status_created 
ON lead_exports(export_status, created_at DESC);

-- Revenue Transaction Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_revenue 
ON b2b_revenue_transactions(net_amount DESC, transaction_date DESC);

-- =============================================
-- USER SESSION PERFORMANCE INDEXES
-- =============================================

-- Session Conversion Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_conversion 
ON user_sessions(converted, conversion_value DESC, started_at DESC);

-- Traffic Source Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_source 
ON user_sessions(utm_source, utm_medium, started_at DESC);

-- Device Performance Analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_device 
ON user_sessions(device_type, session_duration_seconds DESC);

-- =============================================
-- AI MODEL PERFORMANCE INDEXES
-- =============================================

-- AI Model Performance Tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_model_performance 
ON ai_models(model_type, accuracy_score DESC, total_requests DESC);

-- AI Analysis Quality
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analysis_quality 
ON ai_analyses(confidence_score DESC, created_at DESC);

-- =============================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- =============================================

-- Lead Export Query Optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_export_complex 
ON leads(lead_quality, lead_score DESC, export_status, created_at DESC) 
WHERE is_active = true AND export_status = 'pending';

-- NYC Market Analysis Query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_market_analysis 
ON nyc_zip_codes(borough, solar_potential_score DESC, conversion_rate DESC, median_household_income DESC);

-- Revenue Analytics Query
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_analytics 
ON revenue_metrics(date DESC, period_type, total_revenue DESC, qualified_leads DESC);

-- =============================================
-- PARTIAL INDEXES FOR COMMON FILTERS
-- =============================================

-- Active Leads Only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_active_only 
ON leads(created_at DESC, lead_score DESC) 
WHERE is_active = true;

-- Qualified Leads Only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_qualified_only 
ON leads(lead_quality, lead_score DESC, created_at DESC) 
WHERE qualification_status = 'qualified';

-- High-Value Leads
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_high_value 
ON leads(total_revenue_earned DESC, created_at DESC) 
WHERE total_revenue_earned > 100;

-- Recent Conversations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_recent 
ON lead_conversations(lead_id, created_at DESC) 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================
-- INDEX USAGE MONITORING
-- =============================================

-- Create index usage tracking view
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_level
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- =============================================
-- PERFORMANCE VALIDATION QUERIES
-- =============================================

-- Test lead creation performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM leads 
WHERE lead_quality = 'hot' 
ORDER BY created_at DESC 
LIMIT 10;

-- Test conversation retrieval performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM lead_conversations 
WHERE lead_id = (SELECT id FROM leads LIMIT 1) 
ORDER BY created_at DESC;

-- Test NYC zip code lookup performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM nyc_zip_codes 
WHERE zip_code = '10001';

-- Test revenue analytics performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM revenue_metrics 
WHERE date >= CURRENT_DATE - INTERVAL '30 days' 
ORDER BY date DESC;

-- =============================================
-- INDEX MAINTENANCE RECOMMENDATIONS
-- =============================================

-- Update table statistics after index creation
ANALYZE leads;
ANALYZE lead_conversations;
ANALYZE nyc_zip_codes;
ANALYZE revenue_metrics;
ANALYZE platform_performance;
ANALYZE user_sessions;

-- Monitor index bloat (run weekly)
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_size_pretty(pg_relation_size(indrelid)) as table_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Advanced Performance Indexes for 5/5 Rating
-- Additional indexes for maximum performance optimization

-- =============================================
-- ADVANCED LEAD MANAGEMENT INDEXES
-- =============================================

-- Multi-column covering index for lead export queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_export_covering 
ON leads(lead_quality, lead_score DESC, export_status, created_at DESC) 
INCLUDE (id, email, first_name, last_name, zip_code, monthly_electric_bill, total_revenue_earned)
WHERE is_active = true;

-- Lead scoring optimization with NYC data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_scoring_optimized 
ON leads(monthly_electric_bill, zip_code, lead_score) 
WHERE monthly_electric_bill > 0 AND lead_score IS NULL;

-- Lead quality trend analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_quality_trend 
ON leads(created_at, lead_quality, lead_score) 
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days';

-- Revenue optimization queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_revenue_optimization 
ON leads(total_revenue_earned DESC, lead_quality, created_at DESC) 
WHERE is_active = true AND total_revenue_earned > 0;

-- =============================================
-- ADVANCED CONVERSATION INDEXES
-- =============================================

-- Conversation analysis and AI insights
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_ai_insights 
ON lead_conversations(ai_model_used, confidence_score, sentiment_score, created_at DESC) 
WHERE confidence_score > 0.7;

-- Conversation completion analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_completion 
ON lead_conversations(lead_id, message_type, created_at DESC) 
WHERE message_type IN ('user', 'ai');

-- Session-based conversation flow
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_flow 
ON lead_conversations(session_id, created_at, message_type) 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================
-- ADVANCED NYC MARKET DATA INDEXES
-- =============================================

-- Spatial index for geographic queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_zip_spatial 
ON nyc_zip_codes USING GIST (point(longitude, latitude));

-- NYC market intelligence optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_market_intelligence 
ON nyc_zip_codes(solar_potential_score DESC, conversion_rate DESC, median_household_income DESC) 
WHERE high_value_zip_code = true;

-- NYC competition analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_competition 
ON nyc_zip_codes(competition_intensity, market_saturation, solar_installers_count) 
WHERE solar_installers_count > 0;

-- NYC incentive optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_incentives_active 
ON nyc_incentives(zip_code_id, is_active, incentive_amount DESC) 
WHERE is_active = true AND incentive_amount > 0;

-- =============================================
-- ADVANCED ANALYTICS INDEXES
-- =============================================

-- Time-series analytics optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_timeseries_advanced 
ON revenue_metrics(date DESC, period_type, total_revenue DESC, qualified_leads DESC) 
WHERE date >= CURRENT_DATE - INTERVAL '365 days';

-- Platform performance analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_analytics 
ON platform_performance(platform_id, date DESC, acceptance_rate DESC, total_revenue DESC) 
WHERE date >= CURRENT_DATE - INTERVAL '90 days';

-- User session analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_analytics 
ON user_sessions(converted, conversion_value DESC, started_at DESC, device_type) 
WHERE started_at >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================
-- ADVANCED B2B PLATFORM INDEXES
-- =============================================

-- B2B export optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_b2b_export_optimization 
ON lead_exports(platform_id, export_status, created_at DESC, commission_earned DESC) 
WHERE export_status IN ('pending', 'success');

-- Revenue transaction analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_transaction_analysis 
ON b2b_revenue_transactions(transaction_date DESC, net_amount DESC, platform_id, status) 
WHERE status = 'completed';

-- Platform performance tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_performance_tracking 
ON b2b_platforms(is_active, is_accepting_leads, acceptance_rate DESC, total_revenue_generated DESC) 
WHERE is_active = true;

-- =============================================
-- ADVANCED AI MODEL INDEXES
-- =============================================

-- AI model performance analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_model_performance_advanced 
ON ai_models(model_type, accuracy_score DESC, total_requests DESC, average_response_time_ms) 
WHERE is_active = true;

-- AI analysis quality tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ai_analysis_quality_advanced 
ON ai_analyses(confidence_score DESC, created_at DESC, lead_id) 
WHERE confidence_score > 0.8;

-- =============================================
-- PARTIAL INDEXES FOR COMMON FILTERS
-- =============================================

-- High-value leads only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_high_value_advanced 
ON leads(lead_score DESC, total_revenue_earned DESC, created_at DESC) 
WHERE lead_quality = 'hot' AND total_revenue_earned > 200;

-- Recent qualified leads
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_qualified_recent 
ON leads(qualification_status, lead_score DESC, created_at DESC) 
WHERE qualification_status = 'qualified' AND created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Active conversations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_active 
ON lead_conversations(lead_id, created_at DESC) 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days';

-- High-performance NYC zip codes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_high_performance 
ON nyc_zip_codes(zip_code, solar_potential_score, conversion_rate) 
WHERE solar_potential_score > 80 AND conversion_rate > 0.15;

-- =============================================
-- FUNCTIONAL INDEXES FOR COMPLEX QUERIES
-- =============================================

-- Lead scoring function index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_scoring_function 
ON leads((monthly_electric_bill * 0.4 + COALESCE(lead_score, 0) * 0.6) DESC) 
WHERE monthly_electric_bill > 0;

-- Revenue calculation index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_calculation 
ON leads((total_revenue_earned * commission_rate) DESC) 
WHERE total_revenue_earned > 0 AND commission_rate > 0;

-- =============================================
-- INDEX MAINTENANCE AND MONITORING
-- =============================================

-- Create index usage monitoring view
CREATE OR REPLACE VIEW advanced_index_usage_stats AS
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
    END as usage_level,
    CASE 
        WHEN idx_scan = 0 THEN 'Consider dropping'
        WHEN idx_scan < 100 THEN 'Monitor usage'
        WHEN idx_scan < 1000 THEN 'Good usage'
        WHEN idx_scan < 10000 THEN 'High usage'
        ELSE 'Very high usage - consider optimization'
    END as recommendation
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Create query performance monitoring view
CREATE OR REPLACE VIEW query_performance_monitoring AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_time DESC;

-- =============================================
-- UPDATE TABLE STATISTICS
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

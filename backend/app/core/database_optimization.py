"""
Database optimization and performance configuration
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.dialects.postgresql import UUID
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization utilities and configurations"""
    
    @staticmethod
    def create_optimized_engine(database_url: str, **kwargs):
        """Create an optimized database engine with performance settings"""
        
        # Default optimization settings
        engine_kwargs = {
            'poolclass': QueuePool,
            'pool_size': 20,  # Number of connections to maintain
            'max_overflow': 30,  # Additional connections beyond pool_size
            'pool_pre_ping': True,  # Validate connections before use
            'pool_recycle': 3600,  # Recycle connections after 1 hour
            'pool_timeout': 30,  # Timeout for getting connection from pool
            'echo': False,  # Set to True for SQL query logging
            'echo_pool': False,  # Set to True for connection pool logging
            **kwargs
        }
        
        engine = create_engine(database_url, **engine_kwargs)
        
        # Add event listeners for optimization
        DatabaseOptimizer._add_optimization_listeners(engine)
        
        return engine
    
    @staticmethod
    def _add_optimization_listeners(engine: Engine):
        """Add event listeners for database optimization"""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set PostgreSQL-specific optimizations"""
            if 'postgresql' in str(engine.url):
                with dbapi_connection.cursor() as cursor:
                    # Enable query optimization
                    cursor.execute("SET random_page_cost = 1.1")
                    cursor.execute("SET effective_cache_size = '4GB'")
                    cursor.execute("SET work_mem = '256MB'")
                    cursor.execute("SET maintenance_work_mem = '1GB'")
                    cursor.execute("SET shared_buffers = '1GB'")
                    cursor.execute("SET checkpoint_completion_target = 0.9")
                    cursor.execute("SET wal_buffers = '16MB'")
                    cursor.execute("SET default_statistics_target = 100")
                    
                    # Enable parallel queries
                    cursor.execute("SET max_parallel_workers_per_gather = 4")
                    cursor.execute("SET max_parallel_workers = 8")
                    cursor.execute("SET max_parallel_maintenance_workers = 4")
                    
                    # Enable JIT compilation for complex queries
                    cursor.execute("SET jit = on")
                    cursor.execute("SET jit_above_cost = 100000")
                    cursor.execute("SET jit_optimize_above_cost = 500000")
                    
                    # Enable query plan caching
                    cursor.execute("SET plan_cache_mode = force_custom_plan")
                    
                    logger.info("PostgreSQL optimization settings applied")
    
    @staticmethod
    def get_performance_indexes():
        """Get list of performance-critical indexes to create"""
        return [
            # Lead performance indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_created_status ON leads (created_at, status) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_quality_score ON leads (lead_quality, lead_score) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_zip_quality ON leads (zip_code, lead_quality) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_revenue ON leads (total_revenue_earned, created_at) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_export_status ON leads (export_status, created_at) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_borough_type ON leads (borough, property_type) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_electric_bill ON leads (monthly_electric_bill, zip_code) WHERE is_active = true",
            
            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_qualified_exported ON leads (status, export_status, created_at) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_quality_borough ON leads (lead_quality, borough, created_at) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_source_quality ON leads (source, lead_quality, created_at) WHERE is_active = true",
            
            # Revenue analytics indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_date_period ON revenue_metrics (date, period_type)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_year_month ON revenue_metrics (year, month)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_qualified_sold ON revenue_metrics (qualified_leads, sold_leads)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_revenue_total_growth ON revenue_metrics (total_revenue, revenue_growth_rate)",
            
            # Platform performance indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_date_period ON platform_performance (platform_id, date, period_type)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_acceptance_revenue ON platform_performance (acceptance_rate, total_revenue)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_quality_score ON platform_performance (average_lead_score, average_lead_quality)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_platform_error_uptime ON platform_performance (error_rate, uptime_percentage)",
            
            # NYC market intelligence indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_zip_date ON nyc_market_intelligence (zip_code, date)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_borough_date ON nyc_market_intelligence (borough, date)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_adoption_revenue ON nyc_market_intelligence (solar_adoption_rate, total_revenue)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nyc_competition_growth ON nyc_market_intelligence (market_competition_score, growth_rate)",
            
            # User session indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_lead_converted ON user_sessions (lead_id, converted) WHERE lead_id IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_source_medium ON user_sessions (utm_source, utm_medium)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_device_duration ON user_sessions (device_type, session_duration_seconds)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_started_ended ON user_sessions (started_at, ended_at)",
            
            # AI analysis indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_lead_type ON ai_analyses (lead_id, analysis_type)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_score_quality ON ai_analyses (lead_score, lead_quality)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_confidence ON ai_analyses (confidence_score, analyzed_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_nyc_market ON ai_analyses (nyc_market_score, solar_potential_score)",
            
            # Conversation indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_lead_session ON lead_conversations (lead_id, session_id, created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_type_created ON lead_conversations (message_type, created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_quality ON lead_conversations (response_quality_score, user_satisfaction_score)",
            
            # B2B mapping indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mapping_lead_platform ON b2b_lead_mappings (lead_id, platform_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mapping_status_created ON b2b_lead_mappings (mapping_status, created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mapping_revenue ON b2b_lead_mappings (net_revenue, created_at)",
            
            # Revenue transaction indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_lead_platform ON b2b_revenue_transactions (lead_id, platform_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_date_status ON b2b_revenue_transactions (transaction_date, status)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_revenue ON b2b_revenue_transactions (net_amount, transaction_date)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transaction_commission ON b2b_revenue_transactions (commission_amount, commission_paid)",
            
            # Text search indexes (using GIN for full-text search)
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_address_gin ON leads USING gin (to_tsvector('english', property_address))",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_notes_gin ON leads USING gin (to_tsvector('english', notes))",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_content_gin ON lead_conversations USING gin (to_tsvector('english', content))",
            
            # Partial indexes for active records
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_active_recent ON leads (created_at DESC) WHERE is_active = true AND created_at > NOW() - INTERVAL '30 days'",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_qualified_recent ON leads (qualified_at DESC) WHERE status = 'qualified' AND qualified_at > NOW() - INTERVAL '30 days'",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_exported_recent ON leads (exported_at DESC) WHERE export_status = 'exported' AND exported_at > NOW() - INTERVAL '30 days'",
        ]
    
    @staticmethod
    def get_analytics_materialized_views():
        """Get materialized views for analytics performance"""
        return [
            # Daily revenue summary
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_revenue_summary AS
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_leads,
                COUNT(*) FILTER (WHERE status = 'qualified') as qualified_leads,
                COUNT(*) FILTER (WHERE export_status = 'exported') as exported_leads,
                COUNT(*) FILTER (WHERE status = 'sold') as sold_leads,
                SUM(total_revenue_earned) as total_revenue,
                AVG(lead_score) as avg_lead_score,
                AVG(estimated_value) as avg_lead_value
            FROM leads 
            WHERE is_active = true
            GROUP BY DATE(created_at)
            """,
            
            # Platform performance summary
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_platform_performance_summary AS
            SELECT 
                p.platform_name,
                DATE(le.created_at) as date,
                COUNT(*) as total_exports,
                COUNT(*) FILTER (WHERE le.export_status = 'success') as successful_exports,
                COUNT(*) FILTER (WHERE le.export_status = 'failed') as failed_exports,
                AVG(le.commission_earned) as avg_commission,
                SUM(le.commission_earned) as total_commission
            FROM lead_exports le
            JOIN b2b_platforms p ON le.platform_id = p.id
            GROUP BY p.platform_name, DATE(le.created_at)
            """,
            
            # NYC borough performance
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_nyc_borough_performance AS
            SELECT 
                borough,
                DATE(created_at) as date,
                COUNT(*) as total_leads,
                AVG(lead_score) as avg_lead_score,
                AVG(monthly_electric_bill) as avg_electric_bill,
                SUM(total_revenue_earned) as total_revenue,
                AVG(estimated_value) as avg_lead_value
            FROM leads 
            WHERE is_active = true AND borough IS NOT NULL
            GROUP BY borough, DATE(created_at)
            """,
        ]
    
    @staticmethod
    def get_connection_pool_config():
        """Get optimized connection pool configuration"""
        return {
            'pool_size': 20,  # Base number of connections
            'max_overflow': 30,  # Additional connections when needed
            'pool_pre_ping': True,  # Validate connections before use
            'pool_recycle': 3600,  # Recycle connections after 1 hour
            'pool_timeout': 30,  # Timeout for getting connection
            'pool_reset_on_return': 'commit',  # Reset connection state
        }
    
    @staticmethod
    def get_query_optimization_hints():
        """Get query optimization hints and best practices"""
        return {
            'use_explain_analyze': True,  # Always use EXPLAIN ANALYZE for slow queries
            'enable_query_planning': True,  # Enable query plan analysis
            'use_prepared_statements': True,  # Use prepared statements for repeated queries
            'batch_operations': True,  # Batch database operations when possible
            'use_connection_pooling': True,  # Use connection pooling
            'monitor_slow_queries': True,  # Monitor and log slow queries
            'use_indexes_effectively': True,  # Ensure queries use appropriate indexes
            'avoid_n_plus_1': True,  # Avoid N+1 query problems
            'use_joins_over_subqueries': True,  # Prefer JOINs over subqueries
            'limit_result_sets': True,  # Always use LIMIT for large result sets
        }

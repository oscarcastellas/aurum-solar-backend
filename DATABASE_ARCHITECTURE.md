# Aurum Solar Database Architecture

## Overview

This document outlines the comprehensive database architecture for Aurum Solar, an AI-powered solar lead generation platform targeting the NYC market. The architecture is designed for high performance, scalability, and compliance with data privacy requirements.

## Database Schema Design

### Core Tables

#### 1. Lead Management (`leads`)
- **Primary Key**: UUID for better distribution
- **Key Fields**: Contact info, property details, solar potential, lead scoring
- **NYC-Specific**: Borough, zip code, electric rates, solar incentives
- **AI Integration**: AI analysis ID, conversation count, quality tracking
- **Performance**: 15+ indexes for query optimization

#### 2. Lead Conversations (`lead_conversations`)
- **Purpose**: Track AI agent interactions with leads
- **Features**: Sentiment analysis, intent classification, entity extraction
- **Performance**: Session-based grouping, message type indexing

#### 3. Lead Quality History (`lead_quality_history`)
- **Purpose**: Track lead quality score changes over time
- **Features**: Score change tracking, factor analysis, AI model versioning
- **Analytics**: Quality trend analysis, scoring algorithm improvement

#### 4. Lead Exports (`lead_exports`)
- **Purpose**: Track B2B platform exports with detailed status
- **Features**: Platform-specific data, revenue tracking, error handling
- **Performance**: Platform and status-based indexing

### NYC Market Intelligence

#### 1. NYC Zip Codes (`nyc_zip_codes`)
- **Purpose**: Comprehensive NYC market data per zip code
- **Data**: Demographics, solar adoption, electric rates, competition
- **Features**: Solar potential scoring, market saturation analysis
- **Performance**: Borough, income, and solar potential indexing

#### 2. NYC Incentives (`nyc_incentives`)
- **Purpose**: Track solar incentives by zip code
- **Features**: Federal, state, local incentive tracking
- **Management**: Expiration dates, eligibility requirements, usage tracking

#### 3. NYC Demographics (`nyc_demographics`)
- **Purpose**: Detailed demographic data for targeting
- **Data**: Age distribution, income, education, housing characteristics
- **Features**: Environmental consciousness scoring, technology adoption

#### 4. NYC Electric Rates (`nyc_electric_rates`)
- **Purpose**: Electric utility rates and pricing by zip code
- **Features**: Time-of-use rates, demand charges, solar-specific rates
- **Critical**: Essential for solar savings calculations

### B2B Platform Integration

#### 1. B2B Platforms (`b2b_platforms`)
- **Purpose**: Platform configuration and performance tracking
- **Features**: API configuration, pricing tiers, performance metrics
- **Management**: Health monitoring, error tracking, rate limiting

#### 2. B2B Lead Mappings (`b2b_lead_mappings`)
- **Purpose**: Many-to-many relationship between leads and platforms
- **Features**: Platform-specific lead IDs, quality tracking, revenue details
- **Performance**: Lead-platform composite indexing

#### 3. B2B Revenue Transactions (`b2b_revenue_transactions`)
- **Purpose**: Detailed revenue tracking from platform sales
- **Features**: Commission tracking, payment processing, reconciliation
- **Compliance**: Financial record keeping, audit trails

### AI and Analytics

#### 1. AI Models (`ai_models`)
- **Purpose**: AI model configuration and performance tracking
- **Features**: Model versioning, performance metrics, cost tracking
- **Management**: Request limits, quality monitoring, A/B testing

#### 2. AI Analyses (`ai_analyses`)
- **Purpose**: AI analysis results for leads
- **Features**: Lead scoring, insights, recommendations, confidence tracking
- **Performance**: Lead and analysis type indexing

#### 3. AI Conversations (`ai_conversations`)
- **Purpose**: AI conversation tracking and analysis
- **Features**: Sentiment analysis, intent classification, quality scoring
- **Analytics**: Conversation flow analysis, user satisfaction tracking

#### 4. AI Insights (`ai_insights`)
- **Purpose**: AI-generated insights and recommendations
- **Features**: Pattern recognition, trend analysis, business recommendations
- **Management**: Validation tracking, implementation status

### Analytics and Performance

#### 1. Revenue Metrics (`revenue_metrics`)
- **Purpose**: Time-series revenue and performance data
- **Features**: Daily, weekly, monthly aggregations
- **Analytics**: Growth tracking, conversion rates, platform breakdowns

#### 2. Platform Performance (`platform_performance`)
- **Purpose**: B2B platform performance tracking
- **Features**: Export metrics, acceptance rates, revenue tracking
- **Monitoring**: Error rates, uptime, customer satisfaction

#### 3. NYC Market Intelligence (`nyc_market_intelligence`)
- **Purpose**: Aggregated NYC market trends and analysis
- **Features**: Market penetration, competition analysis, growth trends
- **Insights**: Borough-level performance, market maturity assessment

#### 4. User Sessions (`user_sessions`)
- **Purpose**: User engagement and conversion tracking
- **Features**: Session analytics, conversion funnel analysis
- **Marketing**: UTM tracking, device analytics, geographic data

### Authentication and Security

#### 1. Users (`users`)
- **Purpose**: User authentication and profile management
- **Features**: Multi-factor authentication, security tracking
- **Compliance**: GDPR compliance, data retention

#### 2. User Roles (`user_roles`)
- **Purpose**: Role-based access control
- **Features**: Permission management, role expiration
- **Security**: Granular permission system

#### 3. User Permissions (`user_permissions`)
- **Purpose**: Granular permission system
- **Features**: Resource-action based permissions
- **Management**: System and custom permissions

## Performance Optimization

### Indexing Strategy

#### Primary Indexes
- **UUID Primary Keys**: All tables use UUID for better distribution
- **Composite Indexes**: Multi-column indexes for common query patterns
- **Partial Indexes**: Filtered indexes for active records only
- **Covering Indexes**: Include frequently accessed columns

#### Performance-Critical Indexes
```sql
-- Lead performance indexes
CREATE INDEX CONCURRENTLY idx_lead_created_status ON leads (created_at, status) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_lead_quality_score ON leads (lead_quality, lead_score) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_lead_zip_quality ON leads (zip_code, lead_quality) WHERE is_active = true;

-- Revenue analytics indexes
CREATE INDEX CONCURRENTLY idx_revenue_date_period ON revenue_metrics (date, period_type);
CREATE INDEX CONCURRENTLY idx_revenue_qualified_sold ON revenue_metrics (qualified_leads, sold_leads);

-- Platform performance indexes
CREATE INDEX CONCURRENTLY idx_platform_acceptance_revenue ON platform_performance (acceptance_rate, total_revenue);

-- NYC market intelligence indexes
CREATE INDEX CONCURRENTLY idx_nyc_zip_date ON nyc_market_intelligence (zip_code, date);
CREATE INDEX CONCURRENTLY idx_nyc_adoption_revenue ON nyc_market_intelligence (solar_adoption_rate, total_revenue);
```

#### Text Search Indexes
```sql
-- Full-text search indexes using GIN
CREATE INDEX CONCURRENTLY idx_lead_address_gin ON leads USING gin (to_tsvector('english', property_address));
CREATE INDEX CONCURRENTLY idx_conversation_content_gin ON lead_conversations USING gin (to_tsvector('english', content));
```

### Materialized Views

#### Analytics Performance
```sql
-- Daily revenue summary
CREATE MATERIALIZED VIEW mv_daily_revenue_summary AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_leads,
    COUNT(*) FILTER (WHERE status = 'qualified') as qualified_leads,
    SUM(total_revenue_earned) as total_revenue,
    AVG(lead_score) as avg_lead_score
FROM leads 
WHERE is_active = true
GROUP BY DATE(created_at);

-- Platform performance summary
CREATE MATERIALIZED VIEW mv_platform_performance_summary AS
SELECT 
    p.platform_name,
    DATE(le.created_at) as date,
    COUNT(*) as total_exports,
    AVG(le.commission_earned) as avg_commission
FROM lead_exports le
JOIN b2b_platforms p ON le.platform_id = p.id
GROUP BY p.platform_name, DATE(le.created_at);
```

### Connection Pooling

#### Production Configuration
```python
PRODUCTION_POOL_CONFIG = {
    'poolclass': QueuePool,
    'pool_size': 20,  # Base connections
    'max_overflow': 30,  # Additional connections
    'pool_pre_ping': True,  # Validate connections
    'pool_recycle': 3600,  # 1 hour recycle
    'pool_timeout': 30,  # Connection timeout
}
```

#### Read Replica Support
- Separate read replica for analytics queries
- Read-only optimizations
- Reduced connection pool for read operations

## Data Retention and Compliance

### Retention Policies

#### Data Types and Retention Periods
```python
RETENTION_PERIODS = {
    'leads': 2555,  # 7 years for business records
    'conversations': 1095,  # 3 years for conversation history
    'user_sessions': 365,  # 1 year for session data
    'ai_analyses': 1095,  # 3 years for AI analysis data
    'revenue_transactions': 2555,  # 7 years for financial records
    'platform_performance': 1095,  # 3 years for performance data
    'user_activity_logs': 365,  # 1 year for activity logs
    'error_logs': 90,  # 3 months for error logs
}
```

#### GDPR Compliance
- Data anonymization for privacy compliance
- Right to be forgotten implementation
- Consent tracking and management
- Data portability support

### Automated Cleanup
- Scheduled data retention cleanup
- Soft delete for business records
- Hard delete for expired data
- Compliance reporting

## NYC Market Intelligence

### Zip Code Data Structure
Each NYC zip code includes:
- **Demographics**: Population, income, age distribution
- **Housing**: Property types, home values, ownership rates
- **Solar Market**: Adoption rates, installation costs, savings
- **Electric Utility**: Rates, providers, peak demand
- **Competition**: Installer count, market saturation
- **Incentives**: Federal, state, local incentive availability

### Market Analysis Features
- Solar potential scoring by zip code
- High-value zip code identification
- Competition intensity analysis
- Market maturity assessment
- Growth trend tracking

## Scalability Considerations

### Horizontal Scaling
- UUID primary keys for better distribution
- Sharding-ready table design
- Read replica support
- Connection pooling optimization

### Vertical Scaling
- Optimized indexes for query performance
- Materialized views for analytics
- Efficient data types and constraints
- Memory-optimized connection pooling

### Performance Monitoring
- Query performance tracking
- Connection pool monitoring
- Index usage analysis
- Slow query identification

## Security and Compliance

### Data Protection
- Encrypted sensitive data fields
- GDPR compliance features
- Data retention automation
- Audit trail maintenance

### Access Control
- Role-based permissions
- Resource-action based access
- API key management
- Session security

### Monitoring and Alerting
- Database performance monitoring
- Connection pool health checks
- Query performance alerts
- Security event logging

## Migration and Deployment

### Database Migrations
- Alembic-based schema evolution
- Version-controlled migrations
- Rollback capabilities
- Data migration scripts

### Deployment Strategy
- Blue-green deployments
- Zero-downtime migrations
- Connection pool management
- Performance monitoring

### Backup and Recovery
- Automated backups
- Point-in-time recovery
- Cross-region replication
- Disaster recovery procedures

## Monitoring and Maintenance

### Performance Monitoring
- Query execution time tracking
- Connection pool utilization
- Index usage analysis
- Slow query identification

### Health Checks
- Database connectivity
- Connection pool status
- Query performance
- Data integrity checks

### Maintenance Tasks
- Index maintenance
- Statistics updates
- Vacuum operations
- Data retention cleanup

This database architecture provides a solid foundation for Aurum Solar's AI-powered solar lead generation platform, with comprehensive NYC market intelligence, high performance, and full compliance with data privacy requirements.

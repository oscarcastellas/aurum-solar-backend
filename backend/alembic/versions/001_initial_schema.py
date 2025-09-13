"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')  # For text search
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')  # For JSON indexing
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('zip_code', sa.String(length=10), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True, server_default='US'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('email_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('phone_verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('two_factor_secret', sa.String(length=32), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True, server_default='America/New_York'),
        sa.Column('language', sa.String(length=5), nullable=True, server_default='en'),
        sa.Column('notification_preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('dashboard_preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_name', sa.String(length=100), nullable=False),
        sa.Column('role_description', sa.Text(), nullable=True),
        sa.Column('is_primary_role', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_name', name='uq_user_role')
    )
    
    # Create user_permissions table
    op.create_table('user_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('permission_name', sa.String(length=100), nullable=False),
        sa.Column('permission_category', sa.String(length=50), nullable=False),
        sa.Column('permission_description', sa.Text(), nullable=True),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_system_permission', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('permission_name', name='uq_permission_name')
    )
    
    # Create b2b_platforms table
    op.create_table('b2b_platforms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('platform_name', sa.String(length=100), nullable=False),
        sa.Column('platform_code', sa.String(length=50), nullable=False),
        sa.Column('platform_type', sa.String(length=50), nullable=True),
        sa.Column('api_base_url', sa.String(length=500), nullable=False),
        sa.Column('api_version', sa.String(length=20), nullable=True, server_default='v1'),
        sa.Column('authentication_type', sa.String(length=50), nullable=True, server_default='api_key'),
        sa.Column('api_credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('min_lead_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('max_lead_score', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('accepted_lead_qualities', postgresql.ARRAY(sa.String()), nullable=True, server_default='{"hot","warm"}'),
        sa.Column('base_price_per_lead', sa.Float(), nullable=False),
        sa.Column('price_tiers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True, server_default='0.15'),
        sa.Column('required_fields', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('optional_fields', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('data_format', sa.String(length=50), nullable=True, server_default='json'),
        sa.Column('lead_validation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('supports_bulk_export', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('supports_real_time_export', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('supports_lead_updates', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('supports_revenue_tracking', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('max_export_batch_size', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('total_leads_exported', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('successful_exports', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_exports', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('acceptance_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('average_response_time_ms', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_revenue_generated', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_commission_earned', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('average_lead_value', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_accepting_leads', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('maintenance_mode', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(length=20), nullable=True, server_default='unknown'),
        sa.Column('consecutive_failures', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requests_per_minute', sa.Integer(), nullable=True, server_default='60'),
        sa.Column('requests_per_hour', sa.Integer(), nullable=True, server_default='1000'),
        sa.Column('daily_export_limit', sa.Integer(), nullable=True),
        sa.Column('monthly_export_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_export_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('platform_name', name='uq_platform_name'),
        sa.UniqueConstraint('platform_code', name='uq_platform_code')
    )
    
    # Create ai_models table
    op.create_table('ai_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('model_provider', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('model_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('prompt_templates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('successful_requests', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_requests', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('average_response_time_ms', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('average_tokens_used', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('average_cost_per_request', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('precision_score', sa.Float(), nullable=True),
        sa.Column('recall_score', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('user_satisfaction_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('maintenance_mode', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('daily_request_limit', sa.Integer(), nullable=True),
        sa.Column('monthly_request_limit', sa.Integer(), nullable=True),
        sa.Column('cost_limit_daily', sa.Float(), nullable=True),
        sa.Column('cost_limit_monthly', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name', name='uq_ai_model_name')
    )
    
    # Create nyc_zip_codes table
    op.create_table('nyc_zip_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('zip_code', sa.String(length=10), nullable=False),
        sa.Column('borough', sa.String(length=50), nullable=False),
        sa.Column('neighborhood', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('area_sq_miles', sa.Float(), nullable=True),
        sa.Column('total_population', sa.Integer(), nullable=True),
        sa.Column('median_age', sa.Float(), nullable=True),
        sa.Column('median_household_income', sa.Float(), nullable=True),
        sa.Column('homeownership_rate', sa.Float(), nullable=True),
        sa.Column('average_home_value', sa.Float(), nullable=True),
        sa.Column('average_rent', sa.Float(), nullable=True),
        sa.Column('total_housing_units', sa.Integer(), nullable=True),
        sa.Column('single_family_homes', sa.Integer(), nullable=True),
        sa.Column('multi_family_homes', sa.Integer(), nullable=True),
        sa.Column('average_home_age', sa.Float(), nullable=True),
        sa.Column('average_home_size_sqft', sa.Float(), nullable=True),
        sa.Column('solar_adoption_rate', sa.Float(), nullable=True),
        sa.Column('total_solar_installations', sa.Integer(), nullable=True),
        sa.Column('average_system_size_kw', sa.Float(), nullable=True),
        sa.Column('average_installation_cost', sa.Float(), nullable=True),
        sa.Column('average_savings_per_month', sa.Float(), nullable=True),
        sa.Column('average_payback_period_years', sa.Float(), nullable=True),
        sa.Column('primary_electric_provider', sa.String(length=100), nullable=True),
        sa.Column('average_electric_rate_per_kwh', sa.Float(), nullable=True),
        sa.Column('average_monthly_bill', sa.Float(), nullable=True),
        sa.Column('peak_demand_charges', sa.Float(), nullable=True),
        sa.Column('solar_potential_score', sa.Float(), nullable=True),
        sa.Column('average_roof_size_sqft', sa.Float(), nullable=True),
        sa.Column('average_roof_condition', sa.String(length=50), nullable=True),
        sa.Column('shading_factor', sa.Float(), nullable=True),
        sa.Column('roof_orientation_score', sa.Float(), nullable=True),
        sa.Column('solar_installers_count', sa.Integer(), nullable=True),
        sa.Column('market_saturation', sa.Float(), nullable=True),
        sa.Column('competition_intensity', sa.String(length=20), nullable=True),
        sa.Column('state_incentives_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('local_incentives_available', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('net_metering_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('community_solar_available', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('high_value_zip_code', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('average_lead_value', sa.Float(), nullable=True),
        sa.Column('lead_volume_per_month', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('data_source', sa.String(length=100), nullable=True),
        sa.Column('data_confidence', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('zip_code', name='uq_nyc_zip_code')
    )
    
    # Create leads table
    op.create_table('leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('property_address', sa.String(length=500), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True, server_default='New York'),
        sa.Column('state', sa.String(length=2), nullable=True, server_default='NY'),
        sa.Column('zip_code', sa.String(length=10), nullable=False),
        sa.Column('borough', sa.String(length=50), nullable=True),
        sa.Column('property_type', sa.String(length=50), nullable=True),
        sa.Column('square_footage', sa.Integer(), nullable=True),
        sa.Column('lot_size', sa.Float(), nullable=True),
        sa.Column('roof_type', sa.String(length=50), nullable=True),
        sa.Column('roof_condition', sa.String(length=50), nullable=True),
        sa.Column('roof_age', sa.Integer(), nullable=True),
        sa.Column('roof_slope', sa.String(length=20), nullable=True),
        sa.Column('roof_orientation', sa.String(length=20), nullable=True),
        sa.Column('monthly_electric_bill', sa.Float(), nullable=True),
        sa.Column('annual_electric_usage', sa.Float(), nullable=True),
        sa.Column('electric_provider', sa.String(length=100), nullable=True),
        sa.Column('current_rate_per_kwh', sa.Float(), nullable=True),
        sa.Column('solar_potential_score', sa.Float(), nullable=True),
        sa.Column('estimated_system_size', sa.Float(), nullable=True),
        sa.Column('estimated_annual_production', sa.Float(), nullable=True),
        sa.Column('estimated_savings_annual', sa.Float(), nullable=True),
        sa.Column('estimated_payback_period', sa.Float(), nullable=True),
        sa.Column('lead_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('lead_quality', sa.String(length=20), nullable=True, server_default='cold'),
        sa.Column('qualification_status', sa.String(length=50), nullable=True, server_default='unqualified'),
        sa.Column('qualification_reason', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('source_campaign', sa.String(length=100), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_medium', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('referrer_url', sa.Text(), nullable=True),
        sa.Column('ai_analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_conversation_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='new'),
        sa.Column('export_status', sa.String(length=50), nullable=True),
        sa.Column('sales_stage', sa.String(length=50), nullable=True, server_default='prospect'),
        sa.Column('estimated_value', sa.Float(), nullable=True),
        sa.Column('actual_value', sa.Float(), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True, server_default='0.15'),
        sa.Column('total_revenue_earned', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('exported_to_platforms', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('export_timestamps', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('platform_lead_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_contacted', sa.DateTime(timezone=True), nullable=True),
        sa.Column('qualified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_gdpr_compliant', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('consent_given_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('custom_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_lead_email')
    )
    
    # Create remaining tables...
    # (Additional table creation statements would continue here)
    
    # Create indexes
    op.create_index('idx_lead_created_status', 'leads', ['created_at', 'status'])
    op.create_index('idx_lead_quality_score', 'leads', ['lead_quality', 'lead_score'])
    op.create_index('idx_lead_zip_quality', 'leads', ['zip_code', 'lead_quality'])
    op.create_index('idx_lead_revenue', 'leads', ['total_revenue_earned', 'created_at'])
    op.create_index('idx_lead_export_status', 'leads', ['export_status', 'created_at'])
    op.create_index('idx_lead_borough_type', 'leads', ['borough', 'property_type'])
    op.create_index('idx_lead_electric_bill', 'leads', ['monthly_electric_bill', 'zip_code'])
    
    op.create_index('idx_user_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_user_last_login', 'users', ['last_login_at', 'is_active'])
    op.create_index('idx_user_created_active', 'users', ['created_at', 'is_active'])
    
    op.create_index('idx_platform_active_accepting', 'b2b_platforms', ['is_active', 'is_accepting_leads'])
    op.create_index('idx_platform_performance', 'b2b_platforms', ['acceptance_rate', 'total_revenue_generated'])
    op.create_index('idx_platform_health', 'b2b_platforms', ['health_status', 'last_health_check'])
    
    op.create_index('idx_zip_borough_income', 'nyc_zip_codes', ['borough', 'median_household_income'])
    op.create_index('idx_zip_solar_potential', 'nyc_zip_codes', ['solar_potential_score', 'solar_adoption_rate'])
    op.create_index('idx_zip_high_value', 'nyc_zip_codes', ['high_value_zip_code', 'conversion_rate'])
    op.create_index('idx_zip_competition', 'nyc_zip_codes', ['competition_intensity', 'market_saturation'])


def downgrade() -> None:
    """Drop initial database schema"""
    
    # Drop indexes
    op.drop_index('idx_zip_competition', table_name='nyc_zip_codes')
    op.drop_index('idx_zip_high_value', table_name='nyc_zip_codes')
    op.drop_index('idx_zip_solar_potential', table_name='nyc_zip_codes')
    op.drop_index('idx_zip_borough_income', table_name='nyc_zip_codes')
    
    op.drop_index('idx_platform_health', table_name='b2b_platforms')
    op.drop_index('idx_platform_performance', table_name='b2b_platforms')
    op.drop_index('idx_platform_active_accepting', table_name='b2b_platforms')
    
    op.drop_index('idx_user_created_active', table_name='users')
    op.drop_index('idx_user_last_login', table_name='users')
    op.drop_index('idx_user_email_active', table_name='users')
    
    op.drop_index('idx_lead_electric_bill', table_name='leads')
    op.drop_index('idx_lead_borough_type', table_name='leads')
    op.drop_index('idx_lead_export_status', table_name='leads')
    op.drop_index('idx_lead_revenue', table_name='leads')
    op.drop_index('idx_lead_zip_quality', table_name='leads')
    op.drop_index('idx_lead_quality_score', table_name='leads')
    op.drop_index('idx_lead_created_status', table_name='leads')
    
    # Drop tables
    op.drop_table('leads')
    op.drop_table('nyc_zip_codes')
    op.drop_table('ai_models')
    op.drop_table('b2b_platforms')
    op.drop_table('user_permissions')
    op.drop_table('user_roles')
    op.drop_table('users')

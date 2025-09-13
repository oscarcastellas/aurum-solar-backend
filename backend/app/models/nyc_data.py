"""
NYC-specific data models for market intelligence and personalization
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.db_types import UUIDType, ArrayStringType, ArrayUUIDType, get_uuid_default
from app.core.database import Base
import uuid


class NYCZipCode(Base):
    """
    NYC zip code intelligence for solar market analysis
    Provides demographic, economic, and solar potential data
    """
    __tablename__ = "nyc_zip_codes"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    zip_code = Column(String(10), unique=True, nullable=False, index=True)
    borough = Column(String(50), nullable=False, index=True)
    neighborhood = Column(String(100), index=True)
    
    # Geographic data
    latitude = Column(Float)
    longitude = Column(Float)
    area_sq_miles = Column(Float)
    
    # Demographics
    total_population = Column(Integer)
    median_age = Column(Float)
    median_household_income = Column(Float, index=True)
    homeownership_rate = Column(Float)
    average_home_value = Column(Float, index=True)
    average_rent = Column(Float)
    
    # Housing characteristics
    total_housing_units = Column(Integer)
    single_family_homes = Column(Integer)
    multi_family_homes = Column(Integer)
    average_home_age = Column(Float)
    average_home_size_sqft = Column(Float)
    
    # Solar market data
    solar_adoption_rate = Column(Float, index=True)  # Percentage of homes with solar
    total_solar_installations = Column(Integer)
    average_system_size_kw = Column(Float)
    average_installation_cost = Column(Float)
    average_savings_per_month = Column(Float)
    average_payback_period_years = Column(Float)
    
    # Electric utility data
    primary_electric_provider = Column(String(100))
    average_electric_rate_per_kwh = Column(Float, index=True)
    average_monthly_bill = Column(Float, index=True)
    peak_demand_charges = Column(Float)
    
    # Solar potential assessment
    solar_potential_score = Column(Float, index=True)  # 0-100
    average_roof_size_sqft = Column(Float)
    average_roof_condition = Column(String(50))
    shading_factor = Column(Float)  # 0-1, lower is better
    roof_orientation_score = Column(Float)  # 0-100
    
    # Market competition
    solar_installers_count = Column(Integer, index=True)
    market_saturation = Column(Float, index=True)  # 0-1
    competition_intensity = Column(String(20))  # low, medium, high
    
    # Incentives and regulations
    state_incentives_available = Column(Boolean, default=True)
    local_incentives_available = Column(Boolean, default=False)
    net_metering_available = Column(Boolean, default=True)
    community_solar_available = Column(Boolean, default=False)
    
    # Lead quality indicators
    high_value_zip_code = Column(Boolean, default=False, index=True)
    conversion_rate = Column(Float, index=True)
    average_lead_value = Column(Float, index=True)
    lead_volume_per_month = Column(Integer, index=True)
    
    # Data freshness
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    data_source = Column(String(100))
    data_confidence = Column(Float)  # 0-1
    
    # Relationships
    incentives = relationship("NYCIncentive", back_populates="zip_code")
    demographics = relationship("NYCDemographic", back_populates="zip_code")
    electric_rates = relationship("NYCElectricRate", back_populates="zip_code")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_zip_borough_income', 'borough', 'median_household_income'),
        Index('idx_zip_solar_potential', 'solar_potential_score', 'solar_adoption_rate'),
        Index('idx_zip_high_value', 'high_value_zip_code', 'conversion_rate'),
        Index('idx_zip_competition', 'competition_intensity', 'market_saturation'),
        UniqueConstraint('zip_code', name='uq_nyc_zip_code'),
        {'extend_existing': True}  # Allow table redefinition
    )


class NYCIncentive(Base):
    """
    NYC-specific solar incentives and their availability by zip code
    Tracks expiration dates and eligibility requirements
    """
    __tablename__ = "nyc_incentives"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    zip_code_id = Column(UUIDType, ForeignKey("nyc_zip_codes.id"), nullable=False, index=True)
    
    # Incentive details
    incentive_name = Column(String(200), nullable=False, index=True)
    incentive_type = Column(String(50), nullable=False, index=True)  # federal, state, local, utility
    incentive_category = Column(String(50), index=True)  # tax_credit, rebate, grant, loan
    
    # Financial details
    incentive_amount = Column(Float, index=True)
    incentive_percentage = Column(Float)
    max_incentive_amount = Column(Float)
    incentive_per_kw = Column(Float)
    
    # Eligibility requirements
    eligibility_criteria = Column(JSON)
    income_limits = Column(JSON)
    system_size_limits = Column(JSON)
    property_type_requirements = Column(ArrayStringType)
    
    # Availability
    is_active = Column(Boolean, default=True, index=True)
    start_date = Column(DateTime(timezone=True), index=True)
    end_date = Column(DateTime(timezone=True), index=True)
    application_deadline = Column(DateTime(timezone=True))
    
    # Usage tracking
    total_applications = Column(Integer, default=0)
    total_amount_awarded = Column(Float, default=0.0)
    remaining_funding = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    zip_code = relationship("NYCZipCode", back_populates="incentives")
    
    # Indexes
    __table_args__ = (
        Index('idx_incentive_zip_type', 'zip_code_id', 'incentive_type'),
        Index('idx_incentive_active_dates', 'is_active', 'start_date', 'end_date'),
        Index('idx_incentive_amount', 'incentive_amount', 'is_active'),
    )


class NYCDemographic(Base):
    """
    Detailed demographic data for NYC zip codes
    Enables targeted lead generation and personalization
    """
    __tablename__ = "nyc_demographics"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    zip_code_id = Column(UUIDType, ForeignKey("nyc_zip_codes.id"), nullable=False, index=True)
    
    # Population demographics
    age_distribution = Column(JSON)  # Age groups and percentages
    education_levels = Column(JSON)  # Education attainment percentages
    employment_status = Column(JSON)  # Employment statistics
    occupation_categories = Column(JSON)  # Job type distribution
    
    # Housing demographics
    housing_tenure = Column(JSON)  # Owner vs renter percentages
    housing_type_distribution = Column(JSON)  # Single family, multi-family, etc.
    average_household_size = Column(Float)
    family_composition = Column(JSON)  # Family types and percentages
    
    # Economic indicators
    poverty_rate = Column(Float, index=True)
    unemployment_rate = Column(Float, index=True)
    gini_coefficient = Column(Float)  # Income inequality measure
    economic_mobility_score = Column(Float)
    
    # Technology adoption
    internet_penetration = Column(Float)
    smartphone_penetration = Column(Float)
    social_media_usage = Column(JSON)
    
    # Environmental consciousness
    environmental_concern_score = Column(Float, index=True)
    green_energy_adoption_rate = Column(Float)
    sustainability_interest_score = Column(Float)
    
    # Data source and freshness
    data_source = Column(String(100))
    data_year = Column(Integer, index=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    zip_code = relationship("NYCZipCode", back_populates="demographics")
    
    # Indexes
    __table_args__ = (
        Index('idx_demo_zip_year', 'zip_code_id', 'data_year'),
        Index('idx_demo_environmental', 'environmental_concern_score', 'green_energy_adoption_rate'),
        {'extend_existing': True}  # Allow table redefinition
    )


class NYCElectricRate(Base):
    """
    Electric utility rates and pricing by NYC zip code
    Critical for solar savings calculations
    """
    __tablename__ = "nyc_electric_rates"
    
    id = Column(UUIDType, primary_key=True, default=get_uuid_default, index=True)
    zip_code_id = Column(UUIDType, ForeignKey("nyc_zip_codes.id"), nullable=False, index=True)
    
    # Utility information
    utility_company = Column(String(100), nullable=False, index=True)
    rate_schedule = Column(String(100), index=True)
    customer_class = Column(String(50), index=True)  # residential, commercial, industrial
    
    # Rate structure
    base_rate_per_kwh = Column(Float, index=True)
    delivery_charge_per_kwh = Column(Float)
    supply_charge_per_kwh = Column(Float)
    total_rate_per_kwh = Column(Float, index=True)
    
    # Time-of-use rates
    peak_rate_per_kwh = Column(Float)
    off_peak_rate_per_kwh = Column(Float)
    shoulder_rate_per_kwh = Column(Float)
    peak_hours = Column(JSON)  # Peak time periods
    
    # Demand charges
    demand_charge_per_kw = Column(Float)
    demand_charge_period = Column(String(50))
    
    # Additional charges
    connection_charge = Column(Float)
    meter_charge = Column(Float)
    service_charge = Column(Float)
    taxes_and_fees = Column(JSON)
    
    # Rate changes
    effective_date = Column(DateTime(timezone=True), index=True)
    expiration_date = Column(DateTime(timezone=True))
    rate_change_frequency = Column(String(50))  # monthly, quarterly, annually
    
    # Solar-specific rates
    net_metering_rate = Column(Float)
    net_metering_credits_expire = Column(Boolean, default=False)
    net_metering_credit_expiry_months = Column(Integer)
    solar_credit_rate = Column(Float)
    
    # Data freshness
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    data_source = Column(String(100))
    
    # Relationships
    zip_code = relationship("NYCZipCode", back_populates="electric_rates")
    
    # Indexes
    __table_args__ = (
        Index('idx_electric_zip_utility', 'zip_code_id', 'utility_company'),
        Index('idx_electric_rate_effective', 'total_rate_per_kwh', 'effective_date'),
        Index('idx_electric_solar_rates', 'net_metering_rate', 'solar_credit_rate'),
    )

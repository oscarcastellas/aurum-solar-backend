"""
Database models for solar calculation results
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SolarCalculation(Base):
    """Store solar calculation results for lead qualification"""
    __tablename__ = "solar_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Input parameters
    zip_code = Column(String(10), nullable=False)
    monthly_bill = Column(Float, nullable=False)
    borough = Column(String(50), nullable=True)
    roof_type = Column(String(50), nullable=True)
    roof_size = Column(Float, nullable=True)
    shading_factor = Column(Float, nullable=True)
    home_type = Column(String(50), nullable=True)
    
    # Calculation results
    system_size_kw = Column(Float, nullable=False)
    panel_count = Column(Integer, nullable=False)
    panel_type = Column(String(50), nullable=False)
    roof_area_required = Column(Float, nullable=False)
    annual_production_kwh = Column(Integer, nullable=False)
    
    # Financial analysis
    monthly_savings = Column(Float, nullable=False)
    annual_savings = Column(Float, nullable=False)
    gross_cost = Column(Float, nullable=False)
    federal_credit = Column(Float, nullable=False)
    nyserda_rebate = Column(Float, nullable=False)
    property_tax_abatement = Column(Float, nullable=False)
    net_cost = Column(Float, nullable=False)
    payback_years = Column(Float, nullable=False)
    lifetime_savings = Column(Float, nullable=False)
    roi_percentage = Column(Float, nullable=False)
    
    # Additional data
    financing_options = Column(JSON, nullable=True)
    roof_assessment = Column(JSON, nullable=True)
    permit_estimate = Column(JSON, nullable=True)
    installation_timeline = Column(String(255), nullable=True)
    
    # Metadata
    confidence_score = Column(Float, nullable=False)
    calculation_version = Column(String(50), nullable=False, default="v1.0")
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="solar_calculations")


class SolarSystemRecommendation(Base):
    """Store detailed system recommendations for B2B export"""
    __tablename__ = "solar_system_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    calculation_id = Column(Integer, ForeignKey("solar_calculations.id"), nullable=False)
    
    # System specifications
    system_size_kw = Column(Float, nullable=False)
    panel_count = Column(Integer, nullable=False)
    panel_type = Column(String(50), nullable=False)
    inverter_type = Column(String(50), nullable=True)
    mounting_system = Column(String(50), nullable=True)
    
    # Roof requirements
    roof_area_required = Column(Float, nullable=False)
    roof_type = Column(String(50), nullable=True)
    roof_condition = Column(String(50), nullable=True)
    structural_requirements = Column(JSON, nullable=True)
    
    # Production estimates
    annual_production_kwh = Column(Integer, nullable=False)
    monthly_production_kwh = Column(Float, nullable=False)
    peak_power_kw = Column(Float, nullable=False)
    capacity_factor = Column(Float, nullable=False)
    
    # Financial projections
    gross_cost = Column(Float, nullable=False)
    net_cost = Column(Float, nullable=False)
    monthly_savings = Column(Float, nullable=False)
    annual_savings = Column(Float, nullable=False)
    payback_years = Column(Float, nullable=False)
    lifetime_savings = Column(Float, nullable=False)
    roi_percentage = Column(Float, nullable=False)
    
    # Incentive breakdown
    federal_credit = Column(Float, nullable=False)
    nyserda_rebate = Column(Float, nullable=False)
    property_tax_abatement = Column(Float, nullable=False)
    total_incentives = Column(Float, nullable=False)
    
    # Installation details
    installation_timeline = Column(String(255), nullable=True)
    permit_requirements = Column(JSON, nullable=True)
    installation_complexity = Column(String(50), nullable=True)
    estimated_install_days = Column(Integer, nullable=True)
    
    # B2B export data
    b2b_value_estimate = Column(Float, nullable=True)
    qualification_tier = Column(String(50), nullable=True)
    export_ready = Column(Boolean, default=False)
    export_timestamp = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="system_recommendations")
    calculation = relationship("SolarCalculation")


class SolarIncentive(Base):
    """Store current solar incentives and rebates"""
    __tablename__ = "solar_incentives"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # federal, state, local, utility
    amount = Column(Float, nullable=True)
    amount_type = Column(String(50), nullable=True)  # fixed, per_kw, percentage
    max_amount = Column(Float, nullable=True)
    min_amount = Column(Float, nullable=True)
    
    # Eligibility criteria
    zip_codes = Column(JSON, nullable=True)  # List of eligible ZIP codes
    boroughs = Column(JSON, nullable=True)  # List of eligible boroughs
    utility_territories = Column(JSON, nullable=True)  # Con Edison, PSEG
    home_types = Column(JSON, nullable=True)  # single_family, condo, etc.
    income_limits = Column(JSON, nullable=True)  # Income eligibility
    
    # Dates
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=True)
    application_deadline = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_limited_funding = Column(Boolean, default=False)
    remaining_funding = Column(Float, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    application_url = Column(String(500), nullable=True)
    requirements = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SolarMarketData(Base):
    """Store NYC solar market data for calculations"""
    __tablename__ = "solar_market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    zip_code = Column(String(10), nullable=False, index=True)
    borough = Column(String(50), nullable=True)
    utility_territory = Column(String(50), nullable=False)
    
    # Electric rates
    electric_rate_per_kwh = Column(Float, nullable=False)
    rate_schedule = Column(String(50), nullable=True)
    rate_effective_date = Column(DateTime, nullable=True)
    
    # Solar irradiance
    solar_irradiance = Column(Float, nullable=False)  # kWh/kW annually
    irradiance_source = Column(String(100), nullable=True)
    irradiance_date = Column(DateTime, nullable=True)
    
    # Market data
    average_system_cost_per_watt = Column(Float, nullable=False)
    average_system_size_kw = Column(Float, nullable=False)
    solar_adoption_rate = Column(Float, nullable=True)
    competition_intensity = Column(String(50), nullable=True)
    
    # Installation factors
    average_install_time_days = Column(Integer, nullable=True)
    permit_approval_time_days = Column(Integer, nullable=True)
    interconnection_time_days = Column(Integer, nullable=True)
    
    # Metadata
    data_source = Column(String(100), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

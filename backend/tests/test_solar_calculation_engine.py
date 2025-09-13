"""
Unit tests for Solar Calculation Engine
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.solar_calculation_engine import (
    SolarCalculationEngine,
    SolarSystemRecommendation,
    NYCSolarParameters,
    UtilityTerritory,
    RoofType
)


class TestSolarCalculationEngine:
    """Test cases for Solar Calculation Engine"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def engine(self, mock_db):
        """Create engine instance with mocked dependencies"""
        with patch('app.services.solar_calculation_engine.redis.Redis'):
            return SolarCalculationEngine(mock_db)
    
    def test_determine_utility_territory_con_edison(self, engine):
        """Test Con Edison territory detection"""
        # Manhattan ZIP codes
        assert engine._determine_utility_territory("10001", "manhattan") == UtilityTerritory.CON_EDISON
        assert engine._determine_utility_territory("10025", "manhattan") == UtilityTerritory.CON_EDISON
        
        # Bronx ZIP codes
        assert engine._determine_utility_territory("10451", "bronx") == UtilityTerritory.CON_EDISON
        
        # Westchester
        assert engine._determine_utility_territory("10501", None) == UtilityTerritory.CON_EDISON
    
    def test_determine_utility_territory_pseg(self, engine):
        """Test PSEG territory detection"""
        # Queens ZIP codes
        assert engine._determine_utility_territory("11375", "queens") == UtilityTerritory.PSEG
        assert engine._determine_utility_territory("11401", "queens") == UtilityTerritory.PSEG
        
        # Staten Island
        assert engine._determine_utility_territory("10301", "staten_island") == UtilityTerritory.PSEG
    
    def test_calculate_annual_usage(self, engine):
        """Test annual usage calculation"""
        # Con Edison rate: $0.31/kWh
        monthly_bill = 300.0
        rate = 0.31
        annual_usage = engine._calculate_annual_usage(monthly_bill, rate)
        
        expected_monthly_usage = 300.0 / 0.31
        expected_annual_usage = int(expected_monthly_usage * 12)
        
        assert annual_usage == expected_annual_usage
        assert annual_usage > 10000  # Should be substantial usage
    
    def test_calculate_optimal_system_size(self, engine):
        """Test optimal system size calculation"""
        annual_usage = 12000  # kWh
        solar_irradiance = 1300  # kWh/kW
        shading_factor = 0.85
        
        system_size = engine._calculate_optimal_system_size(
            annual_usage, solar_irradiance, shading_factor
        )
        
        # Should be reasonable system size
        assert 3.0 <= system_size <= 15.0
        assert system_size > 5.0  # Should be substantial for 12,000 kWh usage
    
    def test_calculate_panel_configuration(self, engine):
        """Test panel configuration calculation"""
        system_size = 8.0  # kW
        roof_type = "asphalt"
        
        config = engine._calculate_panel_configuration(system_size, roof_type, None)
        
        assert config["panel_count"] > 0
        assert config["panel_type"] == "standard"  # Should choose standard for asphalt
        assert config["roof_area_required"] > 0
        assert config["string_count"] > 0
    
    def test_calculate_panel_configuration_flat_roof(self, engine):
        """Test panel configuration for flat roof"""
        system_size = 6.0  # kW
        roof_type = "flat"
        
        config = engine._calculate_panel_configuration(system_size, roof_type, None)
        
        assert config["panel_type"] == "premium"  # Should choose premium for flat roof
        assert config["panel_count"] > 0
    
    def test_calculate_annual_production(self, engine):
        """Test annual production calculation"""
        system_size = 8.0  # kW
        solar_irradiance = 1300  # kWh/kW
        shading_factor = 0.85
        
        production = engine._calculate_annual_production(
            system_size, solar_irradiance, shading_factor
        )
        
        expected = int(8.0 * 1300 * 0.85)
        assert production == expected
        assert production > 8000  # Should be substantial production
    
    def test_calculate_cost_analysis(self, engine):
        """Test cost analysis calculation"""
        system_size = 8.0  # kW
        params = NYCSolarParameters(
            utility_territory=UtilityTerritory.CON_EDISON,
            electric_rate_per_kwh=0.31,
            solar_irradiance=1300,
            average_system_cost_per_watt=3.75,
            federal_itc_rate=0.30,
            nyserda_rebate_per_kw=400,
            property_tax_abatement_rate=0.30,
            net_metering_credit=1.0,
            system_lifetime_years=25,
            degradation_rate=0.005,
            inflation_rate=0.03
        )
        
        costs = engine._calculate_cost_analysis(system_size, params)
        
        # Gross cost should be system size * 1000 * cost per watt
        expected_gross = 8.0 * 1000 * 3.75
        assert costs["gross_cost"] == expected_gross
        
        # Federal credit should be 30% of gross
        assert costs["federal_credit"] == expected_gross * 0.30
        
        # NYSERDA rebate should be $400/kW, max $3,000
        expected_nyserda = min(8.0 * 400, 3000)
        assert costs["nyserda_rebate"] == expected_nyserda
        
        # Net cost should be positive
        assert costs["net_cost"] > 0
        assert costs["net_cost"] < costs["gross_cost"]  # Should be less than gross
    
    def test_calculate_savings_analysis(self, engine):
        """Test savings analysis calculation"""
        annual_production = 10000  # kWh
        annual_usage = 12000  # kWh
        electric_rate = 0.31
        net_cost = 15000  # $
        
        params = NYCSolarParameters(
            utility_territory=UtilityTerritory.CON_EDISON,
            electric_rate_per_kwh=0.31,
            solar_irradiance=1300,
            average_system_cost_per_watt=3.75,
            federal_itc_rate=0.30,
            nyserda_rebate_per_kw=400,
            property_tax_abatement_rate=0.30,
            net_metering_credit=1.0,
            system_lifetime_years=25,
            degradation_rate=0.005,
            inflation_rate=0.03
        )
        
        savings = engine._calculate_savings_analysis(
            annual_production, annual_usage, electric_rate, net_cost, params
        )
        
        # Annual savings should be production * rate (capped at usage)
        expected_annual = min(10000, 12000) * 0.31
        assert savings["annual_savings"] == expected_annual
        
        # Monthly savings should be annual / 12
        assert savings["monthly_savings"] == expected_annual / 12
        
        # Payback should be net cost / annual savings
        expected_payback = 15000 / expected_annual
        assert abs(savings["payback_years"] - expected_payback) < 0.1
        
        # Lifetime savings should be positive
        assert savings["lifetime_savings"] > 0
        assert savings["roi_percentage"] > 0
    
    def test_assess_roof_requirements(self, engine):
        """Test roof requirements assessment"""
        panel_config = {
            "roof_area_required": 500.0,
            "panel_count": 20
        }
        roof_type = "asphalt"
        home_type = "single_family"
        
        requirements = engine._assess_roof_requirements(panel_config, roof_type, home_type)
        
        assert requirements["roof_area_required"] == 500.0
        assert requirements["panel_count"] == 20
        assert "structural_considerations" in requirements
        assert "permit_requirements" in requirements
        assert requirements["installation_complexity"] == "standard"
    
    def test_assess_roof_requirements_complex(self, engine):
        """Test roof requirements for complex roof"""
        panel_config = {
            "roof_area_required": 600.0,
            "panel_count": 25
        }
        roof_type = "complex"
        home_type = "condo"
        
        requirements = engine._assess_roof_requirements(panel_config, roof_type, home_type)
        
        assert requirements["installation_complexity"] == "high"
        assert "Engineering assessment needed" in requirements["structural_considerations"]
        assert "Board approval required" in requirements["structural_considerations"]
    
    def test_generate_financing_options(self, engine):
        """Test financing options generation"""
        net_cost = 20000.0
        
        options = engine._generate_financing_options(net_cost)
        
        assert len(options) > 0
        
        # Should have cash option
        cash_option = next((opt for opt in options if opt["type"] == "cash"), None)
        assert cash_option is not None
        assert cash_option["down_payment"] == net_cost
        assert cash_option["monthly_payment"] == 0
        
        # Should have loan options
        loan_options = [opt for opt in options if opt["type"] == "loan"]
        assert len(loan_options) > 0
        
        # All loan options should have positive monthly payments
        for loan in loan_options:
            assert loan["monthly_payment"] > 0
            assert loan["total_cost"] > net_cost  # Should include interest
    
    def test_calculate_confidence_score(self, engine):
        """Test confidence score calculation"""
        # High confidence scenario
        score1 = engine._calculate_confidence_score(300, "10001", "asphalt", 1000)
        assert 0.5 <= score1 <= 1.0
        
        # Low confidence scenario
        score2 = engine._calculate_confidence_score(50, "invalid", None, None)
        assert 0.5 <= score2 <= 1.0
        assert score2 < score1  # Should be lower confidence
    
    @pytest.mark.asyncio
    async def test_calculate_solar_recommendation_basic(self, engine):
        """Test basic solar recommendation calculation"""
        with patch.object(engine, '_get_cached_calculation', return_value=None):
            with patch.object(engine, '_cache_calculation'):
                with patch.object(engine, '_store_calculation_result'):
                    recommendation = await engine.calculate_solar_recommendation(
                        monthly_bill=300.0,
                        zip_code="10001",
                        borough="manhattan",
                        roof_type="asphalt"
                    )
                    
                    assert isinstance(recommendation, SolarSystemRecommendation)
                    assert recommendation.system_size_kw > 0
                    assert recommendation.panel_count > 0
                    assert recommendation.monthly_savings > 0
                    assert recommendation.net_cost > 0
                    assert recommendation.payback_years > 0
                    assert recommendation.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_calculate_solar_recommendation_with_caching(self, engine):
        """Test solar recommendation with caching"""
        # Mock cached result
        cached_recommendation = SolarSystemRecommendation(
            system_size_kw=8.0,
            panel_count=20,
            panel_type="standard",
            roof_area_required=500.0,
            annual_production_kwh=10000,
            monthly_savings=250.0,
            annual_savings=3000.0,
            gross_cost=30000.0,
            federal_credit=9000.0,
            nyserda_rebate=3200.0,
            property_tax_abatement=5400.0,
            net_cost=12400.0,
            payback_years=4.1,
            lifetime_savings=75000.0,
            roi_percentage=500.0,
            financing_options=[],
            roof_assessment={},
            permit_estimate={},
            installation_timeline="6-8 weeks",
            confidence_score=0.9,
            calculation_timestamp=datetime.utcnow()
        )
        
        with patch.object(engine, '_get_cached_calculation', return_value=cached_recommendation):
            recommendation = await engine.calculate_solar_recommendation(
                monthly_bill=300.0,
                zip_code="10001"
            )
            
            assert recommendation == cached_recommendation
    
    def test_generate_conversation_response(self, engine):
        """Test conversation response generation"""
        recommendation = SolarSystemRecommendation(
            system_size_kw=8.0,
            panel_count=20,
            panel_type="standard",
            roof_area_required=500.0,
            annual_production_kwh=10000,
            monthly_savings=250.0,
            annual_savings=3000.0,
            gross_cost=30000.0,
            federal_credit=9000.0,
            nyserda_rebate=3200.0,
            property_tax_abatement=5400.0,
            net_cost=12400.0,
            payback_years=4.1,
            lifetime_savings=75000.0,
            roi_percentage=500.0,
            financing_options=[{
                "type": "loan",
                "monthly_payment": 150.0,
                "description": "10-year solar loan at 4.99% APR"
            }],
            roof_assessment={},
            permit_estimate={},
            installation_timeline="6-8 weeks",
            confidence_score=0.9,
            calculation_timestamp=datetime.utcnow()
        )
        
        response = engine.generate_conversation_response(recommendation, "John")
        
        assert "8.0kW system" in response
        assert "20 panels" in response
        assert "$250" in response  # Monthly savings
        assert "4.1 years" in response  # Payback
        assert "$75,000" in response  # Lifetime savings
        assert "John" in response
    
    def test_create_fallback_recommendation(self, engine):
        """Test fallback recommendation creation"""
        recommendation = engine._create_fallback_recommendation(300.0, "10001", "Test error")
        
        assert isinstance(recommendation, SolarSystemRecommendation)
        assert recommendation.system_size_kw == 6.0  # Fallback size
        assert recommendation.panel_count == 15  # Fallback panel count
        assert recommendation.confidence_score == 0.3  # Low confidence for fallback


class TestNYCSolarParameters:
    """Test cases for NYC Solar Parameters"""
    
    def test_con_edison_parameters(self):
        """Test Con Edison parameters"""
        params = NYCSolarParameters(
            utility_territory=UtilityTerritory.CON_EDISON,
            electric_rate_per_kwh=0.31,
            solar_irradiance=1300,
            average_system_cost_per_watt=3.75,
            federal_itc_rate=0.30,
            nyserda_rebate_per_kw=400,
            property_tax_abatement_rate=0.30,
            net_metering_credit=1.0,
            system_lifetime_years=25,
            degradation_rate=0.005,
            inflation_rate=0.03
        )
        
        assert params.electric_rate_per_kwh == 0.31
        assert params.solar_irradiance == 1300
        assert params.average_system_cost_per_watt == 3.75
        assert params.federal_itc_rate == 0.30
        assert params.nyserda_rebate_per_kw == 400
    
    def test_pseg_parameters(self):
        """Test PSEG parameters"""
        params = NYCSolarParameters(
            utility_territory=UtilityTerritory.PSEG,
            electric_rate_per_kwh=0.27,
            solar_irradiance=1250,
            average_system_cost_per_watt=3.50,
            federal_itc_rate=0.30,
            nyserda_rebate_per_kw=400,
            property_tax_abatement_rate=0.30,
            net_metering_credit=1.0,
            system_lifetime_years=25,
            degradation_rate=0.005,
            inflation_rate=0.03
        )
        
        assert params.electric_rate_per_kwh == 0.27
        assert params.solar_irradiance == 1250
        assert params.average_system_cost_per_watt == 3.50


if __name__ == "__main__":
    pytest.main([__file__])

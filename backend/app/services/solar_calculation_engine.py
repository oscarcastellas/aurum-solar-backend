"""
Solar Calculation Engine for NYC Solar Lead Generation
Provides real technical recommendations during AI conversations
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.lead import Lead
from app.models.ai_models import AICalculation, AICalculationResult


class UtilityTerritory(Enum):
    """NYC utility territories with different rates"""
    CON_EDISON = "con_edison"  # Manhattan, Bronx, Westchester
    PSEG = "pseg"  # Queens, Staten Island, Long Island


class RoofType(Enum):
    """NYC roof types with different installation considerations"""
    FLAT = "flat"
    SLOPED_ASPHALT = "sloped_asphalt"
    SLOPED_METAL = "sloped_metal"
    TILE = "tile"
    COMPLEX = "complex"  # Mixed materials, historic, etc.


class SystemSize(Enum):
    """System size categories for NYC residential"""
    SMALL = "small"  # 3-5kW
    MEDIUM = "medium"  # 6-10kW
    LARGE = "large"  # 11-15kW


@dataclass
class SolarSystemRecommendation:
    """Complete solar system recommendation"""
    system_size_kw: float
    panel_count: int
    panel_type: str
    roof_area_required: float
    annual_production_kwh: int
    monthly_savings: float
    annual_savings: float
    gross_cost: float
    federal_credit: float
    nyserda_rebate: float
    property_tax_abatement: float
    net_cost: float
    payback_years: float
    lifetime_savings: float
    roi_percentage: float
    financing_options: List[Dict[str, Any]]
    roof_assessment: Dict[str, Any]
    permit_estimate: Dict[str, Any]
    installation_timeline: str
    confidence_score: float
    calculation_timestamp: datetime


@dataclass
class NYCSolarParameters:
    """NYC-specific solar calculation parameters"""
    utility_territory: UtilityTerritory
    electric_rate_per_kwh: float
    solar_irradiance: float  # kWh/kW annually
    average_system_cost_per_watt: float
    federal_itc_rate: float
    nyserda_rebate_per_kw: float
    property_tax_abatement_rate: float
    net_metering_credit: float
    system_lifetime_years: int
    degradation_rate: float
    inflation_rate: float


class SolarCalculationEngine:
    """Comprehensive solar calculation engine for NYC market"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        
        # NYC market parameters by utility territory
        self.nyc_parameters = {
            UtilityTerritory.CON_EDISON: NYCSolarParameters(
                utility_territory=UtilityTerritory.CON_EDISON,
                electric_rate_per_kwh=0.31,
                solar_irradiance=1300,  # Higher in Manhattan/Bronx
                average_system_cost_per_watt=3.75,  # Higher due to complexity
                federal_itc_rate=0.30,
                nyserda_rebate_per_kw=400,
                property_tax_abatement_rate=0.30,
                net_metering_credit=1.0,
                system_lifetime_years=25,
                degradation_rate=0.005,  # 0.5% per year
                inflation_rate=0.03
            ),
            UtilityTerritory.PSEG: NYCSolarParameters(
                utility_territory=UtilityTerritory.PSEG,
                electric_rate_per_kwh=0.27,
                solar_irradiance=1250,  # Slightly lower in outer boroughs
                average_system_cost_per_watt=3.50,
                federal_itc_rate=0.30,
                nyserda_rebate_per_kw=400,
                property_tax_abatement_rate=0.30,
                net_metering_credit=1.0,
                system_lifetime_years=25,
                degradation_rate=0.005,
                inflation_rate=0.03
            )
        }
        
        # Panel specifications
        self.panel_specs = {
            "standard": {
                "power_watts": 400,
                "efficiency": 0.20,
                "dimensions": {"length": 1.95, "width": 1.10},  # meters
                "cost_per_watt": 0.85
            },
            "premium": {
                "power_watts": 450,
                "efficiency": 0.22,
                "dimensions": {"length": 2.00, "width": 1.10},
                "cost_per_watt": 1.00
            }
        }
        
        # NYC borough-specific adjustments
        self.borough_adjustments = {
            "manhattan": {"irradiance_multiplier": 1.05, "cost_multiplier": 1.15},
            "brooklyn": {"irradiance_multiplier": 1.02, "cost_multiplier": 1.05},
            "queens": {"irradiance_multiplier": 1.00, "cost_multiplier": 1.00},
            "bronx": {"irradiance_multiplier": 1.03, "cost_multiplier": 1.08},
            "staten_island": {"irradiance_multiplier": 0.98, "cost_multiplier": 0.95}
        }
    
    async def calculate_solar_recommendation(
        self,
        monthly_bill: float,
        zip_code: str,
        borough: Optional[str] = None,
        roof_type: Optional[str] = None,
        roof_size: Optional[float] = None,
        shading_factor: Optional[float] = None,
        home_type: Optional[str] = None
    ) -> SolarSystemRecommendation:
        """Calculate comprehensive solar system recommendation"""
        
        try:
            # Check cache first
            cache_key = f"solar_calc:{zip_code}:{monthly_bill}:{roof_type or 'unknown'}"
            cached_result = await self._get_cached_calculation(cache_key)
            if cached_result:
                return cached_result
            
            # Determine utility territory
            utility_territory = self._determine_utility_territory(zip_code, borough)
            params = self.nyc_parameters[utility_territory]
            
            # Apply borough adjustments
            if borough and borough.lower() in self.borough_adjustments:
                adjustments = self.borough_adjustments[borough.lower()]
                params.solar_irradiance *= adjustments["irradiance_multiplier"]
                params.average_system_cost_per_watt *= adjustments["cost_multiplier"]
            
            # Calculate annual usage
            annual_usage_kwh = self._calculate_annual_usage(monthly_bill, params.electric_rate_per_kwh)
            
            # Determine optimal system size
            system_size_kw = self._calculate_optimal_system_size(
                annual_usage_kwh, 
                params.solar_irradiance,
                shading_factor or 0.85  # Default 15% shading loss
            )
            
            # Calculate panel configuration
            panel_config = self._calculate_panel_configuration(
                system_size_kw, 
                roof_type, 
                roof_size
            )
            
            # Calculate production
            annual_production = self._calculate_annual_production(
                system_size_kw, 
                params.solar_irradiance,
                shading_factor or 0.85
            )
            
            # Calculate costs and incentives
            cost_analysis = self._calculate_cost_analysis(system_size_kw, params)
            
            # Calculate savings and ROI
            savings_analysis = self._calculate_savings_analysis(
                annual_production,
                annual_usage_kwh,
                params.electric_rate_per_kwh,
                cost_analysis["net_cost"],
                params
            )
            
            # Assess roof requirements
            roof_assessment = self._assess_roof_requirements(
                panel_config, 
                roof_type, 
                home_type
            )
            
            # Estimate permits and timeline
            permit_estimate = self._estimate_permits_and_timeline(zip_code, borough)
            
            # Generate financing options
            financing_options = self._generate_financing_options(cost_analysis["net_cost"])
            
            # Create recommendation
            recommendation = SolarSystemRecommendation(
                system_size_kw=system_size_kw,
                panel_count=panel_config["panel_count"],
                panel_type=panel_config["panel_type"],
                roof_area_required=panel_config["roof_area_required"],
                annual_production_kwh=annual_production,
                monthly_savings=savings_analysis["monthly_savings"],
                annual_savings=savings_analysis["annual_savings"],
                gross_cost=cost_analysis["gross_cost"],
                federal_credit=cost_analysis["federal_credit"],
                nyserda_rebate=cost_analysis["nyserda_rebate"],
                property_tax_abatement=cost_analysis["property_tax_abatement"],
                net_cost=cost_analysis["net_cost"],
                payback_years=savings_analysis["payback_years"],
                lifetime_savings=savings_analysis["lifetime_savings"],
                roi_percentage=savings_analysis["roi_percentage"],
                financing_options=financing_options,
                roof_assessment=roof_assessment,
                permit_estimate=permit_estimate,
                installation_timeline=self._estimate_installation_timeline(),
                confidence_score=self._calculate_confidence_score(
                    monthly_bill, zip_code, roof_type, roof_size
                ),
                calculation_timestamp=datetime.utcnow()
            )
            
            # Cache the result
            await self._cache_calculation(cache_key, recommendation)
            
            # Store in database
            await self._store_calculation_result(recommendation, zip_code, monthly_bill)
            
            return recommendation
            
        except Exception as e:
            # Return fallback recommendation
            return self._create_fallback_recommendation(monthly_bill, zip_code, str(e))
    
    def _determine_utility_territory(self, zip_code: str, borough: Optional[str]) -> UtilityTerritory:
        """Determine utility territory based on ZIP code and borough"""
        
        # Con Edison territories (Manhattan, Bronx, Westchester)
        con_edison_zips = [
            "10001", "10002", "10003", "10004", "10005", "10006", "10007", "10008", "10009", "10010",
            "10011", "10012", "10013", "10014", "10015", "10016", "10017", "10018", "10019", "10020",
            "10021", "10022", "10023", "10024", "10025", "10026", "10027", "10028", "10029", "10030",
            "10031", "10032", "10033", "10034", "10035", "10036", "10037", "10038", "10039", "10040",
            "10041", "10043", "10044", "10045", "10048", "10055", "10060", "10065", "10069", "10075",
            "10080", "10081", "10082", "10087", "10090", "10095", "10101", "10102", "10103", "10104",
            "10105", "10106", "10107", "10108", "10109", "10110", "10111", "10112", "10113", "10114",
            "10115", "10116", "10117", "10118", "10119", "10120", "10121", "10122", "10123", "10124",
            "10125", "10126", "10128", "10129", "10130", "10131", "10132", "10133", "10138", "10150",
            "10151", "10152", "10153", "10154", "10155", "10156", "10157", "10158", "10159", "10160",
            "10161", "10162", "10163", "10164", "10165", "10166", "10167", "10168", "10169", "10170",
            "10171", "10172", "10173", "10174", "10175", "10176", "10177", "10178", "10179", "10185",
            "10199", "10270", "10271", "10278", "10279", "10280", "10281", "10282", "10285", "10286",
            "10292", "10301", "10302", "10303", "10304", "10305", "10306", "10307", "10308", "10309",
            "10310", "10311", "10312", "10313", "10314", "10451", "10452", "10453", "10454", "10455",
            "10456", "10457", "10458", "10459", "10460", "10461", "10462", "10463", "10464", "10465",
            "10466", "10467", "10468", "10469", "10470", "10471", "10472", "10473", "10474", "10475"
        ]
        
        if zip_code in con_edison_zips or (borough and borough.lower() in ["manhattan", "bronx"]):
            return UtilityTerritory.CON_EDISON
        else:
            return UtilityTerritory.PSEG
    
    def _calculate_annual_usage(self, monthly_bill: float, rate_per_kwh: float) -> int:
        """Calculate annual kWh usage from monthly bill"""
        monthly_usage = monthly_bill / rate_per_kwh
        return int(monthly_usage * 12)
    
    def _calculate_optimal_system_size(
        self, 
        annual_usage_kwh: int, 
        solar_irradiance: float, 
        shading_factor: float
    ) -> float:
        """Calculate optimal system size based on usage and production"""
        
        # Target 80-90% offset for optimal economics
        target_offset = 0.85
        
        # Calculate required production
        required_production = annual_usage_kwh * target_offset
        
        # Calculate system size needed
        system_size = required_production / (solar_irradiance * shading_factor)
        
        # Round to nearest 0.1kW and constrain to NYC residential limits
        system_size = round(system_size, 1)
        system_size = max(3.0, min(15.0, system_size))  # 3-15kW range
        
        return system_size
    
    def _calculate_panel_configuration(
        self, 
        system_size_kw: float, 
        roof_type: Optional[str], 
        roof_size: Optional[float]
    ) -> Dict[str, Any]:
        """Calculate panel configuration based on system size and roof constraints"""
        
        # Choose panel type based on roof type
        if roof_type == "flat":
            panel_type = "premium"  # Better for flat roof mounting
        else:
            panel_type = "standard"  # Standard for sloped roofs
        
        panel_spec = self.panel_specs[panel_type]
        panel_count = int(system_size_kw * 1000 / panel_spec["power_watts"])
        
        # Calculate roof area required
        panel_area_sqft = panel_count * (panel_spec["dimensions"]["length"] * panel_spec["dimensions"]["width"] * 10.764)
        
        # Add 20% for spacing and access
        roof_area_required = panel_area_sqft * 1.2
        
        return {
            "panel_count": panel_count,
            "panel_type": panel_type,
            "panel_area_sqft": panel_area_sqft,
            "roof_area_required": roof_area_required,
            "panels_per_string": min(12, panel_count),  # Typical string size
            "string_count": math.ceil(panel_count / 12)
        }
    
    def _calculate_annual_production(
        self, 
        system_size_kw: float, 
        solar_irradiance: float, 
        shading_factor: float
    ) -> int:
        """Calculate annual kWh production"""
        production = system_size_kw * solar_irradiance * shading_factor
        return int(production)
    
    def _calculate_cost_analysis(self, system_size_kw: float, params: NYCSolarParameters) -> Dict[str, float]:
        """Calculate all costs and incentives"""
        
        # Gross system cost
        gross_cost = system_size_kw * 1000 * params.average_system_cost_per_watt
        
        # Federal Investment Tax Credit (30%)
        federal_credit = gross_cost * params.federal_itc_rate
        
        # NYSERDA rebate ($400/kW, max $3,000)
        nyserda_rebate = min(system_size_kw * params.nyserda_rebate_per_kw, 3000)
        
        # Cost after federal credit and NYSERDA rebate
        cost_after_rebates = gross_cost - federal_credit - nyserda_rebate
        
        # NYC Property Tax Abatement (30% over 4 years)
        property_tax_abatement = cost_after_rebates * params.property_tax_abatement_rate
        
        # Net cost to customer
        net_cost = cost_after_rebates - property_tax_abatement
        
        return {
            "gross_cost": gross_cost,
            "federal_credit": federal_credit,
            "nyserda_rebate": nyserda_rebate,
            "property_tax_abatement": property_tax_abatement,
            "net_cost": max(0, net_cost)  # Ensure non-negative
        }
    
    def _calculate_savings_analysis(
        self,
        annual_production: int,
        annual_usage: int,
        electric_rate: float,
        net_cost: float,
        params: NYCSolarParameters
    ) -> Dict[str, float]:
        """Calculate savings and ROI analysis"""
        
        # Calculate annual savings (production * rate, capped at usage)
        annual_savings = min(annual_production, annual_usage) * electric_rate
        monthly_savings = annual_savings / 12
        
        # Calculate payback period
        payback_years = net_cost / annual_savings if annual_savings > 0 else 999
        
        # Calculate 25-year lifetime savings
        total_production = 0
        total_savings = 0
        
        for year in range(params.system_lifetime_years):
            # Apply degradation
            year_production = annual_production * (1 - params.degradation_rate) ** year
            year_savings = min(year_production, annual_usage) * electric_rate * (1 + params.inflation_rate) ** year
            total_savings += year_savings
        
        lifetime_savings = total_savings - net_cost
        roi_percentage = (lifetime_savings / net_cost * 100) if net_cost > 0 else 0
        
        return {
            "monthly_savings": monthly_savings,
            "annual_savings": annual_savings,
            "payback_years": payback_years,
            "lifetime_savings": lifetime_savings,
            "roi_percentage": roi_percentage
        }
    
    def _assess_roof_requirements(
        self, 
        panel_config: Dict[str, Any], 
        roof_type: Optional[str], 
        home_type: Optional[str]
    ) -> Dict[str, Any]:
        """Assess roof requirements and constraints"""
        
        requirements = {
            "roof_area_required": panel_config["roof_area_required"],
            "panel_count": panel_config["panel_count"],
            "structural_considerations": [],
            "permit_requirements": [],
            "installation_complexity": "standard"
        }
        
        # Add structural considerations based on roof type
        if roof_type == "flat":
            requirements["structural_considerations"].append("Ballasted mounting system required")
            requirements["structural_considerations"].append("Waterproofing inspection needed")
            requirements["installation_complexity"] = "moderate"
        elif roof_type == "tile":
            requirements["structural_considerations"].append("Tile replacement may be needed")
            requirements["structural_considerations"].append("Special mounting hardware required")
            requirements["installation_complexity"] = "high"
        elif roof_type == "complex":
            requirements["structural_considerations"].append("Custom mounting solution required")
            requirements["structural_considerations"].append("Engineering assessment needed")
            requirements["installation_complexity"] = "high"
        
        # Add permit requirements
        requirements["permit_requirements"] = [
            "NYC DOB electrical permit",
            "NYC DOB construction permit",
            "Con Edison interconnection application",
            "NYSERDA incentive application"
        ]
        
        # Add home type considerations
        if home_type == "condo":
            requirements["structural_considerations"].append("Board approval required")
            requirements["permit_requirements"].append("Co-op/condo board approval")
        
        return requirements
    
    def _estimate_permits_and_timeline(self, zip_code: str, borough: Optional[str]) -> Dict[str, Any]:
        """Estimate permit requirements and timeline"""
        
        # Base timeline
        timeline = {
            "permit_approval": "4-6 weeks",
            "installation": "1-2 days",
            "inspection": "1-2 weeks",
            "interconnection": "2-4 weeks",
            "total_timeline": "8-12 weeks"
        }
        
        # Adjust based on borough complexity
        if borough and borough.lower() == "manhattan":
            timeline["permit_approval"] = "6-8 weeks"
            timeline["total_timeline"] = "10-14 weeks"
        
        return {
            "timeline": timeline,
            "permit_costs": {
                "electrical_permit": 200,
                "construction_permit": 300,
                "inspection_fees": 150,
                "total_permit_costs": 650
            },
            "required_documents": [
                "Property deed",
                "Electrical panel photo",
                "Roof photos",
                "Site survey",
                "Engineering drawings"
            ]
        }
    
    def _generate_financing_options(self, net_cost: float) -> List[Dict[str, Any]]:
        """Generate financing options for the customer"""
        
        options = []
        
        # Cash purchase
        options.append({
            "type": "cash",
            "down_payment": net_cost,
            "monthly_payment": 0,
            "total_cost": net_cost,
            "apr": 0,
            "term_months": 0,
            "description": "Full cash payment - best long-term value"
        })
        
        # Solar loan options
        loan_terms = [
            {"term": 10, "apr": 0.0499, "min_credit": 700},
            {"term": 15, "apr": 0.0599, "min_credit": 680},
            {"term": 20, "apr": 0.0699, "min_credit": 650}
        ]
        
        for loan in loan_terms:
            monthly_rate = loan["apr"] / 12
            monthly_payment = net_cost * (monthly_rate * (1 + monthly_rate) ** loan["term"]) / ((1 + monthly_rate) ** loan["term"] - 1)
            total_cost = monthly_payment * loan["term"] * 12
            
            options.append({
                "type": "loan",
                "down_payment": 0,
                "monthly_payment": monthly_payment,
                "total_cost": total_cost,
                "apr": loan["apr"],
                "term_months": loan["term"] * 12,
                "min_credit_score": loan["min_credit"],
                "description": f"{loan['term']}-year solar loan at {loan['apr']:.2%} APR"
            })
        
        # Lease option (if available)
        if net_cost > 10000:  # Only for larger systems
            lease_payment = net_cost * 0.08 / 12  # 8% annual rate
            options.append({
                "type": "lease",
                "down_payment": 0,
                "monthly_payment": lease_payment,
                "total_cost": lease_payment * 20 * 12,  # 20-year lease
                "apr": 0.08,
                "term_months": 240,
                "description": "20-year solar lease - no upfront cost"
            })
        
        return options
    
    def _estimate_installation_timeline(self) -> str:
        """Estimate installation timeline"""
        return "6-8 weeks from contract signing to system activation"
    
    def _calculate_confidence_score(
        self, 
        monthly_bill: float, 
        zip_code: str, 
        roof_type: Optional[str], 
        roof_size: Optional[float]
    ) -> float:
        """Calculate confidence score for the recommendation"""
        
        score = 0.5  # Base score
        
        # Bill amount confidence
        if 100 <= monthly_bill <= 500:
            score += 0.2
        elif 50 <= monthly_bill <= 1000:
            score += 0.1
        
        # ZIP code confidence
        if len(zip_code) == 5 and zip_code.isdigit():
            score += 0.1
        
        # Roof type confidence
        if roof_type:
            score += 0.1
        
        # Roof size confidence
        if roof_size and roof_size > 500:  # sqft
            score += 0.1
        
        return min(1.0, score)
    
    async def _get_cached_calculation(self, cache_key: str) -> Optional[SolarSystemRecommendation]:
        """Get cached calculation result"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Convert back to SolarSystemRecommendation object
                return SolarSystemRecommendation(**data)
        except Exception:
            pass
        return None
    
    async def _cache_calculation(self, cache_key: str, recommendation: SolarSystemRecommendation):
        """Cache calculation result"""
        try:
            # Convert to dict for JSON serialization
            data = {
                "system_size_kw": recommendation.system_size_kw,
                "panel_count": recommendation.panel_count,
                "panel_type": recommendation.panel_type,
                "roof_area_required": recommendation.roof_area_required,
                "annual_production_kwh": recommendation.annual_production_kwh,
                "monthly_savings": recommendation.monthly_savings,
                "annual_savings": recommendation.annual_savings,
                "gross_cost": recommendation.gross_cost,
                "federal_credit": recommendation.federal_credit,
                "nyserda_rebate": recommendation.nyserda_rebate,
                "property_tax_abatement": recommendation.property_tax_abatement,
                "net_cost": recommendation.net_cost,
                "payback_years": recommendation.payback_years,
                "lifetime_savings": recommendation.lifetime_savings,
                "roi_percentage": recommendation.roi_percentage,
                "financing_options": recommendation.financing_options,
                "roof_assessment": recommendation.roof_assessment,
                "permit_estimate": recommendation.permit_estimate,
                "installation_timeline": recommendation.installation_timeline,
                "confidence_score": recommendation.confidence_score,
                "calculation_timestamp": recommendation.calculation_timestamp.isoformat()
            }
            
            self.redis_client.setex(cache_key, 3600, json.dumps(data))  # 1 hour cache
        except Exception:
            pass
    
    async def _store_calculation_result(
        self, 
        recommendation: SolarSystemRecommendation, 
        zip_code: str, 
        monthly_bill: float
    ):
        """Store calculation result in database"""
        try:
            calculation = AICalculation(
                calculation_type="solar_recommendation",
                input_data={
                    "zip_code": zip_code,
                    "monthly_bill": monthly_bill,
                    "calculation_timestamp": recommendation.calculation_timestamp.isoformat()
                },
                result_data={
                    "system_size_kw": recommendation.system_size_kw,
                    "panel_count": recommendation.panel_count,
                    "annual_production_kwh": recommendation.annual_production_kwh,
                    "monthly_savings": recommendation.monthly_savings,
                    "net_cost": recommendation.net_cost,
                    "payback_years": recommendation.payback_years,
                    "lifetime_savings": recommendation.lifetime_savings,
                    "confidence_score": recommendation.confidence_score
                },
                confidence_score=recommendation.confidence_score,
                processing_time_ms=0,  # Calculate actual processing time
                ai_model_used="solar_calculation_engine_v1"
            )
            
            self.db.add(calculation)
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing calculation result: {e}")
            self.db.rollback()
    
    def _create_fallback_recommendation(
        self, 
        monthly_bill: float, 
        zip_code: str, 
        error: str
    ) -> SolarSystemRecommendation:
        """Create fallback recommendation when calculation fails"""
        
        # Use conservative estimates
        system_size = 6.0  # kW
        panel_count = 15
        
        return SolarSystemRecommendation(
            system_size_kw=system_size,
            panel_count=panel_count,
            panel_type="standard",
            roof_area_required=400.0,
            annual_production_kwh=7800,
            monthly_savings=monthly_bill * 0.7,
            annual_savings=monthly_bill * 0.7 * 12,
            gross_cost=system_size * 1000 * 3.50,
            federal_credit=system_size * 1000 * 3.50 * 0.30,
            nyserda_rebate=min(system_size * 400, 3000),
            property_tax_abatement=0,
            net_cost=system_size * 1000 * 2.50,
            payback_years=8.0,
            lifetime_savings=25000.0,
            roi_percentage=300.0,
            financing_options=[],
            roof_assessment={"error": "Calculation failed", "fallback": True},
            permit_estimate={"error": "Estimate unavailable"},
            installation_timeline="8-10 weeks",
            confidence_score=0.3,
            calculation_timestamp=datetime.utcnow()
        )
    
    def generate_conversation_response(
        self, 
        recommendation: SolarSystemRecommendation, 
        customer_name: str = "there",
        monthly_bill: float = None,
        borough: str = None
    ) -> str:
        """Generate natural language response for the AI agent"""
        
        # Format numbers for display
        system_size = f"{recommendation.system_size_kw:.1f}"
        monthly_savings = f"${recommendation.monthly_savings:.0f}"
        annual_savings = f"${recommendation.annual_savings:.0f}"
        net_cost = f"${recommendation.net_cost:,.0f}"
        payback = f"{recommendation.payback_years:.1f}"
        lifetime_savings = f"${recommendation.lifetime_savings:,.0f}"
        
        # Choose best financing option
        best_financing = min(recommendation.financing_options, key=lambda x: x.get("total_cost", float('inf')))
        
        # Build personalized response
        if monthly_bill:
            usage_coverage = (recommendation.annual_production_kwh / (monthly_bill * 12 / 0.30)) * 100
            bill_context = f"your ${monthly_bill:.0f} monthly electric bill"
        else:
            usage_coverage = 85  # Default estimate
            bill_context = "your electric usage"
        
        # Add NYC-specific context
        nyc_context = ""
        if borough:
            if borough.lower() in ["manhattan", "brooklyn"]:
                nyc_context = f" In {borough}, with Con Edison's high rates, solar is particularly valuable."
            elif borough.lower() in ["queens", "staten island"]:
                nyc_context = f" In {borough}, PSEG's rates make solar a smart investment."
        
        # Build response
        response = f"""Based on {bill_context}, I'd recommend a {system_size}kW system with {recommendation.panel_count} panels.{nyc_context}

With current incentives, your net cost would be around {net_cost} after the 30% federal tax credit and NYSERDA rebate. You'd save about {monthly_savings}/month and pay off the system in {payback} years, then enjoy free electricity for the next 19+ years. That's over {lifetime_savings} in lifetime savings!

The system would produce about {recommendation.annual_production_kwh:,} kWh annually, covering about {usage_coverage:.0f}% of your current usage.

{best_financing['description']} with a monthly payment of ${best_financing['monthly_payment']:.0f}."""

        return response

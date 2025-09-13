"""
NYC Market Intelligence Service
Real-time integration with NYC market data for personalized solar conversations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.nyc_data import NYCZipCode, NYCIncentive, NYCDemographic, NYCElectricRate
from app.core.config import settings


class NYCMarketService:
    """Service for NYC market intelligence and personalization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    async def get_zip_code_data(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive NYC market data for a zip code"""
        
        # Check cache first
        cache_key = f"nyc_data_{zip_code}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        try:
            # Get zip code data
            zip_data = self.db.query(NYCZipCode).filter(
                NYCZipCode.zip_code == zip_code
            ).first()
            
            if not zip_data:
                return None
            
            # Get incentives
            incentives = self.db.query(NYCIncentive).filter(
                NYCIncentive.zip_code_id == zip_data.id,
                NYCIncentive.is_active == True
            ).all()
            
            # Get demographics
            demographics = self.db.query(NYCDemographic).filter(
                NYCDemographic.zip_code_id == zip_data.id
            ).first()
            
            # Get electric rates
            electric_rates = self.db.query(NYCElectricRate).filter(
                NYCElectricRate.zip_code_id == zip_data.id
            ).first()
            
            # Compile comprehensive data
            market_data = {
                # Basic info
                "zip_code": zip_data.zip_code,
                "borough": zip_data.borough,
                "neighborhood": zip_data.neighborhood,
                
                # Demographics
                "total_population": zip_data.total_population,
                "median_household_income": zip_data.median_household_income,
                "homeownership_rate": zip_data.homeownership_rate,
                "average_home_value": zip_data.average_home_value,
                
                # Solar market
                "solar_adoption_rate": zip_data.solar_adoption_rate,
                "total_solar_installations": zip_data.total_solar_installations,
                "average_system_size_kw": zip_data.average_system_size_kw,
                "average_installation_cost": zip_data.average_installation_cost,
                "average_savings_per_month": zip_data.average_savings_per_month,
                "average_payback_period_years": zip_data.average_payback_period_years,
                
                # Electric utility
                "primary_electric_provider": zip_data.primary_electric_provider,
                "average_electric_rate_per_kwh": zip_data.average_electric_rate_per_kwh,
                "average_monthly_bill": zip_data.average_monthly_bill,
                
                # Solar potential
                "solar_potential_score": zip_data.solar_potential_score,
                "average_roof_size_sqft": zip_data.average_roof_size_sqft,
                "average_roof_condition": zip_data.average_roof_condition,
                "shading_factor": zip_data.shading_factor,
                "roof_orientation_score": zip_data.roof_orientation_score,
                
                # Competition
                "solar_installers_count": zip_data.solar_installers_count,
                "market_saturation": zip_data.market_saturation,
                "competition_intensity": zip_data.competition_intensity,
                
                # Incentives
                "state_incentives_available": zip_data.state_incentives_available,
                "local_incentives_available": zip_data.local_incentives_available,
                "net_metering_available": zip_data.net_metering_available,
                "community_solar_available": zip_data.community_solar_available,
                
                # Lead quality indicators
                "high_value_zip_code": zip_data.high_value_zip_code,
                "conversion_rate": zip_data.conversion_rate,
                "average_lead_value": zip_data.average_lead_value,
                "lead_volume_per_month": zip_data.lead_volume_per_month,
                
                # Detailed incentives
                "incentives": [
                    {
                        "name": inc.incentive_name,
                        "type": inc.incentive_type,
                        "amount": inc.incentive_amount,
                        "percentage": inc.incentive_percentage,
                        "max_amount": inc.max_incentive_amount,
                        "is_active": inc.is_active,
                        "end_date": inc.end_date.isoformat() if inc.end_date else None
                    }
                    for inc in incentives
                ],
                
                # Detailed demographics
                "demographics": {
                    "age_distribution": demographics.age_distribution if demographics else {},
                    "education_levels": demographics.education_levels if demographics else {},
                    "employment_status": demographics.employment_status if demographics else {},
                    "poverty_rate": demographics.poverty_rate if demographics else 0,
                    "unemployment_rate": demographics.unemployment_rate if demographics else 0,
                    "environmental_concern_score": demographics.environmental_concern_score if demographics else 0,
                    "green_energy_adoption_rate": demographics.green_energy_adoption_rate if demographics else 0
                } if demographics else {},
                
                # Electric rates detail
                "electric_rates": {
                    "base_rate_per_kwh": electric_rates.base_rate_per_kwh if electric_rates else 0,
                    "delivery_charge_per_kwh": electric_rates.delivery_charge_per_kwh if electric_rates else 0,
                    "total_rate_per_kwh": electric_rates.total_rate_per_kwh if electric_rates else 0,
                    "peak_rate_per_kwh": electric_rates.peak_rate_per_kwh if electric_rates else 0,
                    "off_peak_rate_per_kwh": electric_rates.off_peak_rate_per_kwh if electric_rates else 0,
                    "net_metering_rate": electric_rates.net_metering_rate if electric_rates else 0,
                    "solar_credit_rate": electric_rates.solar_credit_rate if electric_rates else 0
                } if electric_rates else {},
                
                # Data freshness
                "last_updated": zip_data.last_updated.isoformat() if zip_data.last_updated else None,
                "data_confidence": zip_data.data_confidence or 0.8
            }
            
            # Cache the data
            self.cache[cache_key] = (market_data, datetime.utcnow())
            
            return market_data
            
        except Exception as e:
            print(f"Error getting NYC market data for {zip_code}: {e}")
            return None
    
    async def calculate_savings_potential(
        self, 
        zip_code: str, 
        monthly_bill: float,
        system_size_kw: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate personalized savings potential for a lead"""
        
        market_data = await self.get_zip_code_data(zip_code)
        if not market_data:
            return {}
        
        # Use provided system size or calculate from bill
        if not system_size_kw:
            system_size_kw = self._estimate_system_size(monthly_bill, market_data)
        
        # Calculate annual savings
        annual_usage_kwh = (monthly_bill / market_data["average_electric_rate_per_kwh"]) * 12
        annual_production_kwh = system_size_kw * 1200  # NYC average production factor
        annual_savings = min(annual_usage_kwh, annual_production_kwh) * market_data["average_electric_rate_per_kwh"]
        
        # Calculate with incentives
        total_incentives = self._calculate_total_incentives(market_data, system_size_kw)
        net_system_cost = (system_size_kw * 3000) - total_incentives  # $3/W base cost
        
        # Calculate payback period
        payback_period = net_system_cost / annual_savings if annual_savings > 0 else 0
        
        # Calculate 20-year savings
        twenty_year_savings = (annual_savings * 20) - net_system_cost
        
        return {
            "system_size_kw": system_size_kw,
            "annual_savings": annual_savings,
            "monthly_savings": annual_savings / 12,
            "total_incentives": total_incentives,
            "net_system_cost": net_system_cost,
            "payback_period_years": payback_period,
            "twenty_year_savings": twenty_year_savings,
            "savings_percentage": (annual_savings / (monthly_bill * 12)) * 100,
            "incentive_breakdown": self._get_incentive_breakdown(market_data, system_size_kw)
        }
    
    def _estimate_system_size(self, monthly_bill: float, market_data: Dict) -> float:
        """Estimate system size based on monthly bill"""
        
        # Calculate annual usage
        annual_usage_kwh = (monthly_bill / market_data["average_electric_rate_per_kwh"]) * 12
        
        # Estimate system size (accounting for 80% offset)
        system_size_kw = (annual_usage_kwh * 0.8) / 1200  # 1200 kWh/kW/year in NYC
        
        # Cap at reasonable maximum
        return min(system_size_kw, 20.0)
    
    def _calculate_total_incentives(self, market_data: Dict, system_size_kw: float) -> float:
        """Calculate total incentives available"""
        
        total_incentives = 0
        system_cost = system_size_kw * 3000  # $3/W base cost
        
        # Federal tax credit (30%)
        federal_credit = system_cost * 0.30
        total_incentives += federal_credit
        
        # NYSERDA rebate (varies by region)
        nyserda_rebate = system_size_kw * 500  # $0.50/W typical
        total_incentives += nyserda_rebate
        
        # Local incentives
        for incentive in market_data.get("incentives", []):
            if incentive["is_active"]:
                if incentive["type"] == "rebate":
                    if incentive["amount"]:
                        total_incentives += min(incentive["amount"], incentive.get("max_incentive_amount", float('inf')))
                    elif incentive["percentage"]:
                        total_incentives += system_cost * (incentive["percentage"] / 100)
                elif incentive["type"] == "grant":
                    total_incentives += incentive["amount"]
        
        return total_incentives
    
    def _get_incentive_breakdown(self, market_data: Dict, system_size_kw: float) -> List[Dict[str, Any]]:
        """Get detailed incentive breakdown"""
        
        breakdown = []
        system_cost = system_size_kw * 3000
        
        # Federal tax credit
        federal_credit = system_cost * 0.30
        breakdown.append({
            "name": "Federal Solar Tax Credit",
            "type": "tax_credit",
            "amount": federal_credit,
            "percentage": 30,
            "description": "30% federal tax credit (expires Dec 31, 2025)"
        })
        
        # NYSERDA rebate
        nyserda_rebate = system_size_kw * 500
        breakdown.append({
            "name": "NYSERDA Solar Incentive",
            "type": "rebate",
            "amount": nyserda_rebate,
            "description": "New York State Energy Research and Development Authority"
        })
        
        # Local incentives
        for incentive in market_data.get("incentives", []):
            if incentive["is_active"]:
                amount = 0
                if incentive["amount"]:
                    amount = min(incentive["amount"], incentive.get("max_incentive_amount", float('inf')))
                elif incentive["percentage"]:
                    amount = system_cost * (incentive["percentage"] / 100)
                
                if amount > 0:
                    breakdown.append({
                        "name": incentive["name"],
                        "type": incentive["type"],
                        "amount": amount,
                        "description": f"Local {incentive['type']} incentive"
                    })
        
        return breakdown
    
    async def get_urgency_factors(self, zip_code: str) -> Dict[str, Any]:
        """Get urgency factors for the 2025 tax credit deadline"""
        
        market_data = await self.get_zip_code_data(zip_code)
        if not market_data:
            return {}
        
        # Calculate time until deadline
        deadline = datetime(2025, 12, 31)
        days_remaining = (deadline - datetime.utcnow()).days
        
        # Calculate potential savings loss
        monthly_bill = market_data.get("average_monthly_bill", 200)
        annual_savings = monthly_bill * 12 * 0.8  # 80% offset
        daily_savings_loss = annual_savings / 365
        
        return {
            "days_remaining": days_remaining,
            "deadline_date": deadline.isoformat(),
            "potential_savings_loss": daily_savings_loss * days_remaining,
            "urgency_level": "high" if days_remaining < 90 else "medium" if days_remaining < 180 else "low",
            "incentive_value": market_data.get("average_installation_cost", 25000) * 0.30,
            "message": f"Only {days_remaining} days left to lock in the 30% federal tax credit!"
        }
    
    async def get_neighborhood_insights(self, zip_code: str) -> Dict[str, Any]:
        """Get neighborhood-specific insights for personalization"""
        
        market_data = await self.get_zip_code_data(zip_code)
        if not market_data:
            return {}
        
        borough = market_data.get("borough", "")
        neighborhood = market_data.get("neighborhood", "")
        
        # Borough-specific insights
        borough_insights = {
            "Manhattan": {
                "avg_bill": 350,
                "savings_potential": 2800,
                "roof_challenges": "Historic district restrictions, co-op board approvals",
                "success_rate": 0.85,
                "typical_timeline": "6-8 months for co-op approval"
            },
            "Brooklyn": {
                "avg_bill": 280,
                "savings_potential": 2200,
                "roof_challenges": "Industrial conversions, mixed-use buildings",
                "success_rate": 0.90,
                "typical_timeline": "3-4 months installation"
            },
            "Queens": {
                "avg_bill": 220,
                "savings_potential": 1800,
                "roof_challenges": "Co-op board process, community solar options",
                "success_rate": 0.88,
                "typical_timeline": "4-6 months with board approval"
            },
            "Bronx": {
                "avg_bill": 180,
                "savings_potential": 1400,
                "roof_challenges": "Multi-family complexity, affordable housing programs",
                "success_rate": 0.82,
                "typical_timeline": "5-7 months for multi-family"
            },
            "Staten Island": {
                "avg_bill": 200,
                "savings_potential": 1600,
                "roof_challenges": "Hurricane zone requirements, single-family focus",
                "success_rate": 0.92,
                "typical_timeline": "3-5 months installation"
            }
        }
        
        insights = borough_insights.get(borough, {})
        
        # Add neighborhood-specific data
        if neighborhood:
            insights.update({
                "neighborhood": neighborhood,
                "solar_adoption_rate": market_data.get("solar_adoption_rate", 0),
                "competition_level": market_data.get("competition_intensity", "medium"),
                "high_value_area": market_data.get("high_value_zip_code", False)
            })
        
        return insights
    
    async def get_objection_responses(self, objection_type: str, zip_code: str) -> Dict[str, Any]:
        """Get NYC-specific objection responses"""
        
        market_data = await self.get_zip_code_data(zip_code)
        if not market_data:
            return {}
        
        objection_responses = {
            "cost": {
                "title": "Solar is More Affordable Than You Think",
                "key_points": [
                    f"With incentives, your net cost could be as low as ${market_data.get('average_installation_cost', 25000) * 0.13:,.0f}",
                    f"Your monthly savings of ${market_data.get('average_savings_per_month', 150):.0f} means you'll break even in {market_data.get('average_payback_period_years', 7):.0f} years",
                    f"NYC's high electric rates (${market_data.get('average_electric_rate_per_kwh', 0.31):.2f}/kWh) make solar especially valuable here"
                ],
                "local_example": f"Similar homes in {market_data.get('neighborhood', 'your area')} save ${market_data.get('average_savings_per_month', 150) * 12:,.0f} annually"
            },
            "roof": {
                "title": "We Handle All NYC Roof Types",
                "key_points": [
                    "Our certified installers specialize in NYC's unique roof challenges",
                    "We handle co-op board approvals, historic district requirements, and flat roof installations",
                    f"Your {market_data.get('average_roof_condition', 'good')} roof condition is perfect for solar"
                ],
                "local_example": f"We've installed {market_data.get('total_solar_installations', 0)} systems in {market_data.get('neighborhood', 'your area')} with 100% success rate"
            },
            "aesthetics": {
                "title": "Modern Solar Panels Enhance Your Home",
                "key_points": [
                    "Today's panels are sleek and low-profile",
                    "We work with historic district requirements and HOA guidelines",
                    "Solar can actually increase your property value by 4-6%"
                ],
                "local_example": f"Historic homes in {market_data.get('neighborhood', 'your area')} have successfully installed solar while maintaining their character"
            },
            "process": {
                "title": "We Handle Everything for You",
                "key_points": [
                    "We manage permits, inspections, and utility connections",
                    "Our team handles co-op board presentations and approvals",
                    "Installation typically takes 1-2 days with minimal disruption"
                ],
                "local_example": f"Our {market_data.get('solar_installers_count', 0)} certified installers have completed projects in every NYC borough"
            },
            "timeline": {
                "title": "Don't Miss the 2025 Tax Credit Deadline",
                "key_points": [
                    "The 30% federal tax credit expires December 31, 2025",
                    "Co-op board approvals can take 3-6 months",
                    "We can start the process immediately to ensure you qualify"
                ],
                "local_example": f"Similar projects in {market_data.get('neighborhood', 'your area')} typically take 4-6 months from start to finish"
            }
        }
        
        return objection_responses.get(objection_type, {})
    
    async def get_competition_analysis(self, zip_code: str) -> Dict[str, Any]:
        """Get competition analysis for the area"""
        
        market_data = await self.get_zip_code_data(zip_code)
        if not market_data:
            return {}
        
        installers_count = market_data.get("solar_installers_count", 0)
        market_saturation = market_data.get("market_saturation", 0)
        competition_intensity = market_data.get("competition_intensity", "medium")
        
        return {
            "installers_count": installers_count,
            "market_saturation": market_saturation,
            "competition_intensity": competition_intensity,
            "market_opportunity": "high" if market_saturation < 0.1 else "medium" if market_saturation < 0.3 else "low",
            "competitive_advantage": "We specialize in NYC's unique challenges and have local expertise",
            "differentiation": "Our certified installers handle co-op approvals, historic districts, and complex NYC installations"
        }

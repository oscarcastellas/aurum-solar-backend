"""
NYC Solar Expertise Database
Comprehensive knowledge base for NYC-specific solar expertise
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class NeighborhoodData:
    """Neighborhood-specific solar data"""
    name: str
    borough: str
    zip_codes: List[str]
    avg_bill: float
    avg_savings: float
    solar_adoption_rate: float
    roof_challenges: List[str]
    success_stories: List[Dict[str, Any]]
    local_installers: List[str]
    board_approval_rate: float
    avg_install_time: int
    local_references: List[str]


@dataclass
class InstallerData:
    """NYC solar installer information"""
    name: str
    certifications: List[str]
    years_experience: int
    installations_completed: int
    specialties: List[str]
    service_areas: List[str]
    rating: float
    co_op_experience: bool
    historic_district_experience: bool


@dataclass
class BuildingTypeData:
    """Building type specific considerations"""
    building_type: str
    common_roof_types: List[str]
    structural_considerations: List[str]
    permit_requirements: List[str]
    board_approval_required: bool
    avg_install_time: int
    cost_multiplier: float
    success_rate: float


class NYCExpertiseDatabase:
    """Comprehensive NYC solar expertise database"""
    
    def __init__(self):
        self.neighborhoods = self._load_neighborhood_data()
        self.installers = self._load_installer_data()
        self.building_types = self._load_building_type_data()
        self.regulatory_info = self._load_regulatory_info()
        self.financing_options = self._load_financing_options()
        self.technical_specs = self._load_technical_specs()
    
    def _load_neighborhood_data(self) -> Dict[str, NeighborhoodData]:
        """Load neighborhood-specific data"""
        
        return {
            "park_slope": NeighborhoodData(
                name="Park Slope",
                borough="Brooklyn",
                zip_codes=["11215", "11217"],
                avg_bill=320.0,
                avg_savings=2800.0,
                solar_adoption_rate=0.12,
                roof_challenges=["Historic district restrictions", "Brownstone complexity", "Limited roof space"],
                success_stories=[
                    {
                        "system_size": "7.2kW",
                        "annual_savings": 3200,
                        "payback_years": 5.8,
                        "roof_type": "brownstone",
                        "quote": "The panels look great and we're saving $267 monthly",
                        "installer": "SolarCity"
                    },
                    {
                        "system_size": "5.8kW",
                        "annual_savings": 2600,
                        "payback_years": 6.2,
                        "roof_type": "co-op",
                        "quote": "Board approval was easier than expected",
                        "installer": "Local NYC Solar"
                    }
                ],
                local_installers=["SolarCity", "SunPower", "Local NYC Solar", "Brooklyn Solar Co"],
                board_approval_rate=0.85,
                avg_install_time=45,
                local_references=["Brooklyn Botanic Garden", "Prospect Park", "7th Avenue shops"]
            ),
            "upper_east_side": NeighborhoodData(
                name="Upper East Side",
                borough="Manhattan",
                zip_codes=["10021", "10028", "10075"],
                avg_bill=450.0,
                avg_savings=3800.0,
                solar_adoption_rate=0.08,
                roof_challenges=["Co-op board approval", "Historic district restrictions", "High-rise complexity"],
                success_stories=[
                    {
                        "system_size": "8.5kW",
                        "annual_savings": 3800,
                        "payback_years": 6.2,
                        "roof_type": "co-op",
                        "quote": "Board approval was easier than expected",
                        "installer": "Premium Solar NYC"
                    },
                    {
                        "system_size": "6.2kW",
                        "annual_savings": 2900,
                        "payback_years": 7.1,
                        "roof_type": "historic",
                        "quote": "Perfect for our landmark building",
                        "installer": "Manhattan Solar Co"
                    }
                ],
                local_installers=["Premium Solar NYC", "Manhattan Solar Co", "Luxury Solar Solutions"],
                board_approval_rate=0.78,
                avg_install_time=60,
                local_references=["Central Park", "Museum Mile", "5th Avenue", "Metropolitan Museum"]
            ),
            "dumbo": NeighborhoodData(
                name="DUMBO",
                borough="Brooklyn",
                zip_codes=["11201"],
                avg_bill=380.0,
                avg_savings=3200.0,
                solar_adoption_rate=0.15,
                roof_challenges=["Industrial building conversions", "Complex roof structures", "Hurricane zone considerations"],
                success_stories=[
                    {
                        "system_size": "6.8kW",
                        "annual_savings": 2900,
                        "payback_years": 5.5,
                        "roof_type": "loft",
                        "quote": "Perfect for our industrial space",
                        "installer": "Industrial Solar Solutions"
                    },
                    {
                        "system_size": "9.2kW",
                        "annual_savings": 4200,
                        "payback_years": 4.8,
                        "roof_type": "commercial",
                        "quote": "Amazing ROI for our business",
                        "installer": "NYC Solar Pro"
                    }
                ],
                local_installers=["Industrial Solar Solutions", "NYC Solar Pro", "Brooklyn Solar Co"],
                board_approval_rate=0.92,
                avg_install_time=35,
                local_references=["Brooklyn Bridge", "DUMBO waterfront", "Brooklyn Bridge Park", "St. Ann's Warehouse"]
            ),
            "forest_hills": NeighborhoodData(
                name="Forest Hills",
                borough="Queens",
                zip_codes=["11375", "11374"],
                avg_bill=220.0,
                avg_savings=1800.0,
                solar_adoption_rate=0.18,
                roof_challenges=["Co-op board approval process", "Community solar coordination", "Limited installer options"],
                success_stories=[
                    {
                        "system_size": "5.2kW",
                        "annual_savings": 1800,
                        "payback_years": 6.8,
                        "roof_type": "co-op",
                        "quote": "Great investment for our building",
                        "installer": "Queens Solar Co"
                    },
                    {
                        "system_size": "7.8kW",
                        "annual_savings": 2600,
                        "payback_years": 5.2,
                        "roof_type": "single_family",
                        "quote": "Best decision we ever made",
                        "installer": "Community Solar NYC"
                    }
                ],
                local_installers=["Queens Solar Co", "Community Solar NYC", "Long Island Solar"],
                board_approval_rate=0.88,
                avg_install_time=40,
                local_references=["Forest Hills Stadium", "Queens", "Austin Street", "Metropolitan Avenue"]
            ),
            "west_village": NeighborhoodData(
                name="West Village",
                borough="Manhattan",
                zip_codes=["10014", "10012"],
                avg_bill=420.0,
                avg_savings=3600.0,
                solar_adoption_rate=0.06,
                roof_challenges=["Historic district restrictions", "Landmark building requirements", "Limited roof access"],
                success_stories=[
                    {
                        "system_size": "6.5kW",
                        "annual_savings": 3100,
                        "payback_years": 7.2,
                        "roof_type": "historic",
                        "quote": "Preserved the historic character perfectly",
                        "installer": "Historic Solar Solutions"
                    }
                ],
                local_installers=["Historic Solar Solutions", "Manhattan Solar Co", "Luxury Solar Solutions"],
                board_approval_rate=0.65,
                avg_install_time=75,
                local_references=["Washington Square Park", "Bleecker Street", "Christopher Street", "Historic district"]
            )
        }
    
    def _load_installer_data(self) -> Dict[str, InstallerData]:
        """Load NYC solar installer data"""
        
        return {
            "solarcity": InstallerData(
                name="SolarCity",
                certifications=["NABCEP", "NYSERDA", "NYC DOB"],
                years_experience=15,
                installations_completed=2500,
                specialties=["Residential", "Commercial", "Co-op installations"],
                service_areas=["All NYC boroughs", "Westchester", "Long Island"],
                rating=4.2,
                co_op_experience=True,
                historic_district_experience=True
            ),
            "sunpower": InstallerData(
                name="SunPower",
                certifications=["NABCEP", "NYSERDA", "NYC DOB", "Premium Installer"],
                years_experience=12,
                installations_completed=1800,
                specialties=["Premium residential", "High-efficiency systems", "Luxury properties"],
                service_areas=["Manhattan", "Brooklyn", "Queens"],
                rating=4.5,
                co_op_experience=True,
                historic_district_experience=True
            ),
            "local_nyc_solar": InstallerData(
                name="Local NYC Solar",
                certifications=["NABCEP", "NYSERDA", "NYC DOB", "Local Business"],
                years_experience=8,
                installations_completed=1200,
                specialties=["Brooklyn", "Queens", "Co-op installations", "Community solar"],
                service_areas=["Brooklyn", "Queens", "Staten Island"],
                rating=4.3,
                co_op_experience=True,
                historic_district_experience=False
            ),
            "premium_solar_nyc": InstallerData(
                name="Premium Solar NYC",
                certifications=["NABCEP", "NYSERDA", "NYC DOB", "Luxury Installer"],
                years_experience=10,
                installations_completed=800,
                specialties=["Luxury residential", "Manhattan", "High-end co-ops"],
                service_areas=["Manhattan", "Brooklyn Heights", "Park Slope"],
                rating=4.7,
                co_op_experience=True,
                historic_district_experience=True
            ),
            "queens_solar_co": InstallerData(
                name="Queens Solar Co",
                certifications=["NABCEP", "NYSERDA", "NYC DOB"],
                years_experience=6,
                installations_completed=600,
                specialties=["Queens", "Co-op installations", "Community solar"],
                service_areas=["Queens", "Nassau County"],
                rating=4.1,
                co_op_experience=True,
                historic_district_experience=False
            )
        }
    
    def _load_building_type_data(self) -> Dict[str, BuildingTypeData]:
        """Load building type specific data"""
        
        return {
            "brownstone": BuildingTypeData(
                building_type="Brownstone",
                common_roof_types=["asphalt", "slate", "flat"],
                structural_considerations=["Historic restrictions", "Slate roof compatibility", "Limited roof space"],
                permit_requirements=["NYC DOB", "Historic district approval", "Structural assessment"],
                board_approval_required=False,
                avg_install_time=45,
                cost_multiplier=1.1,
                success_rate=0.85
            ),
            "co_op": BuildingTypeData(
                building_type="Co-op",
                common_roof_types=["flat", "asphalt", "membrane"],
                structural_considerations=["Board approval required", "Structural load assessment", "Insurance requirements"],
                permit_requirements=["NYC DOB", "Co-op board approval", "Architectural review"],
                board_approval_required=True,
                avg_install_time=60,
                cost_multiplier=1.2,
                success_rate=0.78
            ),
            "condo": BuildingTypeData(
                building_type="Condo",
                common_roof_types=["flat", "asphalt", "membrane"],
                structural_considerations=["HOA approval", "Limited roof access", "Shared space considerations"],
                permit_requirements=["NYC DOB", "HOA approval", "Architectural review"],
                board_approval_required=True,
                avg_install_time=50,
                cost_multiplier=1.15,
                success_rate=0.82
            ),
            "single_family": BuildingTypeData(
                building_type="Single Family",
                common_roof_types=["asphalt", "slate", "tile"],
                structural_considerations=["Standard residential", "Roof age assessment", "Structural integrity"],
                permit_requirements=["NYC DOB", "Con Edison interconnection"],
                board_approval_required=False,
                avg_install_time=35,
                cost_multiplier=1.0,
                success_rate=0.92
            ),
            "high_rise": BuildingTypeData(
                building_type="High-rise",
                common_roof_types=["flat", "membrane"],
                structural_considerations=["Structural load limits", "Wind load requirements", "Access limitations"],
                permit_requirements=["NYC DOB", "Structural engineering", "Wind load analysis"],
                board_approval_required=True,
                avg_install_time=90,
                cost_multiplier=1.5,
                success_rate=0.65
            )
        }
    
    def _load_regulatory_info(self) -> Dict[str, Any]:
        """Load NYC regulatory information"""
        
        return {
            "permits": {
                "nyc_dob": {
                    "electrical_permit": {
                        "cost": 200,
                        "timeline": "2-4 weeks",
                        "requirements": ["Electrical plans", "Contractor license", "Insurance certificate"]
                    },
                    "construction_permit": {
                        "cost": 300,
                        "timeline": "4-6 weeks",
                        "requirements": ["Construction plans", "Structural assessment", "Zoning compliance"]
                    },
                    "inspection": {
                        "cost": 150,
                        "timeline": "1-2 weeks",
                        "requirements": ["3 inspections required", "Final inspection", "Certificate of completion"]
                    }
                },
                "con_edison": {
                    "interconnection": {
                        "cost": 0,
                        "timeline": "2-4 weeks",
                        "requirements": ["Interconnection application", "System specifications", "Electrical inspection"]
                    },
                    "net_metering": {
                        "rate": "1:1 credit",
                        "duration": "20 years",
                        "requirements": ["Bi-directional meter", "System certification", "Safety inspection"]
                    }
                }
            },
            "incentives": {
                "federal_itc": {
                    "rate": 0.30,
                    "expiration": "2025-12-31",
                    "requirements": ["System installation", "Tax liability", "IRS Form 5695"]
                },
                "nyserda_rebate": {
                    "rate": 400,  # $/kW
                    "max_amount": 3000,
                    "requirements": ["NYSERDA application", "System certification", "Installer approval"]
                },
                "nyc_property_tax_abatement": {
                    "rate": 0.30,
                    "duration": "4 years",
                    "requirements": ["NYC application", "System certification", "Property tax liability"]
                }
            },
            "historic_districts": {
                "restrictions": ["Architectural review required", "Historic preservation guidelines", "Design approval"],
                "process": ["LPC application", "Design review", "Public hearing"],
                "timeline": "8-12 weeks",
                "success_rate": 0.65
            }
        }
    
    def _load_financing_options(self) -> Dict[str, Any]:
        """Load financing options data"""
        
        return {
            "solar_loans": {
                "rates": {
                    "excellent_credit": 0.0199,  # 1.99% APR
                    "good_credit": 0.0399,      # 3.99% APR
                    "fair_credit": 0.0599,      # 5.99% APR
                    "poor_credit": 0.0799       # 7.99% APR
                },
                "terms": [10, 15, 20, 25],  # years
                "down_payment": [0, 0.05, 0.10, 0.20],  # 0-20%
                "approval_time": "Same day",
                "requirements": ["Credit score 650+", "Income verification", "Property ownership"]
            },
            "leases": {
                "monthly_payment": "Fixed based on system size",
                "escalation": 0.029,  # 2.9% annual
                "term": 20,  # years
                "buyout_options": ["Year 5", "Year 10", "Year 15", "Year 20"],
                "requirements": ["Credit score 600+", "Income verification", "Property ownership"]
            },
            "power_purchase_agreements": {
                "rate": "Below utility rate",
                "escalation": 0.029,  # 2.9% annual
                "term": 20,  # years
                "maintenance": "Included",
                "requirements": ["Credit score 600+", "Income verification", "Property ownership"]
            }
        }
    
    def _load_technical_specs(self) -> Dict[str, Any]:
        """Load technical specifications"""
        
        return {
            "panel_types": {
                "monocrystalline": {
                    "efficiency": 0.20,
                    "cost_per_watt": 0.85,
                    "lifespan": 25,
                    "warranty": 25,
                    "best_for": ["Limited roof space", "High efficiency needs"]
                },
                "polycrystalline": {
                    "efficiency": 0.18,
                    "cost_per_watt": 0.75,
                    "lifespan": 25,
                    "warranty": 25,
                    "best_for": ["Cost-conscious", "Large roof space"]
                },
                "thin_film": {
                    "efficiency": 0.15,
                    "cost_per_watt": 0.65,
                    "lifespan": 20,
                    "warranty": 20,
                    "best_for": ["Flexible applications", "Aesthetic requirements"]
                }
            },
            "inverters": {
                "string_inverter": {
                    "efficiency": 0.97,
                    "cost_per_watt": 0.15,
                    "lifespan": 12,
                    "warranty": 12,
                    "best_for": ["Standard installations", "Cost-effective"]
                },
                "microinverter": {
                    "efficiency": 0.96,
                    "cost_per_watt": 0.25,
                    "lifespan": 25,
                    "warranty": 25,
                    "best_for": ["Shading issues", "Monitoring needs"]
                },
                "power_optimizer": {
                    "efficiency": 0.98,
                    "cost_per_watt": 0.20,
                    "lifespan": 25,
                    "warranty": 25,
                    "best_for": ["Partial shading", "Performance optimization"]
                }
            },
            "mounting_systems": {
                "asphalt_roof": {
                    "type": "Rail-based",
                    "penetration": "Through-roof",
                    "cost_per_watt": 0.10,
                    "installation_time": "Standard"
                },
                "flat_roof": {
                    "type": "Ballasted",
                    "penetration": "None",
                    "cost_per_watt": 0.15,
                    "installation_time": "Extended"
                },
                "tile_roof": {
                    "type": "Tile replacement",
                    "penetration": "Through-roof",
                    "cost_per_watt": 0.20,
                    "installation_time": "Extended"
                }
            }
        }
    
    def get_neighborhood_data(self, neighborhood: str) -> Optional[NeighborhoodData]:
        """Get neighborhood-specific data"""
        return self.neighborhoods.get(neighborhood.lower())
    
    def get_installer_data(self, installer: str) -> Optional[InstallerData]:
        """Get installer-specific data"""
        return self.installers.get(installer.lower())
    
    def get_building_type_data(self, building_type: str) -> Optional[BuildingTypeData]:
        """Get building type specific data"""
        return self.building_types.get(building_type.lower())
    
    def get_recommended_installers(self, neighborhood: str, building_type: str) -> List[str]:
        """Get recommended installers for neighborhood and building type"""
        neighborhood_data = self.get_neighborhood_data(neighborhood)
        if not neighborhood_data:
            return []
        
        # Filter installers by service area and specialty
        recommended = []
        for installer_name in neighborhood_data.local_installers:
            installer = self.get_installer_data(installer_name)
            if installer and self._is_installer_suitable(installer, building_type):
                recommended.append(installer_name)
        
        return recommended
    
    def _is_installer_suitable(self, installer: InstallerData, building_type: str) -> bool:
        """Check if installer is suitable for building type"""
        building_data = self.get_building_type_data(building_type)
        if not building_data:
            return True
        
        if building_type == "co_op" and not installer.co_op_experience:
            return False
        
        if building_type == "historic" and not installer.historic_district_experience:
            return False
        
        return True
    
    def get_success_story(self, neighborhood: str, building_type: str) -> Optional[Dict[str, Any]]:
        """Get relevant success story for neighborhood and building type"""
        neighborhood_data = self.get_neighborhood_data(neighborhood)
        if not neighborhood_data:
            return None
        
        # Find success story matching building type
        for story in neighborhood_data.success_stories:
            if story.get("roof_type") == building_type:
                return story
        
        # Return any success story if no match
        return neighborhood_data.success_stories[0] if neighborhood_data.success_stories else None
    
    def get_regulatory_timeline(self, building_type: str) -> Dict[str, Any]:
        """Get regulatory timeline for building type"""
        building_data = self.get_building_type_data(building_type)
        if not building_data:
            return self.regulatory_info["permits"]
        
        timeline = {
            "permit_approval": f"{building_data.avg_install_time // 2}-{building_data.avg_install_time} days",
            "installation": f"{building_data.avg_install_time // 3}-{building_data.avg_install_time // 2} days",
            "inspection": "1-2 weeks",
            "total_timeline": f"{building_data.avg_install_time}-{building_data.avg_install_time + 30} days"
        }
        
        if building_data.board_approval_required:
            timeline["board_approval"] = "2-4 weeks"
            timeline["total_timeline"] = f"{building_data.avg_install_time + 30}-{building_data.avg_install_time + 60} days"
        
        return timeline
    
    def get_financing_recommendation(self, credit_score: int, income: float, system_cost: float) -> Dict[str, Any]:
        """Get financing recommendation based on customer profile"""
        if credit_score >= 750:
            credit_tier = "excellent_credit"
        elif credit_score >= 700:
            credit_tier = "good_credit"
        elif credit_score >= 650:
            credit_tier = "fair_credit"
        else:
            credit_tier = "poor_credit"
        
        loan_rates = self.financing_options["solar_loans"]["rates"]
        rate = loan_rates[credit_tier]
        
        # Calculate monthly payment for 20-year term
        monthly_rate = rate / 12
        months = 20 * 12
        monthly_payment = system_cost * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        
        return {
            "recommended_option": "solar_loan",
            "rate": rate,
            "term_years": 20,
            "monthly_payment": monthly_payment,
            "total_cost": monthly_payment * months,
            "savings_vs_cash": system_cost * 0.15  # Rough estimate
        }

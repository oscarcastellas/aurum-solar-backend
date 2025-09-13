"""
NYC Solar Expertise Engine
Provides specialized knowledge about NYC solar installations, regulations, and market conditions
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class BuildingType(Enum):
    """NYC building types with different solar considerations"""
    SINGLE_FAMILY = "single_family"
    BROWNSTONE = "brownstone"
    TOWNHOUSE = "townhouse"
    CO_OP = "co_op"
    CONDO = "condo"
    HIGH_RISE = "high_rise"
    WALK_UP = "walk_up"


class HistoricDistrict(Enum):
    """NYC historic districts with special requirements"""
    GREENWICH_VILLAGE = "greenwich_village"
    BROOKLYN_HEIGHTS = "brooklyn_heights"
    PARK_SLOPE = "park_slope"
    DUMBO = "dumbo"
    TRIBECA = "tribeca"
    SOHO = "soho"
    NOT_HISTORIC = "not_historic"


@dataclass
class NYCExpertiseKnowledge:
    """NYC-specific solar expertise knowledge base"""
    borough: str
    building_type: BuildingType
    historic_district: Optional[HistoricDistrict]
    co_op_approval_required: bool
    roof_challenges: List[str]
    permit_complexity: str
    installation_timeline: str
    local_examples: List[str]
    regulatory_notes: List[str]


class NYCSolarExpertiseEngine:
    """NYC-specific solar expertise for intelligent conversations"""
    
    def __init__(self):
        self.expertise_database = self._build_expertise_database()
        self.neighborhood_data = self._build_neighborhood_data()
    
    def _build_expertise_database(self) -> Dict[str, NYCExpertiseKnowledge]:
        """Build comprehensive NYC solar expertise database"""
        
        return {
            # Manhattan
            "10001": NYCExpertiseKnowledge(
                borough="Manhattan",
                building_type=BuildingType.HIGH_RISE,
                historic_district=None,
                co_op_approval_required=True,
                roof_challenges=["Limited roof space", "HVAC equipment", "Wind loads"],
                permit_complexity="High - DOB approval required",
                installation_timeline="12-16 weeks",
                local_examples=["Midtown East co-ops", "Financial District condos"],
                regulatory_notes=["Fire department approval required", "Structural engineering needed"]
            ),
            
            "10021": NYCExpertiseKnowledge(
                borough="Manhattan",
                building_type=BuildingType.HIGH_RISE,
                historic_district=None,
                co_op_approval_required=True,
                roof_challenges=["Limited roof space", "HVAC equipment"],
                permit_complexity="High - DOB approval required",
                installation_timeline="12-16 weeks",
                local_examples=["Upper East Side co-ops", "Yorkville condos"],
                regulatory_notes=["Co-op board approval essential", "Architectural review required"]
            ),
            
            "10014": NYCExpertiseKnowledge(
                borough="Manhattan",
                building_type=BuildingType.BROWNSTONE,
                historic_district=HistoricDistrict.GREENWICH_VILLAGE,
                co_op_approval_required=False,
                roof_challenges=["Historic preservation", "Aesthetic requirements", "Sloped roofs"],
                permit_complexity="Very High - LPC approval required",
                installation_timeline="16-20 weeks",
                local_examples=["Greenwich Village brownstones", "West Village townhouses"],
                regulatory_notes=["Landmarks Preservation Commission approval", "Historic district restrictions"]
            ),
            
            # Brooklyn
            "11215": NYCExpertiseKnowledge(
                borough="Brooklyn",
                building_type=BuildingType.BROWNSTONE,
                historic_district=HistoricDistrict.PARK_SLOPE,
                co_op_approval_required=False,
                roof_challenges=["Historic preservation", "Flat roofs", "Aesthetic requirements"],
                permit_complexity="High - LPC approval required",
                installation_timeline="14-18 weeks",
                local_examples=["Park Slope brownstones", "Prospect Heights townhouses"],
                regulatory_notes=["Landmarks Preservation Commission approval", "Historic district guidelines"]
            ),
            
            "11201": NYCExpertiseKnowledge(
                borough="Brooklyn",
                building_type=BuildingType.HIGH_RISE,
                historic_district=HistoricDistrict.DUMBO,
                co_op_approval_required=True,
                roof_challenges=["Limited roof space", "Historic preservation", "Wind loads"],
                permit_complexity="Very High - LPC and DOB approval",
                installation_timeline="18-22 weeks",
                local_examples=["DUMBO lofts", "Brooklyn Heights condos"],
                regulatory_notes=["Historic district compliance", "Structural engineering required"]
            ),
            
            # Queens
            "11375": NYCExpertiseKnowledge(
                borough="Queens",
                building_type=BuildingType.SINGLE_FAMILY,
                historic_district=None,
                co_op_approval_required=False,
                roof_challenges=["Standard residential considerations"],
                permit_complexity="Medium - Standard residential permits",
                installation_timeline="8-12 weeks",
                local_examples=["Forest Hills single-family homes", "Kew Gardens townhouses"],
                regulatory_notes=["Standard DOB permits", "Electrical inspection required"]
            ),
            
            # Bronx
            "10462": NYCExpertiseKnowledge(
                borough="Bronx",
                building_type=BuildingType.SINGLE_FAMILY,
                historic_district=None,
                co_op_approval_required=False,
                roof_challenges=["Standard residential considerations"],
                permit_complexity="Medium - Standard residential permits",
                installation_timeline="8-12 weeks",
                local_examples=["Riverdale single-family homes", "Throggs Neck townhouses"],
                regulatory_notes=["Standard DOB permits", "Electrical inspection required"]
            ),
            
            # Staten Island
            "10301": NYCExpertiseKnowledge(
                borough="Staten Island",
                building_type=BuildingType.SINGLE_FAMILY,
                historic_district=None,
                co_op_approval_required=False,
                roof_challenges=["Standard residential considerations"],
                permit_complexity="Low - Simplified permits",
                installation_timeline="6-10 weeks",
                local_examples=["St. George single-family homes", "New Brighton townhouses"],
                regulatory_notes=["Simplified permit process", "Faster approval times"]
            )
        }
    
    def _build_neighborhood_data(self) -> Dict[str, Dict[str, Any]]:
        """Build neighborhood-specific solar market data"""
        
        return {
            "park_slope": {
                "solar_adoption_rate": 0.18,
                "average_system_size": 7.2,
                "typical_building": "Brownstone",
                "special_considerations": ["Historic district", "Flat roofs", "Aesthetic requirements"],
                "success_stories": [
                    "7.5kW system on 4th Avenue brownstone, $280/month savings",
                    "6.8kW system on 7th Avenue townhouse, 6.2 year payback"
                ]
            },
            "upper_east_side": {
                "solar_adoption_rate": 0.12,
                "average_system_size": 5.8,
                "typical_building": "High-rise co-op",
                "special_considerations": ["Co-op board approval", "Limited roof space", "HVAC equipment"],
                "success_stories": [
                    "5.5kW system on 85th Street co-op, $320/month savings",
                    "4.8kW system on York Avenue condo, 7.1 year payback"
                ]
            },
            "forest_hills": {
                "solar_adoption_rate": 0.22,
                "average_system_size": 8.1,
                "typical_building": "Single-family home",
                "special_considerations": ["Standard permits", "Good roof access", "PSEG territory"],
                "success_stories": [
                    "8.5kW system on Austin Street, $245/month savings",
                    "7.2kW system on Burns Street, 5.8 year payback"
                ]
            }
        }
    
    def get_zip_code_expertise(self, zip_code: str) -> Optional[NYCExpertiseKnowledge]:
        """Get NYC expertise for a specific zip code"""
        return self.expertise_database.get(zip_code)
    
    def get_neighborhood_expertise(self, neighborhood: str) -> Optional[Dict[str, Any]]:
        """Get neighborhood-specific solar expertise"""
        return self.neighborhood_data.get(neighborhood.lower())
    
    def generate_nyc_specific_advice(
        self, 
        zip_code: str, 
        building_type: str = None,
        concerns: List[str] = None
    ) -> str:
        """Generate NYC-specific solar advice for conversations"""
        
        expertise = self.get_zip_code_expertise(zip_code)
        if not expertise:
            return "I'd be happy to help you explore solar options for your NYC property."
        
        advice_parts = []
        
        # Building type specific advice
        if expertise.co_op_approval_required:
            advice_parts.append(
                "Since you're in a co-op building, the approval process will involve your co-op board. "
                "We have extensive experience with co-op solar installations and can help guide you through "
                "the board approval process, which typically takes 4-6 weeks."
            )
        
        # Historic district considerations
        if expertise.historic_district and expertise.historic_district != HistoricDistrict.NOT_HISTORIC:
            advice_parts.append(
                f"Your property is in a historic district, which requires special approval from the "
                f"Landmarks Preservation Commission. We've successfully installed systems in {expertise.historic_district.value} "
                f"and understand the aesthetic requirements and approval process."
            )
        
        # Roof challenges
        if expertise.roof_challenges:
            challenges_text = ", ".join(expertise.roof_challenges[:-1])
            if len(expertise.roof_challenges) > 1:
                challenges_text += f", and {expertise.roof_challenges[-1]}"
            else:
                challenges_text = expertise.roof_challenges[0]
            
            advice_parts.append(
                f"Common challenges in your area include {challenges_text}. Our certified installers "
                f"have experience with these conditions and can provide solutions."
            )
        
        # Timeline expectations
        advice_parts.append(
            f"Based on your location, the typical installation timeline is {expertise.installation_timeline}, "
            f"including permit approval and installation."
        )
        
        # Local examples
        if expertise.local_examples:
            examples_text = " and ".join(expertise.local_examples)
            advice_parts.append(
                f"We've successfully installed systems in {examples_text} with excellent results."
            )
        
        return " ".join(advice_parts)
    
    def get_objection_responses(self, objection_type: str, zip_code: str = None) -> str:
        """Get NYC-specific responses to common objections"""
        
        responses = {
            "cost": {
                "default": "I understand cost is a concern. With NYC's high electric rates and current incentives, most homeowners see 75-87% cost reduction and payback in 6-8 years.",
                "high_rise": "For co-op and condo buildings, we can often work with the building to spread costs across multiple units or explore community solar options.",
                "historic": "Historic district installations may have additional costs, but the long-term savings still make it worthwhile. We can show you detailed ROI calculations."
            },
            "roof": {
                "default": "Our certified installers handle all types of NYC roofs daily. We'll conduct a thorough roof assessment and structural analysis.",
                "flat": "Flat roofs are actually ideal for solar in NYC. We use ballasted mounting systems that don't penetrate the roof membrane.",
                "historic": "For historic properties, we use specialized mounting systems and work closely with preservation requirements."
            },
            "aesthetics": {
                "default": "Modern solar panels are sleek and actually add value to your property. We can show you examples of installations in your neighborhood.",
                "historic": "In historic districts, we use panels that blend with the architecture and work with the Landmarks Commission on approval.",
                "co_op": "We understand co-op aesthetic requirements and can provide detailed renderings for board approval."
            },
            "process": {
                "default": "We handle all permits, inspections, and utility paperwork. Our team has extensive NYC experience and knows the process inside and out.",
                "historic": "We have specialized experience with Landmarks Preservation Commission approvals and historic district requirements.",
                "co_op": "We work directly with co-op boards and management companies to streamline the approval process."
            },
            "timeline": {
                "default": "The federal tax credit expires December 31st, 2025, so there's urgency to move forward. We can typically complete installations in 8-12 weeks.",
                "historic": "Historic district approvals add 4-6 weeks, but we can start the process immediately and work in parallel.",
                "co_op": "Co-op board approval typically takes 4-6 weeks, but we can begin the technical planning and permitting process now."
            }
        }
        
        base_response = responses.get(objection_type, {}).get("default", "I'd be happy to address your concerns about solar installation.")
        
        if zip_code:
            expertise = self.get_zip_code_expertise(zip_code)
            if expertise:
                if expertise.historic_district and expertise.historic_district != HistoricDistrict.NOT_HISTORIC:
                    specific_response = responses.get(objection_type, {}).get("historic")
                    if specific_response:
                        base_response = specific_response
                elif expertise.co_op_approval_required:
                    specific_response = responses.get(objection_type, {}).get("co_op")
                    if specific_response:
                        base_response = specific_response
        
        return base_response
    
    def get_financing_advice(self, zip_code: str, building_type: str = None) -> str:
        """Get NYC-specific financing advice"""
        
        expertise = self.get_zip_code_expertise(zip_code)
        
        if expertise and expertise.co_op_approval_required:
            return (
                "For co-op buildings, we offer several financing options including building-wide installations "
                "that can be financed through the building's capital improvements budget. We also work with "
                "lenders who specialize in co-op solar financing."
            )
        else:
            return (
                "We offer $0 down financing with rates as low as 1.99% APR for qualified homeowners. "
                "With NYC's high electric rates, your monthly solar payment is often less than your current "
                "electric bill, so you start saving immediately."
            )
    
    def get_urgency_creation_message(self, zip_code: str = None) -> str:
        """Generate urgency creation message with NYC context"""
        
        messages = [
            "The 30% federal tax credit expires December 31st, 2025 - that's a $6,000+ savings that disappears forever.",
            "NYC electric rates continue to rise, with Con Edison requesting another rate increase this year.",
            "NYSERDA rebates are declining block - the longer you wait, the less incentive money is available.",
            "Installation slots are filling up fast for 2025. We're booking into Q2 already.",
            "Peak installation season is spring/summer - book now to ensure installation before winter weather delays."
        ]
        
        if zip_code:
            expertise = self.get_zip_code_expertise(zip_code)
            if expertise and expertise.historic_district:
                messages.append(
                    "Historic district approvals can take 6-8 weeks - starting now ensures you can install before the tax credit expires."
                )
            elif expertise and expertise.co_op_approval_required:
                messages.append(
                    "Co-op board approval processes can take 4-6 weeks - starting now ensures you don't miss the 2025 tax credit deadline."
                )
        
        return messages[0]  # Return first message for now
    
    def get_neighborhood_success_story(self, neighborhood: str) -> Optional[str]:
        """Get a relevant success story for the neighborhood"""
        
        neighborhood_data = self.get_neighborhood_expertise(neighborhood)
        if neighborhood_data and neighborhood_data.get("success_stories"):
            return neighborhood_data["success_stories"][0]
        
        return None

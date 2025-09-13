#!/usr/bin/env python3
"""
Test Enhanced Conversational AI Agent
Demonstrates intelligent solar system recommendations during conversations
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_conversation_agent():
    """Test the enhanced conversation agent with intelligent solar recommendations"""
    
    print("🤖 Testing Enhanced Aurum Solar Conversational AI Agent")
    print("=" * 70)
    
    # Test scenarios representing different NYC customer types
    test_scenarios = [
        {
            "name": "Premium Lead - Park Slope Brownstone Owner",
            "messages": [
                "Hi, I'm interested in getting solar for my brownstone in Park Slope",
                "Yes, I own the building, it's a 4-story brownstone",
                "My Con Edison bill is around $380 per month",
                "I'm looking to install solar this year, preferably by summer",
                "The roof is flat and in good condition",
                "I'm concerned about the historic district restrictions"
            ]
        },
        {
            "name": "High-Value Lead - Upper East Side Co-op Owner",
            "messages": [
                "I want to explore solar for my co-op apartment",
                "I own the apartment in a 20-story building on the Upper East Side",
                "My electric bill is about $420 monthly",
                "I'm considering solar for next year",
                "I have questions about the co-op board approval process"
            ]
        },
        {
            "name": "Standard Lead - Forest Hills Homeowner",
            "messages": [
                "How much does solar cost for a single-family home?",
                "I own my home in Forest Hills, Queens",
                "My PSEG bill is $220 per month",
                "I'm interested in the financial benefits",
                "What's the installation process like?"
            ]
        },
        {
            "name": "Technical Inquiry - Manhattan Historic District",
            "messages": [
                "Can I install solar on a historic building?",
                "I own a townhouse in Greenwich Village",
                "My Con Edison bill is $450 monthly",
                "I'm worried about Landmarks Commission approval",
                "What about the aesthetic requirements?"
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print("-" * 60)
        
        # Simulate enhanced conversation processing
        conversation_results = simulate_enhanced_conversation(scenario['messages'])
        
        # Display the enhanced lead output format
        display_enhanced_lead_output(conversation_results, scenario['name'])

def simulate_enhanced_conversation(messages: list) -> Dict[str, Any]:
    """Simulate the enhanced conversation processing with intelligent recommendations"""
    
    # Initialize enhanced conversation context
    context = {
        "session_id": f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "messages": [],
        "extracted_data": {},
        "lead_score": 0,
        "quality_tier": "unqualified",
        "conversation_stage": "welcome",
        "nyc_data": {},
        "solar_calculation": None,
        "nyc_expertise": {},
        "b2b_recommendations": []
    }
    
    # Process each message with enhanced intelligence
    for i, message in enumerate(messages):
        context["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "bot_response": generate_enhanced_bot_response(message, context)
        })
        
        # Extract data from message with enhanced analysis
        extracted = extract_enhanced_data_from_message(message, context)
        context["extracted_data"].update(extracted)
        
        # Update conversation stage with intelligent progression
        context["conversation_stage"] = determine_enhanced_stage(context, i)
    
    # Calculate enhanced lead score and quality
    context["lead_score"] = calculate_enhanced_lead_score(context)
    context["quality_tier"] = determine_enhanced_quality_tier(context["lead_score"])
    
    # Generate NYC market data with expertise
    context["nyc_data"] = generate_enhanced_nyc_market_data(context["extracted_data"])
    
    # Generate intelligent solar calculation if enough data
    if context["extracted_data"].get("bill_amount") and context["extracted_data"].get("zip_code"):
        context["solar_calculation"] = generate_intelligent_solar_calculation(context)
    
    # Generate NYC expertise recommendations
    context["nyc_expertise"] = generate_nyc_expertise_recommendations(context)
    
    # Generate enhanced B2B recommendations
    context["b2b_recommendations"] = generate_enhanced_b2b_recommendations(context)
    
    return context

def generate_enhanced_bot_response(message: str, context: Dict[str, Any]) -> str:
    """Generate enhanced bot response with intelligent recommendations"""
    
    message_lower = message.lower()
    stage = context.get("conversation_stage", "welcome")
    
    # Enhanced responses with NYC expertise
    if "interested" in message_lower or "solar" in message_lower:
        return "Excellent! I'd love to help you explore solar options for your NYC property. As a local NYC solar expert, I can provide specific recommendations based on your building type, utility territory, and neighborhood. Do you own your property?"
    
    elif "own" in message_lower and ("yes" in message_lower or "owner" in message_lower):
        if "brownstone" in message_lower or "townhouse" in message_lower:
            return "Perfect! Brownstone and townhouse installations are our specialty. What's your average monthly electric bill, and which utility do you use - Con Edison or PSEG?"
        elif "co-op" in message_lower or "apartment" in message_lower:
            return "Great! Co-op solar installations require board approval, which we handle regularly. What's your monthly electric bill, and which floor are you on?"
        else:
            return "Perfect! Homeownership is the first step. What's your average monthly electric bill?"
    
    elif "bill" in message_lower and "$" in message:
        return "That's helpful information. What utility company do you use - Con Edison or PSEG? Also, what's your zip code so I can provide location-specific recommendations?"
    
    elif "con edison" in message_lower or "con ed" in message_lower:
        return "Con Edison rates are among the highest in the country at around 31¢/kWh, making solar particularly valuable in your area. What's your zip code, and when are you thinking about installing solar?"
    
    elif "pseg" in message_lower:
        return "PSEG rates are around 27¢/kWh, which still makes solar a smart investment. What's your zip code, and what's your timeline for installation?"
    
    elif "this year" in message_lower or "summer" in message_lower:
        return "Excellent timing! The 30% federal tax credit expires December 31st, 2025, so there's urgency to move forward. What's your roof condition like, and do you have any concerns about the installation process?"
    
    elif "roof" in message_lower:
        if "flat" in message_lower:
            return "Flat roofs are actually ideal for solar in NYC. We use ballasted mounting systems that don't penetrate the roof membrane. What's your zip code so I can provide specific recommendations for your area?"
        else:
            return "Good to know. For NYC installations, we need to consider roof type, shading, and structural requirements. What's your zip code?"
    
    elif "historic" in message_lower or "landmarks" in message_lower:
        return "Historic district installations require Landmarks Preservation Commission approval, which we handle regularly. We use specialized mounting systems and work closely with preservation requirements. What's your zip code?"
    
    elif "co-op" in message_lower and "board" in message_lower:
        return "Co-op board approval typically takes 4-6 weeks, but we can begin the technical planning and permitting process now. We have extensive experience with co-op solar installations. What's your zip code?"
    
    elif "cost" in message_lower or "price" in message_lower:
        return "I understand cost is a concern. With NYC's high electric rates and current incentives, most homeowners see 75-87% cost reduction. Let me show you the specific numbers based on your situation. What's your zip code?"
    
    else:
        return "That's great information. Let me gather a few more details to provide you with accurate solar recommendations for your NYC property."

def extract_enhanced_data_from_message(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured data from user message with enhanced analysis"""
    
    extracted = {}
    message_lower = message.lower()
    
    # Extract bill amount
    if "$" in message:
        import re
        bill_match = re.search(r'\$(\d+)', message)
        if bill_match:
            extracted["bill_amount"] = float(bill_match.group(1))
    
    # Extract location information with enhanced NYC mapping
    if "park slope" in message_lower:
        extracted["zip_code"] = "11215"
        extracted["borough"] = "Brooklyn"
        extracted["utility"] = "con_edison"
        extracted["building_type"] = "brownstone"
        extracted["historic_district"] = "park_slope"
    elif "upper east side" in message_lower or "ues" in message_lower:
        extracted["zip_code"] = "10021"
        extracted["borough"] = "Manhattan"
        extracted["utility"] = "con_edison"
        extracted["building_type"] = "high_rise"
        extracted["co_op_approval_required"] = True
    elif "forest hills" in message_lower:
        extracted["zip_code"] = "11375"
        extracted["borough"] = "Queens"
        extracted["utility"] = "pseg"
        extracted["building_type"] = "single_family"
    elif "greenwich village" in message_lower:
        extracted["zip_code"] = "10014"
        extracted["borough"] = "Manhattan"
        extracted["utility"] = "con_edison"
        extracted["building_type"] = "brownstone"
        extracted["historic_district"] = "greenwich_village"
    
    # Extract building type
    if "brownstone" in message_lower:
        extracted["building_type"] = "brownstone"
    elif "co-op" in message_lower or "apartment" in message_lower:
        extracted["building_type"] = "co_op"
        extracted["co_op_approval_required"] = True
    elif "single-family" in message_lower or "house" in message_lower:
        extracted["building_type"] = "single_family"
    
    # Extract homeownership status
    if "own" in message_lower and ("yes" in message_lower or "owner" in message_lower):
        extracted["homeowner"] = True
    elif "rent" in message_lower:
        extracted["homeowner"] = False
    
    # Extract timeline
    if "this year" in message_lower or "summer" in message_lower:
        extracted["timeline"] = "2025"
    elif "next year" in message_lower:
        extracted["timeline"] = "2026"
    
    # Extract roof information
    if "flat roof" in message_lower:
        extracted["roof_type"] = "flat"
    elif "sloped" in message_lower:
        extracted["roof_type"] = "sloped"
    
    # Extract concerns
    if "historic" in message_lower or "landmarks" in message_lower:
        extracted["concerns"] = ["historic_district"]
    elif "board" in message_lower and "approval" in message_lower:
        extracted["concerns"] = ["co_op_approval"]
    elif "cost" in message_lower or "price" in message_lower:
        extracted["concerns"] = ["cost"]
    
    return extracted

def determine_enhanced_stage(context: Dict[str, Any], message_index: int) -> str:
    """Determine conversation stage based on enhanced context"""
    
    if message_index == 0:
        return "welcome"
    elif context["extracted_data"].get("homeowner") is True:
        if context["extracted_data"].get("bill_amount") and context["extracted_data"].get("zip_code"):
            return "solar_calculation"
        elif context["extracted_data"].get("bill_amount"):
            return "qualification"
        else:
            return "discovery"
    elif context["extracted_data"].get("homeowner") is False:
        return "disqualification"
    else:
        return "discovery"

def calculate_enhanced_lead_score(context: Dict[str, Any]) -> int:
    """Calculate enhanced lead score based on extracted data"""
    
    score = 0
    data = context["extracted_data"]
    
    # Homeowner status (40 points)
    if data.get("homeowner") is True:
        score += 40
    elif data.get("homeowner") is False:
        return 0  # Disqualified
    
    # Bill amount (30 points) - Enhanced for NYC rates
    bill = data.get("bill_amount", 0)
    if bill >= 400:
        score += 30
    elif bill >= 300:
        score += 25
    elif bill >= 200:
        score += 20
    elif bill >= 150:
        score += 10
    
    # Timeline urgency (20 points)
    timeline = data.get("timeline")
    if timeline == "2025":
        score += 20
    elif timeline == "2026":
        score += 10
    
    # Location quality (10 points) - Enhanced for NYC
    if data.get("borough") in ["Manhattan", "Brooklyn"]:
        score += 10
    elif data.get("borough") in ["Queens", "Bronx"]:
        score += 5
    
    # Building type bonus (5 points)
    if data.get("building_type") == "single_family":
        score += 5
    
    return min(score, 100)

def determine_enhanced_quality_tier(score: int) -> str:
    """Determine enhanced quality tier based on score"""
    
    if score >= 85:
        return "premium"
    elif score >= 70:
        return "standard"
    elif score >= 50:
        return "basic"
    else:
        return "unqualified"

def generate_enhanced_nyc_market_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate enhanced NYC market data with expertise"""
    
    zip_code = extracted_data.get("zip_code", "10001")
    borough = extracted_data.get("borough", "Manhattan")
    utility = extracted_data.get("utility", "con_edison")
    building_type = extracted_data.get("building_type", "unknown")
    
    # Enhanced NYC market data
    market_data = {
        "zip_code": zip_code,
        "borough": borough,
        "utility": utility,
        "building_type": building_type,
        "electric_rate_per_kwh": 0.31 if utility == "con_edison" else 0.27,
        "solar_adoption_rate": 0.15 if borough in ["Manhattan", "Brooklyn"] else 0.12,
        "average_installation_cost_per_watt": 3.50,
        "incentives": {
            "federal_tax_credit": 0.30,
            "nyserda_rebate": 0.25,
            "nyc_property_tax_abatement": 0.20
        },
        "permit_timeline_days": 30,
        "competition_level": "high" if borough == "Manhattan" else "medium",
        "special_considerations": []
    }
    
    # Add building-specific considerations
    if building_type == "co_op":
        market_data["special_considerations"].append("Co-op board approval required")
        market_data["permit_timeline_days"] = 60
    elif building_type == "brownstone":
        if extracted_data.get("historic_district"):
            market_data["special_considerations"].append("Historic district - LPC approval required")
            market_data["permit_timeline_days"] = 90
    
    return market_data

def generate_intelligent_solar_calculation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate intelligent solar calculation with NYC expertise"""
    
    data = context["extracted_data"]
    market_data = context["nyc_data"]
    
    bill_amount = data.get("bill_amount", 200)
    utility_rate = market_data["electric_rate_per_kwh"]
    borough = data.get("borough", "Manhattan")
    
    # Calculate system size with NYC-specific adjustments
    annual_usage = bill_amount * 12 / utility_rate
    system_size_kw = annual_usage / 1300  # NYC average irradiance
    
    # Adjust for building type
    if data.get("building_type") == "co_op":
        system_size_kw *= 0.7  # Limited roof space
    elif data.get("building_type") == "brownstone":
        system_size_kw *= 0.9  # Some limitations
    
    # Calculate costs and savings
    gross_cost = system_size_kw * market_data["average_installation_cost_per_watt"] * 1000
    federal_credit = gross_cost * market_data["incentives"]["federal_tax_credit"]
    nyserda_rebate = min(system_size_kw * 400, 3000)
    net_cost = gross_cost - federal_credit - nyserda_rebate
    
    annual_savings = annual_usage * utility_rate
    payback_years = net_cost / annual_savings
    
    calculation = {
        "system_size_kw": round(system_size_kw, 1),
        "panel_count": int(system_size_kw * 1000 / 300),  # 300W panels
        "annual_production_kwh": int(annual_usage),
        "gross_cost": round(gross_cost, 2),
        "net_cost": round(net_cost, 2),
        "annual_savings": round(annual_savings, 2),
        "monthly_savings": round(annual_savings / 12, 2),
        "payback_years": round(payback_years, 1),
        "roi_percentage": round((annual_savings * 25 - net_cost) / net_cost * 100, 1),
        "incentives": {
            "federal_credit": round(federal_credit, 2),
            "nyserda_rebate": round(nyserda_rebate, 2)
        },
        "financing_options": [
            {
                "type": "cash_purchase",
                "monthly_payment": 0,
                "total_cost": net_cost,
                "description": "Cash purchase after incentives"
            },
            {
                "type": "financing_1.99",
                "monthly_payment": round(net_cost * 0.0042, 2),  # 1.99% APR
                "total_cost": round(net_cost * 1.12, 2),
                "description": "$0 down financing at 1.99% APR"
            }
        ],
        "nyc_specific_factors": {
            "utility_territory": market_data["utility"],
            "borough": borough,
            "building_type": data.get("building_type"),
            "historic_district": data.get("historic_district"),
            "co_op_approval_required": data.get("co_op_approval_required", False)
        }
    }
    
    return calculation

def generate_nyc_expertise_recommendations(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate NYC-specific expertise recommendations"""
    
    data = context["extracted_data"]
    zip_code = data.get("zip_code")
    
    expertise = {
        "building_type": data.get("building_type"),
        "historic_district": data.get("historic_district"),
        "co_op_approval_required": data.get("co_op_approval_required", False),
        "special_considerations": [],
        "installation_timeline": "8-12 weeks",
        "permit_complexity": "Medium",
        "local_examples": [],
        "regulatory_notes": []
    }
    
    if zip_code:
        if zip_code == "11215":  # Park Slope
            expertise.update({
                "historic_district": "park_slope",
                "special_considerations": ["Historic preservation", "Flat roofs", "Aesthetic requirements"],
                "installation_timeline": "14-18 weeks",
                "permit_complexity": "High - LPC approval required",
                "local_examples": ["Park Slope brownstones", "Prospect Heights townhouses"],
                "regulatory_notes": ["Landmarks Preservation Commission approval", "Historic district guidelines"]
            })
        elif zip_code == "10021":  # Upper East Side
            expertise.update({
                "co_op_approval_required": True,
                "special_considerations": ["Co-op board approval", "Limited roof space", "HVAC equipment"],
                "installation_timeline": "12-16 weeks",
                "permit_complexity": "High - DOB approval required",
                "local_examples": ["Upper East Side co-ops", "Yorkville condos"],
                "regulatory_notes": ["Co-op board approval essential", "Architectural review required"]
            })
        elif zip_code == "11375":  # Forest Hills
            expertise.update({
                "special_considerations": ["Standard residential considerations"],
                "installation_timeline": "8-12 weeks",
                "permit_complexity": "Medium - Standard residential permits",
                "local_examples": ["Forest Hills single-family homes", "Kew Gardens townhouses"],
                "regulatory_notes": ["Standard DOB permits", "Electrical inspection required"]
            })
    
    return expertise

def generate_enhanced_b2b_recommendations(context: Dict[str, Any]) -> list:
    """Generate enhanced B2B platform recommendations"""
    
    quality_tier = context["quality_tier"]
    lead_score = context["lead_score"]
    solar_calc = context.get("solar_calculation")
    expertise = context.get("nyc_expertise", {})
    
    recommendations = []
    
    if quality_tier == "premium":
        recommendations = [
            {
                "platform": "SolarReviews",
                "priority": "immediate",
                "expected_value": 300,
                "reason": f"Premium lead with ${context['extracted_data'].get('bill_amount', 0):.0f} bill, {expertise.get('building_type', 'unknown')} building, 2025 timeline"
            },
            {
                "platform": "Modernize", 
                "priority": "immediate",
                "expected_value": 250,
                "reason": "High-quality lead with technical recommendations"
            }
        ]
    elif quality_tier == "standard":
        recommendations = [
            {
                "platform": "Modernize",
                "priority": "high", 
                "expected_value": 175,
                "reason": f"Standard lead with {expertise.get('building_type', 'unknown')} building, good qualification"
            },
            {
                "platform": "SolarReviews",
                "priority": "medium",
                "expected_value": 150,
                "reason": "Standard lead for shared marketplace"
            }
        ]
    elif quality_tier == "basic":
        recommendations = [
            {
                "platform": "Modernize",
                "priority": "medium",
                "expected_value": 100,
                "reason": "Basic lead with adequate qualification"
            }
        ]
    
    # Add technical details to recommendations
    if solar_calc:
        for rec in recommendations:
            rec["technical_details"] = {
                "system_size_kw": solar_calc["system_size_kw"],
                "estimated_cost": solar_calc["net_cost"],
                "monthly_savings": solar_calc["monthly_savings"],
                "payback_years": solar_calc["payback_years"]
            }
    
    return recommendations

def display_enhanced_lead_output(context: Dict[str, Any], scenario_name: str):
    """Display the enhanced lead output format"""
    
    print(f"\n📊 ENHANCED LEAD OUTPUT FORMAT:")
    print("=" * 60)
    
    # Basic lead information
    print(f"🎯 Lead ID: {context['session_id']}")
    print(f"📅 Created: {datetime.now().isoformat()}")
    print(f"🏷️  Quality Tier: {context['quality_tier'].upper()}")
    print(f"⭐ Lead Score: {context['lead_score']}/100")
    
    # Extracted customer data
    print(f"\n👤 CUSTOMER DATA:")
    print("-" * 40)
    data = context["extracted_data"]
    for key, value in data.items():
        print(f"   {key}: {value}")
    
    # Enhanced NYC market data
    print(f"\n🗽 NYC MARKET DATA:")
    print("-" * 40)
    market_data = context["nyc_data"]
    for key, value in market_data.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Intelligent solar calculation
    if context["solar_calculation"]:
        print(f"\n⚡ INTELLIGENT SOLAR CALCULATION:")
        print("-" * 40)
        calc = context["solar_calculation"]
        for key, value in calc.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        print(f"     {sub_key}: {len(sub_value)} options")
                    else:
                        print(f"     {sub_key}: {sub_value}")
            elif isinstance(value, list):
                print(f"   {key}: {len(value)} items")
            else:
                if "cost" in key.lower() or "savings" in key.lower() or "value" in key.lower():
                    print(f"   {key}: ${value:,.2f}")
                else:
                    print(f"   {key}: {value}")
    
    # NYC expertise recommendations
    if context["nyc_expertise"]:
        print(f"\n🏛️  NYC EXPERTISE RECOMMENDATIONS:")
        print("-" * 40)
        expertise = context["nyc_expertise"]
        for key, value in expertise.items():
            if isinstance(value, list):
                print(f"   {key}: {', '.join(value) if value else 'None'}")
            else:
                print(f"   {key}: {value}")
    
    # Enhanced B2B recommendations
    if context["b2b_recommendations"]:
        print(f"\n💰 ENHANCED B2B RECOMMENDATIONS:")
        print("-" * 40)
        for rec in context["b2b_recommendations"]:
            print(f"   Platform: {rec['platform']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Expected Value: ${rec['expected_value']}")
            print(f"   Reason: {rec['reason']}")
            if rec.get("technical_details"):
                print(f"   Technical Details:")
                for tech_key, tech_value in rec["technical_details"].items():
                    print(f"     {tech_key}: {tech_value}")
            print()
    else:
        print(f"\n❌ NO B2B RECOMMENDATIONS (Unqualified Lead)")
    
    # Conversation summary
    print(f"\n💬 ENHANCED CONVERSATION SUMMARY:")
    print("-" * 40)
    print(f"   Messages: {len(context['messages'])}")
    print(f"   Stage: {context['conversation_stage']}")
    print(f"   Last Message: {context['messages'][-1]['user_message']}")
    print(f"   Bot Response: {context['messages'][-1]['bot_response'][:100]}...")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_enhanced_conversation_agent()

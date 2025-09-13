#!/usr/bin/env python3
"""
Test script to demonstrate the conversation agent output format
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_conversation_agent():
    """Test the conversation agent with realistic NYC customer scenarios"""
    
    print("🤖 Testing Aurum Solar Conversation Agent")
    print("=" * 60)
    
    # Test scenarios representing different NYC customer types
    test_scenarios = [
        {
            "name": "High-Value Lead - Park Slope Homeowner",
            "messages": [
                "Hi, I'm interested in getting solar for my home",
                "Yes, I own my home in Park Slope, Brooklyn",
                "My electric bill is around $380 per month with Con Edison",
                "I'm looking to install solar this year, preferably by summer",
                "My roof is in good condition, it's a flat roof",
                "I'm interested in the financial benefits and environmental impact"
            ]
        },
        {
            "name": "Standard Lead - Queens Homeowner", 
            "messages": [
                "I want to learn about solar panels",
                "I own a single-family home in Queens",
                "My PSEG bill is about $220 monthly",
                "I'm considering solar for next year",
                "I have some questions about the installation process"
            ]
        },
        {
            "name": "Price-Sensitive Lead - Bronx Homeowner",
            "messages": [
                "How much does solar cost?",
                "I own my home in the Bronx",
                "My bill is $180 per month",
                "I'm worried about the upfront costs",
                "Are there any financing options?"
            ]
        },
        {
            "name": "Renter Inquiry (Should be Disqualified)",
            "messages": [
                "I'm interested in solar energy",
                "I rent an apartment in Manhattan",
                "My electric bill is $120 per month",
                "Can I still get solar?"
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print("-" * 50)
        
        # Simulate conversation processing
        conversation_context = simulate_conversation_processing(scenario['messages'])
        
        # Display the lead output format
        display_lead_output(conversation_context, scenario['name'])

def simulate_conversation_processing(messages: list) -> Dict[str, Any]:
    """Simulate the conversation processing logic"""
    
    # Initialize conversation context
    context = {
        "session_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "messages": [],
        "extracted_data": {},
        "lead_score": 0,
        "quality_tier": "unqualified",
        "conversation_stage": "welcome",
        "nyc_data": {},
        "solar_calculation": None,
        "b2b_recommendations": []
    }
    
    # Process each message
    for i, message in enumerate(messages):
        context["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "bot_response": generate_bot_response(message, context)
        })
        
        # Extract data from message
        extracted = extract_data_from_message(message, context)
        context["extracted_data"].update(extracted)
        
        # Update conversation stage
        context["conversation_stage"] = determine_next_stage(context, i)
    
    # Calculate lead score and quality
    context["lead_score"] = calculate_lead_score(context)
    context["quality_tier"] = determine_quality_tier(context["lead_score"])
    
    # Generate NYC market data
    context["nyc_data"] = generate_nyc_market_data(context["extracted_data"])
    
    # Generate solar calculation if enough data
    if context["extracted_data"].get("bill_amount") and context["extracted_data"].get("zip_code"):
        context["solar_calculation"] = generate_solar_calculation(context)
    
    # Generate B2B recommendations
    context["b2b_recommendations"] = generate_b2b_recommendations(context)
    
    return context

def generate_bot_response(message: str, context: Dict[str, Any]) -> str:
    """Generate a realistic bot response"""
    
    message_lower = message.lower()
    
    if "interested" in message_lower or "solar" in message_lower:
        return "Great! I'd love to help you explore solar options for your NYC home. First, do you own your home?"
    
    elif "own" in message_lower and "yes" in message_lower:
        return "Perfect! Homeownership is the first step. What's your average monthly electric bill?"
    
    elif "bill" in message_lower and "$" in message:
        return "That's helpful information. What utility company do you use - Con Edison or PSEG?"
    
    elif "con edison" in message_lower or "con ed" in message_lower:
        return "Con Edison rates are among the highest in the country at around 31¢/kWh. Solar can provide significant savings. What's your timeline for installation?"
    
    elif "pseg" in message_lower:
        return "PSEG rates are around 27¢/kWh. Solar is definitely worth exploring. When are you thinking about installing solar?"
    
    elif "this year" in message_lower or "summer" in message_lower:
        return "Excellent timing! The 30% federal tax credit expires December 31st, 2025. What's your roof condition like?"
    
    elif "roof" in message_lower:
        return "Good to know. For NYC installations, we need to consider roof type, shading, and structural requirements. What's your zip code?"
    
    elif "cost" in message_lower or "price" in message_lower:
        return "I understand cost is a concern. With current incentives, most NYC homeowners see 75-87% cost reduction. Let me show you the numbers based on your situation."
    
    elif "rent" in message_lower:
        return "Unfortunately, solar installation requires homeownership. However, I can connect you with community solar programs or help you discuss solar with your landlord."
    
    else:
        return "That's great information. Let me gather a few more details to provide you with accurate solar recommendations for your NYC home."

def extract_data_from_message(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured data from user message"""
    
    extracted = {}
    message_lower = message.lower()
    
    # Extract bill amount
    if "$" in message:
        import re
        bill_match = re.search(r'\$(\d+)', message)
        if bill_match:
            extracted["bill_amount"] = float(bill_match.group(1))
    
    # Extract location information
    if "park slope" in message_lower:
        extracted["zip_code"] = "11215"
        extracted["borough"] = "Brooklyn"
        extracted["utility"] = "con_edison"
    elif "queens" in message_lower:
        extracted["zip_code"] = "11375"
        extracted["borough"] = "Queens" 
        extracted["utility"] = "pseg"
    elif "bronx" in message_lower:
        extracted["zip_code"] = "10462"
        extracted["borough"] = "Bronx"
        extracted["utility"] = "con_edison"
    elif "manhattan" in message_lower:
        extracted["zip_code"] = "10021"
        extracted["borough"] = "Manhattan"
        extracted["utility"] = "con_edison"
    
    # Extract homeownership status
    if "own" in message_lower and "yes" in message_lower:
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
    
    return extracted

def determine_next_stage(context: Dict[str, Any], message_index: int) -> str:
    """Determine conversation stage based on context"""
    
    if message_index == 0:
        return "welcome"
    elif context["extracted_data"].get("homeowner") is True:
        if context["extracted_data"].get("bill_amount"):
            return "qualification"
        else:
            return "discovery"
    elif context["extracted_data"].get("homeowner") is False:
        return "disqualification"
    else:
        return "discovery"

def calculate_lead_score(context: Dict[str, Any]) -> int:
    """Calculate lead score based on extracted data"""
    
    score = 0
    data = context["extracted_data"]
    
    # Homeowner status (40 points)
    if data.get("homeowner") is True:
        score += 40
    elif data.get("homeowner") is False:
        return 0  # Disqualified
    
    # Bill amount (30 points)
    bill = data.get("bill_amount", 0)
    if bill >= 300:
        score += 30
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
    
    # Location quality (10 points)
    if data.get("borough") in ["Manhattan", "Brooklyn"]:
        score += 10
    elif data.get("borough") in ["Queens", "Bronx"]:
        score += 5
    
    return min(score, 100)

def determine_quality_tier(score: int) -> str:
    """Determine quality tier based on score"""
    
    if score >= 85:
        return "premium"
    elif score >= 70:
        return "standard"
    elif score >= 50:
        return "basic"
    else:
        return "unqualified"

def generate_nyc_market_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate NYC market data based on location"""
    
    zip_code = extracted_data.get("zip_code", "10001")
    borough = extracted_data.get("borough", "Manhattan")
    utility = extracted_data.get("utility", "con_edison")
    
    # Mock NYC market data
    market_data = {
        "zip_code": zip_code,
        "borough": borough,
        "utility": utility,
        "electric_rate_per_kwh": 0.31 if utility == "con_edison" else 0.27,
        "solar_adoption_rate": 0.15 if borough in ["Manhattan", "Brooklyn"] else 0.12,
        "average_installation_cost_per_watt": 3.50,
        "incentives": {
            "federal_tax_credit": 0.30,
            "nyserda_rebate": 0.25,
            "nyc_property_tax_abatement": 0.20
        },
        "permit_timeline_days": 30,
        "competition_level": "high" if borough == "Manhattan" else "medium"
    }
    
    return market_data

def generate_solar_calculation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate solar calculation based on context"""
    
    data = context["extracted_data"]
    market_data = context["nyc_data"]
    
    bill_amount = data.get("bill_amount", 200)
    utility_rate = market_data["electric_rate_per_kwh"]
    
    # Calculate system size
    annual_usage = bill_amount * 12 / utility_rate
    system_size_kw = annual_usage / 1300  # NYC average irradiance
    
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
        }
    }
    
    return calculation

def generate_b2b_recommendations(context: Dict[str, Any]) -> list:
    """Generate B2B platform recommendations"""
    
    quality_tier = context["quality_tier"]
    lead_score = context["lead_score"]
    
    recommendations = []
    
    if quality_tier == "premium":
        recommendations = [
            {
                "platform": "SolarReviews",
                "priority": "immediate",
                "expected_value": 275,
                "reason": "Premium lead with high bill and 2025 timeline"
            },
            {
                "platform": "Modernize", 
                "priority": "immediate",
                "expected_value": 225,
                "reason": "High-quality lead for shared marketplace"
            }
        ]
    elif quality_tier == "standard":
        recommendations = [
            {
                "platform": "Modernize",
                "priority": "high", 
                "expected_value": 150,
                "reason": "Standard lead with good qualification"
            },
            {
                "platform": "SolarReviews",
                "priority": "medium",
                "expected_value": 125,
                "reason": "Standard lead for shared marketplace"
            }
        ]
    elif quality_tier == "basic":
        recommendations = [
            {
                "platform": "Modernize",
                "priority": "medium",
                "expected_value": 90,
                "reason": "Basic lead with adequate qualification"
            }
        ]
    
    return recommendations

def display_lead_output(context: Dict[str, Any], scenario_name: str):
    """Display the formatted lead output"""
    
    print(f"\n📊 LEAD OUTPUT FORMAT:")
    print("=" * 50)
    
    # Basic lead information
    print(f"🎯 Lead ID: {context['session_id']}")
    print(f"📅 Created: {datetime.now().isoformat()}")
    print(f"🏷️  Quality Tier: {context['quality_tier'].upper()}")
    print(f"⭐ Lead Score: {context['lead_score']}/100")
    
    # Extracted customer data
    print(f"\n👤 CUSTOMER DATA:")
    print("-" * 30)
    data = context["extracted_data"]
    for key, value in data.items():
        print(f"   {key}: {value}")
    
    # NYC market data
    print(f"\n🗽 NYC MARKET DATA:")
    print("-" * 30)
    market_data = context["nyc_data"]
    for key, value in market_data.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Solar calculation
    if context["solar_calculation"]:
        print(f"\n⚡ SOLAR CALCULATION:")
        print("-" * 30)
        calc = context["solar_calculation"]
        for key, value in calc.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: ${sub_value:,.2f}")
            else:
                if "cost" in key.lower() or "savings" in key.lower() or "value" in key.lower():
                    print(f"   {key}: ${value:,.2f}")
                else:
                    print(f"   {key}: {value}")
    
    # B2B recommendations
    if context["b2b_recommendations"]:
        print(f"\n💰 B2B RECOMMENDATIONS:")
        print("-" * 30)
        for rec in context["b2b_recommendations"]:
            print(f"   Platform: {rec['platform']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Expected Value: ${rec['expected_value']}")
            print(f"   Reason: {rec['reason']}")
            print()
    else:
        print(f"\n❌ NO B2B RECOMMENDATIONS (Unqualified Lead)")
    
    # Conversation summary
    print(f"\n💬 CONVERSATION SUMMARY:")
    print("-" * 30)
    print(f"   Messages: {len(context['messages'])}")
    print(f"   Stage: {context['conversation_stage']}")
    print(f"   Last Message: {context['messages'][-1]['user_message']}")
    print(f"   Bot Response: {context['messages'][-1]['bot_response']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_conversation_agent()

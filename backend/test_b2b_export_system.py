#!/usr/bin/env python3
"""
Test B2B Export System
Demonstrates comprehensive B2B lead export functionality
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_b2b_export_system():
    """Test the comprehensive B2B export system"""
    
    print("🚀 Testing Enhanced B2B Export System")
    print("=" * 70)
    
    # Test scenarios for different lead types
    test_scenarios = [
        {
            "name": "Premium Lead - Park Slope Brownstone",
            "lead_data": {
                "id": "premium_lead_001",
                "quality_tier": "premium",
                "customer": {
                    "name": "John Smith",
                    "email": "john.smith@email.com",
                    "phone": "+1-555-123-4567",
                    "address": {
                        "street": "123 7th Avenue",
                        "city": "Brooklyn",
                        "state": "NY",
                        "zip_code": "11215",
                        "borough": "Brooklyn"
                    }
                },
                "property": {
                    "homeowner_status": "owner",
                    "property_type": "brownstone",
                    "roof_type": "flat",
                    "zip_code": "11215",
                    "borough": "Brooklyn",
                    "electric_provider": "Con Edison",
                    "current_rate_per_kwh": 0.31
                },
                "solar_profile": {
                    "monthly_bill": 380.0,
                    "annual_usage_kwh": 14709,
                    "recommended_system_kw": 10.2,
                    "panel_count": 33,
                    "annual_savings": 4560.0,
                    "monthly_savings": 380.0,
                    "payback_years": 4.8,
                    "net_cost": 21949.88,
                    "roi_percentage": 419.4,
                    "urgency_factors": ["2025_tax_credit_deadline", "high_competition_area"]
                },
                "qualification_data": {
                    "conversation_quality_score": 95,
                    "engagement_level": "high",
                    "objections_resolved": ["cost_concerns", "historic_district"],
                    "timeline": "within_6_months",
                    "credit_indication": "excellent",
                    "qualification_confidence": 0.95,
                    "conversation_count": 8
                },
                "nyc_market_context": {
                    "electric_rate": 0.31,
                    "borough": "Brooklyn",
                    "competition_level": "medium",
                    "solar_adoption_rate": 0.18,
                    "incentive_value": 15750,
                    "special_considerations": ["Historic district - LPC approval required"]
                },
                "conversation_summary": {
                    "message_count": 8,
                    "engagement_level": "high",
                    "key_topics": ["solar", "cost", "timeline", "historic_district", "roof"],
                    "sentiment_score": 0.8,
                    "conversation_quality": "high"
                }
            }
        },
        {
            "name": "Standard Lead - Upper East Side Co-op",
            "lead_data": {
                "id": "standard_lead_001",
                "quality_tier": "standard",
                "customer": {
                    "name": "Sarah Johnson",
                    "email": "sarah.johnson@email.com",
                    "phone": "+1-555-987-6543",
                    "address": {
                        "street": "456 Park Avenue",
                        "city": "New York",
                        "state": "NY",
                        "zip_code": "10021",
                        "borough": "Manhattan"
                    }
                },
                "property": {
                    "homeowner_status": "owner",
                    "property_type": "co_op",
                    "roof_type": "unknown",
                    "zip_code": "10021",
                    "borough": "Manhattan",
                    "electric_provider": "Con Edison",
                    "current_rate_per_kwh": 0.31
                },
                "solar_profile": {
                    "monthly_bill": 320.0,
                    "annual_usage_kwh": 12387,
                    "recommended_system_kw": 8.5,
                    "panel_count": 28,
                    "annual_savings": 3840.0,
                    "monthly_savings": 320.0,
                    "payback_years": 6.2,
                    "net_cost": 18450.0,
                    "roi_percentage": 325.0,
                    "urgency_factors": ["2025_tax_credit_deadline"]
                },
                "qualification_data": {
                    "conversation_quality_score": 78,
                    "engagement_level": "medium",
                    "objections_resolved": ["co_op_approval"],
                    "timeline": "within_12_months",
                    "credit_indication": "good",
                    "qualification_confidence": 0.78,
                    "conversation_count": 5
                },
                "nyc_market_context": {
                    "electric_rate": 0.31,
                    "borough": "Manhattan",
                    "competition_level": "high",
                    "solar_adoption_rate": 0.12,
                    "incentive_value": 12750,
                    "special_considerations": ["Co-op board approval required"]
                },
                "conversation_summary": {
                    "message_count": 5,
                    "engagement_level": "medium",
                    "key_topics": ["solar", "co_op", "approval", "timeline"],
                    "sentiment_score": 0.6,
                    "conversation_quality": "medium"
                }
            }
        },
        {
            "name": "Basic Lead - Forest Hills Homeowner",
            "lead_data": {
                "id": "basic_lead_001",
                "quality_tier": "basic",
                "customer": {
                    "name": "Michael Chen",
                    "email": "michael.chen@email.com",
                    "phone": "+1-555-456-7890",
                    "address": {
                        "street": "789 Austin Street",
                        "city": "Forest Hills",
                        "state": "NY",
                        "zip_code": "11375",
                        "borough": "Queens"
                    }
                },
                "property": {
                    "homeowner_status": "owner",
                    "property_type": "single_family",
                    "roof_type": "sloped",
                    "zip_code": "11375",
                    "borough": "Queens",
                    "electric_provider": "PSEG",
                    "current_rate_per_kwh": 0.27
                },
                "solar_profile": {
                    "monthly_bill": 220.0,
                    "annual_usage_kwh": 9777,
                    "recommended_system_kw": 7.5,
                    "panel_count": 25,
                    "annual_savings": 2640.0,
                    "monthly_savings": 220.0,
                    "payback_years": 5.8,
                    "net_cost": 15427.35,
                    "roi_percentage": 327.8,
                    "urgency_factors": []
                },
                "qualification_data": {
                    "conversation_quality_score": 65,
                    "engagement_level": "medium",
                    "objections_resolved": ["cost_concerns"],
                    "timeline": "considering",
                    "credit_indication": "fair",
                    "qualification_confidence": 0.65,
                    "conversation_count": 4
                },
                "nyc_market_context": {
                    "electric_rate": 0.27,
                    "borough": "Queens",
                    "competition_level": "medium",
                    "solar_adoption_rate": 0.22,
                    "incentive_value": 9750,
                    "special_considerations": ["Standard residential permits"]
                },
                "conversation_summary": {
                    "message_count": 4,
                    "engagement_level": "medium",
                    "key_topics": ["solar", "cost", "process"],
                    "sentiment_score": 0.4,
                    "conversation_quality": "medium"
                }
            }
        }
    ]
    
    # Test B2B platform configurations
    platform_configs = {
        "solarreviews": {
            "name": "SolarReviews",
            "min_lead_score": 85,
            "price_per_lead": 250.0,
            "quality_tiers_accepted": ["premium"],
            "format_preference": "json",
            "exclusivity_required": True
        },
        "modernize": {
            "name": "Modernize",
            "min_lead_score": 70,
            "price_per_lead": 150.0,
            "quality_tiers_accepted": ["premium", "standard"],
            "format_preference": "csv",
            "exclusivity_required": False
        },
        "regional_nyc": {
            "name": "Regional NYC Platforms",
            "min_lead_score": 60,
            "price_per_lead": 125.0,
            "quality_tiers_accepted": ["premium", "standard", "basic"],
            "format_preference": "json",
            "exclusivity_required": False
        }
    }
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print("-" * 60)
        
        # Test lead enrichment and export
        lead_data = scenario['lead_data']
        test_lead_enrichment(lead_data)
        
        # Test B2B platform compatibility
        test_platform_compatibility(lead_data, platform_configs)
        
        # Test export format generation
        test_export_formats(lead_data, platform_configs)
        
        # Display export recommendations
        display_export_recommendations(lead_data, platform_configs)

def test_lead_enrichment(lead_data: Dict[str, Any]):
    """Test lead enrichment process"""
    
    print(f"\n🔍 LEAD ENRICHMENT TEST:")
    print("-" * 40)
    
    # Simulate enrichment process
    quality_tier = lead_data["quality_tier"]
    estimated_value = calculate_estimated_value(quality_tier, lead_data)
    confidence_score = calculate_confidence_score(lead_data)
    
    print(f"   Quality Tier: {quality_tier.upper()}")
    print(f"   Estimated B2B Value: ${estimated_value}")
    print(f"   Confidence Score: {confidence_score:.2f}")
    print(f"   Customer: {lead_data['customer']['name']}")
    print(f"   Property: {lead_data['property']['borough']} - {lead_data['property']['property_type']}")
    print(f"   Monthly Bill: ${lead_data['solar_profile']['monthly_bill']:.0f}")
    print(f"   Recommended System: {lead_data['solar_profile']['recommended_system_kw']:.1f}kW")
    print(f"   Annual Savings: ${lead_data['solar_profile']['annual_savings']:.0f}")
    print(f"   Payback Period: {lead_data['solar_profile']['payback_years']:.1f} years")

def test_platform_compatibility(lead_data: Dict[str, Any], platform_configs: Dict[str, Any]):
    """Test B2B platform compatibility"""
    
    print(f"\n🎯 PLATFORM COMPATIBILITY TEST:")
    print("-" * 40)
    
    quality_tier = lead_data["quality_tier"]
    estimated_value = calculate_estimated_value(quality_tier, lead_data)
    
    for platform_name, config in platform_configs.items():
        compatible = False
        reasons = []
        
        # Check quality tier acceptance
        if quality_tier in config["quality_tiers_accepted"]:
            compatible = True
        else:
            reasons.append(f"Quality tier {quality_tier} not accepted")
        
        # Check minimum lead score (simplified)
        lead_score = lead_data["qualification_data"]["conversation_quality_score"]
        if lead_score >= config["min_lead_score"]:
            compatible = True
        else:
            reasons.append(f"Lead score {lead_score} below minimum {config['min_lead_score']}")
        
        # Check value threshold
        if estimated_value >= config["price_per_lead"] * 0.8:
            compatible = True
        else:
            reasons.append(f"Value ${estimated_value} below threshold")
        
        status = "✅ COMPATIBLE" if compatible else "❌ INCOMPATIBLE"
        print(f"   {platform_name}: {status}")
        if reasons:
            print(f"     Reasons: {', '.join(reasons)}")
        print(f"     Price per lead: ${config['price_per_lead']}")
        print(f"     Format: {config['format_preference']}")

def test_export_formats(lead_data: Dict[str, Any], platform_configs: Dict[str, Any]):
    """Test export format generation"""
    
    print(f"\n📄 EXPORT FORMAT TEST:")
    print("-" * 40)
    
    quality_tier = lead_data["quality_tier"]
    
    for platform_name, config in platform_configs.items():
        if quality_tier in config["quality_tiers_accepted"]:
            format_type = config["format_preference"]
            
            if format_type == "json":
                export_data = generate_json_export(lead_data, platform_name)
                print(f"   {platform_name} (JSON):")
                print(f"     Keys: {list(export_data.keys())}")
                print(f"     Data size: {len(str(export_data))} characters")
            elif format_type == "csv":
                csv_data = generate_csv_export(lead_data, platform_name)
                print(f"   {platform_name} (CSV):")
                print(f"     Rows: {csv_data.count(chr(10)) + 1}")
                print(f"     Data size: {len(csv_data)} characters")

def display_export_recommendations(lead_data: Dict[str, Any], platform_configs: Dict[str, Any]):
    """Display export recommendations"""
    
    print(f"\n💰 EXPORT RECOMMENDATIONS:")
    print("-" * 40)
    
    quality_tier = lead_data["quality_tier"]
    estimated_value = calculate_estimated_value(quality_tier, lead_data)
    
    recommendations = []
    
    for platform_name, config in platform_configs.items():
        if quality_tier in config["quality_tiers_accepted"]:
            if estimated_value >= config["price_per_lead"] * 0.8:
                priority = "IMMEDIATE" if quality_tier == "premium" else "HIGH" if quality_tier == "standard" else "MEDIUM"
                recommendations.append({
                    "platform": platform_name,
                    "priority": priority,
                    "expected_value": config["price_per_lead"],
                    "format": config["format_preference"],
                    "exclusivity": config["exclusivity_required"]
                })
    
    # Sort by expected value
    recommendations.sort(key=lambda x: x["expected_value"], reverse=True)
    
    if recommendations:
        for rec in recommendations:
            exclusivity_text = " (Exclusive)" if rec["exclusivity"] else ""
            print(f"   Platform: {rec['platform']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Expected Value: ${rec['expected_value']}{exclusivity_text}")
            print(f"   Format: {rec['format']}")
            print()
    else:
        print("   No compatible platforms found")
        print("   Recommendation: Improve lead qualification or wait for better timing")

def calculate_estimated_value(quality_tier: str, lead_data: Dict[str, Any]) -> float:
    """Calculate estimated B2B value for the lead"""
    
    base_values = {
        "premium": 250.0,
        "standard": 150.0,
        "basic": 100.0,
        "unqualified": 0.0
    }
    
    base_value = base_values[quality_tier]
    
    # Adjust based on bill amount
    monthly_bill = lead_data["solar_profile"]["monthly_bill"]
    if monthly_bill >= 500:
        base_value *= 1.2
    elif monthly_bill >= 400:
        base_value *= 1.1
    elif monthly_bill >= 300:
        base_value *= 1.05
    
    # Adjust based on NYC location
    borough = lead_data["property"]["borough"]
    if borough == "Manhattan":
        base_value *= 1.15
    elif borough == "Brooklyn":
        base_value *= 1.1
    elif borough == "Queens":
        base_value *= 1.05
    
    return round(base_value, 2)

def calculate_confidence_score(lead_data: Dict[str, Any]) -> float:
    """Calculate confidence score for lead quality assessment"""
    
    factors = []
    
    # Data completeness (30%)
    data_completeness = 0.9  # Assume high completeness for test data
    factors.append(data_completeness * 0.3)
    
    # Conversation quality (25%)
    conversation_quality = lead_data["qualification_data"]["conversation_quality_score"] / 100
    factors.append(conversation_quality * 0.25)
    
    # Solar calculation confidence (25%)
    solar_confidence = 0.9  # Assume high confidence for test data
    factors.append(solar_confidence * 0.25)
    
    # Lead score factor (20%)
    lead_score_factor = lead_data["qualification_data"]["conversation_quality_score"] / 100
    factors.append(lead_score_factor * 0.2)
    
    return round(sum(factors), 2)

def generate_json_export(lead_data: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """Generate JSON export format"""
    
    return {
        "export_metadata": {
            "lead_id": lead_data["id"],
            "quality_tier": lead_data["quality_tier"],
            "estimated_value": calculate_estimated_value(lead_data["quality_tier"], lead_data),
            "exported_at": datetime.now().isoformat(),
            "platform": platform
        },
        "customer": lead_data["customer"],
        "property": lead_data["property"],
        "solar_profile": lead_data["solar_profile"],
        "qualification_data": lead_data["qualification_data"],
        "nyc_market_context": lead_data["nyc_market_context"],
        "conversation_summary": lead_data["conversation_summary"]
    }

def generate_csv_export(lead_data: Dict[str, Any], platform: str) -> str:
    """Generate CSV export format"""
    
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        "lead_id", "quality_tier", "estimated_value", "customer_name", "customer_email",
        "customer_phone", "property_address", "property_zip", "property_borough",
        "monthly_bill", "homeowner_status", "timeline", "engagement_level",
        "recommended_system_kw", "annual_savings", "payback_years"
    ]
    writer.writerow(headers)
    
    # Write data
    row = [
        lead_data["id"],
        lead_data["quality_tier"],
        calculate_estimated_value(lead_data["quality_tier"], lead_data),
        lead_data["customer"]["name"],
        lead_data["customer"]["email"],
        lead_data["customer"]["phone"],
        lead_data["customer"]["address"]["street"],
        lead_data["property"]["zip_code"],
        lead_data["property"]["borough"],
        lead_data["solar_profile"]["monthly_bill"],
        lead_data["property"]["homeowner_status"],
        lead_data["qualification_data"]["timeline"],
        lead_data["conversation_summary"]["engagement_level"],
        lead_data["solar_profile"]["recommended_system_kw"],
        lead_data["solar_profile"]["annual_savings"],
        lead_data["solar_profile"]["payback_years"]
    ]
    writer.writerow(row)
    
    return output.getvalue()

if __name__ == "__main__":
    test_b2b_export_system()

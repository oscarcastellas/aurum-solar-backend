"""
Comprehensive Testing and Validation Framework for Aurum Solar Conversational Agent
Tests solar calculations, conversation intelligence, lead scoring, and revenue optimization
"""

import pytest
import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass, asdict
import requests
from sqlalchemy.orm import Session

from app.services.conversation_agent import ConversationAgent
from app.services.solar_calculation_engine import SolarCalculationEngine
from app.services.conversation_intelligence_engine import ConversationIntelligenceEngine
from app.services.revenue_optimization_system import RevenueOptimizationSystem
from app.services.nyc_expertise_database import NYCExpertiseDatabase


@dataclass
class TestScenario:
    """Test scenario configuration"""
    scenario_id: str
    name: str
    description: str
    customer_profile: Dict[str, Any]
    conversation_flow: List[Dict[str, str]]
    expected_outcomes: Dict[str, Any]
    validation_criteria: Dict[str, Any]


@dataclass
class TestResult:
    """Test result data"""
    scenario_id: str
    test_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    errors: List[str]
    recommendations: List[str]
    timestamp: datetime


@dataclass
class ValidationMetrics:
    """Comprehensive validation metrics"""
    technical_accuracy: float
    conversation_quality: float
    lead_scoring_accuracy: float
    revenue_optimization: float
    performance_score: float
    overall_score: float
    test_results: List[TestResult]
    benchmark_comparison: Dict[str, float]


class ComprehensiveAgentValidator:
    """Comprehensive validation framework for the conversational agent"""
    
    def __init__(self, db: Session, redis_client):
        self.db = db
        self.redis_client = redis_client
        self.test_scenarios = self._load_test_scenarios()
        self.benchmark_data = self._load_benchmark_data()
        self.validation_results = []
        
        # Initialize services
        self.conversation_agent = ConversationAgent(db)
        self.solar_calculator = SolarCalculationEngine(db)
        self.intelligence_engine = ConversationIntelligenceEngine(db)
        self.revenue_system = RevenueOptimizationSystem(db, redis_client)
        self.nyc_expertise = NYCExpertiseDatabase()
    
    def _load_test_scenarios(self) -> List[TestScenario]:
        """Load comprehensive test scenarios"""
        
        return [
            # High-Value Lead Scenario
            TestScenario(
                scenario_id="high_value_park_slope",
                name="Park Slope Premium Lead",
                description="High-value homeowner in premium NYC neighborhood",
                customer_profile={
                    "homeowner_verified": True,
                    "bill_amount": 380.0,
                    "zip_code": "11215",
                    "borough": "brooklyn",
                    "neighborhood": "park_slope",
                    "home_type": "brownstone",
                    "timeline": "2025 spring",
                    "credit_indicators": ["financing", "pre_approved"],
                    "decision_maker": True,
                    "income_level": "high"
                },
                conversation_flow=[
                    {"user": "I'm interested in solar for my brownstone in Park Slope", "intent": "interest"},
                    {"user": "My Con Ed bill is around $380 monthly", "intent": "bill_disclosure"},
                    {"user": "What kind of savings could I expect?", "intent": "savings_inquiry"},
                    {"user": "I'm concerned about the installation process", "intent": "objection"},
                    {"user": "When would be the best time to install?", "intent": "timeline"}
                ],
                expected_outcomes={
                    "lead_quality_tier": "premium",
                    "revenue_potential": {"min": 200.0, "max": 300.0},
                    "system_recommendation": {"size_range": [7.0, 9.0], "unit": "kW"},
                    "annual_savings": {"min": 2800.0, "max": 3500.0},
                    "roi_payback": {"min": 5.0, "max": 7.0, "unit": "years"},
                    "buyer_routing": "solarreviews",
                    "conversion_probability": {"min": 0.8, "max": 1.0}
                },
                validation_criteria={
                    "technical_accuracy": 0.95,
                    "conversation_quality": 0.9,
                    "lead_scoring_accuracy": 0.95,
                    "revenue_optimization": 0.9
                }
            ),
            
            # Standard Lead Scenario
            TestScenario(
                scenario_id="standard_queens",
                name="Queens Standard Lead",
                description="Standard homeowner in Queens with good potential",
                customer_profile={
                    "homeowner_verified": True,
                    "bill_amount": 220.0,
                    "zip_code": "11375",
                    "borough": "queens",
                    "neighborhood": "forest_hills",
                    "home_type": "single_family",
                    "timeline": "2025 summer",
                    "credit_indicators": ["financing"],
                    "decision_maker": True,
                    "income_level": "medium"
                },
                conversation_flow=[
                    {"user": "I'm considering solar for my house in Forest Hills", "intent": "interest"},
                    {"user": "My PSEG bill is about $220", "intent": "bill_disclosure"},
                    {"user": "How long does installation take?", "intent": "process_inquiry"},
                    {"user": "What about permits and paperwork?", "intent": "objection"},
                    {"user": "This sounds good, what's next?", "intent": "interest"}
                ],
                expected_outcomes={
                    "lead_quality_tier": "standard",
                    "revenue_potential": {"min": 125.0, "max": 175.0},
                    "system_recommendation": {"size_range": [5.0, 7.0], "unit": "kW"},
                    "annual_savings": {"min": 1800.0, "max": 2200.0},
                    "roi_payback": {"min": 6.0, "max": 8.0, "unit": "years"},
                    "buyer_routing": "modernize",
                    "conversion_probability": {"min": 0.6, "max": 0.8}
                },
                validation_criteria={
                    "technical_accuracy": 0.92,
                    "conversation_quality": 0.85,
                    "lead_scoring_accuracy": 0.9,
                    "revenue_optimization": 0.85
                }
            ),
            
            # Objection Handling Scenario
            TestScenario(
                scenario_id="objection_manhattan_coop",
                name="Manhattan Co-op Objection Handling",
                description="Co-op owner with multiple objections requiring expert handling",
                customer_profile={
                    "homeowner_verified": True,
                    "bill_amount": 320.0,
                    "zip_code": "10023",
                    "borough": "manhattan",
                    "neighborhood": "upper_west_side",
                    "home_type": "co_op",
                    "timeline": "considering",
                    "credit_indicators": [],
                    "decision_maker": False,
                    "income_level": "high",
                    "objections": ["cost", "roof_access", "coop_approval", "aesthetics"]
                },
                conversation_flow=[
                    {"user": "I'm interested in solar but worried about the cost", "intent": "objection"},
                    {"user": "My co-op board is very strict about roof modifications", "intent": "objection"},
                    {"user": "The panels might look ugly on our building", "intent": "objection"},
                    {"user": "How do we handle the co-op approval process?", "intent": "process_inquiry"},
                    {"user": "What financing options are available?", "intent": "financing_inquiry"}
                ],
                expected_outcomes={
                    "lead_quality_tier": "standard",
                    "revenue_potential": {"min": 150.0, "max": 200.0},
                    "objection_resolution_rate": {"min": 0.8, "max": 1.0},
                    "technical_expertise_demonstrated": True,
                    "coop_specific_guidance": True,
                    "financing_options_provided": True,
                    "conversion_probability": {"min": 0.5, "max": 0.7}
                },
                validation_criteria={
                    "technical_accuracy": 0.9,
                    "conversation_quality": 0.95,
                    "objection_handling": 0.9,
                    "expertise_demonstration": 0.95
                }
            ),
            
            # Edge Case: Renter
            TestScenario(
                scenario_id="edge_case_renter",
                name="Renter Disqualification",
                description="Renter interested in solar - should be politely disqualified",
                customer_profile={
                    "homeowner_verified": False,
                    "bill_amount": 250.0,
                    "zip_code": "10016",
                    "borough": "manhattan",
                    "neighborhood": "murray_hill",
                    "home_type": "apartment",
                    "rental_status": True
                },
                conversation_flow=[
                    {"user": "I'm interested in solar for my apartment", "intent": "interest"},
                    {"user": "My electric bill is $250 monthly", "intent": "bill_disclosure"},
                    {"user": "Can I install solar as a renter?", "intent": "qualification_inquiry"}
                ],
                expected_outcomes={
                    "lead_quality_tier": "unqualified",
                    "revenue_potential": 0.0,
                    "polite_disqualification": True,
                    "alternative_suggestions": True,
                    "educational_value": True,
                    "conversion_probability": 0.0
                },
                validation_criteria={
                    "polite_handling": 0.95,
                    "educational_value": 0.8,
                    "alternative_suggestions": 0.9
                }
            ),
            
            # Edge Case: Very High Bill
            TestScenario(
                scenario_id="edge_case_high_bill",
                name="Very High Bill Commercial",
                description="Very high bill indicating possible commercial property",
                customer_profile={
                    "homeowner_verified": True,
                    "bill_amount": 850.0,
                    "zip_code": "10018",
                    "borough": "manhattan",
                    "neighborhood": "midtown_west",
                    "home_type": "mixed_use",
                    "commercial_indicator": True
                },
                conversation_flow=[
                    {"user": "I'm interested in solar for my property", "intent": "interest"},
                    {"user": "My electric bill is around $850 monthly", "intent": "bill_disclosure"},
                    {"user": "It's a mixed-use building", "intent": "property_disclosure"}
                ],
                expected_outcomes={
                    "lead_quality_tier": "premium",
                    "revenue_potential": {"min": 300.0, "max": 500.0},
                    "commercial_consideration": True,
                    "system_recommendation": {"size_range": [15.0, 25.0], "unit": "kW"},
                    "specialized_guidance": True,
                    "conversion_probability": {"min": 0.7, "max": 0.9}
                },
                validation_criteria={
                    "commercial_recognition": 0.9,
                    "specialized_guidance": 0.85,
                    "technical_accuracy": 0.9
                }
            ),
            
            # Edge Case: Historic District
            TestScenario(
                scenario_id="edge_case_historic_district",
                name="Historic District Restrictions",
                description="Historic district with installation restrictions",
                customer_profile={
                    "homeowner_verified": True,
                    "bill_amount": 280.0,
                    "zip_code": "10013",
                    "borough": "manhattan",
                    "neighborhood": "soho",
                    "home_type": "historic_building",
                    "historic_district": True,
                    "landmark_status": True
                },
                conversation_flow=[
                    {"user": "I'm interested in solar for my SoHo loft", "intent": "interest"},
                    {"user": "My building is in a historic district", "intent": "restriction_disclosure"},
                    {"user": "Are there special requirements for historic buildings?", "intent": "process_inquiry"}
                ],
                expected_outcomes={
                    "lead_quality_tier": "standard",
                    "revenue_potential": {"min": 150.0, "max": 200.0},
                    "historic_restrictions_addressed": True,
                    "specialized_guidance": True,
                    "permit_process_explained": True,
                    "conversion_probability": {"min": 0.6, "max": 0.8}
                },
                validation_criteria={
                    "historic_knowledge": 0.95,
                    "specialized_guidance": 0.9,
                    "permit_expertise": 0.9
                }
            )
        ]
    
    def _load_benchmark_data(self) -> Dict[str, Any]:
        """Load benchmark data for validation"""
        
        return {
            "industry_solar_calculators": {
                "nrel_pvwatts": "https://pvwatts.nrel.gov/",
                "solar_reviews": "https://www.solarreviews.com/calculator",
                "energysage": "https://www.energysage.com/solar/"
            },
            "nyc_market_data": {
                "average_system_cost_per_watt": 3.50,
                "con_edison_rate": 0.31,
                "pseg_rate": 0.27,
                "average_irradiance": 1300,
                "federal_itc": 0.30,
                "nyserda_rebate_per_kw": 400
            },
            "performance_benchmarks": {
                "conversation_completion_rate": 0.75,
                "qualification_rate": 0.60,
                "average_lead_value": 150.0,
                "technical_accuracy_threshold": 0.95,
                "response_time_threshold": 2.0,
                "b2b_acceptance_rate": 0.90
            }
        }
    
    async def run_comprehensive_validation(self) -> ValidationMetrics:
        """Run comprehensive validation of the conversational agent"""
        
        print("🚀 Starting Comprehensive Agent Validation...")
        
        test_results = []
        
        # 1. Solar Calculation Accuracy Testing
        print("\n📊 Testing Solar Calculation Accuracy...")
        solar_results = await self._test_solar_calculation_accuracy()
        test_results.extend(solar_results)
        
        # 2. Conversation Quality Validation
        print("\n💬 Testing Conversation Quality...")
        conversation_results = await self._test_conversation_quality()
        test_results.extend(conversation_results)
        
        # 3. Lead Scoring Validation
        print("\n🎯 Testing Lead Scoring Accuracy...")
        scoring_results = await self._test_lead_scoring_accuracy()
        test_results.extend(scoring_results)
        
        # 4. Revenue Optimization Testing
        print("\n💰 Testing Revenue Optimization...")
        revenue_results = await self._test_revenue_optimization()
        test_results.extend(revenue_results)
        
        # 5. Integration Testing
        print("\n🔗 Testing System Integration...")
        integration_results = await self._test_system_integration()
        test_results.extend(integration_results)
        
        # 6. Performance Testing
        print("\n⚡ Testing Performance...")
        performance_results = await self._test_performance()
        test_results.extend(performance_results)
        
        # Calculate overall metrics
        validation_metrics = self._calculate_validation_metrics(test_results)
        
        print(f"\n✅ Validation Complete! Overall Score: {validation_metrics.overall_score:.1%}")
        
        return validation_metrics
    
    async def _test_solar_calculation_accuracy(self) -> List[TestResult]:
        """Test solar calculation accuracy against industry standards"""
        
        results = []
        
        # Test system sizing calculations
        test_cases = [
            {
                "monthly_bill": 300.0,
                "utility": "con_edison",
                "zip_code": "10021",
                "expected_size_range": (6.0, 8.0)
            },
            {
                "monthly_bill": 200.0,
                "utility": "pseg",
                "zip_code": "11375",
                "expected_size_range": (4.0, 6.0)
            },
            {
                "monthly_bill": 500.0,
                "utility": "con_edison",
                "zip_code": "11215",
                "expected_size_range": (10.0, 12.0)
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                # Calculate system size
                calculation_result = await self.solar_calculator.calculate_system_size(
                    monthly_bill=test_case["monthly_bill"],
                    utility=test_case["utility"],
                    zip_code=test_case["zip_code"]
                )
                
                # Validate against expected range
                system_size = calculation_result.get("recommended_size", 0)
                expected_min, expected_max = test_case["expected_size_range"]
                
                accuracy_score = 1.0 if expected_min <= system_size <= expected_max else 0.0
                
                results.append(TestResult(
                    scenario_id=f"solar_sizing_{i}",
                    test_name="System Sizing Accuracy",
                    passed=accuracy_score >= 0.95,
                    score=accuracy_score,
                    details={
                        "calculated_size": system_size,
                        "expected_range": test_case["expected_size_range"],
                        "test_case": test_case
                    },
                    errors=[] if accuracy_score >= 0.95 else [f"Size {system_size}kW outside expected range {expected_min}-{expected_max}kW"],
                    recommendations=[] if accuracy_score >= 0.95 else ["Review system sizing algorithm"],
                    timestamp=datetime.utcnow()
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_id=f"solar_sizing_{i}",
                    test_name="System Sizing Accuracy",
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    recommendations=["Fix system sizing calculation error"],
                    timestamp=datetime.utcnow()
                ))
        
        # Test incentive calculations
        incentive_test_cases = [
            {
                "system_cost": 25000.0,
                "expected_federal_itc": 7500.0,
                "expected_nyserda_rebate": 2800.0
            },
            {
                "system_cost": 18000.0,
                "expected_federal_itc": 5400.0,
                "expected_nyserda_rebate": 2000.0
            }
        ]
        
        for i, test_case in enumerate(incentive_test_cases):
            try:
                # Calculate incentives
                incentive_result = await self.solar_calculator.calculate_incentives(
                    system_cost=test_case["system_cost"]
                )
                
                federal_itc = incentive_result.get("federal_itc", 0)
                nyserda_rebate = incentive_result.get("nyserda_rebate", 0)
                
                federal_accuracy = 1.0 if abs(federal_itc - test_case["expected_federal_itc"]) < 100 else 0.0
                nyserda_accuracy = 1.0 if abs(nyserda_rebate - test_case["expected_nyserda_rebate"]) < 100 else 0.0
                
                overall_accuracy = (federal_accuracy + nyserda_accuracy) / 2
                
                results.append(TestResult(
                    scenario_id=f"incentive_calculation_{i}",
                    test_name="Incentive Calculation Accuracy",
                    passed=overall_accuracy >= 0.95,
                    score=overall_accuracy,
                    details={
                        "calculated_federal_itc": federal_itc,
                        "expected_federal_itc": test_case["expected_federal_itc"],
                        "calculated_nyserda_rebate": nyserda_rebate,
                        "expected_nyserda_rebate": test_case["expected_nyserda_rebate"]
                    },
                    errors=[] if overall_accuracy >= 0.95 else ["Incentive calculations inaccurate"],
                    recommendations=[] if overall_accuracy >= 0.95 else ["Review incentive calculation formulas"],
                    timestamp=datetime.utcnow()
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_id=f"incentive_calculation_{i}",
                    test_name="Incentive Calculation Accuracy",
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    recommendations=["Fix incentive calculation error"],
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _test_conversation_quality(self) -> List[TestResult]:
        """Test conversation quality with realistic scenarios"""
        
        results = []
        
        for scenario in self.test_scenarios:
            try:
                # Simulate conversation
                conversation_results = await self._simulate_conversation(scenario)
                
                # Evaluate conversation quality
                quality_score = self._evaluate_conversation_quality(conversation_results, scenario)
                
                results.append(TestResult(
                    scenario_id=scenario.scenario_id,
                    test_name="Conversation Quality",
                    passed=quality_score >= scenario.validation_criteria.get("conversation_quality", 0.8),
                    score=quality_score,
                    details={
                        "scenario": scenario.name,
                        "conversation_results": conversation_results,
                        "quality_factors": self._analyze_conversation_quality_factors(conversation_results)
                    },
                    errors=[] if quality_score >= 0.8 else ["Conversation quality below threshold"],
                    recommendations=[] if quality_score >= 0.8 else ["Improve conversation flow and responses"],
                    timestamp=datetime.utcnow()
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_id=scenario.scenario_id,
                    test_name="Conversation Quality",
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    recommendations=["Fix conversation processing error"],
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _test_lead_scoring_accuracy(self) -> List[TestResult]:
        """Test lead scoring accuracy with known scenarios"""
        
        results = []
        
        for scenario in self.test_scenarios:
            try:
                # Generate lead score
                lead_score = await self.revenue_system.lead_scoring_engine.calculate_real_time_score(
                    session_id=f"test_{scenario.scenario_id}",
                    conversation_context=scenario.customer_profile,
                    conversation_history=[]
                )
                
                # Validate against expected outcomes
                expected_tier = scenario.expected_outcomes.get("lead_quality_tier", "basic")
                actual_tier = lead_score.quality_tier.value
                
                tier_accuracy = 1.0 if actual_tier == expected_tier else 0.0
                
                # Check revenue potential range
                expected_revenue = scenario.expected_outcomes.get("revenue_potential", {"min": 0, "max": 100})
                actual_revenue = lead_score.revenue_potential
                
                revenue_accuracy = 1.0 if (
                    expected_revenue["min"] <= actual_revenue <= expected_revenue["max"]
                ) else 0.0
                
                overall_accuracy = (tier_accuracy + revenue_accuracy) / 2
                
                results.append(TestResult(
                    scenario_id=scenario.scenario_id,
                    test_name="Lead Scoring Accuracy",
                    passed=overall_accuracy >= scenario.validation_criteria.get("lead_scoring_accuracy", 0.9),
                    score=overall_accuracy,
                    details={
                        "expected_tier": expected_tier,
                        "actual_tier": actual_tier,
                        "expected_revenue": expected_revenue,
                        "actual_revenue": actual_revenue,
                        "total_score": lead_score.total_score,
                        "scoring_factors": lead_score.scoring_factors
                    },
                    errors=[] if overall_accuracy >= 0.9 else ["Lead scoring inaccurate"],
                    recommendations=[] if overall_accuracy >= 0.9 else ["Review lead scoring algorithm"],
                    timestamp=datetime.utcnow()
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_id=scenario.scenario_id,
                    test_name="Lead Scoring Accuracy",
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    recommendations=["Fix lead scoring error"],
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _test_revenue_optimization(self) -> List[TestResult]:
        """Test revenue optimization algorithms"""
        
        results = []
        
        # Test B2B routing optimization
        routing_test_cases = [
            {
                "lead_quality_score": 85,
                "expected_buyer_tier": "premium",
                "expected_price_range": {"min": 200.0, "max": 300.0}
            },
            {
                "lead_quality_score": 70,
                "expected_buyer_tier": "standard",
                "expected_price_range": {"min": 125.0, "max": 175.0}
            },
            {
                "lead_quality_score": 50,
                "expected_buyer_tier": "basic",
                "expected_price_range": {"min": 75.0, "max": 125.0}
            }
        ]
        
        for i, test_case in enumerate(routing_test_cases):
            try:
                # Test routing optimization
                routing_decision = await self.revenue_system.b2b_value_optimizer.optimize_buyer_routing(
                    lead_id=f"test_lead_{i}",
                    session_id=f"test_session_{i}",
                    lead_quality_score=test_case["lead_quality_score"],
                    conversation_context={"borough": "manhattan", "bill_amount": 300.0}
                )
                
                # Validate routing decision
                price_accuracy = 1.0 if (
                    test_case["expected_price_range"]["min"] <= routing_decision.price_per_lead <= test_case["expected_price_range"]["max"]
                ) else 0.0
                
                results.append(TestResult(
                    scenario_id=f"revenue_routing_{i}",
                    test_name="B2B Routing Optimization",
                    passed=price_accuracy >= 0.9,
                    score=price_accuracy,
                    details={
                        "routing_decision": asdict(routing_decision),
                        "expected_price_range": test_case["expected_price_range"],
                        "actual_price": routing_decision.price_per_lead
                    },
                    errors=[] if price_accuracy >= 0.9 else ["Routing price outside expected range"],
                    recommendations=[] if price_accuracy >= 0.9 else ["Review B2B routing algorithm"],
                    timestamp=datetime.utcnow()
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_id=f"revenue_routing_{i}",
                    test_name="B2B Routing Optimization",
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    recommendations=["Fix B2B routing error"],
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _test_system_integration(self) -> List[TestResult]:
        """Test end-to-end system integration"""
        
        results = []
        
        # Test complete conversation flow
        for scenario in self.test_scenarios[:3]:  # Test first 3 scenarios
            try:
                # Simulate complete conversation with revenue optimization
                conversation_context = scenario.customer_profile.copy()
                conversation_history = []
                
                for message in scenario.conversation_flow:
                    # Process message through revenue optimization system
                    response = await self.revenue_system.process_conversation_for_revenue_optimization(
                        session_id=f"integration_test_{scenario.scenario_id}",
                        message=message["user"],
                        conversation_context=conversation_context,
                        conversation_history=conversation_history
                    )
                    
                    # Add to conversation history
                    conversation_history.append({
                        "user": message["user"],
                        "bot": response.get("content", ""),
                        "revenue_data": response.get("revenue_optimization", {})
                    })
                
                # Validate integration
                integration_score = self._evaluate_integration_quality(conversation_history, scenario)
                
                results.append(TestResult(
                    scenario_id=scenario.scenario_id,
                    test_name="System Integration",
                    passed=integration_score >= 0.85,
                    score=integration_score,
                    details={
                        "conversation_history": conversation_history,
                        "integration_factors": self._analyze_integration_factors(conversation_history)
                    },
                    errors=[] if integration_score >= 0.85 else ["Integration quality below threshold"],
                    recommendations=[] if integration_score >= 0.85 else ["Improve system integration"],
                    timestamp=datetime.utcnow()
                ))
                
            except Exception as e:
                results.append(TestResult(
                    scenario_id=scenario.scenario_id,
                    test_name="System Integration",
                    passed=False,
                    score=0.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    recommendations=["Fix system integration error"],
                    timestamp=datetime.utcnow()
                ))
        
        return results
    
    async def _test_performance(self) -> List[TestResult]:
        """Test system performance under load"""
        
        results = []
        
        # Test response time
        start_time = datetime.utcnow()
        
        try:
            # Simulate concurrent conversations
            tasks = []
            for i in range(10):  # 10 concurrent conversations
                task = self.revenue_system.process_conversation_for_revenue_optimization(
                    session_id=f"perf_test_{i}",
                    message="I'm interested in solar for my home",
                    conversation_context={
                        "homeowner_verified": True,
                        "bill_amount": 300.0,
                        "zip_code": "10021",
                        "borough": "manhattan"
                    },
                    conversation_history=[]
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            responses = await asyncio.gather(*tasks)
            
            end_time = datetime.utcnow()
            total_time = (end_time - start_time).total_seconds()
            avg_response_time = total_time / len(responses)
            
            performance_score = 1.0 if avg_response_time <= 2.0 else max(0.0, 1.0 - (avg_response_time - 2.0) / 2.0)
            
            results.append(TestResult(
                scenario_id="performance_test",
                test_name="Response Time Performance",
                passed=performance_score >= 0.8,
                score=performance_score,
                details={
                    "total_time": total_time,
                    "avg_response_time": avg_response_time,
                    "concurrent_conversations": len(responses),
                    "threshold": 2.0
                },
                errors=[] if performance_score >= 0.8 else [f"Average response time {avg_response_time:.2f}s exceeds 2s threshold"],
                recommendations=[] if performance_score >= 0.8 else ["Optimize response time performance"],
                timestamp=datetime.utcnow()
            ))
            
        except Exception as e:
            results.append(TestResult(
                scenario_id="performance_test",
                test_name="Response Time Performance",
                passed=False,
                score=0.0,
                details={"error": str(e)},
                errors=[str(e)],
                recommendations=["Fix performance testing error"],
                timestamp=datetime.utcnow()
            ))
        
        return results
    
    async def _simulate_conversation(self, scenario: TestScenario) -> Dict[str, Any]:
        """Simulate a conversation for testing"""
        
        conversation_results = {
            "messages": [],
            "response_quality": [],
            "technical_accuracy": [],
            "expertise_demonstrated": [],
            "personalization_score": []
        }
        
        for message in scenario.conversation_flow:
            try:
                # Process message through conversation agent
                response = await self.conversation_agent.process_intelligent_conversation(
                    message=message["user"],
                    session_id=f"test_{scenario.scenario_id}",
                    lead_id=f"test_lead_{scenario.scenario_id}"
                )
                
                conversation_results["messages"].append({
                    "user": message["user"],
                    "bot": response.get("content", ""),
                    "intent": message.get("intent", "")
                })
                
                # Evaluate response quality
                quality_factors = self._analyze_response_quality(response, scenario)
                conversation_results["response_quality"].append(quality_factors)
                
            except Exception as e:
                conversation_results["messages"].append({
                    "user": message["user"],
                    "bot": f"Error: {str(e)}",
                    "error": True
                })
        
        return conversation_results
    
    def _evaluate_conversation_quality(self, conversation_results: Dict[str, Any], scenario: TestScenario) -> float:
        """Evaluate conversation quality"""
        
        if not conversation_results["messages"]:
            return 0.0
        
        quality_factors = []
        
        # Response relevance
        relevant_responses = sum(1 for msg in conversation_results["messages"] 
                               if not msg.get("error") and len(msg["bot"]) > 10)
        relevance_score = relevant_responses / len(conversation_results["messages"])
        quality_factors.append(relevance_score)
        
        # Technical accuracy (if applicable)
        if scenario.customer_profile.get("bill_amount"):
            technical_responses = sum(1 for quality in conversation_results["response_quality"]
                                    if quality.get("technical_accuracy", 0) > 0.8)
            technical_score = technical_responses / len(conversation_results["response_quality"]) if conversation_results["response_quality"] else 0.5
            quality_factors.append(technical_score)
        
        # Expertise demonstration
        expertise_responses = sum(1 for quality in conversation_results["response_quality"]
                                if quality.get("expertise_demonstrated", False))
        expertise_score = expertise_responses / len(conversation_results["response_quality"]) if conversation_results["response_quality"] else 0.5
        quality_factors.append(expertise_score)
        
        # Personalization (NYC-specific content)
        personalized_responses = sum(1 for quality in conversation_results["response_quality"]
                                   if quality.get("nyc_specific", False))
        personalization_score = personalized_responses / len(conversation_results["response_quality"]) if conversation_results["response_quality"] else 0.5
        quality_factors.append(personalization_score)
        
        return np.mean(quality_factors)
    
    def _analyze_response_quality(self, response: Dict[str, Any], scenario: TestScenario) -> Dict[str, Any]:
        """Analyze response quality factors"""
        
        content = response.get("content", "").lower()
        
        return {
            "technical_accuracy": 0.8 if any(term in content for term in ["kw", "kwh", "system", "solar"]) else 0.5,
            "expertise_demonstrated": any(term in content for term in ["nyc", "manhattan", "brooklyn", "con ed", "pseg"]),
            "nyc_specific": any(term in content for term in ["nyc", "new york", "con edison", "pseg", "nyserda"]),
            "personalization": any(term in content for term in [scenario.customer_profile.get("borough", ""), scenario.customer_profile.get("neighborhood", "")])
        }
    
    def _evaluate_integration_quality(self, conversation_history: List[Dict[str, Any]], scenario: TestScenario) -> float:
        """Evaluate system integration quality"""
        
        if not conversation_history:
            return 0.0
        
        integration_factors = []
        
        # Revenue data integration
        revenue_integrated = sum(1 for msg in conversation_history 
                               if msg.get("revenue_data", {}).get("lead_score"))
        revenue_score = revenue_integrated / len(conversation_history)
        integration_factors.append(revenue_score)
        
        # Conversation flow continuity
        flow_score = 1.0 if len(conversation_history) == len(scenario.conversation_flow) else 0.5
        integration_factors.append(flow_score)
        
        # Response quality consistency
        quality_responses = sum(1 for msg in conversation_history 
                              if msg.get("bot") and len(msg["bot"]) > 20)
        quality_score = quality_responses / len(conversation_history)
        integration_factors.append(quality_score)
        
        return np.mean(integration_factors)
    
    def _analyze_integration_factors(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze integration factors"""
        
        return {
            "total_messages": len(conversation_history),
            "revenue_data_present": sum(1 for msg in conversation_history if msg.get("revenue_data")),
            "avg_response_length": np.mean([len(msg.get("bot", "")) for msg in conversation_history]),
            "error_count": sum(1 for msg in conversation_history if msg.get("error"))
        }
    
    def _analyze_conversation_quality_factors(self, conversation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation quality factors"""
        
        return {
            "total_messages": len(conversation_results["messages"]),
            "relevant_responses": sum(1 for msg in conversation_results["messages"] if not msg.get("error")),
            "avg_technical_accuracy": np.mean([q.get("technical_accuracy", 0) for q in conversation_results["response_quality"]]),
            "expertise_demonstrated": sum(1 for q in conversation_results["response_quality"] if q.get("expertise_demonstrated")),
            "nyc_personalization": sum(1 for q in conversation_results["response_quality"] if q.get("nyc_specific"))
        }
    
    def _calculate_validation_metrics(self, test_results: List[TestResult]) -> ValidationMetrics:
        """Calculate comprehensive validation metrics"""
        
        if not test_results:
            return ValidationMetrics(
                technical_accuracy=0.0,
                conversation_quality=0.0,
                lead_scoring_accuracy=0.0,
                revenue_optimization=0.0,
                performance_score=0.0,
                overall_score=0.0,
                test_results=test_results,
                benchmark_comparison={}
            )
        
        # Calculate category scores
        technical_tests = [r for r in test_results if "solar" in r.test_name.lower() or "incentive" in r.test_name.lower()]
        conversation_tests = [r for r in test_results if "conversation" in r.test_name.lower()]
        scoring_tests = [r for r in test_results if "scoring" in r.test_name.lower()]
        revenue_tests = [r for r in test_results if "revenue" in r.test_name.lower() or "routing" in r.test_name.lower()]
        performance_tests = [r for r in test_results if "performance" in r.test_name.lower()]
        
        technical_accuracy = np.mean([r.score for r in technical_tests]) if technical_tests else 0.0
        conversation_quality = np.mean([r.score for r in conversation_tests]) if conversation_tests else 0.0
        lead_scoring_accuracy = np.mean([r.score for r in scoring_tests]) if scoring_tests else 0.0
        revenue_optimization = np.mean([r.score for r in revenue_tests]) if revenue_tests else 0.0
        performance_score = np.mean([r.score for r in performance_tests]) if performance_tests else 0.0
        
        # Calculate overall score
        overall_score = np.mean([technical_accuracy, conversation_quality, lead_scoring_accuracy, revenue_optimization, performance_score])
        
        # Benchmark comparison
        benchmark_comparison = {
            "technical_accuracy": technical_accuracy / self.benchmark_data["performance_benchmarks"]["technical_accuracy_threshold"],
            "conversation_completion": conversation_quality / self.benchmark_data["performance_benchmarks"]["conversation_completion_rate"],
            "lead_value": revenue_optimization * 150 / self.benchmark_data["performance_benchmarks"]["average_lead_value"]
        }
        
        return ValidationMetrics(
            technical_accuracy=technical_accuracy,
            conversation_quality=conversation_quality,
            lead_scoring_accuracy=lead_scoring_accuracy,
            revenue_optimization=revenue_optimization,
            performance_score=performance_score,
            overall_score=overall_score,
            test_results=test_results,
            benchmark_comparison=benchmark_comparison
        )


# Test runner functions
async def run_comprehensive_validation(db: Session, redis_client) -> ValidationMetrics:
    """Run comprehensive validation of the conversational agent"""
    
    validator = ComprehensiveAgentValidator(db, redis_client)
    return await validator.run_comprehensive_validation()


def generate_validation_report(validation_metrics: ValidationMetrics) -> str:
    """Generate comprehensive validation report"""
    
    report = f"""
# 🚀 Aurum Solar Conversational Agent Validation Report

## 📊 Overall Performance Score: {validation_metrics.overall_score:.1%}

### 🎯 Category Scores
- **Technical Accuracy**: {validation_metrics.technical_accuracy:.1%}
- **Conversation Quality**: {validation_metrics.conversation_quality:.1%}
- **Lead Scoring Accuracy**: {validation_metrics.lead_scoring_accuracy:.1%}
- **Revenue Optimization**: {validation_metrics.revenue_optimization:.1%}
- **Performance**: {validation_metrics.performance_score:.1%}

### 📈 Benchmark Comparison
"""
    
    for benchmark, score in validation_metrics.benchmark_comparison.items():
        status = "✅ PASS" if score >= 1.0 else "❌ FAIL"
        report += f"- **{benchmark.replace('_', ' ').title()}**: {score:.1%} {status}\n"
    
    report += "\n### 🔍 Test Results Summary\n"
    
    # Group tests by category
    categories = {}
    for result in validation_metrics.test_results:
        category = result.test_name.split()[0]
        if category not in categories:
            categories[category] = []
        categories[category].append(result)
    
    for category, tests in categories.items():
        passed = sum(1 for t in tests if t.passed)
        total = len(tests)
        report += f"- **{category.title()}**: {passed}/{total} tests passed ({passed/total:.1%})\n"
    
    report += "\n### ⚠️ Issues and Recommendations\n"
    
    failed_tests = [t for t in validation_metrics.test_results if not t.passed]
    if failed_tests:
        for test in failed_tests[:5]:  # Show top 5 issues
            report += f"- **{test.test_name}** ({test.scenario_id}): {', '.join(test.errors)}\n"
            if test.recommendations:
                report += f"  - Recommendations: {', '.join(test.recommendations)}\n"
    else:
        report += "- ✅ No critical issues found!\n"
    
    report += f"\n### 📅 Validation Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return report


if __name__ == "__main__":
    # Example usage
    print("🧪 Comprehensive Agent Validation Framework")
    print("This framework tests all aspects of the conversational agent")
    print("Run with: python -m pytest test_comprehensive_agent_validation.py -v")

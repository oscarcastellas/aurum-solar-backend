"""
A/B Testing Service for Conversation Optimization
Enables experimentation with different conversation flows and strategies
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadConversation
from app.models.ai_models import AIAnalysis, AIInsight
from app.core.config import settings


class TestType(Enum):
    """Types of A/B tests"""
    CONVERSATION_FLOW = "conversation_flow"
    MESSAGE_TONE = "message_tone"
    URGENCY_CREATION = "urgency_creation"
    OBJECTION_HANDLING = "objection_handling"
    NYC_PERSONALIZATION = "nyc_personalization"
    QUALIFICATION_QUESTIONS = "qualification_questions"


class TestStatus(Enum):
    """Test status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TestVariant:
    """A/B test variant configuration"""
    variant_id: str
    name: str
    description: str
    weight: float  # Traffic allocation (0.0 to 1.0)
    configuration: Dict[str, Any]
    is_control: bool = False


@dataclass
class TestResult:
    """A/B test result data"""
    variant_id: str
    participants: int
    conversions: int
    conversion_rate: float
    avg_lead_score: float
    avg_quality_tier: str
    revenue_generated: float
    avg_conversation_length: float
    completion_rate: float


class ABTestingService:
    """Service for A/B testing conversation optimization"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Active tests cache
        self.active_tests = {}
        self.test_results = {}
        
        # Load active tests
        asyncio.create_task(self._load_active_tests())
    
    async def create_test(
        self,
        test_name: str,
        test_type: TestType,
        description: str,
        variants: List[TestVariant],
        target_audience: Dict[str, Any] = None,
        success_metrics: List[str] = None
    ) -> str:
        """Create a new A/B test"""
        
        try:
            test_id = f"test_{test_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Validate variants
            total_weight = sum(v.weight for v in variants)
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError("Variant weights must sum to 1.0")
            
            # Ensure exactly one control variant
            control_count = sum(1 for v in variants if v.is_control)
            if control_count != 1:
                raise ValueError("Exactly one variant must be marked as control")
            
            # Create test configuration
            test_config = {
                "test_id": test_id,
                "test_name": test_name,
                "test_type": test_type.value,
                "description": description,
                "variants": [
                    {
                        "variant_id": v.variant_id,
                        "name": v.name,
                        "description": v.description,
                        "weight": v.weight,
                        "configuration": v.configuration,
                        "is_control": v.is_control
                    }
                    for v in variants
                ],
                "target_audience": target_audience or {},
                "success_metrics": success_metrics or ["conversion_rate", "lead_score", "revenue"],
                "status": TestStatus.DRAFT.value,
                "created_at": datetime.utcnow().isoformat(),
                "started_at": None,
                "ended_at": None,
                "participants": 0,
                "conversions": 0
            }
            
            # Store test configuration (in production, this would be in database)
            self.active_tests[test_id] = test_config
            
            return test_id
            
        except Exception as e:
            print(f"Error creating A/B test: {e}")
            raise
    
    async def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        
        try:
            if test_id not in self.active_tests:
                return False
            
            test_config = self.active_tests[test_id]
            test_config["status"] = TestStatus.ACTIVE.value
            test_config["started_at"] = datetime.utcnow().isoformat()
            
            # Initialize test results
            self.test_results[test_id] = {
                variant["variant_id"]: {
                    "participants": 0,
                    "conversions": 0,
                    "conversion_rate": 0.0,
                    "avg_lead_score": 0.0,
                    "revenue_generated": 0.0,
                    "avg_conversation_length": 0.0,
                    "completion_rate": 0.0,
                    "quality_tier_distribution": {}
                }
                for variant in test_config["variants"]
            }
            
            return True
            
        except Exception as e:
            print(f"Error starting A/B test: {e}")
            return False
    
    async def assign_variant(self, test_id: str, session_id: str, lead_id: str = None) -> Optional[TestVariant]:
        """Assign a variant to a user session"""
        
        try:
            if test_id not in self.active_tests:
                return None
            
            test_config = self.active_tests[test_id]
            if test_config["status"] != TestStatus.ACTIVE.value:
                return None
            
            # Check if user is eligible for test
            if not await self._is_eligible_for_test(test_config, session_id, lead_id):
                return None
            
            # Select variant based on weights
            selected_variant = self._select_variant(test_config["variants"])
            
            # Record participation
            await self._record_participation(test_id, selected_variant["variant_id"], session_id, lead_id)
            
            return TestVariant(
                variant_id=selected_variant["variant_id"],
                name=selected_variant["name"],
                description=selected_variant["description"],
                weight=selected_variant["weight"],
                configuration=selected_variant["configuration"],
                is_control=selected_variant["is_control"]
            )
            
        except Exception as e:
            print(f"Error assigning variant: {e}")
            return None
    
    async def record_conversion(
        self,
        test_id: str,
        variant_id: str,
        session_id: str,
        lead_id: str,
        conversion_data: Dict[str, Any]
    ):
        """Record a conversion for A/B test"""
        
        try:
            if test_id not in self.test_results:
                return
            
            if variant_id not in self.test_results[test_id]:
                return
            
            # Update conversion data
            variant_results = self.test_results[test_id][variant_id]
            variant_results["conversions"] += 1
            
            # Update metrics
            lead_score = conversion_data.get("lead_score", 0)
            quality_tier = conversion_data.get("quality_tier", "unqualified")
            revenue = conversion_data.get("revenue", 0)
            conversation_length = conversion_data.get("conversation_length", 0)
            
            # Update averages
            total_participants = variant_results["participants"]
            if total_participants > 0:
                # Update average lead score
                current_avg = variant_results["avg_lead_score"]
                variant_results["avg_lead_score"] = (
                    (current_avg * (total_participants - 1) + lead_score) / total_participants
                )
                
                # Update average conversation length
                current_avg_length = variant_results["avg_conversation_length"]
                variant_results["avg_conversation_length"] = (
                    (current_avg_length * (total_participants - 1) + conversation_length) / total_participants
                )
            
            # Update revenue
            variant_results["revenue_generated"] += revenue
            
            # Update quality tier distribution
            if quality_tier not in variant_results["quality_tier_distribution"]:
                variant_results["quality_tier_distribution"][quality_tier] = 0
            variant_results["quality_tier_distribution"][quality_tier] += 1
            
            # Update conversion rate
            variant_results["conversion_rate"] = (
                variant_results["conversions"] / variant_results["participants"]
                if variant_results["participants"] > 0 else 0
            )
            
            # Update test-level metrics
            test_config = self.active_tests[test_id]
            test_config["conversions"] += 1
            
        except Exception as e:
            print(f"Error recording conversion: {e}")
    
    async def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results"""
        
        try:
            if test_id not in self.active_tests:
                return {}
            
            test_config = self.active_tests[test_id]
            test_results = self.test_results.get(test_id, {})
            
            # Calculate statistical significance
            significance = await self._calculate_significance(test_id)
            
            # Generate insights
            insights = await self._generate_test_insights(test_id)
            
            return {
                "test_config": test_config,
                "results": test_results,
                "significance": significance,
                "insights": insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting test results: {e}")
            return {}
    
    async def stop_test(self, test_id: str) -> bool:
        """Stop an A/B test"""
        
        try:
            if test_id not in self.active_tests:
                return False
            
            test_config = self.active_tests[test_id]
            test_config["status"] = TestStatus.COMPLETED.value
            test_config["ended_at"] = datetime.utcnow().isoformat()
            
            # Generate final insights
            final_insights = await self._generate_final_insights(test_id)
            
            # Store insights in database
            await self._store_test_insights(test_id, final_insights)
            
            return True
            
        except Exception as e:
            print(f"Error stopping A/B test: {e}")
            return False
    
    def _select_variant(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select variant based on weights"""
        
        random_value = random.random()
        cumulative_weight = 0.0
        
        for variant in variants:
            cumulative_weight += variant["weight"]
            if random_value <= cumulative_weight:
                return variant
        
        # Fallback to last variant
        return variants[-1]
    
    async def _is_eligible_for_test(
        self, 
        test_config: Dict[str, Any], 
        session_id: str, 
        lead_id: str = None
    ) -> bool:
        """Check if user is eligible for test"""
        
        target_audience = test_config.get("target_audience", {})
        
        # Check if lead_id is required
        if target_audience.get("require_lead_id", False) and not lead_id:
            return False
        
        # Check geographic targeting
        if "zip_codes" in target_audience and lead_id:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if lead and lead.zip_code not in target_audience["zip_codes"]:
                return False
        
        # Check quality tier targeting
        if "quality_tiers" in target_audience and lead_id:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if lead and lead.lead_quality not in target_audience["quality_tiers"]:
                return False
        
        return True
    
    async def _record_participation(
        self, 
        test_id: str, 
        variant_id: str, 
        session_id: str, 
        lead_id: str = None
    ):
        """Record user participation in test"""
        
        try:
            # Update variant participation count
            if test_id in self.test_results and variant_id in self.test_results[test_id]:
                self.test_results[test_id][variant_id]["participants"] += 1
            
            # Update test participation count
            if test_id in self.active_tests:
                self.active_tests[test_id]["participants"] += 1
            
            # Store participation record (in production, this would be in database)
            participation_record = {
                "test_id": test_id,
                "variant_id": variant_id,
                "session_id": session_id,
                "lead_id": lead_id,
                "participated_at": datetime.utcnow().isoformat()
            }
            
            # In production, store in database
            print(f"Participation recorded: {participation_record}")
            
        except Exception as e:
            print(f"Error recording participation: {e}")
    
    async def _calculate_significance(self, test_id: str) -> Dict[str, Any]:
        """Calculate statistical significance for test"""
        
        try:
            if test_id not in self.test_results:
                return {}
            
            test_results = self.test_results[test_id]
            variants = list(test_results.keys())
            
            if len(variants) < 2:
                return {}
            
            # Find control variant
            control_variant = None
            test_variants = []
            
            for variant_id, results in test_results.items():
                if results.get("is_control", False):
                    control_variant = variant_id
                else:
                    test_variants.append(variant_id)
            
            if not control_variant:
                return {}
            
            control_results = test_results[control_variant]
            significance_results = {}
            
            for variant_id in test_variants:
                variant_results = test_results[variant_id]
                
                # Calculate conversion rate difference
                control_rate = control_results["conversion_rate"]
                variant_rate = variant_results["conversion_rate"]
                rate_difference = variant_rate - control_rate
                
                # Calculate statistical significance (simplified)
                # In production, use proper statistical tests
                significance = "not_significant"
                if abs(rate_difference) > 0.05:  # 5% difference threshold
                    significance = "significant" if rate_difference > 0 else "negative"
                
                significance_results[variant_id] = {
                    "control_rate": control_rate,
                    "variant_rate": variant_rate,
                    "rate_difference": rate_difference,
                    "significance": significance,
                    "confidence_level": 0.95  # Placeholder
                }
            
            return significance_results
            
        except Exception as e:
            print(f"Error calculating significance: {e}")
            return {}
    
    async def _generate_test_insights(self, test_id: str) -> List[Dict[str, Any]]:
        """Generate insights from test results"""
        
        try:
            if test_id not in self.test_results:
                return []
            
            test_results = self.test_results[test_id]
            insights = []
            
            # Find best performing variant
            best_variant = max(
                test_results.items(),
                key=lambda x: x[1]["conversion_rate"]
            )
            
            insights.append({
                "type": "best_performer",
                "variant_id": best_variant[0],
                "conversion_rate": best_variant[1]["conversion_rate"],
                "message": f"Variant {best_variant[0]} has the highest conversion rate"
            })
            
            # Check for significant differences
            significance = await self._calculate_significance(test_id)
            for variant_id, sig_data in significance.items():
                if sig_data["significance"] == "significant":
                    insights.append({
                        "type": "significant_improvement",
                        "variant_id": variant_id,
                        "improvement": sig_data["rate_difference"],
                        "message": f"Variant {variant_id} shows significant improvement"
                    })
            
            return insights
            
        except Exception as e:
            print(f"Error generating test insights: {e}")
            return []
    
    async def _generate_final_insights(self, test_id: str) -> List[Dict[str, Any]]:
        """Generate final insights when test is completed"""
        
        try:
            insights = await self._generate_test_insights(test_id)
            
            # Add final recommendations
            if test_id in self.test_results:
                test_results = self.test_results[test_id]
                
                # Find winning variant
                winning_variant = max(
                    test_results.items(),
                    key=lambda x: x[1]["conversion_rate"]
                )
                
                insights.append({
                    "type": "recommendation",
                    "variant_id": winning_variant[0],
                    "action": "implement",
                    "message": f"Implement variant {winning_variant[0]} as the new default"
                })
            
            return insights
            
        except Exception as e:
            print(f"Error generating final insights: {e}")
            return []
    
    async def _store_test_insights(self, test_id: str, insights: List[Dict[str, Any]]):
        """Store test insights in database"""
        
        try:
            for insight in insights:
                ai_insight = AIInsight(
                    insight_type="ab_test_result",
                    insight_category="conversation_optimization",
                    insight_title=f"A/B Test Result: {test_id}",
                    insight_description=insight.get("message", ""),
                    insight_data={
                        "test_id": test_id,
                        "insight_type": insight.get("type"),
                        "variant_id": insight.get("variant_id"),
                        "data": insight
                    },
                    confidence_score=0.8,
                    impact_score=0.7,
                    discovered_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=90)
                )
                
                self.db.add(ai_insight)
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing test insights: {e}")
            self.db.rollback()
    
    async def _load_active_tests(self):
        """Load active tests from database"""
        
        try:
            # In production, load from database
            # For now, initialize with sample tests
            sample_tests = await self._create_sample_tests()
            self.active_tests.update(sample_tests)
            
        except Exception as e:
            print(f"Error loading active tests: {e}")
    
    async def _create_sample_tests(self) -> Dict[str, Dict[str, Any]]:
        """Create sample A/B tests for demonstration"""
        
        return {
            "test_conversation_flow_20241201_120000": {
                "test_id": "test_conversation_flow_20241201_120000",
                "test_name": "Conversation Flow Optimization",
                "test_type": "conversation_flow",
                "description": "Test different conversation flow approaches",
                "variants": [
                    {
                        "variant_id": "control_flow",
                        "name": "Control Flow",
                        "description": "Standard conversation flow",
                        "weight": 0.5,
                        "configuration": {
                            "flow_type": "standard",
                            "urgency_creation": "moderate",
                            "qualification_questions": "standard"
                        },
                        "is_control": True
                    },
                    {
                        "variant_id": "urgent_flow",
                        "name": "Urgency-Focused Flow",
                        "description": "Emphasize 2025 tax credit deadline",
                        "weight": 0.5,
                        "configuration": {
                            "flow_type": "urgency_focused",
                            "urgency_creation": "high",
                            "qualification_questions": "rapid"
                        },
                        "is_control": False
                    }
                ],
                "target_audience": {
                    "require_lead_id": True,
                    "quality_tiers": ["premium", "standard"]
                },
                "success_metrics": ["conversion_rate", "lead_score", "revenue"],
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "started_at": datetime.utcnow().isoformat(),
                "ended_at": None,
                "participants": 0,
                "conversions": 0
            }
        }
    
    async def get_active_tests(self) -> List[Dict[str, Any]]:
        """Get list of active A/B tests"""
        
        return [
            test_config for test_config in self.active_tests.values()
            if test_config["status"] == TestStatus.ACTIVE.value
        ]
    
    async def get_test_performance(self, test_id: str) -> Dict[str, Any]:
        """Get performance metrics for a test"""
        
        try:
            if test_id not in self.active_tests:
                return {}
            
            test_config = self.active_tests[test_id]
            test_results = self.test_results.get(test_id, {})
            
            # Calculate performance metrics
            total_participants = sum(
                results["participants"] for results in test_results.values()
            )
            total_conversions = sum(
                results["conversions"] for results in test_results.values()
            )
            
            overall_conversion_rate = (
                total_conversions / total_participants if total_participants > 0 else 0
            )
            
            return {
                "test_id": test_id,
                "test_name": test_config["test_name"],
                "status": test_config["status"],
                "total_participants": total_participants,
                "total_conversions": total_conversions,
                "overall_conversion_rate": overall_conversion_rate,
                "variant_performance": test_results,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting test performance: {e}")
            return {}

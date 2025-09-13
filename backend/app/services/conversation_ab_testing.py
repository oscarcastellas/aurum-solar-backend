"""
A/B Testing Framework for Conversation Optimization
Tests different conversation strategies to maximize B2B lead value
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

from app.models.lead import Lead
from app.models.ai_models import AIConversation


class TestVariant(Enum):
    """A/B test variants"""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


class TestMetric(Enum):
    """A/B test metrics"""
    QUALIFICATION_RATE = "qualification_rate"
    B2B_VALUE = "b2b_value"
    CONVERSATION_LENGTH = "conversation_length"
    TECHNICAL_ENGAGEMENT = "technical_engagement"
    URGENCY_CREATION = "urgency_creation"
    OBJECTION_RESOLUTION = "objection_resolution"


@dataclass
class ABTestConfig:
    """A/B test configuration"""
    test_name: str
    description: str
    variants: List[TestVariant]
    traffic_split: Dict[TestVariant, float]  # Percentage of traffic
    start_date: datetime
    end_date: datetime
    min_sample_size: int
    success_metrics: List[TestMetric]
    is_active: bool = True


@dataclass
class TestResult:
    """A/B test result"""
    test_name: str
    variant: TestVariant
    metric: TestMetric
    value: float
    sample_size: int
    confidence_level: float
    statistical_significance: bool
    timestamp: datetime


class ConversationABTesting:
    """A/B testing framework for conversation optimization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_tests = self._load_active_tests()
        self.test_results = {}
    
    def _load_active_tests(self) -> Dict[str, ABTestConfig]:
        """Load active A/B tests"""
        
        return {
            "qualification_sequence": ABTestConfig(
                test_name="qualification_sequence",
                description="Test different qualification question sequences",
                variants=[TestVariant.CONTROL, TestVariant.VARIANT_A, TestVariant.VARIANT_B],
                traffic_split={
                    TestVariant.CONTROL: 0.33,
                    TestVariant.VARIANT_A: 0.33,
                    TestVariant.VARIANT_B: 0.34
                },
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                min_sample_size=100,
                success_metrics=[TestMetric.QUALIFICATION_RATE, TestMetric.B2B_VALUE]
            ),
            "urgency_creation": ABTestConfig(
                test_name="urgency_creation",
                description="Test different urgency creation strategies",
                variants=[TestVariant.CONTROL, TestVariant.VARIANT_A],
                traffic_split={
                    TestVariant.CONTROL: 0.5,
                    TestVariant.VARIANT_A: 0.5
                },
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=21),
                min_sample_size=150,
                success_metrics=[TestMetric.URGENCY_CREATION, TestMetric.B2B_VALUE]
            ),
            "technical_expertise": ABTestConfig(
                test_name="technical_expertise",
                description="Test technical expertise presentation",
                variants=[TestVariant.CONTROL, TestVariant.VARIANT_A, TestVariant.VARIANT_B],
                traffic_split={
                    TestVariant.CONTROL: 0.33,
                    TestVariant.VARIANT_A: 0.33,
                    TestVariant.VARIANT_B: 0.34
                },
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=28),
                min_sample_size=120,
                success_metrics=[TestMetric.TECHNICAL_ENGAGEMENT, TestMetric.QUALIFICATION_RATE]
            ),
            "objection_handling": ABTestConfig(
                test_name="objection_handling",
                description="Test objection handling strategies",
                variants=[TestVariant.CONTROL, TestVariant.VARIANT_A],
                traffic_split={
                    TestVariant.CONTROL: 0.5,
                    TestVariant.VARIANT_A: 0.5
                },
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=25),
                min_sample_size=80,
                success_metrics=[TestMetric.OBJECTION_RESOLUTION, TestMetric.B2B_VALUE]
            )
        }
    
    def get_test_variant(self, test_name: str, session_id: str) -> TestVariant:
        """Get test variant for a session"""
        
        if test_name not in self.active_tests:
            return TestVariant.CONTROL
        
        test_config = self.active_tests[test_name]
        if not test_config.is_active:
            return TestVariant.CONTROL
        
        # Use session ID to ensure consistent variant assignment
        hash_input = f"{test_name}_{session_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        random_value = (hash_value % 100) / 100.0
        
        cumulative = 0.0
        for variant, percentage in test_config.traffic_split.items():
            cumulative += percentage
            if random_value <= cumulative:
                return variant
        
        return TestVariant.CONTROL
    
    def get_qualification_sequence(self, variant: TestVariant) -> List[str]:
        """Get qualification sequence for test variant"""
        
        sequences = {
            TestVariant.CONTROL: [
                "What's your monthly electric bill?",
                "Do you own your home?",
                "What's your ZIP code?",
                "When are you looking to install?",
                "What questions do you have about solar?"
            ],
            TestVariant.VARIANT_A: [
                "Do you own your home?",
                "What's your monthly electric bill?",
                "What's your ZIP code?",
                "Are you aware the 30% federal tax credit expires December 31st?",
                "What's most important to you in a solar system?"
            ],
            TestVariant.VARIANT_B: [
                "What's driving your interest in solar right now?",
                "What's your monthly electric bill?",
                "Do you own your home?",
                "What's your ZIP code?",
                "What's your timeline for installation?"
            ]
        }
        
        return sequences.get(variant, sequences[TestVariant.CONTROL])
    
    def get_urgency_strategy(self, variant: TestVariant) -> Dict[str, Any]:
        """Get urgency creation strategy for test variant"""
        
        strategies = {
            TestVariant.CONTROL: {
                "tax_credit_urgency": 0.3,  # 30% chance to mention
                "nyserda_urgency": 0.2,    # 20% chance to mention
                "seasonal_urgency": 0.4,   # 40% chance to mention
                "installer_urgency": 0.3   # 30% chance to mention
            },
            TestVariant.VARIANT_A: {
                "tax_credit_urgency": 0.6,  # 60% chance to mention
                "nyserda_urgency": 0.4,    # 40% chance to mention
                "seasonal_urgency": 0.3,   # 30% chance to mention
                "installer_urgency": 0.2   # 20% chance to mention
            }
        }
        
        return strategies.get(variant, strategies[TestVariant.CONTROL])
    
    def get_technical_expertise_level(self, variant: TestVariant) -> Dict[str, Any]:
        """Get technical expertise level for test variant"""
        
        levels = {
            TestVariant.CONTROL: {
                "technical_depth": "medium",
                "local_examples": 0.5,
                "success_stories": 0.3,
                "installer_credentials": 0.4
            },
            TestVariant.VARIANT_A: {
                "technical_depth": "high",
                "local_examples": 0.8,
                "success_stories": 0.6,
                "installer_credentials": 0.7
            },
            TestVariant.VARIANT_B: {
                "technical_depth": "low",
                "local_examples": 0.3,
                "success_stories": 0.2,
                "installer_credentials": 0.2
            }
        }
        
        return levels.get(variant, levels[TestVariant.CONTROL])
    
    def get_objection_handling_strategy(self, variant: TestVariant) -> Dict[str, Any]:
        """Get objection handling strategy for test variant"""
        
        strategies = {
            TestVariant.CONTROL: {
                "data_driven": 0.6,
                "local_examples": 0.4,
                "urgency_creation": 0.3,
                "personalization": 0.5
            },
            TestVariant.VARIANT_A: {
                "data_driven": 0.8,
                "local_examples": 0.7,
                "urgency_creation": 0.6,
                "personalization": 0.8
            }
        }
        
        return strategies.get(variant, strategies[TestVariant.CONTROL])
    
    def track_conversation_metric(
        self,
        test_name: str,
        variant: TestVariant,
        session_id: str,
        metric: TestMetric,
        value: float
    ):
        """Track conversation metric for A/B test"""
        
        try:
            # Store in database
            conversation = AIConversation(
                lead_id=None,
                session_id=session_id,
                message_type="ab_test_metric",
                content=json.dumps({
                    "test_name": test_name,
                    "variant": variant.value,
                    "metric": metric.value,
                    "value": value,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                sentiment_score=0.0,
                intent_classification="ab_test_tracking",
                entities_extracted={},
                confidence_score=1.0,
                response_time_ms=0,
                ai_model_used="ab_testing_framework",
                tokens_used=0
            )
            
            self.db.add(conversation)
            self.db.commit()
            
        except Exception as e:
            print(f"Error tracking A/B test metric: {e}")
            self.db.rollback()
    
    def get_test_results(self, test_name: str) -> Dict[str, Any]:
        """Get A/B test results"""
        
        if test_name not in self.active_tests:
            return {"error": "Test not found"}
        
        test_config = self.active_tests[test_name]
        
        # Query database for test results
        try:
            conversations = self.db.query(AIConversation).filter(
                AIConversation.intent_classification == "ab_test_tracking",
                AIConversation.content.contains(f'"test_name": "{test_name}"')
            ).all()
            
            # Parse results
            results = {}
            for conversation in conversations:
                data = json.loads(conversation.content)
                variant = data["variant"]
                metric = data["metric"]
                value = data["value"]
                
                if variant not in results:
                    results[variant] = {}
                if metric not in results[variant]:
                    results[variant][metric] = []
                
                results[variant][metric].append(value)
            
            # Calculate statistics
            statistics = {}
            for variant, metrics in results.items():
                statistics[variant] = {}
                for metric, values in metrics.items():
                    if values:
                        statistics[variant][metric] = {
                            "mean": sum(values) / len(values),
                            "count": len(values),
                            "min": min(values),
                            "max": max(values)
                        }
            
            return {
                "test_name": test_name,
                "status": "active" if test_config.is_active else "completed",
                "statistics": statistics,
                "total_conversations": len(conversations)
            }
            
        except Exception as e:
            return {"error": f"Error retrieving test results: {e}"}
    
    def determine_winning_variant(self, test_name: str) -> Optional[TestVariant]:
        """Determine winning variant based on statistical significance"""
        
        results = self.get_test_results(test_name)
        if "error" in results or "statistics" not in results:
            return None
        
        test_config = self.active_tests[test_name]
        primary_metric = test_config.success_metrics[0]
        
        # Get metric values for each variant
        variant_metrics = {}
        for variant, metrics in results["statistics"].items():
            if primary_metric.value in metrics:
                variant_metrics[variant] = metrics[primary_metric.value]
        
        if len(variant_metrics) < 2:
            return None
        
        # Simple comparison (in production, use proper statistical testing)
        best_variant = None
        best_value = 0
        
        for variant, metric_data in variant_metrics.items():
            if metric_data["count"] >= test_config.min_sample_size:
                if metric_data["mean"] > best_value:
                    best_value = metric_data["mean"]
                    best_variant = TestVariant(variant)
        
        return best_variant
    
    def get_optimized_conversation_strategy(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get optimized conversation strategy based on A/B test results"""
        
        strategy = {
            "qualification_sequence": self.get_qualification_sequence(
                self.get_test_variant("qualification_sequence", session_id)
            ),
            "urgency_strategy": self.get_urgency_strategy(
                self.get_test_variant("urgency_creation", session_id)
            ),
            "technical_expertise": self.get_technical_expertise_level(
                self.get_test_variant("technical_expertise", session_id)
            ),
            "objection_handling": self.get_objection_handling_strategy(
                self.get_test_variant("objection_handling", session_id)
            )
        }
        
        return strategy
    
    def create_new_test(
        self,
        test_name: str,
        description: str,
        variants: List[TestVariant],
        traffic_split: Dict[TestVariant, float],
        duration_days: int,
        min_sample_size: int,
        success_metrics: List[TestMetric]
    ) -> bool:
        """Create new A/B test"""
        
        try:
            test_config = ABTestConfig(
                test_name=test_name,
                description=description,
                variants=variants,
                traffic_split=traffic_split,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration_days),
                min_sample_size=min_sample_size,
                success_metrics=success_metrics
            )
            
            self.active_tests[test_name] = test_config
            return True
            
        except Exception as e:
            print(f"Error creating A/B test: {e}")
            return False
    
    def end_test(self, test_name: str) -> bool:
        """End A/B test"""
        
        if test_name in self.active_tests:
            self.active_tests[test_name].is_active = False
            return True
        
        return False
    
    def get_all_test_results(self) -> Dict[str, Any]:
        """Get results for all active tests"""
        
        results = {}
        for test_name in self.active_tests:
            results[test_name] = self.get_test_results(test_name)
        
        return results

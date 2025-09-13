"""
Automated Conversation Simulation Tools for Aurum Solar Agent Testing
Simulates realistic user conversations and validates responses
"""

import pytest
import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from unittest.mock import Mock
import numpy as np

from app.services.revenue_optimization_system import RevenueOptimizationSystem


@dataclass
class ConversationSimulation:
    """Conversation simulation configuration"""
    simulation_id: str
    user_type: str
    conversation_length: int
    user_profile: Dict[str, Any]
    message_templates: List[Dict[str, str]]
    expected_behaviors: List[str]


@dataclass
class SimulationResult:
    """Result of conversation simulation"""
    simulation_id: str
    user_type: str
    total_messages: int
    conversation_duration: float
    response_times: List[float]
    revenue_generated: float
    lead_quality_achieved: str
    conversation_quality_score: float
    technical_accuracy_score: float
    user_satisfaction_score: float
    errors: List[str]
    success: bool


class AutomatedConversationSimulator:
    """Automated conversation simulation and testing framework"""
    
    def __init__(self, revenue_system: RevenueOptimizationSystem):
        self.revenue_system = revenue_system
        self.simulations = self._load_simulation_templates()
        self.performance_metrics = []
    
    def _load_simulation_templates(self) -> List[ConversationSimulation]:
        """Load conversation simulation templates"""
        
        return [
            # High-Intent Customer Simulation
            ConversationSimulation(
                simulation_id="high_intent_customer",
                user_type="high_intent",
                conversation_length=8,
                user_profile={
                    "homeowner_verified": True,
                    "bill_amount": 350.0,
                    "zip_code": "11215",
                    "borough": "brooklyn",
                    "neighborhood": "park_slope",
                    "timeline": "urgent",
                    "decision_maker": True,
                    "research_level": "high"
                },
                message_templates=[
                    {"template": "I'm ready to move forward with solar installation", "intent": "high_intent"},
                    {"template": "What's the best system size for my {bill_amount} monthly bill?", "intent": "technical"},
                    {"template": "How much will I save with solar?", "intent": "savings"},
                    {"template": "What incentives are available in NYC?", "intent": "incentives"},
                    {"template": "When can installation begin?", "intent": "timeline"},
                    {"template": "What financing options do you offer?", "intent": "financing"},
                    {"template": "I want to schedule a consultation", "intent": "action"}
                ],
                expected_behaviors=[
                    "high_engagement",
                    "technical_questions",
                    "urgency_signals",
                    "decision_readiness"
                ]
            ),
            
            # Curious Researcher Simulation
            ConversationSimulation(
                simulation_id="curious_researcher",
                user_type="researcher",
                conversation_length=12,
                user_profile={
                    "homeowner_verified": True,
                    "bill_amount": 220.0,
                    "zip_code": "11375",
                    "borough": "queens",
                    "neighborhood": "forest_hills",
                    "timeline": "exploring",
                    "decision_maker": False,
                    "research_level": "extensive"
                },
                message_templates=[
                    {"template": "I'm just starting to research solar options", "intent": "exploration"},
                    {"template": "How do solar panels work?", "intent": "education"},
                    {"template": "What are the different types of solar systems?", "intent": "education"},
                    {"template": "How long do solar panels last?", "intent": "education"},
                    {"template": "What maintenance is required?", "intent": "education"},
                    {"template": "How do I know if my roof is suitable?", "intent": "technical"},
                    {"template": "What happens during cloudy weather?", "intent": "technical"},
                    {"template": "How does net metering work in NYC?", "intent": "technical"},
                    {"template": "What are the environmental benefits?", "intent": "education"},
                    {"template": "This is very helpful, thank you", "intent": "satisfaction"}
                ],
                expected_behaviors=[
                    "extensive_questions",
                    "educational_focus",
                    "gradual_engagement",
                    "information_gathering"
                ]
            ),
            
            # Skeptical Customer Simulation
            ConversationSimulation(
                simulation_id="skeptical_customer",
                user_type="skeptical",
                conversation_length=10,
                user_profile={
                    "homeowner_verified": True,
                    "bill_amount": 280.0,
                    "zip_code": "10023",
                    "borough": "manhattan",
                    "neighborhood": "upper_west_side",
                    "timeline": "considering",
                    "decision_maker": True,
                    "skepticism_level": "high"
                },
                message_templates=[
                    {"template": "I've heard mixed things about solar", "intent": "skepticism"},
                    {"template": "Isn't solar too expensive?", "intent": "objection"},
                    {"template": "What if the technology becomes obsolete?", "intent": "objection"},
                    {"template": "How do I know you're not just trying to sell me something?", "intent": "objection"},
                    {"template": "What about the installation process?", "intent": "concern"},
                    {"template": "What if something goes wrong?", "intent": "concern"},
                    {"template": "This all sounds too good to be true", "intent": "skepticism"},
                    {"template": "Can you provide references?", "intent": "validation"},
                    {"template": "I need to think about this more", "intent": "hesitation"}
                ],
                expected_behaviors=[
                    "objection_handling",
                    "trust_building",
                    "credibility_demonstration",
                    "gradual_conviction"
                ]
            ),
            
            # Price-Sensitive Customer Simulation
            ConversationSimulation(
                simulation_id="price_sensitive_customer",
                user_type="price_sensitive",
                conversation_length=9,
                user_profile={
                    "homeowner_verified": True,
                    "bill_amount": 180.0,
                    "zip_code": "10451",
                    "borough": "bronx",
                    "neighborhood": "south_bronx",
                    "timeline": "flexible",
                    "decision_maker": True,
                    "budget_conscious": True
                },
                message_templates=[
                    {"template": "I'm interested in solar but worried about the cost", "intent": "cost_concern"},
                    {"template": "What's the cheapest solar option?", "intent": "price_focus"},
                    {"template": "Are there any free solar programs?", "intent": "free_options"},
                    {"template": "What financing options do you have?", "intent": "financing"},
                    {"template": "Can I pay monthly instead of upfront?", "intent": "payment_options"},
                    {"template": "What's the minimum down payment?", "intent": "cost_minimization"},
                    {"template": "How long until I break even?", "intent": "roi_focus"},
                    {"template": "Are there any hidden costs?", "intent": "cost_transparency"},
                    {"template": "I need to find the most affordable option", "intent": "price_priority"}
                ],
                expected_behaviors=[
                    "cost_focus",
                    "financing_emphasis",
                    "roi_calculation",
                    "budget_solutions"
                ]
            ),
            
            # Time-Pressured Customer Simulation
            ConversationSimulation(
                simulation_id="time_pressured_customer",
                user_type="time_pressured",
                conversation_length=6,
                user_profile={
                    "homeowner_verified": True,
                    "bill_amount": 420.0,
                    "zip_code": "10021",
                    "borough": "manhattan",
                    "neighborhood": "upper_east_side",
                    "timeline": "urgent",
                    "decision_maker": True,
                    "time_constraint": True
                },
                message_templates=[
                    {"template": "I need to make a decision quickly about solar", "intent": "urgency"},
                    {"template": "What's the fastest installation timeline?", "intent": "speed"},
                    {"template": "Can you give me a quick overview?", "intent": "efficiency"},
                    {"template": "I don't have time for a long consultation", "intent": "time_constraint"},
                    {"template": "What's the most important thing I need to know?", "intent": "priority"},
                    {"template": "I need to decide by Friday", "intent": "deadline"}
                ],
                expected_behaviors=[
                    "efficiency_focus",
                    "urgency_creation",
                    "quick_qualification",
                    "rapid_decision_support"
                ]
            )
        ]
    
    async def run_comprehensive_simulation(self) -> List[SimulationResult]:
        """Run comprehensive conversation simulation"""
        
        print("🤖 Starting Automated Conversation Simulation...")
        
        results = []
        
        for simulation in self.simulations:
            print(f"\n🎭 Simulating: {simulation.user_type} customer")
            
            try:
                result = await self._simulate_conversation(simulation)
                results.append(result)
                
                status = "✅ SUCCESS" if result.success else "❌ FAILED"
                print(f"  {status} - Quality: {result.conversation_quality_score:.1%}, Revenue: ${result.revenue_generated:.0f}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {str(e)}")
                results.append(SimulationResult(
                    simulation_id=simulation.simulation_id,
                    user_type=simulation.user_type,
                    total_messages=0,
                    conversation_duration=0.0,
                    response_times=[],
                    revenue_generated=0.0,
                    lead_quality_achieved="error",
                    conversation_quality_score=0.0,
                    technical_accuracy_score=0.0,
                    user_satisfaction_score=0.0,
                    errors=[str(e)],
                    success=False
                ))
        
        # Calculate overall performance
        self._calculate_performance_metrics(results)
        
        return results
    
    async def _simulate_conversation(self, simulation: ConversationSimulation) -> SimulationResult:
        """Simulate a single conversation"""
        
        start_time = datetime.utcnow()
        conversation_context = simulation.user_profile.copy()
        conversation_history = []
        response_times = []
        errors = []
        
        # Generate conversation messages
        messages = self._generate_conversation_messages(simulation)
        
        for i, message in enumerate(messages):
            try:
                message_start = datetime.utcnow()
                
                # Process message through revenue optimization system
                response = await self.revenue_system.process_conversation_for_revenue_optimization(
                    session_id=f"sim_{simulation.simulation_id}_{i}",
                    message=message["content"],
                    conversation_context=conversation_context,
                    conversation_history=conversation_history
                )
                
                message_end = datetime.utcnow()
                response_time = (message_end - message_start).total_seconds()
                response_times.append(response_time)
                
                # Add to conversation history
                conversation_history.append({
                    "user": message["content"],
                    "bot": response.get("content", ""),
                    "intent": message["intent"],
                    "response_time": response_time,
                    "revenue_data": response.get("revenue_optimization", {})
                })
                
                # Update context based on response
                self._update_conversation_context(conversation_context, message, response)
                
            except Exception as e:
                errors.append(f"Message {i}: {str(e)}")
                response_times.append(5.0)  # Default error response time
        
        end_time = datetime.utcnow()
        conversation_duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        revenue_data = conversation_history[-1].get("revenue_data", {}) if conversation_history else {}
        lead_score = revenue_data.get("lead_score", {})
        
        revenue_generated = lead_score.get("revenue_potential", 0.0)
        lead_quality_achieved = lead_score.get("quality_tier", "unqualified")
        
        # Calculate quality scores
        conversation_quality_score = self._calculate_conversation_quality(conversation_history, simulation)
        technical_accuracy_score = self._calculate_technical_accuracy(conversation_history)
        user_satisfaction_score = self._calculate_user_satisfaction(conversation_history, simulation)
        
        # Determine success
        success = (
            conversation_quality_score >= 0.7 and
            technical_accuracy_score >= 0.8 and
            user_satisfaction_score >= 0.7 and
            len(errors) == 0 and
            np.mean(response_times) <= 3.0
        )
        
        return SimulationResult(
            simulation_id=simulation.simulation_id,
            user_type=simulation.user_type,
            total_messages=len(messages),
            conversation_duration=conversation_duration,
            response_times=response_times,
            revenue_generated=revenue_generated,
            lead_quality_achieved=lead_quality_achieved,
            conversation_quality_score=conversation_quality_score,
            technical_accuracy_score=technical_accuracy_score,
            user_satisfaction_score=user_satisfaction_score,
            errors=errors,
            success=success
        )
    
    def _generate_conversation_messages(self, simulation: ConversationSimulation) -> List[Dict[str, str]]:
        """Generate conversation messages based on simulation template"""
        
        messages = []
        templates = simulation.message_templates.copy()
        
        # Generate messages up to conversation_length
        for i in range(simulation.conversation_length):
            if not templates:
                break
            
            # Select template (weighted by position in conversation)
            template_weights = [1.0 / (j + 1) for j in range(len(templates))]
            selected_template = random.choices(templates, weights=template_weights)[0]
            
            # Customize message based on user profile
            message_content = self._customize_message(selected_template["template"], simulation.user_profile)
            
            messages.append({
                "content": message_content,
                "intent": selected_template["intent"],
                "template": selected_template["template"]
            })
            
            # Remove used template to avoid repetition
            templates.remove(selected_template)
        
        return messages
    
    def _customize_message(self, template: str, user_profile: Dict[str, Any]) -> str:
        """Customize message template with user profile data"""
        
        message = template
        
        # Replace placeholders
        if "{bill_amount}" in message:
            message = message.replace("{bill_amount}", str(user_profile.get("bill_amount", 250)))
        
        if "{borough}" in message:
            message = message.replace("{borough}", user_profile.get("borough", "manhattan").title())
        
        if "{neighborhood}" in message:
            message = message.replace("{neighborhood}", user_profile.get("neighborhood", "downtown").title())
        
        return message
    
    def _update_conversation_context(self, context: Dict[str, Any], message: Dict[str, str], response: Dict[str, Any]):
        """Update conversation context based on message and response"""
        
        # Update based on user message
        if "bill" in message["content"].lower() and "$" in message["content"]:
            # Extract bill amount if mentioned
            import re
            bill_match = re.search(r'\$(\d+)', message["content"])
            if bill_match:
                context["bill_amount"] = float(bill_match.group(1))
        
        if "timeline" in message["content"].lower() or "when" in message["content"].lower():
            # Update timeline urgency
            if "urgent" in message["content"].lower() or "quickly" in message["content"].lower():
                context["timeline"] = "urgent"
        
        # Update based on response
        revenue_data = response.get("revenue_optimization", {})
        if revenue_data.get("lead_score"):
            lead_score = revenue_data["lead_score"]
            context["lead_quality_tier"] = lead_score.get("quality_tier")
            context["revenue_potential"] = lead_score.get("revenue_potential")
    
    def _calculate_conversation_quality(self, conversation_history: List[Dict[str, Any]], simulation: ConversationSimulation) -> float:
        """Calculate conversation quality score"""
        
        if not conversation_history:
            return 0.0
        
        quality_factors = []
        
        # Response relevance
        relevant_responses = sum(1 for msg in conversation_history if len(msg.get("bot", "")) > 20)
        relevance_score = relevant_responses / len(conversation_history)
        quality_factors.append(relevance_score)
        
        # Technical engagement (for technical simulations)
        if simulation.user_type in ["high_intent", "researcher"]:
            technical_responses = sum(1 for msg in conversation_history 
                                    if any(term in msg.get("bot", "").lower() 
                                          for term in ["kw", "kwh", "system", "solar", "panel"]))
            technical_score = technical_responses / len(conversation_history)
            quality_factors.append(technical_score)
        
        # NYC-specific content
        nyc_responses = sum(1 for msg in conversation_history 
                          if any(term in msg.get("bot", "").lower() 
                                for term in ["nyc", "new york", "con ed", "pseg", "manhattan", "brooklyn"]))
        nyc_score = nyc_responses / len(conversation_history)
        quality_factors.append(nyc_score)
        
        # Revenue optimization integration
        revenue_responses = sum(1 for msg in conversation_history 
                              if msg.get("revenue_data", {}).get("lead_score"))
        revenue_score = revenue_responses / len(conversation_history)
        quality_factors.append(revenue_score)
        
        return sum(quality_factors) / len(quality_factors)
    
    def _calculate_technical_accuracy(self, conversation_history: List[Dict[str, Any]]) -> float:
        """Calculate technical accuracy score"""
        
        if not conversation_history:
            return 0.0
        
        accuracy_factors = []
        
        for msg in conversation_history:
            bot_response = msg.get("bot", "").lower()
            
            # Check for technical accuracy indicators
            accuracy_score = 0.5  # Base score
            
            # Solar-specific terms
            if any(term in bot_response for term in ["solar", "panel", "system"]):
                accuracy_score += 0.2
            
            # Energy units
            if any(term in bot_response for term in ["kw", "kwh", "kilowatt"]):
                accuracy_score += 0.2
            
            # NYC-specific accuracy
            if any(term in bot_response for term in ["con ed", "pseg", "nyserda"]):
                accuracy_score += 0.1
            
            accuracy_factors.append(min(1.0, accuracy_score))
        
        return sum(accuracy_factors) / len(accuracy_factors)
    
    def _calculate_user_satisfaction(self, conversation_history: List[Dict[str, Any]], simulation: ConversationSimulation) -> float:
        """Calculate user satisfaction score"""
        
        if not conversation_history:
            return 0.0
        
        satisfaction_factors = []
        
        for msg in conversation_history:
            bot_response = msg.get("bot", "").lower()
            user_intent = msg.get("intent", "")
            
            satisfaction_score = 0.5  # Base score
            
            # Intent-specific satisfaction
            if user_intent == "technical" and any(term in bot_response for term in ["kw", "system", "panel"]):
                satisfaction_score += 0.3
            
            elif user_intent == "savings" and any(term in bot_response for term in ["save", "savings", "money"]):
                satisfaction_score += 0.3
            
            elif user_intent == "objection" and any(term in bot_response for term in ["understand", "address", "concern"]):
                satisfaction_score += 0.3
            
            elif user_intent == "urgency" and any(term in bot_response for term in ["quickly", "fast", "timeline"]):
                satisfaction_score += 0.3
            
            # Positive language indicators
            if any(term in bot_response for term in ["great", "excellent", "perfect", "helpful"]):
                satisfaction_score += 0.2
            
            satisfaction_factors.append(min(1.0, satisfaction_score))
        
        return sum(satisfaction_factors) / len(satisfaction_factors)
    
    def _calculate_performance_metrics(self, results: List[SimulationResult]):
        """Calculate overall performance metrics"""
        
        if not results:
            return
        
        successful_simulations = [r for r in results if r.success]
        
        self.performance_metrics = {
            "total_simulations": len(results),
            "successful_simulations": len(successful_simulations),
            "success_rate": len(successful_simulations) / len(results),
            "avg_conversation_quality": np.mean([r.conversation_quality_score for r in results]),
            "avg_technical_accuracy": np.mean([r.technical_accuracy_score for r in results]),
            "avg_user_satisfaction": np.mean([r.user_satisfaction_score for r in results]),
            "avg_response_time": np.mean([np.mean(r.response_times) for r in results if r.response_times]),
            "total_revenue_generated": sum([r.revenue_generated for r in results]),
            "avg_revenue_per_simulation": np.mean([r.revenue_generated for r in results])
        }


# Test runner functions
async def run_automated_simulation(revenue_system: RevenueOptimizationSystem) -> List[SimulationResult]:
    """Run automated conversation simulation"""
    
    simulator = AutomatedConversationSimulator(revenue_system)
    return await simulator.run_comprehensive_simulation()


def generate_simulation_report(results: List[SimulationResult], performance_metrics: Dict[str, Any]) -> str:
    """Generate simulation test report"""
    
    report = f"""
# 🤖 Automated Conversation Simulation Report

## 📊 Overall Performance
- **Total Simulations**: {performance_metrics['total_simulations']}
- **Success Rate**: {performance_metrics['success_rate']:.1%}
- **Average Conversation Quality**: {performance_metrics['avg_conversation_quality']:.1%}
- **Average Technical Accuracy**: {performance_metrics['avg_technical_accuracy']:.1%}
- **Average User Satisfaction**: {performance_metrics['avg_user_satisfaction']:.1%}
- **Average Response Time**: {performance_metrics['avg_response_time']:.2f}s
- **Total Revenue Generated**: ${performance_metrics['total_revenue_generated']:.0f}

## 🎭 Simulation Results
"""
    
    for result in results:
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        report += f"""
### {result.user_type.title()} Customer
- **Status**: {status}
- **Messages**: {result.total_messages}
- **Duration**: {result.conversation_duration:.1f}s
- **Quality Score**: {result.conversation_quality_score:.1%}
- **Technical Accuracy**: {result.technical_accuracy_score:.1%}
- **User Satisfaction**: {result.user_satisfaction_score:.1%}
- **Revenue Generated**: ${result.revenue_generated:.0f}
- **Lead Quality**: {result.lead_quality_achieved}
"""
        
        if result.errors:
            report += f"- **Errors**: {', '.join(result.errors)}\n"
    
    # Performance benchmarks
    report += "\n## 🎯 Performance Benchmarks\n"
    
    benchmarks = {
        "Conversation Quality": (performance_metrics['avg_conversation_quality'], 0.8),
        "Technical Accuracy": (performance_metrics['avg_technical_accuracy'], 0.9),
        "User Satisfaction": (performance_metrics['avg_user_satisfaction'], 0.8),
        "Response Time": (performance_metrics['avg_response_time'], 3.0, "lower_better")
    }
    
    for benchmark, (actual, target) in benchmarks.items():
        if benchmark == "Response Time":
            passed = actual <= target
            comparison = f"{actual:.2f}s <= {target}s"
        else:
            passed = actual >= target
            comparison = f"{actual:.1%} >= {target:.1%}"
        
        status = "✅ PASS" if passed else "❌ FAIL"
        report += f"- **{benchmark}**: {comparison} {status}\n"
    
    return report


if __name__ == "__main__":
    print("🤖 Automated Conversation Simulator")
    print("Simulates realistic user conversations for testing")

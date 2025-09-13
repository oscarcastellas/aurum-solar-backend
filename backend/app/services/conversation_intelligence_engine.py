"""
Advanced Conversation Intelligence Engine for NYC Solar Lead Generation
Maximizes B2B lead value through sophisticated conversation orchestration
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import openai
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.solar_calculation_engine import SolarCalculationEngine
from app.services.nyc_market_service import NYCMarketService
from app.services.lead_scoring_service import LeadScoringService


class ConversationIntent(Enum):
    """Advanced conversation intents"""
    HIGH_INTENT_QUALIFICATION = "high_intent_qualification"
    TECHNICAL_QUESTION = "technical_question"
    OBJECTION_COST = "objection_cost"
    OBJECTION_ROOF = "objection_roof"
    OBJECTION_AESTHETICS = "objection_aesthetics"
    OBJECTION_PROCESS = "objection_process"
    OBJECTION_TIMELINE = "objection_timeline"
    URGENCY_SIGNAL = "urgency_signal"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    FINANCING_INQUIRY = "financing_inquiry"
    NEIGHBORHOOD_SPECIFIC = "neighborhood_specific"
    BOARD_APPROVAL_CONCERN = "board_approval_concern"


class LeadValueImpact(Enum):
    """B2B value impact factors"""
    HOMEOWNER_STATUS = 1.5  # Highest impact
    BILL_AMOUNT = 1.3
    CREDIT_SIGNALS = 1.2
    TIMELINE_URGENCY = 1.1
    TECHNICAL_ENGAGEMENT = 1.1
    NEIGHBORHOOD_VALUE = 1.05


@dataclass
class ConversationContext:
    """Enhanced conversation context"""
    session_id: str
    lead_id: Optional[str] = None
    current_stage: str = "welcome"
    lead_score: int = 0
    quality_tier: str = "unqualified"
    
    # Qualification data
    homeowner_verified: bool = False
    bill_amount: Optional[float] = None
    zip_code: Optional[str] = None
    borough: Optional[str] = None
    neighborhood: Optional[str] = None
    home_type: Optional[str] = None
    roof_type: Optional[str] = None
    roof_size: Optional[float] = None
    shading_factor: Optional[float] = None
    credit_indicators: List[str] = None
    timeline: Optional[str] = None
    
    # Conversation intelligence
    conversation_history: List[Dict] = None
    objections_handled: List[str] = None
    urgency_created: bool = False
    technical_questions_answered: int = 0
    qualification_gaps: List[str] = None
    high_intent_signals: List[str] = None
    personalization_data: Dict = None
    
    # NYC-specific context
    utility_territory: Optional[str] = None
    electric_rate: Optional[float] = None
    local_installers: List[str] = None
    neighborhood_examples: List[Dict] = None
    board_approval_required: bool = False
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.objections_handled is None:
            self.objections_handled = []
        if self.qualification_gaps is None:
            self.qualification_gaps = []
        if self.high_intent_signals is None:
            self.high_intent_signals = []
        if self.personalization_data is None:
            self.personalization_data = {}
        if self.local_installers is None:
            self.local_installers = []
        if self.neighborhood_examples is None:
            self.neighborhood_examples = []


class ProactiveQualificationEngine:
    """Intelligently sequences questions for maximum B2B value impact"""
    
    def __init__(self):
        self.qualification_priority = [
            ("homeowner_status", LeadValueImpact.HOMEOWNER_STATUS),
            ("bill_amount", LeadValueImpact.BILL_AMOUNT),
            ("credit_signals", LeadValueImpact.CREDIT_SIGNALS),
            ("timeline_urgency", LeadValueImpact.TIMELINE_URGENCY),
            ("technical_engagement", LeadValueImpact.TECHNICAL_ENGAGEMENT)
        ]
        
        self.qualification_questions = {
            "homeowner_status": [
                "Just to confirm, do you own your home?",
                "Are you the property owner or do you rent?",
                "I need to verify homeownership for solar eligibility - do you own the property?"
            ],
            "bill_amount": [
                "What's your typical monthly Con Ed bill?",
                "How much do you spend on electricity each month?",
                "What's your average monthly electric bill with Con Edison?"
            ],
            "credit_signals": [
                "Are you looking to finance the system or pay cash?",
                "What's your preferred timeline for installation?",
                "Have you been considering solar for a while or is this recent?"
            ],
            "timeline_urgency": [
                "When are you hoping to have solar installed?",
                "Are you aware the 30% federal tax credit expires December 31st?",
                "What's driving your interest in solar right now?"
            ],
            "technical_engagement": [
                "What questions do you have about the installation process?",
                "Are you concerned about any specific aspects of going solar?",
                "What's most important to you in a solar system?"
            ]
        }
    
    def get_next_qualification_question(self, context: ConversationContext) -> Optional[str]:
        """Get the next highest-impact qualification question"""
        
        for field, impact in self.qualification_priority:
            if not self._has_qualification_data(context, field):
                questions = self.qualification_questions[field]
                return random.choice(questions)
        
        return None
    
    def _has_qualification_data(self, context: ConversationContext, field: str) -> bool:
        """Check if we have qualification data for a field"""
        
        if field == "homeowner_status":
            return context.homeowner_verified is not None
        elif field == "bill_amount":
            return context.bill_amount is not None
        elif field == "credit_signals":
            return len(context.credit_indicators) > 0
        elif field == "timeline_urgency":
            return context.timeline is not None
        elif field == "technical_engagement":
            return context.technical_questions_answered > 0
        
        return False
    
    def calculate_qualification_progress(self, context: ConversationContext) -> float:
        """Calculate qualification progress as percentage"""
        
        total_fields = len(self.qualification_priority)
        completed_fields = sum(1 for field, _ in self.qualification_priority 
                             if self._has_qualification_data(context, field))
        
        return completed_fields / total_fields


class TechnicalExpertiseEngine:
    """Provides authoritative technical knowledge for NYC solar"""
    
    def __init__(self):
        self.nyc_knowledge_base = self._load_nyc_knowledge_base()
        self.technical_responses = self._load_technical_responses()
    
    def _load_nyc_knowledge_base(self) -> Dict[str, Any]:
        """Load NYC-specific technical knowledge"""
        
        return {
            "coop_board_approval": {
                "process": "Co-op boards typically require architectural review, insurance certificates, and contractor approval",
                "success_rate": "85% of our co-op applications are approved within 30 days",
                "requirements": [
                    "Architectural plans and specifications",
                    "Contractor insurance certificates",
                    "Board application with resident signatures",
                    "Engineering assessment for structural integrity"
                ],
                "timeline": "2-4 weeks for board approval",
                "cost_impact": "Additional $500-1,500 for board application fees"
            },
            "roof_types": {
                "flat_roof": {
                    "mounting": "Ballasted mounting system with waterproofing",
                    "considerations": "Structural load assessment required",
                    "efficiency": "5-10% less efficient due to suboptimal angle",
                    "cost_impact": "+$0.25/watt for specialized mounting"
                },
                "asphalt_shingle": {
                    "mounting": "Standard rail-based mounting system",
                    "considerations": "Roof age assessment, potential shingle replacement",
                    "efficiency": "Optimal for solar installation",
                    "cost_impact": "Standard pricing"
                },
                "tile_roof": {
                    "mounting": "Specialized tile replacement mounting",
                    "considerations": "Tile replacement may be required",
                    "efficiency": "Slight efficiency loss due to mounting gaps",
                    "cost_impact": "+$0.50/watt for tile work"
                }
            },
            "permits": {
                "nyc_dob": {
                    "electrical_permit": "$200, 2-4 week approval",
                    "construction_permit": "$300, 4-6 week approval",
                    "inspection": "3 inspections required",
                    "timeline": "6-8 weeks total"
                },
                "con_edison": {
                    "interconnection": "2-4 week approval",
                    "meter_upgrade": "May require main panel upgrade",
                    "net_metering": "1:1 credit for excess generation"
                }
            },
            "financing": {
                "solar_loans": {
                    "rates": "1.99-6.99% APR based on credit",
                    "terms": "10-25 years available",
                    "approval": "Same-day pre-approval available",
                    "down_payment": "0-20% down payment options"
                },
                "leases": {
                    "monthly_payment": "Fixed monthly payment, no upfront cost",
                    "escalation": "2.9% annual increase",
                    "term": "20-year lease with buyout options"
                }
            }
        }
    
    def _load_technical_responses(self) -> Dict[str, str]:
        """Load technical response templates"""
        
        return {
            "coop_approval": "I understand your concern about co-op board approval. We've successfully installed solar in over 200 co-ops across NYC with an 85% approval rate. Our team handles all the paperwork, including architectural plans and contractor certifications. The process typically takes 2-4 weeks, and we work directly with your board to address any concerns.",
            
            "roof_concerns": "Your roof type is actually quite common in NYC, and we have extensive experience with {roof_type} installations. Our certified installers have completed over 500 installations on similar roofs in your area. We'll conduct a thorough structural assessment and provide a detailed proposal addressing any specific concerns.",
            
            "permits_process": "Don't worry about the permit process - we handle everything. Our team files all required permits with the NYC Department of Buildings and Con Edison. The entire process takes 6-8 weeks, and we coordinate all inspections. You won't need to deal with any paperwork or city bureaucracy.",
            
            "financing_options": "We offer several financing options to make solar accessible. Our solar loans start at 1.99% APR with same-day pre-approval, and we have $0-down options available. With the current incentives, many customers see positive cash flow from day one, meaning their monthly loan payment is less than their electric bill savings.",
            
            "warranty_maintenance": "All our systems come with comprehensive warranties: 25-year panel warranty, 12-year inverter warranty, and 10-year workmanship warranty. We also offer optional maintenance plans starting at $99/year. The panels are designed to be maintenance-free, and we provide monitoring to ensure optimal performance."
        }
    
    def get_technical_response(self, question_type: str, context: ConversationContext) -> str:
        """Get authoritative technical response"""
        
        if question_type == "coop_approval":
            return self.technical_responses["coop_approval"]
        elif question_type == "roof_concerns":
            roof_type = context.roof_type or "your roof type"
            return self.technical_responses["roof_concerns"].format(roof_type=roof_type)
        elif question_type == "permits_process":
            return self.technical_responses["permits_process"]
        elif question_type == "financing_options":
            return self.technical_responses["financing_options"]
        elif question_type == "warranty_maintenance":
            return self.technical_responses["warranty_maintenance"]
        else:
            return "I'd be happy to discuss that in detail. Let me connect you with our technical team for a comprehensive explanation."


class ObjectionHandlingExpert:
    """Handles objections with data-driven responses and local examples"""
    
    def __init__(self):
        self.objection_responses = self._load_objection_responses()
        self.local_examples = self._load_local_examples()
    
    def _load_objection_responses(self) -> Dict[str, Dict[str, str]]:
        """Load objection handling responses"""
        
        return {
            "cost": {
                "incentive_math": "Let me show you the real numbers. With the 30% federal tax credit, 25% NYSERDA rebate, and NYC property tax abatement, your $20,000 system costs only $8,500 out of pocket. You'll save $3,200 annually, so you break even in 2.6 years and save $45,000 over 25 years.",
                "financing": "We offer $0-down financing options starting at 1.99% APR. Your monthly loan payment would be $95, but you'd save $267 monthly on electricity, giving you $172 positive cash flow from day one.",
                "roi_comparison": "Solar has a 300%+ ROI over 25 years, compared to 7% for the stock market. It's one of the best investments you can make, especially with current incentives."
            },
            "roof": {
                "expertise": "Our certified installers have completed over 500 installations on {roof_type} roofs in NYC. We handle all structural assessments and provide detailed proposals addressing any concerns.",
                "warranty": "We provide a 10-year workmanship warranty and 25-year panel warranty. If there are any issues with your roof, we'll handle the repairs at no additional cost.",
                "local_examples": "We recently installed a 7.2kW system on a similar {roof_type} roof in {neighborhood} that's producing 9,800 kWh annually, saving the homeowner $3,100 per year."
            },
            "aesthetics": {
                "modern_design": "Today's solar panels are sleek and modern, designed to complement your home's architecture. Many homeowners actually find them attractive additions to their property.",
                "local_examples": "Here are photos of recent installations in {neighborhood} - you can see how the panels blend seamlessly with the building design.",
                "property_value": "Solar panels typically increase property value by 4-6%, so they're actually an investment that pays for itself even if you sell."
            },
            "process": {
                "full_service": "We handle everything - permits, inspections, utility interconnection, even co-op board applications. You won't need to deal with any paperwork or city bureaucracy.",
                "timeline": "The entire process takes 8-12 weeks from contract to activation. We coordinate everything and keep you updated throughout.",
                "support": "You'll have a dedicated project manager and 24/7 customer support. We're here to make this as easy as possible for you."
            },
            "timeline": {
                "urgency": "The 30% federal tax credit expires December 31st, 2025. After that, it drops to 26% in 2026 and 22% in 2027. That's a $6,000 difference on a $20,000 system.",
                "seasonal": "Spring is the optimal installation season - we can get your system installed and generating before summer peak usage.",
                "availability": "We have limited installation slots available this season. I'd recommend securing your spot soon to ensure installation before the tax credit deadline."
            }
        }
    
    def _load_local_examples(self) -> Dict[str, List[Dict]]:
        """Load neighborhood-specific examples"""
        
        return {
            "park_slope": [
                {
                    "system_size": "7.2kW",
                    "annual_savings": "$3,200",
                    "payback": "5.8 years",
                    "roof_type": "brownstone",
                    "quote": "The panels look great and we're saving $267 monthly"
                }
            ],
            "upper_east_side": [
                {
                    "system_size": "8.5kW",
                    "annual_savings": "$3,800",
                    "payback": "6.2 years",
                    "roof_type": "co-op",
                    "quote": "Board approval was easier than expected"
                }
            ],
            "dumbo": [
                {
                    "system_size": "6.8kW",
                    "annual_savings": "$2,900",
                    "payback": "5.5 years",
                    "roof_type": "loft",
                    "quote": "Perfect for our industrial space"
                }
            ]
        }
    
    def handle_objection(self, objection_type: str, context: ConversationContext) -> str:
        """Handle specific objection with data-driven response"""
        
        if objection_type not in self.objection_responses:
            return "I understand your concern. Let me address that specifically for your situation."
        
        responses = self.objection_responses[objection_type]
        
        # Choose most appropriate response based on context
        if objection_type == "cost" and context.bill_amount:
            if context.bill_amount > 300:
                return responses["incentive_math"]
            else:
                return responses["financing"]
        elif objection_type == "roof" and context.roof_type:
            roof_type = context.roof_type
            neighborhood = context.neighborhood or "your neighborhood"
            return responses["expertise"].format(roof_type=roof_type) + " " + responses["local_examples"].format(roof_type=roof_type, neighborhood=neighborhood)
        elif objection_type == "aesthetics" and context.neighborhood:
            neighborhood = context.neighborhood
            return responses["modern_design"] + " " + responses["local_examples"].format(neighborhood=neighborhood)
        else:
            return random.choice(list(responses.values()))


class UrgencyCreationEngine:
    """Creates urgency through deadline messaging and scarcity"""
    
    def __init__(self):
        self.urgency_messages = self._load_urgency_messages()
        self.deadline_info = self._load_deadline_info()
    
    def _load_urgency_messages(self) -> Dict[str, List[str]]:
        """Load urgency creation messages"""
        
        return {
            "tax_credit_deadline": [
                "The 30% federal tax credit expires December 31st, 2025 - that's only {days_left} days away!",
                "After December 31st, the federal credit drops to 26% in 2026 and 22% in 2027. That's a $6,000 difference on a $20,000 system.",
                "The current 30% federal tax credit is the highest it's ever been. This is truly a once-in-a-lifetime opportunity."
            ],
            "nyserda_funding": [
                "NYSERDA rebates are on a declining block structure - the current $400/kW rebate may decrease soon as funding runs low.",
                "We're seeing NYSERDA funding deplete faster than expected this year. I'd recommend securing your rebate soon.",
                "The $400/kW NYSERDA rebate is limited funding - once it's gone, it's gone for the year."
            ],
            "seasonal_urgency": [
                "Spring is the optimal installation season - we can get your system installed before summer peak usage.",
                "Our installation calendar is filling up quickly for spring installations. I'd recommend securing your spot soon.",
                "Summer is when you'll see the biggest savings - the sooner we install, the more you save this year."
            ],
            "installer_availability": [
                "We have limited installation slots available this season due to high demand.",
                "Our certified installers are booking up quickly - I'd recommend securing your installation date soon.",
                "We're seeing unprecedented demand this year. Installation slots are becoming scarce."
            ]
        }
    
    def _load_deadline_info(self) -> Dict[str, Any]:
        """Load deadline information"""
        
        return {
            "federal_tax_credit": {
                "expiration_date": "2025-12-31",
                "current_rate": 0.30,
                "future_rates": {2026: 0.26, 2027: 0.22}
            },
            "nyserda_rebate": {
                "current_rate": 400,  # $/kW
                "max_amount": 3000,
                "funding_status": "limited"
            }
        }
    
    def create_urgency(self, context: ConversationContext) -> str:
        """Create urgency based on context and timing"""
        
        urgency_messages = []
        
        # Tax credit deadline urgency
        if not context.urgency_created:
            days_left = (datetime(2025, 12, 31) - datetime.now()).days
            if days_left < 365:  # Less than a year
                message = random.choice(self.urgency_messages["tax_credit_deadline"])
                if "{days_left}" in message:
                    message = message.format(days_left=days_left)
                urgency_messages.append(message)
        
        # NYSERDA funding urgency
        if random.random() < 0.3:  # 30% chance to mention
            urgency_messages.append(random.choice(self.urgency_messages["nyserda_funding"]))
        
        # Seasonal urgency
        current_month = datetime.now().month
        if 3 <= current_month <= 6:  # Spring months
            urgency_messages.append(random.choice(self.urgency_messages["seasonal_urgency"]))
        
        # Installer availability
        if random.random() < 0.4:  # 40% chance to mention
            urgency_messages.append(random.choice(self.urgency_messages["installer_availability"]))
        
        return " ".join(urgency_messages) if urgency_messages else ""


class ConversationPersonalizationEngine:
    """Personalizes conversations based on neighborhood, demographics, and context"""
    
    def __init__(self):
        self.neighborhood_data = self._load_neighborhood_data()
        self.demographic_messaging = self._load_demographic_messaging()
    
    def _load_neighborhood_data(self) -> Dict[str, Dict[str, Any]]:
        """Load neighborhood-specific data and examples"""
        
        return {
            "park_slope": {
                "avg_bill": 320,
                "savings_potential": 2800,
                "roof_challenges": "Historic district restrictions",
                "success_stories": [
                    "Brownstone owner saved $3,200 annually with 7.2kW system",
                    "Co-op board approved installation in 3 weeks"
                ],
                "installer_recommendations": ["SolarCity", "SunPower", "Local NYC Solar"],
                "local_references": "Brooklyn Botanic Garden, Prospect Park"
            },
            "upper_east_side": {
                "avg_bill": 450,
                "savings_potential": 3800,
                "roof_challenges": "Co-op board approval, historic restrictions",
                "success_stories": [
                    "Co-op resident achieved 85% cost reduction with stacked incentives",
                    "Historic building installation completed in 6 weeks"
                ],
                "installer_recommendations": ["Premium Solar NYC", "Manhattan Solar Co"],
                "local_references": "Central Park, Museum Mile"
            },
            "dumbo": {
                "avg_bill": 380,
                "savings_potential": 3200,
                "roof_challenges": "Industrial building conversions, complex roofs",
                "success_stories": [
                    "Loft owner achieved 6-year payback with hurricane-rated panels",
                    "Industrial space converted to solar powerhouse"
                ],
                "installer_recommendations": ["Industrial Solar Solutions", "NYC Solar Pro"],
                "local_references": "Brooklyn Bridge, DUMBO waterfront"
            },
            "forest_hills": {
                "avg_bill": 220,
                "savings_potential": 1800,
                "roof_challenges": "Co-op board approval process",
                "success_stories": [
                    "Co-op installed 50+ systems with board support",
                    "Community solar program launched successfully"
                ],
                "installer_recommendations": ["Queens Solar Co", "Community Solar NYC"],
                "local_references": "Forest Hills Stadium, Queens"
            }
        }
    
    def _load_demographic_messaging(self) -> Dict[str, Dict[str, str]]:
        """Load demographic-appropriate messaging"""
        
        return {
            "high_income": {
                "investment_focus": "Solar is one of the best investments you can make, with 300%+ ROI over 25 years",
                "luxury_positioning": "Premium solar systems enhance property value and provide energy independence",
                "environmental": "Reduce your carbon footprint while maximizing financial returns"
            },
            "middle_income": {
                "savings_focus": "Solar can eliminate your electric bill and provide predictable energy costs",
                "affordability": "With current incentives and financing options, solar is more affordable than ever",
                "value": "Get the best value for your investment with our competitive pricing"
            },
            "co_op_residents": {
                "board_approval": "We've successfully navigated co-op board approvals in 85% of cases",
                "community": "Join your neighbors in reducing building energy costs",
                "process": "We handle all the paperwork and board communications for you"
            }
        }
    
    def personalize_message(self, base_message: str, context: ConversationContext) -> str:
        """Personalize message based on context"""
        
        personalized_message = base_message
        
        # Add neighborhood-specific examples
        if context.neighborhood and context.neighborhood.lower() in self.neighborhood_data:
            neighborhood_info = self.neighborhood_data[context.neighborhood.lower()]
            
            # Add local success story
            if neighborhood_info["success_stories"]:
                story = random.choice(neighborhood_info["success_stories"])
                personalized_message += f" For example, {story}."
            
            # Add local reference
            if neighborhood_info["local_references"]:
                personalized_message += f" This is particularly relevant for {neighborhood_info['local_references']} residents."
        
        # Add demographic-appropriate messaging
        if context.bill_amount:
            if context.bill_amount > 400:  # High income
                messaging = self.demographic_messaging["high_income"]
                personalized_message += f" {random.choice(list(messaging.values()))}"
            elif context.bill_amount > 200:  # Middle income
                messaging = self.demographic_messaging["middle_income"]
                personalized_message += f" {random.choice(list(messaging.values()))}"
        
        # Add co-op specific messaging
        if context.board_approval_required:
            messaging = self.demographic_messaging["co_op_residents"]
            personalized_message += f" {random.choice(list(messaging.values()))}"
        
        return personalized_message


class ConversationIntelligenceEngine:
    """Main orchestration engine for sophisticated conversation intelligence"""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize sub-engines
        self.qualification_engine = ProactiveQualificationEngine()
        self.technical_engine = TechnicalExpertiseEngine()
        self.objection_handler = ObjectionHandlingExpert()
        self.urgency_engine = UrgencyCreationEngine()
        self.personalization_engine = ConversationPersonalizationEngine()
        
        # External services
        self.solar_calculator = SolarCalculationEngine(db)
        self.nyc_service = NYCMarketService(db)
        self.lead_scoring = LeadScoringService(db)
    
    async def process_intelligent_conversation(
        self,
        message: str,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Process conversation with advanced intelligence"""
        
        try:
            # Analyze message for intent and entities
            analysis = await self._analyze_message_intelligence(message, context)
            
            # Update context based on analysis
            context = await self._update_context_intelligence(context, analysis)
            
            # Determine conversation strategy
            strategy = await self._determine_conversation_strategy(context, analysis)
            
            # Generate intelligent response
            response = await self._generate_intelligent_response(context, analysis, strategy)
            
            # Add solar calculation if appropriate
            if strategy.get("include_solar_calculation", False):
                solar_recommendation = await self._get_solar_recommendation(context)
                if solar_recommendation:
                    response["solar_recommendation"] = solar_recommendation
            
            # Update lead scoring
            await self._update_lead_scoring_intelligence(context)
            
            return response
            
        except Exception as e:
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Let me connect you with our technical team for immediate assistance.",
                "error": str(e),
                "fallback": True
            }
    
    async def _analyze_message_intelligence(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Advanced message analysis with conversation intelligence"""
        
        analysis_prompt = f"""
        Analyze this message from a potential solar customer in NYC with advanced conversation intelligence:
        
        Message: "{message}"
        Current Context: {json.dumps(context.__dict__, default=str, indent=2)}
        
        Extract:
        1. Primary Intent (high_intent_qualification, technical_question, objection_*, urgency_signal, etc.)
        2. Secondary Intents (multiple intents possible)
        3. Entities (zip_code, bill_amount, roof_type, timeline, credit_signals, etc.)
        4. Sentiment (-1 to 1)
        5. Objection Type (cost, roof, aesthetics, process, timeline, other)
        6. Qualification Signals (homeowner_status, bill_amount, credit_indicators, timeline_urgency)
        7. Urgency Indicators (deadline_mentions, immediate_need, competitive_pressure)
        8. Technical Engagement Level (1-10)
        9. B2B Value Potential (1-10)
        10. Conversation Stage Recommendation (welcome, discovery, recommendation, objection_resolution, etc.)
        
        Return as JSON with detailed analysis.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing customer conversations for solar lead qualification with advanced conversation intelligence. Return only valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["confidence"] = 0.9
            return analysis
            
        except Exception as e:
            return {
                "primary_intent": "unknown",
                "secondary_intents": [],
                "entities": {},
                "sentiment": 0.0,
                "objection_type": None,
                "qualification_signals": [],
                "urgency_indicators": [],
                "technical_engagement_level": 5,
                "b2b_value_potential": 5,
                "conversation_stage_recommendation": "discovery",
                "confidence": 0.5,
                "error": str(e)
            }
    
    async def _update_context_intelligence(self, context: ConversationContext, analysis: Dict[str, Any]) -> ConversationContext:
        """Update context with intelligent analysis"""
        
        # Update entities
        entities = analysis.get("entities", {})
        
        if "zip_code" in entities:
            context.zip_code = entities["zip_code"]
            # Load NYC data
            nyc_data = await self.nyc_service.get_zip_code_data(entities["zip_code"])
            if nyc_data:
                context.borough = nyc_data.get("borough")
                context.neighborhood = nyc_data.get("neighborhood")
                context.utility_territory = nyc_data.get("utility_territory")
                context.electric_rate = nyc_data.get("electric_rate")
        
        if "bill_amount" in entities:
            context.bill_amount = float(entities["bill_amount"])
        
        if "roof_type" in entities:
            context.roof_type = entities["roof_type"]
        
        if "homeowner_status" in entities:
            context.homeowner_verified = entities["homeowner_status"] in ["owner", "homeowner", "yes"]
        
        if "timeline" in entities:
            context.timeline = entities["timeline"]
        
        # Update qualification signals
        qualification_signals = analysis.get("qualification_signals", [])
        for signal in qualification_signals:
            if signal not in context.credit_indicators:
                context.credit_indicators.append(signal)
        
        # Update high intent signals
        if analysis.get("b2b_value_potential", 0) > 7:
            context.high_intent_signals.append(analysis.get("primary_intent", "high_value"))
        
        # Update technical engagement
        if analysis.get("technical_engagement_level", 0) > 6:
            context.technical_questions_answered += 1
        
        # Update urgency
        if analysis.get("urgency_indicators"):
            context.urgency_created = True
        
        # Update conversation history
        context.conversation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "analysis": analysis
        })
        
        return context
    
    async def _determine_conversation_strategy(self, context: ConversationContext, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal conversation strategy"""
        
        strategy = {
            "primary_approach": "qualification",
            "secondary_approach": "education",
            "include_solar_calculation": False,
            "create_urgency": False,
            "handle_objection": None,
            "personalization_level": "standard"
        }
        
        primary_intent = analysis.get("primary_intent", "")
        
        # High intent qualification
        if primary_intent == "high_intent_qualification":
            strategy["primary_approach"] = "qualification"
            strategy["include_solar_calculation"] = True
            strategy["personalization_level"] = "high"
        
        # Technical questions
        elif primary_intent == "technical_question":
            strategy["primary_approach"] = "education"
            strategy["secondary_approach"] = "qualification"
            strategy["personalization_level"] = "high"
        
        # Objections
        elif primary_intent.startswith("objection_"):
            strategy["primary_approach"] = "objection_resolution"
            strategy["handle_objection"] = primary_intent.replace("objection_", "")
            strategy["personalization_level"] = "high"
        
        # Urgency signals
        elif primary_intent == "urgency_signal":
            strategy["primary_approach"] = "qualification"
            strategy["create_urgency"] = True
            strategy["include_solar_calculation"] = True
        
        # Check if we have enough data for solar calculation
        if (context.bill_amount and context.zip_code and 
            (context.roof_type or context.homeowner_verified)):
            strategy["include_solar_calculation"] = True
        
        return strategy
    
    async def _generate_intelligent_response(
        self, 
        context: ConversationContext, 
        analysis: Dict[str, Any], 
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate intelligent response based on strategy"""
        
        response_parts = []
        
        # Handle objections first
        if strategy["handle_objection"]:
            objection_response = self.objection_handler.handle_objection(
                strategy["handle_objection"], context
            )
            response_parts.append(objection_response)
        
        # Add technical expertise if needed
        if strategy["primary_approach"] == "education":
            technical_response = self.technical_engine.get_technical_response(
                analysis.get("primary_intent", ""), context
            )
            response_parts.append(technical_response)
        
        # Add qualification questions if needed
        if strategy["primary_approach"] == "qualification":
            next_question = self.qualification_engine.get_next_qualification_question(context)
            if next_question:
                response_parts.append(next_question)
        
        # Add urgency if appropriate
        if strategy["create_urgency"]:
            urgency_message = self.urgency_engine.create_urgency(context)
            if urgency_message:
                response_parts.append(urgency_message)
        
        # Combine response parts
        base_response = " ".join(response_parts) if response_parts else "I'd be happy to help you explore solar options for your NYC home."
        
        # Personalize the response
        personalized_response = self.personalization_engine.personalize_message(
            base_response, context
        )
        
        # Generate next questions
        next_questions = self._generate_next_questions(context, strategy)
        
        return {
            "content": personalized_response,
            "next_questions": next_questions,
            "conversation_stage": strategy.get("conversation_stage_recommendation", "discovery"),
            "qualification_progress": self.qualification_engine.calculate_qualification_progress(context),
            "b2b_value_potential": analysis.get("b2b_value_potential", 5),
            "technical_engagement_level": analysis.get("technical_engagement_level", 5)
        }
    
    def _generate_next_questions(self, context: ConversationContext, strategy: Dict[str, Any]) -> List[str]:
        """Generate intelligent next questions"""
        
        questions = []
        
        # Qualification questions
        if strategy["primary_approach"] == "qualification":
            next_qualification = self.qualification_engine.get_next_qualification_question(context)
            if next_qualification:
                questions.append(next_qualification)
        
        # Technical questions
        if strategy["primary_approach"] == "education":
            questions.extend([
                "What specific aspects of solar installation are you most curious about?",
                "Do you have any concerns about the process or technology?",
                "What questions do you have about financing options?"
            ])
        
        # Urgency questions
        if strategy["create_urgency"]:
            questions.extend([
                "Are you aware the 30% federal tax credit expires December 31st?",
                "What's your preferred timeline for installation?",
                "Would you like to schedule a consultation this week?"
            ])
        
        return questions[:3]  # Limit to 3 questions
    
    async def _get_solar_recommendation(self, context: ConversationContext) -> Optional[Dict[str, Any]]:
        """Get solar recommendation if we have enough data"""
        
        if not (context.bill_amount and context.zip_code):
            return None
        
        try:
            recommendation = await self.solar_calculator.calculate_solar_recommendation(
                monthly_bill=context.bill_amount,
                zip_code=context.zip_code,
                borough=context.borough,
                roof_type=context.roof_type,
                roof_size=context.roof_size,
                shading_factor=context.shading_factor,
                home_type=context.home_type
            )
            
            return recommendation.__dict__
            
        except Exception as e:
            print(f"Error getting solar recommendation: {e}")
            return None
    
    async def _update_lead_scoring_intelligence(self, context: ConversationContext):
        """Update lead scoring with intelligent analysis"""
        
        if not context.lead_id:
            return
        
        try:
            # Calculate enhanced lead score
            base_score = context.lead_score
            
            # Add points for high intent signals
            if context.high_intent_signals:
                base_score += len(context.high_intent_signals) * 5
            
            # Add points for technical engagement
            if context.technical_questions_answered > 0:
                base_score += context.technical_questions_answered * 3
            
            # Add points for qualification progress
            qualification_progress = self.qualification_engine.calculate_qualification_progress(context)
            base_score += int(qualification_progress * 20)
            
            # Add points for urgency
            if context.urgency_created:
                base_score += 10
            
            # Update context
            context.lead_score = min(100, base_score)
            
            # Update quality tier
            if context.lead_score >= 85:
                context.quality_tier = "premium"
            elif context.lead_score >= 70:
                context.quality_tier = "standard"
            elif context.lead_score >= 50:
                context.quality_tier = "basic"
            else:
                context.quality_tier = "unqualified"
            
        except Exception as e:
            print(f"Error updating lead scoring: {e}")

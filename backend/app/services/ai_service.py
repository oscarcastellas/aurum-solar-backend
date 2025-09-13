"""
AI service for lead analysis and chat functionality
"""

import openai
from typing import Dict, Any, List
import json
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY


class AIService:
    """AI service for lead analysis and chat"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def analyze_lead(self, lead) -> Dict[str, Any]:
        """Analyze a lead using AI to determine quality and insights"""
        
        # Create prompt for lead analysis
        prompt = f"""
        Analyze this solar lead for the NYC market:
        
        Lead Details:
        - Name: {lead.first_name} {lead.last_name}
        - Email: {lead.email}
        - Phone: {lead.phone}
        - Property: {lead.property_address}, {lead.city}, {lead.state} {lead.zip_code}
        - Property Type: {lead.property_type}
        - Square Footage: {lead.square_footage}
        - Monthly Electric Bill: ${lead.monthly_electric_bill}
        - Roof Type: {lead.roof_type}
        - Roof Condition: {lead.roof_condition}
        
        Please provide:
        1. Lead quality score (0-100)
        2. Lead quality category (hot, warm, cold)
        3. Estimated lead value ($75-300)
        4. Key insights about this lead
        5. NYC market specific insights
        6. Recommended next steps
        
        Return as JSON with keys: score, quality, estimated_value, insights, nyc_insights, recommendations
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a solar lead analysis expert specializing in the NYC market. Provide detailed, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return {
                "score": analysis.get("score", 50),
                "quality": analysis.get("quality", "cold"),
                "estimated_value": analysis.get("estimated_value", 150),
                "insights": analysis.get("insights", ""),
                "nyc_insights": analysis.get("nyc_insights", ""),
                "recommendations": analysis.get("recommendations", ""),
                "conversation_data": {
                    "analysis_timestamp": str(datetime.utcnow()),
                    "ai_model": "gpt-4",
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
        except Exception as e:
            # Fallback analysis
            return {
                "score": 50,
                "quality": "cold",
                "estimated_value": 150,
                "insights": f"AI analysis failed: {str(e)}",
                "nyc_insights": "",
                "recommendations": "Manual review required",
                "conversation_data": {
                    "error": str(e),
                    "analysis_timestamp": str(datetime.utcnow())
                }
            }
    
    async def chat_with_lead(self, message: str, lead_context: Dict[str, Any]) -> str:
        """Chat with a lead using AI"""
        
        system_prompt = f"""
        You are a solar energy consultant for Aurum Solar, specializing in the NYC market.
        
        Lead Context:
        - Name: {lead_context.get('first_name', '')} {lead_context.get('last_name', '')}
        - Property: {lead_context.get('property_address', '')}, {lead_context.get('city', '')}, {lead_context.get('state', '')} {lead_context.get('zip_code', '')}
        - Monthly Electric Bill: ${lead_context.get('monthly_electric_bill', 'Unknown')}
        - Property Type: {lead_context.get('property_type', 'Unknown')}
        
        Your goals:
        1. Qualify the lead for solar installation
        2. Gather additional property details
        3. Explain NYC solar incentives and benefits
        4. Schedule a consultation if appropriate
        5. Be helpful, professional, and knowledgeable about NYC solar market
        
        Keep responses concise but informative. Ask follow-up questions to gather more details.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I apologize, but I'm experiencing technical difficulties. Please try again later or contact us directly at (555) 123-4567. Error: {str(e)}"
    
    async def generate_lead_questions(self, lead_context: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions for a lead"""
        
        prompt = f"""
        Generate 5-7 follow-up questions for this solar lead in NYC:
        
        Lead Context:
        - Property: {lead_context.get('property_address', '')}, {lead_context.get('city', '')}, {lead_context.get('state', '')} {lead_context.get('zip_code', '')}
        - Monthly Electric Bill: ${lead_context.get('monthly_electric_bill', 'Unknown')}
        - Property Type: {lead_context.get('property_type', 'Unknown')}
        - Roof Type: {lead_context.get('roof_type', 'Unknown')}
        
        Focus on:
        1. Property details (roof condition, shading, etc.)
        2. Energy usage patterns
        3. Timeline for installation
        4. Budget considerations
        5. NYC-specific incentives and programs
        
        Return as a JSON array of questions.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a solar sales expert. Generate targeted follow-up questions to qualify leads."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            questions = json.loads(response.choices[0].message.content)
            return questions if isinstance(questions, list) else []
            
        except Exception as e:
            # Fallback questions
            return [
                "What is the condition of your roof?",
                "Are there any trees or buildings that shade your roof?",
                "When are you looking to install solar?",
                "What is your budget range for solar installation?",
                "Have you looked into NYC solar incentives?",
                "Do you own or rent this property?",
                "What questions do you have about solar energy?"
            ]

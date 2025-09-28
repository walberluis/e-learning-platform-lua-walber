"""
Google Gemini API integration client.
Infrastructure Layer - Integration Package
"""

import google.generativeai as genai
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import asyncio
import httpx

load_dotenv()

class GeminiClient:
    """
    Google Gemini API client for AI-powered features.
    Implements external AI service integration.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    async def generate_content(self, prompt: str) -> str:
        """
        Generate content using Gemini AI with a custom prompt.
        
        Args:
            prompt: The prompt to send to the AI
            
        Returns:
            AI-generated content as text
        """
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            print(f"Error generating content: {e}")
            return ""
    
    async def generate_learning_recommendations(self, user_profile: Dict, learning_history: List[Dict]) -> str:
        """
        Generate personalized learning recommendations using Gemini AI.
        
        Args:
            user_profile: User's learning profile and preferences
            learning_history: User's past learning activities and performance
            
        Returns:
            AI-generated recommendations as text
        """
        prompt = self._build_recommendation_prompt(user_profile, learning_history)
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return "Unable to generate recommendations at this time. Please try again later."
    
    async def generate_chatbot_response(self, user_question: str, context: Dict) -> str:
        """
        Generate chatbot response using Gemini AI.
        
        Args:
            user_question: User's question or message
            context: Conversation context and user information
            
        Returns:
            AI-generated response
        """
        prompt = self._build_chatbot_prompt(user_question, context)
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            print(f"Error generating chatbot response: {e}")
            return "I'm sorry, I'm having trouble understanding right now. Could you please rephrase your question?"
    
    async def generate_quiz_questions(self, topic: str, difficulty: str, module_title: str, count: int = 10) -> Dict:
        """
        Generate quiz questions for a learning module using Gemini AI.
        
        Args:
            topic: Main learning topic
            difficulty: Difficulty level (iniciante, intermediario, avancado)
            module_title: Title of the specific module
            count: Number of questions to generate
            
        Returns:
            Generated questions in structured format
        """
        difficulty_descriptions = {
            "iniciante": "nível iniciante (conceitos básicos, exemplos simples)",
            "intermediario": "nível intermediário (conceitos mais complexos, aplicações práticas)",
            "avancado": "nível avançado (conceitos especializados, cenários complexos)"
        }
        
        difficulty_desc = difficulty_descriptions.get(difficulty, difficulty_descriptions["iniciante"])
        
        prompt = f"""
Crie {count} questões de múltipla escolha sobre "{topic}" com foco em "{module_title}" para {difficulty_desc}.

Cada questão deve ter:
- Uma pergunta clara e objetiva
- 5 alternativas (a, b, c, d, e)
- Apenas uma resposta correta
- Explicação detalhada da resposta correta

IMPORTANTE: Retorne APENAS um JSON válido no seguinte formato:
[
  {{
    "pergunta": "Texto da pergunta aqui",
    "alternativas": {{
      "a": "Primeira opção",
      "b": "Segunda opção", 
      "c": "Terceira opção",
      "d": "Quarta opção",
      "e": "Quinta opção"
    }},
    "resposta_correta": "a",
    "explicacao": "Explicação detalhada da resposta correta"
  }}
]

Não inclua texto adicional, apenas o JSON válido com {count} questões.
"""
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return {"questions": response.text, "status": "success"}
        except Exception as e:
            print(f"Error generating quiz questions: {e}")
            return {"questions": None, "status": "error", "error": str(e)}
    
    async def analyze_learning_content(self, content: str, content_type: str) -> Dict:
        """
        Analyze learning content to extract key information and difficulty level.
        
        Args:
            content: The learning content to analyze
            content_type: Type of content (video, text, quiz, etc.)
            
        Returns:
            Analysis results including difficulty, topics, and recommendations
        """
        prompt = f"""
        Analyze the following {content_type} learning content and provide:
        1. Difficulty level (beginner, intermediate, advanced)
        2. Main topics covered
        3. Estimated study time
        4. Prerequisites
        5. Learning objectives
        
        Content: {content[:1000]}...  # Limit content length
        
        Provide the analysis in JSON format.
        """
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return {"analysis": response.text, "status": "success"}
        except Exception as e:
            print(f"Error analyzing content: {e}")
            return {"analysis": "Content analysis unavailable", "status": "error"}
    
    def _build_recommendation_prompt(self, user_profile: Dict, learning_history: List[Dict]) -> str:
        """Build prompt for learning recommendations."""
        profile_text = f"""
        User Profile:
        - Name: {user_profile.get('nome', 'Unknown')}
        - Learning Profile: {user_profile.get('perfil_aprend', 'Not specified')}
        - Email: {user_profile.get('email', 'Not provided')}
        """
        
        history_text = "Learning History:\n"
        for item in learning_history[-5:]:  # Last 5 items
            history_text += f"- {item.get('titulo', 'Unknown')}: Progress {item.get('progresso', 0)}%\n"
        
        prompt = f"""
        You are an AI learning advisor for an e-learning platform. Based on the user's profile and learning history, 
        provide personalized learning recommendations.
        
        {profile_text}
        
        {history_text}
        
        Please provide:
        1. 3-5 specific course recommendations
        2. Learning path suggestions
        3. Study schedule recommendations
        4. Areas for improvement
        
        Keep recommendations practical and encouraging. Focus on the user's learning style and progress.
        """
        
        return prompt
    
    def _build_chatbot_prompt(self, user_question: str, context: Dict) -> str:
        """Build prompt for chatbot responses."""
        context_text = f"""
        Context:
        - User: {context.get('user_name', 'Student')}
        - Current Course: {context.get('current_course', 'None')}
        - Learning Level: {context.get('level', 'Beginner')}
        """
        
        prompt = f"""
        You are a helpful AI assistant for an e-learning platform. Answer the user's question in a friendly, 
        educational manner. Provide clear, concise, and helpful responses.
        
        {context_text}
        
        User Question: {user_question}
        
        Provide a helpful response that encourages learning and provides actionable advice when possible.
        """
        
        return prompt

class APIGateway:
    """
    API Gateway for external service integrations.
    Manages communication with external APIs and services.
    """
    
    def __init__(self):
        self.base_timeout = 30.0
        self.max_retries = 3
    
    async def make_external_request(self, url: str, method: str = "GET", data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to external APIs with retry logic.
        
        Args:
            url: Target URL
            method: HTTP method
            data: Request data
            headers: Request headers
            
        Returns:
            Response data
        """
        async with httpx.AsyncClient(timeout=self.base_timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, json=data, headers=headers)
                    elif method.upper() == "PUT":
                        response = await client.put(url, json=data, headers=headers)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    response.raise_for_status()
                    return {"data": response.json(), "status": "success"}
                    
                except httpx.RequestError as e:
                    if attempt == self.max_retries - 1:
                        return {"error": str(e), "status": "error"}
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
                except httpx.HTTPStatusError as e:
                    return {"error": f"HTTP {e.response.status_code}: {e.response.text}", "status": "error"}

# Global instances
gemini_client = GeminiClient()
api_gateway = APIGateway()

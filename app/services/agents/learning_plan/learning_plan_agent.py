"""
Learning Plan Agent - Generates personalized study plans based on user parameters
"""

import os
import time
from typing import Dict, Any


from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.logging.logging_config import get_logger

logger = get_logger(__name__)

class LearningPlanAgent:
    """Agent responsible for generating personalized learning plans"""
    
    def __init__(self):
        # Load system prompt from co-located prompt file
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "learning_plan_system.prompt")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError("Learning plan system prompt not found")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=1500,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=True,
        )
    
    async def generate_learning_plan(self, settings: Dict[str, Any]) -> str:
        """
        Generate a personalized learning plan based on user settings
        
        Args:
            settings: Dictionary containing learning plan parameters:
                - testName: str
                - planDurationDays: int
                - hoursPerDay: int
                - startingProficiency: str
                - targetScore: int
                - timing: dict with timePerItemSec
                - skills: list of skill names
                - constraints: dict with contentBalance and enemySets
        
        Returns:
            Generated learning plan as JSON string
        """
        try:
            logger.info(f"Generating learning plan for settings: {settings}")
            
            # Prepare the user message with all parameters
            user_message = self._format_user_message(settings)
            
            # Use LangChain messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]
            
            # Call LangChain LLM
            start_time = time.time()
            resp = self.llm.invoke(messages)
            end_time = time.time()
            logger.info(f"LLM invocation time: {end_time - start_time:.2f} seconds")
            learning_plan = getattr(resp, "content", "") or ""
            
            logger.info(f"Learning plan generated successfully, length: {len(learning_plan)} characters")
            return learning_plan
            
        except Exception as e:
            logger.error(f"Error generating learning plan: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return f"Error generating learning plan: {str(e)}"
    
    def _format_user_message(self, settings: Dict[str, Any]) -> str:
        """Format the user settings into a clear message for the AI"""
        
        # Extract parameters
        test_name = settings.get('testName', 'Unknown Test')
        duration_days = settings.get('planDurationDays', 14)
        hours_per_day = settings.get('hoursPerDay', 2)
        target_score = settings.get('targetScore', 75)
        skills = settings.get('skills', [])
        constraints = settings.get('constraints', {})
        enemy_sets = constraints.get('enemySets', [])
        
        # Format skills list
        skills_text = ', '.join(skills) if skills else 'All core skills'
        
        # Format enemy sets
        enemy_text = ', '.join(enemy_sets) if enemy_sets else 'None specified'
        
        # Create the user message
        message = f"""{test_name} study plan: {duration_days} days, {hours_per_day}h/day. Target: {target_score}%. Skills: {skills_text}. Focus: {enemy_text if enemy_text != 'None specified' else 'balanced'}."""
        return message.strip()

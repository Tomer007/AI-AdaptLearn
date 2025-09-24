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
            
            # Check if we have minimal settings - use default plan
            if not settings or len(settings) < 3:
                logger.info("Minimal settings provided, using default adaptive plan")
                return self._get_default_plan()
            
            # Calculate scaling to determine if we should use direct scaling or LLM
            total_hours = settings.get('planDurationDays', 14) * settings.get('hoursPerDay', 1)
            
            # Enforce minimum of 8 hours
            if total_hours < 8:
                logger.info(f"Total hours {total_hours} is below minimum of 8 hours, adjusting to 8 hours")
                total_hours = 8
                # Adjust days or hours per day to meet minimum
                if settings.get('planDurationDays', 14) >= 8:
                    settings['hoursPerDay'] = max(1, 8 // settings.get('planDurationDays', 14))
                else:
                    settings['planDurationDays'] = 8
                    settings['hoursPerDay'] = 1
            
            scaling_factor = total_hours / 8.0
            
            # For significant scaling (>2x or <0.5x), use direct scaling for better control
            if scaling_factor > 2.0 or scaling_factor < 0.5:
                logger.info(f"Using direct scaling for factor {scaling_factor:.2f}")
                return self._generate_scaled_plan(settings)
            
            # For moderate scaling, use LLM with explicit instructions
            logger.info(f"Using LLM with explicit scaling instructions for factor {scaling_factor:.2f}")
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
    
    def _get_default_plan(self) -> str:
        """Return the default English adaptive plan when no user input is provided"""
        return """**Test Preparation Plan (8 Hours)**

**Introduction – 30-40 minutes**
Diagnostic Test 1 – Simulates the actual exam
Relative scoring
Summary report with error review option
(No question repetition)

**Adaptive Lesson 1 – 45 minutes**
More questions on weak areas
Fewer questions on strong areas
Wrong answer → additional attempt

**Adaptive Lesson 2 – 45 minutes**

**Diagnostic Test 2 – Same as the first**
Progress relative scoring
Summary report with error review option

**Adaptive Lesson 3 – 45 minutes**
**Adaptive Lesson 4 – 45 minutes**

**Diagnostic Test 3 – Includes summary report + errors**
**Diagnostic Test 4 – Includes summary report + errors**
**Diagnostic Test 5 – Includes summary report + errors**

---

**Key Features:**
- **5 Diagnostic Tests** with comprehensive reporting
- **4 Adaptive Lessons** focusing on weak areas  
- **Progress Tracking** with relative scoring
- **Error Analysis** with detailed mistake review
- **No Question Repetition** - each question appears only once

**Let's get started on this journey to master your test! You've got this. Let's do this!**"""
    
    def _generate_scaled_plan(self, settings: Dict[str, Any]) -> str:
        """Generate a scaled plan based on user settings without LLM call"""
        test_name = settings.get('testName', 'Unknown Test')
        duration_days = settings.get('planDurationDays', 14)
        hours_per_day = settings.get('hoursPerDay', 1)
        target_score = settings.get('targetScore', 75)
        
        total_hours = duration_days * hours_per_day
        
        # Enforce minimum of 8 hours
        if total_hours < 8:
            total_hours = 8
            if duration_days >= 8:
                hours_per_day = max(1, 8 // duration_days)
            else:
                duration_days = 8
                hours_per_day = 1
        
        scaling_factor = total_hours / 8.0
        
        num_tests = max(1, int(5 * scaling_factor))
        num_lessons = max(1, int(4 * scaling_factor))
        lesson_duration = max(15, int(45 * scaling_factor))
        
        # Generate scaled English plan
        scaled_plan = f"""**Test Preparation Plan ({total_hours} Hours)**

**Introduction – {max(15, int(30 * scaling_factor))}-{max(20, int(40 * scaling_factor))} minutes**

**Diagnostic Tests – {num_tests} tests:**
"""
        
        for i in range(1, num_tests + 1):
            scaled_plan += f"Diagnostic Test {i} – Simulates the actual exam\n"
            if i == 1:
                scaled_plan += "Relative scoring\nSummary report with error review option\n(No question repetition)\n\n"
            elif i == 2:
                scaled_plan += "Progress relative scoring\nSummary report with error review option\n\n"
            else:
                scaled_plan += "Includes summary report + errors\n"
        
        scaled_plan += f"\n**Adaptive Lessons – {num_lessons} lessons:**\n"
        
        for i in range(1, num_lessons + 1):
            scaled_plan += f"**Adaptive Lesson {i} – {lesson_duration} minutes**\n"
            if i == 1:
                scaled_plan += "More questions on weak areas\nFewer questions on strong areas\nWrong answer → additional attempt\n\n"
            else:
                scaled_plan += "\n"
        
        scaled_plan += f"""
---

**Personalized Plan:**
- **Total Duration:** {duration_days} days, {hours_per_day} hours per day
- **Total Hours:** {total_hours} hours (scaled from 8-hour base)
- **Scaling Factor:** {scaling_factor:.2f}
- **Target Score:** {target_score}%
- **Diagnostic Tests:** {num_tests} (was 5, now {num_tests})
- **Adaptive Lessons:** {num_lessons} (was 4, now {num_lessons})
- **Lesson Duration:** {lesson_duration} minutes (was 45, now {lesson_duration})

**Let's get started on this journey to master your test! You've got this. Let's do this!**
"""
        
        return scaled_plan
    
    def _format_user_message(self, settings: Dict[str, Any]) -> str:
        """Format the user settings into a clear message for the AI with adaptive planning logic"""
        
        # Extract parameters
        test_name = settings.get('testName', 'Unknown Test')
        duration_days = settings.get('planDurationDays', 14)
        hours_per_day = settings.get('hoursPerDay', 1)  # Default to 1 hour for 8-hour base plan
        target_score = settings.get('targetScore', 75)
        skills = settings.get('skills', [])
        constraints = settings.get('constraints', {})
        enemy_sets = constraints.get('enemySets', [])
        
        # Calculate total hours and scaling factor
        total_hours = duration_days * hours_per_day
        
        # Enforce minimum of 8 hours
        if total_hours < 8:
            total_hours = 8
            if duration_days >= 8:
                hours_per_day = max(1, 8 // duration_days)
            else:
                duration_days = 8
                hours_per_day = 1
        
        base_hours = 8  # Base plan is 8 hours
        scaling_factor = total_hours / base_hours if base_hours > 0 else 1
        
        # Format skills list
        skills_text = ', '.join(skills) if skills else 'All core skills'
        
        # Format enemy sets (weak areas to focus on)
        enemy_text = ', '.join(enemy_sets) if enemy_sets else 'None specified'
        
        # Determine if we need to scale the plan
        needs_scaling = abs(scaling_factor - 1.0) > 0.1  # More than 10% difference
        
        # Create the user message with adaptive planning context
        message = f"""Adaptive Study Plan Request:
Test: {test_name}
Duration: {duration_days} days, {hours_per_day} hours per day
Total Hours: {total_hours} hours
Target Score: {target_score}%
Skills Focus: {skills_text}
Weak Areas to Emphasize: {enemy_text if enemy_text != 'None specified' else 'balanced approach'}

SCALING CALCULATIONS:
Base Plan: 8 hours total
User Request: {total_hours} hours total
Scaling Factor: {scaling_factor:.2f}
Diagnostic Tests: 5 × {scaling_factor:.2f} = {5 * scaling_factor:.1f} tests
Adaptive Lessons: 4 × {scaling_factor:.2f} = {4 * scaling_factor:.1f} lessons
Lesson Duration: 45 × {scaling_factor:.2f} = {45 * scaling_factor:.1f} minutes each

CRITICAL: You MUST scale the base template proportionally. Do NOT just return the base 8-hour template. 
Show the actual scaled numbers in your response. For {total_hours} hours, provide a detailed schedule with {5 * scaling_factor:.0f} diagnostic tests and {4 * scaling_factor:.0f} adaptive lessons distributed over {duration_days} days."""
        
        return message.strip()

"""
Learning Plan Agent - Generates personalized study plans from JSON diagnostic score input
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.logging.logging_config import get_logger
from app.models.adaptive_learning import (
    CategoryWeight, 
    DiagnosticScore, 
    LearningPlanInput
)

logger = get_logger(__name__)

class LearningPlanAgent:
    """Agent responsible for generating personalized learning plans from JSON diagnostic score input"""
    
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
            max_tokens=2000,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=False,
        )
    
    async def generate_learning_plan_from_json(self, json_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a personalized learning plan from JSON input format with diagnostic scores.
        Uses the adaptive time allocation algorithm to calculate optimal time distribution.
        
        Args:
            json_input: Dictionary containing:
                - assessment_name: str
                - user_id: str
                - plan_version: str
                - total_available_time_minutes: int
                - timestamp: str
                - category_weights: List[Dict[str, Any]]
                - initial_diagnostic_scores: List[Dict[str, Any]]
        
        Returns:
            Generated learning plan as JSON dictionary with time allocations
        """
        try:
            logger.info(f"Generating learning plan from JSON input: {json_input}")
            
            # Extract input data
            assessment_name = json_input.get('assessment_name', 'Unknown Assessment')
            user_id = json_input.get('user_id', 'unknown')
            plan_version = json_input.get('plan_version', 'v1.0')
            total_available_time_minutes = json_input.get('total_available_time_minutes', 480)
            timestamp = json_input.get('timestamp', datetime.now().isoformat())
            category_weights = json_input.get('category_weights', [])
            initial_diagnostic_scores = json_input.get('initial_diagnostic_scores', [])
            
            # Validate input data
            if not category_weights or not initial_diagnostic_scores:
                raise ValueError("category_weights and initial_diagnostic_scores are required")
            
            if len(category_weights) != len(initial_diagnostic_scores):
                raise ValueError("category_weights and initial_diagnostic_scores must have the same length")
            
            # Create input data for the prompt
            prompt_input = {
                "assessment_name": assessment_name,
                "user_id": user_id,
                "plan_version": plan_version,
                "total_available_time_minutes": total_available_time_minutes,
                "timestamp": timestamp,
                "category_weights": category_weights,
                "initial_diagnostic_scores": initial_diagnostic_scores
            }
            
            # Create user message with the input data
            user_message = f"""Please generate a learning plan using the adaptive time allocation algorithm with the following input data:

{json.dumps(prompt_input, indent=2)}

Please return ONLY the JSON output format as specified in the system prompt. Do not include any additional text or explanations."""
            
            # Use LangChain messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_message)
            ]
            
            # Call LangChain LLM
            logger.info("Calling LLM to generate learning plan")
            response = self.llm.invoke(messages)
            learning_plan_text = getattr(response, "content", "") or ""
            
            # Parse the JSON response from the LLM
            try:
                # Extract JSON from the response (in case there's extra text)
                json_start = learning_plan_text.find('{')
                json_end = learning_plan_text.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = learning_plan_text[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    raise ValueError("No valid JSON found in LLM response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                logger.error(f"LLM response: {learning_plan_text}")
                # Fallback: use the adaptive time allocation algorithm directly
                result = self._calculate_adaptive_time_allocation(prompt_input)
            
            logger.info(f"Learning plan generated successfully for {assessment_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating learning plan from JSON: {str(e)}")
            return {
                "error": f"Error generating learning plan: {str(e)}",
                "assessment_name": json_input.get('assessment_name', 'Unknown'),
                "user_id": json_input.get('user_id', 'unknown'),
                "plan_version": json_input.get('plan_version', 'v1.0'),
                "remaining_time_minutes": 0,
                "total_time_allocated": 0,
                "timestamp": datetime.now().isoformat(),
                "plan": []
            }
    
    def _calculate_adaptive_time_allocation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate adaptive time allocation using the mathematical algorithm.
        This is a fallback method when LLM parsing fails.
        """
        try:
            category_weights = input_data['category_weights']
            initial_diagnostic_scores = input_data['initial_diagnostic_scores']
            total_time = input_data['total_available_time_minutes']
            
            # Step 1: Calculate gaps (d_i = 1 - s_i)
            gaps = []
            for score_data in initial_diagnostic_scores:
                score = score_data['score']
                gap = 1.0 - score
                gaps.append(gap)
            
            # Step 2: Calculate priority scores (p_i = w_i * (1 + d_i))
            priorities = []
            for i, weight_data in enumerate(category_weights):
                weight = weight_data['weight']
                gap = gaps[i]
                priority = weight * (1 + gap)
                priorities.append(priority)
            
            # Step 3: Calculate normalized priorities (P_i = p_i / sum(p_j))
            total_priority = sum(priorities)
            normalized_priorities = [p / total_priority for p in priorities]
            
            # Step 4: Calculate time allocation (t_i = T * P_i)
            plan = []
            for i, weight_data in enumerate(category_weights):
                category = weight_data['category']
                weight = weight_data['weight']
                score = initial_diagnostic_scores[i]['score']
                gap = gaps[i]
                priority = priorities[i]
                normalized_priority = normalized_priorities[i]
                allocated_minutes = int(total_time * normalized_priority)
                allocated_hours = allocated_minutes / 60.0
                
                plan.append({
                    "category": category,
                    "weight": weight,
                    "diagnostic_score": score,
                    "gap": gap,
                    "priority": priority,
                    "normalized_priority": normalized_priority,
                    "allocated_minutes": allocated_minutes,
                    "allocated_hours": round(allocated_hours, 1)
                })
            
            return {
                "assessment_name": input_data['assessment_name'],
                "user_id": input_data['user_id'],
                "plan_version": input_data['plan_version'],
                "remaining_time_minutes": total_time,
                "total_time_allocated": total_time,
                "timestamp": input_data['timestamp'],
                "plan": plan
            }
            
        except Exception as e:
            logger.error(f"Error in adaptive time allocation calculation: {str(e)}")
            raise

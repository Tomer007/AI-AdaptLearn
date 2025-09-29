"""
Learning Plan Agent - Generates personalized study plans from JSON diagnostic score input
"""

import os
from typing import Dict, Any, List
from datetime import datetime

from app.logging.logging_config import get_logger
from app.services.adaptive_time_allocation import AdaptiveTimeAllocation
from app.models.adaptive_learning import (
    CategoryWeight, 
    DiagnosticScore, 
    LearningPlanInput
)

logger = get_logger(__name__)

class LearningPlanAgent:
    """Agent responsible for generating personalized learning plans from JSON diagnostic score input"""
    
    def __init__(self):
        # Initialize adaptive time allocation
        self.adaptive_time_allocation = AdaptiveTimeAllocation()
    
    async def generate_learning_plan_from_json(self, json_input: Dict[str, Any]) -> Dict[str, Any]:
        
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
            
            # Convert to the format expected by adaptive time allocation
            weights = []
            scores = []
            
            for weight_data in category_weights:
                weights.append(CategoryWeight(
                    category=weight_data['category'],
                    weight=weight_data['weight']
                ))
            
            for score_data in initial_diagnostic_scores:
                scores.append(DiagnosticScore(
                    category=score_data['category'],
                    score=score_data['score']
                ))
            
            # Create learning plan input
            plan_input = LearningPlanInput(
                assessment_name=assessment_name,
                user_id=user_id,
                total_available_time_minutes=total_available_time_minutes,
                category_weights=weights,
                initial_diagnostic_scores=scores
            )
            
            # Generate adaptive learning plan
            adaptive_plan = self.adaptive_time_allocation.generate_plan(plan_input)
            
            # Convert to the expected JSON output format
            result = {
                "assessment_name": adaptive_plan.assessment_name,
                "user_id": adaptive_plan.user_id,
                "plan_version": plan_version,
                "remaining_time_minutes": adaptive_plan.remaining_time_minutes,
                "total_time_allocated": adaptive_plan.total_time_allocated,
                "timestamp": timestamp,
                "plan": []
            }
            
            # Add plan details
            for allocation in adaptive_plan.plan:
                result["plan"].append({
                    "category": allocation.category,
                    "weight": allocation.weight,
                    "diagnostic_score": allocation.diagnostic_score,
                    "gap": allocation.gap,
                    "priority": allocation.priority,
                    "normalized_priority": allocation.normalized_priority,
                    "allocated_minutes": allocation.allocated_minutes,
                    "allocated_hours": allocation.allocated_hours
                })
            
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

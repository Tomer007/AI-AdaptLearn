"""
Adaptive Time Allocation Algorithm
Implements the mathematical algorithm for personalized learning plan time allocation
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.adaptive_learning import (
    CategoryWeight, 
    DiagnosticScore, 
    TimeAllocation, 
    AdaptiveLearningPlan,
    LearningPlanInput
)
from app.logging.logging_config import get_logger

logger = get_logger(__name__)


class AdaptiveTimeAllocation:
    """Implements the adaptive time allocation algorithm"""
    
    def __init__(self):
        self.logger = logger
    
    def calculate_adaptive_time_allocation(
        self,
        category_weights: List[CategoryWeight],
        diagnostic_scores: List[DiagnosticScore],
        total_time_minutes: int
    ) -> List[TimeAllocation]:
        """
        Calculate adaptive time allocation using the specified algorithm:
        
        1. Gap Calculation: d_i = 1 - s_i
        2. Priority Score: p_i = w_i * (1 + d_i)
        3. Normalized Priorities: P_i = p_i / sum(p_j)
        4. Time Allocation: t_i = T * P_i
        
        Args:
            category_weights: List of category weights (must sum to 1.0)
            diagnostic_scores: List of diagnostic scores (0.0 to 1.0)
            total_time_minutes: Total available time in minutes
            
        Returns:
            List of TimeAllocation objects with calculated values
        """
        try:
            self.logger.info(f"Calculating adaptive time allocation for {len(category_weights)} categories")
            
            # Validate inputs
            self._validate_inputs(category_weights, diagnostic_scores, total_time_minutes)
            
            # Create a mapping of category to diagnostic score
            score_map = {score.category: score.score for score in diagnostic_scores}
            
            # Calculate time allocation for each category
            allocations = []
            
            for weight in category_weights:
                category = weight.category
                weight_value = weight.weight
                
                # Get diagnostic score for this category (default to 0.5 if not found)
                diagnostic_score = score_map.get(category, 0.5)
                
                # Step 1: Gap Calculation
                gap = 1.0 - diagnostic_score
                
                # Step 2: Priority Score
                priority = weight_value * (1.0 + gap)
                
                allocations.append({
                    'category': category,
                    'weight': weight_value,
                    'diagnostic_score': diagnostic_score,
                    'gap': gap,
                    'priority': priority
                })
            
            # Step 3: Normalize Priorities
            total_priority = sum(alloc['priority'] for alloc in allocations)
            
            if total_priority == 0:
                # Fallback: equal distribution
                normalized_priority = 1.0 / len(allocations)
                for alloc in allocations:
                    alloc['normalized_priority'] = normalized_priority
            else:
                for alloc in allocations:
                    alloc['normalized_priority'] = alloc['priority'] / total_priority
            
            # Step 4: Time Allocation
            time_allocations = []
            for alloc in allocations:
                allocated_minutes = int(total_time_minutes * alloc['normalized_priority'])
                allocated_hours = round(allocated_minutes / 60.0, 2)
                
                time_allocation = TimeAllocation(
                    category=alloc['category'],
                    weight=alloc['weight'],
                    diagnostic_score=alloc['diagnostic_score'],
                    gap=alloc['gap'],
                    priority=alloc['priority'],
                    normalized_priority=alloc['normalized_priority'],
                    allocated_minutes=allocated_minutes,
                    allocated_hours=allocated_hours
                )
                time_allocations.append(time_allocation)
            
            self.logger.info(f"Time allocation calculated successfully for {len(time_allocations)} categories")
            return time_allocations
            
        except Exception as e:
            self.logger.error(f"Error calculating adaptive time allocation: {str(e)}")
            raise
    
    def generate_adaptive_learning_plan(
        self,
        plan_input: LearningPlanInput,
        remaining_time_minutes: Optional[int] = None
    ) -> AdaptiveLearningPlan:
        """
        Generate a complete adaptive learning plan with time allocation
        
        Args:
            plan_input: Input data for the learning plan
            remaining_time_minutes: Remaining time (defaults to total available time)
            
        Returns:
            Complete AdaptiveLearningPlan object
        """
        try:
            # Use remaining time or total available time
            time_to_allocate = remaining_time_minutes or plan_input.total_available_time_minutes
            
            # Calculate time allocation
            time_allocations = self.calculate_adaptive_time_allocation(
                category_weights=plan_input.category_weights,
                diagnostic_scores=plan_input.initial_diagnostic_scores,
                total_time_minutes=time_to_allocate
            )
            
            # Create the adaptive learning plan
            adaptive_plan = AdaptiveLearningPlan(
                assessment_name=plan_input.assessment_name,
                user_id=plan_input.user_id,
                plan_version=plan_input.plan_version,
                remaining_time_minutes=time_to_allocate,
                total_time_allocated=plan_input.total_available_time_minutes,
                timestamp=plan_input.timestamp,
                plan=time_allocations
            )
            
            self.logger.info(f"Adaptive learning plan generated for {plan_input.assessment_name}")
            return adaptive_plan
            
        except Exception as e:
            self.logger.error(f"Error generating adaptive learning plan: {str(e)}")
            raise
    
    def _validate_inputs(
        self, 
        category_weights: List[CategoryWeight], 
        diagnostic_scores: List[DiagnosticScore], 
        total_time_minutes: int
    ) -> None:
        """Validate input parameters"""
        
        if not category_weights:
            raise ValueError("Category weights cannot be empty")
        
        if not diagnostic_scores:
            raise ValueError("Diagnostic scores cannot be empty")
        
        if total_time_minutes <= 0:
            raise ValueError("Total time must be positive")
        
        # Validate weights sum to 1.0 (with small tolerance for floating point)
        weight_sum = sum(w.weight for w in category_weights)
        if not math.isclose(weight_sum, 1.0, abs_tol=0.01):
            raise ValueError(f"Category weights must sum to 1.0, got {weight_sum}")
        
        # Validate all weights are between 0 and 1
        for weight in category_weights:
            if not 0 <= weight.weight <= 1:
                raise ValueError(f"Weight for {weight.category} must be between 0 and 1, got {weight.weight}")
        
        # Validate all diagnostic scores are between 0 and 1
        for score in diagnostic_scores:
            if not 0 <= score.score <= 1:
                raise ValueError(f"Diagnostic score for {score.category} must be between 0 and 1, got {score.score}")
    
    def get_default_category_weights(self, assessment_type: str = "SHL") -> List[CategoryWeight]:
        """Get default category weights for common assessment types"""
        
        if "SHL" in assessment_type.upper():
            return [
                CategoryWeight(category="Numerical", weight=0.4),
                CategoryWeight(category="Verbal", weight=0.3),
                CategoryWeight(category="Abstract", weight=0.3)
            ]
        elif "WATSON" in assessment_type.upper() or "GLASER" in assessment_type.upper():
            return [
                CategoryWeight(category="Inference", weight=0.2),
                CategoryWeight(category="Recognition of Assumptions", weight=0.2),
                CategoryWeight(category="Deduction", weight=0.2),
                CategoryWeight(category="Interpretation", weight=0.2),
                CategoryWeight(category="Evaluation of Arguments", weight=0.2)
            ]
        else:
            # Generic default - equal weights
            return [
                CategoryWeight(category="Category 1", weight=0.33),
                CategoryWeight(category="Category 2", weight=0.33),
                CategoryWeight(category="Category 3", weight=0.34)
            ]
    
    def get_default_diagnostic_scores(self, categories: List[str]) -> List[DiagnosticScore]:
        """Get default diagnostic scores (0.5 for all categories)"""
        return [DiagnosticScore(category=cat, score=0.5) for cat in categories]

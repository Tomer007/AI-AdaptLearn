"""
Data models for adaptive learning plan time allocation
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class CategoryWeight:
    """Represents the weight/importance of a skill category"""
    category: str
    weight: float  # 0.0 to 1.0, must sum to 1.0 across all categories


@dataclass
class DiagnosticScore:
    """Represents a diagnostic score for a specific category"""
    category: str
    score: float  # 0.0 to 1.0 (0 = weak, 1 = strong)


@dataclass
class TimeAllocation:
    """Represents the calculated time allocation for a category"""
    category: str
    weight: float
    diagnostic_score: float
    gap: float
    priority: float
    normalized_priority: float
    allocated_minutes: int
    allocated_hours: float


@dataclass
class AdaptiveLearningPlan:
    """Complete adaptive learning plan with time allocation"""
    assessment_name: str
    user_id: str
    plan_version: str
    remaining_time_minutes: int
    total_time_allocated: int
    timestamp: str
    plan: List[TimeAllocation]


@dataclass
class LearningPlanInput:
    """Input data for generating adaptive learning plan"""
    assessment_name: str
    user_id: str
    plan_version: str
    total_available_time_minutes: int
    timestamp: str
    category_weights: List[CategoryWeight]
    initial_diagnostic_scores: List[DiagnosticScore]

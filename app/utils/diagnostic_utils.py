"""
Utility functions for extracting diagnostic scores from user data
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.adaptive_learning import DiagnosticScore
from app.logging.logging_config import get_logger

logger = get_logger(__name__)


def get_diagnostic_scores_from_user_data(
    user_id: str, 
    assessment_name: str = "Watson Glaser"
) -> Optional[List[DiagnosticScore]]:
    """
    Extract diagnostic scores from user's saved data files
    
    Args:
        user_id: User identifier
        assessment_name: Name of the assessment (e.g., "Watson Glaser", "SHL")
        
    Returns:
        List of DiagnosticScore objects or None if no data found
    """
    try:
        # Map assessment names to data directories
        data_dir_map = {
            "Watson Glaser": "Watson Glaser",
            "SHL": "SHL",
            "Watson-Glaser": "Watson Glaser"
        }
        
        data_dir = data_dir_map.get(assessment_name, "Watson Glaser")
        data_path = os.path.join("data", data_dir)
        
        if not os.path.exists(data_path):
            logger.warning(f"Data directory not found: {data_path}")
            return None
        
        # Look for user's data file
        safe_user_id = user_id.replace("/", "_").replace("\\", "_").replace(" ", "_")
        user_file = os.path.join(data_path, f"{safe_user_id}_answers.json")
        
        if not os.path.exists(user_file):
            logger.info(f"No user data file found: {user_file}")
            return None
        
        # Load user data
        with open(user_file, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        
        if not isinstance(user_data, list) or len(user_data) == 0:
            logger.info(f"No user data entries found in {user_file}")
            return None
        
        # Calculate scores by category
        category_scores = {}
        category_totals = {}
        
        for entry in user_data:
            category = entry.get("category", "").lower()
            is_correct = entry.get("is_correct", False)
            
            if category:
                if category not in category_scores:
                    category_scores[category] = 0
                    category_totals[category] = 0
                
                category_scores[category] += 1 if is_correct else 0
                category_totals[category] += 1
        
        # Convert to diagnostic scores (0.0 to 1.0)
        diagnostic_scores = []
        
        for category, correct_count in category_scores.items():
            total_count = category_totals[category]
            if total_count > 0:
                score = correct_count / total_count
                # Map category names to standard format
                standard_category = map_category_name(category)
                diagnostic_scores.append(DiagnosticScore(
                    category=standard_category,
                    score=score
                ))
        
        if not diagnostic_scores:
            logger.info("No valid diagnostic scores calculated")
            return None
        
        logger.info(f"Extracted {len(diagnostic_scores)} diagnostic scores for user {user_id}")
        return diagnostic_scores
        
    except Exception as e:
        logger.error(f"Error extracting diagnostic scores: {str(e)}")
        return None


def map_category_name(category: str) -> str:
    """
    Map category names from user data to standard format
    
    Args:
        category: Category name from user data
        
    Returns:
        Standardized category name
    """
    category_mapping = {
        "inference": "Inference",
        "interpretation": "Interpretation", 
        "assumptions": "Recognition of Assumptions",
        "evaluation of arguments": "Evaluation of Arguments",
        "deduction": "Deduction",
        "numerical": "Numerical",
        "verbal": "Verbal",
        "abstract": "Abstract"
    }
    
    return category_mapping.get(category.lower(), category.title())


def get_diagnostic_scores_from_session_data(session_data: Dict[str, Any]) -> Optional[List[DiagnosticScore]]:
    """
    Extract diagnostic scores from session data
    
    Args:
        session_data: Session data containing scores
        
    Returns:
        List of DiagnosticScore objects or None if no data found
    """
    try:
        scores = session_data.get("scores", {})
        if not scores:
            return None
        
        diagnostic_scores = []
        
        for domain, score_list in scores.items():
            if score_list and len(score_list) > 0:
                # Calculate average score for this domain
                avg_score = sum(score_list) / len(score_list)
                # Convert to 0.0-1.0 scale (assuming scores are 0-100)
                normalized_score = avg_score / 100.0 if avg_score > 1.0 else avg_score
                
                # Map domain to category name
                category = map_domain_to_category(domain)
                diagnostic_scores.append(DiagnosticScore(
                    category=category,
                    score=normalized_score
                ))
        
        return diagnostic_scores if diagnostic_scores else None
        
    except Exception as e:
        logger.error(f"Error extracting diagnostic scores from session data: {str(e)}")
        return None


def map_domain_to_category(domain: str) -> str:
    """
    Map domain names to category names
    
    Args:
        domain: Domain name from session data
        
    Returns:
        Category name for adaptive learning
    """
    domain_mapping = {
        "Inference": "Inference",
        "Interpretation": "Interpretation",
        "Assumptions": "Recognition of Assumptions", 
        "Evaluation_of_Arguments": "Evaluation of Arguments",
        "Deduction": "Deduction"
    }
    
    return domain_mapping.get(domain, domain.replace("_", " ").title())

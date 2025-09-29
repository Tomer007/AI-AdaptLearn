from pydantic import BaseModel
from enum import Enum
from typing import List, Optional, Dict


class Domain(str, Enum):
    Inference = "Inference"
    Interpretation = "Interpretation"
    Assumptions = "Assumptions"
    Evaluation_of_Arguments = "Evaluation of Arguments"
    Deduction = "Deduction"


class Stage(str, Enum):
    INIT = "INIT"
    QUICK = "QUICK"
    DEEPEN = "DEEPEN"
    SUMMARY = "SUMMARY"
    FEEDBACK = "FEEDBACK"
    END = "END"


class Question(BaseModel):
    id: str
    domain: Domain
    stem: str
    stimuli: Optional[str] = None
    options: List[str]
    correct: str  # e.g., "A" | "B" | ...
    explanation: str
    difficulty: int  # 1..10



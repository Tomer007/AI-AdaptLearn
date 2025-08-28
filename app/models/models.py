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


class Session(BaseModel):
    id: str
    user_id: str
    stage: Stage = Stage.INIT
    plan: Dict[str, Dict[Domain, List[str]]] = {}  # qids per stage per domain
    retries: Dict[str, int] = {}  # qid -> retry count
    history: List[Dict] = []  # events
    scores: Dict[Domain, List[float]] = {
        Domain.Inference: [],
        Domain.Interpretation: [],
        Domain.Assumptions: [],
        Domain.Evaluation_of_Arguments: [],
        Domain.Deduction: [],
    }
    wrong_ids: List[str] = []



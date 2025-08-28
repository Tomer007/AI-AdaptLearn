import json
import uuid
import os
from typing import List, Dict, Set, Optional

from app.models.models import Question, Domain


DOMAIN_MAP = {
    # Canonical Watson–Glaser subjects
    "Inference": "Inference",
    "Interpretation": "Interpretation",
    "Assumptions": "Assumptions",
    "Evaluation of Arguments": "Evaluation of Arguments",
    "Deduction": "Deduction",
    # Common aliases or noisy labels mapped to closest canonical subjects
    "Logic": "Deduction",
    "Logical": "Deduction",
}


class QuestionBank:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Support both flat lists and Watson–Glaser { metadata, questions, statistics }
        if isinstance(raw, dict) and "questions" in raw:
            records = raw["questions"] or []
        else:
            records = raw or []

        self.by_id: Dict[str, Question] = {}
        for r in records:
            subj = (
                r.get("Subject")
                or r.get("subject")
                or r.get("category")
                or ""
            )
            d = DOMAIN_MAP.get(subj, "Deduction")

            qid = (
                r.get("id")
                or r.get("question_id")
                or r.get("Question ID")
                or str(uuid.uuid4())
            )
            qid = str(qid)

            # Build options from various schemas
            options: List[str] = []
            if isinstance(r.get("answers"), dict):
                # answers: {"answer_1": ..., "answer_2": ...}
                options = [v for k, v in sorted(r["answers"].items()) if v]
            else:
                # fallbacks: "answer 1", "answer_1", etc.
                key_sets = [
                    ["answer 1", "answer 2", "answer 3", "answer 4", "answer 5"],
                    ["answer_1", "answer_2", "answer_3", "answer_4", "answer_5"],
                    ["option_1", "option_2", "option_3", "option_4", "option_5"],
                ]
                for keys in key_sets:
                    vals = [r.get(k) for k in keys if r.get(k)]
                    if vals:
                        options = vals
                        break

            stem = (
                r.get("question content")
                or r.get("question_content")
                or r.get("question")
                or r.get("stem")
                or ""
            )
            stimuli = r.get("question stimuli") or r.get("question_stimuli") or r.get("stimuli")
            correct = (
                r.get("correct answer")
                or r.get("correct_answer")
                or r.get("answer")
                or r.get("correct")
                or ""
            )
            explanation = r.get("explanation") or ""
            difficulty_raw = (
                r.get("Difficulty level")
                or r.get("difficulty_level")
                or r.get("difficulty")
                or 5
            )
            try:
                difficulty = int(difficulty_raw)
            except Exception:
                difficulty = 5

            self.by_id[qid] = Question(
                id=qid,
                domain=Domain(d),
                stem=stem,
                stimuli=stimuli,
                options=options,
                correct=str(correct).strip(),
                explanation=explanation,
                difficulty=difficulty,
            )

    def get(self, qid: str) -> Question:
        return self.by_id[qid]

    def list(
        self, domain: Domain, diff_min: int, diff_max: int, n: int, exclude: Set[str]
    ) -> List[Question]:
        items = [
            q
            for q in self.by_id.values()
            if q.domain == domain and diff_min <= q.difficulty <= diff_max and q.id not in exclude
        ]
        return items[:n]

    def suggest_next(
        self, domain: Domain, target_diff: int, n: int, exclude: Set[str]
    ) -> List[Question]:
        return self.list(
            domain, max(1, target_diff - 1), min(10, target_diff + 1), n, exclude
        )


# Singleton accessor
_QUESTION_BANK: Optional[QuestionBank] = None


def get_question_bank() -> QuestionBank:
    global _QUESTION_BANK
    if _QUESTION_BANK is None:
        default_path = os.path.join(
            "data",
            "Watson Glaser",
            "simulation_data.json",
        )
        _QUESTION_BANK = QuestionBank(default_path)
    return _QUESTION_BANK



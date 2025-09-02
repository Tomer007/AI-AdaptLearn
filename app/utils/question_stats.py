import os
import json
from typing import Dict, Any, Optional, List


def _default_stat() -> Dict[str, Any]:
    return {
        # Spec fields
        "question_id": None,
        "stem": None,
        "domain": None,
        "difficulty": None,
        "total_attempts": 0,
        "total_correct": 0,
        "total_incorrect": 0,
        "hint_usage_count": 0,
        "observed_stats": {
            "exposures": 0,
            "overall_correct_rate": 0.0,
            "first_try_correct_rate": 0.0,
            "avg_latency_ms": None,
            "hint_usage_rate": 0.0,
        },
    }


def update_question_stat(
    question_bank: str,
    qid: str,
    domain: str,
    difficulty: int,
    is_correct: bool,
    attempt_index: int,
    latency_ms: Optional[int] = None,
    hint_used: Optional[bool] = None,
    stem: Optional[str] = None,
    topics: Optional[List[str]] = None,
    estimated_time_sec: Optional[int] = None,
) -> None:
    """
    Update per-question aggregate stats for the given bank.

    Stats file location: data/{question_bank}/question_stats.json

    - total_attempts: increments on the first attempt only (exposures)
    - total_correct / total_incorrect: increments based on is_correct (first attempt only)
    - domain/difficulty tracked from last seen values
    - last_answered_at updated to current ISO timestamp
    """

    folder = os.path.join("data", question_bank)
    os.makedirs(folder, exist_ok=True)
    stats_path = os.path.join(folder, f"{question_bank}_quastions_stat.json")

    try:
        data: Dict[str, Any] = {}
        if os.path.exists(stats_path):
            with open(stats_path, "r", encoding="utf-8") as f:
                loaded = json.load(f) or {}
                if isinstance(loaded, dict):
                    data = loaded
        # ensure structure
        if "metadata" not in data:
            data["metadata"] = {"question_bank": question_bank}
        if "stats" not in data or not isinstance(data.get("stats"), dict):
            data["stats"] = {}

        stats = data["stats"].get(qid) or _default_stat()
        # set spec-identifiers
        stats["question_id"] = qid
        if stem is not None:
            stats["stem"] = stem
        # update aggregates / identifiers
        stats["domain"] = domain
        stats["difficulty"] = difficulty
        # Count exposures and correctness ONLY on first attempt
        if attempt_index == 0:
            stats["total_attempts"] = int(stats.get("total_attempts", 0)) + 1
            if is_correct:
                stats["total_correct"] = int(stats.get("total_correct", 0)) + 1
            else:
                stats["total_incorrect"] = int(stats.get("total_incorrect", 0)) + 1
        # Running average latency (no cumulative field stored); only first attempts considered
        prev_avg = None
        try:
            prev_avg = stats.get("observed_stats", {}).get("avg_latency_ms")
        except Exception:
            prev_avg = None
        if isinstance(latency_ms, (int, float)) and latency_ms >= 0 and attempt_index == 0:
            exposures_after = int(stats.get("total_attempts", 0))
            if prev_avg is None or exposures_after <= 1:
                new_avg = int(latency_ms)
            else:
                new_avg = int(round(((int(prev_avg) * (exposures_after - 1)) + int(latency_ms)) / exposures_after))
        else:
            new_avg = prev_avg if prev_avg is not None else None
        # Update hint usage rate as a running average based on first attempts only
        prev_hint_rate = 0.0
        try:
            prev_hint_rate = float(stats.get("observed_stats", {}).get("hint_usage_rate", 0.0) or 0.0)
        except Exception:
            prev_hint_rate = 0.0
        if attempt_index == 0:
            exposures_after = int(stats.get("total_attempts", 0))
            if exposures_after > 0:
                # previous exposures before this attempt
                before = max(0, exposures_after - 1)
                used = 1.0 if hint_used else 0.0
                if before == 0:
                    new_hint_rate = used
                else:
                    new_hint_rate = ((prev_hint_rate * before) + used) / exposures_after
            else:
                new_hint_rate = prev_hint_rate
        else:
            new_hint_rate = prev_hint_rate
        # compute observed_stats
        exposures = int(stats.get("total_attempts", 0))
        total_correct = int(stats.get("total_correct", 0))

        overall_rate = round(total_correct / exposures, 4) if exposures > 0 else 0.0
        # First-try rate equals overall here because we count only first attempts
        first_rate = overall_rate
        avg_latency = new_avg if (new_avg is not None and exposures > 0) else None
        hint_rate = round(new_hint_rate, 4) if exposures > 0 else 0.0

        stats["observed_stats"] = {
            "exposures": exposures,
            "overall_correct_rate": overall_rate,
            "first_try_correct_rate": first_rate,
            "avg_latency_ms": avg_latency,
            "hint_usage_rate": hint_rate,
        }

        # Remove difficulty analysis from persisted schema (no longer tracked)
        if "difficulty_analysis" in stats:
            try:
                del stats["difficulty_analysis"]
            except Exception:
                pass

        data["stats"][qid] = stats

        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # Non-fatal; do not interrupt main flow
        pass



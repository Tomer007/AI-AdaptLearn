from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.agents import WelcomeAgent
from app.services.agents.qa.qa_agent import QAAgent
from app.services.agents import IntroAgent
from app.utils.question_bank import get_question_bank
from app.utils.question_stats import update_question_stat
import os
import json
from app.services.agents.qstats.qstats_agent import QStatsAgent
from app.services.agents.learning_plan.learning_plan_agent import LearningPlanAgent
from app.models.adaptive_learning import DiagnosticScore
from app.logging.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

class QARequest(BaseModel):
    """Assessment Q&A request model aligned with frontend payload."""
    message: str = Field(..., description="User message/question")
    session_id: str = Field(..., description="Chat session identifier")
    settings: Optional[Dict[str, Any]] = Field(None, description="User settings context")


class WelcomeRequest(BaseModel):
    """Request model for generating a welcome message using WelcomeAgent."""
    settings: Dict[str, Any] = Field(..., description="Arbitrary user settings dictionary")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Optional conversation history")


class WelcomeResponse(BaseModel):
    """Response model containing the generated welcome message."""
    welcome_message: str
    session_id: Optional[str] = None
    generated_at: str


@router.post("/assessment-qa")
async def process_qa_data(
    qa_request: QARequest) -> Dict[str, Any]:
    """
    Process Q&A data from the initial conversation.
    
    Args:
        qa_request: Q&A data request
        
    Returns:
        Processing result
    """
    try:
        agent = QAAgent()
        reply = agent.answer(
            question=qa_request.message,
            user_settings=qa_request.settings,
            conversation_history=None,
        )

        
        return {
            "reply": reply
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing Q&A data: {str(e)}"
        )


# -------- Question Stats Q&A Endpoint --------
class QStatsQARequest(BaseModel):
    message: str = Field(..., description="User question about the stats")
    qid: Optional[str] = Field(None, description="Optional target question id")
    stats: Dict[str, Any] = Field(..., description="Full question stats JSON (as loaded by FE)")


@router.post("/qstats-qa")
async def qstats_qa_endpoint(req: QStatsQARequest) -> Dict[str, Any]:
    try:
        agent = QStatsAgent()
        reply = agent.answer(message=req.message, stats=req.stats)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing stats Q&A: {str(e)}")


@router.post("/welcome", response_model=WelcomeResponse)
async def generate_welcome_message_endpoint(
    welcome_request: WelcomeRequest
) -> WelcomeResponse:
    """
    Generate a personalized welcome message using the WelcomeAgent.
    
    Args:
        welcome_request: Request containing generic user settings and optional history
    
    Returns:
        Generated welcome message and metadata
    """
    try:
        from fastapi.encoders import jsonable_encoder
        agent = WelcomeAgent()
        # Normalize to plain dict to avoid Pydantic FieldInfo issues
        settings_val: Any = jsonable_encoder(welcome_request.settings or {})
        if not isinstance(settings_val, dict):
            try:
                settings_val = dict(settings_val)
            except Exception:
                settings_val = {}

        message = agent.generate_welcome_message(user_settings=settings_val)
        sess_id = None
        try:
            sess_id = settings_val.get("session_id")
        except Exception:
            sess_id = None
        return WelcomeResponse(
            welcome_message=message,
            session_id=sess_id,
            generated_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating welcome message: {str(e)}"
        )


# -------- Intro Agent Endpoint --------
class IntroRequest(BaseModel):
    action: str = Field(..., description="one of: select_intro, select_deepen, hint, explain, summary, feedback_classify")
    payload: Optional[Dict[str, Any]] = Field(None, description="Action-specific payload")


@router.post("/intro")
async def intro_endpoint(req: IntroRequest) -> Dict[str, Any]:
    try:
        agent = IntroAgent()
        action = req.action
        data = req.payload or {}

        if action == "select_intro":
            exclude_ids = data.get("exclude_ids", [])
            selection = agent.select_for_intro(exclude_ids=exclude_ids)
            return {"selection": selection}

        if action == "select_deepen":
            target = data.get("target_difficulty", {})
            exclude_ids = data.get("exclude_ids", [])
            selection = agent.select_for_deepen(target_difficulty=target, exclude_ids=exclude_ids)
            return {"selection": selection}

        if action == "hint":
            stem = data.get("stem", "")
            choices = data.get("choices", [])
            chosen = data.get("chosen", "")
            tags = data.get("tags")
            hint = agent.hint(stem=stem, choices=choices, chosen=chosen, tags=tags)
            return {"hint": hint}

        if action == "explain":
            stem = data.get("stem", "")
            choices = data.get("choices", [])
            correct = data.get("correct", "")
            first_attempt = int(data.get("first_attempt", -1))
            second_attempt = int(data.get("second_attempt", -1))
            tags = data.get("tags")
            explanation, misconception = agent.explanation(
                stem=stem,
                choices=choices,
                correct=correct,
                first_attempt=first_attempt,
                second_attempt=second_attempt,
                tags=tags,
            )
            return {"explanation": explanation, "misconception": misconception}

        if action == "summary":
            # Prefer computing stats from saved user data file
            tester_name = str(data.get("tester_name") or "Tomer").strip()
            overall_percentile = int(data.get("overall_percentile", 50))
            lang = data.get("lang", "en")

            file_per_section: Dict[str, Dict[str, Any]] = {}
            per_question_details: List[Dict[str, Any]] = []

            try:
                safe_name = tester_name.replace("/", "_").replace("\\", "_").replace(" ", "_") or "Unknown"
                file_path = os.path.join("data", "Watson Glaser", f"{safe_name}_{assessment_date}.json")
                entries: List[Dict[str, Any]] = []
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        entries = json.load(f) or []
                        if not isinstance(entries, list):
                            entries = []
                # Group by qid, pick earliest attempt as first-try
                by_qid: Dict[str, Dict[str, Any]] = {}
                for e in entries:
                    qid = str(e.get("qid"))
                    ts = e.get("timestamp") or ""
                    try:
                        t = datetime.fromisoformat(ts)
                    except Exception:
                        t = datetime.min
                    if qid not in by_qid or t < by_qid[qid]["_t"]:
                        by_qid[qid] = {**e, "_t": t}
                # Sort by earliest time
                sorted_firsts = sorted(by_qid.values(), key=lambda x: x.get("_t", datetime.min))
                # Build per-section and per-question
                for idx, rec in enumerate(sorted_firsts, start=1):
                    section = str(rec.get("domain") or "").strip()
                    is_correct = bool(rec.get("is_correct"))
                    if section not in file_per_section:
                        file_per_section[section] = {"correct_first_try": 0, "total": 0, "total_time_sec": 0}
                    file_per_section[section]["total"] += 1
                    if is_correct:
                        file_per_section[section]["correct_first_try"] += 1
                    per_question_details.append({
                        "question_number": idx,
                        "section": section,
                        "user_answer": rec.get("chosen"),
                        "correct_answer": rec.get("correct"),
                        "is_correct": is_correct,
                        "duration_seconds": rec.get("duration_seconds"),  # may be None if not tracked server-side
                    })
            except Exception:
                # Fallback to client-provided data if file read fails
                file_per_section = data.get("per_section", {})
                per_question_details = data.get("records") or []

            message = agent.summary(
                per_section=file_per_section,
                overall_percentile=overall_percentile,
                lang=lang,
                records=per_question_details,
            )
            return {"message": message}

        if action == "feedback_classify":
            raw = data.get("raw_feedback", "")
            result = agent.classify_feedback(raw)
            return result

        if action == "check":
            qid = data.get("qid")
            chosen = str(data.get("chosen", "")).strip()
            tester_name = str(data.get("tester_name") or "Unknown").strip()
            attempt = int(data.get("attempt", 0))
            assessment_date = str(data.get("assessment_date") or datetime.now().date().isoformat()).strip()
            if not qid:
                raise HTTPException(status_code=400, detail="Missing qid")
            qb = get_question_bank()
            try:
                q = qb.get(qid)
            except Exception:
                raise HTTPException(status_code=404, detail="Question not found")
            is_correct = chosen == str(q.correct).strip()
            # Save the first attempt for each question. If it's incorrect, save with is_correct=false.
            # File name: {tester_name}_answers.json
            try:
                record_dir = os.path.join("data", "Watson Glaser")
                os.makedirs(record_dir, exist_ok=True)
                safe_name = tester_name.replace("/", "_").replace("\\", "_").replace(" ", "_") or "Unknown"
                file_path = os.path.join(record_dir, f"{safe_name}_answers.json")
                if attempt == 0:
                    payload = {
                        "qid": str(qid),
                        "is_correct": bool(is_correct),
                        "domain": getattr(getattr(q, "domain", None), "value", str(getattr(q, "domain", ""))),
                        "difficulty": getattr(q, "difficulty", None),
                    }
                    # Append to file object with metadata { metadata:{question_bank}, answers:[...] }
                    file_obj: Dict[str, Any] = {"metadata": {"question_bank": "Watson Glaser"}, "answers": []}
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                loaded = json.load(f)
                                if isinstance(loaded, dict) and isinstance(loaded.get("answers"), list):
                                    file_obj = loaded
                                elif isinstance(loaded, list):
                                    file_obj["answers"] = loaded
                                else:
                                    # keep default structure
                                    pass
                        except Exception:
                            pass
                    # ensure metadata present
                    meta = file_obj.get("metadata") or {}
                    if "question_bank" not in meta:
                        meta["question_bank"] = "Watson Glaser"
                    file_obj["metadata"] = meta
                    # append answer (enforce unique qid; first attempt wins)
                    answers_list = file_obj.get("answers") or []
                    if not any(str(x.get("qid")) == payload["qid"] for x in answers_list):
                        answers_list.append(payload)
                    file_obj["answers"] = answers_list
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(file_obj, f, ensure_ascii=False, indent=2)
            except Exception:
                # Non-fatal: saving should not block answering
                pass

            # Update bank-level question statistics (all attempts)
            try:
                update_question_stat(
                    question_bank="Watson Glaser",
                    qid=str(qid),
                    domain=getattr(getattr(q, "domain", None), "value", str(getattr(q, "domain", ""))),
                    difficulty=int(getattr(q, "difficulty", 0) or 0),
                    is_correct=bool(is_correct),
                    attempt_index=int(attempt),
                    latency_ms=None,
                    hint_used=False,
                    stem=getattr(q, "stem", None),
                    topics=[getattr(getattr(q, "domain", None), "value", str(getattr(q, "domain", "")))],
                )
            except Exception:
                pass

            return {"is_correct": is_correct, "correct": q.correct}

        raise HTTPException(status_code=400, detail="Unknown action")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intro endpoint error: {str(e)}")




class LearningPlanJsonRequest(BaseModel):
    """Request model for generating a learning plan from JSON input with diagnostic scores."""
    assessment_name: str = Field(..., description="Name of the assessment")
    user_id: str = Field(..., description="Unique user identifier")
    plan_version: str = Field(default="v1.0", description="Version of the plan")
    total_available_time_minutes: int = Field(..., description="Total time available for preparation")
    timestamp: str = Field(..., description="When the request was made")
    category_weights: List[Dict[str, Any]] = Field(..., description="Categories with their importance weights")
    initial_diagnostic_scores: List[Dict[str, Any]] = Field(..., description="Categories with current skill levels")


class LearningPlanJsonResponse(BaseModel):
    """Response model containing the generated learning plan as JSON."""
    assessment_name: str = Field(..., description="Name of the assessment")
    user_id: str = Field(..., description="Unique user identifier")
    plan_version: str = Field(..., description="Version of the plan")
    remaining_time_minutes: int = Field(..., description="Time remaining for preparation")
    total_time_allocated: int = Field(..., description="Original total time allocated")
    timestamp: str = Field(..., description="When the plan was generated")
    plan: List[Dict[str, Any]] = Field(..., description="Time allocation results per category")


@router.post("/learning-plan", response_model=LearningPlanJsonResponse)
async def generate_learning_plan(request: LearningPlanJsonRequest):
    try:
        # Generate learning plan using JSON input
        agent = LearningPlanAgent()
        
        # Convert request to dictionary
        json_input = request.model_dump()
        
        # Generate adaptive learning plan
        result = await agent.generate_learning_plan_from_json(json_input)
        
        # Check if result contains an error
        if "error" in result:
            logger.error(f"Learning plan generation failed: {result['error']}")
            raise HTTPException(status_code=500, detail=result['error'])
        
        return LearningPlanJsonResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating learning plan from JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating learning plan: {str(e)}")


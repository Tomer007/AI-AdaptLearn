from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.agents import WelcomeAgent
from app.services.agents.qa.qa_agent import QAAgent
from app.services.agents import IntroAgent
from app.utils.question_bank import get_question_bank

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
            per_section = data.get("per_section", {})
            overall_percentile = int(data.get("overall_percentile", 50))
            lang = data.get("lang", "en")
            message = agent.summary(per_section=per_section, overall_percentile=overall_percentile, lang=lang)
            return {"message": message}

        if action == "feedback_classify":
            raw = data.get("raw_feedback", "")
            result = agent.classify_feedback(raw)
            return result

        if action == "check":
            qid = data.get("qid")
            chosen = str(data.get("chosen", "")).strip()
            if not qid:
                raise HTTPException(status_code=400, detail="Missing qid")
            qb = get_question_bank()
            try:
                q = qb.get(qid)
            except Exception:
                raise HTTPException(status_code=404, detail="Question not found")
            is_correct = chosen == str(q.correct).strip()
            return {"is_correct": is_correct, "correct": q.correct}

        raise HTTPException(status_code=400, detail="Unknown action")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intro endpoint error: {str(e)}")


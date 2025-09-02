import os
from typing import Any, Dict, List, Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.logging.logging_config import get_logger

from app.config import settings
from app.models.models import Domain, Question
from app.utils.question_bank import get_question_bank


def _question_to_payload(q: Question) -> Dict[str, Any]:
    # Try to compute the 0-based index of the correct answer within the choices
    correct_index = None
    try:
        normalized_correct = str(q.correct).strip()
        for i, opt in enumerate(q.options):
            if str(opt).strip() == normalized_correct:
                correct_index = i
                break
    except Exception:
        correct_index = None

    return {
        "id": q.id,
        "domain": q.domain.value,
        "stem": q.stem,
        "stimuli": q.stimuli,
        "choices": q.options,
        "difficulty": q.difficulty,
        "correct_index": correct_index,
    }


class IntroAgent:
    """
    LLM-only adaptive intro assessment engine over the Watson-Glaser bank.

    Phases (mapped to Stage):
      - INIT  → Assessment Intro (1 question per domain)
      - DEEPEN → Deepen Familiarity (3 questions per domain)
      - SUMMARY → Summary & Diagnosis
      - FEEDBACK → Emotional Feedback Collection

    State is simulated via inputs and conversation history. The caller is
    responsible for maintaining progress and passing prior context back in.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.bank = get_question_bank()

        # Load system prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "intro_system.prompt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        else:
            # Fallback minimal prompt
            self.system_prompt = (
                "You are the LLM-Only Adaptive Intro Assessment Engine. "
                "Return concise hints and explanations. Keep tone supportive."
            )
        self.logger.info("IntroAgent initialized: model=gpt-4o temp=0.3, bank_loaded=%s", bool(self.bank))

    # ---------- Selection ----------
    def select_for_intro(self, exclude_ids: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Select 1 question per domain for warm-up (INIT)."""
        self.logger.info("[INIT] Selecting warm-up questions | exclude_count=%s", len(exclude_ids or []))
        exclude = set(exclude_ids or [])
        payload: Dict[str, List[Dict[str, Any]]] = {d.value: [] for d in Domain}
        for d in Domain:
            qs = self.bank.suggest_next(d, target_diff=4, n=1, exclude=exclude)
            payload[d.value] = [_question_to_payload(q) for q in qs]
        self.logger.debug("[INIT] Selected IDs per domain: %s", {k: [x["id"] for x in v] for k, v in payload.items()})
        return payload

    def select_for_deepen(
        self,
        target_difficulty: Dict[str, int],
        exclude_ids: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Select 3 diverse questions per domain near target difficulty (DEEPEN)."""
        self.logger.info(
            "[DEEPEN] Selecting questions | targets=%s exclude_count=%s",
            {d: int(target_difficulty.get(d, 5)) for d in [d.value for d in Domain]},
            len(exclude_ids or []),
        )
        exclude = set(exclude_ids or [])
        payload: Dict[str, List[Dict[str, Any]]] = {d.value: [] for d in Domain}
        for d in Domain:
            t = max(1, min(10, int(target_difficulty.get(d.value, 5))))
            qs = self.bank.suggest_next(d, target_diff=t, n=3, exclude=exclude)
            payload[d.value] = [_question_to_payload(q) for q in qs]
        self.logger.debug("[DEEPEN] Selected IDs per domain: %s", {k: [x["id"] for x in v] for k, v in payload.items()})
        return payload

    # ---------- Feedback ----------
    def hint(
        self,
        stem: str,
        choices: List[str],
        chosen: str,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Generate a short actionable hint (no spoilers)."""
        self.logger.info("[FEEDBACK] Generating hint | has_tags=%s choices=%s", bool(tags), len(choices))
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    "User chose a wrong option on the first attempt. "
                    "Provide ONE actionable hint (<=160 chars), no spoilers.\n"
                    f"Stem: {stem}\nChoices: {choices}\nChosen: {chosen}\nTags: {tags or []}"
                )
            ),
        ]
        resp = self.llm.invoke(messages).content.strip()
        self.logger.debug("[FEEDBACK] Hint length=%s chars", len(resp))
        return resp

    def explanation(
        self,
        stem: str,
        choices: List[str],
        correct: str,
        first_attempt: int,
        second_attempt: int,
        tags: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Return (explanation, misconception) after second failure."""
        self.logger.info(
            "[FEEDBACK] Generating explanation | first=%s second=%s",
            first_attempt,
            second_attempt,
        )
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=(
                    "The user failed twice. Provide: (1) <=120-word explanation of why the "
                    "correct option works, (2) <=200-char misconception describing the likely trap.\n"
                    f"Stem: {stem}\nChoices: {choices}\nCorrect: {correct}\n"
                    f"Attempts: first={first_attempt}, second={second_attempt}\nTags: {tags or []}"
                )
            ),
        ]
        resp = self.llm.invoke(messages).content.strip()
        self.logger.debug("[FEEDBACK] Explanation length=%s chars", len(resp))
        # Heuristic split if model returns two parts separated by a line
        if "\n\n" in resp:
            parts = resp.split("\n\n", 1)
            return parts[0].strip(), parts[1].strip()
        return resp, "Common trap: focusing on surface cues instead of the governing rule."

    # ---------- Summary & Feedback ----------
    def summary(self, per_section: Dict[str, Dict[str, float]], overall_percentile: int, lang: str = "en", records: Optional[List[Dict[str, Any]]] = None) -> str:
        self.logger.info(
            "[SUMMARY] Generating summary | sections=%s overall=%s lang=%s",
            list(per_section.keys()),
            overall_percentile,
            lang,
        )
        per_question_details = records or []
        messages = [
    SystemMessage(content=self.system_prompt),
    HumanMessage(
        content=(
            "Goal: Generate a warm, encouraging summary in the specified language to help the user reflect on their assessment performance with positivity and insight, while also providing a sharp, witty analytical breakdown of results."
            "Behavior and Tone"
            "- Primary Tone: Warm, celebratory, and motivational 🎉 (supportive coach).\n"
            "- Secondary Tone: Sharp, slightly sarcastic, but constructive (bright teenager commentary).\n"
            "- Persona: Supportive coach mixed with analyst – empathetic, insightful, empowering, yet playfully observant.\n"
            "- Language: Always respond in the user-specified `lang`.\n"
            "Output Structure\n"
            "1. **Opening Sentence (1 line):** Celebrate the user's effort."
            "2. **Reflective Paragraphs (1–2):** Highlight strengths , areas for improvement , and mention overall_percentile."
            "3. **Markdown Summary Block** with '###  Assessment Summary' and lines '- Section: X correct out of Y' using emoji legend (✅ ≥80%, ⚠️ 50–79%, ❌ <50%)."
            "Extended Analytical Add-On (Assessment Analyst AI)"
            "5. **Raw Results Table:** Display all input data cleanly."
            "6. **Statistical Summary:**"
            "   - Overall accuracy (% correct)."
            "   - Accuracy by domain (Inference, Assumptions, Deduction, Evaluation of Arguments, Interpretation)."
            "7. **Insights Section:** Provide witty, informal commentary:"
            "   - Strong areas (domains with high accuracy)."
            "   - Weak areas (domains with low accuracy)."
            "   - Notable quirks or paradoxes (e.g., better at harder questions than medium ones)."
            "   - Keep it concise, witty, and observational."
            "❗Critical"
            "- Never be demotivating."
            "- Always include all Markdown blocks.\n"
            "- Do not invent details; rely only on provided variables.\n"
            "- Always respect `lang`.\n\n"
            f"Variables: per_section={per_section}, overall_percentile={overall_percentile}, per_question_details={per_question_details}, lang={lang}"
            )
            ),
            ]
        resp = self.llm.invoke(messages).content.strip()
        self.logger.debug("[SUMMARY] Summary length=%s chars", len(resp))
        return resp

    def classify_feedback(self, raw_feedback: str) -> Dict[str, str]:
        text = raw_feedback.lower()
        sentiment = "neutral"
        if any(x in text for x in ["love", "great", "helpful", "good", "nice"]):
            sentiment = "positive"
        if any(x in text for x in ["frustrated", "hate", "bad", "confusing", "annoying"]):
            sentiment = "negative"

        pace = "fine"
        if "too fast" in text or "rushed" in text or "fast" in text:
            pace = "too_fast"
        if "too slow" in text or "slow" in text:
            pace = "too_slow"

        difficult_section = "none"
        # Map user feedback keywords to Watson–Glaser subjects
        if "inference" in text:
            difficult_section = "Inference"
        elif "interpretation" in text:
            difficult_section = "Interpretation"
        elif "assumption" in text or "assumptions" in text:
            difficult_section = "Assumptions"
        elif "evaluation" in text or "argument" in text or "arguments" in text:
            difficult_section = "Evaluation of Arguments"
        elif "deduction" in text or "logic" in text or "logical" in text or "syllog" in text:
            difficult_section = "Deduction"

        return {
            "sentiment": sentiment,
            "pace": pace,
            "difficult_section": difficult_section,
        }



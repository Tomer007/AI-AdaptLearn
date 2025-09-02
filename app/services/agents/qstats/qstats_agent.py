import os
import json
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings


class QStatsAgent:
    """
    LLM-backed analyst for per-question statistics.

    Usage:
        agent = QStatsAgent()
        reply = agent.answer(message="...", qid="19", stats={...})
    """

    def __init__(self) -> None:
        # Load system prompt from co-located prompt file
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "qstats_system.prompt")
        if not os.path.exists(prompt_path):
            raise FileNotFoundError("QStats system prompt not found")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.2,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    def answer(self, message: str, qid: Optional[str], stats: Dict[str, Any]) -> Optional[str]:
        payload = {
            "qid": qid,
            "question": message,
            "stats": stats,
        }

        # If the user message includes Hebrew characters, request Hebrew output
        def _is_hebrew(text: str) -> bool:
            try:
                return any('\u0590' <= ch <= '\u05FF' for ch in text)
            except Exception:
                return False

        messages = [SystemMessage(content=self.system_prompt)]
        if _is_hebrew(message):
            messages.append(SystemMessage(content="ענה בעברית בבקשה."))
        messages.append(HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2)))

        resp = self.llm.invoke(messages)
        return getattr(resp, "content", "") or ""



import os
import json
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings


class WelcomeAgent:
    def __init__(self):
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "prompts",
            "welcome_agent.prompt",
        )
        if not os.path.exists(prompt_path):
            raise FileNotFoundError("Welcome prompt not found")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_text = f.read()

        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.5,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    def generate_welcome_message(
        self,
        user_settings: Dict[str, Any],
    ) -> str:
        # Normalize settings to a plain dict
        if not isinstance(user_settings, dict):
            try:
                user_settings = user_settings.model_dump()  # pydantic v2
            except Exception:
                try:
                    user_settings = dict(user_settings)
                except Exception:
                    user_settings = {}

        # Prepare variables for the prompt
        settings_json = json.dumps(user_settings or {}, ensure_ascii=False, indent=2)

        def _as_text(val: Any) -> str:
            if val is None:
                return ""
            if isinstance(val, (list, tuple)):
                return ", ".join(str(x) for x in val if x)
            return str(val)

        variables = {
            "assessment_name": _as_text(user_settings.get("pack_name")),
            "tester_name": _as_text(user_settings.get("tester_name")),
            "user_settings": settings_json,
            "job_position": _as_text(user_settings.get("position")),
            "company_name": _as_text(user_settings.get("company")),
            "difficult_topics": _as_text(user_settings.get("difficult_topic")),
            "user_concerns": _as_text(user_settings.get("user_concerns")),
        }

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant for JobTestPrep's Adaptive Learning System."),
            ("human", self.prompt_text),
        ])

        messages = prompt.format_messages(**variables)
        try:
            resp = self.llm.invoke(messages)
        except Exception as e:
            print("error:", e)
            raise Exception(f"Failed to generate welcome message: {str(e)}")
        return getattr(resp, "content", str(resp))


import os
import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory

from app.config import settings


class QAAgent:
    def __init__(self) -> None:
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "prompts",
            "evaluation.prompt",
        )
        if not os.path.exists(prompt_path):
            raise FileNotFoundError("QA evaluation prompt not found")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_text = f.read()

        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.memory = ConversationBufferWindowMemory(k=10, return_messages=True)

    def answer(
        self,
        question: str,
        user_settings: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        settings_json = json.dumps(user_settings or {}, ensure_ascii=False, indent=2)
        user_prompt = (
            f"{self.prompt_text}\n\nUser Settings (JSON):\n{settings_json}\n\nQuestion: {question}\n"
        )

        if conversation_history:
            for msg in conversation_history[-10:]:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    self.memory.chat_memory.add_user_message(content)
                elif role == "assistant":
                    self.memory.chat_memory.add_ai_message(content)

        messages = [
            SystemMessage(content="Watson-Glaser evaluation assistant. Follow structure strictly."),
            HumanMessage(content=user_prompt),
        ]

        if self.memory.chat_memory.messages:
            messages.extend(self.memory.chat_memory.messages[-10:])

        response = self.llm.invoke(messages)
        self.memory.chat_memory.add_user_message(user_prompt)
        self.memory.chat_memory.add_ai_message(response.content)
        return response.content



import json
import logging
from typing import Optional
from src.domain.entities.decision import ActionDecision, ActionType
from src.domain.ports.llm import ILLMClient

logger = logging.getLogger(__name__)


class CloudLLMClient(ILLMClient):
    """Client for Cloud LLM (OpenAI / Claude / Gemini) enforcing structured JSON schema output."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name

    def evaluate_and_generate(
        self,
        context_text: str,
        action_type: ActionType,
        thread_context: Optional[str] = None,
    ) -> ActionDecision:
        # Prompt template with JSON schema instruction
        system_prompt = (
            "Bạn là trợ lý hỗ trợ tương tác Facebook tự nhiên, văn phong thân thiện, lịch sự và súc tích.\n"
            "Hãy quyết định xem có nên phản hồi không và tạo nội dung tương ứng.\n"
            "Chỉ trả về JSON theo schema:\n"
            '{"should_act": bool, "reason": string, "text": string}'
        )

        if not self.api_key:
            logger.warning("No LLM API key configured. Returning default SKIP decision.")
            return ActionDecision(
                should_act=False,
                reason="No LLM API key provided",
                action_type=ActionType.SKIP,
            )

        # In production, call openai/anthropic/google-genai client here
        return ActionDecision(
            should_act=False,
            reason="Cloud LLM adapter initialized in skeleton mode",
            action_type=ActionType.SKIP,
        )

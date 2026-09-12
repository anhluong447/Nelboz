from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.decision import ActionDecision, ActionType


class ILLMClient(ABC):
    @abstractmethod
    def evaluate_and_generate(
        self,
        context_text: str,
        action_type: ActionType,
        thread_context: Optional[str] = None,
    ) -> ActionDecision:
        """Calls cloud LLM API with structured JSON output schema to decide and generate response."""
        pass

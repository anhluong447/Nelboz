from typing import Optional
from src.domain.entities.decision import ActionDecision, ActionType
from src.domain.ports.llm import ILLMClient


class MockLLMClient(ILLMClient):
    """Mock LLM client returning predictable decisions for pipeline testing."""

    def __init__(
        self,
        should_act: bool = True,
        sample_response: str = "Góc nhìn rất hay và thực tế, cảm ơn bạn đã chia sẻ!",
    ):
        self.should_act = should_act
        self.sample_response = sample_response

    def evaluate_and_generate(
        self,
        context_text: str,
        action_type: ActionType,
        thread_context: Optional[str] = None,
    ) -> ActionDecision:
        return ActionDecision(
            should_act=self.should_act,
            text=self.sample_response if self.should_act else "",
            action_type=action_type if self.should_act else ActionType.SKIP,
            reason="Mock decision for testing",
            confidence=0.98,
        )

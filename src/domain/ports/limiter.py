from abc import ABC, abstractmethod


class IRateLimiter(ABC):
    @abstractmethod
    def can_perform(self, action_key: str) -> bool:
        """Checks if the given action exceeds the rate limit."""
        pass

    @abstractmethod
    def record_action(self, action_key: str) -> None:
        """Records an action timestamp into history."""
        pass

    @abstractmethod
    def wait_if_needed(self, action_key: str) -> None:
        """Blocks until the action is allowed by rate limiting."""
        pass

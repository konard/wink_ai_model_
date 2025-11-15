from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple


class ModificationStrategy(ABC):
    """Base class for all modification strategies."""

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def can_handle(self, modification_type: str) -> bool:
        """Check if this strategy can handle the given modification type."""
        pass

    @abstractmethod
    def apply(
        self,
        scenes: List[Dict[str, Any]],
        params: Dict[str, Any],
        entities: Dict[str, List[Any]],
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Apply modification to scenes.

        Returns:
            Tuple of (modified_scenes, metadata about changes)
        """
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate modification parameters."""
        pass

    def get_description(self) -> str:
        """Get human-readable description of this strategy."""
        return self.__doc__ or self.name


class StrategyRegistry:
    """Registry for all available modification strategies."""

    def __init__(self):
        self._strategies: List[ModificationStrategy] = []

    def register(self, strategy: ModificationStrategy):
        """Register a new strategy."""
        self._strategies.append(strategy)

    def get_strategy(self, modification_type: str) -> ModificationStrategy:
        """Get strategy that can handle the given modification type."""
        for strategy in self._strategies:
            if strategy.can_handle(modification_type):
                return strategy
        raise ValueError(
            f"No strategy found for modification type: {modification_type}"
        )

    def list_strategies(self) -> List[str]:
        """List all registered strategy names."""
        return [s.name for s in self._strategies]


_global_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    """Get global strategy registry."""
    return _global_registry

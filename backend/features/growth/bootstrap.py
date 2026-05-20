from core.contracts import ConceptMasteredEvent
from core.event_bus import event_bus

from .handlers import on_concept_mastered


def register_growth_subscriptions() -> None:
    event_bus.subscribe(ConceptMasteredEvent, on_concept_mastered)


__all__ = ["register_growth_subscriptions"]

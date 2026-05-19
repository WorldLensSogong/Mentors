from __future__ import annotations

import logging

from core.contracts import ConceptMasteredEvent
from core.db import SessionLocal

from .service import process_concept_mastered_event

logger = logging.getLogger("growth.handlers")


async def on_concept_mastered(event: ConceptMasteredEvent) -> None:
    try:
        async with SessionLocal() as session:
            await process_concept_mastered_event(
                event.user_id,
                event.concept_id,
                event.event_id,
                session,
            )
    except Exception:
        logger.exception(
            "growth.concept_mastered_failed",
            extra={"event_id": event.event_id, "user_id": event.user_id},
        )


__all__ = ["on_concept_mastered"]

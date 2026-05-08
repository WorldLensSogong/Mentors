from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.curriculum import LearningModule
from app.models.level import LevelDefinition
from app.schemas.curriculum import CurriculumModuleSummary


def list_learning_modules(
    db: Session,
    *,
    strategy_id: int | None = None,
    level_no: int | None = None,
) -> list[CurriculumModuleSummary]:
    stmt: Select[tuple[LearningModule]] = (
        select(LearningModule)
        .where(LearningModule.is_active.is_(True))
        .order_by(LearningModule.sort_order.asc(), LearningModule.id.asc())
    )
    if strategy_id is not None:
        stmt = stmt.where(LearningModule.strategy_id == strategy_id)

    modules = db.scalars(stmt).all()

    if level_no is not None:
        allowed_level_ids = {
            row.id
            for row in db.scalars(select(LevelDefinition).where(LevelDefinition.level_no == level_no)).all()
        }
        modules = [module for module in modules if module.level_id in allowed_level_ids]

    level_map = {
        level.id: level.level_no
        for level in db.scalars(select(LevelDefinition)).all()
    }

    return [
        CurriculumModuleSummary(
            id=module.id,
            code=module.code,
            title=module.title,
            strategy_id=module.strategy_id,
            level_no=level_map.get(module.level_id, 0),
            concept_summary=module.concept_summary,
            sort_order=module.sort_order,
        )
        for module in modules
    ]

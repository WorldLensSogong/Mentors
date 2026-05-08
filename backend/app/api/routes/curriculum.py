from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.curriculum_repository import list_learning_modules
from app.schemas.common import ListPayload, ResponseEnvelope
from app.schemas.curriculum import CurriculumModuleSummary

router = APIRouter()


@router.get("/modules", response_model=ResponseEnvelope[ListPayload[CurriculumModuleSummary]])
def get_curriculum_modules(
    strategy_id: int | None = Query(default=None, ge=1),
    level_no: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ListPayload[CurriculumModuleSummary]]:
    items = list_learning_modules(db, strategy_id=strategy_id, level_no=level_no)
    payload = ListPayload[CurriculumModuleSummary](items=items, total=len(items))
    return ResponseEnvelope(data=payload, message="curriculum modules fetched")


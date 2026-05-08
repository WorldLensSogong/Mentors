from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import ResponseEnvelope
from app.schemas.report import ReportPreviewRequest, ReportPreviewResult
from app.services.report_service import build_report_preview

router = APIRouter()


@router.post("/preview", response_model=ResponseEnvelope[ReportPreviewResult])
def preview_report(
    payload: ReportPreviewRequest,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[ReportPreviewResult]:
    result = build_report_preview(db, payload)
    return ResponseEnvelope(data=result, message="report preview generated")


from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import HealthPayload, ResponseEnvelope

router = APIRouter()


@router.get("/health", response_model=ResponseEnvelope[HealthPayload])
def health_check() -> ResponseEnvelope[HealthPayload]:
    return ResponseEnvelope(
        data=HealthPayload(status="ok", timestamp=datetime.utcnow()),
        message="server is running",
    )


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import ResponseEnvelope
from app.schemas.onboarding import OnboardingRequest, OnboardingResult
from app.services.onboarding_service import create_onboarding_result

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[OnboardingResult])
def submit_onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[OnboardingResult]:
    result = create_onboarding_result(db, payload)
    return ResponseEnvelope(data=result, message="onboarding completed")


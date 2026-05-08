from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.mentor_repository import list_mentors
from app.schemas.common import ListPayload, ResponseEnvelope
from app.schemas.mentor import MentorSummary

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[ListPayload[MentorSummary]])
def get_mentors(db: Session = Depends(get_db)) -> ResponseEnvelope[ListPayload[MentorSummary]]:
    mentors = list_mentors(db)
    payload = ListPayload[MentorSummary](items=mentors, total=len(mentors))
    return ResponseEnvelope(data=payload, message="mentors fetched")


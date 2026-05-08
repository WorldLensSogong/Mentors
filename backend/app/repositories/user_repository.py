from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.mentor import InterestTopic
from app.models.user import User


def ensure_user_not_exists(db: Session, email: str, nickname: str) -> None:
    existing = db.scalar(select(User).where(or_(User.email == email, User.nickname == nickname)))
    if existing is not None:
        raise HTTPException(status_code=409, detail="user with same email or nickname already exists")


def get_topics_by_codes(db: Session, topic_codes: list[str]) -> list[InterestTopic]:
    if not topic_codes:
        return []
    stmt = select(InterestTopic).where(InterestTopic.code.in_(topic_codes))
    return db.scalars(stmt).all()


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


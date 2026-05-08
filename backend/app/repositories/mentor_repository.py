from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.level import LevelDefinition
from app.models.mentor import Mentor
from app.schemas.mentor import MentorSummary


def list_mentors(db: Session) -> list[MentorSummary]:
    stmt: Select[tuple[Mentor]] = (
        select(Mentor)
        .options(joinedload(Mentor.strategy), joinedload(Mentor.unlock_level))
        .where(Mentor.is_active.is_(True))
        .order_by(Mentor.is_free.desc(), Mentor.id.asc())
    )
    mentors = db.scalars(stmt).all()
    return [_to_summary(mentor) for mentor in mentors]


def get_mentor_model(db: Session, mentor_id: int) -> Mentor:
    stmt = (
        select(Mentor)
        .options(joinedload(Mentor.strategy), joinedload(Mentor.unlock_level))
        .where(Mentor.id == mentor_id, Mentor.is_active.is_(True))
    )
    mentor = db.scalar(stmt)
    if mentor is None:
        raise HTTPException(status_code=404, detail="mentor not found")
    return mentor


def list_recommendation_candidates(db: Session, risk_profile_tag: str | None) -> list[Mentor]:
    stmt = (
        select(Mentor)
        .options(joinedload(Mentor.strategy), joinedload(Mentor.unlock_level))
        .where(Mentor.is_active.is_(True))
        .order_by(Mentor.is_free.desc(), Mentor.id.asc())
    )
    mentors = db.scalars(stmt).all()
    if risk_profile_tag is None:
        return mentors[:3]

    matched = [mentor for mentor in mentors if mentor.strategy.risk_profile_tag == risk_profile_tag]
    fallback = [mentor for mentor in mentors if mentor not in matched]
    return (matched + fallback)[:3]


def get_level_one(db: Session) -> LevelDefinition:
    level = db.scalar(select(LevelDefinition).where(LevelDefinition.level_no == 1))
    if level is None:
        raise HTTPException(status_code=500, detail="level seed data is missing")
    return level


def _to_summary(mentor: Mentor) -> MentorSummary:
    return MentorSummary(
        id=mentor.id,
        code=mentor.code,
        name=mentor.name,
        one_liner=mentor.one_liner,
        philosophy=mentor.philosophy,
        strategy_name=mentor.strategy.name,
        risk_profile_tag=mentor.strategy.risk_profile_tag,
        unlock_level_no=mentor.unlock_level.level_no if mentor.unlock_level else None,
        is_free=mentor.is_free,
    )


from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MentorCatalogEntry:
    id: int
    slug: str
    name: str
    title: str
    summary: str
    mentor_strategy: str
    experience_match: tuple[str, ...]
    risk_match: tuple[str, ...]
    goal_match: tuple[str, ...]
    interest_match: tuple[str, ...]
    style_match: tuple[str, ...]


MENTOR_CATALOG: tuple[MentorCatalogEntry, ...] = (
    MentorCatalogEntry(
        id=1,
        slug="warren-buffett",
        name="워런 버핏",
        title="가치 투자 멘토",
        summary="장기 복리, 밸류에이션 원칙, 그리고 기다림의 중요성을 설명합니다.",
        mentor_strategy="value",
        experience_match=("beginner", "steady-builder"),
        risk_match=("steady",),
        goal_match=("build-habit", "protect-capital"),
        interest_match=(
            "value",
            "dividend",
            "long-term",
            "fundamentals",
            "domestic-stock",
            "us-stock",
            "finance",
            "etf",
        ),
        style_match=("gentle", "patient"),
    ),
    MentorCatalogEntry(
        id=2,
        slug="peter-lynch",
        name="피터 린치",
        title="생활밀착형 종목 발굴 멘토",
        summary="실생활 사례를 바탕으로 기업을 읽는 법을 쉽게 설명합니다.",
        mentor_strategy="growth",
        experience_match=("beginner", "exploring"),
        risk_match=("balanced", "steady"),
        goal_match=("find-ideas", "understand-companies"),
        interest_match=(
            "stocks",
            "growth",
            "earnings",
            "consumer",
            "tech",
            "it",
            "bio",
            "domestic-stock",
            "us-stock",
            "semiconductor",
            "battery",
            "ai",
            "entertainment-media",
            "fashion-consumer",
        ),
        style_match=("practical", "friendly", "gentle"),
    ),
    MentorCatalogEntry(
        id=3,
        slug="ray-dalio",
        name="레이 달리오",
        title="거시경제와 포트폴리오 멘토",
        summary="거시경제 프레임워크와 분산 투자, 구조적인 의사결정을 함께 다룹니다.",
        mentor_strategy="macro",
        experience_match=("exploring", "experienced"),
        risk_match=("balanced", "dynamic"),
        goal_match=("understand-news", "build-allocation"),
        interest_match=(
            "macro",
            "etf",
            "diversification",
            "portfolio",
            "tech",
            "it",
            "global",
            "energy",
            "finance",
            "us-stock",
        ),
        style_match=("structured", "analytical"),
    ),
)

_MENTOR_BY_ID = {entry.id: entry for entry in MENTOR_CATALOG}
_MENTOR_BY_SLUG = {entry.slug: entry for entry in MENTOR_CATALOG}


def list_catalog_mentors() -> tuple[MentorCatalogEntry, ...]:
    return MENTOR_CATALOG


def get_catalog_mentor_by_id(mentor_id: int) -> MentorCatalogEntry | None:
    return _MENTOR_BY_ID.get(mentor_id)


def get_catalog_mentor_by_slug(slug: str | None) -> MentorCatalogEntry | None:
    if slug is None:
        return None
    return _MENTOR_BY_SLUG.get(slug)


__all__ = [
    "MentorCatalogEntry",
    "get_catalog_mentor_by_id",
    "get_catalog_mentor_by_slug",
    "list_catalog_mentors",
]

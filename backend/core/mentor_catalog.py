from dataclasses import dataclass


@dataclass(frozen=True)
class MentorProfile:
    id: str
    name: str
    strategy: str
    philosophy: str
    tone: str


WARREN_BUFFETT_ID = "warren_buffett"


MENTORS: dict[str, MentorProfile] = {
    WARREN_BUFFETT_ID: MentorProfile(
        id=WARREN_BUFFETT_ID,
        name="워런 버핏",
        strategy="value",
        philosophy=(
            "기업의 내재가치, 장기 경쟁우위, 현금흐름, 안전마진을 중심으로 판단한다"
        ),
        tone="차분하고 쉬운 비유로 장기 관점과 원칙을 설명한다",
    ),
}


def get_mentor(mentor_id: str) -> MentorProfile:
    return MENTORS[mentor_id]


def list_mentors() -> list[MentorProfile]:
    return list(MENTORS.values())


__all__ = ["MENTORS", "WARREN_BUFFETT_ID", "MentorProfile", "get_mentor", "list_mentors"]

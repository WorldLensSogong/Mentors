"""멘토 전략 매핑 및 페르소나 관리."""

from core.contracts import MentorStrategy

from .dividend import SYSTEM_PROMPT as DIVIDEND_PROMPT
from .growth import SYSTEM_PROMPT as GROWTH_PROMPT
from .momentum import SYSTEM_PROMPT as MOMENTUM_PROMPT
from .value import SYSTEM_PROMPT as VALUE_PROMPT


def get_mentor_strategy(mentor_id: int) -> MentorStrategy:
    """멘토 ID를 기반으로 내재된 투자 전략을 반환한다."""
    mapping = {
        1: MentorStrategy.VALUE,
        2: MentorStrategy.GROWTH,
        3: MentorStrategy.DIVIDEND,
        4: MentorStrategy.MOMENTUM,
    }
    return mapping.get(mentor_id, MentorStrategy.VALUE)


def get_system_prompt(strategy: MentorStrategy) -> str:
    """투자 전략에 따른 시스템 프롬프트를 반환한다."""
    prompts = {
        MentorStrategy.VALUE: VALUE_PROMPT,
        MentorStrategy.GROWTH: GROWTH_PROMPT,
        MentorStrategy.DIVIDEND: DIVIDEND_PROMPT,
        MentorStrategy.MOMENTUM: MOMENTUM_PROMPT,
    }
    return prompts.get(strategy, VALUE_PROMPT)


__all__ = ["get_mentor_strategy", "get_system_prompt"]

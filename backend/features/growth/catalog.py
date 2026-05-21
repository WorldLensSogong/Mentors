from __future__ import annotations

from dataclasses import dataclass

from core.contracts import MentorStrategy, Tier
from features.learning import curriculum


@dataclass(frozen=True)
class TierConcept:
    id: int
    code: str
    title: str


@dataclass(frozen=True)
class PromotionChoice:
    id: str
    text: str


@dataclass(frozen=True)
class PromotionQuestion:
    id: str
    prompt: str
    choices: tuple[PromotionChoice, ...]
    correct_choice_id: str


def _build_tier_concepts() -> dict[Tier, tuple[TierConcept, ...]]:
    concepts_by_tier: dict[Tier, list[TierConcept]] = {tier: [] for tier in Tier}
    for concept in curriculum.list_concepts_for_strategy(MentorStrategy.VALUE):
        concepts_by_tier[concept.tier_required].append(
            TierConcept(
                int(concept.id),
                f"value_concept_{int(concept.id)}",
                concept.name,
            )
        )
    return {tier: tuple(items) for tier, items in concepts_by_tier.items()}


_TIER_CONCEPTS = _build_tier_concepts()


_PROMOTION_QUESTIONS: dict[Tier, tuple[PromotionQuestion, ...]] = {
    Tier.T1: (
        PromotionQuestion(
            "t1-q1",
            "Which choice best matches a margin-of-safety mindset?",
            (
                PromotionChoice("A", "Wait for a price below reasonable value."),
                PromotionChoice("B", "Buy because the chart moved quickly."),
                PromotionChoice("C", "Follow the loudest social post."),
                PromotionChoice("D", "Ignore business fundamentals."),
            ),
            "A",
        ),
        PromotionQuestion(
            "t1-q2",
            "If short-term volatility rises but the business thesis is unchanged, what fits T1?",
            (
                PromotionChoice("A", "Panic sell immediately."),
                PromotionChoice("B", "Re-check the thesis before reacting."),
                PromotionChoice("C", "Double down without review."),
                PromotionChoice("D", "Trade every intraday swing."),
            ),
            "B",
        ),
        PromotionQuestion(
            "t1-q3",
            "Intrinsic value is closest to which idea?",
            (
                PromotionChoice("A", "Yesterday's closing price"),
                PromotionChoice("B", "A rumor-driven target"),
                PromotionChoice("C", "Estimated business worth based on fundamentals"),
                PromotionChoice("D", "The highest price on social media"),
            ),
            "C",
        ),
        PromotionQuestion(
            "t1-q4",
            "Which signal matters most for long-term investing?",
            (
                PromotionChoice("A", "Business quality and staying power"),
                PromotionChoice("B", "One day of price momentum"),
                PromotionChoice("C", "A trending meme"),
                PromotionChoice("D", "A random ticker mention"),
            ),
            "A",
        ),
        PromotionQuestion(
            "t1-q5",
            "What is risk in the Mentors T1 context?",
            (
                PromotionChoice("A", "Any daily price drop"),
                PromotionChoice("B", "Only media sentiment"),
                PromotionChoice("C", "A temporary red candle"),
                PromotionChoice("D", "Permanent loss from a weak thesis or business"),
            ),
            "D",
        ),
    ),
    Tier.T2: (
        PromotionQuestion(
            "t2-q1",
            "What unlocks the debate arena in the docs?",
            (
                PromotionChoice("A", "Reaching T2"),
                PromotionChoice("B", "Paying for premium"),
                PromotionChoice("C", "Skipping onboarding"),
                PromotionChoice("D", "Posting more chats"),
            ),
            "A",
        ),
        PromotionQuestion(
            "t2-q2",
            "What is the best use of a counter-argument in debate?",
            (
                PromotionChoice("A", "Ignore it to stay confident"),
                PromotionChoice("B", "Use it to test your thesis"),
                PromotionChoice("C", "Always reverse the thesis"),
                PromotionChoice("D", "Turn it into a trade signal"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t2-q3",
            "Healthy position sizing is closest to which behavior?",
            (
                PromotionChoice("A", "Put every asset into one idea"),
                PromotionChoice("B", "Size positions with risk in mind"),
                PromotionChoice("C", "Size by social media volume"),
                PromotionChoice("D", "Scale only after daily gains"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t2-q4",
            "Portfolio balance mainly helps with what?",
            (
                PromotionChoice("A", "Guaranteeing profits"),
                PromotionChoice("B", "Making every idea equal"),
                PromotionChoice("C", "Removing all uncertainty"),
                PromotionChoice("D", "Reducing dependence on one thesis"),
            ),
            "D",
        ),
        PromotionQuestion(
            "t2-q5",
            "If new evidence weakens your original thesis, what fits T2 best?",
            (
                PromotionChoice("A", "Pretend the thesis is unchanged"),
                PromotionChoice("B", "Review and update the thesis consistently"),
                PromotionChoice("C", "Average down automatically"),
                PromotionChoice("D", "Trade only by emotion"),
            ),
            "B",
        ),
    ),
    Tier.T3: (
        PromotionQuestion(
            "t3-q1",
            "What unlocks additional mentors in MVP?",
            (
                PromotionChoice("A", "T3 or above"),
                PromotionChoice("B", "Any completed debate"),
                PromotionChoice("C", "Three daily reports"),
                PromotionChoice("D", "A one-time purchase"),
            ),
            "A",
        ),
        PromotionQuestion(
            "t3-q2",
            "Why compare multiple mentors at T3?",
            (
                PromotionChoice("A", "To collect random opinions"),
                PromotionChoice("B", "To test the same thesis through different lenses"),
                PromotionChoice("C", "To maximize daily alerts"),
                PromotionChoice("D", "To avoid building a personal framework"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t3-q3",
            "A sector rotation signal should be used how?",
            (
                PromotionChoice("A", "As the only decision input"),
                PromotionChoice("B", "As supporting context for the thesis"),
                PromotionChoice("C", "As a guarantee of returns"),
                PromotionChoice("D", "Only for meme stocks"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t3-q4",
            "Scenario mapping is most useful for what?",
            (
                PromotionChoice("A", "Predicting one exact future"),
                PromotionChoice("B", "Comparing possible outcomes before acting"),
                PromotionChoice("C", "Avoiding any written thesis"),
                PromotionChoice("D", "Trading by reaction alone"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t3-q5",
            "Allocation discipline at T3 means what?",
            (
                PromotionChoice("A", "Move all funds into the newest mentor"),
                PromotionChoice("B", "Allocate according to conviction and risk"),
                PromotionChoice("C", "Copy the strongest debate speaker"),
                PromotionChoice("D", "Use the same size for every idea always"),
            ),
            "B",
        ),
    ),
    Tier.T4: (
        PromotionQuestion(
            "t4-q1",
            "Rate sensitivity helps answer which question?",
            (
                PromotionChoice("A", "How a business reacts when rates change"),
                PromotionChoice("B", "Which chart pattern broke first"),
                PromotionChoice("C", "Which mentor speaks fastest"),
                PromotionChoice("D", "Which stock is most viral"),
            ),
            "A",
        ),
        PromotionQuestion(
            "t4-q2",
            "A macro regime lens should do what?",
            (
                PromotionChoice("A", "Replace company analysis"),
                PromotionChoice("B", "Frame how context changes thesis quality"),
                PromotionChoice("C", "Guarantee the timing entry"),
                PromotionChoice("D", "Ignore rates and liquidity"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t4-q3",
            "Earnings quality matters because it shows what?",
            (
                PromotionChoice("A", "Only last week's momentum"),
                PromotionChoice("B", "Whether profit quality supports the thesis"),
                PromotionChoice("C", "How to trade headlines faster"),
                PromotionChoice("D", "Which ticker trends more"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t4-q4",
            "Stress testing a thesis is mainly about what?",
            (
                PromotionChoice("A", "Assuming best-case only"),
                PromotionChoice("B", "Checking if the thesis survives bad scenarios"),
                PromotionChoice("C", "Picking the most complex model"),
                PromotionChoice("D", "Removing all uncertainty"),
            ),
            "B",
        ),
        PromotionQuestion(
            "t4-q5",
            "Cross-cycle judgment means what?",
            (
                PromotionChoice("A", "Use one fixed answer in every market"),
                PromotionChoice("B", "Adapt the same principles across different cycles"),
                PromotionChoice("C", "Ignore the current macro backdrop"),
                PromotionChoice("D", "Trade every cycle as a new meme"),
            ),
            "B",
        ),
    ),
}


def list_concepts_for_tier(tier: Tier) -> tuple[TierConcept, ...]:
    return _TIER_CONCEPTS[tier]


def list_promotion_questions(tier: Tier) -> tuple[PromotionQuestion, ...]:
    return _PROMOTION_QUESTIONS.get(tier, ())


def get_concept_by_id(concept_id: int) -> TierConcept | None:
    for concepts in _TIER_CONCEPTS.values():
        for concept in concepts:
            if concept.id == concept_id:
                return concept
    return None


__all__ = [
    "PromotionChoice",
    "PromotionQuestion",
    "TierConcept",
    "get_concept_by_id",
    "list_concepts_for_tier",
    "list_promotion_questions",
]

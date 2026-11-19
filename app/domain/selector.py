from collections.abc import Set as AbstractSet

from app.bank import QuestionBank
from app.domain.models import Question
from app.domain.rules import MAX_LEVEL, MIN_LEVEL


def levels_in_search_order(level: int) -> list[int]:
    """All levels, in the order the selector should try them.

    Closest level first. When two levels are equally close, the lower one first.
    Example: level 5 -> [5, 4, 6, 3, 7, 2, 8, 1, 9, 10]
    """
    all_levels = list(range(MIN_LEVEL, MAX_LEVEL + 1))

    def closeness(candidate: int) -> tuple[int, int]:
        distance = abs(candidate - level)
        return (distance, candidate)

    return sorted(all_levels, key=closeness)


def first_unserved_on_level(
    bank: QuestionBank, level: int, served: AbstractSet[str]
) -> Question | None:
    """The lowest-id question at this level that hasn't been served, or None."""
    questions = bank.by_level.get(level, ())
    for question in questions:
        if question.id not in served:
            return question

    return None


def next_question(bank: QuestionBank, level: int, served: AbstractSet[str]) -> Question | None:
    """Choose the next question for a learner at `level`.

    1. Only questions whose id is not in `served` count.
    2. Use the current level if it has one; otherwise the closest level that
       does. If a lower and a higher level are equally close, the lower wins.
    3. Within a level, the lowest id wins (bank.by_level is already sorted).

    Returns None when every question has been served.
    Never changes `bank` or `served`.
    """
    if level > MAX_LEVEL or level < MIN_LEVEL:
        raise ValueError(
            f"Level must be between {MIN_LEVEL} and {MAX_LEVEL}, level now is: {level}"
        )

    order = levels_in_search_order(level)

    for candidate_level in order:
        question = first_unserved_on_level(bank, candidate_level, served)
        if question is not None:
            return question

    return None

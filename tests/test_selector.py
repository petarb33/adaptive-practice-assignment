"""Choosing the next question: closest level, lower level on ties, lowest id."""

import pytest

from app.domain.selector import levels_in_search_order, next_question
from tests.conftest import small_bank


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (5, [5, 4, 6, 3, 7, 2, 8, 1, 9, 10]),
        (1, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        (10, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]),
        (6, [6, 5, 7, 4, 8, 3, 9, 2, 10, 1]),
    ],
)
def test_search_order_is_closest_first_lower_on_ties(level, expected):
    assert levels_in_search_order(level) == expected


def test_picks_lowest_id_at_current_level(bank):
    assert next_question(bank, 5, set()).id == "q17"


def test_skips_served_questions(bank):
    assert next_question(bank, 5, {"q17"}).id == "q18"
    assert next_question(bank, 5, {"q17", "q18", "q19"}).id == "q20"


def test_empty_level_ties_go_to_the_lower_level(bank):
    # Level 6 has no questions; 5 and 7 are equally close, so 5 wins.
    assert next_question(bank, 6, {"q17"}).id == "q18"


def test_tie_lower_wins_even_when_higher_has_lower_id():
    # Level 6 empty; level 5 has "z01", level 7 has "a01". Lower level wins, not lower id.
    bank = small_bank(("z01", 5), ("a01", 7))
    assert next_question(bank, 6, set()).id == "z01"


def test_falls_back_to_closest_level_when_current_level_is_used_up(bank):
    # Level 10 only has q30; after it, level 9 is closest.
    assert next_question(bank, 10, {"q30"}).id == "q27"


def test_falls_back_when_closer_level_is_exhausted(bank):
    # Level 6: 5 and 7 tie; once level 5 is used up, 7 is next closest.
    served = {"q17", "q18", "q19", "q20"}
    assert next_question(bank, 6, served).id == "q21"


def test_lowest_id_is_compared_naturally():
    bank = small_bank(("id10", 3), ("id2", 3), ("id1", 3))
    assert next_question(bank, 3, set()).id == "id1"
    assert next_question(bank, 3, {"id1"}).id == "id2"
    assert next_question(bank, 3, {"id1", "id2"}).id == "id10"


def test_returns_none_when_everything_is_served():
    bank = small_bank(("q01", 1), ("q02", 10))
    assert next_question(bank, 5, {"q01", "q02"}) is None


def test_does_not_mutate_served():
    bank = small_bank(("q01", 1))
    served: set[str] = set()
    next_question(bank, 1, served)
    assert served == set()


@pytest.mark.parametrize("level", [0, 11, -1])
def test_level_out_of_range_raises(level, bank):
    with pytest.raises(ValueError):
        next_question(bank, level, set())

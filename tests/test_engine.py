"""The session rules: level changes, retries, limits and when a session ends."""

from app.bank import QuestionBank
from app.domain.engine import apply_answer, start_session
from app.domain.rules import MAX_LEVEL, MIN_LEVEL, SESSION_LENGTH, START_LEVEL
from tests.conftest import right, small_bank, wrong


def answer(session, bank, correct: bool):
    qid = session.current_question_id
    return apply_answer(session, bank, right(bank, qid) if correct else wrong(bank, qid))


# --- start --------------------------------------------------------------------


def test_new_session_starts_at_level_5_with_q17(bank):
    session = start_session("s1", bank)
    assert session.level == START_LEVEL == 5
    assert session.current_question_id == "q17"
    assert session.attempt == 1
    assert not session.finished


def test_empty_bank_is_finished_at_start():
    session = start_session("s1", QuestionBank([]))
    assert session.finished


# --- answer rules -------------------------------------------------------------


def test_correct_first_attempt_finishes_question_and_levels_up(bank):
    session = start_session("s1", bank)
    outcome = answer(session, bank, correct=True)

    assert outcome.correct is True
    assert outcome.retry_open is False
    assert outcome.question_finished is True
    assert session.level == 6
    assert session.current_question_id == "q18"
    assert session.attempt == 1
    assert session.correct_first_attempt == 1


def test_wrong_first_attempt_opens_retry_and_keeps_level(bank):
    session = start_session("s1", bank)
    outcome = answer(session, bank, correct=False)

    assert outcome.correct is False
    assert outcome.retry_open is True
    assert outcome.question_finished is False
    assert session.level == 5
    assert session.current_question_id == "q17"
    assert session.attempt == 2
    assert session.questions_finished == 0


def test_correct_on_retry_finishes_question_and_keeps_level(bank):
    session = start_session("s1", bank)
    answer(session, bank, correct=False)
    outcome = answer(session, bank, correct=True)

    assert outcome.correct is True
    assert outcome.retry_open is False
    assert outcome.question_finished is True
    assert session.level == 5
    assert session.current_question_id == "q18"
    assert session.attempt == 1
    assert session.correct_on_retry == 1
    assert session.correct_first_attempt == 0


def test_wrong_on_retry_finishes_question_and_levels_down(bank):
    session = start_session("s1", bank)
    answer(session, bank, correct=False)
    outcome = answer(session, bank, correct=False)

    assert outcome.correct is False
    assert outcome.retry_open is False
    assert outcome.question_finished is True
    assert session.level == 4
    assert session.current_question_id == "q13"
    assert session.attempt == 1
    assert session.questions_finished == 1


def test_readme_example(bank):
    session = start_session("s1", bank)
    served = []
    for _ in range(3):
        served.append(session.current_question_id)
        answer(session, bank, correct=True)
    assert served == ["q17", "q18", "q21"]
    assert session.level == 8


# --- limits -------------------------------------------------------------------


def test_level_never_goes_above_10(bank):
    session = start_session("s1", bank)
    for _ in range(5):
        answer(session, bank, correct=True)
    assert session.level == MAX_LEVEL == 10

    answer(session, bank, correct=True)
    assert session.level == 10


def test_level_never_goes_below_1(bank):
    session = start_session("s1", bank)
    for _ in range(4):
        answer(session, bank, correct=False)
        answer(session, bank, correct=False)
    assert session.level == MIN_LEVEL == 1

    answer(session, bank, correct=False)
    answer(session, bank, correct=False)
    assert session.level == 1


def test_level_is_not_changed_to_match_the_served_question(bank):
    session = start_session("s1", bank)
    answer(session, bank, correct=True)  # level 6, serves q18 (difficulty 5)
    assert bank[session.current_question_id].difficulty == 5
    assert session.level == 6

    answer(session, bank, correct=False)  # wrong first attempt: still 6
    assert session.level == 6
    answer(session, bank, correct=True)  # right on retry: still 6, not 5
    assert session.level == 6


def test_a_wrong_first_attempt_at_level_10_does_not_change_level(bank):
    session = start_session("s1", bank)
    for _ in range(5):
        answer(session, bank, correct=True)
    answer(session, bank, correct=False)
    assert session.level == 10
    answer(session, bank, correct=False)
    assert session.level == 9


# --- session end --------------------------------------------------------------


def test_no_question_is_served_twice(bank):
    session = start_session("s1", bank)
    seen = []
    while not session.finished:
        seen.append(session.current_question_id)
        answer(session, bank, correct=len(seen) % 2 == 0)
        if session.attempt == 2:
            answer(session, bank, correct=False)
    assert len(seen) == len(set(seen))


def test_session_ends_after_10_finished_questions(bank):
    session = start_session("s1", bank)
    for i in range(SESSION_LENGTH):
        assert not session.finished, f"finished early after {i}"
        answer(session, bank, correct=True)
    assert SESSION_LENGTH == 10
    assert session.finished
    assert session.questions_finished == 10
    assert session.current_question_id is None


def test_retries_do_not_count_as_extra_questions(bank):
    session = start_session("s1", bank)
    for _ in range(SESSION_LENGTH):
        answer(session, bank, correct=False)
        assert not session.finished
        answer(session, bank, correct=True)
    assert session.finished
    assert session.questions_finished == 10
    assert session.correct_on_retry == 10


def test_session_ends_when_bank_runs_out():
    bank = small_bank(("q01", 5), ("q02", 1), ("q03", 9))
    session = start_session("s1", bank)
    for _ in range(3):
        assert not session.finished
        answer(session, bank, correct=True)
    assert session.finished
    assert session.questions_finished == 3


def test_counters_after_a_mixed_run(bank):
    session = start_session("s1", bank)
    answer(session, bank, correct=True)  # first-attempt correct: 5 -> 6
    answer(session, bank, correct=False)
    answer(session, bank, correct=True)  # retry correct: stays 6
    answer(session, bank, correct=False)
    answer(session, bank, correct=False)  # retry wrong: 6 -> 5
    answer(session, bank, correct=True)  # first-attempt correct: 5 -> 6

    assert session.questions_finished == 4
    assert session.correct_first_attempt == 2
    assert session.correct_on_retry == 1
    assert session.level == 6

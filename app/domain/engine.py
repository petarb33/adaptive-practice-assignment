from dataclasses import dataclass

from app.bank import QuestionBank
from app.domain.models import Session
from app.domain.rules import MAX_LEVEL, MIN_LEVEL, SESSION_LENGTH
from app.domain.selector import next_question


@dataclass(frozen=True)
class Outcome:
    """What happened when one answer was applied."""

    correct: bool
    retry_open: bool  # True only after a wrong first attempt
    question_finished: bool


def start_session(session_id: str, bank: QuestionBank) -> Session:
    session = Session(id=session_id)
    choose_next_question(session, bank)
    return session


def choose_next_question(session: Session, bank: QuestionBank):
    """Make the next question current, or end the session if there is none."""
    if session.questions_finished >= SESSION_LENGTH:
        end_session(session)
        return

    question = next_question(bank, session.level, session.served_ids)
    if question is None:
        end_session(session)
        return

    session.current_question_id = question.id
    session.attempt = 1
    session.served_ids.add(question.id)


def apply_answer(session: Session, bank: QuestionBank, answer: str) -> Outcome:
    if session.finished:
        raise ValueError("cannot answer: session finished")

    question = bank[session.current_question_id]
    is_correct = answer == question.correct_answer

    if session.attempt == 1:
        if is_correct:
            session.correct_first_attempt += 1
            session.level = level_up(session.level)
            finish_question(session, bank)
            return Outcome(correct=True, retry_open=False, question_finished=True)

        session.attempt = 2
        return Outcome(correct=False, retry_open=True, question_finished=False)

    if is_correct:
        session.correct_on_retry += 1
    else:
        session.level = level_down(session.level)

    finish_question(session, bank)
    return Outcome(correct=is_correct, retry_open=False, question_finished=True)


def end_session(session: Session) -> None:
    session.current_question_id = None
    session.attempt = 1


def finish_question(session: Session, bank: QuestionBank) -> None:
    session.questions_finished += 1
    choose_next_question(session, bank)


def level_up(level: int) -> int:
    return min(level + 1, MAX_LEVEL)


def level_down(level: int) -> int:
    return max(level - 1, MIN_LEVEL)

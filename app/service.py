import secrets
import string
from collections.abc import Callable

from app.bank import QuestionBank
from app.domain.engine import apply_answer, start_session
from app.domain.exceptions import InvalidOption, QuestionNotCurrent, SessionEnded
from app.schemas import AnswerResult, CurrentQuestion, Results, StartedSession
from app.store import DuplicateSessionId, InMemorySessionStore

# How many fresh ids start() tries before giving up. Only reached if the id space is nearly full.
MAX_ID_ATTEMPTS = 100


def random_session_id() -> str:
    """Three lowercase letters and three digits, e.g. "kqz402"."""
    letters = "".join(secrets.choice(string.ascii_lowercase) for _ in range(3))
    digits = "".join(secrets.choice(string.digits) for _ in range(3))
    return letters + digits


class PracticeService:
    def __init__(
        self,
        bank: QuestionBank,
        store: InMemorySessionStore,
        new_session_id: Callable[[], str] = random_session_id,
    ) -> None:
        self.bank = bank
        self.store = store
        self._new_session_id = new_session_id

    def start(self) -> StartedSession:
        """POST /sessions. A generated id that is already in use is replaced by a fresh one."""
        for _ in range(MAX_ID_ATTEMPTS):
            session = start_session(self._new_session_id(), self.bank)
            try:
                self.store.add(session)
            except DuplicateSessionId:
                continue
            return StartedSession(session_id=session.id, level=session.level)
        raise RuntimeError(f"no free session id after {MAX_ID_ATTEMPTS} attempts")

    def current_question(self, session_id: str) -> CurrentQuestion | None:
        """GET /sessions/{id}/question"""
        session = self.store.get(session_id)
        if session.finished:
            return None

        question = self.bank[session.current_question_id]
        return CurrentQuestion(
            question_id=question.id,
            text=question.text,
            options=question.options,
            difficulty=question.difficulty,  # the question's difficulty, not the session level
            attempt=session.attempt,
        )

    def answer(self, session_id: str, question_id: str, answer: str) -> AnswerResult:
        """POST /sessions/{id}/answers"""

        session = self.store.get(session_id)  # raises SessionNotFound

        if session.finished:
            raise SessionEnded(session_id)

        if question_id != session.current_question_id:
            raise QuestionNotCurrent(question_id, session.current_question_id)

        question = self.bank[question_id]
        if answer not in question.options:
            raise InvalidOption(answer, question.options)

        outcome = apply_answer(session, self.bank, answer)

        return AnswerResult(
            correct=outcome.correct,
            retry_open=outcome.retry_open,
            level=session.level,
            session_finished=session.finished,
            question_finished=outcome.question_finished,
            questions_finished=session.questions_finished,
        )

    def results(self, session_id: str) -> Results:
        """GET /sessions/{id}/results. Works during a session too."""
        session = self.store.get(session_id)  # raises SessionNotFound
        return Results(
            questions_finished=session.questions_finished,
            correct_first_attempt=session.correct_first_attempt,
            correct_on_retry=session.correct_on_retry,
            final_level=session.level,
            session_finished=session.finished,
        )

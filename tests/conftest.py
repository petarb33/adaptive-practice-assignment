"""Shared fixtures and helpers for the test suite."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.bank import QuestionBank
from app.config import DEFAULT_QUESTIONS_PATH
from app.domain.models import Question
from app.main import create_app


def make_q(
    qid: str,
    difficulty: int,
    correct: str = "a",
    options: tuple[str, ...] = ("a", "b", "c"),
) -> Question:
    return Question(
        id=qid,
        difficulty=difficulty,
        text=f"Question {qid}?",
        options=options,
        correct_answer=correct,
    )


def small_bank(*specs: tuple[str, int]) -> QuestionBank:
    """A tiny bank from (id, difficulty) pairs. Every correct answer is "a"."""
    return QuestionBank(make_q(qid, difficulty) for qid, difficulty in specs)


def right(bank: QuestionBank, qid: str) -> str:
    return bank[qid].correct_answer


def wrong(bank: QuestionBank, qid: str) -> str:
    question = bank[qid]
    return next(o for o in question.options if o != question.correct_answer)


@pytest.fixture(scope="session")
def bank() -> QuestionBank:
    """The real bank from data/questions.json. Read-only, so it can be shared."""
    return QuestionBank.load(DEFAULT_QUESTIONS_PATH)


@pytest.fixture
def client():
    # The context manager runs the lifespan, which loads the bank.
    with TestClient(create_app(DEFAULT_QUESTIONS_PATH)) as c:
        yield c


@pytest.fixture
def new_session(client) -> Callable[[], str]:
    def _new() -> str:
        response = client.post("/sessions")
        assert response.status_code == 201
        return response.json()["session_id"]

    return _new


@pytest.fixture
def play(client, bank):
    """play(sid, correct) answers the current question right or wrong; returns the answer JSON."""

    def _play(session_id: str, correct: bool) -> dict:
        question = client.get(f"/sessions/{session_id}/question").json()
        qid = question["question_id"]
        answer = right(bank, qid) if correct else wrong(bank, qid)
        response = client.post(
            f"/sessions/{session_id}/answers",
            json={"question_id": qid, "answer": answer},
        )
        assert response.status_code == 200, response.text
        return response.json()

    return _play

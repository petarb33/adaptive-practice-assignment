"""The HTTP API: shapes, the rules end to end, and errors."""

import re

import pytest

from tests.conftest import right, wrong


def get_question(client, sid):
    return client.get(f"/sessions/{sid}/question")


def post_answer(client, sid, question_id, answer):
    return client.post(
        f"/sessions/{sid}/answers", json={"question_id": question_id, "answer": answer}
    )


def finish_session(play, sid):
    for _ in range(10):
        play(sid, correct=True)


# --- start --------------------------------------------------------------------


def test_start_session(client):
    response = client.post("/sessions")
    assert response.status_code == 201
    body = response.json()
    assert body["level"] == 5
    assert re.fullmatch(r"[a-z]{3}[0-9]{3}", body["session_id"])


def test_sessions_are_independent(client, new_session, play):
    a, b = new_session(), new_session()
    assert a != b
    play(a, correct=True)
    assert get_question(client, a).json()["question_id"] == "q18"
    assert get_question(client, b).json()["question_id"] == "q17"


# --- current question ---------------------------------------------------------


def test_question_shape_and_no_correct_answer(client, new_session, bank):
    sid = new_session()
    response = get_question(client, sid)
    assert response.status_code == 200
    body = response.json()

    assert body["question_id"] == "q17"
    assert body["text"] == bank["q17"].text
    assert body["options"] == list(bank["q17"].options)
    assert body["difficulty"] == 5
    assert body["attempt"] == 1
    assert "correct_answer" not in body


def test_question_is_stable_until_answered(client, new_session):
    sid = new_session()
    first = get_question(client, sid).json()
    second = get_question(client, sid).json()
    assert first == second


def test_retry_returns_same_question_with_attempt_2(client, new_session, bank):
    sid = new_session()
    post_answer(client, sid, "q17", wrong(bank, "q17"))
    body = get_question(client, sid).json()
    assert body["question_id"] == "q17"
    assert body["attempt"] == 2


# --- answers ------------------------------------------------------------------


def test_answer_shape_correct_first_attempt(client, new_session, bank):
    sid = new_session()
    response = post_answer(client, sid, "q17", right(bank, "q17"))
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["retry_open"] is False
    assert body["level"] == 6
    assert body["session_finished"] is False


def test_wrong_then_right_over_http(client, new_session, bank):
    sid = new_session()
    first = post_answer(client, sid, "q17", wrong(bank, "q17")).json()
    assert first == first | {"correct": False, "retry_open": True, "level": 5}

    second = post_answer(client, sid, "q17", right(bank, "q17")).json()
    assert second == second | {"correct": True, "retry_open": False, "level": 5}


def test_wrong_then_wrong_over_http(client, new_session, bank):
    sid = new_session()
    post_answer(client, sid, "q17", wrong(bank, "q17"))
    body = post_answer(client, sid, "q17", wrong(bank, "q17")).json()
    assert body == body | {"correct": False, "retry_open": False, "level": 4}
    assert get_question(client, sid).json()["question_id"] == "q13"


def test_readme_example_over_http(client, new_session, play):
    sid = new_session()
    served = []
    for _ in range(3):
        served.append(get_question(client, sid).json()["question_id"])
        last = play(sid, correct=True)
    assert served == ["q17", "q18", "q21"]
    assert last["level"] == 8


def test_answer_is_compared_exactly(client, new_session, bank):
    sid = new_session()
    correct = right(bank, "q17")
    response = post_answer(client, sid, "q17", f" {correct}")
    assert response.status_code == 422  # not one of the options


# --- results ------------------------------------------------------------------


def test_results_mid_session(client, new_session, play):
    sid = new_session()
    play(sid, correct=True)  # 5 -> 6, first attempt
    play(sid, correct=False)
    play(sid, correct=True)  # retry correct, stays 6

    body = client.get(f"/sessions/{sid}/results").json()
    assert body == {
        "questions_finished": 2,
        "correct_first_attempt": 1,
        "correct_on_retry": 1,
        "final_level": 6,
        "session_finished": False,
    }


def test_full_session_results(client, new_session, play):
    sid = new_session()
    results = []
    for i in range(10):
        if i % 3 == 0:
            results.append(play(sid, correct=True))
        elif i % 3 == 1:
            play(sid, correct=False)
            results.append(play(sid, correct=True))
        else:
            play(sid, correct=False)
            results.append(play(sid, correct=False))

    assert [r["session_finished"] for r in results] == [False] * 9 + [True]

    body = client.get(f"/sessions/{sid}/results").json()
    assert body["questions_finished"] == 10
    assert body["correct_first_attempt"] == 4  # i = 0, 3, 6, 9
    assert body["correct_on_retry"] == 3  # i = 1, 4, 7
    assert body["final_level"] == results[-1]["level"]
    assert body["session_finished"] is True


# --- errors -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "json"),
    [
        ("get", "/sessions/nope/question", None),
        ("post", "/sessions/nope/answers", {"question_id": "q17", "answer": "32"}),
        ("get", "/sessions/nope/results", None),
    ],
)
def test_unknown_session_is_404(client, method, path, json):
    response = client.request(method, path, json=json)
    assert response.status_code == 404
    assert response.json()["error"] == "session_not_found"


@pytest.mark.parametrize("question_id", ["q18", "q99"])
def test_answer_to_a_question_that_is_not_current_is_409(client, new_session, bank, question_id):
    sid = new_session()
    response = post_answer(client, sid, question_id, "anything")
    assert response.status_code == 409
    assert response.json()["error"] == "question_not_current"

    # Nothing changed.
    assert get_question(client, sid).json()["attempt"] == 1
    assert client.get(f"/sessions/{sid}/results").json()["final_level"] == 5


def test_answer_after_session_ended_is_409(client, new_session, play, bank):
    sid = new_session()
    finish_session(play, sid)
    response = post_answer(client, sid, "q17", right(bank, "q17"))
    assert response.status_code == 409
    assert response.json()["error"] == "session_finished"


def test_question_after_session_ended_says_finished(client, new_session, play):
    sid = new_session()
    finish_session(play, sid)
    response = get_question(client, sid)
    assert response.status_code == 200
    body = response.json()
    assert body["session_finished"] is True
    assert body.get("question_id") is None


@pytest.mark.parametrize("bad_answer", ["999", "", "thirty-two"])
def test_answer_not_in_options_is_422_and_uses_no_attempt(client, new_session, bank, bad_answer):
    sid = new_session()
    response = post_answer(client, sid, "q17", bad_answer)
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_option"

    assert get_question(client, sid).json()["attempt"] == 1

    # A real wrong answer still opens the retry, so the first attempt was not used.
    body = post_answer(client, sid, "q17", wrong(bank, "q17")).json()
    assert body["retry_open"] is True


def test_invalid_option_during_retry_uses_no_attempt(client, new_session, bank):
    sid = new_session()
    post_answer(client, sid, "q17", wrong(bank, "q17"))
    assert post_answer(client, sid, "q17", "999").status_code == 422
    assert get_question(client, sid).json()["attempt"] == 2
    body = post_answer(client, sid, "q17", right(bank, "q17")).json()
    assert body["level"] == 5  # right on retry, level unchanged


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"json": {"question_id": "q17"}}, id="missing-answer"),
        pytest.param({"json": {"answer": "32"}}, id="missing-question-id"),
        pytest.param({"json": {"question_id": "q17", "answer": 32}}, id="number-answer"),
        pytest.param({"json": {"question_id": 17, "answer": "32"}}, id="number-question-id"),
        pytest.param(
            {"content": "not json", "headers": {"content-type": "application/json"}},
            id="not-json",
        ),
    ],
)
def test_malformed_body_is_422(client, new_session, kwargs):
    sid = new_session()
    response = client.post(f"/sessions/{sid}/answers", **kwargs)
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_request"
    assert get_question(client, sid).json()["attempt"] == 1

"""Loading and validating the question bank."""

import json

import pytest

from app.bank import BankError, QuestionBank


def write_bank(tmp_path, questions) -> str:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps({"questions": questions}), encoding="utf-8")
    return path


def q(qid="q01", difficulty=1, options=("a", "b"), correct="a") -> dict:
    return {
        "id": qid,
        "difficulty": difficulty,
        "text": "?",
        "options": list(options),
        "correct_answer": correct,
    }


def test_real_bank_loads_30_questions(bank):
    assert len(bank) == 30
    assert "q17" in bank
    assert bank["q17"].difficulty == 5


def test_levels_are_sorted_by_id(bank):
    for questions in bank.by_level.values():
        ids = [int(question.id[1:]) for question in questions]
        assert ids == sorted(ids)


def test_uneven_levels_are_kept(bank):
    assert 6 not in bank.by_level
    assert len(bank.by_level[10]) == 1


def test_valid_custom_file_loads(tmp_path):
    bank = QuestionBank.load(write_bank(tmp_path, [q("q01"), q("q02", 3)]))
    assert len(bank) == 2


@pytest.mark.parametrize(
    "questions",
    [
        pytest.param([q("q01"), q("q01")], id="duplicate-id"),
        pytest.param([q(correct="z")], id="correct-not-in-options"),
        pytest.param([q(options=("a", "a"))], id="duplicate-options"),
        pytest.param([q(difficulty=0)], id="difficulty-0"),
        pytest.param([q(difficulty=11)], id="difficulty-11"),
        pytest.param([q(options=("a",))], id="single-option"),
        pytest.param([{"id": "q01"}], id="missing-fields"),
    ],
)
def test_invalid_questions_raise_bank_error(tmp_path, questions):
    with pytest.raises(BankError):
        QuestionBank.load(write_bank(tmp_path, questions))


def test_missing_file_raises_bank_error(tmp_path):
    with pytest.raises(BankError):
        QuestionBank.load(tmp_path / "nope.json")


def test_invalid_json_raises_bank_error(tmp_path):
    path = tmp_path / "questions.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(BankError):
        QuestionBank.load(path)


@pytest.mark.parametrize("content", [[], {"items": []}, {"questions": "x"}])
def test_wrong_top_level_shape_raises_bank_error(tmp_path, content):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(BankError):
        QuestionBank.load(path)

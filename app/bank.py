import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from app.domain.models import Question


class BankError(ValueError):
    pass


def id_sort_key(question_id: str) -> tuple:
    parts = re.split(r"(\d+)", question_id)
    return tuple(int(p) if i % 2 else p for i, p in enumerate(parts))


class QuestionBank:
    def __init__(self, questions: Iterable[Question]) -> None:
        by_id: dict[str, Question] = {}
        for q in questions:
            if q.id in by_id:
                raise BankError(f"duplicate question id {q.id}")
            by_id[q.id] = q

        grouped: defaultdict[int, list[Question]] = defaultdict(list)
        for q in by_id.values():
            grouped[q.difficulty].append(q)

        self.by_id: dict[str, Question] = by_id
        self.by_level: dict[int, tuple[Question, ...]] = {
            level: tuple(sorted(qs, key=lambda q: id_sort_key(q.id)))
            for level, qs in sorted(grouped.items())
        }

    @classmethod
    def load(cls, path: str | Path):
        path = Path(path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise BankError(f"question file not found: {path}") from None
        except json.JSONDecodeError as e:
            raise BankError(f"{path} is not valid JSON: {e}") from None

        if not isinstance(raw, dict) or not isinstance(raw.get("questions"), list):
            raise BankError(f'{path}: expected an object with a "questions" list')
        raw = raw["questions"]
        questions = []
        for i, item in enumerate(raw):
            try:
                questions.append(Question.model_validate(item))
            except ValidationError as e:
                q_id = item.get("id", "?") if isinstance(item, dict) else "?"
                raise BankError(f"{path}: question #{i} (id {q_id}) is invalid:\n{e}") from None

        return cls(questions)

    def __getitem__(self, question_id: str) -> Question:
        return self.by_id[question_id]

    def __contains__(self, question_id: object) -> bool:
        return question_id in self.by_id

    def __len__(self) -> int:
        return len(self.by_id)

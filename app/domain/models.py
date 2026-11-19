from dataclasses import dataclass, field

from pydantic import BaseModel, Field, model_validator

from app.domain.rules import START_LEVEL


class Question(BaseModel):
    id: str = Field(min_length=3)
    difficulty: int = Field(ge=1, le=10)
    text: str = Field(min_length=1)
    options: tuple[str, ...] = Field(min_length=2)
    correct_answer: str

    @model_validator(mode="after")
    def check(self):
        if len(self.options) != len(set(self.options)):
            raise ValueError("options contain duplicates")
        if self.correct_answer not in self.options:
            raise ValueError("correct_answer is not included in options")
        return self


@dataclass
class Session:
    id: str
    level: int = START_LEVEL

    current_question_id: str | None = None
    attempt: int = 1

    served_ids: set[str] = field(default_factory=set)

    questions_finished: int = 0
    correct_first_attempt: int = 0
    correct_on_retry: int = 0

    @property
    def finished(self) -> bool:
        return self.current_question_id is None

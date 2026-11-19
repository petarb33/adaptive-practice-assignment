from pydantic import BaseModel, ConfigDict, StrictStr


class Response(BaseModel):
    """Base for responses: read-only once built."""

    model_config = ConfigDict(frozen=True)


# POST /sessions
class StartedSession(Response):
    session_id: str
    level: int


# GET /sessions/{id}/question
class CurrentQuestion(Response):
    question_id: str
    text: str
    options: tuple[str, ...]
    difficulty: int
    attempt: int
    session_finished: bool = False


class SessionFinishedQuestion(Response):
    """Returned instead of a question once the session has ended."""

    session_finished: bool = True
    question_id: None = None
    message: str = "The session has finished; no more questions. See the results endpoint."


# POST /sessions/{id}/answers
class AnswerIn(BaseModel):
    question_id: StrictStr
    answer: StrictStr


class AnswerResult(Response):
    correct: bool
    retry_open: bool
    level: int
    session_finished: bool
    question_finished: bool  # (added)
    questions_finished: int  # (added)


# GET /sessions/{id}/results
class Results(Response):
    questions_finished: int
    correct_first_attempt: int
    correct_on_retry: int
    final_level: int
    session_finished: bool


class ErrorOut(Response):
    error: str
    message: str

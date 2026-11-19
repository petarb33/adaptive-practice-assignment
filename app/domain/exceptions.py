class PracticeError(Exception):
    """Base class"""


class SessionNotFound(PracticeError):
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Unknown session {session_id!r}")


class SessionEnded(PracticeError):
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id!r} has finished; see its results")


class QuestionNotCurrent(PracticeError):
    def __init__(self, given_id: str, current_id: str) -> None:
        self.given_id = given_id
        self.current_id = current_id
        super().__init__(
            f"Question {given_id!r} is not the current question; the current question is {current_id!r}"
        )


class InvalidOption(PracticeError):
    def __init__(self, answer: str, options: tuple[str, ...]) -> None:
        self.answer = answer
        self.options = options
        super().__init__(
            f"{answer!r} is not one of the options {list(options)}; no attempt was used"
        )

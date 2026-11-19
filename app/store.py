from app.domain.exceptions import SessionNotFound
from app.domain.models import Session


class DuplicateSessionId(Exception):
    """A session with this id is already stored."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"session id {session_id!r} is already in use")


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def add(self, session: Session) -> None:
        """Store a new session. Never overwrites: raises DuplicateSessionId instead."""
        if session.id in self._sessions:
            raise DuplicateSessionId(session.id)
        self._sessions[session.id] = session

    def get(self, session_id: str) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionNotFound(session_id) from None

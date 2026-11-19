"""Session id generation and handling of duplicate ids."""

import re

import pytest

from app.domain.engine import start_session
from app.service import MAX_ID_ATTEMPTS, PracticeService, random_session_id
from app.store import DuplicateSessionId, InMemorySessionStore

ID_PATTERN = re.compile(r"[a-z]{3}[0-9]{3}")


def test_random_session_id_format():
    for _ in range(1000):
        assert ID_PATTERN.fullmatch(random_session_id())


def test_store_rejects_duplicate_id_and_keeps_original(bank):
    store = InMemorySessionStore()
    original = start_session("abc123", bank)
    store.add(original)

    with pytest.raises(DuplicateSessionId):
        store.add(start_session("abc123", bank))
    assert store.get("abc123") is original


def test_start_regenerates_an_id_that_is_already_in_use(bank):
    ids = iter(["abc123", "abc123", "xyz789"])
    service = PracticeService(bank, InMemorySessionStore(), new_session_id=ids.__next__)

    first = service.start()
    first_session = service.store.get(first.session_id)
    second = service.start()

    assert first.session_id == "abc123"
    assert second.session_id == "xyz789"
    assert service.store.get("abc123") is first_session


def test_start_gives_up_when_no_free_id_is_found(bank):
    calls = 0

    def always_same() -> str:
        nonlocal calls
        calls += 1
        return "abc123"

    service = PracticeService(bank, InMemorySessionStore(), new_session_id=always_same)
    service.start()
    calls = 0

    with pytest.raises(RuntimeError):
        service.start()
    assert calls == MAX_ID_ATTEMPTS

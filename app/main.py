from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api import errors, routes
from app.bank import QuestionBank
from app.config import get_questions_path
from app.service import PracticeService
from app.store import InMemorySessionStore


def create_app(questions_path: str | Path | None = None) -> FastAPI:
    if questions_path is None:
        questions_path = get_questions_path()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        bank = QuestionBank.load(questions_path)
        app.state.service = PracticeService(bank, InMemorySessionStore())
        yield

    app = FastAPI(title="Adaptive Practice Service", lifespan=lifespan)
    app.include_router(routes.router)
    errors.register(app)
    return app

from fastapi import APIRouter

from app.api.deps import ServiceDep
from app.schemas import (
    AnswerIn,
    AnswerResult,
    CurrentQuestion,
    ErrorOut,
    Results,
    SessionFinishedQuestion,
    StartedSession,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


NOT_FOUND = {404: {"model": ErrorOut, "description": "Unknown session"}}


@router.post("", status_code=201)
async def start_session(service: ServiceDep) -> StartedSession:
    return service.start()


@router.get("/{session_id}/question", responses=NOT_FOUND)
async def get_question(
    session_id: str, service: ServiceDep
) -> CurrentQuestion | SessionFinishedQuestion:
    question = service.current_question(session_id)
    if question is None:
        return SessionFinishedQuestion()
    return question


@router.post(
    "/{session_id}/answers",
    responses={
        **NOT_FOUND,
        409: {"model": ErrorOut, "description": "Session finished, or not the current question"},
        422: {
            "model": ErrorOut,
            "description": "Answer isn't one of the options (no attempt used), or bad body",
        },
    },
)
async def answer_question(session_id: str, body: AnswerIn, service: ServiceDep) -> AnswerResult:
    return service.answer(session_id, body.question_id, body.answer)


@router.get("/{session_id}/results", responses=NOT_FOUND)
async def get_results(session_id: str, service: ServiceDep) -> Results:
    return service.results(session_id)

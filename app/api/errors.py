from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import (
    InvalidOption,
    PracticeError,
    QuestionNotCurrent,
    SessionEnded,
    SessionNotFound,
)
from app.schemas import ErrorOut

ERRORS: dict[type[PracticeError], tuple[int, str]] = {
    SessionNotFound: (404, "session_not_found"),
    SessionEnded: (409, "session_finished"),
    QuestionNotCurrent: (409, "question_not_current"),
    InvalidOption: (422, "invalid_option"),
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    body = ErrorOut(error=code, message=message)
    return JSONResponse(status_code=status, content=body.model_dump())


async def handle_practice_error(request: Request, exc: PracticeError) -> JSONResponse:
    """The four errors from domain/exceptions.py."""
    status, code = ERRORS.get(type(exc), (400, "bad_request"))
    return error_response(status, code, str(exc))


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """A body FastAPI couldn't read: bad JSON, a missing field, a number instead of a string."""
    first = exc.errors()[0]
    where = ".".join(str(part) for part in first["loc"])  # e.g. "body.answer"
    return error_response(422, "invalid_request", f"{where}: {first['msg']}")


async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "http_error"
    return error_response(exc.status_code, code, str(exc.detail))


def register(app: FastAPI) -> None:
    app.add_exception_handler(PracticeError, handle_practice_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)

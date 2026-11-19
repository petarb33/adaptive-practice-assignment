from typing import Annotated

from fastapi import Depends, Request

from app.service import PracticeService


def get_service(request: Request) -> PracticeService:
    return request.app.state.service


ServiceDep = Annotated[PracticeService, Depends(get_service)]

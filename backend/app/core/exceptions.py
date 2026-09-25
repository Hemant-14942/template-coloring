from fastapi import Request
from fastapi.responses import JSONResponse


class TemplateNotFoundError(Exception):
    def __init__(self, template_id: str) -> None:
        self.template_id = template_id


class SlideNotFoundError(Exception):
    def __init__(self, template_id: str, number: int) -> None:
        self.template_id = template_id
        self.number = number


async def template_not_found_handler(_: Request, exc: TemplateNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": f"Template '{exc.template_id}' was not found."})


async def slide_not_found_handler(_: Request, exc: SlideNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": f"Slide {exc.number} was not found in template '{exc.template_id}'."},
    )

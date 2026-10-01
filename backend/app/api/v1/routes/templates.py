import logging

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from app.api.deps import template_store
from app.schemas.template import RecolorRequest, SlideOut, TemplateDetail, TemplateSummary
from app.services.icon import prepare_icon, icon_slot
from app.services.recolor import recolor_pptx
from app.services.template_store import TemplateStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
ASSET_CACHE = "public, max-age=86400"


@router.get("", response_model=list[TemplateSummary])
def list_templates(store: TemplateStore = Depends(template_store)) -> list[TemplateSummary]:
    return [TemplateSummary(id=t.id, name=t.name, slide_count=len(t.slides)) for t in store.list()]


def _versioned_asset_url(request: Request, route_name: str, template_id: str, number: int, path) -> str:
    """File mtime in the URL so a replaced preview is not served from the browser cache."""
    url = str(request.url_for(route_name, template_id=template_id, number=number).path)
    if path.is_file():
        return f"{url}?v={int(path.stat().st_mtime)}"
    return url


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str, request: Request, store: TemplateStore = Depends(template_store)) -> TemplateDetail:
    config = store.get(template_id)
    slides = [
        SlideOut(
            **s.model_dump(),
            preview_url=_versioned_asset_url(
                request, "slide_preview", template_id, s.number, store.slide_asset(template_id, s.number, "preview")
            ),
            mask_url=_versioned_asset_url(
                request, "slide_mask", template_id, s.number, store.slide_asset(template_id, s.number, "mask")
            ),
        )
        for s in config.slides
    ]
    return TemplateDetail(id=config.id, name=config.name, base_colors=config.base_colors, slides=slides)


@router.get("/{template_id}/slides/{number}/preview", name="slide_preview")
def slide_preview(template_id: str, number: int, store: TemplateStore = Depends(template_store)) -> FileResponse:
    return FileResponse(store.slide_asset(template_id, number, "preview"), media_type="image/jpeg",
                        headers={"Cache-Control": ASSET_CACHE})


@router.get("/{template_id}/slides/{number}/mask", name="slide_mask")
def slide_mask(template_id: str, number: int, store: TemplateStore = Depends(template_store)) -> FileResponse:
    return FileResponse(store.slide_asset(template_id, number, "mask"), media_type="image/png",
                        headers={"Cache-Control": ASSET_CACHE})


async def _recolor_input(request: Request) -> tuple[str, str | None, bytes | None]:
    """Read colors and an optional icon. Closing the form deletes the upload spool."""
    if "multipart/form-data" in request.headers.get("content-type", ""):
        form = await request.form()
        try:
            background = form.get("background")
            upload = form.get("icon")
            icon = await upload.read() if isinstance(upload, UploadFile) and upload.filename else None
            body = RecolorRequest(
                color=str(form.get("color") or ""),
                background=str(background) if background else None,
            )
            return body.color, body.background, icon
        finally:
            await form.close()
    body = RecolorRequest.model_validate_json(await request.body())
    return body.color, body.background, None


@router.post("/{template_id}/recolor")
async def recolor(template_id: str, request: Request, store: TemplateStore = Depends(template_store)) -> Response:
    try:
        color, background, icon = await _recolor_input(request)
    except ValidationError as exc:
        return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})
    config = store.get(template_id)
    source = store.pptx_path(template_id).read_bytes()
    replaced_icon = icon is not None
    icon_png = None
    try:
        if icon:
            canvas, slot = await run_in_threadpool(icon_slot, source)
            icon_png = await run_in_threadpool(prepare_icon, icon, canvas, slot)
        data = await run_in_threadpool(recolor_pptx, source, config, color, background, icon_png)
    finally:
        del icon, icon_png
    filename = f"{template_id}-{color}.pptx" if not background else f"{template_id}-{color}-bg{background}.pptx"
    logger.info(
        "Recolored %s with #%s background #%s icon %s",
        template_id, color, background or "unchanged", "replaced" if replaced_icon else "original",
    )
    return Response(
        content=data,
        media_type=PPTX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

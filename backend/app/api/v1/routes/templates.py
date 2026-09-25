import logging

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response

from app.api.deps import template_store
from app.schemas.template import RecolorRequest, SlideOut, TemplateDetail, TemplateSummary
from app.services.recolor import recolor_pptx
from app.services.template_store import TemplateStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["templates"])

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
ASSET_CACHE = "public, max-age=86400"


@router.get("", response_model=list[TemplateSummary])
def list_templates(store: TemplateStore = Depends(template_store)) -> list[TemplateSummary]:
    return [TemplateSummary(id=t.id, name=t.name, slide_count=len(t.slides)) for t in store.list()]


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str, request: Request, store: TemplateStore = Depends(template_store)) -> TemplateDetail:
    config = store.get(template_id)
    slides = [
        SlideOut(
            **s.model_dump(),
            preview_url=str(request.url_for("slide_preview", template_id=template_id, number=s.number).path),
            mask_url=str(request.url_for("slide_mask", template_id=template_id, number=s.number).path),
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


@router.post("/{template_id}/recolor")
async def recolor(template_id: str, body: RecolorRequest, store: TemplateStore = Depends(template_store)) -> Response:
    config = store.get(template_id)
    source = store.pptx_path(template_id).read_bytes()
    data = await run_in_threadpool(recolor_pptx, source, config, body.color)
    filename = f"{template_id}-{body.color}.pptx"
    logger.info("Recolored %s with #%s", template_id, body.color)
    return Response(
        content=data,
        media_type=PPTX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

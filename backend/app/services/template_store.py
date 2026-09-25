import json
import logging
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import SlideNotFoundError, TemplateNotFoundError
from app.schemas.template import TemplateConfig

logger = logging.getLogger(__name__)


class TemplateStore:
    """Loads template folders: <templates_dir>/<id>/template.json + template.pptx + previews/ + masks/."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._templates: dict[str, TemplateConfig] = {}
        self.reload()

    def reload(self) -> None:
        self._templates.clear()
        for cfg_path in sorted(self.root.glob("*/template.json")):
            config = TemplateConfig.model_validate(json.loads(cfg_path.read_text(encoding="utf-8")))
            self._templates[config.id] = config
            logger.info("Loaded template %s (%d slides)", config.id, len(config.slides))

    def list(self) -> list[TemplateConfig]:
        return list(self._templates.values())

    def get(self, template_id: str) -> TemplateConfig:
        if template_id not in self._templates:
            raise TemplateNotFoundError(template_id)
        return self._templates[template_id]

    def folder(self, template_id: str) -> Path:
        self.get(template_id)
        return self.root / template_id

    def pptx_path(self, template_id: str) -> Path:
        return self.folder(template_id) / self.get(template_id).file

    def slide_asset(self, template_id: str, number: int, kind: str) -> Path:
        config = self.get(template_id)
        if not any(s.number == number for s in config.slides):
            raise SlideNotFoundError(template_id, number)
        sub, ext = ("previews", "jpg") if kind == "preview" else ("masks", "png")
        path = self.folder(template_id) / sub / f"slide-{number:02d}.{ext}"
        if not path.is_file():
            raise SlideNotFoundError(template_id, number)
        return path


@lru_cache
def get_template_store() -> TemplateStore:
    return TemplateStore(get_settings().templates_dir)

import re

from pydantic import BaseModel, Field, field_validator

HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")


class ColorSet(BaseModel):
    dark: str
    main: str
    bright: str


class SlideConfig(BaseModel):
    number: int
    name: str
    change: str
    recolor: bool = True


class TemplateConfig(BaseModel):
    id: str
    name: str
    file: str
    base_colors: ColorSet
    theme_accent: str | None = "accent1"
    slides: list[SlideConfig]


class SlideOut(SlideConfig):
    preview_url: str
    mask_url: str


class TemplateSummary(BaseModel):
    id: str
    name: str
    slide_count: int


class TemplateDetail(BaseModel):
    id: str
    name: str
    base_colors: ColorSet
    slides: list[SlideOut]


class RecolorRequest(BaseModel):
    color: str = Field(..., examples=["#1F4E9A"])

    @field_validator("color")
    @classmethod
    def validate_hex(cls, value: str) -> str:
        if not HEX_RE.match(value):
            raise ValueError("Color must be a 6-digit hex code like #1F4E9A.")
        return value.lstrip("#").upper()

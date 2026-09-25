"""Rewrites colors inside a .pptx (a zip of XML parts) without touching anything else."""
import io
import re
import zipfile

from app.schemas.template import ColorSet, TemplateConfig
from app.services.color import shades_for

SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
THEME_PATH = "ppt/theme/theme1.xml"


def _slide_replacer(base: ColorSet, new: ColorSet):
    swap = {base.dark.upper(): new.dark, base.main.upper(): new.main, base.bright.upper(): new.bright}
    pattern = re.compile(
        r'(<a:srgbClr val=")(' + "|".join(map(re.escape, swap)) + r')(")', flags=re.IGNORECASE
    )
    return lambda xml: pattern.sub(lambda m: m.group(1) + swap[m.group(2).upper()] + m.group(3), xml)


def _theme_replacer(accent: str, color: str):
    pattern = re.compile(rf'(<a:{accent}>\s*<a:srgbClr val=")[0-9A-Fa-f]{{6}}(")')
    return lambda xml: pattern.sub(lambda m: m.group(1) + color + m.group(2), xml, count=1)


def recolor_pptx(source: bytes, config: TemplateConfig, color: str) -> bytes:
    new = shades_for(color)
    targets = {s.number for s in config.slides if s.recolor}
    replace_slide = _slide_replacer(config.base_colors, new)
    replace_theme = _theme_replacer(config.theme_accent, new.main) if config.theme_accent else None

    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source)) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        # [Content_Types].xml first (safest for Office), everything else in source order
        items = sorted(zin.infolist(), key=lambda i: i.filename != "[Content_Types].xml")
        for item in items:
            data = zin.read(item.filename)
            match = SLIDE_RE.match(item.filename)
            if match and int(match.group(1)) in targets:
                data = replace_slide(data.decode("utf-8")).encode("utf-8")
            elif replace_theme and item.filename == THEME_PATH:
                data = replace_theme(data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data, compress_type=zipfile.ZIP_DEFLATED)
    return out.getvalue()

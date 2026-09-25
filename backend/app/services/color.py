"""Shade generation. Keep in sync with frontend/src/lib/color.ts."""
import colorsys

from app.schemas.template import ColorSet

DARK_RATIO = 0.74
BRIGHT_RATIO = 1.33


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    return "".join(f"{round(max(0, min(1, c)) * 255):02X}" for c in (r, g, b))


def shades_for(hex_color: str) -> ColorSet:
    """Return dark/main/bright shades using the same ratios as the original red template."""
    r, g, b = _hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    dark = colorsys.hls_to_rgb(h, l * DARK_RATIO, s)
    bright = colorsys.hls_to_rgb(h, min(l * BRIGHT_RATIO, l + (1 - l) * 0.5), s)
    return ColorSet(dark=_rgb_to_hex(*dark), main=hex_color.lstrip("#").upper(), bright=_rgb_to_hex(*bright))

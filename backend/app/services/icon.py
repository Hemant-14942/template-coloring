"""Fit an uploaded icon into the template picture without storing the upload."""
import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.exceptions import IconError

ICON_MEDIA = "ppt/media/image2.png"
MAX_ICON_BYTES = 5 * 1024 * 1024


def icon_slot(source: bytes) -> tuple[tuple[int, int], tuple[int, int, int, int]]:
    """Return the original canvas size and the rectangle the pencil artwork actually fills."""
    import zipfile

    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        try:
            data = archive.read(ICON_MEDIA)
        except KeyError as exc:
            raise IconError("This template has no replaceable heading icon.") from exc
    with Image.open(io.BytesIO(data)) as image:
        image = image.convert("RGBA")
        box = image.getbbox() or (0, 0, image.width, image.height)
        return image.size, box


def prepare_icon(raw: bytes, canvas: tuple[int, int], slot: tuple[int, int, int, int]) -> bytes:
    """Place the upload in the pencil's visible area, not in the empty margin around it."""
    if not raw:
        raise IconError("Choose an image file.")
    if len(raw) > MAX_ICON_BYTES:
        raise IconError("Icon must be 5 MB or smaller.")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image).convert("RGBA")
            content = image.crop(image.getbbox() or (0, 0, image.width, image.height))
            left, top, right, bottom = slot
            scale = min((right - left) / content.width, (bottom - top) / content.height)
            content = content.resize(
                (max(1, round(content.width * scale)), max(1, round(content.height * scale))),
                Image.Resampling.LANCZOS,
            )
            fitted = Image.new("RGBA", canvas, (0, 0, 0, 0))
            x = left + (right - left - content.width) // 2
            y = top + (bottom - top - content.height) // 2
            fitted.paste(content, (x, y), content)
            out = io.BytesIO()
            fitted.save(out, format="PNG")
            return out.getvalue()
    except (UnidentifiedImageError, OSError) as exc:
        raise IconError("Icon must be a PNG, JPG, or WebP image.") from exc

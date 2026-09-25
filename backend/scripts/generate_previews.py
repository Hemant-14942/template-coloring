"""
Build preview images and recolor masks for a template folder.

Usage (needs LibreOffice + poppler-utils installed):
    python scripts/generate_previews.py assets/templates/red-final

How it works: renders the template once as-is and once with the base colors
swapped to green. Pixels that differ are exactly the recolorable areas; those
become the mask the frontend uses for the live preview.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image


def swap_to_marker(src: Path, dst: Path, base: dict[str, str]) -> None:
    marker = {v.upper(): "00" + v[:2] + "00" for v in base.values()}  # red channel -> green channel
    pattern = re.compile(r'(<a:srgbClr val=")(' + "|".join(marker) + r')(")', re.IGNORECASE)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("ppt/slides/slide") and item.filename.endswith(".xml"):
                data = pattern.sub(lambda m: m.group(1) + marker[m.group(2).upper()] + m.group(3),
                                   data.decode()).encode()
            zout.writestr(item, data)


def render(pptx: Path, out_dir: Path, prefix: str, width: int) -> list[Path]:
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
                   check=True, capture_output=True)
    pdf = out_dir / (pptx.stem + ".pdf")
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", str(width), "-scale-to-y", "-1", str(pdf),
                    str(out_dir / prefix)], check=True)
    return sorted(out_dir.glob(f"{prefix}-*.png"))


def main(folder: Path, width: int = 1280) -> None:
    config = json.loads((folder / "template.json").read_text())
    src = folder / config["file"]
    (folder / "previews").mkdir(exist_ok=True)
    (folder / "masks").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original = tmp_path / "original.pptx"
        shutil.copy(src, original)
        marker = tmp_path / "marker.pptx"
        swap_to_marker(src, marker, config["base_colors"])
        a_pages = render(original, tmp_path, "a", width)
        b_pages = render(marker, tmp_path, "b", width)
        for i, (a_path, b_path) in enumerate(zip(a_pages, b_pages), start=1):
            a = Image.open(a_path).convert("RGB")
            b = Image.open(b_path).convert("RGB")
            diff = np.abs(np.asarray(a, dtype=int) - np.asarray(b, dtype=int)).sum(axis=2) > 24
            a.save(folder / "previews" / f"slide-{i:02d}.jpg", quality=88)
            Image.fromarray((diff * 255).astype("uint8")).convert("1").save(
                folder / "masks" / f"slide-{i:02d}.png", optimize=True)
            print(f"slide {i}: {int(diff.sum())} recolorable pixels")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/generate_previews.py <template-folder>")
    main(Path(sys.argv[1]))

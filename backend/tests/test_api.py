import io
import re
import zipfile

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_template_detail_lists_12_slides():
    res = client.get("/api/v1/templates/red-final")
    assert res.status_code == 200
    body = res.json()
    assert len(body["slides"]) == 12
    assert client.get(body["slides"][0]["preview_url"]).status_code == 200
    assert client.get(body["slides"][0]["mask_url"]).status_code == 200


def test_unknown_template_404():
    assert client.get("/api/v1/templates/nope").status_code == 404


def test_invalid_color_422():
    assert client.post("/api/v1/templates/red-final/recolor", json={"color": "blue"}).status_code == 422
    assert client.post("/api/v1/templates/red-final/recolor", json={"color": "#1F4E9A", "background": "blue"}).status_code == 422


def test_background_is_written_on_each_slide_without_changing_theme():
    res = client.post("/api/v1/templates/red-final/recolor", json={"color": "#1F4E9A", "background": "#0E1628"})
    assert res.status_code == 200
    assert "red-final-1F4E9A-bg0E1628.pptx" in res.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        theme = z.read("ppt/theme/theme1.xml").decode()
        assert '<a:dk1><a:srgbClr val="000000"/></a:dk1>' in theme
        assert '<a:accent2><a:srgbClr val="E97132"/></a:accent2>' in theme
        assert re.search(r'<a:accent1>\s*<a:srgbClr val="1F4E9A"', theme)
        slides = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
        assert slides
        for name in slides:
            xml = z.read(name).decode()
            bg = re.search(r"<p:bg>.*?</p:bg>", xml)
            assert bg and 'srgbClr val="0E1628"' in bg.group(0), name
            assert "dk1" not in bg.group(0), name


def test_uploaded_icon_replaces_heading_icon_only_in_download():
    from pathlib import Path

    from PIL import Image

    from app.core.config import get_settings

    original_path = Path(get_settings().templates_dir) / "red-final" / "template.pptx"
    before = original_path.read_bytes()
    upload = io.BytesIO()
    Image.new("RGBA", (80, 80), (0, 128, 255, 255)).save(upload, format="PNG")
    res = client.post(
        "/api/v1/templates/red-final/recolor",
        data={"color": "#1F4E9A", "background": "#000000"},
        files={"icon": ("mark.png", upload.getvalue(), "image/png")},
    )
    assert res.status_code == 200
    assert original_path.read_bytes() == before
    with zipfile.ZipFile(io.BytesIO(before)) as original, zipfile.ZipFile(io.BytesIO(res.content)) as generated:
        assert generated.read("ppt/media/image2.png") != original.read("ppt/media/image2.png")
        assert generated.read("ppt/media/image1.png") == original.read("ppt/media/image1.png")
        assert generated.read("ppt/media/image3.png") == original.read("ppt/media/image3.png")
        with Image.open(io.BytesIO(generated.read("ppt/media/image2.png"))) as icon:
            with Image.open(io.BytesIO(original.read("ppt/media/image2.png"))) as source:
                assert icon.size == source.size
                source_box = source.convert("RGBA").getbbox()
                icon_box = icon.convert("RGBA").getbbox()
                assert source_box and icon_box
                source_height = source_box[3] - source_box[1]
                icon_height = icon_box[3] - icon_box[1]
                assert icon_height >= source_height * 0.9


def test_invalid_icon_422():
    res = client.post(
        "/api/v1/templates/red-final/recolor",
        data={"color": "#1F4E9A"},
        files={"icon": ("notes.txt", b"not an image", "text/plain")},
    )
    assert res.status_code == 422


def test_recolor_replaces_all_reds_and_theme():
    res = client.post("/api/v1/templates/red-final/recolor", json={"color": "#1F4E9A"})
    assert res.status_code == 200
    assert "red-final-1F4E9A.pptx" in res.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        assert z.namelist()[0] == "[Content_Types].xml"
        slides = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
        for name in slides:
            xml = z.read(name).decode()
            assert not re.search(r'srgbClr val="(8E0000|C00000|FF0000)"', xml, re.I), name
        assert 'srgbClr val="1F4E9A"' in z.read("ppt/slides/slide1.xml").decode()
        assert re.search(r'<a:accent1>\s*<a:srgbClr val="1F4E9A"', z.read("ppt/theme/theme1.xml").decode())

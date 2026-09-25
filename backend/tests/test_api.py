import io
import re
import zipfile

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_template_detail_lists_13_slides():
    res = client.get("/api/v1/templates/red-final")
    assert res.status_code == 200
    body = res.json()
    assert len(body["slides"]) == 13
    assert client.get(body["slides"][0]["preview_url"]).status_code == 200
    assert client.get(body["slides"][0]["mask_url"]).status_code == 200


def test_unknown_template_404():
    assert client.get("/api/v1/templates/nope").status_code == 404


def test_invalid_color_422():
    assert client.post("/api/v1/templates/red-final/recolor", json={"color": "blue"}).status_code == 422


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

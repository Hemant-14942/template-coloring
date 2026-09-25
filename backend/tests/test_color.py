from app.services.color import shades_for


def test_original_red_reproduces_template_shades():
    s = shades_for("#C00000")
    assert (s.dark, s.main, s.bright) == ("8E0000", "C00000", "FF0000")


def test_accepts_without_hash_and_lowercase():
    assert shades_for("1f4e9a").main == "1F4E9A"

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_graphics_demo_keeps_graphics_mode_active():
    source = (ROOT / "examples/graphics/graphics_demo.c").read_text(encoding="utf-8")
    assert "InitGraphics();" in source
    assert "DrawLine(" in source
    code = source.split("/*", 1)[0]
    assert "DoneGraphics(" not in code


def test_text_demo_explicitly_leaves_graphics_mode():
    source = (ROOT / "examples/graphics/graphics_demo_text.c").read_text(encoding="utf-8")
    assert "DoneGraphics(tmUpperLower);" in source
    assert source.index("DoneGraphics(tmUpperLower);") < source.index("printf(")


def test_c_and_pascal_color_names_match():
    c_header = (ROOT / "c64c/include/graphics.h").read_text(encoding="utf-8")
    pascal = (ROOT / "c64pascal/units/System/Graphics.pas").read_text(encoding="utf-8")
    for name in (
        "ColorBlack", "ColorWhite", "ColorRed", "ColorCyan",
        "ColorPurple", "ColorGreen", "ColorBlue", "ColorYellow",
        "ColorOrange", "ColorBrown", "ColorLightRed", "ColorDarkGray",
        "ColorGray", "ColorLightGreen", "ColorLightBlue", "ColorLightGray",
    ):
        assert name in c_header
        assert name in pascal

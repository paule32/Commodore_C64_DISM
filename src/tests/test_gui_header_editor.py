from pathlib import Path
import re


def test_header_is_an_internal_editor_extension():
    source = (Path(__file__).parents[1] / "d64_dism.py").read_text(encoding="utf-8")
    block = re.search(r"EDITOR_EXTENSIONS\s*=\s*\{(?P<body>.*?)\n\s*\}", source, re.S)
    assert block is not None
    assert '".h"' in block.group("body")


def test_c_filter_contains_headers():
    source = (Path(__file__).parents[1] / "d64_dism.py").read_text(encoding="utf-8")
    assert '"C": {".c", ".h"}' in source


def test_double_click_uses_case_insensitive_suffix():
    source = (Path(__file__).parents[1] / "d64_dism.py").read_text(encoding="utf-8")
    assert "path.suffix.lower() in self.EDITOR_EXTENSIONS" in source

"""Stage 528: frozen native watchdog path resolution and source build contract."""
from __future__ import annotations

import ast
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from watchdog import native_watchdog as nw


@pytest.mark.parametrize("arch", ["x86", "x64"])
def test_frozen_bundle_path(monkeypatch, tmp_path, arch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    expected = tmp_path / "watchdog" / "bin" / f"d64_watchdog_{arch}.exe"
    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.write_bytes(b"MZ fake test binary")
    assert nw.bundled_executable(arch) == expected


def test_frozen_copy_reusable_and_content_addressed(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    bundle = tmp_path / "d64_watchdog_x64.exe"
    bundle.write_bytes(b"MZ test version 1")
    first = nw._onefile_watchdog_copy(bundle, "x64")
    assert first.is_file()
    assert first.read_bytes() == bundle.read_bytes()
    assert nw._onefile_watchdog_copy(bundle, "x64") == first
    bundle.write_bytes(b"MZ test version 2")
    newer = nw._onefile_watchdog_copy(bundle, "x64")
    assert newer != first
    assert first.read_bytes() == b"MZ test version 1"
    assert newer.read_bytes() == b"MZ test version 2"


def test_watchdog_is_early_in_main():
    source = (SRC / "__main__.py").read_text(encoding="utf-8")
    assert source.index("start_watchdog(app_name = APP_NAME )") < source.index("from PyQt5.QtCore")


def test_root_spec_onefile_entry_and_binary():
    source = (ROOT / "d64_dism.spec").read_text(encoding="utf-8")
    ast.parse(source)
    assert 'SRC / "__main__.py"' in source
    assert '"watchdog/bin"' in source
    assert "a.binaries, a.datas" in source
    assert "COLLECT(" not in source


def test_early_watchdog_selftest():
    source = (SRC / "__main__.py").read_text(encoding="utf-8")
    assert '"--watchdog-self-test"' in source
    assert "os._exit(33)" in source

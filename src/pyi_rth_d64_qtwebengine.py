# ---------------------------------------------------------------------------
# PyInstaller runtime hook for d64_dism / QtWebEngine (Windows)
# Must run before __main__.py imports PyQt5.
# ---------------------------------------------------------------------------
from __future__ import annotations

import os
import sys
from pathlib import Path


def _roots():
    result = []
    bundle = getattr(sys, "_MEIPASS", "")
    if bundle:
        result.append(Path(bundle))
    try:
        result.append(Path(sys.executable).resolve().parent)
    except Exception:
        pass
    return result


def _find_file(name: str):
    for root in _roots():
        if not root.exists():
            continue
        try:
            for path in root.rglob(name):
                if path.is_file():
                    return path
        except OSError:
            continue
    return None


def _find_dir(name: str):
    for root in _roots():
        if not root.exists():
            continue
        try:
            for path in root.rglob(name):
                if path.is_dir():
                    return path
        except OSError:
            continue
    return None


process = _find_file("QtWebEngineProcess.exe")
resources_pak = _find_file("qtwebengine_resources.pak")
locales = _find_dir("qtwebengine_locales")

if process is not None:
    os.environ["QTWEBENGINEPROCESS_PATH"] = str(process)
if resources_pak is not None:
    os.environ["QTWEBENGINE_RESOURCES_PATH"] = str(resources_pak.parent)
if locales is not None:
    os.environ["QTWEBENGINE_LOCALES_PATH"] = str(locales)

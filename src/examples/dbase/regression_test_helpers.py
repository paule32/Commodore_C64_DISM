"""Shared regression-test helpers kept outside the numbered Stage history."""
from __future__ import annotations
from pathlib import Path
import ast
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field, replace
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
import textwrap
import zlib
from typing import *

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


def pe_namespace():
    start = SOURCE.index("IMAGE_FILE_MACHINE_I386 = 0x014C")
    end = SOURCE.index(
        "# ---------------------------------------------------------------------------\n"
        "# Windows-Grafik-ABI.",
        start,
    )
    prefix = "from __future__ import annotations\n"
    ns = {
        "os": os, "re": re, "struct": struct, "ctypes": ctypes,
        "ast": ast, "json": json, "math": math, "hashlib": hashlib,
        "shutil": shutil, "subprocess": subprocess, "tempfile": tempfile,
        "_d64info_zlib": zlib, "Path": Path, "dataclass": dataclass,
        "field": field, "replace": replace, "wintypes": wintypes,
        "Optional": Optional, "Sequence": Sequence, "Dict": Dict,
        "Tuple": Tuple, "List": List, "Set": Set,
    }
    exec(prefix + SOURCE[start:end], ns)
    ns["_pe32_mszip_compress_buffer"] = lambda data: zlib.compress(bytes(data), 9)
    ns["PE32_TEXT_COMPRESSION_MSZIP_DEFAULT"] = True
    ns["PE64_TEXT_COMPRESSION_MSZIP_DEFAULT"] = True
    ns["PE32_PACK_COMPACTOR_DEFAULT"] = False
    return ns


def pe_layout(image: bytes):
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    file_header = pe + 4
    machine, count = struct.unpack_from("<HH", image, file_header)
    opt_size = struct.unpack_from("<H", image, file_header + 16)[0]
    opt = file_header + 20
    table = opt + opt_size
    sections = {}
    for i in range(count):
        h = table + i * 40
        name = image[h:h+8].split(b"\0", 1)[0].decode("ascii")
        vs, rva, rs, rp = struct.unpack_from("<IIII", image, h + 8)
        sections[name] = {
            "virtual_size": vs, "rva": rva,
            "raw_size": rs, "raw_ptr": rp,
            "raw": image[rp:rp+rs] if rs else b"",
        }
    return machine, opt, sections


def fallback_function():
    tree = ast.parse(SOURCE)
    node = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
        and n.name == "_compile_dbase_wfm_fallback"
    )
    source = textwrap.dedent(ast.get_source_segment(SOURCE, node))

    class AssemblerError(Exception):
        pass

    def _normalize_project_windows_debug_theme(value):
        return value

    namespace = {
        "re": re,
        "struct": struct,
        "replace": replace,
        "AssemblerError": AssemblerError,
        "_normalize_project_windows_debug_theme": _normalize_project_windows_debug_theme,
    }
    exec(source, namespace)
    return namespace["_compile_dbase_wfm_fallback"]


class DummyExplorer:
    @staticmethod
    def _dbase_wfm_prop(props, name, default=None):
        for key, value in dict(props or {}).items():
            if str(key).casefold() == str(name).casefold():
                return value
        return default

    @staticmethod
    def _dbase_wfm_int(props, name, default=0):
        value = DummyExplorer._dbase_wfm_prop(props, name, default)
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return int(default)

    @staticmethod
    def _dbase_wfm_asm_bytes(value):
        if value is None:
            return b""
        if isinstance(value, bytes):
            return value
        if isinstance(value, bytearray):
            return bytes(value)
        return str(value).encode("utf-8")

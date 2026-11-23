# -*- coding: utf-8 -*-
"""Stage 676: the IDE button installs the fully merged native runtime.

A console-only COFF DLL would overwrite the Pascal/JitObject services and is
therefore never constructed by this path.
"""
from __future__ import annotations
from pathlib import Path
from .native_runtime_deploy import deploy_runtime


def create_runtime_dll(target: str, directory: Path, *, get_exports,
                       assemble32=None, coff32=None, link32=None,
                       assemble64=None, coff64=None, link64=None,
                       pack_dll=False, compressor=None) -> Path:
    return deploy_runtime(Path(directory) / 'App.exe', target,
                          get_exports=get_exports)

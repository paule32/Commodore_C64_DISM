# -*- coding: utf-8 -*-
"""Stage 447: manually build the native dBASE console DLL for PE32 or PE32+.

Uses the same in-process COFF assembler/PE linker as the automatic runtime
builder, but always regenerates the requested DLL rather than copying a
packaged binary. The result is validated before replacing an existing file.
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from .console_runtime import DLL_NAME, EXPORTS, build_dll
from .pe_dll_pack import replace_verified_runtime
from .pe_dll_payload import is_payload_packed


def create_runtime_dll(target: str, directory: Path, *, get_exports,
                       assemble32, coff32, link32, assemble64, coff64, link64,
                       pack_dll: bool = False, compressor=None) -> Path:
    """Rebuild a Windows DLL to *directory*, checking architecture and exports.

    Existing output is only replaced after a successful build+validation.
    No external compilers or build tools are launched.
    """
    if target not in ("pe32", "pe64"):
        raise ValueError(f"Unbekannte Windows-Architektur: {target}")
    if not str(directory or "").strip():
        raise ValueError("Bitte ein Ausgabe-Verzeichnis auswählen.")
    target_dir = Path(directory).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    if not target_dir.is_dir():
        raise NotADirectoryError(str(target_dir))
    expected_machine = 0x014c if target == "pe32" else 0x8664
    destination = target_dir / DLL_NAME
    # Use a staging directory inside the same volume for atomic os.replace.
    with TemporaryDirectory(prefix=".dbase-runtime-", dir=str(target_dir)) as tempdir:
        candidate = Path(tempdir) / DLL_NAME
        build_dll(target, candidate,
                  assemble32=assemble32, coff32=coff32, link32=link32,
                  assemble64=assemble64, coff64=coff64, link64=link64,
                  pack_dll=pack_dll, compressor=compressor)
        exports = get_exports(candidate, expected_machine)
        if not set(EXPORTS).issubset(set(exports)):
            raise ValueError(f"Ungültige {target}-DLL: Architektur oder Exporte stimmen nicht")
        if not candidate.is_file() or candidate.stat().st_size == 0:
            raise ValueError("Die erzeugte DLL ist leer oder fehlt")
        if pack_dll and not is_payload_packed(candidate):
            raise ValueError('D64Z-Payload fehlt in der erzeugten Runtime-DLL')
        if not set(EXPORTS).issubset(set(get_exports(candidate, expected_machine))):
            raise ValueError('Das Runtime-Packing hat die DLL-Exporte verändert')
        replace_verified_runtime(candidate, destination, pack_dll=False)
    return destination

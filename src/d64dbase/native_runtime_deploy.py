# -*- coding: utf-8 -*-
"""Stage 678: deploy the Qt5 DLL with embedded native JIT/dBASE runtime.

The old standalone runtimes are not copied.  All symbols must be exported
from the architecture-matched Qt5 DLL built with the statically linked core.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

DLL_NAME = 'libd64_qt5.dll'
DBASE_EXPORTS = (
    'DBaseConsoleEnsure', 'DBaseConsoleWrite', 'DBaseConsoleShutdown',
    'DBaseConsoleSetTitle', 'DBaseCharIsLowerCP1252', 'DBaseCharIsUpperCP1252',
    'DBaseCharIsLowerUtf8', 'DBaseCharIsUpperUtf8', 'DBaseStringLengthN',
    'DBaseWfmClassifyType', 'DBaseWfmFormatValue',
)
# These symbols must remain present when deploying a merged library; do not
# accidentally overwrite an existing Pascal/TObject runtime with the old,
# standalone 11-export assembly DLL.
EXISTING_EXPORTS = ('jit_object_instance_new', 'jit_get_virtual_object',
                    '_jit_malloc', '_jit_free', 'jit_pas_inttostr',
                    'jit_pas_strtoint', 'jit_default_tobject_vmt_abi')
REQUIRED_EXPORTS = frozenset(DBASE_EXPORTS + EXISTING_EXPORTS)


def candidates(target: str, *, package_root: Path | None = None):
    root = Path(package_root) if package_root is not None else Path(__file__).resolve().parents[1]
    arch = 'win32' if target == 'pe32' else 'win64'
    for path in (
        root / 'd64qt5' / 'release' / DLL_NAME,
        root / 'd64qt5' / 'debug' / DLL_NAME,
        root / 'bin' / target / DLL_NAME,

        root / DLL_NAME,
    ):
        yield path


def deploy_runtime(output_path: Path, target: str, *, get_exports,
                   package_root: Path | None = None, **_legacy_build_args) -> Path:
    """Install a native PE32/PE32+ DLL, rejecting wrong ABI and architecture."""
    if target not in ('pe32','pe64'):
        raise ValueError('Unbekanntes dBASE-Runtimeziel: '+str(target))
    expected_machine = 0x014c if target=='pe32' else 0x8664
    destination = Path(output_path).resolve().parent / DLL_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)

    def valid(p: Path) -> bool:
        if not p.is_file(): return False
        try:
            return REQUIRED_EXPORTS.issubset(set(get_exports(p,expected_machine)))
        except (OSError, ValueError, TypeError):
            return False

    # Prefer an explicitly rebuilt Qt5 DLL over stale executable neighbors.
    # A previous Qt5 DLL without the embedded JitObject exports is rejected.
    packaged = next((p for p in candidates(target,package_root=package_root)
                     if valid(p)),None)
    if packaged is None:
        if valid(destination):
            return destination
        raise FileNotFoundError(
            f'Keine gültige {target}-Datei {DLL_NAME} mit dBASE-/JitObject-Exports gefunden. '
            'Erstelle die Qt5-Runtime mit der passenden MinGW-Toolchain '
            '(PE32: d64qt5/build_d64qt5_mingw32.bat) und stelle sie unter '
            f'd64qt5/release/{DLL_NAME} bereit. '
            'Weder c64_dbase_runtime.dll noch libd64_runtime.dll sind Ersatz.'
        )
    if packaged.resolve()==destination.resolve():
        return destination
    if valid(destination) and destination.read_bytes()==packaged.read_bytes():
        return destination
    with TemporaryDirectory(prefix='.d64-native-runtime-',dir=str(destination.parent)) as temp:
        staged=Path(temp)/DLL_NAME
        shutil.copy2(packaged,staged)
        if not valid(staged):
            raise ValueError('Staged native Runtime verlor Exporte oder Architektur')
        os.replace(staged,destination)
    return destination

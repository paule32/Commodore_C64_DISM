"""Stage 583: Check whether a built PE32 runtime DLL has the cookie exports.

Usage (from project root):
    python runtime/pascal/verify_cookie_runtime.py runtime/win32/libd64_runtime.dll
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from pascal_console_dependencies import inspect_pe, PEInspectionError

REQUIRED_EXPORTS = {
    'jit_pas_cookie_initialize32',
    'jit_pas_cookie_failure32',
}
PE32_MACHINE = 0x014C


def verify(path: str | Path) -> tuple[bool, str]:
    file_path = Path(path)
    if not file_path.is_file():
        return False, f'DLL nicht gefunden: {file_path}'
    try:
        machine, _imports, exports = inspect_pe(file_path)
    except (OSError, PEInspectionError) as exc:
        return False, f'Ungueltige DLL: {exc}'
    if machine != PE32_MACHINE:
        return False, f'Falsche Architektur: 0x{machine:04X} (erwartet PE32 0x014C)'
    missing = REQUIRED_EXPORTS - exports
    if missing:
        return False, ('DLL zu alt / erforderliche Exporte fehlen: '
                       + ', '.join(sorted(missing)))
    return True, 'DLL PE32 und beide Stack-Cookie-Exporte vorhanden'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Aufruf: python runtime/pascal/verify_cookie_runtime.py <dll-pfad>')
        raise SystemExit(2)
    success, msg = verify(sys.argv[1])
    print(msg)
    raise SystemExit(0 if success else 1)

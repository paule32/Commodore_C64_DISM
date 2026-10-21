"""Stage 477: typed Win32/Win64 DLL declarations shared by PRG and WFM.

Prototype syntax::
    extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, ;
        LPCSTR, CINT) shell32 ;
        from "ShellExecuteA"

The preprocessor has already expanded ``#define shell32 "shell32.dll"``.
No DLL is loaded during compilation; imports are emitted into the PE image.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Tuple

from .ffi_types import FFI_TYPES, WinAPIType, ffi_type_info, ffi_return_instructions


@dataclass(frozen=True)
class DBaseFFIPrototype:
    name: str
    return_type: str
    argument_types: Tuple[str, ...]
    dll: str
    entry: str
    line: int

    @property
    def label(self) -> str:
        return '__dbase_ffi_' + self.name.casefold()

    @property
    def import_line(self) -> str:
        return f'import {self.label}, "{self.dll}", "{self.entry}"'


def extract_ffi_prototypes(source: str, *, filename: str = '<dBase>'):
    """Strip extern prototypes without changing source line numbers.

    Returns ``(masked_source, prototypes)``. ValueError messages include the
    offending source position and are converted to DBaseCompilerError upstream.
    """
    lines = source.splitlines(keepends=True)
    prototypes = []
    seen = set()
    i = 0
    while i < len(lines):
        start = i
        if not re.match(r'^\s*extern\s+', lines[i], re.I):
            i += 1
            continue
        # Prototypes may span multiple lines via a semicolon after the last
        # argument or after the DLL identifier. Stop at the `from` clause.
        text = lines[i].strip()
        while not re.search(r'\bfrom\s+["\']', text, re.I) and i + 1 < len(lines):
            i += 1
            text += ' ' + lines[i].strip()
            if i - start > 16:
                break
        # The semicolon after an argument or DLL name is a declaration-line
        # continuation marker, not part of an argument or a DLL filename.
        text = re.sub(r';\s*', ' ', text).strip()
        match = re.fullmatch(
            r'extern\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*'
            r'\(([^()]*)\)\s+("[^"\r\n]+"|[A-Za-z_]\w*)\s+'
            r'from\s+"([^"\r\n]+)"\s*\.?\s*', text, re.I,
        )
        if match is None:
            raise ValueError(f'{filename}:{start + 1}: Ungueltige extern-DLL-Deklaration: {text}')
        result_type, name, raw_args, raw_dll, entry = match.groups()
        result_type = result_type.upper()
        argument_types = tuple(s.strip().upper() for s in raw_args.split(',') if s.strip())
        if argument_types in (('CVOID',), ('VOID',)):
            argument_types = ()  # f(void): nullary function
        if result_type not in FFI_TYPES:
            raise ValueError(f'{filename}:{start + 1}: Unbekannter DLL-Rueckgabetyp {result_type}.')
        for arg in argument_types:
            if arg not in FFI_TYPES or arg == 'CVOID':
                raise ValueError(f'{filename}:{start + 1}: Ungueltiger DLL-Parametertyp {arg}.')
        dll = raw_dll.strip('"')
        if not dll.casefold().endswith('.dll') or any(c in dll for c in '\\/:'):
            raise ValueError(f'{filename}:{start + 1}: DLL erwartet einen Dateinamen wie "shell32.dll": {dll}.')
        if not re.fullmatch(r'[#A-Za-z_][\w@#]*', entry):
            raise ValueError(f'{filename}:{start + 1}: Ungueltiger DLL-Exportname {entry}.')
        if name.casefold() in seen:
            raise ValueError(f'{filename}:{start + 1}: DLL-Prototyp {name} mehrfach deklariert.')
        seen.add(name.casefold())
        prototypes.append(DBaseFFIPrototype(name, result_type, argument_types, dll, entry, start + 1))
        for line_idx in range(start, i + 1):
            eol = '\r\n' if lines[line_idx].endswith('\r\n') else '\n' if lines[line_idx].endswith('\n') else ''
            lines[line_idx] = eol
        i += 1
    return ''.join(lines), tuple(prototypes)

"""Stage 552: verify/deploy the console DLL used by generated Pascal PE images.

PE import tables are read directly, without pefile and without executing DLLs.
The original import manifest covers compressed executables whose on-disk PE
import directory contains only their unpacker/loader's Windows dependencies.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Iterable

CONSOLE_DLL = 'libd64_console.dll'
MACHINE_I386 = 0x14c
MACHINE_AMD64 = 0x8664


class PEInspectionError(ValueError):
    pass


def _pe_tables(path: str | Path):
    content = Path(path).read_bytes()

    def uint16(offset):
        if offset < 0 or offset + 2 > len(content):
            raise PEInspectionError('Truncated PE16')
        return struct.unpack_from('<H', content, offset)[0]

    def uint32(offset):
        if offset < 0 or offset + 4 > len(content):
            raise PEInspectionError('Truncated PE32')
        return struct.unpack_from('<I', content, offset)[0]

    if len(content) < 0x40 or content[:2] != b'MZ':
        raise PEInspectionError('No MZ header')
    pe = uint32(0x3c)
    if pe + 24 > len(content) or content[pe:pe + 4] != b'PE\0\0':
        raise PEInspectionError('No PE signature')
    coff = pe + 4
    machine = uint16(coff)
    sections_count = uint16(coff + 2)
    optional_size = uint16(coff + 16)
    optional = coff + 20
    magic = uint16(optional)
    if magic == 0x10b:
        data_directories = optional + 96
    elif magic == 0x20b:
        data_directories = optional + 112
    else:
        raise PEInspectionError('Unsupported PE optional header')
    if optional + optional_size > len(content):
        raise PEInspectionError('Truncated optional header')
    directories = []
    for index in (0, 1):  # export/import directory
        start = data_directories + index * 8
        if start + 8 > optional + optional_size:
            directories.append((0, 0))
        else:
            directories.append((uint32(start), uint32(start + 4)))
    table_offset = optional + optional_size
    sections = []
    for idx in range(sections_count):
        off = table_offset + idx * 40
        if off + 40 > len(content):
            raise PEInspectionError('Truncated section table')
        vsize = uint32(off + 8)
        rva = uint32(off + 12)
        rsize = uint32(off + 16)
        raw = uint32(off + 20)
        sections.append((rva, max(vsize, rsize), raw, rsize))

    def at_rva(rva, size=1):
        if rva <= 0:
            raise PEInspectionError('Missing RVA')
        for base, virtual_size, raw, raw_size in sections:
            if base <= rva and rva + size <= base + virtual_size:
                delta = rva - base
                if delta + size > raw_size or raw + delta + size > len(content):
                    raise PEInspectionError('RVA outside PE file')
                return raw + delta
        raise PEInspectionError('Unmapped PE RVA')

    def read_cstr(rva):
        start = at_rva(rva)
        end = content.find(b'\0', start, min(len(content), start + 8192))
        if end < 0:
            raise PEInspectionError('Unterminated PE string')
        return content[start:end].decode('ascii', errors='replace')

    return content, machine, directories, at_rva, read_cstr


def inspect_pe(path: str | Path) -> tuple[int, dict[str, set[str]], set[str]]:
    """Return (PE machine, imported DLL->symbol names, exported symbol names)."""
    data, machine, directories, at_rva, read_cstr = _pe_tables(path)
    imports: dict[str, set[str]] = {}
    export_names: set[str] = set()
    export_rva, export_size = directories[0]
    if export_rva and export_size:
        exp = at_rva(export_rva, 40)
        count = struct.unpack_from('<I', data, exp + 24)[0]
        names_rva = struct.unpack_from('<I', data, exp + 32)[0]
        if count > 100000:
            raise PEInspectionError('Invalid PE export name count')
        for index in range(count):
            name_offset = at_rva(names_rva + index * 4, 4)
            export_names.add(read_cstr(struct.unpack_from('<I', data, name_offset)[0]))
    import_rva, import_size = directories[1]
    if import_rva and import_size:
        descriptor_size = 20
        for index in range(min(10000, import_size // descriptor_size + 1)):
            d = at_rva(import_rva + index * descriptor_size, descriptor_size)
            lookup, _time, _forward, name_rva, first_thunk = struct.unpack_from('<IIIII', data, d)
            if not lookup and not name_rva and not first_thunk:
                break
            dll_name = read_cstr(name_rva).casefold()
            names = imports.setdefault(dll_name, set())
            thunk_rva = lookup or first_thunk
            stride = 8 if machine == MACHINE_AMD64 else 4
            flags = 0x8000000000000000 if stride == 8 else 0x80000000
            fmt = '<Q' if stride == 8 else '<I'
            for t in range(100000):
                th = at_rva(thunk_rva + t * stride, stride)
                value = struct.unpack_from(fmt, data, th)[0]
                if not value:
                    break
                if not value & flags:
                    names.add(read_cstr(value + 2))
            else:
                raise PEInspectionError('Unterminated PE import thunk array')
        else:
            raise PEInspectionError('Unterminated PE import table')
    return machine, imports, export_names


def manifest_dlls_and_console_symbols(manifest: object) -> tuple[set[str], set[str]]:
    """Inspect the Stage-541 link manifest, not the packed EXE import table."""
    dlls: set[str] = set()
    console_symbols: set[str] = set()
    if not isinstance(manifest, dict):
        return dlls, console_symbols
    records = manifest.get('imports', ())
    if not isinstance(records, list):
        return dlls, console_symbols
    for entry in records:
        if not isinstance(entry, dict):
            continue
        dll = str(entry.get('dll', '')).casefold()
        member = str(entry.get('member', ''))
        if not dll:
            continue
        dlls.add(dll)
        if dll == CONSOLE_DLL:
            console_symbols.add(member)
    return dlls, console_symbols


def required_console_exports(
    output_path: str | Path,
    manifest: object,
    source_includes_console: bool = False,
) -> set[str]:
    """Gather required exports, including imports of adjacent Pascal DLLs.

    We cannot inspect the packed EXE's import directory for this: the loader
    replaces it with kernel32/cabinet imports, so use the link manifest first.
    """
    output_path = Path(output_path)
    dlls, symbols = manifest_dlls_and_console_symbols(manifest)
    if source_includes_console and not symbols:
        # A legacy build without the link manifest still requires the DLL.
        symbols.add('d64_console_init')
    seen: set[str] = set()
    for dll in dlls:
        if dll in seen or dll == CONSOLE_DLL or dll in {'kernel32.dll', 'user32.dll'}:
            continue
        seen.add(dll)
        dependency = output_path.parent / dll
        if not dependency.is_file():
            # Win file names are case insensitive; tests also run on Linux.
            dependency = next((p for p in output_path.parent.iterdir()
                               if p.name.casefold() == dll and p.is_file()), dependency)
        if dependency.is_file():
            try:
                _machine, dll_imports, _exports = inspect_pe(dependency)
            except (OSError, PEInspectionError):
                continue
            symbols.update(dll_imports.get(CONSOLE_DLL, ()))
    return symbols


def validate_console_library(path: str | Path, machine: int,
                             required: Iterable[str]) -> str | None:
    """Return the diagnostic error, or None when the DLL is usable."""
    try:
        actual_machine, _imports, exports = inspect_pe(path)
    except (OSError, PEInspectionError) as exc:
        return f'{Path(path).name}: ungültige DLL: {exc}'
    if actual_machine != machine:
        return (f'{Path(path).name}: Architektur 0x{actual_machine:04X}, '
                f'erwartet 0x{machine:04X}')
    missing = sorted(set(required) - exports)
    if missing:
        return f'{Path(path).name}: fehlende Exporte: {", ".join(missing)}'
    return None


def diagnose_package(directory: str | Path) -> list[str]:
    """Useful for inspecting a user's produced artifacts without running them."""
    directory = Path(directory)
    messages = []
    for path in sorted(directory.glob('*.exe')):
        manifest_file = Path(str(path) + '.imports.json')
        manifest = json.loads(manifest_file.read_text('utf-8')) if manifest_file.is_file() else None
        dlls, _required = manifest_dlls_and_console_symbols(manifest)
        symbols = required_console_exports(path, manifest)
        if not symbols:
            continue
        console = directory / CONSOLE_DLL
        if not console.is_file():
            messages.append(f'{path.name}: {CONSOLE_DLL} FEHLT; benötigte Exporte: {", ".join(sorted(symbols))}')
        else:
            machine = MACHINE_AMD64 if str((manifest or {}).get('target', '')).lower() == 'pe64' else MACHINE_I386
            error = validate_console_library(console, machine, symbols)
            if error:
                messages.append(f'{path.name}: {error}')
    return messages

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Prüft Pascal-EXE/DLL-Ausgaben auf fehlende Konsolenruntime-Imports.'
    )
    parser.add_argument('output_directory', type=Path,
                        help='Projekt-Ausgabeordner mit EXE/DLL und *.imports.json')
    args = parser.parse_args()
    if not args.output_directory.is_dir():
        parser.error('Ausgabeverzeichnis nicht gefunden')
    errors = diagnose_package(args.output_directory)
    if errors:
        for error in errors:
            print('FEHLER:', error)
        raise SystemExit(1)
    print('Keine fehlende oder inkompatible Konsolenruntime nachweisbar.')

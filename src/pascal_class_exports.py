"""Stage 542: source-free Pascal class export ABI descriptors.

A public/protected instance field is not a global DLL symbol.  We therefore
publish its layout in the PUI and export explicit typed memory access bridges.
The executable imports *methods* through the Windows import table, never by
loading stored function addresses from a PUI file.
"""
from __future__ import annotations
import re

_VERSION = 1
_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_EXPORT = re.compile(r"\{\s*\$\s*export\s+(" + _IDENTIFIER + r")\s*\}", re.I)
_CLASS = re.compile(r"\b(" + _IDENTIFIER + r")\s*=\s*class\b", re.I)


def exported_classes(source: str, code_mask: str) -> tuple[str, ...]:
    """Resolve {$export TName} against the *next* class declaration.

    code_mask is a same-length lexical mask produced by the Pascal frontend;
    it ignores class keywords inside strings, comments and inactive branches.
    """
    declarations = list(_CLASS.finditer(code_mask))
    exports: dict[str, str] = {}
    for directive in _EXPORT.finditer(source):
        # Disabled IFDEF branches are blanked by the preprocessing stage.
        # Unlike the class keyword, the directive is permitted inside a {$...}.
        next_class = next((item for item in declarations if item.start() > directive.end()), None)
        expected = directive.group(1)
        if next_class is None or next_class.group(1).casefold() != expected.casefold():
            raise ValueError(
                f"{{$export {expected}}} muss unmittelbar der nächsten "
                f"Klassendefinition '{expected} = class' zugeordnet sein."
            )
        key = expected.casefold()
        if key in exports:
            raise ValueError(f"Klassenexport doppelt deklariert: {expected}")
        exports[key] = next_class.group(1)
    return tuple(exports.values())


def export_name(class_name: str, member_name: str, kind: str = 'method') -> str:
    for text in (class_name, member_name):
        if re.fullmatch(_IDENTIFIER, text) is None:
            raise ValueError(f"Ungueltiger Pascal-DLL-Symbolname: {text!r}")
    if kind == 'method':
        return f"{class_name}_{member_name}"
    if kind in {'get', 'set', 'new'}:
        return f"{class_name}_{kind}_{member_name}"
    raise ValueError(f"Ungueltige Exportart: {kind}")


def bridge_symbol(class_name: str, member_name: str, kind: str = 'method') -> str:
    normalized = re.sub(r"[^a-z0-9_]", "_", f"{class_name}_{kind}_{member_name}".casefold())
    return "__d64_cls_" + normalized


def public_class_contract(document: dict) -> list[dict]:
    exported = {x.casefold() for x in document.get('exported_classes', [])}
    result = []
    for cls in document.get('symbols', {}).get('classes', []):
        if isinstance(cls, dict) and cls.get('name', '').casefold() in exported:
            result.append(cls)
    return result


def _pe_exports(binary: bytes, target: str) -> set[str]:
    """Read PE export names without importing/loading executable code.

    Returns only public exported *names*. Ordinal-only exports cannot satisfy
    a PUI class import because their ABI has no stable symbolic identity.
    """
    import struct
    if len(binary) < 256 or binary[:2] != b'MZ':
        raise ValueError('Keine gueltige Windows-DLL (MZ-Header fehlt).')
    pe_offset = struct.unpack_from('<I', binary, 0x3c)[0]
    if pe_offset + 24 > len(binary) or binary[pe_offset:pe_offset+4] != b'PE\0\0':
        raise ValueError('Keine gueltige Windows-DLL (PE-Signatur fehlt).')
    machine, sections = struct.unpack_from('<HH', binary, pe_offset+4)
    target_machine = 0x8664 if str(target).casefold() in {'pe64','win64','windows64','windows-pe64','windows-pe32+'} else 0x14c
    if machine != target_machine:
        raise ValueError(f'DLL-Architektur unpassend: PE-Maschine 0x{machine:04X}, benötigt 0x{target_machine:04X}.')
    optional_size, characteristics = struct.unpack_from('<HH', binary, pe_offset+20)
    if not characteristics & 0x2000:
        raise ValueError('Die Datei ist kein DLL-Image (IMAGE_FILE_DLL fehlt).')
    optional = pe_offset + 24
    if optional + optional_size > len(binary):
        raise ValueError('Beschädigter PE Optional Header.')
    magic = struct.unpack_from('<H', binary, optional)[0]
    if (magic, machine) not in ((0x10b, 0x14c), (0x20b, 0x8664)):
        raise ValueError('PE Optional Header passt nicht zur DLL-Architektur.')
    data_directory_offset = 112 if magic == 0x20b else 96
    if data_directory_offset + 8 > optional_size:
        return set()
    export_rva, export_size = struct.unpack_from('<II', binary, optional+data_directory_offset)
    if not export_rva or not export_size:
        return set()
    headers_size = struct.unpack_from('<I', binary, optional+60)[0]
    ranges = []
    section_start = optional + optional_size
    for index in range(sections):
        off = section_start + 40*index
        if off+40 > len(binary):
            raise ValueError('Abgeschnittener PE-Sektionsheader.')
        virtual_size, rva, raw_size, raw_ptr = struct.unpack_from('<IIII', binary, off+8)
        ranges.append((rva,rva+max(raw_size,virtual_size),raw_ptr,raw_size))

    def deref(rva: int, size: int) -> int:
        if rva < headers_size and rva+size <= len(binary):
            return rva
        for low, high, raw, raw_size in ranges:
            if low <= rva and rva+size <= high and rva-low+size <= raw_size:
                pos=raw+rva-low
                if pos+size <= len(binary):
                    return pos
        raise ValueError(f'DLL-Exportadresse RVA 0x{rva:X} ist ungueltig.')

    exp = deref(export_rva, 40)
    count = struct.unpack_from('<I', binary, exp+24)[0]
    names_rva = struct.unpack_from('<I', binary, exp+32)[0]
    if count > 100000:
        raise ValueError('Ungueltige Anzahl von DLL-Exportnamen.')
    if not count:
        return set()
    names_pos = deref(names_rva, count*4)
    names = set()
    for i in range(count):
        rva = struct.unpack_from('<I', binary, names_pos+4*i)[0]
        pos = deref(rva, 1)
        end = binary.find(b'\0', pos, min(len(binary), pos+1024))
        if end < 0:
            raise ValueError('Ungueltiger DLL-Exportname ohne Terminator.')
        names.add(binary[pos:end].decode('ascii'))
    return names


def validate_class_dll_references(refs, contracts, *, target: str,
                                   filename: str, output_directory=None,
                                   link_search_paths=()) -> tuple[str,...]:
    """Enforce explicit DLL linkage and machine/export-name consistency.

    Only DLLs explicitly linked using {$L libfoo} are candidates, never all
    DLL files found in PATH. This prevents accidental linking to a stale copy.
    """
    from pathlib import Path
    import os
    contracts = list(contracts)
    if not contracts:
        return ()
    refs = list(refs)
    if len(refs) != 1:
        raise ValueError('DLL-Klassenimporte erfordern eine eindeutige {$L libfoo}-Angabe.')
    name = Path(refs[0]).name
    source_dir = (Path(filename).expanduser().resolve().parent
                  if filename and not str(filename).startswith('<') else Path.cwd())
    # Project-configured paths take precedence over CWD/PATH, so an old
    # Runtime.dll beside a different source cannot silently win. A fully
    # qualified DLL reference always identifies that exact file.
    reference = Path(refs[0]).expanduser()
    if reference.is_absolute():
        candidates = [reference]
    else:
        folders = ([Path(path) for path in link_search_paths]
                   + ([Path(output_directory)] if output_directory else [])
                   + [source_dir, Path.cwd()])
        folders += [Path(path) for path in os.environ.get('PATH','').split(os.pathsep) if path]
        candidates = []
        for folder in folders:
            candidates.append(folder / reference)
            if reference != Path(name):
                candidates.append(folder / name)
    location = next((item.resolve() for item in candidates if item.is_file()), None)
    if location is None:
        checked = ', '.join(str(p) for p in dict.fromkeys(item.parent for item in candidates[:14]))
        raise ValueError(f'DLL für {{$L {Path(name).stem}}} nicht gefunden: {name}. '
                         f'Geprüfte Verzeichnisse: {checked}. '
                         'Ausgabe-Verzeichnis, Suchpfad und Zielarchitektur prüfen.')
    imports = _pe_exports(location.read_bytes(), target)
    expected = set()
    for contract in contracts:
        cls = contract['name']
        expected.update(str(item.get('dll_export_name') or export_name(cls, item['name']))
                        for item in contract.get('methods',()))
        expected.update(export_name(cls, item['name'], 'new')
                        for item in contract.get('methods',())
                        if str(item.get('kind','')).casefold() == 'constructor')
        for field in contract.get('fields',()):
            if field.get('visibility') == 'private':
                continue
            expected.add(export_name(cls, field['name'], 'get'))
            expected.add(export_name(cls, field['name'], 'set'))
        for prop in contract.get('properties',()):
            for direction, accessor in (('get','read'),('set','write')):
                if not prop.get(accessor):
                    continue
                expected.add(export_name(cls, prop['name'], direction))
    missing = expected - imports
    if missing:
        raise ValueError(f'DLL {name}: {len(missing)} PUI-Klassenexporte fehlen: '
                         + ', '.join(sorted(missing)[:8]))
    return (str(location),)

"""Project-driven dBASE COFF inputs for PE32 / PE32+ (Stage 668).

`Module` is the link owner (EXE _start or DLL __d64_dll_entry).
`Programme` are ordinary relocatable object contributors; they never provide
an entry point. The COFF namespace isolates their private runtime symbols.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import re


def module_namespace(source_path) -> str:
    identity = str(Path(source_path).expanduser().resolve()).casefold()
    return '__d64_module_' + sha256(identity.encode('utf-8')).hexdigest()[:12] + '_'


def namespace_module_object(obj, source_path, *, hide_tobject_exports=False):
    """Namespace private COFF labels; retain declared public exports.

    Backwards compatible helper from Stage 667; Stage 668 applies it to
    *Programme* objects instead of the selected executable Module.
    """
    prefix = module_namespace(source_path)
    declared = getattr(obj, 'exports', {}) or {}
    def retained(public_name, internal):
        return not (hide_tobject_exports and (
            str(public_name).casefold().startswith('__dbase_cls_tobject_')
            or str(internal).casefold().startswith('__dbase_cls_tobject_')
        ))
    public = {str(internal).casefold() for public_name, internal in declared.items()
              if retained(public_name, internal)}
    mapping = {
        name: name if name.casefold() in public and name.casefold() != '_start'
        else prefix + name
        for name in obj.symbols
    }
    return replace(
        obj,
        symbols={mapping[name]: value for name, value in obj.symbols.items()},
        symbol_sections={mapping.get(name, name): sec for name, sec in obj.symbol_sections.items()},
        relocations=tuple(
            replace(rel, symbol=mapping.get(rel.symbol, rel.symbol))
            for rel in obj.relocations
        ),
        entry_symbol=mapping.get(getattr(obj, 'entry_symbol', '_start'),
                                 getattr(obj, 'entry_symbol', '_start')),
        exports={public_name: mapping.get(internal, internal)
                 for public_name, internal in declared.items()
                 if retained(public_name, internal)},
    )


_START_BEGIN = '; __d64_dbase_startup_begin__'
_START_END = '; __d64_dbase_startup_end__'


def strip_program_entry_assembly(source: str) -> str:
    """Remove the entire generated EXE startup/teardown from Programme ASM.

    The dBASE code emitter wraps startup code in an explicit marker pair so
    replacing it cannot accidentally consume class method implementations.
    The .text section remains for generated class methods and procedures.
    """
    text = str(source)
    before, found, after = text.partition(_START_BEGIN)
    if not found:
        raise ValueError('dBASE-Startcode-Marker fehlt. Bitte Quelle mit Stage 668 erneut kompilieren.')
    removed, end, tail = after.partition(_START_END)
    if not end:
        raise ValueError('dBASE-Startcode-Endmarker fehlt. Bitte Quelle erneut kompilieren.')
    if not re.search(r'(?m)^\s*_start\s*:', removed):
        raise ValueError('dBASE-Startcode hat keinen erwarteten _start-Einstieg.')
    # Imports emitted by the TObject/VMT ABI may precede the startup code
    # but lie *inside* its marker range.  Generated class factories following
    # the startup tail still call these symbols.  Stripping the imports while
    # keeping the factories would leave unresolved __dbase_obj_* references.
    # Retain the declarations, not the startup instructions or _start label.
    retained_imports = []
    defined_imports = set()
    import_pattern = re.compile(r'(?i)^\s*import\s+([^,\s]+)\s*,')
    for line in (before + '\n' + tail).splitlines():
        match = import_pattern.match(line)
        if match:
            defined_imports.add(match.group(1).casefold())
    for line in removed.splitlines():
        match = import_pattern.match(line)
        if not match or match.group(1).casefold() in defined_imports:
            continue
        retained_imports.append(line)
        defined_imports.add(match.group(1).casefold())
    header = '\n'.join(retained_imports)
    result = before + ('\n' + header if header else '') + '\nsection .text\n' + tail
    if re.search(r'(?mi)^\s*(?:entry|global)\s+_start\b|^\s*_start\s*:', result):
        raise ValueError('Nach dem Entfernen des Startcodes ist _start noch definiert.')
    return result


def strip_dbase_library_entry_assembly(source: str) -> str:
    """Remove the DLL loader stub from a class-library Programme object.

    Keep the class code, exports and data. The selected Module exclusively
    owns the actual __d64_dll_entry at link time.
    """
    text = str(source)
    pattern = (r'(?m)^global __d64_dll_entry\s*\n'
               r'entry __d64_dll_entry\s*\n')
    changed, count = re.subn(pattern, '', text, count=1)
    if count != 1:
        raise ValueError('DLL-Einstieg konnte nicht entfernt werden: Quelle neu kompilieren.')
    stub = (r'(?m)^__d64_dll_entry:\s*\n'
            r'[ \t]*mov eax, 1\s*\n[ \t]*ret(?: 12)?\s*\n')
    changed, count = re.subn(stub, '', changed, count=1)
    if count != 1:
        raise ValueError('DLL-Startcode konnte nicht entfernt werden: Quelle neu kompilieren.')
    return changed


def module_link_inputs(module_object, program_sources: Iterable, object_for_source):
    """Resolve selected Module (first) and all associated Programme .o files.

    A Module is sufficient to build an EXE; Programme objects are optional.
    Every listed source must have an existing COFF object and duplicates are
    rejected. Missing objects are never silently rebuilt or ignored.
    """
    module = Path(module_object).resolve()
    if not module.is_file():
        raise ValueError(f'Das Modul wurde noch nicht assembliert: {module}')
    output = [module]
    seen = {str(module).casefold()}
    for source in program_sources:
        path = Path(source).resolve()
        obj = Path(object_for_source(path)).resolve()
        key = str(obj).casefold()
        if key in seen:
            raise ValueError(f'Modul/Programm liefert eine doppelte Objektdatei: {obj}')
        if not obj.is_file():
            raise ValueError(
                f'COFF-Objekt des Programms fehlt: {obj}\n'
                f'Bitte {path.name} zuerst im ASM-Tab assemblieren.'
            )
        output.append(obj)
        seen.add(key)
    return tuple(output)

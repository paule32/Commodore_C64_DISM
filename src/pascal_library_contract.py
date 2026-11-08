"""Source-free, architecture-scoped Pascal DLL ownership contracts.

An explicit {$L library} is required on the consumer.  A contract describes
which PUI units are provided by that DLL.  It never stores source, pointer
addresses or generated code; all external symbols are linked as PE imports.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

FORMAT = 'd64-pascal-library-contract'
VERSION = 1


def canonical_target(target):
    text = str(target).casefold()
    return 'pe64' if text in ('pe64', 'win64', 'windows64', 'windows-pe64', 'windows-pe32+') else 'pe32'


def public_routine_export(unit, name):
    return 'D64_' + ''.join(c if c.isalnum() or c == '_' else '_' for c in unit) + '_' + name


def _contract_path(output_directory, library):
    return Path(output_directory) / (str(library) + '.paslib.json')


def write_contract(output_directory, library, target, unit_documents, emitted_assembly):
    """Publish only symbols that the DLL's assembler actually exports.

    The caller must have a successful native DLL link before treating this
    metadata as a usable provider. Consumers validate PE exports separately.
    """
    import re
    name = str(library)
    exported = set(re.findall(r'^\s*export\s+"([^"]+)"\s*,', emitted_assembly, re.M))
    units = {}
    for unit, doc in unit_documents.items():
        classes = []
        for cls in doc.get('symbols', {}).get('classes', []):
            if str(cls.get('name', '')).casefold() in {str(n).casefold() for n in doc.get('exported_classes', [])}:
                classes.append(str(cls['name']))
        functions = []
        for kind in ('functions', 'procedures'):
            for routine in doc.get('symbols', {}).get(kind, ()):
                if not isinstance(routine, dict):
                    continue
                label = public_routine_export(unit, str(routine['name']))
                if label in exported:
                    functions.append({'name': str(routine['name']), 'export': label})
        units[unit.casefold()] = {
            'name': unit, 'classes': sorted(classes, key=str.casefold),
            'routines': functions,
        }
    data = {'format': FORMAT, 'version': VERSION, 'library': name + '.dll',
            'target': canonical_target(target), 'units': units,
            'exports': sorted(exported, key=str.casefold)}
    destination = _contract_path(output_directory, name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(prefix='.' + name + '-', suffix='.tmp', dir=destination.parent)
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(temp, destination)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return destination


def read_contract(dll_reference, target, search_paths=()):
    """Read only a contract for the explicitly named DLL; reject wrong ABI."""
    reference = Path(dll_reference)
    stem = reference.stem
    # Explicit project output folders win over the process working directory.
    # A full path supplied by {$L ...} stays authoritative.
    dirs = ([reference.parent] if reference.is_absolute() else
            [Path(p) for p in search_paths] + [reference.parent])
    checked = set()
    for folder in dirs:
        for base in (stem + '.paslib.json', reference.name + '.paslib.json'):
            candidate = folder / base
            key = str(candidate.resolve()).casefold()
            if key in checked:
                continue
            checked.add(key)
            if not candidate.is_file():
                continue
            try:
                data = json.loads(candidate.read_text(encoding='utf-8'))
            except (OSError, UnicodeError, ValueError) as exc:
                raise ValueError(f'Beschädigter Pascal-DLL-Vertrag: {candidate}: {exc}') from exc
            if data.get('format') != FORMAT or data.get('version') != VERSION:
                raise ValueError(f'Ungültige Pascal-DLL-Vertragsversion: {candidate}')
            if data.get('target') != canonical_target(target):
                raise ValueError(f'DLL-Vertrag {candidate}: falsche Zielarchitektur.')
            if str(data.get('library', '')).casefold() != reference.name.casefold():
                raise ValueError(f'DLL-Vertrag {candidate}: falscher DLL-Name.')
            if not isinstance(data.get('units'), dict):
                raise ValueError(f'DLL-Vertrag {candidate}: Unit-Tabelle fehlt.')
            return data
    return None


def unit_contract(providers, unit):
    matches = [(lib, doc['units'][unit.casefold()]) for lib, doc in providers
               if unit.casefold() in doc['units']]
    if len(matches) > 1:
        raise ValueError(f'Unit {unit} wird von mehreren DLLs bereitgestellt.')
    return matches[0] if matches else None


def validate_contract_exports(contract, dll_reference, target, search_paths=()):
    """Fail closed on stale DLL/manifest or a mismatched architecture."""
    from pascal_class_exports import _pe_exports
    reference = Path(dll_reference)
    if reference.is_absolute():
        candidates = [reference]
    else:
        folders = [Path(x) for x in search_paths] + [reference.parent]
        candidates = [folder / reference for folder in folders]
        if reference != Path(reference.name):
            candidates.extend(folder / reference.name for folder in folders)
    library = next((candidate for candidate in candidates if candidate.is_file()), None)
    if library is None:
        checked = ', '.join(str(p) for p in dict.fromkeys(item.parent for item in candidates[:14]))
        raise ValueError(f'Pascal-DLL nicht vorhanden: {reference.name}. '
                         f'Geprüfte Verzeichnisse: {checked}. Erst DLL erstellen.')
    exports = _pe_exports(library.read_bytes(), target)
    expected = set(str(name) for name in contract.get('exports', ()))
    missing = expected - exports
    if missing:
        raise ValueError(f'DLL {library.name} entspricht nicht dem Pascal-PUI-Vertrag: '
                         f'{len(missing)} Exporte fehlen: ' + ', '.join(sorted(missing)[:8]))
    return str(library.resolve())

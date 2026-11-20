# -*- coding: utf-8 -*-
"""Atomic GNU gettext help-catalog deployment as <EXE stem>.hlp (Stage 652)."""
from __future__ import annotations
import gettext
import io
import os
import struct
import tempfile
from pathlib import Path


def install_help_catalog(executable: str | Path, catalog: str | Path) -> Path:
    """Validate the GNU-MO payload, then install it as App.hlp beside App.exe."""
    target_exe = Path(executable).resolve(strict=True)
    if target_exe.suffix.casefold() != '.exe':
        raise ValueError(f'Help catalog needs a Windows EXE: {target_exe}')
    source = Path(catalog).resolve(strict=True)
    if source.suffix.casefold() != '.hlp':
        raise ValueError(f'Help source must be a compiled .hlp: {source}')
    data = source.read_bytes()
    if len(data) < 28 or data[:4] not in (b'\xde\x12\x04\x95', b'\x95\x04\x12\xde'):
        raise ValueError(f'Ungültiger GNU-MO/HLP-Header: {source}')
    try:
        catalog_obj = gettext.GNUTranslations(fp=io.BytesIO(data))
    except (OSError, ValueError, UnicodeError, struct.error) as exc:
        raise ValueError(f'GNU-MO/HLP-Katalog nicht lesbar: {source}: {exc}') from exc
    if 'index' not in catalog_obj._catalog:
        raise ValueError(f'Katalog ohne Standardthema index: {source}')
    destination = target_exe.with_suffix('.hlp')
    if destination == source:
        return destination
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent,
                                         prefix=destination.name + '.', suffix='.tmp',
                                         delete=False) as out:
            tmp = Path(out.name)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, destination)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return destination


def compile_help_sources(sources, executable: str | Path, *, require_executable=False):
    """Compile project THLP sources using the selected EXE profile name.

    THLP filenames are never used for output names. The editable intermediate
    <Project>.po lives next to the first THLP, while <Project>.hlp is placed
    beside the configured executable, even before the EXE has been linked.
    """
    from turbo_help_compiler import HelpCompiler, read_po, write_po, write_mo
    files = list(dict.fromkeys(Path(item).expanduser().resolve(strict=True)
                               for item in sources))
    if not files:
        raise ValueError('Keine .thlp-Projektdateien vorhanden')
    if any(path.suffix.casefold() != '.thlp' for path in files):
        raise ValueError('Turbo Help akzeptiert ausschließlich .thlp als Quelle')
    target = Path(executable).expanduser().resolve()
    if target.suffix.casefold() != '.exe' or not target.stem:
        raise ValueError(f'Turbo Help benötigt einen konfigurierten EXE-Projektnamen: {target}')
    if require_executable and not target.is_file():
        raise FileNotFoundError(f'EXE wurde noch nicht erzeugt: {target}')
    topics = HelpCompiler.compile_files(files)
    po_path = files[0].parent / f'{target.stem}.po'
    po_text = write_po(topics)
    # Only replace the PO when all sources compiled successfully.
    po_path.write_text(po_text, encoding='utf-8', newline='\n')
    data = write_mo(read_po(po_text))
    destination = target.with_suffix('.hlp')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent,
                                         prefix=destination.name + '.', suffix='.tmp',
                                         delete=False) as output:
            temp = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, destination)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    return dict(topics), po_path, destination


def compile_project_help(sources, executable: str | Path) -> Path:
    """Link-time rebuild: install <EXE stem>.hlp next to an existing EXE."""
    _topics, _po_path, destination = compile_help_sources(
        sources, executable, require_executable=True)
    return destination

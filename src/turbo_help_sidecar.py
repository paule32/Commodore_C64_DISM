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


def _write_hlp_atomic(path: Path, content: bytes) -> None:
    """Never expose a partially written GNU gettext catalog to F1 consumers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp',
                                         delete=False) as output:
            temp = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def compile_help_sources(sources, executable: str | Path, *, require_executable=False,
                         root=None, include_paths=(), metadata=None,
                         po_path=None, hlp_path=None):
    """Compile THLP sources as a PO and a compiled GNU gettext *.hlp.

    Existing projects still default to <EXE stem>.po beside the source and
    <EXE stem>.hlp beside the executable. Stage 688 settings can replace both
    outputs (by default <main THLP stem>.po/.hlp). The latter is additionally
    deployed as <EXE stem>.hlp when necessary for the existing F1 runtime ABI.
    At no point do we save an additional *.mo file.
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
    topics = HelpCompiler.compile_files(files, root=root, include_paths=include_paths)
    po_path = Path(po_path).expanduser().resolve() if po_path else files[0].parent / f'{target.stem}.po'
    destination = target.with_suffix('.hlp')
    hlp_path = Path(hlp_path).expanduser().resolve() if hlp_path else destination
    if po_path.suffix.casefold() != '.po' or hlp_path.suffix.casefold() != '.hlp':
        raise ValueError('Hilfekatalog-Dateiendungen müssen .po und .hlp sein')
    if po_path == hlp_path or po_path == destination:
        raise ValueError('PO und HLP benötigen getrennte Dateien')
    po_text = write_po(topics, metadata=metadata)
    # Validate the PO and build GNU-MO *bytes*, but only write .hlp files.
    data = write_mo(read_po(po_text))
    po_path.parent.mkdir(parents=True, exist_ok=True)
    po_path.write_text(po_text, encoding='utf-8', newline='\n')
    _write_hlp_atomic(hlp_path, data)
    if hlp_path != destination:
        _write_hlp_atomic(destination, data)
    return dict(topics), po_path, destination


def compile_project_help(sources, executable: str | Path, *, root=None, include_paths=(),
                         metadata=None, po_path=None, hlp_path=None) -> Path:
    """Link-time rebuild: install <EXE stem>.hlp next to an existing EXE."""
    _topics, _po_path, destination = compile_help_sources(
        sources, executable, require_executable=True,
        root=root, include_paths=include_paths,
        metadata=metadata, po_path=po_path, hlp_path=hlp_path)
    return destination

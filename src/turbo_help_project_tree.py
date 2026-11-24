"""Stage 685: persistent nested Turbo Help project tree and safe include paths."""
from __future__ import annotations

from pathlib import Path


def normalize_help_name(name: str, *, folder: bool = False) -> str:
    """Return a single safe child name (never an absolute/parent path)."""
    value = str(name or '').strip()
    if not value or value in ('.', '..') or '/' in value or '\\' in value or ':' in value:
        raise ValueError('Bitte nur einen Datei- oder Ordnernamen ohne Pfad angeben.')
    if any(ord(char) < 32 or char in '<>"|?*' for char in value):
        raise ValueError('Ungültige Zeichen im Datei- oder Ordnernamen.')
    if value.rstrip(' .') != value:
        raise ValueError('Name darf nicht mit Leerzeichen oder Punkt enden.')
    if value.split('.')[0].casefold() in {
        'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)),
        *(f'lpt{i}' for i in range(1, 10)),
    }:
        raise ValueError('Reservierter Windows-Dateiname.')
    if not folder:
        if not Path(value).suffix:
            value += '.thlp'
        if Path(value).suffix.casefold() != '.thlp':
            raise ValueError('Turbo-Hilfequellen benötigen die Endung .thlp')
    return value


def checked_child(root: Path, parent: Path, name: str) -> Path:
    """Keep new help files and folders under the configured root."""
    root = Path(root).expanduser().resolve()
    parent = Path(parent).expanduser().resolve()
    if not parent.is_relative_to(root):
        raise ValueError('Ordner liegt außerhalb des Turbo-Hilfe-Stammverzeichnisses.')
    result = parent / name
    if result.resolve().parent != parent:
        raise ValueError('Ungültiger oder umgeleiteter Hilfe-Pfad.')
    return result


def ordered_main_sources(rows):
    """Validate a single marked main document; preserve remaining project order."""
    files = [row for row in rows if row.get('kind', 'file') == 'file' and row.get('path')]
    mains = [row for row in files if bool(row.get('main'))]
    if len(mains) != 1:
        raise ValueError('Bitte genau einen Haupt-Eintrag im Turbo-Hilfe-Projektbaum festlegen.')
    main = mains[0]
    return [Path(main['path'])] + [Path(row['path']) for row in files if row is not main]


def resolve_include(name: str, source: Path, known_files, search_paths=()):
    """Resolve nested %include first locally, then by project path or file name.

    Ambiguous identical basenames are rejected to avoid non-deterministic builds.
    """
    source = Path(source).resolve()
    requested = Path(name)
    if requested.is_absolute() or '..' in requested.parts:
        raise ValueError(f'Unzulässiger %include-Pfad: {name}')
    known = {Path(p).resolve() for p in known_files}
    roots = tuple(Path(directory).resolve() for directory in search_paths)
    # Support the historical transposition '.tlhp' seen in older help sources.
    # Exact paths always take precedence; only a missing typo is substituted.
    requested_names = [requested]
    if requested.suffix.casefold() == '.tlhp':
        requested_names.append(requested.with_suffix('.thlp'))
    for lookup in requested_names:
        candidates = [source.parent / lookup, *(directory / lookup for directory in roots)]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_file() and (resolved in known or any(
                    resolved.is_relative_to(directory) for directory in roots)):
                return resolved
        matches = [p for p in known if p.name.casefold() == lookup.name.casefold()]
        if len(matches) > 1:
            raise ValueError(f'Mehrdeutiges %include {name}: ' + ', '.join(str(p) for p in sorted(matches)))
        if len(matches) == 1:
            return matches[0]
    raise FileNotFoundError(f'%include {name}: Datei nicht im Turbo-Hilfe-Projektbaum gefunden')


def rename_help_path(source: Path, destination: Path, *, overwrite: bool = False) -> bool:
    """Rename a Turbo Help source, optionally replacing an existing target.

    The target is parked beside its original location until moving the source
    succeeds. If the move fails the old target is restored. Replacing a folder
    intentionally replaces its entire directory tree, not only its name.

    Return True when an existing target was replaced, otherwise False.
    """
    import shutil
    import uuid

    source, destination = Path(source), Path(destination)
    if not source.exists() and not source.is_symlink():
        raise FileNotFoundError(f'Quelle existiert nicht: {source}')
    if source == destination:
        return False
    if source.parent != destination.parent:
        raise ValueError('Umbenennen darf das übergeordnete Verzeichnis nicht ändern.')

    target_exists = destination.exists() or destination.is_symlink()
    # Under Windows, an unchanged name with different capitalization points to
    # the same file. This is a spelling-only rename, not an overwrite.
    if target_exists and str(source).casefold() == str(destination).casefold():
        source.rename(destination)
        return False
    if not target_exists:
        source.rename(destination)
        return False
    if not overwrite:
        raise FileExistsError(f'Datei oder Verzeichnis bereits vorhanden: {destination}')
    if source.is_dir() != destination.is_dir():
        raise ValueError('Datei und Verzeichnis können einander nicht ersetzen.')

    backup = destination.with_name(f'.{destination.name}.d64-rename-{uuid.uuid4().hex}.bak')
    destination.rename(backup)
    try:
        source.rename(destination)
    except BaseException:
        # The source move did not succeed: do not lose the old destination.
        try:
            backup.rename(destination)
        except OSError as restore_exc:
            raise OSError(
                f'Umbenennen gescheitert; Sicherung konnte nicht wiederhergestellt '
                f'werden: {backup} ({restore_exc})') from restore_exc
        raise

    # The replacement succeeded; the former target is no longer referenced by
    # the project tree and can be removed. Never report the rename itself as
    # failed just because deletion of the parked backup failed.
    try:
        if backup.is_dir() and not backup.is_symlink():
            shutil.rmtree(backup)
        else:
            backup.unlink()
    except OSError as exc:
        import warnings
        warnings.warn(f'Backup des ersetzten Hilfeziels bleibt erhalten: {backup}: {exc}', RuntimeWarning)
    return True

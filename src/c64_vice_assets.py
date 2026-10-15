"""Stage 402: stage raw C64 sprite dependencies for both VICE BASIC start paths.

The original LOAD "name",8,1 command is *not* rewritten. Instead, the
host .spr/.sprite file is converted into a C64 program file with a $3000 load
header, exposed using the name requested by BASIC on virtual drive 8.
"""
from __future__ import annotations

import re
import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

from c64_sprite_codec import decode_raw_sprites, encode_raw_sprites

SPRITE_LOAD_ADDRESS = 0x3000
# Match only a literal-name KERNAL LOAD from device 8 with SA=1. Ordinary
# LOAD, LOAD SCREEN, variables, or other devices remain unmodified.
_LOAD_SPRITE_RE = re.compile(
    r'(?i)(?<![\w])LOAD\s*"(?P<name>[^"\r\n]+\.(?:spr|sprite))"\s*,\s*8\s*,\s*1(?=\s|:|$)'
)


def c64_basic_sprite_load_names(source: str) -> tuple[str, ...]:
    """Collect literal .spr/.sprite dependency names from a BASIC source.

    Excludes simple REM comments; doesn't attempt to evaluate dynamic BASIC
    expressions (those are handled at runtime on the configured drive).
    """
    names = []
    seen = set()
    for source_line in str(source).splitlines():
        line = re.sub(r'^\s*\d+\s*', '', source_line)
        if re.match(r'(?i)^REM(?:\s|$)', line):
            continue
        for match in _LOAD_SPRITE_RE.finditer(line):
            # Never interpret text after REM as executable BASIC.
            before = line[:match.start()]
            if re.search(r'(?i)(?<!\w)REM(?:\s|$)', before):
                continue
            name = match.group('name')
            if name.casefold() not in seen:
                names.append(name)
                seen.add(name.casefold())
    return tuple(names)


def _existing_case_insensitive(directory: Path, name: str) -> Optional[Path]:
    direct = directory / name
    if direct.is_file():
        return direct
    if not directory.is_dir():
        return None
    for child in directory.iterdir():
        if child.is_file() and child.name.casefold() == name.casefold():
            return child
    return None


def c64_vice_sprite_program(raw: bytes, load_address: int = SPRITE_LOAD_ADDRESS) -> bytes:
    """Accept raw sprites or a previously prepared $3000-header PRG.

    Raw sprites have 63-/64-byte records.  A prepared PRG has exactly
    two more bytes than an integer number of 64-byte records.  Do not
    convert such a file for a second time: the user may already have
    copied a staged drive-8 file back into the project.
    """
    raw = bytes(raw)
    load_address = int(load_address)
    if not 0 <= load_address <= 0xFFFF:
        raise ValueError('Ungueltige Sprite-Ladeadresse.')
    if len(raw) >= 66 and (len(raw) - 2) % 64 == 0:
        recorded_address = int.from_bytes(raw[:2], 'little')
        if recorded_address != load_address:
            raise ValueError(
                f'Sprite-PRG erwartet Ladeadresse ${load_address:04X}, '
                f'Datei enthaelt ${recorded_address:04X}.'
            )
        if load_address + len(raw) - 2 > 0x10000:
            raise ValueError('Sprite-Daten ueberschreiten den C64-Adressraum.')
        return raw
    sprites, _ = decode_raw_sprites(raw)
    data = encode_raw_sprites(sprites, 64)
    if load_address + len(data) > 0x10000:
        raise ValueError('Sprite-Daten ueberschreiten den C64-Adressraum.')
    return load_address.to_bytes(2, 'little') + data


def prepare_c64_vice_sprite_drive(
    source: str,
    source_path: Optional[Path],
    *,
    search_dirs: Iterable[Path] = (),
    stage_root: Optional[Path] = None,
) -> Optional[Path]:
    """Convert referenced local .spr files to PRG images on virtual drive 8.

    None means no relevant sprite LOAD statements; caller doesn't modify VICE.
    FileNotFoundError / ValueError are surfaced BEFORE starting VICE.
    """
    names = c64_basic_sprite_load_names(source)
    if not names:
        return None

    roots = []
    if source_path is not None:
        roots.append(Path(source_path).resolve().parent)
    for candidate in search_dirs:
        directory = Path(candidate).resolve()
        if directory not in roots:
            roots.append(directory)
    if not roots:
        roots.append(Path.cwd())

    found = []
    for name in names:
        # Only simple CBM filenames; never allow arbitrary host path traversal.
        if (name in ('.', '..') or Path(name).name != name or
                '/' in name or '\\' in name or '\x00' in name):
            raise ValueError(f'Ungueltiger Sprite-Dateiname fuer VICE: {name!r}')
        path = next((match for base in roots
                     if (match := _existing_case_insensitive(base, name)) is not None), None)
        if path is None:
            raise FileNotFoundError(
                f'Sprite-Datei {name!r} nicht gefunden. Suchverzeichnisse: '
                + ', '.join(str(root) for root in roots)
            )
        found.append((name, c64_vice_sprite_program(path.read_bytes())))

    if stage_root is None:
        # Stage 407: NEVER use Windows %TEMP% as an implicit VICE drive.
        # Keep generated files near their BASIC project, normally on T:.
        stage_root = roots[0] / '.d64_dism' / 'vice_drive8'
    directory = Path(stage_root).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    # Track ONLY files that d64_dism itself generated. This permits a revised
    # sprite to refresh its earlier drive-8 copy without ever overwriting an
    # unrelated file (particularly an original raw .spr or vice.ini).
    manifest_file = directory / '.d64_dism_vice_generated.json'
    known = {}
    if manifest_file.exists():
        try:
            loaded = json.loads(manifest_file.read_text(encoding='utf-8'))
            if isinstance(loaded, dict):
                known = {str(k).casefold(): str(v) for k, v in loaded.items()}
        except (OSError, ValueError, TypeError):
            # A corrupt manifest cannot authorize any overwrites.
            known = {}
    planned = []
    for name, image in found:
        destination = directory / name
        if destination.exists():
            if not destination.is_file():
                raise FileExistsError(f'VICE-Laufwerk 8: Ziel ist keine Datei: {destination}')
            current = destination.read_bytes()
            if current != image:
                prior_digest = known.get(name.casefold())
                if not prior_digest or hashlib.sha256(current).hexdigest() != prior_digest:
                    raise FileExistsError(
                        f'VICE-Laufwerk 8: {destination} ist bereits vorhanden und '
                        'enthaelt fremde oder veraenderte Daten. Keine Quelldatei '
                        'wurde ueberschrieben. Bitte ein separates '
                        'Laufwerk-8-Verzeichnis waehlen.'
                    )
        planned.append((name, destination, image))
    # Validate *all* destination files before writing anything.
    for name, destination, image in planned:
        if not destination.exists() or destination.read_bytes() != image:
            destination.write_bytes(image)
        known[name.casefold()] = hashlib.sha256(image).hexdigest()
    manifest_file.write_text(json.dumps(known, indent=2, sort_keys=True), encoding='utf-8')
    return directory


def c64_generated_asm_basic_source(
    assembler_path: Path,
    *,
    output_directory: Optional[Path] = None,
    assembly_source: str = '',
) -> Optional[Path]:
    """Locate the original BASIC source behind a *.generated.asm file.

    A matching sibling source takes precedence. If the compiler wrote an
    absolute source pathname into its header, that pathname is a fallback.
    Never infer dependencies from unrelated assembler documents.
    """
    assembler_path = Path(assembler_path)
    suffix = '.generated.asm'
    if not assembler_path.name.casefold().endswith(suffix):
        return None
    stem = assembler_path.name[:-len(suffix)]
    folders = [assembler_path.parent]
    if output_directory is not None:
        folder = Path(output_directory)
        if folder not in folders:
            folders.append(folder)
    for directory in folders:
        for ext in ('.bas', '.basic'):
            found = _existing_case_insensitive(directory, stem + ext)
            if found is not None:
                return found.resolve()
    marker = re.search(
        r'(?im)^;\s*C64 BASIC Compiler output:\s*(.+?\.(?:bas|basic))\s*$',
        str(assembly_source)[:4096],
    )
    if marker is not None:
        candidate = Path(marker.group(1).strip().strip('"'))
        if candidate.is_file():
            return candidate.resolve()
    return None


def c64_vice_ini_drive8_directory(settings_file: Optional[Path]) -> Optional[Path]:
    """Read FSDevice8Dir from a user-selected VICE resource file.

    VICE uses sections such as [C64] or [C64SC], NOT JSON and NOT the
    application's QSettings. The returned path is not written to vice.ini.
    """
    if settings_file is None or not str(settings_file).strip():
        return None
    config = Path(settings_file).expanduser().resolve()
    if not config.is_file():
        raise FileNotFoundError(f'VICE-Einstellungen nicht gefunden: {config}')
    text = config.read_text(encoding='utf-8-sig', errors='replace')
    section = ''
    candidates = []
    for original in text.splitlines():
        line = original.strip()
        if not line or line.startswith((';', '#')):
            continue
        if line.startswith('[') and ']' in line:
            section = line[1:line.index(']')].strip().upper()
            continue
        match = re.match(r'(?i)^FSDevice8Dir\s*=\s*(.*)$', line)
        if match and section in ('C64', 'C64SC', ''):
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            if value:
                candidates.append((section, value))
    if not candidates:
        return None
    # Prefer x64sc's [C64] over unrelated machine sections.
    _, directory = next((x for x in candidates if x[0] == 'C64'), candidates[-1])
    path = Path(directory).expanduser()
    if not path.is_absolute():
        path = config.parent / path
    return path.resolve()


def c64_vice_configuration_command_options(settings_file: Optional[Path]) -> list[str]:
    """Honor an explicitly selected vice.ini in all VICE launch paths."""
    if not settings_file or not str(settings_file).strip():
        return []
    settings_file = Path(settings_file).expanduser().resolve()
    if not settings_file.is_file():
        raise FileNotFoundError(f'VICE-Einstellungen fehlen: {settings_file}')
    return ['-config', str(settings_file)]


@lru_cache(maxsize=8)
def _vice_drive8_trap_option(executable: str) -> str:
    """VICE 3.10 renamed -virtualdev8 to -trapdevice8.

    Inspect the executable's advertised options rather than guessing based
    on the project or silently enabling the unrelated IEC bus mode.
    """
    options = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                   text=True, errors='replace', timeout=5)
    if hasattr(subprocess, 'CREATE_NO_WINDOW'):
        options['creationflags'] = subprocess.CREATE_NO_WINDOW
    try:
        result = subprocess.run([str(executable), '-help'], **options)
        help_text = result.stdout or ''
        if '-trapdevice8' in help_text:
            return '-trapdevice8'
        if '-virtualdev8' in help_text:
            return '-virtualdev8'
    except (OSError, subprocess.TimeoutExpired):
        pass
    # Supported recent VICE builds use this name. With an unrecognized older
    # VICE, the process will reject this option rather than pretending that
    # a virtual directory has been enabled.
    return '-trapdevice8'


def c64_vice_drive8_command_options(
    path: Optional[Path], vice_executable: Optional[Path] = None,
) -> list[str]:
    """Expose a prepared directory as drive 8 for C64 KERNAL LOAD.

    An IEC/BusDevice8 setting is NOT a substitute for KERNAL traps.
    True-drive emulation must be disabled for host filesystem accesses.
    """
    if path is None:
        return []
    trap = (_vice_drive8_trap_option(str(vice_executable))
            if vice_executable is not None else '-trapdevice8')
    return [
        '-fs8', str(Path(path).resolve()),
        '-devicebackend8', '1',
        '+drive8truedrive',
        '+fs8hidecbm',
        trap,
    ]

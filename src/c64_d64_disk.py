"""Pure-Python Commodore 1541 D64 writer for BASIC/VICE build dependencies.

A standard 35-track, 683-sector D64. Sector 18/0 is the BAM, directory
starts at 18/1, files use the normal two-byte-per-sector chain. No VICE or
external c1541 dependency; source .spr and existing disk images stay intact.
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Iterable, Optional

TRACK_SECTORS = tuple([0] + [21]*17 + [19]*7 + [18]*6 + [17]*5)
DISK_SIZE = sum(TRACK_SECTORS[1:]) * 256  # 174848


def _offset(track: int, sector: int) -> int:
    if not (1 <= track <= 35 and 0 <= sector < TRACK_SECTORS[track]):
        raise ValueError(f'Unzulaessiger D64-Sektor {track}/{sector}')
    return (sum(TRACK_SECTORS[1:track]) + sector) * 256


def _cbm_name(name: str) -> bytes:
    """Use explicitly representable C64 DOS names (never silently truncate)."""
    if not name or len(name) > 16 or any(c in '"*/:?\\' or ord(c) < 32 or ord(c) > 126 for c in name):
        raise ValueError(f'Unzulaessiger C64-Disketten-Dateiname (max. 16 ASCII-Zeichen): {name!r}')
    return name.upper().encode('ascii')


def build_1541_d64(files: Iterable[tuple[str, bytes]], *, label: str = 'DBASE2MANY', disk_id: str = 'D4') -> bytes:
    """Build a real DOS 2A 1541 image containing closed PRG files.

    Each PRG value MUST include its 2-byte C64 load address. Handles multiple
    directory blocks, final-sector byte counts, BAM, and disk-full errors.
    """
    items = [(str(name), bytes(contents)) for name, contents in files]
    normalized = set()
    for name, data in items:
        encoded = _cbm_name(name)
        if encoded in normalized:
            raise ValueError(f'C64-Diskette: Dateiname doppelt: {name}')
        normalized.add(encoded)
        if len(data) < 2:
            raise ValueError(f'C64-Diskette: PRG ohne Ladeadress-Header: {name}')
    label_bytes = _cbm_name(label)
    id_bytes = _cbm_name(disk_id)
    image = bytearray(DISK_SIZE)
    free = {(t, s) for t in range(1, 36) for s in range(TRACK_SECTORS[t])}

    def reserve(t: int, s: int) -> None:
        free.remove((t, s))

    reserve(18, 0)  # BAM
    reserve(18, 1)  # first directory sector
    directory_count = (len(items) + 7) // 8
    if directory_count > TRACK_SECTORS[18] - 1:
        raise ValueError('C64-Diskette: zu viele Dateien fuer das Verzeichnis')
    dir_sectors = [(18, 1)]
    for s in range(2, directory_count + 1):
        reserve(18, s)
        dir_sectors.append((18, s))
    for i, (t, s) in enumerate(dir_sectors):
        o = _offset(t, s)
        if i + 1 < len(dir_sectors):
            image[o:o+2] = bytes(dir_sectors[i+1])
        else:
            image[o:o+2] = b'\x00\xff'

    # Prefer non-directory tracks. Disk sectors form deterministic chains.
    allocation = [(t, s) for t in tuple(range(17, 0, -1)) + tuple(range(19, 36))
                  for s in range(TRACK_SECTORS[t])]
    position = 0
    for file_index, (name, data) in enumerate(items):
        blocks = max(1, math.ceil(len(data) / 254))
        if position + blocks > len(allocation):
            raise ValueError('C64-Diskette voll: zu viele Sprite-/Programm-Daten')
        chain = allocation[position:position+blocks]
        position += blocks
        for block_index, (t, s) in enumerate(chain):
            reserve(t, s)
            o = _offset(t, s)
            payload = data[block_index*254:(block_index+1)*254]
            if block_index + 1 == len(chain):
                image[o:o+2] = bytes((0, len(payload) + 1))
            else:
                image[o:o+2] = bytes(chain[block_index+1])
            image[o+2:o+2+len(payload)] = payload
        dir_t, dir_s = dir_sectors[file_index // 8]
        o = _offset(dir_t, dir_s) + (file_index % 8) * 32
        image[o+2] = 0x82  # PRG, closed
        image[o+3:o+5] = bytes(chain[0])
        name_bytes = _cbm_name(name)
        image[o+5:o+21] = name_bytes.ljust(16, b'\xa0')
        image[o+30:o+32] = blocks.to_bytes(2, 'little')

    bam = _offset(18, 0)
    image[bam:bam+4] = b'\x12\x01\x41\x00'
    for t in range(1, 36):
        free_on_track = [s for s in range(TRACK_SECTORS[t]) if (t, s) in free]
        o = bam + 4 + (t-1)*4
        image[o] = len(free_on_track)
        bitmap = sum(1 << s for s in free_on_track)
        image[o+1:o+4] = bitmap.to_bytes(3, 'little')
    image[bam+0x90:bam+0xA0] = label_bytes.ljust(16, b'\xa0')
    image[bam+0xA0:bam+0xA2] = b'\xa0\xa0'
    image[bam+0xA2:bam+0xA4] = id_bytes.ljust(2, b'\xa0')
    image[bam+0xA4:bam+0xA9] = b'\xa0' + b'2A' + b'\xa0\xa0'
    return bytes(image)


def prepare_c64_sprite_disk(stage_directory: Path, *,
                            program_path: Optional[Path] = None,
                            program_name: Optional[str] = None,
                            names: Iterable[str] = (),
                            disk_root: Optional[Path] = None) -> tuple[Path, Optional[str]]:
    """Create immutable-content-named .d64 with sprites and optional autostart PRG.

    A new content hash gets a new filename, so never overwrite a VICE-mounted
    or manually edited disk. Only take explicitly referenced sprite names from
    the staging directory (not the JSON stage manifest).
    """
    directory = Path(stage_directory).resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f'VICE D64: Sprite-Verzeichnis fehlt: {directory}')
    files = []
    seen = set()
    for name in names:
        name = str(name)
        key = _cbm_name(name)
        if key in seen:
            continue
        seen.add(key)
        match = next((p for p in directory.iterdir()
                      if p.is_file() and p.name.casefold() == name.casefold()), None)
        if match is None:
            raise FileNotFoundError(f'VICE D64: vorbereitete Sprite-Datei fehlt: {name}')
        files.append((name, match.read_bytes()))
    if not files:
        raise ValueError('VICE D64: keine Sprite-Dateien gefunden')
    autostart_name = None
    if program_path is not None:
        program = Path(program_path).resolve()
        if not program.is_file():
            raise FileNotFoundError(f'VICE D64: Programm fehlt: {program}')
        autostart_name = program_name or program.stem
        # Avoid VICE autostart choosing sprite as first PRG entry.
        files.insert(0, (autostart_name, program.read_bytes()))
    image = build_1541_d64(files, label='DBASE2MANY', disk_id='D4')
    if disk_root is None:
        # .d64_dism/vice_drive8 -> .d64_dism/vice_disks
        disk_root = directory.parent / 'vice_disks'
    disk_root = Path(disk_root).resolve()
    disk_root.mkdir(parents=True, exist_ok=True)
    basename = Path(program_path).stem if program_path else 'C64_SPRITES'
    basename = re.sub(r'[^A-Za-z0-9_-]', '_', basename)[:50] or 'C64_SPRITES'
    fingerprint = hashlib.sha256(image).hexdigest()[:16]
    target = disk_root / f'{basename}_{fingerprint}.d64'
    if target.exists():
        if target.read_bytes() != image:
            raise FileExistsError(f'VICE D64: vorhandenes Image wurde veraendert: {target}')
    else:
        # Exclusive create guarantees an existing disk is never truncated.
        with target.open('xb') as handle:
            handle.write(image)
    return target, autostart_name


def c64_vice_d64_command_options(disk_path: Path) -> list[str]:
    """VICE's documented disk attachment switch; no host FS/trap overrides."""
    path = Path(disk_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f'VICE D64 nicht gefunden: {path}')
    return ['-8', str(path)]


def c64_vice_d64_autostart_options(disk_path: Path) -> list[str]:
    """Stage 412: autostart first PRG from a D64, without a host-name suffix.

    ``-autostart <image>:<prgname>`` converts the ASCII suffix to PETSCII
    in VICE. For our generated images, the executable is guaranteed to be
    directory entry 0, so the suffix is both redundant and a source of
    graphical-name/FILE NOT FOUND failures. Keep -8 explicit: the image
    must remain mounted for the program's subsequent LOAD commands.
    """
    path = Path(disk_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f'VICE D64 nicht gefunden: {path}')
    return ['-8', str(path), '-autostart', str(path)]

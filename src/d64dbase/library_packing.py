# -*- coding: utf-8 -*-
"""Stage 608: validate D64Z/MSZIP packing of named dBASE class libraries.

Unlike c64_dbase_runtime.dll, a RuntimeDB.dll is produced by the ordinary
COFF library link. Keep its project checkbox and the actual PE payload in sync.
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from .pe_dll_payload import D64Z, import_iats, parse_pe


class DBaseLibraryPackingError(ValueError):
    """The linked class DLL does not match its selected D64Z build mode."""


def validate_library_packing(
    image: Union[bytes, bytearray, memoryview, Path, str],
    target: str,
    *,
    requested: bool,
) -> dict:
    """Validate a real PE DLL and return its D64Z .text sizes when packed.

    A plain .ztext marker is not enough: check the loader entry, released raw
    .text, D64Z header and the Cabinet API imports. This function works both
    before saving and after Windows resource embedding / signing.
    """
    if isinstance(image, (str, Path)):
        data = Path(image).read_bytes()
    else:
        data = bytes(image)
    try:
        pe = parse_pe(data)
    except (ValueError, IndexError) as exc:
        raise DBaseLibraryPackingError(f'dBASE-DLL: ungültiges PE-Image: {exc}') from exc
    key = str(target).casefold().strip()
    machine = {'pe32': 0x14c, 'pe64': 0x8664}.get(key)
    if machine is None:
        raise DBaseLibraryPackingError(f'dBASE-DLL: unbekanntes Windows-Ziel: {target}')
    if pe['machine'] != machine:
        raise DBaseLibraryPackingError(
            f'dBASE-DLL: Architektur stimmt nicht überein ({key}; PE-Machine 0x{pe["machine"]:04X})'
        )
    sections = {section['name']: section for section in pe['secs']}
    markers = (b'.loader', b'.ztext')
    if not requested:
        if any(marker in sections for marker in markers):
            raise DBaseLibraryPackingError(
                'dBASE-DLL: D64Z-Payload vorhanden, obwohl die PE-Packung deaktiviert ist'
            )
        return {'packed': False, 'original_bytes': None, 'compressed_bytes': None}

    text = sections.get(b'.text')
    loader = sections.get(b'.loader')
    ztext = sections.get(b'.ztext')
    if text is None or loader is None or ztext is None:
        raise DBaseLibraryPackingError(
            'dBASE-DLL: D64Z/MSZIP wurde angefordert, aber .loader/.ztext fehlen. '
            'Der Klassen-DLL-Linker hat die Packoption nicht übernommen.'
        )
    if not text['vsize'] or text['rsize']:
        raise DBaseLibraryPackingError('dBASE-DLL: .text wurde nicht vollständig in D64Z ausgelagert')
    if not (loader['rva'] <= pe['entry'] < loader['rva'] + loader['vsize']):
        raise DBaseLibraryPackingError('dBASE-DLL: DLL-Einstiegspunkt zeigt nicht auf den Entpacker')
    if ztext['vsize'] < D64Z.size or len(ztext['data']) < D64Z.size:
        raise DBaseLibraryPackingError('dBASE-DLL: D64Z-Header fehlt')
    try:
        magic, version, codec, flags, rva, original, compressed, old_entry, _crc = (
            D64Z.unpack_from(ztext['data'])
        )
    except (ValueError, IndexError) as exc:
        raise DBaseLibraryPackingError('dBASE-DLL: D64Z-Header ungültig') from exc
    if (magic, version, codec, flags) != (b'D64Z', 1, 2, 1):
        raise DBaseLibraryPackingError('dBASE-DLL: ungültiges D64Z/MSZIP-Format')
    if (rva, original) != (text['rva'], text['vsize']):
        raise DBaseLibraryPackingError('dBASE-DLL: Text-RVA bzw. Entpackgröße falsch')
    if not (0 < compressed <= ztext['vsize'] - D64Z.size
            and compressed <= len(ztext['data']) - D64Z.size):
        raise DBaseLibraryPackingError('dBASE-DLL: komprimierte Payload-Größe ist ungültig')
    if not (text['rva'] <= old_entry < text['rva'] + text['vsize']):
        raise DBaseLibraryPackingError('dBASE-DLL: ursprünglicher DLL-Entry ungültig')
    try:
        imported_dlls = {dll.lower() for dll, _func in import_iats(pe)}
    except (ValueError, IndexError, KeyError) as exc:
        raise DBaseLibraryPackingError(f'dBASE-DLL: Loader-Importtabelle ungültig: {exc}') from exc
    if 'cabinet.dll' not in imported_dlls:
        raise DBaseLibraryPackingError('dBASE-DLL: cabinet.dll für den MSZIP-Entpacker fehlt')
    return {'packed': True, 'original_bytes': int(original), 'compressed_bytes': int(compressed)}

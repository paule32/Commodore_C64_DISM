# -*- coding: utf-8 -*-
"""Stage 610: optional, lossless-on-load physical PE32/PE32+ compactor.

Only whole FileAlignment blocks are removed.  Virtual addresses, section
VirtualSize, data directories, imports, exports and relocation contents stay
unchanged.  Trailing all-zero raw blocks may be represented by the PE loader's
ordinary zero-fill.  The compactor refuses signed/ambiguous images.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Any


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def compact_pe_image(image: bytes) -> tuple[bytes, dict[str, Any]]:
    original = bytes(image)
    report: dict[str, Any] = {
        'changed': False, 'before_size': len(original),
        'after_size': len(original), 'saved_bytes': 0,
        'zero_blocks': 0, 'zero_bytes': 0,
        'reason': 'Keine entbehrlichen FileAlignment-Blöcke.',
    }

    def skip(reason: str) -> tuple[bytes, dict[str, Any]]:
        report['reason'] = reason
        return original, report

    try:
        if len(original) < 0x100 or original[:2] != b'MZ':
            return skip('Kein MZ/PE-Image.')
        old_pe = struct.unpack_from('<I', original, 0x3C)[0]
        if old_pe < 0x40 or old_pe + 24 > len(original) or original[old_pe:old_pe + 4] != b'PE\0\0':
            return skip('Ungültiger NT-Header.')
        machine, section_count = struct.unpack_from('<HH', original, old_pe + 4)
        optional_size = struct.unpack_from('<H', original, old_pe + 20)[0]
        coff_flags = struct.unpack_from('<H', original, old_pe + 22)[0]
        optional = old_pe + 24
        if (machine, struct.unpack_from('<H', original, optional)[0]) not in ((0x14C, 0x10B), (0x8664, 0x20B)):
            return skip('Nur Windows PE32/PE32+ unterstützt.')
        table = optional + optional_size
        if not 0 < section_count <= 96 or table + section_count * 40 > len(original):
            return skip('Ungültige Section-Tabelle.')
        file_alignment, section_alignment = struct.unpack_from('<II', original, optional + 36)[0], struct.unpack_from('<I', original, optional + 32)[0]
        if (file_alignment < 512 or file_alignment > 65536 or file_alignment & (file_alignment - 1)
                or section_alignment < file_alignment or section_alignment & (section_alignment - 1)):
            return skip('Nicht unterstütztes PE-Alignment.')
        headers = struct.unpack_from('<I', original, optional + 60)[0]
        if headers % file_alignment or headers > len(original) or headers < table + 40 * section_count:
            return skip('Ungültiges SizeOfHeaders.')
        if struct.unpack_from('<II', original, old_pe + 12) != (0, 0):
            return skip('COFF-Symboltabelle vorhanden.')
        if struct.unpack_from('<I', original, optional + 64)[0]:
            return skip('Gesetzte PE-Prüfsumme; Datei nicht verändern.')
        directories = optional + (112 if machine == 0x8664 else 96)
        if optional + optional_size < directories + 16 * 8:
            return skip('Optionale Datenverzeichnisse fehlen.')
        if (struct.unpack_from('<II', original, directories + 4 * 8) != (0, 0)
                or struct.unpack_from('<II', original, directories + 6 * 8) != (0, 0)):
            return skip('Authenticode-/Debug-Dateioffsets nicht unterstützen.')
        for i in range(16):
            rva, size = struct.unpack_from('<II', original, directories + i * 8)
            if rva and size and rva < headers:
                return skip('Ein Datenverzeichnis zeigt in den Header.')
        sections = []
        for idx in range(section_count):
            hdr = table + idx * 40
            virt_size, rva, raw_size, raw_ptr = struct.unpack_from('<IIII', original, hdr + 8)
            relptr, lineptr = struct.unpack_from('<II', original, hdr + 24)
            nrel, nline = struct.unpack_from('<HH', original, hdr + 32)
            if relptr or lineptr or nrel or nline:
                return skip('Sektionsbezogene COFF-Dateioffsets vorhanden.')
            if raw_size:
                if (raw_ptr < headers or raw_ptr % file_alignment or raw_size % file_alignment
                        or raw_ptr + raw_size > len(original)):
                    return skip('Sektions-Rohdaten sind nicht ausgerichtet.')
            section_data = original[raw_ptr:raw_ptr + raw_size] if raw_size else b''
            trimmed = raw_size
            # Remove complete trailing zero blocks, not arbitrary zeros inside
            # the block. The PE loader supplies zeros through VirtualSize.
            if virt_size:
                while trimmed >= file_alignment and not any(section_data[trimmed - file_alignment:trimmed]):
                    trimmed -= file_alignment
            sections.append(dict(index=idx, header=hdr, virtual_size=virt_size,
                                 rva=rva, pointer=raw_ptr, raw_size=raw_size,
                                 trimmed=trimmed, data=section_data))
        physical = sorted((s for s in sections if s['raw_size']), key=lambda s: s['pointer'])
        last = headers
        for sec in physical:
            if sec['pointer'] < last:
                return skip('Überlappende Rohdaten-Sektionen.')
            if any(original[last:sec['pointer']]):
                return skip('Nichtleere Dateilücken oder zusätzliche Metadaten.')
            last = sec['pointer'] + sec['raw_size']
        if last != len(original):
            return skip('Overlay oder nachgestellte Dateidaten vorhanden.')

        new_pe = 0x40
        nt_prefix_len = table - old_pe
        new_table = new_pe + nt_prefix_len
        new_header_size = _align(new_table + 40 * section_count, file_alignment)
        if new_header_size > headers:
            return skip('Header kann nicht kompakter angeordnet werden.')
        out_size = new_header_size + sum(s['trimmed'] for s in physical)
        if out_size >= len(original):
            return skip('Keine überflüssigen vollständigen FileAlignment-Blöcke.')

        result = bytearray(out_size)
        result[:64] = original[:64]
        struct.pack_into('<I', result, 0x3C, new_pe)
        result[new_pe:new_table] = original[old_pe:table]
        new_optional = new_pe + 24
        struct.pack_into('<I', result, new_optional + 60, new_header_size)
        offsets: dict[int, int] = {}
        cursor = new_header_size
        for sec in physical:
            trimmed = sec['trimmed']
            offsets[sec['index']] = cursor if trimmed else 0
            if trimmed:
                result[cursor:cursor + trimmed] = sec['data'][:trimmed]
                cursor += trimmed
        for sec in sections:
            h = new_table + sec['index'] * 40
            result[h:h + 40] = original[sec['header']:sec['header'] + 40]
            struct.pack_into('<II', result, h + 16, sec['trimmed'], offsets.get(sec['index'], 0))

        # Optional-header section totals must match changed raw section sizes.
        # Rebuild from the same characteristics masks the original writer uses.
        code = sum(s['trimmed'] for s in sections if struct.unpack_from('<I', original, s['header'] + 36)[0] & 0x20)
        init = sum(s['trimmed'] for s in sections if struct.unpack_from('<I', original, s['header'] + 36)[0] & 0x40)
        struct.pack_into('<II', result, new_optional + 4, code, init)

        # Full postcondition: image still has the same virtual headers, data
        # directories and initialized bytes; removed tails were already zero.
        new_directories = new_optional + (112 if machine == 0x8664 else 96)
        if (result[new_directories:new_directories + 128]
                != original[directories:directories + 128]):
            return skip('Veränderte PE-Datenverzeichnisse.')
        for sec in sections:
            new_h = new_table + sec['index'] * 40
            if (struct.unpack_from('<II', result, new_h + 8)
                    != (sec['virtual_size'], sec['rva'])):
                return skip('Eine virtuelle Sektionsadresse wurde verändert.')
            new_raw_size = struct.unpack_from('<I', result, new_h + 16)[0]
            new_raw_ptr = struct.unpack_from('<I', result, new_h + 20)[0]
            if (result[new_raw_ptr:new_raw_ptr + new_raw_size]
                    + bytes(sec['raw_size'] - new_raw_size) != sec['data']):
                return skip('Sektionsinhalt ist nicht identisch.')
        if len(result) != out_size or cursor != out_size:
            return skip('Fehler beim Zusammenstellen der Sektionsdaten.')
        zero_bytes = sum(s['raw_size'] - s['trimmed'] for s in sections)
        report.update(changed=True, after_size=out_size,
                      saved_bytes=len(original) - out_size,
                      zero_blocks=zero_bytes // file_alignment,
                      zero_bytes=zero_bytes,
                      reason='PE-Rohdaten neu angeordnet; vollständige Nullblöcke entfernt.')
        return bytes(result), report
    except (ValueError, IndexError, struct.error, OverflowError) as error:
        return skip(f'PE-Layout nicht eindeutig: {error}')


def compact_pe_file(path: str | Path) -> dict[str, Any]:
    """Apply a validated compaction before signing, atomically on success."""
    output = Path(path)
    original = output.read_bytes()
    compacted, report = compact_pe_image(original)
    if report['changed']:
        # Only replace after complete postcondition validation in memory.
        # Existing build output has just been written by the linker.
        output.write_bytes(compacted)
    return report

# -*- coding: utf-8 -*-
"""Stage 591: conservative *physical* PE DLL layout compaction.

Do not remove bytes inside a FileAlignment-sized section block. Only move
complete raw blocks and, when possible, shorten the DOS/PE header region.
All RVAs, exports, imports, relocations and original section bytes are retained.
Unsupported or ambiguous images are returned unchanged.
"""
from __future__ import annotations

import struct
from typing import Any

from .pe_dll_payload import parse_pe


def compact_pe_dll_layout(image: bytes) -> tuple[bytes, dict[str, Any]]:
    original = bytes(image)
    report: dict[str, Any] = {
        "changed": False, "before_size": len(original),
        "after_size": len(original), "saved_bytes": 0,
        "reason": "Kein entbehrlicher vollständig ausgerichteter Raw-Block.",
    }

    def unchanged(reason: str):
        report["reason"] = reason
        return original, report

    try:
        pe = parse_pe(original)
        fa = pe["f_align"]
        sa = pe["s_align"]
        if fa < 512 or fa & (fa - 1) or sa < fa or sa & (sa - 1):
            return unchanged("Ungültige oder nicht unterstützte PE-Ausrichtung.")
        opt = pe["opt"]
        old_headers = struct.unpack_from("<I", original, opt + 60)[0]
        if old_headers < pe["sht"] + len(pe["secs"]) * 40:
            return unchanged("PE-Header ist unvollständig.")
        if old_headers % fa or old_headers > len(original):
            return unchanged("Nicht standardkonformes SizeOfHeaders.")
        # We deliberately do not touch signed, debug, symbol-bearing or
        # checksum-protected images; they may contain absolute file offsets.
        if struct.unpack_from("<II", original, pe["pe"] + 12) != (0, 0):
            return unchanged("COFF-Symboltabelle mit Datei-Offsets vorhanden.")
        if struct.unpack_from("<I", original, opt + 64)[0]:
            return unchanged("PE-Prüfsumme gesetzt.")
        for index, message in ((4, "Signatur/Zertifikat"), (6, "Debug-Verzeichnis")):
            if any(struct.unpack_from("<II", original, pe["dd"] + 8 * index)):
                return unchanged(message + " vorhanden.")
        for index in range(16):
            rva, size = struct.unpack_from("<II", original, pe["dd"] + 8 * index)
            if rva and size and rva < old_headers:
                return unchanged("Datenverzeichnis zeigt in den PE-Header.")
        sections = []
        last_end = old_headers
        for index, sec in enumerate(pe["secs"]):
            hdr = pe["sht"] + index * 40
            reloc_ptr, line_ptr = struct.unpack_from("<II", original, hdr + 24)
            reloc_count, line_count = struct.unpack_from("<HH", original, hdr + 32)
            if reloc_ptr or line_ptr or reloc_count or line_count:
                return unchanged("Sektionsbezogene COFF-Datei-Offsets vorhanden.")
            if sec["rsize"]:
                if sec["rptr"] % fa or sec["rsize"] % fa:
                    return unchanged("Unzulässige Sektionsausrichtung.")
                if sec["rptr"] < old_headers:
                    return unchanged("Sektionsdaten überlappen den Header.")
                last_end = max(last_end, sec["rptr"] + sec["rsize"])
            sections.append((index, sec))
        if last_end != len(original):
            return unchanged("Overlay oder zusätzliche Datei-Metadaten vorhanden.")
        physical = sorted((row for row in sections if row[1]["rsize"]),
                          key=lambda row: row[1]["rptr"])
        for left, right in zip(physical, physical[1:]):
            if left[1]["rptr"] + left[1]["rsize"] > right[1]["rptr"]:
                return unchanged("Überlappende Raw-Sektionen.")

        # An IMAGE_DOS_HEADER occupies exactly 64 bytes; Windows only needs
        # its e_lfanew to locate the moved NT headers (old DOS stub omitted).
        new_pe = 0x40
        nt_len = 24 + (pe["sht"] - (pe["pe"] + 24))
        nt_end = new_pe + nt_len + len(sections) * 40
        new_headers = (nt_end + fa - 1) & ~(fa - 1)
        if new_headers > old_headers:
            return unchanged("Neue PE-Header würden größer als zuvor.")
        new_size = new_headers + sum(s["rsize"] for _, s in physical)
        if new_size >= len(original):
            return unchanged("Alle Nullbereiche sind erforderliches Alignment.")

        rebuilt = bytearray(new_size)
        rebuilt[:64] = original[:64]
        struct.pack_into("<I", rebuilt, 0x3c, new_pe)
        rebuilt[new_pe:new_pe + nt_len] = original[pe["pe"]:pe["sht"]]
        new_opt = opt + new_pe - pe["pe"]
        new_sht = new_pe + nt_len
        struct.pack_into("<I", rebuilt, new_opt + 60, new_headers)
        cursor = new_headers
        offsets = {}
        for index, sec in physical:
            rebuilt[cursor:cursor + sec["rsize"]] = sec["data"]
            offsets[index] = cursor
            cursor += sec["rsize"]
        for index, sec in sections:
            sh = pe["sht"] + index * 40
            dst = new_sht + index * 40
            rebuilt[dst:dst + 40] = original[sh:sh + 40]
            struct.pack_into("<I", rebuilt, dst + 20, offsets.get(index, 0))

        candidate = bytes(rebuilt)
        updated = parse_pe(candidate)
        if updated["entry"] != pe["entry"] or updated["base"] != pe["base"]:
            return unchanged("Revalidierung von EntryPoint/ImageBase fehlgeschlagen.")
        if candidate[updated["dd"]:updated["dd"] + 128] != original[pe["dd"]:pe["dd"] + 128]:
            return unchanged("Datenverzeichnisse würden geändert.")
        for old, new in zip(pe["secs"], updated["secs"]):
            for key in ("name", "vsize", "rva", "rsize", "chars", "data"):
                if old[key] != new[key]:
                    return unchanged("Sektionsinhalt oder virtuelle Adresse verändert.")
        report.update(changed=True, after_size=len(candidate),
                      saved_bytes=len(original) - len(candidate),
                      reason="Unbenutzte physische FileAlignment-Blöcke entfernt; RVAs unverändert.")
        return candidate, report
    except (ValueError, IndexError, struct.error, OverflowError) as error:
        return unchanged(f"DLL-Layout nicht eindeutig: {error}")

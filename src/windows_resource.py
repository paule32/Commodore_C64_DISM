# -*- coding: utf-8 -*-
"""Internal Microsoft Windows RC/RES/COFF resource compiler.

Stage 150 of d64_dism.  The module intentionally has no dependency on an
external rc.exe, cvtres.exe or windres executable.  It implements the two
binary formats involved in the Microsoft resource tool chain:

    .rc -> .res -> COFF .obj (.rsrc$01/.rsrc$02)

The writer supports IMAGE_FILE_MACHINE_I386 and IMAGE_FILE_MACHINE_AMD64 and
uses the image-relative relocation forms required by resource data entries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import ast
import os
from pathlib import Path
import re
import struct
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union


# ---------------------------------------------------------------------------
# Win32 resource constants
# ---------------------------------------------------------------------------
RT_CURSOR = 1
RT_BITMAP = 2
RT_ICON = 3
RT_MENU = 4
RT_DIALOG = 5
RT_STRING = 6
RT_FONTDIR = 7
RT_FONT = 8
RT_ACCELERATOR = 9
RT_RCDATA = 10
RT_MESSAGETABLE = 11
RT_GROUP_CURSOR = 12
RT_GROUP_ICON = 14
RT_VERSION = 16
RT_DLGINCLUDE = 17
RT_PLUGPLAY = 19
RT_VXD = 20
RT_ANICURSOR = 21
RT_ANIICON = 22
RT_HTML = 23
RT_MANIFEST = 24
RT_TOOLBAR = 241

RESOURCE_TYPES: Dict[str, int] = {
    "CURSOR": RT_CURSOR,
    "BITMAP": RT_BITMAP,
    "ICON": RT_ICON,
    "MENU": RT_MENU,
    "DIALOG": RT_DIALOG,
    "STRINGTABLE": RT_STRING,
    "FONTDIR": RT_FONTDIR,
    "FONT": RT_FONT,
    "ACCELERATORS": RT_ACCELERATOR,
    "RCDATA": RT_RCDATA,
    "MESSAGETABLE": RT_MESSAGETABLE,
    "GROUP_CURSOR": RT_GROUP_CURSOR,
    "GROUP_ICON": RT_GROUP_ICON,
    "VERSIONINFO": RT_VERSION,
    "DLGINCLUDE": RT_DLGINCLUDE,
    "PLUGPLAY": RT_PLUGPLAY,
    "VXD": RT_VXD,
    "ANICURSOR": RT_ANICURSOR,
    "ANIICON": RT_ANIICON,
    "HTML": RT_HTML,
    "MANIFEST": RT_MANIFEST,
    "TOOLBAR": RT_TOOLBAR,
}

# Resource memory flags used by .res files.
MOVEABLE = 0x0010
PURE = 0x0020
PRELOAD = 0x0040
DISCARDABLE = 0x1000
MEMORY_FLAGS = {
    "MOVEABLE": MOVEABLE,
    "FIXED": 0,
    "PURE": PURE,
    "IMPURE": 0,
    "PRELOAD": PRELOAD,
    "LOADONCALL": 0,
    "DISCARDABLE": DISCARDABLE,
}

# Dialog/menu styles commonly found in Microsoft .rc files.  Unknown symbols
# remain usable when supplied by #define.
RC_CONSTANTS: Dict[str, int] = {
    # Languages
    "LANG_NEUTRAL": 0x00, "LANG_INVARIANT": 0x7F, "LANG_ENGLISH": 0x09,
    "LANG_GERMAN": 0x07, "LANG_FRENCH": 0x0C, "LANG_ITALIAN": 0x10,
    "LANG_SPANISH": 0x0A, "LANG_JAPANESE": 0x11,
    "SUBLANG_NEUTRAL": 0x00, "SUBLANG_DEFAULT": 0x01,
    "SUBLANG_SYS_DEFAULT": 0x02, "SUBLANG_ENGLISH_US": 0x01,
    "SUBLANG_GERMAN": 0x01, "SUBLANG_GERMAN_SWISS": 0x02,
    # Window styles
    "WS_OVERLAPPED": 0x00000000, "WS_POPUP": 0x80000000,
    "WS_CHILD": 0x40000000, "WS_MINIMIZE": 0x20000000,
    "WS_VISIBLE": 0x10000000, "WS_DISABLED": 0x08000000,
    "WS_CLIPSIBLINGS": 0x04000000, "WS_CLIPCHILDREN": 0x02000000,
    "WS_MAXIMIZE": 0x01000000, "WS_CAPTION": 0x00C00000,
    "WS_BORDER": 0x00800000, "WS_DLGFRAME": 0x00400000,
    "WS_VSCROLL": 0x00200000, "WS_HSCROLL": 0x00100000,
    "WS_SYSMENU": 0x00080000, "WS_THICKFRAME": 0x00040000,
    "WS_GROUP": 0x00020000, "WS_TABSTOP": 0x00010000,
    "WS_MINIMIZEBOX": 0x00020000, "WS_MAXIMIZEBOX": 0x00010000,
    "WS_OVERLAPPEDWINDOW": 0x00CF0000,
    "WS_EX_DLGMODALFRAME": 0x00000001, "WS_EX_NOPARENTNOTIFY": 0x00000004,
    "WS_EX_TOPMOST": 0x00000008, "WS_EX_ACCEPTFILES": 0x00000010,
    "WS_EX_TRANSPARENT": 0x00000020, "WS_EX_CLIENTEDGE": 0x00000200,
    "WS_EX_CONTEXTHELP": 0x00000400, "WS_EX_RIGHT": 0x00001000,
    "WS_EX_LEFTSCROLLBAR": 0x00004000, "WS_EX_CONTROLPARENT": 0x00010000,
    "WS_EX_STATICEDGE": 0x00020000, "WS_EX_APPWINDOW": 0x00040000,
    # Dialog styles
    "DS_ABSALIGN": 0x0001, "DS_SYSMODAL": 0x0002, "DS_3DLOOK": 0x0004,
    "DS_FIXEDSYS": 0x0008, "DS_NOFAILCREATE": 0x0010, "DS_LOCALEDIT": 0x0020,
    "DS_SETFONT": 0x0040, "DS_MODALFRAME": 0x0080, "DS_NOIDLEMSG": 0x0100,
    "DS_SETFOREGROUND": 0x0200, "DS_CONTROL": 0x0400,
    "DS_CENTER": 0x0800, "DS_CENTERMOUSE": 0x1000, "DS_CONTEXTHELP": 0x2000,
    "DS_SHELLFONT": 0x0048,
    # Button
    "BS_PUSHBUTTON": 0x00000000, "BS_DEFPUSHBUTTON": 0x00000001,
    "BS_CHECKBOX": 0x00000002, "BS_AUTOCHECKBOX": 0x00000003,
    "BS_RADIOBUTTON": 0x00000004, "BS_3STATE": 0x00000005,
    "BS_AUTO3STATE": 0x00000006, "BS_GROUPBOX": 0x00000007,
    "BS_AUTORADIOBUTTON": 0x00000009, "BS_OWNERDRAW": 0x0000000B,
    # Static
    "SS_LEFT": 0x00000000, "SS_CENTER": 0x00000001, "SS_RIGHT": 0x00000002,
    "SS_ICON": 0x00000003, "SS_BITMAP": 0x0000000E,
    "SS_CENTERIMAGE": 0x00000200, "SS_NOTIFY": 0x00000100,
    # Edit/list/combo
    "ES_LEFT": 0x0000, "ES_CENTER": 0x0001, "ES_RIGHT": 0x0002,
    "ES_MULTILINE": 0x0004, "ES_UPPERCASE": 0x0008, "ES_LOWERCASE": 0x0010,
    "ES_PASSWORD": 0x0020, "ES_AUTOVSCROLL": 0x0040, "ES_AUTOHSCROLL": 0x0080,
    "ES_READONLY": 0x0800, "ES_WANTRETURN": 0x1000,
    "LBS_NOTIFY": 0x0001, "LBS_SORT": 0x0002, "LBS_MULTIPLESEL": 0x0008,
    "LBS_NOINTEGRALHEIGHT": 0x0100, "LBS_EXTENDEDSEL": 0x0800,
    "CBS_SIMPLE": 0x0001, "CBS_DROPDOWN": 0x0002, "CBS_DROPDOWNLIST": 0x0003,
    "CBS_OWNERDRAWFIXED": 0x0010, "CBS_SORT": 0x0100,
    # Standard dialog/control IDs and additional common control styles
    "IDOK": 1, "IDCANCEL": 2, "IDABORT": 3, "IDRETRY": 4, "IDIGNORE": 5,
    "IDYES": 6, "IDNO": 7, "IDCLOSE": 8, "IDHELP": 9, "IDC_STATIC": -1,
    "WS_EX_LEFT": 0x00000000, "WS_EX_LTRREADING": 0x00000000,
    "WS_EX_RIGHTSCROLLBAR": 0x00000000, "WS_EX_WINDOWEDGE": 0x00000100,
    "WS_EX_TOOLWINDOW": 0x00000080, "WS_EX_LAYERED": 0x00080000,
    "BS_LEFTTEXT": 0x00000020, "BS_TEXT": 0x00000000, "BS_ICON": 0x00000040,
    "BS_BITMAP": 0x00000080, "BS_LEFT": 0x00000100, "BS_RIGHT": 0x00000200,
    "BS_CENTER": 0x00000300, "BS_TOP": 0x00000400, "BS_BOTTOM": 0x00000800,
    "BS_VCENTER": 0x00000C00, "BS_PUSHLIKE": 0x00001000, "BS_MULTILINE": 0x00002000,
    "BS_NOTIFY": 0x00004000, "BS_FLAT": 0x00008000,
    "SS_BLACKRECT": 0x00000004, "SS_GRAYRECT": 0x00000005, "SS_WHITERECT": 0x00000006,
    "SS_BLACKFRAME": 0x00000007, "SS_GRAYFRAME": 0x00000008, "SS_WHITEFRAME": 0x00000009,
    "SS_SIMPLE": 0x0000000B, "SS_LEFTNOWORDWRAP": 0x0000000C, "SS_OWNERDRAW": 0x0000000D,
    "SS_ETCHEDHORZ": 0x00000010, "SS_ETCHEDVERT": 0x00000011, "SS_ETCHEDFRAME": 0x00000012,
    "SS_NOPREFIX": 0x00000080, "SS_SUNKEN": 0x00001000,
    "ES_NOHIDESEL": 0x0100, "ES_OEMCONVERT": 0x0400, "ES_NUMBER": 0x2000,
    "LBS_HASSTRINGS": 0x0040, "LBS_USETABSTOPS": 0x0080, "LBS_DISABLENOSCROLL": 0x1000,
    "CBS_AUTOHSCROLL": 0x0040, "CBS_OEMCONVERT": 0x0080, "CBS_NOINTEGRALHEIGHT": 0x0400,
    "SBS_HORZ": 0x0000, "SBS_VERT": 0x0001, "SBS_TOPALIGN": 0x0002, "SBS_LEFTALIGN": 0x0002,
    # Menu flags
    "GRAYED": 0x0001, "INACTIVE": 0x0002, "BITMAP": 0x0004,
    "CHECKED": 0x0008, "POPUP": 0x0010, "MENUBARBREAK": 0x0020,
    "MENUBREAK": 0x0040, "END": 0x0080, "OWNERDRAW": 0x0100,
    "HELP": 0x4000, "SEPARATOR": 0x0800,
    "MFT_STRING": 0x00000000, "MFT_BITMAP": 0x00000004,
    "MFT_MENUBARBREAK": 0x00000020, "MFT_MENUBREAK": 0x00000040,
    "MFT_OWNERDRAW": 0x00000100, "MFT_RADIOCHECK": 0x00000200,
    "MFT_SEPARATOR": 0x00000800, "MFT_RIGHTORDER": 0x00002000,
    "MFS_GRAYED": 0x00000003, "MFS_DISABLED": 0x00000003,
    "MFS_CHECKED": 0x00000008, "MFS_HILITE": 0x00000080,
    "MFS_ENABLED": 0x00000000, "MFS_UNCHECKED": 0x00000000,
    # Accelerator flags
    "VIRTKEY": 0x01, "ASCII": 0x00, "NOINVERT": 0x02,
    "SHIFT": 0x04, "CONTROL": 0x08, "ALT": 0x10,
    # Version constants
    "VOS_UNKNOWN": 0x00000000, "VOS_DOS": 0x00010000,
    "VOS_NT": 0x00040000, "VOS__WINDOWS32": 0x00000004,
    "VOS_NT_WINDOWS32": 0x00040004, "VFT_UNKNOWN": 0x00000000,
    "VFT_APP": 0x00000001, "VFT_DLL": 0x00000002, "VFT_DRV": 0x00000003,
    "VFT_FONT": 0x00000004, "VFT_VXD": 0x00000005,
    "VS_FF_DEBUG": 0x00000001, "VS_FF_PRERELEASE": 0x00000002,
    "VS_FF_PATCHED": 0x00000004, "VS_FF_PRIVATEBUILD": 0x00000008,
    "VS_FF_INFOINFERRED": 0x00000010, "VS_FF_SPECIALBUILD": 0x00000020,
}


ResourceId = Union[int, str]


class ResourceCompilerError(Exception):
    def __init__(self, message: str, *, source: str = "", line: int = 0):
        prefix = ""
        if source:
            prefix = source
            if line:
                prefix += f"({line})"
            prefix += ": "
        super().__init__(prefix + message)
        self.source = source
        self.line = int(line or 0)
        self.message = message


@dataclass
class ResourceEntry:
    type_id: ResourceId
    name_id: ResourceId
    data: bytes
    language: int = 0x0409
    data_version: int = 0
    memory_flags: int = MOVEABLE | PURE
    version: int = 0
    characteristics: int = 0
    codepage: int = 0
    source: str = ""

    def key(self):
        return (self.type_id, self.name_id, self.language)


@dataclass
class ResourceCompilation:
    entries: List[ResourceEntry] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# .RES reader/writer
# ---------------------------------------------------------------------------
def _align(value: int, boundary: int) -> int:
    return (int(value) + boundary - 1) & ~(boundary - 1)


def _pad(data: bytearray, boundary: int = 4) -> None:
    data.extend(b"\0" * ((_align(len(data), boundary) - len(data)) % boundary))


def _put_name_or_ordinal(out: bytearray, value: ResourceId) -> None:
    if isinstance(value, int):
        if not (0 <= value <= 0xFFFF):
            raise ResourceCompilerError(f"Resource-ID außerhalb WORD-Bereich: {value}")
        out += struct.pack("<HH", 0xFFFF, value)
    else:
        text = str(value)
        out += text.encode("utf-16le") + b"\0\0"


def _read_name_or_ordinal(blob: bytes, pos: int, limit: int) -> Tuple[ResourceId, int]:
    if pos + 2 > limit:
        raise ResourceCompilerError("Beschädigter .res-Header (Name/Ordinal fehlt)")
    first = struct.unpack_from("<H", blob, pos)[0]
    if first == 0xFFFF:
        if pos + 4 > limit:
            raise ResourceCompilerError("Beschädigter .res-Ordinalwert")
        return struct.unpack_from("<H", blob, pos + 2)[0], pos + 4
    chars: List[int] = []
    while True:
        if pos + 2 > limit:
            raise ResourceCompilerError("Nicht terminierter UTF-16-Name im .res-Header")
        ch = struct.unpack_from("<H", blob, pos)[0]
        pos += 2
        if ch == 0:
            break
        chars.append(ch)
    raw = b"".join(struct.pack("<H", ch) for ch in chars)
    return raw.decode("utf-16le", errors="replace"), pos


def _res_record(entry: ResourceEntry) -> bytes:
    variable = bytearray()
    _put_name_or_ordinal(variable, entry.type_id)
    _put_name_or_ordinal(variable, entry.name_id)
    # Alignment is relative to start of full header, which already has 8 bytes.
    while (8 + len(variable)) % 4:
        variable.append(0)
    variable += struct.pack(
        "<IHHII",
        entry.data_version & 0xFFFFFFFF,
        entry.memory_flags & 0xFFFF,
        entry.language & 0xFFFF,
        entry.version & 0xFFFFFFFF,
        entry.characteristics & 0xFFFFFFFF,
    )
    header_size = 8 + len(variable)
    out = bytearray(struct.pack("<II", len(entry.data), header_size))
    out += variable
    out += entry.data
    _pad(out, 4)
    return bytes(out)


def write_res(entries: Iterable[ResourceEntry]) -> bytes:
    """Write Microsoft Win32 .res bytes, including the mandatory null entry."""
    out = bytearray()
    null_entry = ResourceEntry(0, 0, b"", language=0, memory_flags=0)
    out += _res_record(null_entry)
    for entry in entries:
        out += _res_record(entry)
    return bytes(out)


def read_res(data_or_path: Union[bytes, bytearray, memoryview, str, os.PathLike]) -> List[ResourceEntry]:
    if isinstance(data_or_path, (str, os.PathLike)):
        blob = Path(data_or_path).read_bytes()
    else:
        blob = bytes(data_or_path)
    entries: List[ResourceEntry] = []
    pos = 0
    while pos < len(blob):
        if pos + 8 > len(blob):
            # legal trailing zero padding
            if any(blob[pos:]):
                raise ResourceCompilerError("Abgeschnittener .res-Datensatz")
            break
        data_size, header_size = struct.unpack_from("<II", blob, pos)
        if header_size < 16 or pos + header_size > len(blob):
            raise ResourceCompilerError(f"Ungültige .res-Headergröße {header_size} bei Offset 0x{pos:X}")
        hpos = pos + 8
        hend = pos + header_size
        type_id, hpos = _read_name_or_ordinal(blob, hpos, hend)
        name_id, hpos = _read_name_or_ordinal(blob, hpos, hend)
        hpos = _align(hpos, 4)
        if hpos + 16 > hend:
            raise ResourceCompilerError("Unvollständiger fester .res-Header")
        data_version, memory_flags, language, version, characteristics = struct.unpack_from(
            "<IHHII", blob, hpos
        )
        dpos = pos + header_size
        dend = dpos + data_size
        if dend > len(blob):
            raise ResourceCompilerError("Abgeschnittene Ressourcendaten in .res-Datei")
        if not (data_size == 0 and type_id == 0 and name_id == 0):
            entries.append(
                ResourceEntry(
                    type_id=type_id,
                    name_id=name_id,
                    data=blob[dpos:dend],
                    language=language,
                    data_version=data_version,
                    memory_flags=memory_flags,
                    version=version,
                    characteristics=characteristics,
                )
            )
        pos = _align(dend, 4)
    return entries


def save_res(path: Union[str, os.PathLike], entries: Iterable[ResourceEntry]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(write_res(entries))
    return target


# ---------------------------------------------------------------------------
# COFF resource object writer
# ---------------------------------------------------------------------------
IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_FILE_MACHINE_AMD64 = 0x8664
IMAGE_REL_I386_DIR32NB = 0x0007
IMAGE_REL_AMD64_ADDR32NB = 0x0003
IMAGE_SCN_CNT_INITIALIZED_DATA = 0x00000040
IMAGE_SCN_ALIGN_4BYTES = 0x00300000
IMAGE_SCN_MEM_READ = 0x40000000


def _resource_sort_key(value: ResourceId):
    return (0, str(value).casefold(), str(value)) if isinstance(value, str) else (1, int(value), "")


def _build_resource_sections(entries: Sequence[ResourceEntry]) -> Tuple[bytes, bytes, List[int]]:
    """Return .rsrc$01, .rsrc$02 and relocation offsets in section 1."""
    tree: Dict[ResourceId, Dict[ResourceId, Dict[int, ResourceEntry]]] = {}
    for entry in entries:
        lang = int(entry.language) & 0xFFFF
        names = tree.setdefault(entry.type_id, {})
        languages = names.setdefault(entry.name_id, {})
        if lang in languages:
            raise ResourceCompilerError(
                f"Doppelte Ressource Typ={entry.type_id!r}, Name={entry.name_id!r}, Sprache=0x{lang:04X}"
            )
        languages[lang] = entry

    directory = bytearray()
    raw = bytearray()
    relocation_offsets: List[int] = []

    def alloc(size: int, alignment: int = 4) -> int:
        while len(directory) % alignment:
            directory.append(0)
        off = len(directory)
        directory.extend(b"\0" * size)
        return off

    def alloc_name(text: str) -> int:
        encoded = str(text).encode("utf-16le")
        count = len(encoded) // 2
        if count > 0xFFFF:
            raise ResourceCompilerError("Resource-Name ist zu lang")
        off = alloc(2 + len(encoded), 2)
        struct.pack_into("<H", directory, off, count)
        directory[off + 2 : off + 2 + len(encoded)] = encoded
        return off

    def append_raw(blob: bytes) -> int:
        while len(raw) % 4:
            raw.append(0)
        off = len(raw)
        raw.extend(blob)
        return off

    def emit_dir(node: Mapping, level: int) -> int:
        keys = sorted(node.keys(), key=_resource_sort_key)
        named = [k for k in keys if isinstance(k, str)]
        ids = [k for k in keys if not isinstance(k, str)]
        ordered = named + ids
        off = alloc(16 + 8 * len(ordered), 4)
        struct.pack_into("<IIHHHH", directory, off, 0, 0, 0, 0, len(named), len(ids))
        for i, key in enumerate(ordered):
            ent_off = off + 16 + i * 8
            if isinstance(key, str):
                name_off = alloc_name(key)
                name_field = 0x80000000 | name_off
            else:
                name_field = int(key) & 0xFFFF
            child = node[key]
            if level < 2:
                child_off = emit_dir(child, level + 1)
                data_field = 0x80000000 | child_off
            else:
                # language level -> IMAGE_RESOURCE_DATA_ENTRY
                resource: ResourceEntry = child
                data_off = alloc(16, 4)
                raw_off = append_raw(resource.data)
                # Linker applies ADDR32NB/DIR32NB against .rsrc$02 and adds raw_off.
                struct.pack_into(
                    "<IIII", directory, data_off,
                    raw_off & 0xFFFFFFFF,
                    len(resource.data) & 0xFFFFFFFF,
                    int(resource.codepage) & 0xFFFFFFFF,
                    0,
                )
                relocation_offsets.append(data_off)
                data_field = data_off
            struct.pack_into("<II", directory, ent_off, name_field, data_field)
        return off

    emit_dir(tree, 0)
    _pad(directory, 4)
    _pad(raw, 4)
    return bytes(directory), bytes(raw), relocation_offsets


def _coff_section_symbol(name: bytes, section_number: int, length: int, reloc_count: int) -> bytes:
    name8 = name[:8].ljust(8, b"\0")
    # IMAGE_SYMBOL + IMAGE_AUX_SYMBOL_SECTION_DEF (18 + 18 bytes)
    sym = struct.pack("<8sIhHBB", name8, 0, section_number, 0, 3, 1)
    aux = struct.pack("<IHHIhBBH", length, reloc_count, 0, 0, 0, 0, 0, 0)
    return sym + aux


def write_resource_coff(
    entries: Iterable[ResourceEntry],
    *,
    machine: Union[str, int] = "x86",
    timestamp: int = 0,
) -> bytes:
    items = list(entries)
    sec1, sec2, reloc_offsets = _build_resource_sections(items)
    if isinstance(machine, str):
        key = machine.strip().lower().replace("-", "")
        if key in {"x86", "i386", "386", "pe32", "win32"}:
            machine_id = IMAGE_FILE_MACHINE_I386
            reloc_type = IMAGE_REL_I386_DIR32NB
        elif key in {"x64", "amd64", "x8664", "pe64", "pe32+", "win64"}:
            machine_id = IMAGE_FILE_MACHINE_AMD64
            reloc_type = IMAGE_REL_AMD64_ADDR32NB
        else:
            raise ResourceCompilerError(f"Unbekannte COFF-Zielarchitektur: {machine}")
    else:
        machine_id = int(machine)
        if machine_id == IMAGE_FILE_MACHINE_I386:
            reloc_type = IMAGE_REL_I386_DIR32NB
        elif machine_id == IMAGE_FILE_MACHINE_AMD64:
            reloc_type = IMAGE_REL_AMD64_ADDR32NB
        else:
            raise ResourceCompilerError(f"Nicht unterstützte COFF-Machine 0x{machine_id:04X}")

    if len(reloc_offsets) > 0xFFFF:
        raise ResourceCompilerError("Zu viele Resource-Relocations für einen COFF-Abschnitt")

    header_size = 20 + 2 * 40
    p1 = header_size
    pr1 = _align(p1 + len(sec1), 4)
    p2 = _align(pr1 + len(reloc_offsets) * 10, 4)
    psym = _align(p2 + len(sec2), 4)

    characteristics = IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_ALIGN_4BYTES | IMAGE_SCN_MEM_READ
    coff = bytearray()
    coff += struct.pack(
        "<HHIIIHH",
        machine_id,
        2,
        int(timestamp) & 0xFFFFFFFF,
        psym,
        4,  # two section symbols, each with one aux record
        0,
        0,
    )
    coff += struct.pack(
        "<8sIIIIIIHHI",
        b".rsrc$01", 0, 0, len(sec1), p1, pr1 if reloc_offsets else 0, 0,
        len(reloc_offsets), 0, characteristics,
    )
    coff += struct.pack(
        "<8sIIIIIIHHI",
        b".rsrc$02", 0, 0, len(sec2), p2, 0, 0, 0, 0, characteristics,
    )
    if len(coff) != header_size:
        raise AssertionError("interner COFF-Headerfehler")
    coff += sec1
    while len(coff) < pr1:
        coff.append(0)
    if reloc_offsets:
        # .rsrc$02 section symbol is symbol-table index 2 (index 0 + aux 1 precede it).
        for virtual_address in reloc_offsets:
            coff += struct.pack("<IIH", virtual_address, 2, reloc_type)
    while len(coff) < p2:
        coff.append(0)
    coff += sec2
    while len(coff) < psym:
        coff.append(0)
    coff += _coff_section_symbol(b".rsrc$01", 1, len(sec1), len(reloc_offsets))
    coff += _coff_section_symbol(b".rsrc$02", 2, len(sec2), 0)
    coff += struct.pack("<I", 4)  # empty COFF string table
    return bytes(coff)


def save_resource_coff(path: Union[str, os.PathLike], entries: Iterable[ResourceEntry], *, machine="x86") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(write_resource_coff(entries, machine=machine))
    return target


# ---------------------------------------------------------------------------
# RC preprocessor / lexer
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    line: int


_TOKEN_RE = re.compile(
    r'''(?P<SPACE>[ \t\f\v]+)|(?P<COMMENT>//[^\n]*|/\*.*?\*/)|'''
    r'''(?P<NEWLINE>\r?\n)|(?P<WSTRING>L"(?:\\.|[^"\\])*")|'''
    r'''(?P<STRING>"(?:\\.|[^"\\])*")|'''
    r'''(?P<NUMBER>0[xX][0-9A-Fa-f]+[uUlL]*|\d+[uUlL]*)|'''
    r'''(?P<IDENT>[A-Za-z_$][A-Za-z0-9_$@.]*)|'''
    r'''(?P<OP><<|>>|<=|>=|==|!=|\|\||&&|[{}(),|&~+\-*/%^<>!=])''',
    re.S,
)


def _decode_c_string(raw: str) -> str:
    if raw.startswith('L"'):
        raw = raw[1:]
    try:
        return ast.literal_eval(raw)
    except Exception:
        body = raw[1:-1]
        return bytes(body, "utf-8").decode("unicode_escape")


def _tokenize(text: str, source: str = "") -> List[_Token]:
    result: List[_Token] = []
    pos = 0
    line = 1
    for match in _TOKEN_RE.finditer(text):
        if match.start() != pos:
            bad = text[pos:match.start()]
            if bad.strip():
                raise ResourceCompilerError(f"Unbekanntes RC-Zeichen {bad[:20]!r}", source=source, line=line)
            line += bad.count("\n")
        kind = match.lastgroup or ""
        value = match.group(0)
        token_line = line
        line += value.count("\n")
        pos = match.end()
        if kind in {"SPACE", "COMMENT"}:
            continue
        if kind in {"STRING", "WSTRING"}:
            result.append(_Token(kind, _decode_c_string(value), token_line))
        else:
            result.append(_Token(kind, value, token_line))
    if pos != len(text):
        bad = text[pos:]
        if bad.strip():
            raise ResourceCompilerError(f"Unbekannter RC-Text {bad[:30]!r}", source=source, line=line)
    result.append(_Token("EOF", "", line))
    return result


class _ExprEvaluator(ast.NodeVisitor):
    def __init__(self, symbols: Mapping[str, int]):
        self.symbols = {str(k).upper(): int(v) for k, v in symbols.items() if isinstance(v, int)}

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node.value, int):
            return node.value
        raise ValueError("non-integer constant")

    def visit_Name(self, node):
        key = node.id.upper()
        if key not in self.symbols:
            raise ValueError(f"Unbekanntes Symbol {node.id}")
        return self.symbols[key]

    _bin = {
        ast.BitOr: lambda a,b: a|b, ast.BitAnd: lambda a,b:a&b,
        ast.BitXor: lambda a,b:a^b, ast.LShift: lambda a,b:a<<b,
        ast.RShift: lambda a,b:a>>b, ast.Add: lambda a,b:a+b,
        ast.Sub: lambda a,b:a-b, ast.Mult: lambda a,b:a*b,
        ast.FloorDiv: lambda a,b:a//b, ast.Mod: lambda a,b:a%b,
    }
    _unary = {ast.Invert: lambda a:~a, ast.UAdd: lambda a:+a, ast.USub: lambda a:-a, ast.Not: lambda a:int(not a)}
    _cmp = {ast.Eq:lambda a,b:a==b, ast.NotEq:lambda a,b:a!=b, ast.Lt:lambda a,b:a<b,
            ast.LtE:lambda a,b:a<=b, ast.Gt:lambda a,b:a>b, ast.GtE:lambda a,b:a>=b}

    def visit_BinOp(self,node):
        fn=self._bin.get(type(node.op));
        if fn is None: raise ValueError("operator")
        return fn(self.visit(node.left),self.visit(node.right))
    def visit_UnaryOp(self,node):
        fn=self._unary.get(type(node.op));
        if fn is None: raise ValueError("operator")
        return fn(self.visit(node.operand))
    def visit_BoolOp(self,node):
        vals=[bool(self.visit(v)) for v in node.values]
        return int(all(vals) if isinstance(node.op,ast.And) else any(vals))
    def visit_Compare(self,node):
        left=self.visit(node.left)
        for op,right_node in zip(node.ops,node.comparators):
            right=self.visit(right_node); fn=self._cmp.get(type(op))
            if fn is None or not fn(left,right): return 0
            left=right
        return 1
    def generic_visit(self,node):
        raise ValueError(f"unsupported expression {type(node).__name__}")


def eval_rc_expression(text: str, symbols: Mapping[str, int]) -> int:
    expr = str(text).strip()
    expr = re.sub(r"\b(0[xX][0-9A-Fa-f]+|\d+)[uUlL]+\b", r"\1", expr)
    expr = expr.replace("&&", " and ").replace("||", " or ")
    # unary ! but not !=
    expr = re.sub(r"!(?!=)", " not ", expr)
    try:
        tree = ast.parse(expr, mode="eval")
        return int(_ExprEvaluator(symbols).visit(tree))
    except Exception as exc:
        raise ResourceCompilerError(f"Ungültiger RC-Ausdruck {text!r}: {exc}") from exc


def _preprocess_file(
    path: Path,
    *,
    defines: Optional[MutableMapping[str, Union[int, str]]] = None,
    include_dirs: Sequence[Union[str, os.PathLike]] = (),
    stack: Optional[List[Path]] = None,
) -> Tuple[str, Dict[str, Union[int, str]], List[str]]:
    path = Path(path).expanduser().resolve()
    symbols: Dict[str, Union[int, str]] = dict(RC_CONSTANTS)
    if defines:
        symbols.update({str(k): v for k,v in defines.items()})
    dependencies: List[str] = []
    stack = list(stack or [])
    if path in stack:
        raise ResourceCompilerError("Zyklisches #include: " + " -> ".join(map(str, stack+[path])))
    stack.append(path)

    def resolve_include(name: str) -> Path:
        candidates = [path.parent / name] + [Path(d) / name for d in include_dirs]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        # d64_dism carries the Win32 constants needed by ordinary .rc files,
        # so classic SDK umbrella headers do not require an external SDK.
        if Path(name).name.casefold() in {
            "windows.h", "winuser.h", "winres.h", "winresrc.h",
            "afxres.h", "commctrl.h", "prsht.h",
        }:
            return Path("__d64_builtin__") / Path(name).name
        raise ResourceCompilerError(f"Include-Datei nicht gefunden: {name}", source=str(path))

    raw_source = path.read_bytes()
    if raw_source.startswith((b"\xff\xfe", b"\xfe\xff")):
        source = raw_source.decode("utf-16")
    elif raw_source.startswith(b"\xef\xbb\xbf"):
        source = raw_source.decode("utf-8-sig")
    else:
        try:
            source = raw_source.decode("utf-8")
        except UnicodeDecodeError:
            source = raw_source.decode("cp1252")
    source = re.sub(r"\\\r?\n", "", source)  # C preprocessor continuation
    output: List[str] = []
    active_stack: List[Tuple[bool, bool]] = []  # parent-active, branch-taken/current helper
    active = True
    is_header = path.suffix.lower() in {".h", ".hpp", ".hh", ".hxx"}

    lines = source.splitlines(True)
    for lineno, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            if active and not is_header:
                output.append(line)
            else:
                output.append("\n" if line.endswith("\n") else "")
            continue
        directive = stripped[1:].strip()
        keyword, _, rest = directive.partition(" ")
        keyword = keyword.lower()
        rest = rest.strip()
        if keyword in {"ifdef", "ifndef", "if"}:
            parent = active
            if keyword == "ifdef":
                cond = rest in symbols
            elif keyword == "ifndef":
                cond = rest not in symbols
            else:
                numeric = {k:int(v) for k,v in symbols.items() if isinstance(v,int)}
                expr = re.sub(r"defined\s*\(\s*([A-Za-z_$][\w$@.]*)\s*\)", lambda m: "1" if m.group(1) in symbols else "0", rest)
                expr = re.sub(r"defined\s+([A-Za-z_$][\w$@.]*)", lambda m: "1" if m.group(1) in symbols else "0", expr)
                try: cond = bool(eval_rc_expression(expr, numeric))
                except ResourceCompilerError: cond = False
            active_stack.append((parent, bool(cond)))
            active = parent and bool(cond)
        elif keyword == "else":
            if not active_stack:
                raise ResourceCompilerError("#else ohne #if", source=str(path), line=lineno)
            parent, first_cond = active_stack[-1]
            active = parent and not first_cond
            active_stack[-1] = (parent, True)
        elif keyword == "elif":
            if not active_stack:
                raise ResourceCompilerError("#elif ohne #if", source=str(path), line=lineno)
            parent, already = active_stack[-1]
            if already:
                active = False
            else:
                numeric = {k:int(v) for k,v in symbols.items() if isinstance(v,int)}
                cond = bool(eval_rc_expression(rest, numeric))
                active = parent and cond
                active_stack[-1] = (parent, cond)
        elif keyword == "endif":
            if not active_stack:
                raise ResourceCompilerError("#endif ohne #if", source=str(path), line=lineno)
            parent, _ = active_stack.pop()
            active = parent
        elif active and keyword == "define":
            m = re.match(r"([A-Za-z_$][\w$@.]*)(?:\s+(.*))?$", rest)
            if m and "(" not in m.group(1):
                name, value = m.group(1), (m.group(2) or "1").strip()
                value = re.sub(r"//.*$", "", value).strip()
                numeric = {k:int(v) for k,v in symbols.items() if isinstance(v,int)}
                try:
                    symbols[name] = eval_rc_expression(value, numeric)
                except ResourceCompilerError:
                    if value.startswith('"') and value.endswith('"'):
                        symbols[name] = _decode_c_string(value)
                    else:
                        # Keep alias text if it resolves later in RC lexer.
                        symbols[name] = value
        elif active and keyword == "undef":
            symbols.pop(rest.split()[0] if rest else "", None)
        elif active and keyword == "pragma":
            # Stage 154: preserve code_page in token order for the internal RC
            # parser. This lets each following resource carry a PE CodePage
            # value while the source remains valid RC syntax.
            m = re.match(r"code_page\s*\(\s*(0[xX][0-9A-Fa-f]+|\d+)\s*\)", rest, re.IGNORECASE)
            if m:
                output.append(f"D64_CODEPAGE {int(m.group(1), 0)}\n")
                continue
        elif active and keyword == "include":
            m = re.match(r'[<"]([^>"]+)[>"]', rest)
            if not m:
                raise ResourceCompilerError("Ungültiges #include", source=str(path), line=lineno)
            inc = resolve_include(m.group(1))
            if "__d64_builtin__" in inc.parts:
                output.append("\n" if line.endswith("\n") else "")
                continue
            dependencies.append(str(inc))
            inc_text, inc_defs, inc_deps = _preprocess_file(
                inc, defines=symbols, include_dirs=include_dirs, stack=stack
            )
            symbols.update(inc_defs)
            dependencies.extend(inc_deps)
            if inc.suffix.lower() not in {".h", ".hpp", ".hh", ".hxx"}:
                output.append(inc_text)
        # Other directives (#pragma, #line, code_page) are intentionally harmless.
        output.append("\n" if line.endswith("\n") else "")
    if active_stack:
        raise ResourceCompilerError("Nicht abgeschlossenes #if/#ifdef", source=str(path))
    return "".join(output), symbols, dependencies


class _Stream:
    def __init__(self, tokens: Sequence[_Token], symbols: Mapping[str, Union[int,str]], source: str):
        self.tokens = list(tokens)
        self.i = 0
        self.symbols = dict(symbols)
        self.source = source

    def peek(self, n=0):
        return self.tokens[min(self.i+n, len(self.tokens)-1)]

    def pop(self):
        tok=self.peek(); self.i=min(self.i+1,len(self.tokens)-1); return tok

    def skip_nl(self):
        while self.peek().kind == "NEWLINE": self.pop()

    def is_value(self, value: str, n=0):
        return self.peek(n).value.upper() == value.upper()

    def accept(self, value: str):
        if self.is_value(value): return self.pop()
        return None

    def expect(self, value: str):
        tok=self.pop()
        if tok.value.upper()!=value.upper():
            raise ResourceCompilerError(f"Erwartet {value!r}, erhalten {tok.value!r}",source=self.source,line=tok.line)
        return tok

    def error(self, message: str, tok: Optional[_Token]=None):
        t=tok or self.peek(); raise ResourceCompilerError(message,source=self.source,line=t.line)

    def line_tokens(self) -> List[_Token]:
        out=[]
        while self.peek().kind not in {"NEWLINE","EOF"}: out.append(self.pop())
        if self.peek().kind=="NEWLINE": self.pop()
        return out

    def collect_until_comma_or_nl(self) -> List[_Token]:
        out=[]; depth=0
        while True:
            t=self.peek()
            if t.kind in {"EOF","NEWLINE"} and depth==0: break
            if t.value=="," and depth==0: break
            if t.value=="(": depth+=1
            elif t.value==")" and depth: depth-=1
            out.append(self.pop())
        return out

    def expr(self, toks: Sequence[_Token]) -> int:
        if not toks: self.error("Leerer numerischer Ausdruck")
        parts=[]
        for t in toks:
            if t.kind=="IDENT":
                if t.value.upper() == "NOT":
                    parts.append("~")
                    continue
                val=self.symbols.get(t.value, self.symbols.get(t.value.upper()))
                if isinstance(val,int): parts.append(str(val))
                elif isinstance(val,str): parts.append(val)
                else: parts.append(t.value)
            elif t.kind=="NUMBER": parts.append(re.sub(r"[uUlL]+$","",t.value))
            else: parts.append(t.value)
        numeric={k:int(v) for k,v in self.symbols.items() if isinstance(v,int)}
        return eval_rc_expression(" ".join(parts),numeric)

    def expr_to_comma(self) -> int:
        toks=self.collect_until_comma_or_nl(); return self.expr(toks)

    def id_value(self, tok: Optional[_Token]=None) -> ResourceId:
        tok=tok or self.pop()
        if tok.kind in {"STRING","WSTRING"}: return tok.value
        if tok.kind=="NUMBER": return int(re.sub(r"[uUlL]+$","",tok.value),0)
        if tok.kind=="IDENT":
            val=self.symbols.get(tok.value, self.symbols.get(tok.value.upper()))
            if isinstance(val,int): return val
            if isinstance(val,str):
                try: return eval_rc_expression(val,{k:int(v) for k,v in self.symbols.items() if isinstance(v,int)})
                except Exception: return val
            return tok.value
        self.error("Resource-ID erwartet",tok)
        return 0


# ---------------------------------------------------------------------------
# RC binary template helpers
# ---------------------------------------------------------------------------
def _utf16z(text: str) -> bytes:
    return str(text).encode("utf-16le") + b"\0\0"


def _template_name(value: Optional[ResourceId]) -> bytes:
    if value is None or value == "": return b"\0\0"
    if isinstance(value,int): return struct.pack("<HH",0xFFFF,value&0xFFFF)
    return _utf16z(str(value))


def _pack_menu_standard(items: list) -> bytes:
    out=bytearray(struct.pack("<HH",0,0))
    def rec(children):
        for index,item in enumerate(children):
            is_last=index==len(children)-1
            flags=int(item.get("flags",0)) | (0x80 if is_last else 0)
            if item["kind"]=="popup":
                flags |= 0x10
                out.extend(struct.pack("<H",flags&0xFFFF)); out.extend(_utf16z(item.get("text","")))
                rec(item.get("children",[]))
            else:
                out.extend(struct.pack("<HH",flags&0xFFFF,int(item.get("id",0))&0xFFFF)); out.extend(_utf16z(item.get("text","")))
    rec(items)
    return bytes(out)


def _pack_menuex(items: list, help_id: int=0) -> bytes:
    out=bytearray(struct.pack("<HHI",1,4,help_id&0xFFFFFFFF))
    def align4():
        while len(out)%4: out.append(0)
    def rec(children):
        for index,item in enumerate(children):
            align4(); is_last=index==len(children)-1
            popup=item["kind"]=="popup"
            resinfo=(0x01 if popup else 0)|(0x80 if is_last else 0)
            out.extend(struct.pack("<IIIH",int(item.get("type",0))&0xFFFFFFFF,int(item.get("state",0))&0xFFFFFFFF,int(item.get("id",0))&0xFFFFFFFF,resinfo))
            out.extend(_utf16z(item.get("text",""))); align4()
            if popup:
                out.extend(struct.pack("<I",int(item.get("help",0))&0xFFFFFFFF)); rec(item.get("children",[]))
    rec(items); return bytes(out)


_CONTROL_DEFAULTS = {
    "LTEXT": (0x82, 0x50000000 | 0x00000000),
    "CTEXT": (0x82, 0x50000000 | 0x00000001),
    "RTEXT": (0x82, 0x50000000 | 0x00000002),
    "ICON": (0x82, 0x50000000 | 0x00000003),
    "PUSHBUTTON": (0x80, 0x50010000 | 0x00000000),
    "DEFPUSHBUTTON": (0x80, 0x50010000 | 0x00000001),
    "CHECKBOX": (0x80, 0x50010000 | 0x00000002),
    "AUTOCHECKBOX": (0x80, 0x50010000 | 0x00000003),
    "RADIOBUTTON": (0x80, 0x50010000 | 0x00000004),
    "AUTORADIOBUTTON": (0x80, 0x50010000 | 0x00000009),
    "GROUPBOX": (0x80, 0x50000000 | 0x00000007),
    "EDITTEXT": (0x81, 0x50810000),
    "LISTBOX": (0x83, 0x50810001),
    "COMBOBOX": (0x85, 0x50210000),
    "SCROLLBAR": (0x84, 0x50000000),
}


def _pack_dialog(info: dict, extended: bool) -> bytes:
    controls=info.get("controls",[]); style=int(info.get("style",0)); exstyle=int(info.get("exstyle",0))
    x,y,cx,cy=[int(v) for v in info["rect"]]
    out=bytearray()
    if extended:
        out += struct.pack("<HHIIIHhhhh",1,0xFFFF,int(info.get("help",0)),exstyle,style,len(controls),x,y,cx,cy)
    else:
        out += struct.pack("<IIHhhhh",style,exstyle,len(controls),x,y,cx,cy)
    out += _template_name(info.get("menu")); out += _template_name(info.get("class")); out += _utf16z(info.get("caption",""))
    if style & 0x40 or info.get("font"):
        font=info.get("font") or {}; out += struct.pack("<H",int(font.get("size",8))&0xFFFF)
        if extended:
            out += struct.pack("<HBB",int(font.get("weight",400))&0xFFFF,int(font.get("italic",0))&0xFF,int(font.get("charset",1))&0xFF)
        out += _utf16z(font.get("face","MS Shell Dlg"))
    for c in controls:
        while len(out)%4: out.append(0)
        if extended:
            out += struct.pack("<IIIhhhhI",int(c.get("help",0)),int(c.get("exstyle",0)),int(c.get("style",0)),int(c["x"]),int(c["y"]),int(c["cx"]),int(c["cy"]),int(c.get("id",0))&0xFFFFFFFF)
        else:
            out += struct.pack("<IIhhhhH",int(c.get("style",0)),int(c.get("exstyle",0)),int(c["x"]),int(c["y"]),int(c["cx"]),int(c["cy"]),int(c.get("id",0))&0xFFFF)
        out += _template_name(c.get("class")); out += _template_name(c.get("text")); out += struct.pack("<H",0)
    return bytes(out)


def _version_block(key: str, *, value: bytes=b"", value_length: Optional[int]=None, value_type: int=0, children: Sequence[bytes]=()) -> bytes:
    out=bytearray(b"\0\0\0\0\0\0")
    out += _utf16z(key); _pad(out,4)
    out += value; _pad(out,4)
    for child in children: out += child; _pad(out,4)
    total=len(out)
    if value_length is None: value_length=len(value) if value_type==0 else len(value)//2
    struct.pack_into("<HHH",out,0,total,value_length,value_type)
    return bytes(out)


def _pack_version_info(fixed: dict, nodes: list) -> bytes:
    fv=fixed.get("FILEVERSION",(0,0,0,0)); pv=fixed.get("PRODUCTVERSION",fv)
    def ms(v): return ((int(v[0])&0xFFFF)<<16)|(int(v[1])&0xFFFF)
    def ls(v): return ((int(v[2])&0xFFFF)<<16)|(int(v[3])&0xFFFF)
    ffi=struct.pack("<13I",0xFEEF04BD,0x00010000,ms(fv),ls(fv),ms(pv),ls(pv),int(fixed.get("FILEFLAGSMASK",0x3F)),int(fixed.get("FILEFLAGS",0)),int(fixed.get("FILEOS",0x00040004)),int(fixed.get("FILETYPE",1)),int(fixed.get("FILESUBTYPE",0)),0,0)
    def encode_node(node):
        kind=node[0]
        if kind=="BLOCK":
            return _version_block(node[1],value_type=1,children=[encode_node(c) for c in node[2]])
        key,vals=node[1],node[2]
        if vals and isinstance(vals[0],str):
            text="".join(str(v) for v in vals); raw=_utf16z(text)
            return _version_block(key,value=raw,value_length=len(raw)//2,value_type=1)
        raw=b"".join(struct.pack("<H",int(v)&0xFFFF) for v in vals)
        return _version_block(key,value=raw,value_length=len(raw),value_type=0)
    children=[encode_node(n) for n in nodes]
    return _version_block("VS_VERSION_INFO",value=ffi,value_length=len(ffi),value_type=0,children=children)


def _parse_icon_container(blob: bytes, *, cursor: bool=False):
    if len(blob)<6: raise ResourceCompilerError("ICON/CURSOR-Datei ist zu kurz")
    reserved,typ,count=struct.unpack_from("<HHH",blob,0)
    expected=2 if cursor else 1
    if reserved!=0 or typ!=expected: raise ResourceCompilerError("Ungültiger ICO/CUR-Header")
    if len(blob)<6+16*count: raise ResourceCompilerError("Abgeschnittenes ICO/CUR-Verzeichnis")
    result=[]
    for i in range(count):
        w,h,colors,resv,p1,p2,size,off=struct.unpack_from("<BBBBHHII",blob,6+16*i)
        if off+size>len(blob): raise ResourceCompilerError("ICO/CUR-Bilddaten außerhalb Datei")
        result.append((w,h,colors,resv,p1,p2,size,blob[off:off+size]))
    return result


# ---------------------------------------------------------------------------
# Main RC parser
# ---------------------------------------------------------------------------
class ResourceScriptCompiler:
    def __init__(self, *, include_dirs: Sequence[Union[str,os.PathLike]]=(), defines: Optional[Mapping[str,Union[int,str]]]=None, default_language: int=0x0409):
        self.include_dirs=[Path(p) for p in include_dirs]
        self.defines=dict(defines or {})
        self.default_language=default_language&0xFFFF
        self.language=self.default_language
        # Stage 154: Codepage metadata carried into IMAGE_RESOURCE_DATA_ENTRY.
        self.codepage=0
        self.entries: List[ResourceEntry]=[]
        self.dependencies: List[str]=[]
        self.warnings: List[str]=[]
        self.source_path=Path()
        self.stream: Optional[_Stream]=None
        self._next_icon_id=1
        self._next_cursor_id=1

    def compile_file(self,path: Union[str,os.PathLike]) -> ResourceCompilation:
        self.source_path=Path(path).expanduser().resolve(); self.entries=[]; self.dependencies=[]; self.warnings=[]; self.language=self.default_language; self.codepage=0
        text,symbols,deps=_preprocess_file(self.source_path,defines=dict(self.defines),include_dirs=self.include_dirs)
        self.dependencies=[str(self.source_path),*deps]
        self.stream=_Stream(_tokenize(text,str(self.source_path)),symbols,str(self.source_path))
        self._parse_top()
        return ResourceCompilation(list(self.entries),list(dict.fromkeys(self.dependencies)),list(self.warnings))

    @property
    def s(self):
        assert self.stream is not None; return self.stream

    def _parse_top(self):
        s=self.s
        while True:
            s.skip_nl(); t=s.peek()
            if t.kind=="EOF": break
            if s.is_value("LANGUAGE"):
                s.pop(); p=s.expr_to_comma(); s.accept(","); sub=s.expr_to_comma(); self.language=((sub&0x3F)<<10)|(p&0x3FF); s.line_tokens(); continue
            if s.is_value("D64_CODEPAGE"):
                s.pop(); self.codepage=s.expr_to_comma() & 0xFFFFFFFF; s.line_tokens(); continue
            if s.is_value("CHARACTERISTICS") or s.is_value("VERSION"):
                s.line_tokens(); continue
            if s.is_value("STRINGTABLE"):
                self._parse_stringtable(); continue
            name=s.id_value(s.pop()); typ_tok=s.pop(); typ_name=typ_tok.value.upper()
            typ: ResourceId = RESOURCE_TYPES.get(typ_name, s.id_value(typ_tok))
            if typ_name=="VERSIONINFO": self._parse_version(name); continue
            if typ_name in {"DIALOG","DIALOGEX"}: self._parse_dialog(name,typ_name=="DIALOGEX"); continue
            if typ_name in {"MENU","MENUEX"}: self._parse_menu(name,typ_name=="MENUEX"); continue
            if typ_name=="ACCELERATORS": self._parse_accelerators(name); continue
            if typ_name=="TOOLBAR": self._parse_toolbar(name); continue
            self._parse_simple(name,typ,typ_name)

    def _parse_flags_to_eol(self) -> int:
        s=self.s; flags=MOVEABLE|PURE
        toks=s.line_tokens()
        for t in toks:
            key=t.value.upper()
            if key in MEMORY_FLAGS:
                if key in {"FIXED","IMPURE","LOADONCALL"}:
                    clear={"FIXED":MOVEABLE,"IMPURE":PURE,"LOADONCALL":PRELOAD}[key]; flags &= ~clear
                else: flags |= MEMORY_FLAGS[key]
        return flags

    def _resolve_asset(self,text: str) -> Path:
        p=Path(text)
        candidates=[p] if p.is_absolute() else [self.source_path.parent/p,*[d/p for d in self.include_dirs]]
        for c in candidates:
            if c.exists():
                q=c.resolve(); self.dependencies.append(str(q)); return q
        self.s.error(f"Ressourcendatei nicht gefunden: {text}")
        return p

    def _parse_simple(self,name: ResourceId,typ: ResourceId,typ_name: str):
        s=self.s
        # Header can contain memory flags and then a quoted filename on same line.
        line=s.line_tokens(); mem=MOVEABLE|PURE; filename=None; inline_tokens=[]
        for tok in line:
            k=tok.value.upper()
            if k in MEMORY_FLAGS:
                if k in {"FIXED","IMPURE","LOADONCALL"}: mem &= ~{"FIXED":MOVEABLE,"IMPURE":PURE,"LOADONCALL":PRELOAD}[k]
                else: mem |= MEMORY_FLAGS[k]
            elif tok.kind in {"STRING","WSTRING"}: filename=tok.value
            else: inline_tokens.append(tok)
        s.skip_nl()
        if filename is not None:
            if typ_name == "DLGINCLUDE":
                blob = filename.encode("cp1252", errors="replace") + b"\0"
                self.entries.append(ResourceEntry(typ,name,blob,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))
                return
            blob=self._resolve_asset(filename).read_bytes()
            if typ_name=="BITMAP" and len(blob)>=14 and blob[:2]==b"BM": blob=blob[14:]
            if typ_name=="ICON": self._emit_icon(name,blob,mem); return
            if typ_name=="CURSOR": self._emit_cursor(name,blob,mem); return
            self.entries.append(ResourceEntry(typ,name,blob,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path))); return
        if s.is_value("BEGIN") or s.is_value("{"):
            raw=self._parse_raw_block(); self.entries.append(ResourceEntry(typ,name,raw,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path))); return
        if inline_tokens:
            # unquoted filename is tolerated for classic RC files.
            candidate="".join(t.value for t in inline_tokens)
            try:
                blob=self._resolve_asset(candidate).read_bytes()
                if typ_name=="BITMAP" and blob[:2]==b"BM": blob=blob[14:]
                self.entries.append(ResourceEntry(typ,name,blob,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path))); return
            except ResourceCompilerError: pass
        s.error(f"Daten oder Dateiname für Ressource {name!r} erwartet")

    def _parse_raw_block(self) -> bytes:
        s=self.s; start=s.pop(); end="END" if start.value.upper()=="BEGIN" else "}"; out=bytearray()
        while True:
            s.skip_nl()
            if s.is_value(end): s.pop(); s.line_tokens(); break
            if s.peek().kind=="EOF": s.error("Nicht abgeschlossener RCDATA-Block")
            tok=s.pop()
            if tok.value==",": continue
            if tok.kind=="STRING": out += tok.value.encode("cp1252",errors="replace") + b"\0"
            elif tok.kind=="WSTRING": out += tok.value.encode("utf-16le") + b"\0\0"
            else:
                value=s.id_value(tok)
                if not isinstance(value,int): s.error("Numerischer RCDATA-Wert erwartet",tok)
                long_value=tok.kind=="NUMBER" and tok.value.lower().endswith("l")
                out += struct.pack("<I" if long_value else "<H",value & (0xFFFFFFFF if long_value else 0xFFFF))
        return bytes(out)

    def _emit_icon(self,name,blob,mem):
        images=_parse_icon_container(blob,cursor=False); group=bytearray(struct.pack("<HHH",0,1,len(images)))
        for w,h,colors,resv,planes,bpp,size,data in images:
            rid=self._next_icon_id; self._next_icon_id+=1
            self.entries.append(ResourceEntry(RT_ICON,rid,data,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))
            group += struct.pack("<BBBBHHIH",w,h,colors,resv,planes,bpp,size,rid)
        self.entries.append(ResourceEntry(RT_GROUP_ICON,name,bytes(group),self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _emit_cursor(self,name,blob,mem):
        images=_parse_icon_container(blob,cursor=True); group=bytearray(struct.pack("<HHH",0,2,len(images)))
        for w,h,colors,resv,hotx,hoty,size,data in images:
            rid=self._next_cursor_id; self._next_cursor_id+=1
            payload=struct.pack("<HH",hotx,hoty)+data
            self.entries.append(ResourceEntry(RT_CURSOR,rid,payload,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))
            width=256 if w==0 else w; height=256 if h==0 else h
            group += struct.pack("<HHHHIH",width,height,1,32,len(payload),rid)
        self.entries.append(ResourceEntry(RT_GROUP_CURSOR,name,bytes(group),self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _parse_stringtable(self):
        s=self.s; s.pop(); mem=self._parse_flags_to_eol(); s.skip_nl(); start=s.pop()
        if start.value.upper() not in {"BEGIN","{"}: s.error("BEGIN nach STRINGTABLE erwartet",start)
        end="END" if start.value.upper()=="BEGIN" else "}"; values={}
        while True:
            s.skip_nl()
            if s.is_value(end): s.pop(); s.line_tokens(); break
            ident=s.id_value(s.pop());
            if not isinstance(ident,int): s.error("Numerische String-ID erwartet")
            # Microsoft RC accepts the canonical ``ID, "text"`` form.
            # Stage 150 already accepted the historical whitespace-only form
            # ``ID "text"``; keep that compatibility and consume an optional
            # comma before the string literal.
            s.accept(",")
            tok=s.pop()
            if tok.kind not in {"STRING","WSTRING"}: s.error("String-Literal erwartet",tok)
            text=tok.value
            while s.peek().kind in {"STRING","WSTRING"}: text += s.pop().value
            s.line_tokens(); values[ident]=text
        blocks={}
        for ident,text in values.items(): blocks.setdefault((ident>>4)+1,{})[ident&15]=text
        for block_id,mapping in sorted(blocks.items()):
            data=bytearray()
            for idx in range(16):
                enc=mapping.get(idx,"").encode("utf-16le"); data+=struct.pack("<H",len(enc)//2)+enc
            self.entries.append(ResourceEntry(RT_STRING,block_id,bytes(data),self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _parse_accelerators(self,name):
        s=self.s; mem=self._parse_flags_to_eol(); s.skip_nl(); start=s.pop(); end="END" if start.value.upper()=="BEGIN" else "}"
        rows=[]
        while True:
            s.skip_nl()
            if s.is_value(end): s.pop(); s.line_tokens(); break
            line=s.line_tokens(); chunks=[]; cur=[]
            for t in line:
                if t.value==",": chunks.append(cur); cur=[]
                else: cur.append(t)
            chunks.append(cur)
            if len(chunks)<2: continue
            keytok=chunks[0][0]
            if keytok.kind in {"STRING","WSTRING"}:
                val=keytok.value
                key=ord(val[-1].upper()) if val.startswith("^") and len(val)>1 else (ord(val[0]) if val else 0)
            else: key=s.expr(chunks[0])
            cmd=s.expr(chunks[1]); flags=0
            for ch in chunks[2:]:
                for t in ch: flags |= int(RC_CONSTANTS.get(t.value.upper(),0))
            rows.append((flags,key,cmd))
        out=bytearray()
        for i,(flags,key,cmd) in enumerate(rows):
            if i==len(rows)-1: flags|=0x80
            out += struct.pack("<HHHH",flags&0xFFFF,key&0xFFFF,cmd&0xFFFF,0)
        self.entries.append(ResourceEntry(RT_ACCELERATOR,name,bytes(out),self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _parse_menu(self,name,extended):
        s=self.s; mem=self._parse_flags_to_eol(); s.skip_nl()
        while not (s.is_value("BEGIN") or s.is_value("{")):
            if s.peek().kind=="EOF": s.error("BEGIN bei MENU erwartet")
            s.line_tokens(); s.skip_nl()
        start=s.pop(); end="END" if start.value.upper()=="BEGIN" else "}"
        def parse_items(endword):
            items=[]
            while True:
                s.skip_nl()
                if s.is_value(endword): s.pop(); s.line_tokens(); break
                kind=s.pop().value.upper()
                if kind=="POPUP":
                    line=s.line_tokens(); text=""; flags=0
                    if line and line[0].kind in {"STRING","WSTRING"}: text=line[0].value; rest=line[1:]
                    else: rest=line
                    for t in rest:
                        if t.value!=",": flags |= int(RC_CONSTANTS.get(t.value.upper(),0))
                    s.skip_nl(); st=s.pop(); child_end="END" if st.value.upper()=="BEGIN" else "}"
                    items.append({"kind":"popup","text":text,"flags":flags,"type":flags,"children":parse_items(child_end)})
                elif kind=="MENUITEM":
                    line=s.line_tokens();
                    if line and line[0].value.upper()=="SEPARATOR": items.append({"kind":"item","text":"","id":0,"flags":0x0800,"type":0x0800}); continue
                    chunks=[];cur=[]
                    for t in line:
                        if t.value==",": chunks.append(cur);cur=[]
                        else: cur.append(t)
                    chunks.append(cur)
                    text=chunks[0][0].value if chunks and chunks[0] and chunks[0][0].kind in {"STRING","WSTRING"} else ""
                    ident=s.expr(chunks[1]) if len(chunks)>1 and chunks[1] else 0; flags=0
                    for ch in chunks[2:]:
                        for t in ch: flags |= int(RC_CONSTANTS.get(t.value.upper(),0))
                    items.append({"kind":"item","text":text,"id":ident,"flags":flags,"type":flags})
                else:
                    s.error(f"Unbekannter MENU-Eintrag {kind}")
            return items
        items=parse_items(end); data=_pack_menuex(items) if extended else _pack_menu_standard(items)
        self.entries.append(ResourceEntry(RT_MENU,name,data,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _parse_dialog(self,name,extended):
        s=self.s
        # read x,y,cx,cy from remainder of declaration line
        line=s.line_tokens(); chunks=[];cur=[]
        for t in line:
            if t.value==",": chunks.append(cur);cur=[]
            elif t.value.upper() not in MEMORY_FLAGS: cur.append(t)
        chunks.append(cur)
        chunks=[c for c in chunks if c]
        if len(chunks)<4: s.error("DIALOG benötigt x,y,cx,cy")
        rect=[s.expr(c) for c in chunks[-4:]]
        info={"rect":rect,"style":0x90C800C4,"exstyle":0,"caption":"","controls":[]}
        mem=MOVEABLE|PURE
        while True:
            s.skip_nl()
            if s.is_value("BEGIN") or s.is_value("{"): break
            key=s.pop().value.upper(); line=s.line_tokens()
            if key=="STYLE": info["style"]=s.expr(line)
            elif key=="EXSTYLE": info["exstyle"]=s.expr(line)
            elif key=="CAPTION" and line: info["caption"]=line[0].value
            elif key=="CLASS" and line: info["class"]=s.id_value(line[0])
            elif key=="MENU" and line: info["menu"]=s.id_value(line[0])
            elif key=="FONT":
                chunks=[];cur=[]
                for t in line:
                    if t.value==",": chunks.append(cur);cur=[]
                    else: cur.append(t)
                chunks.append(cur); f={"size":s.expr(chunks[0]) if chunks and chunks[0] else 8,"face":chunks[1][0].value if len(chunks)>1 and chunks[1] else "MS Shell Dlg"}
                if len(chunks)>2 and chunks[2]: f["weight"]=s.expr(chunks[2])
                if len(chunks)>3 and chunks[3]: f["italic"]=s.expr(chunks[3])
                if len(chunks)>4 and chunks[4]: f["charset"]=s.expr(chunks[4])
                info["font"]=f; info["style"] |= 0x40
            elif key=="LANGUAGE" and line:
                # local LANGUAGE is respected for this resource
                pass
            elif key in MEMORY_FLAGS:
                mem |= MEMORY_FLAGS.get(key,0)
        start=s.pop(); end="END" if start.value.upper()=="BEGIN" else "}"
        while True:
            s.skip_nl()
            if s.is_value(end): s.pop(); s.line_tokens(); break
            kind=s.pop().value.upper(); line=s.line_tokens(); chunks=[];cur=[]
            for t in line:
                if t.value==",": chunks.append(cur);cur=[]
                else: cur.append(t)
            chunks.append(cur)
            def val(idx,default=0): return s.expr(chunks[idx]) if idx<len(chunks) and chunks[idx] else default
            def txt(idx,default=""):
                if idx<len(chunks) and chunks[idx]:
                    t=chunks[idx][0]
                    return t.value if t.kind in {"STRING","WSTRING"} else s.id_value(t)
                return default
            c={}
            if kind=="CONTROL":
                if len(chunks)<8: s.error("CONTROL benötigt Text,ID,Klasse,Style,x,y,cx,cy")
                c.update(text=txt(0),id=val(1),class_=txt(2),style=val(3),x=val(4),y=val(5),cx=val(6),cy=val(7),exstyle=val(8) if len(chunks)>8 else 0)
                c["class"]=c.pop("class_")
            elif kind in _CONTROL_DEFAULTS:
                cls,base_style=_CONTROL_DEFAULTS[kind]
                has_text=kind not in {"EDITTEXT","LISTBOX","COMBOBOX","SCROLLBAR"}
                shift=1 if has_text else 0
                c["text"]=txt(0) if has_text else ""; c["id"]=val(shift); c["x"]=val(shift+1); c["y"]=val(shift+2); c["cx"]=val(shift+3); c["cy"]=val(shift+4)
                c["style"]=base_style | (val(shift+5) if len(chunks)>shift+5 and chunks[shift+5] else 0); c["exstyle"]=val(shift+6) if len(chunks)>shift+6 else 0; c["class"]=cls
            else: s.error(f"Unbekanntes DIALOG-Control {kind}")
            info["controls"].append(c)
        data=_pack_dialog(info,extended); self.entries.append(ResourceEntry(RT_DIALOG,name,data,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _parse_version(self,name):
        s=self.s; mem=self._parse_flags_to_eol(); fixed={}; nodes=[]
        s.skip_nl()
        while not (s.is_value("BEGIN") or s.is_value("{")):
            key=s.pop().value.upper(); line=s.line_tokens()
            if key in {"FILEVERSION","PRODUCTVERSION"}:
                chunks=[];cur=[]
                for t in line:
                    if t.value==",": chunks.append(cur);cur=[]
                    else: cur.append(t)
                chunks.append(cur); vals=[s.expr(c) for c in chunks if c]
                fixed[key]=tuple((vals+[0,0,0,0])[:4])
            elif key in {"FILEFLAGSMASK","FILEFLAGS","FILEOS","FILETYPE","FILESUBTYPE"}: fixed[key]=s.expr(line)
            s.skip_nl()
        start=s.pop(); end="END" if start.value.upper()=="BEGIN" else "}"
        def parse_nodes(endword):
            out=[]
            while True:
                s.skip_nl()
                if s.is_value(endword): s.pop(); s.line_tokens(); break
                kind=s.pop().value.upper()
                if kind=="BLOCK":
                    keytok=s.pop(); key=keytok.value; s.line_tokens(); s.skip_nl(); st=s.pop(); e="END" if st.value.upper()=="BEGIN" else "}"
                    out.append(("BLOCK",key,parse_nodes(e)))
                elif kind=="VALUE":
                    line=s.line_tokens(); chunks=[];cur=[]
                    for t in line:
                        if t.value==",": chunks.append(cur);cur=[]
                        else: cur.append(t)
                    chunks.append(cur); key=chunks[0][0].value if chunks and chunks[0] else ""
                    vals=[]
                    for ch in chunks[1:]:
                        if not ch: continue
                        if ch[0].kind in {"STRING","WSTRING"}: vals.extend(t.value for t in ch if t.kind in {"STRING","WSTRING"})
                        else: vals.append(s.expr(ch))
                    out.append(("VALUE",key,vals))
                else: s.error(f"Unbekannter VERSIONINFO-Eintrag {kind}")
            return out
        nodes=parse_nodes(end); data=_pack_version_info(fixed,nodes)
        self.entries.append(ResourceEntry(RT_VERSION,name,data,self.language,memory_flags=mem,codepage=self.codepage,source=str(self.source_path)))

    def _parse_toolbar(self,name):
        s=self.s; line=s.line_tokens(); chunks=[];cur=[]
        for t in line:
            if t.value==",": chunks.append(cur);cur=[]
            elif t.value.upper() not in MEMORY_FLAGS: cur.append(t)
        chunks.append(cur); chunks=[c for c in chunks if c]
        if len(chunks)<2: s.error("TOOLBAR benötigt Breite,Höhe")
        width,height=s.expr(chunks[-2]),s.expr(chunks[-1]); s.skip_nl(); st=s.pop(); end="END" if st.value.upper()=="BEGIN" else "}"; ids=[]
        while True:
            s.skip_nl()
            if s.is_value(end): s.pop(); s.line_tokens(); break
            kind=s.pop().value.upper(); line=s.line_tokens()
            if kind=="SEPARATOR": ids.append(0)
            elif kind=="BUTTON": ids.append(s.expr(line))
            else: s.error(f"Unbekannter TOOLBAR-Eintrag {kind}")
        data=struct.pack("<HHHH",1,width&0xFFFF,height&0xFFFF,len(ids)&0xFFFF)+b"".join(struct.pack("<H",i&0xFFFF) for i in ids)
        self.entries.append(ResourceEntry(RT_TOOLBAR,name,data,self.language,memory_flags=MOVEABLE|PURE,codepage=self.codepage,source=str(self.source_path)))


# ---------------------------------------------------------------------------
# Public convenience API / small command line frontend
# ---------------------------------------------------------------------------
def compile_rc(path: Union[str,os.PathLike], *, include_dirs=(), defines=None, default_language: int=0x0409) -> ResourceCompilation:
    return ResourceScriptCompiler(include_dirs=include_dirs,defines=defines,default_language=default_language).compile_file(path)


def compile_rc_to_res(path: Union[str,os.PathLike], output: Optional[Union[str,os.PathLike]]=None, *, include_dirs=(), defines=None, default_language: int=0x0409) -> Path:
    source=Path(path); target=Path(output) if output else source.with_suffix(".res")
    comp=compile_rc(source,include_dirs=include_dirs,defines=defines,default_language=default_language)
    return save_res(target,comp.entries)


def convert_res_to_coff(path: Union[str,os.PathLike], output: Optional[Union[str,os.PathLike]]=None, *, machine="x86") -> Path:
    source=Path(path); target=Path(output) if output else source.with_suffix(".obj")
    return save_resource_coff(target,read_res(source),machine=machine)


def compile_rc_to_coff(path: Union[str,os.PathLike], output: Optional[Union[str,os.PathLike]]=None, *, machine="x86", include_dirs=(), defines=None, default_language: int=0x0409) -> Path:
    source=Path(path); target=Path(output) if output else source.with_suffix(".obj")
    comp=compile_rc(source,include_dirs=include_dirs,defines=defines,default_language=default_language)
    return save_resource_coff(target,comp.entries,machine=machine)


def describe_resource_id(value: ResourceId) -> str:
    if isinstance(value,str): return value
    for name,ident in RESOURCE_TYPES.items():
        if ident==value: return f"{name} ({value})"
    return str(value)


def main(argv=None) -> int:
    import argparse
    import sys
    raw = list(sys.argv[1:] if argv is None else argv)
    # Accept the most useful Microsoft RC spellings while keeping POSIX
    # absolute paths usable (argparse itself therefore keeps prefix_chars='-').
    normalized = []
    i = 0
    while i < len(raw):
        arg = raw[i]
        low = arg.casefold()
        if low == "/nologo":
            i += 1
            continue
        if low in {"/fo", "/i", "/d", "/l"}:
            normalized.append({"/fo":"-fo", "/i":"-I", "/d":"-D", "/l":"--language"}[low])
            i += 1
            if i < len(raw): normalized.append(raw[i])
            i += 1
            continue
        if low.startswith("/fo") and len(arg) > 3:
            normalized.extend(["-fo", arg[3:]])
        elif low.startswith("/i") and len(arg) > 2:
            normalized.extend(["-I", arg[2:]])
        elif low.startswith("/d") and len(arg) > 2:
            normalized.extend(["-D", arg[2:]])
        elif low.startswith("/l") and len(arg) > 2:
            normalized.extend(["--language", arg[2:]])
        elif low == "/r":
            normalized.extend(["--target", "res"])
        else:
            normalized.append(arg)
        i += 1

    p=argparse.ArgumentParser(description="d64_dism internal Windows Resource Compiler")
    p.add_argument("input",help=".rc or .res input")
    p.add_argument("-o","--output","-fo",dest="output")
    p.add_argument("--target",choices=["x86","x64","res"],default="res")
    p.add_argument("--language",default="0x0409",help="default LANGID, e.g. 0x0407")
    p.add_argument("-I",dest="includes",action="append",default=[])
    p.add_argument("-D",dest="defines",action="append",default=[])
    ns=p.parse_args(normalized)
    defs={}
    for item in ns.defines:
        key,eq,val=item.partition("="); defs[key]=int(val,0) if eq else 1
    src=Path(ns.input)
    default_language = int(str(ns.language), 0) & 0xFFFF
    if src.suffix.lower()==".res":
        if ns.target=="res": raise SystemExit(".res -> .res ist nicht erforderlich")
        convert_res_to_coff(src,ns.output,machine=ns.target)
    elif ns.target=="res": compile_rc_to_res(src,ns.output,include_dirs=ns.includes,defines=defs,default_language=default_language)
    else: compile_rc_to_coff(src,ns.output,machine=ns.target,include_dirs=ns.includes,defines=defs,default_language=default_language)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

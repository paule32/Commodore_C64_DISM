# ---------------------------------------------------------------------------
# (c) 2026 by Jens Kallup - paule32
# Alle Rechte vorbehalten.
#
# Funktionen:
#  * verschiebbare Toolbar
#  * verschiebbare und skalierbare Dock-Fenster
#  * Dateisystembaum mit wählbarem Arbeitsverzeichnis
#  * Pfadeingabe mit Navigation per Eingabetaste
#  * Icon-Liste mit D64/RAM/ASM/PRG/TXT-Filtern
#  * integrierte Anzeige des C64-Verzeichnisses einer D64-Datei
#  * zentraler Texteditor mit Dokument- und Unterregisterkarten
#  * bytegenauer Hex-Editor mit 16-Bit-Offset, 4+4-Darstellung und C64-Pro-Schrift
#  * PETSCII-Zeichenauswahl fuer das aktuelle Byte im Hex-Editor
#  * Character-Editor fuer 255 frei editierbare 8x8-Zeichen
#  * Paletten-Editor fuer die 16 C64-Farben mit Quellcodeexport
#  * Text-Bildschirm-Editor fuer 40x25 Zeichen und Farben
#  * Pixel-Bildschirm-Editor fuer 320x200 Pixel, 16 Farben und Formwerkzeuge
#  * Neu/Oeffnen/Speichern/Speichern unter mit sicherer Schliessabfrage
#  * Syntax-Hervorhebung fuer 6502/6510-Assembler und Kommentare
#  * integrierte 6510-/680x0-Assembler mit C64-PRG-/Amiga-Hunk-Ausgabe
#  * Amiga-CPU-Profile mk68000..mk68060 und optionale 68881/68882-FPU
#  * integrierter IA-32-/PE32-Assembler mit Microsoft-COFF32-Objekten
#  * integrierter COFF32-.a-Archivierer und PE32-Linker samt DLL-Imports/-Exports
#  * Windows-Grafikziel fuer 320x200 ueber Direct2D oder Direct3D
#  * C64-BASIC-Compiler sowie ANTLR-Compiler fuer Pascal und C
#  * zielabhängiger Start in VICE, WinUAE oder als Windows-PE32-Programm
#  * Operanden-Rechner fuer Dezimal-, Hexadezimal- und Binaerwerte
#  * integrierter CHM-Viewer mit unterschiedlichen Themen-/Blatt-Icons
#  * INI-basiertes Projekt-Panel mit geschuetzten Kategorien und *.pro-Dateien
#  * Projekt-Kontextaktion Neu mit Unbenannt_<n> und passendem Spezialeditor
#  * Hilfe-Schaltflaeche links neben dem Zoom sowie dunkler Projekt-Oeffnen-Button
#  * Protokoll-Loeschaktion in der Dock-Leiste und weisse Dock-/Tab-Symbole
#  * Statusfelder fuer INS/CAPS/NUM, Dateigroesse, Zeile und Spalte
#  * Registerkarten-Kontextmenue und sprachabhaengige F1-Kontexthilfe
#  * Datei-Neu-Untermenue fuer BASIC, ASM, Pascal, C und C64-Editoren
#  * Editor-Zoom sowie umschaltbarer Hell-/Dunkelmodus
#
# Installation:
#    py -m pip install PyQt5 PyQtWebEngine antlr4-python3-runtime==4.13.2
#
# Start:
#    py d64_dism.py
#    py d64_dism.py "T:/C64/Images"
# ---------------------------------------------------------------------------
from __future__ import annotations

import argparse
import ast
import configparser
import hashlib
import html
import inspect

from html.parser import HTMLParser

import json
import os
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import time
import zlib      as _d64info_zlib
import base64    as _d64info_base64

from dataclasses import dataclass, field
from decimal     import Decimal, localcontext
from fractions   import Fraction
from pathlib     import Path
from typing      import Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# C64 Pro Mono: direkte PETSCII-Zuordnung fuer die Zeichenansicht des
# Hex-Editors. Die privaten Unicode-Codepunkte U+E000..U+E0FF stammen aus der
# "Direct PETSCII"-Belegung des Fonts. PETSCII-Steuercodes in 00..1F und
# 80..9F besitzen absichtlich keine druckbare Glyphe; fuer sie wird die
# ebenfalls im C64-Font enthaltene Punktglyphe U+E071 verwendet.
# ---------------------------------------------------------------------------
C64_PRO_CONTROL_GLYPH = "\uE071"
C64_PRO_PETSCII_GLYPHS: Tuple[str, ...] = tuple(
    chr(0xE000 + byte_value)
    if 0x20 <= byte_value <= 0x7F or 0xA0 <= byte_value <= 0xFF
    else C64_PRO_CONTROL_GLYPH
    for byte_value in range(0x100)
)

# ---------------------------------------------------------------------------
# C64-Character-Editor: Ein Zeichensatz umfasst 256 Zeichen zu je acht Bytes.
# Zeichen $00 bleibt als reserviertes Leerzeichen erhalten; editierbar sind
# die 255 Zeichen $01..$FF. Rohdateien duerfen entweder 2048 Bytes inklusive
# Zeichen $00 oder 2040 Bytes nur fuer die editierbaren Zeichen enthalten.
# ---------------------------------------------------------------------------
C64_CHARACTER_WIDTH                 = 8
C64_CHARACTER_HEIGHT                = 8
C64_CHARACTER_BYTES                 = 8
C64_CHARACTER_TOTAL_COUNT           = 256
C64_CHARACTER_EDITABLE_COUNT        = 255
C64_CHARACTER_FILE_SIZE             =  C64_CHARACTER_TOTAL_COUNT    * C64_CHARACTER_BYTES
C64_CHARACTER_EDITABLE_FILE_SIZE    = (C64_CHARACTER_EDITABLE_COUNT * C64_CHARACTER_BYTES)

C64_CHARACTER_PALETTE: Tuple[Tuple[str, str], ...] = (
    ("Schwarz",     "#000000"),
    ("Weiß",        "#FFFFFF"),
    ("Rot",         "#883932"),
    ("Cyan",        "#67B6BD"),
    ("Violett",     "#8B3F96"),
    ("Grün",        "#55A049"),
    ("Blau",        "#40318D"),
    ("Gelb",        "#BFCE72"),
    ("Orange",      "#8B5429"),
    ("Braun",       "#574200"),
    ("Hellrot",     "#B86962"),
    ("Dunkelgrau",  "#505050"),
    ("Grau",        "#787878"),
    ("Hellgrün",    "#94E089"),
    ("Hellblau",    "#7869C4"),
    ("Hellgrau",    "#9F9F9F"),
)


HUNK_HEADER             = 0x000003F3
HUNK_CODE               = 0x000003E9
HUNK_END                = 0x000003F2

ADF_SIZE                = 80 * 2 * 11 * 512
BOOT_BLOCK_SIZE         = 1024
BOOT_CODE_OFFSET        = 12
AMIGA_DD_ROOT_BLOCK     = 880
BOOT_PAYLOAD_OFFSET     = BOOT_BLOCK_SIZE
BOOT_PAYLOAD_ADDRESS    = 0x00040000
BOOT_STACK_ADDRESS      = 0x0007FFFC
MAX_BOOT_PAYLOAD_SIZE   = 0x0003F000

# ---------------------------------------------------------------------------
# Plattformprofile: Amiga-CPU/FPU sowie Windows PE32/COFF32.
# Die Namen der CPU-Profile entsprechen bewusst der GUI-Benennung.
# ---------------------------------------------------------------------------
AMIGA_CPU_MODELS: Tuple[str, ...] = (
    "mk68000",
    "mk68010",
    "mk68020",
    "mk68030",
    "mk68040",
    "mk68060",
)
AMIGA_CPU_LEVEL: Dict[str, int] = {
    name: index for index, name in enumerate(AMIGA_CPU_MODELS)
}
AMIGA_FPU_MODELS: Tuple[str, ...] = (
    "FPU: None",
    "FPU: 68881",
    "FPU: 68882",
)
WINDOWS_GRAPHICS_BACKENDS: Tuple[str, ...] = (
    "Direct2D",
    "Direct3D",
)
WINDOWS_APPLICATION_MODES: Tuple[str, ...] = (
    "Console",
    "GUI",
    "Direct2D",
    "Direct3D",
)


def normalize_amiga_cpu_model(value: str) -> str:
    text = str(value or "mk68000").strip().casefold()
    aliases = {
        "68000": "mk68000",
        "68010": "mk68010",
        "68020": "mk68020",
        "68030": "mk68030",
        "68040": "mk68040",
        "68060": "mk68060",
    }
    text = aliases.get(text, text)
    if text not in AMIGA_CPU_LEVEL:
        raise ValueError(
            "Unbekanntes Amiga-CPU-Profil: " + str(value)
            + ". Erlaubt: " + ", ".join(AMIGA_CPU_MODELS)
        )
    return text


def normalize_amiga_fpu_model(value: str) -> str:
    text = str(value or "FPU: None").strip().casefold()
    aliases = {
        "none": "FPU: None",
        "fpu:none": "FPU: None",
        "fpu: none": "FPU: None",
        "68881": "FPU: 68881",
        "fpu:68881": "FPU: 68881",
        "fpu: 68881": "FPU: 68881",
        "68882": "FPU: 68882",
        "fpu:68882": "FPU: 68882",
        "fpu: 68882": "FPU: 68882",
    }
    normalized = aliases.get(text)
    if normalized is None:
        for candidate in AMIGA_FPU_MODELS:
            if candidate.casefold() == text:
                normalized = candidate
                break
    if normalized is None:
        raise ValueError(
            "Unbekanntes Amiga-FPU-Profil: " + str(value)
            + ". Erlaubt: " + ", ".join(AMIGA_FPU_MODELS)
        )
    return normalized


def amiga_cpu_at_least(current: str, required: str) -> bool:
    return (
        AMIGA_CPU_LEVEL[normalize_amiga_cpu_model(current)]
        >= AMIGA_CPU_LEVEL[normalize_amiga_cpu_model(required)]
    )


def normalize_windows_graphics_backend(value: str) -> str:
    text = str(value or "Direct2D").strip().casefold()
    if text in {"direct2d", "d2d", "direct2"}:
        return "Direct2D"
    if text in {"direct3d", "d3d", "d3d9", "direct3d9"}:
        return "Direct3D"
    raise ValueError(
        "Unbekanntes Windows-Grafikbackend: " + str(value)
        + ". Erlaubt: Direct2D, Direct3D"
    )


def normalize_windows_application_mode(value: str) -> str:
    text = str(value or "Console").strip().casefold()
    aliases = {
        "console": "Console",
        "konsole": "Console",
        "gui": "GUI",
        "windows": "GUI",
        "direct2d": "Direct2D",
        "d2d": "Direct2D",
        "direct3d": "Direct3D",
        "d3d": "Direct3D",
        "d3d9": "Direct3D",
    }
    normalized = aliases.get(text)
    if normalized is None:
        raise ValueError(
            "Unbekannter Windows-Anwendungsmodus: " + str(value)
            + ". Erlaubt: " + ", ".join(WINDOWS_APPLICATION_MODES)
        )
    return normalized


def windows_application_predefined_macros(mode: str) -> Dict[str, str]:
    selected = normalize_windows_application_mode(mode)
    macros = {"__D64_TARGET_PE32__": "1"}
    if selected == "Console":
        macros["__D64_WINDOWS_CONSOLE__"] = "1"
        return macros
    macros["__D64_WINDOWS_GUI__"] = "1"
    if selected in WINDOWS_GRAPHICS_BACKENDS:
        macros.update(windows_graphics_predefined_macros(selected))
    return macros


# ---------------------------------------------------------------------------
# Minimaler, aber echter IA-32-Assembler und PE32/COFF32-Linker.
# Ziel ist eine in d64_dism integrierte, deterministische Toolchain. Der
# Assembler verwendet Intel-Syntax und erzeugt entweder ein PE32-Image oder
# ein relocierbares Microsoft-COFF32-Objekt.
# ---------------------------------------------------------------------------
IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_REL_I386_DIR32 = 0x0006
IMAGE_REL_I386_REL32 = 0x0014
PE32_IMAGE_BASE = 0x00400000
PE32_DLL_IMAGE_BASE = 0x10000000
PE32_SECTION_RVA = 0x00001000
PE32_FILE_ALIGNMENT = 0x200
PE32_SECTION_ALIGNMENT = 0x1000


class PE32AssemblerError(Exception):
    def __init__(self, message: str, line: int = 0) -> None:
        self.message = str(message)
        self.line = int(line or 0)
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"Zeile {self.line}: {self.message}" if self.line else self.message


@dataclass(frozen=True)
class PE32Relocation:
    offset: int
    symbol: str
    relocation_type: int


@dataclass(frozen=True)
class PE32ObjectProgram:
    code: bytes
    symbols: Dict[str, int]
    externals: Tuple[str, ...]
    relocations: Tuple[PE32Relocation, ...]
    entry_symbol: str = "_start"
    imports: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    exports: Dict[str, str] = field(default_factory=dict)
    dll_name: Optional[str] = None


@dataclass(frozen=True)
class PE32Program:
    executable: bytes
    code: bytes
    entry_offset: int
    instruction_count: int
    symbols: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Coff32ParsedObject:
    code: bytes
    symbols: Dict[str, Optional[int]]
    relocations: Tuple[PE32Relocation, ...]
    imports: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    exports: Dict[str, str] = field(default_factory=dict)
    dll_name: Optional[str] = None


_X86_REGISTERS = {
    "eax": 0,
    "ecx": 1,
    "edx": 2,
    "ebx": 3,
    "esp": 4,
    "ebp": 5,
    "esi": 6,
    "edi": 7,
}
_X86_JCC = {
    "jo": 0x80,
    "jno": 0x81,
    "jb": 0x82,
    "jc": 0x82,
    "jnae": 0x82,
    "jae": 0x83,
    "jnb": 0x83,
    "jnc": 0x83,
    "je": 0x84,
    "jz": 0x84,
    "jne": 0x85,
    "jnz": 0x85,
    "jbe": 0x86,
    "jna": 0x86,
    "ja": 0x87,
    "jnbe": 0x87,
    "js": 0x88,
    "jns": 0x89,
    "jp": 0x8A,
    "jpe": 0x8A,
    "jnp": 0x8B,
    "jpo": 0x8B,
    "jl": 0x8C,
    "jnge": 0x8C,
    "jge": 0x8D,
    "jnl": 0x8D,
    "jle": 0x8E,
    "jng": 0x8E,
    "jg": 0x8F,
    "jnle": 0x8F,
}


def _align_up(value: int, alignment: int) -> int:
    alignment = max(1, int(alignment))
    return (int(value) + alignment - 1) & ~(alignment - 1)


def _x86_strip_comment(line: str) -> str:
    in_string = False
    quote = ""
    result = []
    escape = False
    for char in str(line):
        if escape:
            result.append(char)
            escape = False
            continue
        if char == "\\" and in_string:
            result.append(char)
            escape = True
            continue
        if in_string:
            result.append(char)
            if char == quote:
                in_string = False
            continue
        if char in {'"', "'"}:
            in_string = True
            quote = char
            result.append(char)
            continue
        if char == ";":
            break
        result.append(char)
    return "".join(result).strip()


def _x86_parse_int(text: str) -> Optional[int]:
    value = str(text).strip()
    if not value:
        return None
    sign = 1
    if value[0] in "+-":
        if value[0] == "-":
            sign = -1
        value = value[1:].strip()
    try:
        if value.startswith("$"):
            return sign * int(value[1:], 16)
        if value.lower().startswith("0x"):
            return sign * int(value[2:], 16)
        if value.endswith(("h", "H")) and re.fullmatch(r"[0-9A-Fa-f]+[hH]", value):
            return sign * int(value[:-1], 16)
        if value.startswith("%"):
            return sign * int(value[1:], 2)
        if value.lower().startswith("0b"):
            return sign * int(value[2:], 2)
        if re.fullmatch(r"[0-9]+", value):
            return sign * int(value, 10)
    except ValueError:
        return None
    return None


def _x86_split_operands(text: str) -> List[str]:
    result = []
    start = 0
    depth = 0
    in_string = False
    quote = ""
    escape = False
    for index, char in enumerate(str(text)):
        if escape:
            escape = False
            continue
        if in_string:
            if char == "\\":
                escape = True
            elif char == quote:
                in_string = False
            continue
        if char in {'"', "'"}:
            in_string = True
            quote = char
            continue
        if char in "[()":
            depth += 1
        elif char in "])":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            result.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        result.append(tail)
    return result


def _x86_modrm(reg_field: int, rm_field: int) -> int:
    return 0xC0 | ((int(reg_field) & 7) << 3) | (int(rm_field) & 7)


def _x86_reg(name: str, line: int) -> int:
    key = str(name).strip().casefold()
    if key not in _X86_REGISTERS:
        raise PE32AssemblerError(f"IA-32-Register erwartet: {name}", line)
    return _X86_REGISTERS[key]



_X86_SIZE_PREFIX_RE = re.compile(
    r"^\s*(?:(byte|word|dword)\s+(?:ptr\s+)?)?(\[.*\])\s*$",
    re.IGNORECASE,
)
_X86_REGISTERS8 = {"al": 0, "cl": 1, "dl": 2, "bl": 3, "ah": 4, "ch": 5, "dh": 6, "bh": 7}
_X86_REGISTERS16 = {"ax": 0, "cx": 1, "dx": 2, "bx": 3, "sp": 4, "bp": 5, "si": 6, "di": 7}
_X86_SETCC = {
    "seto": 0x90, "setno": 0x91, "setb": 0x92, "setc": 0x92,
    "setnae": 0x92, "setae": 0x93, "setnb": 0x93, "setnc": 0x93,
    "sete": 0x94, "setz": 0x94, "setne": 0x95, "setnz": 0x95,
    "setbe": 0x96, "setna": 0x96, "seta": 0x97, "setnbe": 0x97,
    "sets": 0x98, "setns": 0x99, "setp": 0x9A, "setpe": 0x9A,
    "setnp": 0x9B, "setpo": 0x9B, "setl": 0x9C, "setnge": 0x9C,
    "setge": 0x9D, "setnl": 0x9D, "setle": 0x9E, "setng": 0x9E,
    "setg": 0x9F, "setnle": 0x9F,
}


def _x86_memory_operand(text: str, line: int):
    """Parst die ueblichen 32-Bit-Intel-Speicheroperanden.

    Unterstuetzt werden [reg], [reg+disp], [base+index*scale+disp] und
    [symbol]. Ein Symbol zusammen mit Basis-/Indexregister wird bewusst noch
    abgewiesen, damit Relocations deterministisch bleiben.
    """
    match = _X86_SIZE_PREFIX_RE.fullmatch(str(text).strip())
    if match is None:
        return None
    size_hint = (match.group(1) or "dword").casefold()
    inside = match.group(2)[1:-1].strip()
    if not inside:
        raise PE32AssemblerError("Leerer Speicheroperand [].", line)

    # Minuszeichen in additive Terme umwandeln, ohne ein fuehrendes Minus zu
    # verlieren. Compiler-Ausgaben verwenden hier typischerweise EBP-4.
    normalized = re.sub(r"(?<!^)-", "+-", inside.replace(" ", ""))
    terms = [item for item in normalized.split("+") if item]
    base = None
    index = None
    scale = 1
    displacement = 0
    symbol = None
    for term in terms:
        lower = term.casefold()
        if "*" in lower:
            reg_text, scale_text = lower.split("*", 1)
            if reg_text not in _X86_REGISTERS:
                raise PE32AssemblerError(f"IA-32-Indexregister erwartet: {term}", line)
            if index is not None:
                raise PE32AssemblerError("Nur ein IA-32-Indexregister ist erlaubt.", line)
            parsed_scale = _x86_parse_int(scale_text)
            if parsed_scale not in {1, 2, 4, 8}:
                raise PE32AssemblerError("IA-32-Skalierung muss 1, 2, 4 oder 8 sein.", line)
            index = reg_text
            scale = int(parsed_scale)
            continue
        if lower in _X86_REGISTERS:
            if base is None:
                base = lower
            elif index is None:
                index = lower
                scale = 1
            else:
                raise PE32AssemblerError("Zu viele IA-32-Register im Speicheroperanden.", line)
            continue
        numeric = _x86_parse_int(term)
        if numeric is not None:
            displacement += int(numeric)
            continue
        if re.fullmatch(r"[A-Za-z_.$?@][A-Za-z0-9_.$?@]*", term):
            if symbol is not None:
                raise PE32AssemblerError("Nur ein Symbol pro Speicheroperand ist erlaubt.", line)
            symbol = term.casefold()
            continue
        raise PE32AssemblerError(f"Ungueltiger IA-32-Speicherterm: {term}", line)

    if symbol is not None and (base is not None or index is not None):
        raise PE32AssemblerError(
            "Symbol+Register-Adressierung wird im internen PE32-Assembler noch nicht unterstuetzt.",
            line,
        )
    return {
        "size": size_hint,
        "base": base,
        "index": index,
        "scale": scale,
        "disp": displacement,
        "symbol": symbol,
    }


def _x86_rm_encoding(reg_field: int, operand: str, line: int):
    """Liefert ModR/M+SIB+Displacement und optionales DIR32-Symbol."""
    key = str(operand).strip().casefold()
    if key in _X86_REGISTERS:
        return bytes((_x86_modrm(reg_field, _X86_REGISTERS[key]),)), None, None
    memory = _x86_memory_operand(operand, line)
    if memory is None:
        raise PE32AssemblerError(f"Register oder Speicheroperand erwartet: {operand}", line)

    symbol = memory["symbol"]
    base_name = memory["base"]
    index_name = memory["index"]
    displacement = int(memory["disp"])
    output = bytearray()

    if symbol is not None:
        # mod=00, r/m=101 -> disp32 absolute; Relocation zeigt auf die 4 Bytes.
        output.append(((reg_field & 7) << 3) | 0x05)
        reloc_local = len(output)
        output.extend(b"\x00\x00\x00\x00")
        return bytes(output), symbol, reloc_local

    base = _X86_REGISTERS[base_name] if base_name is not None else None
    index = _X86_REGISTERS[index_name] if index_name is not None else None
    needs_sib = index is not None or base == 4 or base is None

    if base is None:
        mod = 0
        disp_size = 4
    elif displacement == 0 and base != 5:
        mod = 0
        disp_size = 0
    elif -128 <= displacement <= 127:
        mod = 1
        disp_size = 1
    else:
        mod = 2
        disp_size = 4

    rm = 4 if needs_sib else int(base)
    output.append((mod << 6) | ((reg_field & 7) << 3) | (rm & 7))
    if needs_sib:
        scale_bits = {1: 0, 2: 1, 4: 2, 8: 3}[int(memory["scale"])]
        index_bits = 4 if index is None else index
        base_bits = 5 if base is None else base
        output.append((scale_bits << 6) | ((index_bits & 7) << 3) | (base_bits & 7))
    if disp_size == 1:
        output.extend(struct.pack("<b", displacement))
    elif disp_size == 4:
        output.extend(struct.pack("<i", displacement))
    return bytes(output), None, None


def _x86_rm_length(operand: str, line: int) -> int:
    encoded, _symbol, _local = _x86_rm_encoding(0, operand, line)
    return len(encoded)


def _x86_is_rm32(operand: str, line: int) -> bool:
    key = str(operand).strip().casefold()
    if key in _X86_REGISTERS:
        return True
    try:
        return _x86_memory_operand(operand, line) is not None
    except PE32AssemblerError:
        raise

def _x86_data_values(arguments: str, line: int, unit: int) -> bytes:
    output = bytearray()
    for token in _x86_split_operands(arguments):
        token = token.strip()
        if unit == 1 and len(token) >= 2 and token[0] in {'"', "'"} and token[-1] == token[0]:
            try:
                decoded = ast.literal_eval(token)
            except Exception as exc:
                raise PE32AssemblerError(f"Ungültige Zeichenkette: {token}", line) from exc
            if not isinstance(decoded, str):
                raise PE32AssemblerError("DB-Zeichenkette erwartet Text.", line)
            output.extend(decoded.encode("latin-1", errors="replace"))
            continue
        value = _x86_parse_int(token)
        if value is None:
            raise PE32AssemblerError(f"Numerischer Datenwert erwartet: {token}", line)
        output.extend(int(value).to_bytes(unit, "little", signed=False))
    return bytes(output)


def _pe32_unquote(text: str) -> str:
    value = str(text).strip()
    if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
        try:
            decoded = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            decoded = value[1:-1]
        return str(decoded)
    return value


def _parse_pe32_source_lines(
    source: str,
) -> Tuple[
    List[Tuple[int, str]],
    Dict[str, int],
    str,
    Tuple[str, ...],
    Dict[str, Tuple[str, str]],
    Dict[str, str],
    Optional[str],
]:
    """Parst den internen IA-32-Assembler einschließlich Linker-Metadaten.

    Zusätzliche Direktiven:

    ``import symbol, "dll", "member"``
        Ordnet ein externes COFF-Symbol einem DLL-Import zu. Wird ``member``
        weggelassen, wird der Symbolname als DLL-Member verwendet.

    ``export public_name, internal_symbol``
        Exportiert beim DLL-Link den internen COFF-Symbolnamen unter dem
        angegebenen öffentlichen Namen. Der zweite Operand ist optional.

    ``dllname "name.dll"``
        Speichert den gewünschten DLL-Namen im COFF32-Objekt.
    """
    lines: List[Tuple[int, str]] = []
    labels: Dict[str, int] = {}
    externals = set()
    imports: Dict[str, Tuple[str, str]] = {}
    exports: Dict[str, str] = {}
    dll_name: Optional[str] = None
    entry_symbol = "_start"
    offset = 0

    def instruction_size(text: str, line: int) -> int:
        lower = text.strip().casefold()
        parts = lower.split(None, 1)
        mnemonic = parts[0]
        operands = _x86_split_operands(parts[1] if len(parts) > 1 else "")
        if mnemonic == "ret":
            return 1 if not operands else 3
        if mnemonic in {"nop", "leave", "int3", "pushad", "popad", "cdq", "cld", "std", "cli", "sti"}:
            return 1
        if mnemonic == "int" and len(operands) == 1:
            return 2
        if mnemonic in {"call", "jmp"} and len(operands) == 1:
            if _x86_memory_operand(operands[0], line) is not None or operands[0] in _X86_REGISTERS:
                return 1 + _x86_rm_length(operands[0], line)
            return 5
        if mnemonic in _X86_JCC:
            return 6
        if mnemonic in {"push", "pop", "inc", "dec"} and len(operands) == 1:
            if operands[0] in _X86_REGISTERS:
                return 1
            if _x86_memory_operand(operands[0], line) is not None:
                return 1 + _x86_rm_length(operands[0], line)
            if mnemonic == "push":
                return 5
        if mnemonic == "mov" and len(operands) == 2:
            dst, src = operands
            dst_mem = _x86_memory_operand(dst, line)
            if dst_mem is not None and src in _X86_REGISTERS8:
                return 1 + _x86_rm_length(dst, line)
            if dst_mem is not None and src in _X86_REGISTERS16:
                return 2 + _x86_rm_length(dst, line)
            if dst in _X86_REGISTERS and src in _X86_REGISTERS:
                return 2
            if dst in _X86_REGISTERS and _x86_memory_operand(src, line) is not None:
                return 1 + _x86_rm_length(src, line)
            if _x86_memory_operand(dst, line) is not None and src in _X86_REGISTERS:
                return 1 + _x86_rm_length(dst, line)
            if _x86_memory_operand(dst, line) is not None:
                return 1 + _x86_rm_length(dst, line) + 4
            if dst in _X86_REGISTERS:
                return 5
        if mnemonic == "lea" and len(operands) == 2 and operands[0] in _X86_REGISTERS:
            return 1 + _x86_rm_length(operands[1], line)
        if mnemonic in {"xor", "and", "or", "test", "add", "sub", "cmp"} and len(operands) == 2:
            dst, src = operands
            if src in _X86_REGISTERS and _x86_is_rm32(dst, line):
                return 1 + _x86_rm_length(dst, line)
            if dst in _X86_REGISTERS and _x86_memory_operand(src, line) is not None:
                return 1 + _x86_rm_length(src, line)
            if _x86_is_rm32(dst, line) and _x86_parse_int(src) is not None:
                return 1 + _x86_rm_length(dst, line) + 4
        if mnemonic == "imul" and len(operands) == 2 and operands[0] in _X86_REGISTERS and _x86_is_rm32(operands[1], line):
            return 2 + _x86_rm_length(operands[1], line)
        if mnemonic in {"div", "idiv", "neg", "not"} and len(operands) == 1 and _x86_is_rm32(operands[0], line):
            return 1 + _x86_rm_length(operands[0], line)
        if mnemonic in {"movzx", "movsx"} and len(operands) == 2 and operands[0] in _X86_REGISTERS:
            src_key = operands[1].casefold()
            if src_key in _X86_REGISTERS8:
                return 3
            memory = _x86_memory_operand(operands[1], line)
            if memory is not None:
                return 2 + _x86_rm_length(operands[1], line)
        if mnemonic in _X86_SETCC and len(operands) == 1:
            if operands[0] in _X86_REGISTERS8:
                return 3
            memory = _x86_memory_operand(operands[0], line)
            if memory is not None:
                return 2 + _x86_rm_length(operands[0], line)
        if mnemonic == "xchg" and len(operands) == 2:
            if operands[1] in _X86_REGISTERS and _x86_is_rm32(operands[0], line):
                return 1 + _x86_rm_length(operands[0], line)
            if operands[0] in _X86_REGISTERS and _x86_is_rm32(operands[1], line):
                return 1 + _x86_rm_length(operands[1], line)
        if mnemonic in {"shl", "sal", "shr", "sar"} and len(operands) == 2 and _x86_is_rm32(operands[0], line):
            return 1 + _x86_rm_length(operands[0], line) + (0 if operands[1].casefold() == "cl" else 1)
        raise PE32AssemblerError(f"PE32-Assemblerbefehl nicht unterstützt: {text}", line)

    for line_number, raw in enumerate(str(source).splitlines(), 1):
        text = _x86_strip_comment(raw)
        if not text:
            continue
        while True:
            match = re.match(r"^([A-Za-z_.$?@][A-Za-z0-9_.$?@]*)\s*:\s*(.*)$", text)
            if match is None:
                break
            name = match.group(1)
            key = name.casefold()
            if key in labels:
                raise PE32AssemblerError(f"Symbol mehrfach definiert: {name}", line_number)
            labels[key] = offset
            text = match.group(2).strip()
            if not text:
                break
        if not text:
            continue
        parts = text.split(None, 1)
        directive = parts[0].casefold().lstrip(".")
        args = parts[1].strip() if len(parts) > 1 else ""
        if directive in {"section", "text", "code", "global", "globl", "public", "bits", "cpu", "model"}:
            lines.append((line_number, text))
            continue
        if directive in {"extern", "extrn"}:
            for item in _x86_split_operands(args):
                if item:
                    externals.add(item.strip().casefold())
            lines.append((line_number, text))
            continue
        if directive == "import":
            operands = _x86_split_operands(args)
            if len(operands) not in {2, 3}:
                raise PE32AssemblerError(
                    'IMPORT erwartet: import symbol, "dll", "member"', line_number
                )
            symbol = _pe32_unquote(operands[0]).strip()
            dll = _pe32_unquote(operands[1]).strip()
            member = _pe32_unquote(operands[2]).strip() if len(operands) == 3 else symbol
            if not symbol or not dll or not member:
                raise PE32AssemblerError("IMPORT enthält einen leeren Namen.", line_number)
            key = symbol.casefold()
            imports[key] = (dll, member)
            externals.add(key)
            lines.append((line_number, text))
            continue
        if directive == "export":
            operands = _x86_split_operands(args)
            if len(operands) not in {1, 2}:
                raise PE32AssemblerError(
                    "EXPORT erwartet: export public_name [, internal_symbol]", line_number
                )
            public_name = _pe32_unquote(operands[0]).strip()
            internal_name = _pe32_unquote(operands[1]).strip() if len(operands) == 2 else public_name
            if not public_name or not internal_name:
                raise PE32AssemblerError("EXPORT enthält einen leeren Namen.", line_number)
            exports[public_name] = internal_name.casefold()
            lines.append((line_number, text))
            continue
        if directive == "dllname":
            if not args:
                raise PE32AssemblerError('DLLNAME erwartet z. B. dllname "mylib.dll".', line_number)
            dll_name = _pe32_unquote(args)
            lines.append((line_number, text))
            continue
        if directive == "entry":
            if not args:
                raise PE32AssemblerError(".entry erwartet ein Symbol.", line_number)
            entry_symbol = args.split()[0]
            lines.append((line_number, text))
            continue
        if directive == "align":
            alignment = _x86_parse_int(args)
            if alignment is None or alignment <= 0 or alignment & (alignment - 1):
                raise PE32AssemblerError("ALIGN erwartet eine Zweierpotenz.", line_number)
            offset = _align_up(offset, alignment)
            lines.append((line_number, text))
            continue
        if directive in {"db", "byte"}:
            offset += len(_x86_data_values(args, line_number, 1))
            lines.append((line_number, text))
            continue
        if directive in {"dw", "word"}:
            offset += len(_x86_data_values(args, line_number, 2))
            lines.append((line_number, text))
            continue
        if directive in {"dd", "dword", "long"}:
            offset += 4 * len(_x86_split_operands(args))
            lines.append((line_number, text))
            continue
        offset += instruction_size(text, line_number)
        lines.append((line_number, text))
    return (
        lines,
        labels,
        entry_symbol,
        tuple(sorted(externals)),
        imports,
        exports,
        dll_name,
    )

def assemble_pe32_object_source(
    source: str,
    *,
    filename: str = "<PE32-Assembler>",
) -> PE32ObjectProgram:
    del filename
    (
        lines, labels, entry_symbol, declared_externals,
        declared_imports, declared_exports, dll_name,
    ) = _parse_pe32_source_lines(source)
    output = bytearray()
    relocations: List[PE32Relocation] = []
    externals = set(declared_externals)
    instruction_count = 0

    def emit_symbol32(symbol: str, relocation_type: int) -> None:
        relocations.append(
            PE32Relocation(len(output), symbol.casefold(), relocation_type)
        )
        output.extend(b"\x00\x00\x00\x00")
        if symbol.casefold() not in labels:
            externals.add(symbol.casefold())

    def ensure_offset(target: int) -> None:
        if len(output) > target:
            raise PE32AssemblerError("Interner PE32-Layoutfehler.")
        if len(output) < target:
            output.extend(bytes(target - len(output)))

    def emit_rm_operand(reg_field: int, operand: str, line: int) -> None:
        encoded, symbol, relocation_local = _x86_rm_encoding(
            reg_field, operand, line
        )
        start = len(output)
        output.extend(encoded)
        if symbol is not None and relocation_local is not None:
            relocations.append(
                PE32Relocation(
                    start + relocation_local,
                    symbol.casefold(),
                    IMAGE_REL_I386_DIR32,
                )
            )
            if symbol.casefold() not in labels:
                externals.add(symbol.casefold())

    # zweiter Durchlauf: Labels liefern aus dem ersten Pass die Zieloffsets.
    cursor = 0
    label_positions = sorted((offset, name) for name, offset in labels.items())
    label_iter = iter(label_positions)
    next_label = next(label_iter, None)

    for line_number, original in lines:
        # Position auf die im ersten Durchlauf implizit berechnete Reihenfolge bringen.
        while next_label is not None and next_label[0] <= len(output):
            next_label = next(label_iter, None)
        text = _x86_strip_comment(original)
        parts = text.split(None, 1)
        directive = parts[0].casefold().lstrip(".")
        args = parts[1].strip() if len(parts) > 1 else ""
        if directive in {
            "section", "text", "code", "global", "globl", "public",
            "bits", "cpu", "model", "extern", "extrn", "entry",
            "import", "export", "dllname",
        }:
            continue
        if directive == "align":
            alignment = int(_x86_parse_int(args) or 1)
            ensure_offset(_align_up(len(output), alignment))
            continue
        if directive in {"db", "byte"}:
            output.extend(_x86_data_values(args, line_number, 1))
            continue
        if directive in {"dw", "word"}:
            output.extend(_x86_data_values(args, line_number, 2))
            continue
        if directive in {"dd", "dword", "long"}:
            for token in _x86_split_operands(args):
                value = _x86_parse_int(token)
                if value is None:
                    emit_symbol32(token, IMAGE_REL_I386_DIR32)
                else:
                    output.extend(struct.pack("<I", value & 0xFFFFFFFF))
            continue

        inst_parts = text.split(None, 1)
        mnemonic = inst_parts[0].casefold()
        operands = _x86_split_operands(inst_parts[1] if len(inst_parts) > 1 else "")
        instruction_count += 1

        # Compilerrelevante r/m32-Adressierungen. Diese Zweige stehen vor den
        # kompakten Register-/Immediate-Faellen weiter unten.
        if mnemonic in {"call", "jmp"} and len(operands) == 1:
            op_key = operands[0].casefold()
            memory = _x86_memory_operand(operands[0], line_number)
            if op_key in _X86_REGISTERS or memory is not None:
                output.append(0xFF)
                emit_rm_operand(2 if mnemonic == "call" else 4, operands[0], line_number)
                continue
        if mnemonic in {"push", "pop", "inc", "dec"} and len(operands) == 1:
            memory = _x86_memory_operand(operands[0], line_number)
            if memory is not None:
                if mnemonic == "pop":
                    output.append(0x8F)
                    emit_rm_operand(0, operands[0], line_number)
                else:
                    output.append(0xFF)
                    emit_rm_operand({"push": 6, "inc": 0, "dec": 1}[mnemonic], operands[0], line_number)
                continue
        if mnemonic == "mov" and len(operands) == 2:
            dst_key = operands[0].casefold()
            src_key = operands[1].casefold()
            dst_mem = _x86_memory_operand(operands[0], line_number)
            src_mem = _x86_memory_operand(operands[1], line_number)
            if dst_key in _X86_REGISTERS and src_mem is not None:
                output.append(0x8B)
                emit_rm_operand(_x86_reg(dst_key, line_number), operands[1], line_number)
                continue
            if dst_mem is not None and src_key in _X86_REGISTERS8:
                output.append(0x88)
                emit_rm_operand(_X86_REGISTERS8[src_key], operands[0], line_number)
                continue
            if dst_mem is not None and src_key in _X86_REGISTERS16:
                output.extend((0x66, 0x89))
                emit_rm_operand(_X86_REGISTERS16[src_key], operands[0], line_number)
                continue
            if dst_mem is not None and src_key in _X86_REGISTERS:
                output.append(0x89)
                emit_rm_operand(_x86_reg(src_key, line_number), operands[0], line_number)
                continue
            if dst_mem is not None:
                value = _x86_parse_int(operands[1])
                output.append(0xC7)
                emit_rm_operand(0, operands[0], line_number)
                if value is None:
                    emit_symbol32(operands[1], IMAGE_REL_I386_DIR32)
                else:
                    output.extend(struct.pack("<I", value & 0xFFFFFFFF))
                continue
        if mnemonic == "lea" and len(operands) == 2 and operands[0].casefold() in _X86_REGISTERS:
            if _x86_memory_operand(operands[1], line_number) is None:
                raise PE32AssemblerError("LEA erwartet einen Speicheroperanden.", line_number)
            output.append(0x8D)
            emit_rm_operand(_x86_reg(operands[0], line_number), operands[1], line_number)
            continue
        if mnemonic in {"add", "sub", "cmp", "xor", "and", "or", "test"} and len(operands) == 2:
            dst_key = operands[0].casefold()
            src_key = operands[1].casefold()
            dst_mem = _x86_memory_operand(operands[0], line_number)
            src_mem = _x86_memory_operand(operands[1], line_number)
            if src_key in _X86_REGISTERS and (dst_mem is not None):
                opcode = {"add": 0x01, "sub": 0x29, "cmp": 0x39, "xor": 0x31, "and": 0x21, "or": 0x09, "test": 0x85}[mnemonic]
                output.append(opcode)
                emit_rm_operand(_x86_reg(src_key, line_number), operands[0], line_number)
                continue
            if dst_key in _X86_REGISTERS and src_mem is not None:
                if mnemonic == "test":
                    output.append(0x85)
                    emit_rm_operand(_x86_reg(dst_key, line_number), operands[1], line_number)
                else:
                    opcode = {"add": 0x03, "sub": 0x2B, "cmp": 0x3B, "xor": 0x33, "and": 0x23, "or": 0x0B}[mnemonic]
                    output.append(opcode)
                    emit_rm_operand(_x86_reg(dst_key, line_number), operands[1], line_number)
                continue
            if dst_mem is not None:
                value = _x86_parse_int(operands[1])
                if value is not None:
                    if mnemonic == "test":
                        output.append(0xF7)
                        emit_rm_operand(0, operands[0], line_number)
                    else:
                        output.append(0x81)
                        emit_rm_operand({"add": 0, "or": 1, "and": 4, "sub": 5, "xor": 6, "cmp": 7}[mnemonic], operands[0], line_number)
                    output.extend(struct.pack("<I", value & 0xFFFFFFFF))
                    continue
        if mnemonic == "imul" and len(operands) == 2 and operands[0].casefold() in _X86_REGISTERS:
            if _x86_memory_operand(operands[1], line_number) is not None:
                output.extend((0x0F, 0xAF))
                emit_rm_operand(_x86_reg(operands[0], line_number), operands[1], line_number)
                continue
        if mnemonic in {"div", "idiv", "neg", "not"} and len(operands) == 1:
            if _x86_is_rm32(operands[0], line_number):
                output.append(0xF7)
                emit_rm_operand({"not": 2, "neg": 3, "div": 6, "idiv": 7}[mnemonic], operands[0], line_number)
                continue
        if mnemonic in {"movzx", "movsx"} and len(operands) == 2 and operands[0].casefold() in _X86_REGISTERS:
            src_key = operands[1].casefold()
            memory = _x86_memory_operand(operands[1], line_number)
            if src_key in _X86_REGISTERS8:
                output.extend((0x0F, 0xB6 if mnemonic == "movzx" else 0xBE))
                output.append(_x86_modrm(_x86_reg(operands[0], line_number), _X86_REGISTERS8[src_key]))
                continue
            if memory is not None:
                is_word = memory["size"] == "word"
                opcode = (0xB7 if is_word else 0xB6) if mnemonic == "movzx" else (0xBF if is_word else 0xBE)
                output.extend((0x0F, opcode))
                emit_rm_operand(_x86_reg(operands[0], line_number), operands[1], line_number)
                continue
        if mnemonic in _X86_SETCC and len(operands) == 1:
            output.extend((0x0F, _X86_SETCC[mnemonic]))
            dst_key = operands[0].casefold()
            if dst_key in _X86_REGISTERS8:
                output.append(_x86_modrm(0, _X86_REGISTERS8[dst_key]))
                continue
            memory = _x86_memory_operand(operands[0], line_number)
            if memory is not None:
                emit_rm_operand(0, operands[0], line_number)
                continue
            raise PE32AssemblerError("SETcc erwartet ein 8-Bit-Register oder BYTE-Speicherziel.", line_number)
        if mnemonic == "xchg" and len(operands) == 2:
            if operands[1].casefold() in _X86_REGISTERS and _x86_is_rm32(operands[0], line_number):
                output.append(0x87)
                emit_rm_operand(_x86_reg(operands[1], line_number), operands[0], line_number)
                continue
            if operands[0].casefold() in _X86_REGISTERS and _x86_is_rm32(operands[1], line_number):
                output.append(0x87)
                emit_rm_operand(_x86_reg(operands[0], line_number), operands[1], line_number)
                continue
        if mnemonic in {"shl", "sal", "shr", "sar"} and len(operands) == 2:
            if _x86_memory_operand(operands[0], line_number) is not None:
                ext = {"shl": 4, "sal": 4, "shr": 5, "sar": 7}[mnemonic]
                if operands[1].casefold() == "cl":
                    output.append(0xD3)
                    emit_rm_operand(ext, operands[0], line_number)
                else:
                    count = _x86_parse_int(operands[1])
                    if count is None or not 0 <= count <= 255:
                        raise PE32AssemblerError("Schiebeweite muss 0..255 oder CL sein.", line_number)
                    output.append(0xC1)
                    emit_rm_operand(ext, operands[0], line_number)
                    output.append(count)
                continue

        if mnemonic == "nop":
            output.append(0x90); continue
        if mnemonic == "ret":
            if not operands:
                output.append(0xC3)
            elif len(operands) == 1:
                value = _x86_parse_int(operands[0])
                if value is None or not 0 <= value <= 0xFFFF:
                    raise PE32AssemblerError("RET erwartet eine 16-Bit-Stackweite.", line_number)
                output.append(0xC2)
                output.extend(struct.pack("<H", value))
            else:
                raise PE32AssemblerError("RET erwartet höchstens einen Operanden.", line_number)
            continue
        if mnemonic == "leave":
            output.append(0xC9); continue
        if mnemonic == "int3":
            output.append(0xCC); continue
        if mnemonic == "pushad":
            output.append(0x60); continue
        if mnemonic == "popad":
            output.append(0x61); continue
        if mnemonic == "cdq":
            output.append(0x99); continue
        if mnemonic == "cld":
            output.append(0xFC); continue
        if mnemonic == "std":
            output.append(0xFD); continue
        if mnemonic == "cli":
            output.append(0xFA); continue
        if mnemonic == "sti":
            output.append(0xFB); continue
        if mnemonic == "int" and len(operands) == 1:
            value = _x86_parse_int(operands[0])
            if value is None or not 0 <= value <= 255:
                raise PE32AssemblerError("INT erwartet #0..255.", line_number)
            output.extend((0xCD, value)); continue
        if mnemonic in {"push", "pop", "inc", "dec"} and len(operands) == 1 and operands[0].casefold() in _X86_REGISTERS:
            reg = _x86_reg(operands[0], line_number)
            base = {"push": 0x50, "pop": 0x58, "inc": 0x40, "dec": 0x48}[mnemonic]
            output.append(base + reg); continue
        if mnemonic == "push" and len(operands) == 1:
            output.append(0x68)
            value = _x86_parse_int(operands[0])
            if value is None:
                emit_symbol32(operands[0], IMAGE_REL_I386_DIR32)
            else:
                output.extend(struct.pack("<I", value & 0xFFFFFFFF))
            continue
        if mnemonic in {"call", "jmp"} and len(operands) == 1:
            output.append(0xE8 if mnemonic == "call" else 0xE9)
            emit_symbol32(operands[0], IMAGE_REL_I386_REL32)
            continue
        if mnemonic in _X86_JCC and len(operands) == 1:
            output.extend((0x0F, _X86_JCC[mnemonic]))
            emit_symbol32(operands[0], IMAGE_REL_I386_REL32)
            continue
        if mnemonic == "mov" and len(operands) == 2:
            dst_key = operands[0].casefold(); src_key = operands[1].casefold()
            if dst_key in _X86_REGISTERS and src_key in _X86_REGISTERS:
                dst = _x86_reg(dst_key, line_number); src = _x86_reg(src_key, line_number)
                output.extend((0x89, _x86_modrm(src, dst))); continue
            if dst_key in _X86_REGISTERS:
                dst = _x86_reg(dst_key, line_number)
                output.append(0xB8 + dst)
                value = _x86_parse_int(operands[1])
                if value is None:
                    emit_symbol32(operands[1], IMAGE_REL_I386_DIR32)
                else:
                    output.extend(struct.pack("<I", value & 0xFFFFFFFF))
                continue
        if mnemonic in {"xor", "and", "or", "test"} and len(operands) == 2 and all(item.casefold() in _X86_REGISTERS for item in operands):
            dst = _x86_reg(operands[0], line_number); src = _x86_reg(operands[1], line_number)
            opcode = {"xor": 0x31, "and": 0x21, "or": 0x09, "test": 0x85}[mnemonic]
            output.extend((opcode, _x86_modrm(src, dst))); continue
        if mnemonic in {"xor", "and", "or", "test"} and len(operands) == 2 and operands[0].casefold() in _X86_REGISTERS:
            dst = _x86_reg(operands[0], line_number)
            value = _x86_parse_int(operands[1])
            if value is not None:
                if mnemonic == "test":
                    output.extend((0xF7, _x86_modrm(0, dst)))
                else:
                    ext = {"or": 1, "and": 4, "xor": 6}[mnemonic]
                    output.extend((0x81, _x86_modrm(ext, dst)))
                output.extend(struct.pack("<I", value & 0xFFFFFFFF)); continue
        if mnemonic in {"add", "sub", "cmp"} and len(operands) == 2 and operands[0].casefold() in _X86_REGISTERS:
            dst = _x86_reg(operands[0], line_number)
            src_key = operands[1].casefold()
            if src_key in _X86_REGISTERS:
                src = _x86_reg(src_key, line_number)
                opcode = {"add": 0x01, "sub": 0x29, "cmp": 0x39}[mnemonic]
                output.extend((opcode, _x86_modrm(src, dst))); continue
            value = _x86_parse_int(operands[1])
            if value is None:
                raise PE32AssemblerError(f"{mnemonic.upper()} erwartet Register oder Konstante.", line_number)
            ext = {"add": 0, "sub": 5, "cmp": 7}[mnemonic]
            output.extend((0x81, _x86_modrm(ext, dst)))
            output.extend(struct.pack("<I", value & 0xFFFFFFFF)); continue
        if mnemonic == "imul" and len(operands) == 2 and all(item.casefold() in _X86_REGISTERS for item in operands):
            dst = _x86_reg(operands[0], line_number); src = _x86_reg(operands[1], line_number)
            output.extend((0x0F, 0xAF, _x86_modrm(dst, src))); continue
        if mnemonic in {"shl", "sal", "shr", "sar"} and len(operands) == 2 and operands[0].casefold() in _X86_REGISTERS:
            reg = _x86_reg(operands[0], line_number)
            ext = {"shl": 4, "sal": 4, "shr": 5, "sar": 7}[mnemonic]
            if operands[1].casefold() == "cl":
                output.extend((0xD3, _x86_modrm(ext, reg))); continue
            count = _x86_parse_int(operands[1])
            if count is None or not 0 <= count <= 255:
                raise PE32AssemblerError("Schiebeweite muss 0..255 oder CL sein.", line_number)
            output.extend((0xC1, _x86_modrm(ext, reg), count)); continue
        raise PE32AssemblerError(f"PE32-Assemblerbefehl nicht unterstützt: {text}", line_number)

    return PE32ObjectProgram(
        code=bytes(output),
        symbols=dict(labels),
        externals=tuple(sorted(externals)),
        relocations=tuple(relocations),
        entry_symbol=entry_symbol.casefold(),
        imports=dict(declared_imports),
        exports=dict(declared_exports),
        dll_name=dll_name,
    )


def _pe32_apply_single_object_relocations(obj: PE32ObjectProgram) -> Tuple[bytes, int]:
    code = bytearray(obj.code)
    for relocation in obj.relocations:
        symbol = relocation.symbol.casefold()
        if symbol not in obj.symbols:
            raise PE32AssemblerError(f"Externes Symbol nicht aufgelöst: {relocation.symbol}")
        target = obj.symbols[symbol]
        if relocation.relocation_type == IMAGE_REL_I386_REL32:
            value = target - (relocation.offset + 4)
            struct.pack_into("<i", code, relocation.offset, value)
        elif relocation.relocation_type == IMAGE_REL_I386_DIR32:
            value = PE32_IMAGE_BASE + PE32_SECTION_RVA + target
            struct.pack_into("<I", code, relocation.offset, value & 0xFFFFFFFF)
        else:
            raise PE32AssemblerError(
                f"COFF32-Relocation nicht unterstützt: 0x{relocation.relocation_type:04X}"
            )
    entry = obj.symbols.get(obj.entry_symbol)
    if entry is None:
        entry = obj.symbols.get("start", obj.symbols.get("main", 0))
    return bytes(code), int(entry)


def build_pe32_executable(code: bytes, entry_offset: int = 0, *, gui: bool = False) -> bytes:
    code = bytes(code)
    dos = bytearray(0x80)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)
    pe = bytearray()
    pe.extend(b"PE\0\0")
    pe.extend(struct.pack(
        "<HHIIIHH",
        IMAGE_FILE_MACHINE_I386,
        1,
        0,
        0,
        0,
        0xE0,
        0x0102,
    ))
    raw_size = _align_up(len(code), PE32_FILE_ALIGNMENT)
    size_of_headers = PE32_FILE_ALIGNMENT
    size_of_image = _align_up(PE32_SECTION_RVA + max(1, len(code)), PE32_SECTION_ALIGNMENT)
    optional = bytearray(0xE0)
    struct.pack_into("<H", optional, 0x00, 0x010B)
    optional[0x02] = 1
    optional[0x03] = 0
    struct.pack_into("<I", optional, 0x04, raw_size)
    struct.pack_into("<I", optional, 0x08, 0)
    struct.pack_into("<I", optional, 0x0C, 0)
    struct.pack_into("<I", optional, 0x10, PE32_SECTION_RVA + int(entry_offset))
    struct.pack_into("<I", optional, 0x14, PE32_SECTION_RVA)
    struct.pack_into("<I", optional, 0x18, PE32_SECTION_RVA + raw_size)
    struct.pack_into("<I", optional, 0x1C, PE32_IMAGE_BASE)
    struct.pack_into("<I", optional, 0x20, PE32_SECTION_ALIGNMENT)
    struct.pack_into("<I", optional, 0x24, PE32_FILE_ALIGNMENT)
    struct.pack_into("<HHHH", optional, 0x28, 4, 0, 0, 0)
    struct.pack_into("<HH", optional, 0x30, 4, 0)
    struct.pack_into("<I", optional, 0x38, size_of_image)
    struct.pack_into("<I", optional, 0x3C, size_of_headers)
    struct.pack_into("<H", optional, 0x44, 2 if gui else 3)
    struct.pack_into("<H", optional, 0x46, 0)
    struct.pack_into("<IIII", optional, 0x48, 0x00100000, 0x1000, 0x00100000, 0x1000)
    struct.pack_into("<II", optional, 0x58, 0, 16)
    pe.extend(optional)
    section = bytearray(40)
    section[0:8] = b".text\0\0\0"
    struct.pack_into("<I", section, 0x08, len(code))
    struct.pack_into("<I", section, 0x0C, PE32_SECTION_RVA)
    struct.pack_into("<I", section, 0x10, raw_size)
    struct.pack_into("<I", section, 0x14, PE32_FILE_ALIGNMENT)
    # Der integrierte Assembler legt derzeit Code UND Runtime-/Pascal-Daten
    # gemeinsam in dieser Sektion ab. Deshalb muss sie bis zur spaeteren
    # Trennung in .text/.data auch schreibbar sein. Andernfalls verursacht
    # bereits `mov [stdin_handle], eax` nach AllocConsole eine Access Violation.
    struct.pack_into("<I", section, 0x24, 0xE0000020)
    pe.extend(section)
    headers = bytes(dos) + bytes(pe)
    headers += bytes(size_of_headers - len(headers))
    return headers + code + bytes(raw_size - len(code))



# Bekannte Win32-/Runtime-Imports. Externe COFF-Symbole, die nicht durch ein
# Objekt/Archiv definiert werden, können vom integrierten Linker über diese
# Tabelle automatisch in .idata und einen JMP-[IAT]-Thunk überführt werden.
PE32_DEFAULT_IMPORTS: Dict[str, Tuple[str, str]] = {
    "exitprocess": ("kernel32.dll", "ExitProcess"),
    "allocconsole": ("kernel32.dll", "AllocConsole"),
    "getstdhandle": ("kernel32.dll", "GetStdHandle"),
    "setconsolescreenbuffersize": ("kernel32.dll", "SetConsoleScreenBufferSize"),
    "setconsolewindowinfo": ("kernel32.dll", "SetConsoleWindowInfo"),
    "getconsolemode": ("kernel32.dll", "GetConsoleMode"),
    "setconsolemode": ("kernel32.dll", "SetConsoleMode"),
    "writefile": ("kernel32.dll", "WriteFile"),
    "readfile": ("kernel32.dll", "ReadFile"),
    "createfilea": ("kernel32.dll", "CreateFileA"),
    "lstrlena": ("kernel32.dll", "lstrlenA"),
    "wsprintfa": ("user32.dll", "wsprintfA"),
    "getmodulehandlea": ("kernel32.dll", "GetModuleHandleA"),
    "getprocaddress": ("kernel32.dll", "GetProcAddress"),
    "loadlibrarya": ("kernel32.dll", "LoadLibraryA"),
    "getcommandlinea": ("kernel32.dll", "GetCommandLineA"),
    "getprocessheap": ("kernel32.dll", "GetProcessHeap"),
    "heapalloc": ("kernel32.dll", "HeapAlloc"),
    "heapfree": ("kernel32.dll", "HeapFree"),
    "sleep": ("kernel32.dll", "Sleep"),
    "registerclassexa": ("user32.dll", "RegisterClassExA"),
    "createwindowexa": ("user32.dll", "CreateWindowExA"),
    "defwindowproca": ("user32.dll", "DefWindowProcA"),
    "destroywindow": ("user32.dll", "DestroyWindow"),
    "showwindow": ("user32.dll", "ShowWindow"),
    "updatewindow": ("user32.dll", "UpdateWindow"),
    "peekmessagea": ("user32.dll", "PeekMessageA"),
    "translatemessage": ("user32.dll", "TranslateMessage"),
    "dispatchmessagea": ("user32.dll", "DispatchMessageA"),
    "loadcursora": ("user32.dll", "LoadCursorA"),
    "postquitmessage": ("user32.dll", "PostQuitMessage"),
    "getclientrect": ("user32.dll", "GetClientRect"),
    "messageboxa": ("user32.dll", "MessageBoxA"),
    "d2d1createfactory": ("d2d1.dll", "D2D1CreateFactory"),
    "direct3dcreate9": ("d3d9.dll", "Direct3DCreate9"),
    "printf": ("msvcrt.dll", "printf"),
    # Gemeinsame Windows-Grafik-Runtime (Direct2D/Direct3D).
    "settextcolor": ("d64graphics.dll", "SetTextColor"),
    "clearscreen": ("d64graphics.dll", "ClearScreen"),
    "initgraphics": ("d64graphics.dll", "InitGraphics"),
    "donegraphics": ("d64graphics.dll", "DoneGraphics"),
    "setpixel": ("d64graphics.dll", "SetPixel"),
    "getpixel": ("d64graphics.dll", "GetPixel"),
    "drawline": ("d64graphics.dll", "DrawLine"),
    "drawrect": ("d64graphics.dll", "DrawRect"),
    "fillrect": ("d64graphics.dll", "FillRect"),
    "drawcircle": ("d64graphics.dll", "DrawCircle"),
    "fillcircle": ("d64graphics.dll", "FillCircle"),
    "floodfill": ("d64graphics.dll", "FloodFill"),
    "drawtriangle": ("d64graphics.dll", "DrawTriangle"),
    "filltriangle": ("d64graphics.dll", "FillTriangle"),
    "drawtriangleangles": ("d64graphics.dll", "DrawTriangleAngles"),
    "puts": ("msvcrt.dll", "puts"),
    "malloc": ("msvcrt.dll", "malloc"),
    "calloc": ("msvcrt.dll", "calloc"),
    "realloc": ("msvcrt.dll", "realloc"),
    "free": ("msvcrt.dll", "free"),
    "memcpy": ("msvcrt.dll", "memcpy"),
    "memmove": ("msvcrt.dll", "memmove"),
    "memset": ("msvcrt.dll", "memset"),
    "strlen": ("msvcrt.dll", "strlen"),
    "strcmp": ("msvcrt.dll", "strcmp"),
    "strcpy": ("msvcrt.dll", "strcpy"),
}


def _resolve_pe32_default_import(symbol: str) -> Optional[Tuple[str, str]]:
    name = str(symbol).strip().casefold()
    candidates = [name]
    if name.startswith("_"):
        candidates.append(name[1:])
    undecorated = re.sub(r"@\d+$", "", name)
    if undecorated not in candidates:
        candidates.append(undecorated)
    if undecorated.startswith("_"):
        candidates.append(undecorated[1:])
    for candidate in candidates:
        spec = PE32_DEFAULT_IMPORTS.get(candidate)
        if spec is not None:
            return spec
    return None


def _build_pe32_import_section(
    import_specs: Dict[str, Tuple[str, str]],
    idata_rva: int,
) -> Tuple[bytes, Dict[str, int], int, int]:
    grouped: Dict[str, List[str]] = {}
    for _symbol, (dll, function) in import_specs.items():
        functions = grouped.setdefault(dll, [])
        if function not in functions:
            functions.append(function)
    if not grouped:
        return b"", {}, 0, 0

    dll_items = list(grouped.items())
    descriptor_size = 20 * (len(dll_items) + 1)
    data = bytearray(descriptor_size)
    ilt_offsets: Dict[str, int] = {}
    iat_offsets: Dict[str, int] = {}
    hint_offsets: Dict[Tuple[str, str], int] = {}
    dll_name_offsets: Dict[str, int] = {}

    for dll, functions in dll_items:
        ilt_offsets[dll] = len(data)
        data.extend(bytes(4 * (len(functions) + 1)))
    for dll, functions in dll_items:
        iat_offsets[dll] = len(data)
        data.extend(bytes(4 * (len(functions) + 1)))
    for dll, functions in dll_items:
        for function in functions:
            if len(data) & 1:
                data.append(0)
            hint_offsets[(dll, function)] = len(data)
            data.extend(struct.pack("<H", 0))
            data.extend(function.encode("ascii") + b"\0")
    for dll, _functions in dll_items:
        dll_name_offsets[dll] = len(data)
        data.extend(dll.encode("ascii") + b"\0")

    iat_by_spec: Dict[Tuple[str, str], int] = {}
    first_iat_rva = 0
    total_iat_size = 0
    for descriptor_index, (dll, functions) in enumerate(dll_items):
        ilt_rva = idata_rva + ilt_offsets[dll]
        iat_rva = idata_rva + iat_offsets[dll]
        if first_iat_rva == 0:
            first_iat_rva = iat_rva
        total_iat_size += 4 * (len(functions) + 1)
        name_rva = idata_rva + dll_name_offsets[dll]
        struct.pack_into(
            "<IIIII",
            data,
            descriptor_index * 20,
            ilt_rva,
            0,
            0,
            name_rva,
            iat_rva,
        )
        for function_index, function in enumerate(functions):
            hint_rva = idata_rva + hint_offsets[(dll, function)]
            struct.pack_into(
                "<I", data, ilt_offsets[dll] + function_index * 4, hint_rva
            )
            struct.pack_into(
                "<I", data, iat_offsets[dll] + function_index * 4, hint_rva
            )
            iat_by_spec[(dll, function)] = iat_rva + function_index * 4

    symbol_iat_rvas = {
        symbol: iat_by_spec[spec]
        for symbol, spec in import_specs.items()
    }
    return bytes(data), symbol_iat_rvas, first_iat_rva, total_iat_size


def _build_pe32_reloc_section(rvas: Sequence[int]) -> bytes:
    """Erzeugt IMAGE_BASE_RELOCATION-Bloecke fuer HIGHLOW-Fixups."""
    pages: Dict[int, List[int]] = {}
    for raw_rva in sorted({int(value) for value in rvas if int(value) >= 0}):
        page_rva = raw_rva & ~0xFFF
        pages.setdefault(page_rva, []).append(raw_rva & 0xFFF)
    data = bytearray()
    for page_rva, offsets in sorted(pages.items()):
        entries = [((3 << 12) | offset) for offset in offsets]  # HIGHLOW
        block_size = 8 + len(entries) * 2
        if block_size & 3:
            entries.append(0)  # IMAGE_REL_BASED_ABSOLUTE als Padding
            block_size += 2
        data.extend(struct.pack("<II", page_rva, block_size))
        for entry in entries:
            data.extend(struct.pack("<H", entry))
    return bytes(data)


def _build_pe32_export_section(
    exports: Dict[str, int],
    dll_name: str,
    edata_rva: int,
    text_rva: int,
) -> bytes:
    """Erzeugt IMAGE_EXPORT_DIRECTORY + EAT/Name/Ordinal-Tabellen."""
    items = sorted(
        ((str(public), int(offset)) for public, offset in exports.items()),
        key=lambda item: item[0].casefold(),
    )
    if not items:
        return b""

    count = len(items)
    directory_size = 40
    eat_offset = directory_size
    name_pointer_offset = eat_offset + count * 4
    ordinal_offset = name_pointer_offset + count * 4
    data = bytearray(ordinal_offset + count * 2)

    dll_name_bytes = (str(dll_name or "library.dll").encode("ascii", errors="replace") + b"\0")
    dll_name_offset = len(data)
    data.extend(dll_name_bytes)

    export_name_offsets: List[int] = []
    for public_name, _offset in items:
        export_name_offsets.append(len(data))
        data.extend(public_name.encode("ascii", errors="replace") + b"\0")

    struct.pack_into(
        "<IIHHIIIIIII",
        data,
        0,
        0,  # Characteristics
        0,  # TimeDateStamp
        0,  # MajorVersion
        0,  # MinorVersion
        edata_rva + dll_name_offset,
        1,  # Ordinal Base
        count,
        count,
        edata_rva + eat_offset,
        edata_rva + name_pointer_offset,
        edata_rva + ordinal_offset,
    )
    for index, ((_public_name, code_offset), name_offset) in enumerate(
        zip(items, export_name_offsets)
    ):
        struct.pack_into("<I", data, eat_offset + index * 4, text_rva + code_offset)
        struct.pack_into(
            "<I", data, name_pointer_offset + index * 4, edata_rva + name_offset
        )
        struct.pack_into("<H", data, ordinal_offset + index * 2, index)
    return bytes(data)


def build_pe32_image_with_imports_exports(
    code: bytes,
    entry_offset: Optional[int],
    import_specs: Dict[str, Tuple[str, str]],
    thunk_patches: Dict[str, int],
    *,
    exports: Optional[Dict[str, int]] = None,
    dll_name: str = "library.dll",
    gui: bool = False,
    dll: bool = False,
    image_base: int = PE32_IMAGE_BASE,
    base_relocations: Optional[Sequence[int]] = None,
) -> Tuple[bytes, bytes]:
    """Schreibt ein vollständiges PE32-EXE- oder DLL-Image intern.

    Es werden keine externen Compiler, Assembler oder Linker verwendet.
    ``code`` ist bereits aus internen COFF32-Objekten zusammengeführt.
    """
    text = bytearray(code)
    text_rva = PE32_SECTION_RVA

    idata = b""
    iat_rvas: Dict[str, int] = {}
    first_iat_rva = 0
    iat_size = 0
    idata_rva = 0
    next_rva = _align_up(text_rva + max(1, len(text)), PE32_SECTION_ALIGNMENT)
    if import_specs:
        idata_rva = next_rva
        idata, iat_rvas, first_iat_rva, iat_size = _build_pe32_import_section(
            import_specs, idata_rva
        )
        next_rva = _align_up(
            idata_rva + max(1, len(idata)), PE32_SECTION_ALIGNMENT
        )

    for symbol, patch_offset in thunk_patches.items():
        if symbol not in iat_rvas:
            raise PE32AssemblerError(
                f"Interner PE32-Linkerfehler: IAT-Eintrag fehlt für {symbol}."
            )
        struct.pack_into(
            "<I", text, patch_offset, int(image_base) + iat_rvas[symbol]
        )

    export_offsets = dict(exports or {})
    edata = b""
    edata_rva = 0
    if export_offsets:
        edata_rva = next_rva
        edata = _build_pe32_export_section(
            export_offsets, dll_name, edata_rva, text_rva
        )
        next_rva = _align_up(
            edata_rva + max(1, len(edata)), PE32_SECTION_ALIGNMENT
        )

    reloc = b""
    reloc_rva = 0
    requested_relocations = tuple(base_relocations or ())
    if requested_relocations:
        reloc_rva = next_rva
        reloc = _build_pe32_reloc_section(requested_relocations)
        next_rva = _align_up(
            reloc_rva + max(1, len(reloc)), PE32_SECTION_ALIGNMENT
        )

    sections: List[Tuple[bytes, bytes, int, int]] = []
    # Gemischte Code-/Datensektion des internen Assemblers: EXECUTE | READ |
    # WRITE | CODE. Runtime-Variablen wie stdout_handle/read_count liegen bis
    # zur echten .data-Aufteilung ebenfalls hier und werden zur Laufzeit
    # beschrieben.
    sections.append((b".text\0\0\0", bytes(text), text_rva, 0xE0000020))
    if idata:
        sections.append((b".idata\0\0", idata, idata_rva, 0xC0000040))
    if edata:
        sections.append((b".edata\0\0", edata, edata_rva, 0x40000040))
    if reloc:
        sections.append((b".reloc\0\0", reloc, reloc_rva, 0x42000040))

    number_of_sections = len(sections)
    headers_unaligned = 0x80 + 4 + 20 + 0xE0 + number_of_sections * 40
    size_of_headers = _align_up(headers_unaligned, PE32_FILE_ALIGNMENT)

    raw_layout: List[Tuple[bytes, bytes, int, int, int, int]] = []
    raw_pointer = size_of_headers
    size_of_code = 0
    size_of_initialized_data = 0
    for name, data, rva, characteristics in sections:
        raw_size = _align_up(len(data), PE32_FILE_ALIGNMENT)
        raw_layout.append((name, data, rva, characteristics, raw_pointer, raw_size))
        raw_pointer += raw_size
        if name.startswith(b".text"):
            size_of_code += raw_size
        else:
            size_of_initialized_data += raw_size

    size_of_image = _align_up(next_rva, PE32_SECTION_ALIGNMENT)

    dos = bytearray(0x80)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)
    pe = bytearray(b"PE\0\0")
    characteristics = 0x0102 | (0x2000 if dll else 0)
    pe.extend(struct.pack(
        "<HHIIIHH",
        IMAGE_FILE_MACHINE_I386,
        number_of_sections,
        0,
        0,
        0,
        0xE0,
        characteristics,
    ))

    optional = bytearray(0xE0)
    struct.pack_into("<H", optional, 0x00, 0x010B)
    optional[0x02] = 1
    struct.pack_into("<I", optional, 0x04, size_of_code)
    struct.pack_into("<I", optional, 0x08, size_of_initialized_data)
    address_of_entry = 0 if entry_offset is None else text_rva + int(entry_offset)
    struct.pack_into("<I", optional, 0x10, address_of_entry)
    struct.pack_into("<I", optional, 0x14, text_rva)
    first_data_rva = idata_rva or edata_rva or 0
    struct.pack_into("<I", optional, 0x18, first_data_rva)
    struct.pack_into("<I", optional, 0x1C, int(image_base))
    struct.pack_into("<I", optional, 0x20, PE32_SECTION_ALIGNMENT)
    struct.pack_into("<I", optional, 0x24, PE32_FILE_ALIGNMENT)
    struct.pack_into("<HHHH", optional, 0x28, 4, 0, 0, 0)
    struct.pack_into("<HH", optional, 0x30, 4, 0)
    struct.pack_into("<I", optional, 0x38, size_of_image)
    struct.pack_into("<I", optional, 0x3C, size_of_headers)
    struct.pack_into("<H", optional, 0x44, 2 if gui else 3)
    struct.pack_into(
        "<H", optional, 0x46,
        0x0040 if (dll and reloc) else 0,  # DYNAMIC_BASE bei Relokationen
    )
    struct.pack_into(
        "<IIII", optional, 0x48,
        0x00100000, 0x1000, 0x00100000, 0x1000,
    )
    struct.pack_into("<II", optional, 0x58, 0, 16)
    if edata:
        struct.pack_into("<II", optional, 0x60, edata_rva, len(edata))
    if idata:
        struct.pack_into("<II", optional, 0x68, idata_rva, len(idata))
        struct.pack_into("<II", optional, 0xC0, first_iat_rva, iat_size)
    if reloc:
        # DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC] (Index 5).
        struct.pack_into("<II", optional, 0x88, reloc_rva, len(reloc))
    pe.extend(optional)

    for name, data, rva, section_chars, section_raw_pointer, raw_size in raw_layout:
        section = bytearray(40)
        section[0:8] = name[:8].ljust(8, b"\0")
        struct.pack_into("<I", section, 0x08, len(data))
        struct.pack_into("<I", section, 0x0C, rva)
        struct.pack_into("<I", section, 0x10, raw_size)
        struct.pack_into("<I", section, 0x14, section_raw_pointer)
        struct.pack_into("<I", section, 0x24, section_chars)
        pe.extend(section)

    headers = bytes(dos) + bytes(pe)
    headers += bytes(size_of_headers - len(headers))
    image = bytearray(headers)
    for _name, data, _rva, _chars, _raw_pointer, raw_size in raw_layout:
        image.extend(data)
        image.extend(bytes(raw_size - len(data)))
    return bytes(image), bytes(text)


def build_pe32_executable_with_imports(
    code: bytes,
    entry_offset: int,
    import_specs: Dict[str, Tuple[str, str]],
    thunk_patches: Dict[str, int],
    *,
    gui: bool = False,
) -> Tuple[bytes, bytes]:
    return build_pe32_image_with_imports_exports(
        code,
        entry_offset,
        import_specs,
        thunk_patches,
        gui=gui,
        dll=False,
    )

def assemble_pe32_source(
    source: str,
    *,
    filename: str = "<PE32-Assembler>",
    gui: bool = False,
) -> PE32Program:
    """Assembliert IA-32 und linkt bekannte Win32-Imports direkt in PE32."""
    obj = assemble_pe32_object_source(source, filename=filename)
    linked = link_coff32_objects(
        (write_coff32_object(obj),),
        entry_symbol=obj.entry_symbol or "_start",
        gui=gui,
    )
    instruction_count = sum(
        1 for line in str(source).splitlines()
        if _x86_strip_comment(line)
        and not _x86_strip_comment(line).lstrip().startswith(
            (".", "section ", "global ", "extern ", "db ", "dw ", "dd ")
        )
    )
    return PE32Program(
        executable=linked.executable,
        code=linked.code,
        entry_offset=linked.entry_offset,
        instruction_count=instruction_count,
        symbols=dict(linked.symbols),
    )


def _coff_symbol_name_bytes(name: str, string_table: bytearray) -> bytes:
    encoded = str(name).encode("utf-8")
    if len(encoded) <= 8:
        return encoded.ljust(8, b"\0")
    offset = 4 + len(string_table)
    string_table.extend(encoded + b"\0")
    return struct.pack("<II", 0, offset)


def _coff32_metadata_bytes(obj: PE32ObjectProgram) -> bytes:
    document = {
        "format": "d64-coff32-link-v1",
        "entry": obj.entry_symbol,
        "imports": {
            symbol: {"dll": spec[0], "member": spec[1]}
            for symbol, spec in sorted(obj.imports.items())
        },
        "exports": dict(obj.exports),
        "dll_name": obj.dll_name,
    }
    if not document["imports"] and not document["exports"] and not document["dll_name"]:
        return b""
    return (json.dumps(document, ensure_ascii=True, sort_keys=True) + "\n").encode("ascii")


def write_coff32_object(obj: PE32ObjectProgram) -> bytes:
    """Schreibt ein Microsoft-COFF32-Objekt ohne externen Assembler.

    Linker-Metadaten werden optional in einer echten ``.drectve``-Sektion
    gespeichert. Dadurch bleiben DLL-Import-/Exportinformationen auch nach
    dem Ablegen in einer ``.o``-Datei oder einem ``.a``-Archiv erhalten.
    """
    all_names = list(obj.symbols.keys())
    for name in obj.externals:
        if name not in all_names:
            all_names.append(name)
    symbol_index = {name: index for index, name in enumerate(all_names)}

    metadata = _coff32_metadata_bytes(obj)
    section_count = 2 if metadata else 1
    header_size = 20 + section_count * 40
    text_raw_pointer = header_size
    drectve_raw_pointer = text_raw_pointer + len(obj.code) if metadata else 0
    relocation_pointer = text_raw_pointer + len(obj.code) + len(metadata)
    symbol_pointer = relocation_pointer + len(obj.relocations) * 10

    header = struct.pack(
        "<HHIIIHH",
        IMAGE_FILE_MACHINE_I386,
        section_count,
        0,
        symbol_pointer,
        len(all_names),
        0,
        0,
    )

    text_section = bytearray(40)
    text_section[0:8] = b".text\0\0\0"
    struct.pack_into("<I", text_section, 0x10, len(obj.code))
    struct.pack_into("<I", text_section, 0x14, text_raw_pointer)
    struct.pack_into(
        "<I", text_section, 0x18,
        relocation_pointer if obj.relocations else 0,
    )
    struct.pack_into("<H", text_section, 0x20, len(obj.relocations))
    # Das COFF32-Objekt enthaelt derzeit Code und Daten gemeinsam in .text.
    # IMAGE_SCN_MEM_WRITE muss deshalb erhalten bleiben, damit auch ein spaeter
    # gelinktes Objekt seine Runtime-/Variablendaten beschreiben darf.
    struct.pack_into("<I", text_section, 0x24, 0xE0500020)

    section_headers = bytearray(text_section)
    if metadata:
        drectve_section = bytearray(40)
        drectve_section[0:8] = b".drectve"
        struct.pack_into("<I", drectve_section, 0x10, len(metadata))
        struct.pack_into("<I", drectve_section, 0x14, drectve_raw_pointer)
        # IMAGE_SCN_LNK_INFO | IMAGE_SCN_LNK_REMOVE | ALIGN_1BYTES
        struct.pack_into("<I", drectve_section, 0x24, 0x00100A00)
        section_headers.extend(drectve_section)

    relocation_bytes = bytearray()
    for relocation in obj.relocations:
        if relocation.symbol not in symbol_index:
            raise PE32AssemblerError(f"COFF-Symbol fehlt: {relocation.symbol}")
        relocation_bytes.extend(struct.pack(
            "<IIH",
            relocation.offset,
            symbol_index[relocation.symbol],
            relocation.relocation_type,
        ))

    strings = bytearray()
    symbols = bytearray()
    for name in all_names:
        symbols.extend(_coff_symbol_name_bytes(name, strings))
        defined = name in obj.symbols
        value = obj.symbols.get(name, 0)
        symbols.extend(struct.pack(
            "<IhHBB",
            int(value),
            1 if defined else 0,
            0,
            2,
            0,
        ))
    string_table = struct.pack("<I", 4 + len(strings)) + bytes(strings)
    return (
        header
        + bytes(section_headers)
        + obj.code
        + metadata
        + bytes(relocation_bytes)
        + bytes(symbols)
        + string_table
    )


def assemble_pe32_coff_object(
    source: str,
    *,
    filename: str = "<PE32-Assembler>",
) -> bytes:
    return write_coff32_object(
        assemble_pe32_object_source(source, filename=filename)
    )


def parse_coff32_object(data: bytes) -> Coff32ParsedObject:
    payload = bytes(data)
    if len(payload) < 60:
        raise PE32AssemblerError("COFF32-Objekt ist zu klein.")
    machine, sections, _timestamp, symbol_pointer, symbol_count, optional_size, _chars = struct.unpack_from(
        "<HHIIIHH", payload, 0
    )
    if machine != IMAGE_FILE_MACHINE_I386 or sections < 1 or optional_size != 0:
        raise PE32AssemblerError(
            "Nur relocierbare IA-32-COFF-Objekte werden unterstützt."
        )

    text_info = None
    metadata_payload = b""
    for section_index in range(sections):
        section_offset = 20 + section_index * 40
        if section_offset + 40 > len(payload):
            raise PE32AssemblerError("COFF32-Sektionstabelle ist beschädigt.")
        name = payload[section_offset:section_offset + 8].rstrip(b"\0")
        raw_size, raw_pointer, reloc_pointer = struct.unpack_from(
            "<III", payload, section_offset + 0x10
        )
        reloc_count = struct.unpack_from("<H", payload, section_offset + 0x20)[0]
        if raw_pointer and raw_pointer + raw_size > len(payload):
            raise PE32AssemblerError("COFF32-Sektion liegt außerhalb der Datei.")
        if name == b".text":
            text_info = (raw_size, raw_pointer, reloc_pointer, reloc_count)
        elif name == b".drectve" and raw_pointer:
            metadata_payload = payload[raw_pointer:raw_pointer + raw_size]

    if text_info is None:
        raise PE32AssemblerError("COFF32-Objekt enthält keine .text-Sektion.")
    raw_size, raw_pointer, reloc_pointer, reloc_count = text_info
    code = payload[raw_pointer:raw_pointer + raw_size]

    string_table_offset = symbol_pointer + symbol_count * 18
    if string_table_offset + 4 > len(payload):
        raise PE32AssemblerError("COFF32-Symboltabelle ist beschädigt.")
    string_size = struct.unpack_from("<I", payload, string_table_offset)[0]
    string_table = payload[
        string_table_offset:string_table_offset + max(4, string_size)
    ]
    symbol_names: List[str] = []
    symbols: Dict[str, Optional[int]] = {}
    index = 0
    while index < symbol_count:
        offset = symbol_pointer + index * 18
        raw_name = payload[offset:offset + 8]
        zeroes, string_offset = struct.unpack("<II", raw_name)
        if zeroes == 0 and string_offset:
            relative = string_offset
            end = string_table.find(b"\0", relative)
            if end < 0:
                end = len(string_table)
            symbol_name = string_table[relative:end].decode(
                "utf-8", errors="replace"
            )
        else:
            symbol_name = raw_name.rstrip(b"\0").decode(
                "ascii", errors="replace"
            )
        value, section_number, _type, _storage, aux_count = struct.unpack_from(
            "<IhHBB", payload, offset + 8
        )
        key = symbol_name.casefold()
        symbol_names.append(key)
        symbols[key] = int(value) if section_number == 1 else None
        for _ in range(aux_count):
            index += 1
            symbol_names.append("")
        index += 1

    relocations = []
    for rel_index in range(reloc_count):
        offset = reloc_pointer + rel_index * 10
        if offset + 10 > len(payload):
            raise PE32AssemblerError("COFF32-Relocationstabelle ist beschädigt.")
        virtual_address, symbol_table_index, relocation_type = struct.unpack_from(
            "<IIH", payload, offset
        )
        if symbol_table_index >= len(symbol_names):
            raise PE32AssemblerError(
                "COFF32-Relocation verweist auf ein ungültiges Symbol."
            )
        symbol_name = symbol_names[symbol_table_index]
        relocations.append(
            PE32Relocation(virtual_address, symbol_name, relocation_type)
        )

    imports: Dict[str, Tuple[str, str]] = {}
    exports: Dict[str, str] = {}
    dll_name: Optional[str] = None
    if metadata_payload.strip():
        try:
            document = json.loads(metadata_payload.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PE32AssemblerError(
                "COFF32-.drectve enthält ungültige d64-Linker-Metadaten."
            ) from exc
        if isinstance(document, dict) and document.get("format") == "d64-coff32-link-v1":
            raw_imports = document.get("imports", {})
            if isinstance(raw_imports, dict):
                for symbol, spec in raw_imports.items():
                    if isinstance(spec, dict):
                        dll = str(spec.get("dll", "")).strip()
                        member = str(spec.get("member", "")).strip()
                        if dll and member:
                            imports[str(symbol).casefold()] = (dll, member)
            raw_exports = document.get("exports", {})
            if isinstance(raw_exports, dict):
                for public_name, internal_name in raw_exports.items():
                    public = str(public_name).strip()
                    internal = str(internal_name).strip().casefold()
                    if public and internal:
                        exports[public] = internal
            raw_dll_name = document.get("dll_name")
            if raw_dll_name:
                dll_name = str(raw_dll_name)

    return Coff32ParsedObject(
        code,
        symbols,
        tuple(relocations),
        imports=imports,
        exports=exports,
        dll_name=dll_name,
    )


AR_MAGIC = b"!<arch>\n"


def create_coff32_archive(members: Sequence[Tuple[str, bytes]]) -> bytes:
    output = bytearray(AR_MAGIC)
    for name, data in members:
        clean = Path(str(name)).name.encode("ascii", errors="replace")[:15]
        member_name = clean + b"/"
        header = (
            member_name.ljust(16, b" ")
            + b"0".ljust(12, b" ")
            + b"0".ljust(6, b" ")
            + b"0".ljust(6, b" ")
            + b"100644".ljust(8, b" ")
            + str(len(data)).encode("ascii").ljust(10, b" ")
            + b"`\n"
        )
        output.extend(header)
        output.extend(data)
        if len(data) & 1:
            output.extend(b"\n")
    return bytes(output)


def parse_coff32_archive(data: bytes) -> Tuple[Tuple[str, bytes], ...]:
    payload = bytes(data)
    if not payload.startswith(AR_MAGIC):
        raise PE32AssemblerError("Ungültiges .a/.lib-Archiv.")
    offset = len(AR_MAGIC)
    members = []
    while offset + 60 <= len(payload):
        header = payload[offset:offset + 60]
        offset += 60
        if header[58:60] != b"`\n":
            raise PE32AssemblerError("Beschädigter Archivkopf.")
        name = header[:16].decode("ascii", errors="replace").strip().rstrip("/")
        try:
            size = int(header[48:58].decode("ascii").strip() or "0")
        except ValueError as exc:
            raise PE32AssemblerError("Ungültige Archiv-Mitgliedsgröße.") from exc
        if offset + size > len(payload):
            raise PE32AssemblerError("Archivmitglied liegt außerhalb der Datei.")
        members.append((name, payload[offset:offset + size]))
        offset += size + (size & 1)
    return tuple(members)


def link_coff32_objects(
    objects: Sequence[bytes],
    *,
    entry_symbol: str = "_start",
    gui: bool = False,
    dll: bool = False,
    imports: Optional[Dict[str, Tuple[str, str]]] = None,
    exports: Optional[Dict[str, str]] = None,
    dll_name: Optional[str] = None,
) -> PE32Program:
    """Linkt interne COFF32-Objekte zu einer PE32-EXE oder -DLL.

    Import- und Exportinformationen werden primär aus der ``.drectve``-Sektion
    der Objekte übernommen. Zusätzlich können sie programmgesteuert ergänzt
    werden. Nicht explizit zugeordnete Win32-Symbole dürfen weiterhin über
    ``PE32_DEFAULT_IMPORTS`` aufgelöst werden.
    """
    parsed = [parse_coff32_object(item) for item in objects]
    code = bytearray()
    object_bases: List[int] = []
    globals_map: Dict[str, int] = {}

    declared_imports: Dict[str, Tuple[str, str]] = {}
    declared_exports: Dict[str, str] = {}
    declared_dll_name: Optional[str] = None

    for obj in parsed:
        for symbol, spec in obj.imports.items():
            key = symbol.casefold()
            previous = declared_imports.get(key)
            if previous is not None and previous != spec:
                raise PE32AssemblerError(
                    f"COFF32-Import {symbol} besitzt widersprüchliche DLL-Ziele."
                )
            declared_imports[key] = spec
        for public_name, internal_name in obj.exports.items():
            previous = declared_exports.get(public_name)
            if previous is not None and previous.casefold() != internal_name.casefold():
                raise PE32AssemblerError(
                    f"COFF32-Export {public_name} ist mehrfach unterschiedlich definiert."
                )
            declared_exports[public_name] = internal_name.casefold()
        if obj.dll_name:
            if declared_dll_name is not None and declared_dll_name.casefold() != obj.dll_name.casefold():
                raise PE32AssemblerError(
                    "COFF32-Objekte enthalten unterschiedliche DLLNAME-Angaben."
                )
            declared_dll_name = obj.dll_name

    for symbol, spec in (imports or {}).items():
        declared_imports[str(symbol).casefold()] = (str(spec[0]), str(spec[1]))
    for public_name, internal_name in (exports or {}).items():
        declared_exports[str(public_name)] = str(internal_name).casefold()
    if dll_name:
        declared_dll_name = str(dll_name)

    effective_dll = bool(dll or declared_exports)
    image_base = PE32_DLL_IMAGE_BASE if effective_dll else PE32_IMAGE_BASE
    base_relocations: List[int] = []

    for obj in parsed:
        base = _align_up(len(code), 16)
        if base > len(code):
            code.extend(bytes(base - len(code)))
        object_bases.append(base)
        code.extend(obj.code)
        for name, value in obj.symbols.items():
            if value is None:
                continue
            if name in globals_map:
                raise PE32AssemblerError(
                    f"COFF32-Symbol mehrfach definiert: {name}"
                )
            globals_map[name] = base + value

    # DLL-Imports werden vor der Relocation-Phase als lokale JMP-IAT-Thunks
    # materialisiert. CALL/JMP aus allen COFF32-Objekten bleiben damit REL32.
    import_specs: Dict[str, Tuple[str, str]] = {}
    thunk_patches: Dict[str, int] = {}
    unresolved_symbols: List[str] = []
    for obj in parsed:
        for relocation in obj.relocations:
            symbol = relocation.symbol.casefold()
            if symbol in globals_map or symbol in import_specs:
                continue
            spec = declared_imports.get(symbol)
            if spec is None:
                spec = _resolve_pe32_default_import(symbol)
            if spec is None:
                unresolved_symbols.append(symbol)
                continue
            thunk_offset = _align_up(len(code), 4)
            if thunk_offset > len(code):
                code.extend(bytes(thunk_offset - len(code)))
            # FF 25 imm32 -> JMP DWORD PTR [absolute IAT address]
            code.extend(b"\xFF\x25\x00\x00\x00\x00")
            globals_map[symbol] = thunk_offset
            import_specs[symbol] = spec
            thunk_patches[symbol] = thunk_offset + 2
            if effective_dll:
                base_relocations.append(PE32_SECTION_RVA + thunk_offset + 2)

    if unresolved_symbols:
        unique = []
        seen = set()
        for symbol in unresolved_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique.append(symbol)
        raise PE32AssemblerError(
            "COFF32-Linker: externe Symbole nicht aufgeloest: "
            + ", ".join(unique)
        )

    for obj, base in zip(parsed, object_bases):
        for relocation in obj.relocations:
            target = globals_map.get(relocation.symbol.casefold())
            if target is None:
                raise PE32AssemblerError(
                    "COFF32-Linker: externes Symbol nicht aufgeloest: "
                    f"{relocation.symbol}"
                )
            patch = base + relocation.offset
            if relocation.relocation_type == IMAGE_REL_I386_REL32:
                struct.pack_into("<i", code, patch, target - (patch + 4))
            elif relocation.relocation_type == IMAGE_REL_I386_DIR32:
                struct.pack_into(
                    "<I",
                    code,
                    patch,
                    image_base + PE32_SECTION_RVA + target,
                )
                if effective_dll:
                    base_relocations.append(PE32_SECTION_RVA + patch)
            else:
                raise PE32AssemblerError(
                    "COFF32-Linker: Relocation "
                    f"0x{relocation.relocation_type:04X} nicht unterstuetzt."
                )

    wanted = str(entry_symbol or "").strip()
    entry: Optional[int] = None
    if wanted:
        entry = globals_map.get(wanted.casefold())
        if entry is None and not effective_dll:
            for fallback in ("_start", "start", "main", "_main"):
                entry = globals_map.get(fallback)
                if entry is not None:
                    break
    if entry is None and not effective_dll:
        entry = 0

    export_offsets: Dict[str, int] = {}
    for public_name, internal_name in declared_exports.items():
        target = globals_map.get(internal_name.casefold())
        if target is None:
            raise PE32AssemblerError(
                f"DLL-Export {public_name} verweist auf unbekanntes Symbol {internal_name}."
            )
        export_offsets[public_name] = target

    effective_dll = bool(effective_dll or export_offsets)
    final_dll_name = declared_dll_name or "library.dll"

    # Auch eine rein REL32-basierte DLL soll verschiebbar bleiben. Falls der
    # eigentliche Code keinen absoluten Fixup benötigt, legen wir am Ende der
    # .text-Sektion einen unbenutzten 32-Bit-Relocation-Anker ab.
    if effective_dll and not base_relocations:
        anchor_offset = _align_up(len(code), 4)
        if anchor_offset > len(code):
            code.extend(bytes(anchor_offset - len(code)))
        code.extend(struct.pack(
            "<I", image_base + PE32_SECTION_RVA + anchor_offset
        ))
        base_relocations.append(PE32_SECTION_RVA + anchor_offset)

    executable, patched_code = build_pe32_image_with_imports_exports(
        bytes(code),
        entry,
        import_specs,
        thunk_patches,
        exports=export_offsets,
        dll_name=final_dll_name,
        gui=gui,
        dll=effective_dll,
        image_base=image_base,
        base_relocations=base_relocations,
    )
    return PE32Program(
        executable=executable,
        code=patched_code,
        entry_offset=int(entry or 0),
        instruction_count=0,
        symbols=globals_map,
    )

def link_coff32_inputs(
    paths: Sequence[Path],
    *,
    entry_symbol: str = "_start",
    gui: bool = False,
    dll: bool = False,
    imports: Optional[Dict[str, Tuple[str, str]]] = None,
    exports: Optional[Dict[str, str]] = None,
    dll_name: Optional[str] = None,
) -> PE32Program:
    objects: List[bytes] = []
    for path_value in paths:
        path = Path(path_value)
        data = path.read_bytes()
        if path.suffix.casefold() in {".a", ".lib"}:
            for _name, member_data in parse_coff32_archive(data):
                objects.append(member_data)
        else:
            objects.append(data)
    if not objects:
        raise PE32AssemblerError("Der COFF32-Linker benötigt mindestens ein Objekt.")
    return link_coff32_objects(
        objects,
        entry_symbol=entry_symbol,
        gui=gui,
        dll=dll,
        imports=imports,
        exports=exports,
        dll_name=dll_name,
    )


# ---------------------------------------------------------------------------
# Windows-Grafik-ABI. Die Compiler können über target='pe32' und die beiden
# Präprozessor-Symbole die passende Runtime auswählen. Die eigentliche
# Direct2D/Direct3D-Runtime kann dadurch plattformgetrennt bleiben, während
# die öffentliche Grafik-API identisch bleibt.
# ---------------------------------------------------------------------------
def windows_graphics_predefined_macros(backend: str) -> Dict[str, str]:
    selected = normalize_windows_graphics_backend(backend)
    macros = {
        "__D64_TARGET_PE32__": "1",
        "__D64_GRAPHICS_WINDOWS__": "1",
    }
    if selected == "Direct3D":
        macros["__D64_GRAPHICS_DIRECT3D__"] = "1"
    else:
        macros["__D64_GRAPHICS_DIRECT2D__"] = "1"
    return macros


WINDOWS_GRAPHICS_RUNTIME_HEADER = r'''#ifndef D64_WINDOWS_GRAPHICS_H
#define D64_WINDOWS_GRAPHICS_H

#include <stdint.h>

#if defined(_WIN32)
# if defined(D64_GRAPHICS_RUNTIME_EXPORTS)
#  define D64_GRAPHICS_API __declspec(dllexport)
# else
#  define D64_GRAPHICS_API __declspec(dllimport)
# endif
#else
# define D64_GRAPHICS_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define GRAPHICS_WIDTH  320
#define GRAPHICS_HEIGHT 200

typedef uint8_t GraphicsColor;
typedef uint8_t TextMode;

D64_GRAPHICS_API void SetTextColor(unsigned int foreground, unsigned int background);
D64_GRAPHICS_API void ClearScreen(void);
D64_GRAPHICS_API void InitGraphics(void);
D64_GRAPHICS_API void DoneGraphics(TextMode mode);
D64_GRAPHICS_API void SetPixel(int x, int y, GraphicsColor color);
D64_GRAPHICS_API GraphicsColor GetPixel(int x, int y);
D64_GRAPHICS_API void DrawLine(int x1, int y1, int x2, int y2, GraphicsColor color);
D64_GRAPHICS_API void DrawRect(int x1, int y1, int x2, int y2, GraphicsColor color);
D64_GRAPHICS_API void FillRect(int x1, int y1, int x2, int y2,
                              GraphicsColor fillColor,
                              GraphicsColor borderColor,
                              unsigned int borderWidth);
D64_GRAPHICS_API void DrawCircle(int centerX, int centerY, int radius, GraphicsColor color);
D64_GRAPHICS_API void FillCircle(int centerX, int centerY, int radius,
                                GraphicsColor fillColor,
                                GraphicsColor borderColor,
                                unsigned int borderWidth);
D64_GRAPHICS_API void FloodFill(int x, int y, GraphicsColor fillColor);
D64_GRAPHICS_API void DrawTriangle(int x1, int y1, int x2, int y2,
                                  int x3, int y3, GraphicsColor color);
D64_GRAPHICS_API void FillTriangle(int x1, int y1, int x2, int y2,
                                  int x3, int y3,
                                  GraphicsColor fillColor,
                                  GraphicsColor borderColor,
                                  unsigned int borderWidth);
D64_GRAPHICS_API void DrawTriangleAngles(int centerX, int centerY,
                                        int radius1, int radius2, int radius3,
                                        int angle1, int angle2, int angle3,
                                        GraphicsColor color);

#ifdef __cplusplus
}
#endif

#endif
'''


def write_windows_graphics_runtime_header(path: Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(WINDOWS_GRAPHICS_RUNTIME_HEADER, encoding="utf-8", newline="\n")
    return target

WINDOWS_GRAPHICS_RUNTIME_CPP = r'''#define WIN32_LEAN_AND_MEAN
#define D64_GRAPHICS_RUNTIME_EXPORTS 1
#include <windows.h>
#include <stdint.h>
#include <string.h>
#include "graphics_windows.h"

#if defined(__D64_GRAPHICS_DIRECT3D__)
# include <d3d9.h>
#else
# include <d2d1.h>
# include <dxgiformat.h>
#endif

static HWND g_hwnd = 0;
static uint32_t g_pixels[320 * 200];
static uint32_t g_logical_pixels[320 * 200];
static unsigned int g_present_divider = 0;
static unsigned int g_text_foreground = 1;
static unsigned int g_text_background = 0;

static const uint32_t g_c64_palette[16] = {
    0x000000,0xFFFFFF,0x883932,0x67B6BD,
    0x8B3F96,0x55A049,0x40318D,0xBFCE72,
    0x8B5429,0x574200,0xB86962,0x505050,
    0x787878,0x94E089,0x7869C4,0x9F9F9F
};

static uint32_t d64_color(unsigned int value)
{
    if (value < 16) value = g_c64_palette[value];
    return 0xFF000000u | (value & 0x00FFFFFFu);
}

static LRESULT CALLBACK d64_wndproc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (msg == WM_CLOSE) { DestroyWindow(hwnd); return 0; }
    if (msg == WM_DESTROY) { g_hwnd = 0; return 0; }
    return DefWindowProcA(hwnd, msg, wp, lp);
}

static void d64_pump_messages(void)
{
    MSG msg;
    while (PeekMessageA(&msg, 0, 0, 0, PM_REMOVE)) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
}

#if defined(__D64_GRAPHICS_DIRECT3D__)
static IDirect3D9 *g_d3d = 0;
static IDirect3DDevice9 *g_device = 0;

static int d64_create_renderer(void)
{
    D3DPRESENT_PARAMETERS pp;
    ZeroMemory(&pp, sizeof(pp));
    pp.Windowed = TRUE;
    pp.SwapEffect = D3DSWAPEFFECT_DISCARD;
    pp.hDeviceWindow = g_hwnd;
    pp.BackBufferWidth = 640;
    pp.BackBufferHeight = 400;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    pp.PresentationInterval = D3DPRESENT_INTERVAL_ONE;
    pp.Flags = D3DPRESENTFLAG_LOCKABLE_BACKBUFFER;

    g_d3d = Direct3DCreate9(D3D_SDK_VERSION);
    if (!g_d3d) return 0;
    if (FAILED(g_d3d->CreateDevice(
        D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, g_hwnd,
        D3DCREATE_SOFTWARE_VERTEXPROCESSING, &pp, &g_device))) {
        return 0;
    }
    return 1;
}

static void d64_present(void)
{
    if (!g_device || !g_hwnd) return;
    IDirect3DSurface9 *back = 0;
    if (FAILED(g_device->GetBackBuffer(0, 0, D3DBACKBUFFER_TYPE_MONO, &back))) return;
    D3DLOCKED_RECT lock;
    if (SUCCEEDED(back->LockRect(&lock, 0, 0))) {
        for (int y = 0; y < 400; ++y) {
            uint32_t *dst = (uint32_t *)((unsigned char *)lock.pBits + y * lock.Pitch);
            const uint32_t *src = &g_pixels[(y >> 1) * 320];
            for (int x = 0; x < 640; ++x) dst[x] = src[x >> 1];
        }
        back->UnlockRect();
    }
    back->Release();
    g_device->Present(0, 0, 0, 0);
    d64_pump_messages();
}

static void d64_destroy_renderer(void)
{
    if (g_device) { g_device->Release(); g_device = 0; }
    if (g_d3d) { g_d3d->Release(); g_d3d = 0; }
}
#else
static ID2D1Factory *g_factory = 0;
static ID2D1HwndRenderTarget *g_target = 0;
static ID2D1Bitmap *g_bitmap = 0;

static int d64_create_renderer(void)
{
    HRESULT hr = D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, &g_factory);
    if (FAILED(hr)) return 0;
    D2D1_RENDER_TARGET_PROPERTIES props = D2D1::RenderTargetProperties();
    D2D1_HWND_RENDER_TARGET_PROPERTIES hwndProps =
        D2D1::HwndRenderTargetProperties(g_hwnd, D2D1::SizeU(640, 400));
    hr = g_factory->CreateHwndRenderTarget(props, hwndProps, &g_target);
    if (FAILED(hr)) return 0;
    D2D1_BITMAP_PROPERTIES bp = D2D1::BitmapProperties(
        D2D1::PixelFormat(DXGI_FORMAT_B8G8R8A8_UNORM, D2D1_ALPHA_MODE_IGNORE));
    hr = g_target->CreateBitmap(D2D1::SizeU(320, 200), 0, 0, &bp, &g_bitmap);
    return SUCCEEDED(hr);
}

static void d64_present(void)
{
    if (!g_target || !g_bitmap || !g_hwnd) return;
    g_bitmap->CopyFromMemory(0, g_pixels, 320 * 4);
    g_target->BeginDraw();
    g_target->Clear(D2D1::ColorF(D2D1::ColorF::Black));
    g_target->DrawBitmap(
        g_bitmap,
        D2D1::RectF(0.0f, 0.0f, 640.0f, 400.0f),
        1.0f,
        D2D1_BITMAP_INTERPOLATION_MODE_NEAREST_NEIGHBOR);
    g_target->EndDraw();
    d64_pump_messages();
}

static void d64_destroy_renderer(void)
{
    if (g_bitmap) { g_bitmap->Release(); g_bitmap = 0; }
    if (g_target) { g_target->Release(); g_target = 0; }
    if (g_factory) { g_factory->Release(); g_factory = 0; }
}
#endif

D64_GRAPHICS_API void SetTextColor(unsigned int foreground, unsigned int background)
{
    g_text_foreground = foreground;
    g_text_background = background;
}

D64_GRAPHICS_API void InitGraphics(void)
{
    WNDCLASSEXA wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = d64_wndproc;
    wc.hInstance = GetModuleHandleA(0);
    wc.hCursor = LoadCursorA(0, IDC_ARROW);
    wc.lpszClassName = "dBase2ManyGraphicsWindow";
    RegisterClassExA(&wc);
    g_hwnd = CreateWindowExA(
        0, wc.lpszClassName, "dBase2Many - 320x200 Graphics",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT, 656, 439,
        0, 0, wc.hInstance, 0);
    memset(g_pixels, 0, sizeof(g_pixels));
    memset(g_logical_pixels, 0, sizeof(g_logical_pixels));
    d64_create_renderer();
    d64_present();
}

D64_GRAPHICS_API void DoneGraphics(TextMode mode)
{
    (void)mode;
    d64_present();
    d64_destroy_renderer();
    if (g_hwnd) { DestroyWindow(g_hwnd); g_hwnd = 0; }
}

D64_GRAPHICS_API void ClearScreen(void)
{
    const unsigned int color = 0;
    uint32_t value = d64_color(color);
    for (int i = 0; i < 320 * 200; ++i) {
        g_pixels[i] = value;
        g_logical_pixels[i] = color;
    }
    d64_present();
}

D64_GRAPHICS_API void SetPixel(int x, int y, GraphicsColor color)
{
    if ((unsigned)x >= 320u || (unsigned)y >= 200u) return;
    g_pixels[y * 320 + x] = d64_color(color);
    g_logical_pixels[y * 320 + x] = color;
    if ((++g_present_divider & 255u) == 0u) d64_present();
}

D64_GRAPHICS_API GraphicsColor GetPixel(int x, int y)
{
    if ((unsigned)x >= 320u || (unsigned)y >= 200u) return 0;
    return (GraphicsColor)(g_logical_pixels[y * 320 + x] & 0xFFu);
}

D64_GRAPHICS_API void DrawLine(int x1,int y1,int x2,int y2,GraphicsColor c)
{
    int dx = x2 > x1 ? x2-x1 : x1-x2;
    int sx = x1 < x2 ? 1 : -1;
    int dy = -(y2 > y1 ? y2-y1 : y1-y2);
    int sy = y1 < y2 ? 1 : -1;
    int err = dx + dy;
    for (;;) {
        SetPixel(x1,y1,c);
        if (x1 == x2 && y1 == y2) break;
        int e2 = err << 1;
        if (e2 >= dy) { err += dy; x1 += sx; }
        if (e2 <= dx) { err += dx; y1 += sy; }
    }
    d64_present();
}

D64_GRAPHICS_API void DrawRect(int x1,int y1,int x2,int y2,GraphicsColor c)
{
    DrawLine(x1,y1,x2,y1,c); DrawLine(x2,y1,x2,y2,c);
    DrawLine(x2,y2,x1,y2,c); DrawLine(x1,y2,x1,y1,c);
}

D64_GRAPHICS_API void FillRect(int x1,int y1,int x2,int y2,GraphicsColor fill,
              GraphicsColor border,unsigned int bw)
{
    if (x1 > x2) { int t=x1; x1=x2; x2=t; }
    if (y1 > y2) { int t=y1; y1=y2; y2=t; }
    for (int y=y1;y<=y2;++y) for (int x=x1;x<=x2;++x) SetPixel(x,y,fill);
    for (int i=0;i<bw;++i) DrawRect(x1+i,y1+i,x2-i,y2-i,border);
    d64_present();
}

D64_GRAPHICS_API void DrawCircle(int cx,int cy,int r,GraphicsColor c)
{
    int x=r,y=0,d=1-r;
    while (x>=y) {
        SetPixel(cx+x,cy+y,c);SetPixel(cx-x,cy+y,c);
        SetPixel(cx+x,cy-y,c);SetPixel(cx-x,cy-y,c);
        SetPixel(cx+y,cy+x,c);SetPixel(cx-y,cy+x,c);
        SetPixel(cx+y,cy-x,c);SetPixel(cx-y,cy-x,c);
        ++y; if (d<0) d+=2*y+1; else { --x; d+=2*(y-x)+1; }
    }
    d64_present();
}

D64_GRAPHICS_API void FillCircle(int cx,int cy,int r,GraphicsColor fill,
                GraphicsColor border,unsigned int bw)
{
    for (int y=-r;y<=r;++y) {
        int xx=0; while ((xx+1)*(xx+1)+y*y<=r*r) ++xx;
        DrawLine(cx-xx,cy+y,cx+xx,cy+y,fill);
    }
    for (int i=0;i<bw;++i) DrawCircle(cx,cy,r-i,border);
    d64_present();
}

static void d64_hline(int x1, int y, int x2, GraphicsColor color)
{
    if (y < 0 || y >= GRAPHICS_HEIGHT) return;
    if (x1 > x2) { int t=x1; x1=x2; x2=t; }
    if (x1 < 0) x1 = 0;
    if (x2 >= GRAPHICS_WIDTH) x2 = GRAPHICS_WIDTH - 1;
    for (int x=x1; x<=x2; ++x) SetPixel(x,y,color);
}

D64_GRAPHICS_API void FloodFill(int x, int y, GraphicsColor fillColor)
{
    if ((unsigned)x >= GRAPHICS_WIDTH || (unsigned)y >= GRAPHICS_HEIGHT) return;
    GraphicsColor source = GetPixel(x,y);
    if (source == fillColor) return;

    enum { STACK_SIZE = GRAPHICS_WIDTH * GRAPHICS_HEIGHT };
    static int xs[STACK_SIZE];
    static int ys[STACK_SIZE];
    int top = 0;
    xs[top] = x; ys[top] = y; ++top;
    while (top > 0) {
        --top;
        int cx = xs[top], cy = ys[top];
        if ((unsigned)cx >= GRAPHICS_WIDTH || (unsigned)cy >= GRAPHICS_HEIGHT) continue;
        if (GetPixel(cx,cy) != source) continue;
        SetPixel(cx,cy,fillColor);
        if (top + 4 < STACK_SIZE) {
            xs[top]=cx-1; ys[top]=cy; ++top;
            xs[top]=cx+1; ys[top]=cy; ++top;
            xs[top]=cx; ys[top]=cy-1; ++top;
            xs[top]=cx; ys[top]=cy+1; ++top;
        }
    }
    d64_present();
}

D64_GRAPHICS_API void DrawTriangle(int x1,int y1,int x2,int y2,int x3,int y3,GraphicsColor color)
{
    DrawLine(x1,y1,x2,y2,color);
    DrawLine(x2,y2,x3,y3,color);
    DrawLine(x3,y3,x1,y1,color);
    d64_present();
}

static void d64_thick_line(int x1,int y1,int x2,int y2,GraphicsColor color,unsigned int width)
{
    if (width <= 1u) { DrawLine(x1,y1,x2,y2,color); return; }
    int dx = x2>x1 ? x2-x1 : x1-x2;
    int dy = y2>y1 ? y2-y1 : y1-y2;
    int half = (int)(width/2u);
    if (dx >= dy) {
        for (int o=-half;o<=half;++o) DrawLine(x1,y1+o,x2,y2+o,color);
    } else {
        for (int o=-half;o<=half;++o) DrawLine(x1+o,y1,x2+o,y2,color);
    }
}

D64_GRAPHICS_API void FillTriangle(int x1,int y1,int x2,int y2,int x3,int y3,
                                   GraphicsColor fillColor,GraphicsColor borderColor,
                                   unsigned int borderWidth)
{
    int t;
    if (y1>y2) { t=y1;y1=y2;y2=t; t=x1;x1=x2;x2=t; }
    if (y2>y3) { t=y2;y2=y3;y3=t; t=x2;x2=x3;x3=t; }
    if (y1>y2) { t=y1;y1=y2;y2=t; t=x1;x1=x2;x2=t; }
    if (y1==y3) {
        int lo=x1, hi=x1;
        if (x2<lo) lo=x2; if (x3<lo) lo=x3;
        if (x2>hi) hi=x2; if (x3>hi) hi=x3;
        d64_hline(lo,y1,hi,fillColor);
    } else {
        for (int y=y1;y<=y3;++y) {
            int a, b;
            if (y<y2 && y2!=y1) a=x1+((x2-x1)*(y-y1))/(y2-y1);
            else if (y3!=y2) a=x2+((x3-x2)*(y-y2))/(y3-y2);
            else a=x2;
            b=x1+((x3-x1)*(y-y1))/(y3-y1);
            /* Draw span regardless of edge ordering. */
            if (a<=b) d64_hline(a,y,b,fillColor); else d64_hline(b,y,a,fillColor);
        }
    }
    if (borderWidth) {
        d64_thick_line(x1,y1,x2,y2,borderColor,borderWidth);
        d64_thick_line(x2,y2,x3,y3,borderColor,borderWidth);
        d64_thick_line(x3,y3,x1,y1,borderColor,borderWidth);
    }
    d64_present();
}

static int d64_sine_quarter(unsigned int index)
{
    static const int table[19] = {0,22,44,66,88,108,128,147,165,181,196,210,222,232,241,247,252,255,256};
    return table[index <= 18u ? index : 18u];
}

static int d64_sin_deg(int angle)
{
    while (angle < 0) angle += 360;
    while (angle >= 360) angle -= 360;
    unsigned int quadrant=(unsigned int)angle/90u;
    unsigned int remainder=(unsigned int)angle%90u;
    if (quadrant==1u || quadrant==3u) remainder=90u-remainder;
    unsigned int index=(remainder+2u)/5u;
    int value=d64_sine_quarter(index);
    if (quadrant>=2u) value=-value;
    return value;
}
static int d64_cos_deg(int angle) { return d64_sin_deg(angle+90); }

D64_GRAPHICS_API void DrawTriangleAngles(int centerX,int centerY,
                                         int radius1,int radius2,int radius3,
                                         int angle1,int angle2,int angle3,
                                         GraphicsColor color)
{
    int x1=centerX+(d64_cos_deg(angle1)*radius1)/256;
    int y1=centerY+(d64_sin_deg(angle1)*radius1)/256;
    int x2=centerX+(d64_cos_deg(angle2)*radius2)/256;
    int y2=centerY+(d64_sin_deg(angle2)*radius2)/256;
    int x3=centerX+(d64_cos_deg(angle3)*radius3)/256;
    int y3=centerY+(d64_sin_deg(angle3)*radius3)/256;
    DrawTriangle(x1,y1,x2,y2,x3,y3,color);
}
'''


def write_windows_graphics_runtime_source(path: Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(WINDOWS_GRAPHICS_RUNTIME_CPP, encoding="utf-8", newline="\n")
    return target



def build_windows_graphics_runtime_dll(
    output_path: Path,
    backend: str = "Direct2D",
) -> Path:
    """Baut die 32-Bit-Windows-Grafik-Runtime als ``d64graphics.dll``.

    Der Build benutzt bewusst einen vorhandenen MinGW-g++-Compiler, während
    der eigentliche PE32-Programm-Linker weiterhin vollständig in d64_dism
    bleibt. Das Runtime-DLL kapselt die C++-/COM-Anteile von Direct2D/Direct3D,
    die nicht in den einfachen internen COFF32-Objektleser gehören.
    """
    if os.name != "nt":
        raise PE32AssemblerError(
            "Die Direct2D/Direct3D-Runtime kann nur unter Windows gebaut werden."
        )

    selected = normalize_windows_graphics_backend(backend)
    compiler = (
        shutil.which("i686-w64-mingw32-g++")
        or shutil.which("g++")
        or shutil.which("c++")
    )
    if not compiler:
        raise PE32AssemblerError(
            "Kein MinGW-C++-Compiler gefunden. Erwartet wird "
            "i686-w64-mingw32-g++ oder g++ im PATH."
        )

    target = Path(output_path).expanduser().resolve()
    if target.suffix.casefold() != ".dll":
        target = target.with_suffix(".dll")
    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="d64graphics_") as temp_name:
        temp_dir = Path(temp_name)
        header = write_windows_graphics_runtime_header(
            temp_dir / "graphics_windows.h"
        )
        source = write_windows_graphics_runtime_source(
            temp_dir / "graphics_windows_runtime.cpp"
        )
        del header

        command = [
            compiler,
            "-m32",
            "-shared",
            "-O2",
            "-std=gnu++17",
            "-Wl,--enable-auto-import",
            "-D__D64_GRAPHICS_DIRECT3D__"
            if selected == "Direct3D"
            else "-D__D64_GRAPHICS_DIRECT2D__",
            str(source),
            "-o",
            str(target),
            "-luser32",
            "-lkernel32",
        ]
        if selected == "Direct3D":
            command.append("-ld3d9")
        else:
            command.extend(("-ld2d1", "-ldxgi", "-lole32"))

        result = subprocess.run(
            command,
            cwd=str(temp_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()
            raise PE32AssemblerError(
                "Windows-Grafik-Runtime konnte nicht gebaut werden"
                + (f": {details}" if details else ".")
            )

    try:
        data = target.read_bytes()
        if len(data) < 0x40 or data[:2] != b"MZ":
            raise ValueError("kein MZ-Header")
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe_offset:pe_offset + 4] != b"PE\x00\x00":
            raise ValueError("keine PE-Signatur")
        machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
        if machine != 0x014C:
            raise ValueError(
                f"falsche PE-Machine 0x{machine:04X}; IA-32/0x014C erwartet"
            )

        # Sicherstellen, dass MinGW die erwarteten undecorated C-Namen in die
        # Exporttabelle geschrieben hat. Damit stimmt die DLL exakt mit den
        # vom internen PE32-Linker erzeugten Imports ueberein.
        section_count = struct.unpack_from("<H", data, pe_offset + 6)[0]
        optional_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
        optional_offset = pe_offset + 24
        if struct.unpack_from("<H", data, optional_offset)[0] != 0x010B:
            raise ValueError("kein PE32-Optional-Header")
        export_rva = struct.unpack_from("<I", data, optional_offset + 96)[0]
        if not export_rva:
            raise ValueError("Runtime-DLL besitzt keine Exporttabelle")
        section_offset = optional_offset + optional_size

        def rva_to_offset(rva: int) -> int:
            for index in range(section_count):
                base = section_offset + index * 40
                virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
                    "<IIII", data, base + 8
                )
                span = max(virtual_size, raw_size)
                if virtual_address <= rva < virtual_address + span:
                    return raw_pointer + (rva - virtual_address)
            raise ValueError(f"RVA 0x{rva:08X} liegt in keiner Sektion")

        export_offset = rva_to_offset(export_rva)
        name_count = struct.unpack_from("<I", data, export_offset + 24)[0]
        names_rva = struct.unpack_from("<I", data, export_offset + 32)[0]
        names_offset = rva_to_offset(names_rva)
        exports = set()
        for index in range(name_count):
            name_rva = struct.unpack_from("<I", data, names_offset + index * 4)[0]
            name_offset = rva_to_offset(name_rva)
            end = data.find(b"\0", name_offset)
            if end < 0:
                raise ValueError("ungueltiger Name in der Exporttabelle")
            exports.add(data[name_offset:end].decode("ascii", errors="replace"))
        required_exports = {
            "SetTextColor", "ClearScreen", "InitGraphics", "DoneGraphics",
            "SetPixel", "GetPixel", "DrawLine", "DrawRect", "FillRect",
            "DrawCircle", "FillCircle", "FloodFill", "DrawTriangle",
            "FillTriangle", "DrawTriangleAngles",
        }
        missing_exports = sorted(required_exports - exports)
        if missing_exports:
            raise ValueError(
                "fehlende DLL-Exports: " + ", ".join(missing_exports)
            )
    except (OSError, struct.error, ValueError) as exc:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise PE32AssemblerError(
            f"Das erzeugte Runtime-DLL ist kein gültiges PE32-i386-DLL: {exc}"
        ) from exc

    return target



class AmigaAssemblerError(Exception):
    """Assemblerfehler mit optionaler Quellzeile."""

    def __init__(self, message: str, line: int = 0) -> None:
        self.message = str(message)
        self.line = int(line or 0)
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.line:
            return f"Zeile {self.line}: {self.message}"
        return self.message


@dataclass(frozen=True)
class AmigaProgram:
    executable: bytes
    code: bytes
    entry_offset: int
    end_offset: int
    instruction_count: int
    hunk_count: int = 1


@dataclass(frozen=True)
class AmigaBootProgram:
    """Bootfähiges ADF mit Trackloader und direkt ausführbarem 68000-Code."""

    adf: bytes
    boot_block: bytes
    code: bytes
    entry_offset: int
    end_offset: int
    instruction_count: int
    hunk_count: int = 0
    load_address: int = BOOT_PAYLOAD_ADDRESS
    payload_offset: int = BOOT_PAYLOAD_OFFSET


@dataclass(frozen=True)
class _SourceItem:
    line: int
    offset: int
    text: str


@dataclass(frozen=True)
class _EffectiveAddress:
    mode: int
    register: int
    extension_kind: str = ""
    expression: str = ""

    @property
    def bits(self) -> int:
        return (self.mode << 3) | self.register

    def extension_words(
        self,
        labels: Dict[str, int],
        extension_offset: int,
        size: str,
        line: int,
        resolve: bool,
    ) -> List[int]:
        kind = self.extension_kind
        if not kind:
            return []
        if kind == "immediate":
            value = _parse_expression(self.expression, labels, line, resolve)
            if size == "l":
                value &= 0xFFFFFFFF
                return [(value >> 16) & 0xFFFF, value & 0xFFFF]
            return [value & 0xFFFF]
        if kind == "pc":
            target = _parse_expression(self.expression, labels, line, resolve)
            displacement = target - extension_offset if resolve else 0
            _require_signed_word(displacement, line, "PC-relativer Abstand")
            return [displacement & 0xFFFF]
        if kind == "displacement":
            value = _parse_expression(self.expression, labels, line, resolve)
            _require_signed_word(value, line, "Adressabstand")
            return [value & 0xFFFF]
        if kind == "absolute_word":
            value = _parse_expression(self.expression, labels, line, resolve)
            if resolve and not -32768 <= value <= 0xFFFF:
                raise AmigaAssemblerError(
                    f"Absolute Word-Adresse außerhalb des Bereichs: {value}.",
                    line,
                )
            return [value & 0xFFFF]
        raise AmigaAssemblerError(f"Interner EA-Fehler: {kind}.", line)

_LABEL_RE       = re.compile(r"^[A-Za-z_.$][A-Za-z0-9_.$]*$")
_REGISTER_RE    = re.compile(r"^(?P<kind>[dDaA])(?P<number>[0-7])$")
_INDIRECT_RE    = re.compile(r"^\((?P<register>a[0-7]|sp)\)$", re.IGNORECASE)
_POSTINC_RE     = re.compile(r"^\((?P<register>a[0-7]|sp)\)\+$", re.IGNORECASE)
_PREDEC_RE      = re.compile(r"^-\((?P<register>a[0-7]|sp)\)$", re.IGNORECASE)
_INDEXED_RE     = re.compile(r"^(?P<expression>.+?)\((?P<register>a[0-7]|sp|pc)\)$", re.IGNORECASE,)


def _register_number(text: str, line: int) -> Tuple[str, int]:
    lowered = text.strip().lower()
    if lowered == "sp":
        return "a", 7
    match = _REGISTER_RE.fullmatch(lowered)
    if match is None:
        raise AmigaAssemblerError(f"Register erwartet: {text}.", line)
    return match.group("kind").lower(), int(match.group("number"))


def _parse_number(text: str) -> Optional[int]:
    value = text.strip()
    sign = 1
    if value.startswith(("+", "-")):
        if value[0] == "-":
            sign = -1
        value = value[1:].strip()
    try:
        if value.startswith("$"):
            return sign * int(value[1:], 16)
        if value.startswith("%"):
            return sign * int(value[1:], 2)
        if value.lower().startswith("0x"):
            return sign * int(value[2:], 16)
        if value.lower().startswith("0b"):
            return sign * int(value[2:], 2)
        if value.isdigit():
            return sign * int(value, 10)
    except ValueError:
        return None
    return None

def _parse_expression(
    text: str,
    labels: Dict[str, int],
    line: int,
    resolve: bool,
) -> int:
    expression = text.strip()
    numeric = _parse_number(expression)
    if numeric is not None:
        return numeric

    match = re.fullmatch(
        r"(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)"
        r"(?:\s*(?P<operator>[+-])\s*(?P<offset>.+))?",
        expression,
    )
    if match is None:
        raise AmigaAssemblerError(f"Ungültiger Ausdruck: {text}.", line)
    label = match.group("label").casefold()
    if label not in labels:
        if not resolve:
            base = 0
        else:
            raise AmigaAssemblerError(
                f"Symbol nicht definiert: {match.group('label')}.",
                line,
            )
    else:
        base = labels[label]
    offset_text = match.group("offset")
    if offset_text:
        offset = _parse_number(offset_text)
        if offset is None:
            raise AmigaAssemblerError(
                f"Numerischer Symbolabstand erwartet: {offset_text}.",
                line,
            )
        base = base + offset if match.group("operator") == "+" else base - offset
    return base

def _require_signed_word(value: int, line: int, description: str) -> None:
    if not -32768 <= int(value) <= 32767:
        raise AmigaAssemblerError(
            f"{description} liegt außerhalb -32768..32767: {value}.",
            line,
        )

def _parse_ea(text: str, line: int) -> _EffectiveAddress:
    operand = text.strip()
    if operand.startswith("#"):
        return _EffectiveAddress(7, 4, "immediate", operand[1:].strip())

    register_match = _REGISTER_RE.fullmatch(operand)
    if register_match is not None:
        kind = register_match.group("kind").lower()
        return _EffectiveAddress(
            0 if kind == "d" else 1,
            int(register_match.group("number")),
        )
    if operand.lower() == "sp":
        return _EffectiveAddress(1, 7)

    match = _INDIRECT_RE.fullmatch(operand)
    if match is not None:
        unused_kind, register = _register_number(match.group("register"), line)
        return _EffectiveAddress(2, register)
    match = _POSTINC_RE.fullmatch(operand)
    if match is not None:
        unused_kind, register = _register_number(match.group("register"), line)
        return _EffectiveAddress(3, register)
    match = _PREDEC_RE.fullmatch(operand)
    if match is not None:
        unused_kind, register = _register_number(match.group("register"), line)
        return _EffectiveAddress(4, register)
    match = _INDEXED_RE.fullmatch(operand)
    if match is not None:
        register_text = match.group("register").lower()
        if register_text == "pc":
            return _EffectiveAddress(7, 2, "pc", match.group("expression"))
        unused_kind, register = _register_number(register_text, line)
        return _EffectiveAddress(
            5,
            register,
            "displacement",
            match.group("expression"),
        )
    if operand.lower().endswith(".w"):
        return _EffectiveAddress(7, 0, "absolute_word", operand[:-2])
    raise AmigaAssemblerError(f"Adressierungsart nicht unterstützt: {text}.", line)

def _split_operands(text: str) -> List[str]:
    result: List[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(text):
        if character == "(":
            depth += 1
        elif character == ")":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            result.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        result.append(tail)
    return result


def _word_bytes(words: Sequence[int]) -> bytes:
    return b"".join(struct.pack(">H", word & 0xFFFF) for word in words)


def _ea_words(
    ea: _EffectiveAddress,
    labels: Dict[str, int],
    extension_offset: int,
    size: str,
    line: int,
    resolve: bool,
) -> List[int]:
    return ea.extension_words(
        labels,
        extension_offset,
        size,
        line,
        resolve,
    )

_SIZE_BITS = {"b": 0x0000, "w": 0x0040, "l": 0x0080}
_MOVE_BASE = {"b": 0x1000, "w": 0x3000, "l": 0x2000}
_AMIGA_MOVEC_REGISTERS: Dict[str, Tuple[int, str, Optional[str]]] = {
    "sfc":   (0x000, "mk68010", None),
    "dfc":   (0x001, "mk68010", None),
    "cacr":  (0x002, "mk68020", None),
    "tc":    (0x003, "mk68040", None),
    "itt0":  (0x004, "mk68040", None),
    "itt1":  (0x005, "mk68040", None),
    "dtt0":  (0x006, "mk68040", None),
    "dtt1":  (0x007, "mk68040", None),
    "usp":   (0x800, "mk68010", None),
    "vbr":   (0x801, "mk68010", None),
    "caar":  (0x802, "mk68020", "mk68030"),
    "msp":   (0x803, "mk68020", None),
    "isp":   (0x804, "mk68020", None),
    "mmusr": (0x805, "mk68040", None),
    "urp":   (0x806, "mk68040", None),
    "srp":   (0x807, "mk68040", None),
    "pcr":   (0x808, "mk68060", None),
}


def _amiga_movec_register_code(name: str, cpu_model: str, line: int) -> int:
    key = str(name).strip().casefold()
    spec = _AMIGA_MOVEC_REGISTERS.get(key)
    if spec is None:
        raise AmigaAssemblerError(f"Unbekanntes MOVEC-Control-Register: {name}.", line)
    code, minimum, maximum = spec
    if not amiga_cpu_at_least(cpu_model, minimum):
        raise AmigaAssemblerError(
            f"MOVEC {name.upper()} benötigt mindestens {minimum}.", line
        )
    if maximum is not None and AMIGA_CPU_LEVEL[normalize_amiga_cpu_model(cpu_model)] > AMIGA_CPU_LEVEL[maximum]:
        raise AmigaAssemblerError(
            f"MOVEC {name.upper()} ist nur bis {maximum} verfügbar.", line
        )
    return code


_BRANCH_CONDITION = {
    "bra": 0x0,
    "bsr": 0x1,
    "bhi": 0x2,
    "bls": 0x3,
    "bcc": 0x4,
    "bhs": 0x4,
    "bcs": 0x5,
    "blo": 0x5,
    "bne": 0x6,
    "beq": 0x7,
    "bvc": 0x8,
    "bvs": 0x9,
    "bpl": 0xA,
    "bmi": 0xB,
    "bge": 0xC,
    "blt": 0xD,
    "bgt": 0xE,
    "ble": 0xF,
}


def _encode_instruction(
    text: str,
    offset: int,
    labels: Dict[str, int],
    line: int,
    resolve: bool,
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
) -> bytes:
    cpu_model = normalize_amiga_cpu_model(cpu_model)
    fpu_model = normalize_amiga_fpu_model(fpu_model)
    parts = text.strip().split(None, 1)
    mnemonic_text = parts[0].lower()
    operands = _split_operands(parts[1] if len(parts) > 1 else "")
    if "." in mnemonic_text:
        mnemonic, size = mnemonic_text.split(".", 1)
    else:
        mnemonic, size = mnemonic_text, ""

    if mnemonic == "nop" and not operands:
        return _word_bytes([0x4E71])
    if mnemonic == "rts" and not operands:
        return _word_bytes([0x4E75])

    if mnemonic == "reset" and not operands:
        return _word_bytes([0x4E70])
    if mnemonic == "rte" and not operands:
        return _word_bytes([0x4E73])
    if mnemonic == "rtr" and not operands:
        return _word_bytes([0x4E77])
    if mnemonic == "trapv" and not operands:
        return _word_bytes([0x4E76])
    if mnemonic == "stop":
        if len(operands) != 1 or not operands[0].startswith("#"):
            raise AmigaAssemblerError("STOP erwartet #Statuswort.", line)
        value = _parse_expression(operands[0][1:], labels, line, resolve)
        return _word_bytes([0x4E72, value])
    if mnemonic == "trap":
        if len(operands) != 1 or not operands[0].startswith("#"):
            raise AmigaAssemblerError("TRAP erwartet #0..15.", line)
        vector = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not 0 <= vector <= 15:
            raise AmigaAssemblerError("TRAP-Vektor muss 0..15 sein.", line)
        return _word_bytes([0x4E40 | (vector & 15)])
    if mnemonic == "unlk":
        if len(operands) != 1:
            raise AmigaAssemblerError("UNLK erwartet An.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "a":
            raise AmigaAssemblerError("UNLK erwartet ein Adressregister.", line)
        return _word_bytes([0x4E58 | register])
    if mnemonic == "link":
        if len(operands) != 2 or not operands[1].startswith("#"):
            raise AmigaAssemblerError("LINK erwartet An,#Abstand.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "a":
            raise AmigaAssemblerError("LINK erwartet ein Adressregister.", line)
        displacement = _parse_expression(operands[1][1:], labels, line, resolve)
        if size in {"", "w"}:
            _require_signed_word(displacement, line, "LINK.W-Abstand")
            return _word_bytes([0x4E50 | register, displacement])
        if size == "l":
            if not amiga_cpu_at_least(cpu_model, "mk68020"):
                raise AmigaAssemblerError("LINK.L benötigt mindestens mk68020.", line)
            value = displacement & 0xFFFFFFFF
            return _word_bytes([0x4808 | register, (value >> 16) & 0xFFFF, value & 0xFFFF])
        raise AmigaAssemblerError("LINK unterstützt .W oder ab mk68020 .L.", line)
    if mnemonic == "movec":
        if not amiga_cpu_at_least(cpu_model, "mk68010"):
            raise AmigaAssemblerError("MOVEC benötigt mindestens mk68010.", line)
        if len(operands) != 2:
            raise AmigaAssemblerError("MOVEC erwartet Rc,Rn oder Rn,Rc.", line)
        left = operands[0].strip()
        right = operands[1].strip()
        left_control = left.casefold() in _AMIGA_MOVEC_REGISTERS
        right_control = right.casefold() in _AMIGA_MOVEC_REGISTERS
        if left_control == right_control:
            raise AmigaAssemblerError("MOVEC benötigt genau ein Control-Register.", line)
        if left_control:
            control = _amiga_movec_register_code(left, cpu_model, line)
            kind, register = _register_number(right, line)
            first_word = 0x4E7A
        else:
            kind, register = _register_number(left, line)
            control = _amiga_movec_register_code(right, cpu_model, line)
            first_word = 0x4E7B
        extension = ((1 if kind == "a" else 0) << 15) | ((register & 7) << 12) | control
        return _word_bytes([first_word, extension])

    if mnemonic in _BRANCH_CONDITION:
        if len(operands) != 1:
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet ein Ziel.", line)
        target = _parse_expression(operands[0], labels, line, resolve)
        opcode = 0x6000 | (_BRANCH_CONDITION[mnemonic] << 8)
        if size == "l":
            if not amiga_cpu_at_least(cpu_model, "mk68020"):
                raise AmigaAssemblerError(
                    f"{mnemonic.upper()}.L benötigt mindestens mk68020.", line
                )
            displacement = target - (offset + 2) if resolve else 0
            value = displacement & 0xFFFFFFFF
            return _word_bytes([
                opcode | 0x00FF,
                (value >> 16) & 0xFFFF,
                value & 0xFFFF,
            ])
        if size not in {"", "w"}:
            raise AmigaAssemblerError(
                f"{mnemonic.upper()} unterstützt hier nur .W oder ab mk68020 .L.", line
            )
        displacement = target - (offset + 2) if resolve else 0
        _require_signed_word(displacement, line, "Sprungabstand")
        return _word_bytes([opcode, displacement])

    if mnemonic in {"jmp", "jsr"} and len(operands) == 1:
        if _LABEL_RE.fullmatch(operands[0]):
            pseudo = "bra" if mnemonic == "jmp" else "bsr"
            return _encode_instruction(
                f"{pseudo} {operands[0]}",
                offset,
                labels,
                line,
                resolve,
                cpu_model,
                fpu_model,
            )
        ea = _parse_ea(operands[0], line)
        extension = _ea_words(ea, labels, offset + 2, "l", line, resolve)
        return _word_bytes([(0x4EC0 if mnemonic == "jmp" else 0x4E80) | ea.bits] + extension)

    if mnemonic == "moveq":
        if len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError("MOVEQ erwartet #Wert,Dn.", line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError("MOVEQ benötigt ein Datenregister.", line)
        value = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not -128 <= value <= 255:
            raise AmigaAssemblerError("MOVEQ-Wert liegt außerhalb -128..255.", line)
        return _word_bytes([0x7000 | (register << 9) | (value & 0xFF)])

    if mnemonic == "move":
        if size not in _MOVE_BASE or len(operands) != 2:
            raise AmigaAssemblerError("MOVE benötigt .B, .W oder .L und zwei Operanden.", line)
        source = _parse_ea(operands[0], line)
        destination = _parse_ea(operands[1], line)
        if destination.mode == 7:
            raise AmigaAssemblerError("MOVE-Zieladressierung wird nicht unterstützt.", line)
        source_extension = _ea_words(source, labels, offset + 2, size, line, resolve)
        destination_extension_offset = offset + 2 + 2 * len(source_extension)
        destination_extension = _ea_words(
            destination,
            labels,
            destination_extension_offset,
            size,
            line,
            resolve,
        )
        opcode = (
            _MOVE_BASE[size]
            | (destination.register << 9)
            | (destination.mode << 6)
            | source.bits
        )
        return _word_bytes([opcode] + source_extension + destination_extension)

    if mnemonic == "lea":
        if len(operands) != 2:
            raise AmigaAssemblerError("LEA erwartet Quelle,An.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "a":
            raise AmigaAssemblerError("LEA benötigt ein Adressregister als Ziel.", line)
        extension = _ea_words(source, labels, offset + 2, "l", line, resolve)
        return _word_bytes([0x41C0 | (register << 9) | source.bits] + extension)

    if mnemonic in {"tst", "clr", "neg"}:
        if size not in _SIZE_BITS or len(operands) != 1:
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt eine Größe und einen Operanden.", line)
        ea = _parse_ea(operands[0], line)
        base = {"tst": 0x4A00, "clr": 0x4200, "neg": 0x4400}[mnemonic]
        extension = _ea_words(ea, labels, offset + 2, size, line, resolve)
        return _word_bytes([base | _SIZE_BITS[size] | ea.bits] + extension)

    if mnemonic == "swap":
        if len(operands) != 1:
            raise AmigaAssemblerError("SWAP erwartet Dn.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("SWAP erwartet ein Datenregister.", line)
        return _word_bytes([0x4840 | register])

    if mnemonic == "ext":
        if size not in {"w", "l"} or len(operands) != 1:
            raise AmigaAssemblerError("EXT erwartet .W oder .L und Dn.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("EXT erwartet ein Datenregister.", line)
        return _word_bytes([(0x4880 if size == "w" else 0x48C0) | register])

    if mnemonic in {"add", "sub", "and", "or", "cmp"}:
        if size not in _SIZE_BITS or len(operands) != 2:
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt Größe und zwei Operanden.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt Dn als Ziel.", line)
        base = {"add": 0xD000, "sub": 0x9000, "and": 0xC000, "or": 0x8000, "cmp": 0xB000}[mnemonic]
        extension = _ea_words(source, labels, offset + 2, size, line, resolve)
        return _word_bytes([base | (register << 9) | _SIZE_BITS[size] | source.bits] + extension)

    if mnemonic == "eor":
        if size not in _SIZE_BITS or len(operands) != 2:
            raise AmigaAssemblerError("EOR benötigt Größe und zwei Operanden.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("EOR benötigt Dn als Quelle.", line)
        destination = _parse_ea(operands[1], line)
        extension = _ea_words(destination, labels, offset + 2, size, line, resolve)
        return _word_bytes([0xB100 | (register << 9) | _SIZE_BITS[size] | destination.bits] + extension)

    immediate_bases = {
        "addi": 0x0600,
        "subi": 0x0400,
        "andi": 0x0200,
        "ori": 0x0000,
        "eori": 0x0A00,
        "cmpi": 0x0C00,
    }
    if mnemonic in immediate_bases:
        if size not in _SIZE_BITS or len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet #Wert,Ziel.", line)
        destination = _parse_ea(operands[1], line)
        immediate = _EffectiveAddress(7, 4, "immediate", operands[0][1:])
        immediate_words = _ea_words(immediate, labels, offset + 2, size, line, resolve)
        destination_offset = offset + 2 + 2 * len(immediate_words)
        extension = _ea_words(destination, labels, destination_offset, size, line, resolve)
        opcode = immediate_bases[mnemonic] | _SIZE_BITS[size] | destination.bits
        return _word_bytes([opcode] + immediate_words + extension)

    if mnemonic in {"addq", "subq"}:
        if size not in _SIZE_BITS or len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet #1..8,Ziel.", line)
        count = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not 1 <= count <= 8:
            raise AmigaAssemblerError("Quick-Konstante muss 1..8 betragen.", line)
        destination = _parse_ea(operands[1], line)
        extension = _ea_words(destination, labels, offset + 2, size, line, resolve)
        encoded_count = 0 if count == 8 else count
        opcode = (0x5100 if mnemonic == "subq" else 0x5000)
        opcode |= (encoded_count << 9) | _SIZE_BITS[size] | destination.bits
        return _word_bytes([opcode] + extension)

    if mnemonic in {"adda", "suba"}:
        if size not in {"w", "l"} or len(operands) != 2:
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet .W/.L Quelle,An.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "a":
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt An als Ziel.", line)
        base = 0xD0C0 if mnemonic == "adda" else 0x90C0
        if size == "l":
            base |= 0x0100
        extension = _ea_words(source, labels, offset + 2, size, line, resolve)
        return _word_bytes([base | (register << 9) | source.bits] + extension)

    if mnemonic in {"mulu", "muls", "divu", "divs"}:
        if size not in {"", "w"} or len(operands) != 2:
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet Quelle,Dn.", line)
        source = _parse_ea(operands[0], line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError(f"{mnemonic.upper()} benötigt Dn als Ziel.", line)
        base = {"mulu": 0xC0C0, "muls": 0xC1C0, "divu": 0x80C0, "divs": 0x81C0}[mnemonic]
        extension = _ea_words(source, labels, offset + 2, "w", line, resolve)
        return _word_bytes([base | (register << 9) | source.bits] + extension)

    if mnemonic == "rtd":
        if not amiga_cpu_at_least(cpu_model, "mk68010"):
            raise AmigaAssemblerError("RTD benötigt mindestens mk68010.", line)
        if len(operands) != 1 or not operands[0].startswith("#"):
            raise AmigaAssemblerError("RTD erwartet #Abstand.", line)
        value = _parse_expression(operands[0][1:], labels, line, resolve)
        _require_signed_word(value, line, "RTD-Stackabstand")
        return _word_bytes([0x4E74, value])

    if mnemonic == "bkpt":
        if not amiga_cpu_at_least(cpu_model, "mk68010"):
            raise AmigaAssemblerError("BKPT benötigt mindestens mk68010.", line)
        if len(operands) != 1 or not operands[0].startswith("#"):
            raise AmigaAssemblerError("BKPT erwartet #0..7.", line)
        value = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not 0 <= value <= 7:
            raise AmigaAssemblerError("BKPT-Vektor muss 0..7 sein.", line)
        return _word_bytes([0x4848 | (value & 7)])

    if mnemonic == "extb":
        if not amiga_cpu_at_least(cpu_model, "mk68020"):
            raise AmigaAssemblerError("EXTB.L benötigt mindestens mk68020.", line)
        if size not in {"", "l"} or len(operands) != 1:
            raise AmigaAssemblerError("EXTB erwartet .L Dn.", line)
        kind, register = _register_number(operands[0], line)
        if kind != "d":
            raise AmigaAssemblerError("EXTB.L erwartet ein Datenregister.", line)
        return _word_bytes([0x49C0 | register])

    fpu_register_opmodes = {
        "fmove": 0x00, "fint": 0x01, "fintrz": 0x03,
        "fsqrt": 0x04, "fabs": 0x18, "fneg": 0x1A,
        "fdiv": 0x20, "fadd": 0x22, "fmul": 0x23,
        "fsub": 0x28, "fcmp": 0x38, "ftst": 0x3A,
    }
    if mnemonic in fpu_register_opmodes:
        if fpu_model == "FPU: None":
            raise AmigaAssemblerError(
                f"{mnemonic.upper()} benötigt FPU: 68881 oder FPU: 68882.", line
            )
        if size not in {"", "x"}:
            raise AmigaAssemblerError(
                f"{mnemonic.upper()} unterstützt im integrierten Assembler derzeit FP-Register/X-Format.", line
            )
        def fp_register(value: str) -> int:
            match = re.fullmatch(r"fp([0-7])", value.strip(), re.IGNORECASE)
            if match is None:
                raise AmigaAssemblerError(
                    f"{mnemonic.upper()} erwartet FP0..FP7.", line
                )
            return int(match.group(1))
        if mnemonic == "ftst":
            if len(operands) != 1:
                raise AmigaAssemblerError("FTST erwartet FPn.", line)
            source_register = fp_register(operands[0])
            destination_register = source_register
        elif len(operands) == 1 and mnemonic in {"fint", "fintrz", "fsqrt", "fabs", "fneg"}:
            source_register = fp_register(operands[0])
            destination_register = source_register
        elif len(operands) == 2:
            source_register = fp_register(operands[0])
            destination_register = fp_register(operands[1])
        else:
            raise AmigaAssemblerError(
                f"{mnemonic.upper()} erwartet FPm,FPn.", line
            )
        extension = (source_register << 10) | (destination_register << 7) | fpu_register_opmodes[mnemonic]
        return _word_bytes([0xF200, extension])

    if mnemonic == "fnop":
        if fpu_model == "FPU: None":
            raise AmigaAssemblerError(
                "FNOP benötigt FPU: 68881 oder FPU: 68882.", line
            )
        if operands:
            raise AmigaAssemblerError("FNOP besitzt keine Operanden.", line)
        return _word_bytes([0xF280, 0x0000])

    if mnemonic in {"lsl", "lsr"}:
        if size not in {"b", "w", "l"} or len(operands) != 2 or not operands[0].startswith("#"):
            raise AmigaAssemblerError(f"{mnemonic.upper()} erwartet #1..8,Dn.", line)
        count = _parse_expression(operands[0][1:], labels, line, resolve)
        if resolve and not 1 <= count <= 8:
            raise AmigaAssemblerError("Schiebeweite muss 1..8 betragen.", line)
        kind, register = _register_number(operands[1], line)
        if kind != "d":
            raise AmigaAssemblerError("Register-Schiebebefehl benötigt Dn.", line)
        size_bits = {"b": 0x0000, "w": 0x0040, "l": 0x0080}[size]
        encoded_count = 0 if count == 8 else count
        opcode = 0xE008 | (encoded_count << 9) | size_bits | register
        if mnemonic == "lsl":
            opcode |= 0x0100
        return _word_bytes([opcode])

    raise AmigaAssemblerError(f"68000-Befehl nicht unterstützt: {text}.", line)

def _strip_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()

def _split_label(text: str) -> Tuple[Optional[str], str]:
    match = re.match(
        r"^(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*:\s*(?P<tail>.*)$",
        text,
    )
    if match is None:
        return None, text
    return match.group("label"), match.group("tail").strip()

def _directive_parts(text: str) -> Tuple[str, str]:
    parts = text.strip().split(None, 1)
    name = parts[0].lower().lstrip(".") if parts else ""
    arguments = parts[1].strip() if len(parts) > 1 else ""
    return name, arguments

def _data_values(arguments: str) -> List[str]:
    return [item.strip() for item in _split_operands(arguments) if item.strip()]

def _item_size(
    text: str,
    offset: int,
    labels: Dict[str, int],
    line: int,
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
) -> int:
    name, arguments = _directive_parts(text)
    if name in {"section", "xdef", "end", "bootable"}:
        return 0
    if name == "even":
        return offset & 1
    if name in {"dc.b", "dc.w", "dc.l"}:
        unit = {"dc.b": 1, "dc.w": 2, "dc.l": 4}[name]
        return unit * len(_data_values(arguments))
    if name in {"ds.b", "ds.w", "ds.l"}:
        unit = {"ds.b": 1, "ds.w": 2, "ds.l": 4}[name]
        count = _parse_expression(arguments, labels, line, False)
        if count < 0:
            raise AmigaAssemblerError("DS-Anzahl darf nicht negativ sein.", line)
        return unit * count
    return len(_encode_instruction(
        text, offset, labels, line, False, cpu_model, fpu_model
    ))

def _encode_item(
    item: _SourceItem,
    labels: Dict[str, int],
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
) -> Tuple[bytes, int]:
    name, arguments = _directive_parts(item.text)
    if name in {"section", "xdef", "end", "bootable"}:
        return b"", 0
    if name == "even":
        return (b"\x00" if item.offset & 1 else b""), 0
    if name in {"dc.b", "dc.w", "dc.l"}:
        unit = {"dc.b": 1, "dc.w": 2, "dc.l": 4}[name]
        output = bytearray()
        for expression in _data_values(arguments):
            value = _parse_expression(expression, labels, item.line, True)
            if unit == 1:
                output.append(value & 0xFF)
            elif unit == 2:
                output.extend(struct.pack(">H", value & 0xFFFF))
            else:
                output.extend(struct.pack(">I", value & 0xFFFFFFFF))
        return bytes(output), 0
    if name in {"ds.b", "ds.w", "ds.l"}:
        unit = {"ds.b": 1, "ds.w": 2, "ds.l": 4}[name]
        count = _parse_expression(arguments, labels, item.line, True)
        return bytes(unit * count), 0
    return (
        _encode_instruction(
            item.text,
            item.offset,
            labels,
            item.line,
            True,
            cpu_model,
            fpu_model,
        ),
        1,
    )


def _hunk_executable(code: bytes) -> bytes:
    padded_size = (len(code) + 3) & ~3
    padded_code = code + bytes(padded_size - len(code))
    long_count = padded_size // 4
    header = struct.pack(
        ">6I",
        HUNK_HEADER,
        0,
        1,
        0,
        0,
        long_count,
    )
    return (
        header
        + struct.pack(">2I", HUNK_CODE, long_count)
        + padded_code
        + struct.pack(">I", HUNK_END)
    )

def is_amiga_boot_source(source: str) -> bool:
    """Erkennt die explizite ``.bootable``-Direktive."""
    for raw_line in str(source).splitlines():
        text = _strip_comment(raw_line)
        if not text:
            continue
        unused_label, tail = _split_label(text)
        if tail and _directive_parts(tail)[0] == "bootable":
            return True
    return False


def _boot_block_checksum(block: bytes) -> int:
    """Berechnet die Amiga-Bootblock-Prüfsumme mit End-Around-Carry."""
    if len(block) != BOOT_BLOCK_SIZE:
        raise ValueError("Ein Amiga-Bootblock muss genau 1024 Bytes groß sein.")
    total = 0
    for (value,) in struct.iter_unpack(">I", block):
        previous = total
        total = (total + value) & 0xFFFFFFFF
        if total < previous:
            total = (total + 1) & 0xFFFFFFFF
    return (~total) & 0xFFFFFFFF


def _boot_loader_source(payload_size: int) -> str:
    """Erzeugt den kleinen Bootblock-Trackloader für den Nutzcode."""
    return (
        "section code,code\n"
        "xdef _start\n"
        "_start:\n"
        f"    move.l #${BOOT_PAYLOAD_ADDRESS:08X},$28(a1)\n"
        f"    move.l #${payload_size:08X},$24(a1)\n"
        f"    move.l #${BOOT_PAYLOAD_OFFSET:08X},$2C(a1)\n"
        "    move.w #$0002,$1C(a1)\n"
        "    jsr -456(a6)\n"
        "    tst.b $1F(a1)\n"
        "    bne .load_error\n"
        f"    move.l #${BOOT_PAYLOAD_ADDRESS:08X},a0\n"
        "    jmp (a0)\n"
        ".load_error:\n"
        "    moveq #-1,d0\n"
        "    rts\n"
    )

def _bootable_adf(code: bytes) -> Tuple[bytes, bytes]:
    if len(code) > MAX_BOOT_PAYLOAD_SIZE:
        raise AmigaAssemblerError(
            "Der Standalone-Nutzcode ist zu groß: "
            f"{len(code)} Bytes; erlaubt sind höchstens "
            f"{MAX_BOOT_PAYLOAD_SIZE} Bytes."
        )

    padded_size = (len(code) + 511) & ~511
    if BOOT_PAYLOAD_OFFSET + padded_size > ADF_SIZE:
        raise AmigaAssemblerError(
            "Der Standalone-Nutzcode passt nicht auf eine Amiga-DD-Diskette."
        )

    loader = assemble_amiga_source(_boot_loader_source(padded_size))
    maximum_loader_size = BOOT_BLOCK_SIZE - BOOT_CODE_OFFSET
    if len(loader.code) > maximum_loader_size:
        raise AmigaAssemblerError(
            "Interner Fehler: Der Amiga-Trackloader überschreitet den Bootblock."
        )

    boot_block = bytearray(BOOT_BLOCK_SIZE)
    boot_block[0:4] = b"DOS\0"
    struct.pack_into(">I", boot_block, 8, AMIGA_DD_ROOT_BLOCK)
    boot_block[
        BOOT_CODE_OFFSET:BOOT_CODE_OFFSET + len(loader.code)
    ] = loader.code
    struct.pack_into(">I", boot_block, 4, _boot_block_checksum(boot_block))

    adf = bytearray(ADF_SIZE)
    adf[:BOOT_BLOCK_SIZE] = boot_block
    adf[
        BOOT_PAYLOAD_OFFSET:BOOT_PAYLOAD_OFFSET + len(code)
    ] = code
    return bytes(adf), bytes(boot_block)


def assemble_amiga_source(
    source: str,
    *,
    filename: str = "<Amiga-Assembler>",
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
) -> AmigaProgram:
    """Assembliert 68k-Quelltext passend zum gewählten CPU/FPU-Profil."""
    del filename
    cpu_model = normalize_amiga_cpu_model(cpu_model)
    fpu_model = normalize_amiga_fpu_model(fpu_model)
    labels: Dict[str, int] = {}
    items: List[_SourceItem] = []
    offset = 0

    for line_number, raw_line in enumerate(source.splitlines(), 1):
        text = _strip_comment(raw_line)
        if not text:
            continue
        label, text = _split_label(text)
        if label is not None:
            key = label.casefold()
            if key in labels:
                raise AmigaAssemblerError(f"Symbol mehrfach definiert: {label}.", line_number)
            labels[key] = offset
        if not text:
            continue
        size = _item_size(
            text, offset, labels, line_number, cpu_model, fpu_model
        )
        items.append(_SourceItem(line_number, offset, text))
        offset += size

    if "_start" not in labels:
        raise AmigaAssemblerError("Einsprungmarke _start fehlt.")
    if labels["_start"] != 0:
        raise AmigaAssemblerError("_start muss am Beginn des CODE-Hunks stehen.")

    output = bytearray()
    instruction_count = 0
    for item in items:
        if len(output) != item.offset:
            raise AmigaAssemblerError("Interner Layoutfehler.", item.line)
        encoded, instructions = _encode_item(
            item, labels, cpu_model, fpu_model
        )
        output.extend(encoded)
        instruction_count += instructions

    code = bytes(output)
    return AmigaProgram(
        executable=_hunk_executable(code),
        code=code,
        entry_offset=labels["_start"],
        end_offset=len(code),
        instruction_count=instruction_count,
    )

def assemble_amiga_boot_source(
    source: str,
    *,
    filename: str = "<Amiga-Standalone-Assembler>",
    cpu_model: str = "mk68000",
    fpu_model: str = "FPU: None",
) -> AmigaBootProgram:
    """Erzeugt aus ``.bootable``-Quelltext ein direkt bootfähiges ADF."""
    if not is_amiga_boot_source(source):
        raise AmigaAssemblerError(
            "Für ein Standalone-ADF fehlt die Direktive .bootable."
        )
    program = assemble_amiga_source(
        source,
        filename=filename,
        cpu_model=cpu_model,
        fpu_model=fpu_model,
    )
    adf, boot_block = _bootable_adf(program.code)
    return AmigaBootProgram(
        adf=adf,
        boot_block=boot_block,
        code=program.code,
        entry_offset=BOOT_PAYLOAD_ADDRESS + program.entry_offset,
        end_offset=BOOT_PAYLOAD_ADDRESS + program.end_offset,
        instruction_count=program.instruction_count,
    )



def normalize_c64_charset_data(data: bytes) -> bytearray:
    """Normalisiert eine 2048- oder 2040-Byte-Zeichensatzdatei."""
    payload = bytes(data)
    if len(payload) == C64_CHARACTER_FILE_SIZE:
        return bytearray(payload)
    if len(payload) == C64_CHARACTER_EDITABLE_FILE_SIZE:
        return bytearray(C64_CHARACTER_BYTES) + bytearray(payload)
    raise ValueError(
        "Ein C64-Zeichensatz muss 2048 Bytes (256 Zeichen) oder "
        "2040 Bytes (Zeichen $01-$FF) enthalten."
    )


def c64_charset_character_rows(
    charset: Sequence[int],
    character_code: int,
) -> Tuple[int, ...]:
    code = int(character_code)
    if not 0 <= code < C64_CHARACTER_TOTAL_COUNT:
        raise ValueError("Der Zeichencode muss zwischen $00 und $FF liegen.")
    if len(charset) < C64_CHARACTER_FILE_SIZE:
        raise ValueError("Der Zeichensatz enthält weniger als 2048 Bytes.")
    start = code * C64_CHARACTER_BYTES
    return tuple(int(value) & 0xFF for value in charset[start:start + 8])


def c64_charset_set_character_rows(
    charset: bytearray,
    character_code: int,
    rows: Sequence[int],
) -> None:
    code = int(character_code)
    if not 1 <= code < C64_CHARACTER_TOTAL_COUNT:
        raise ValueError("Editierbar sind nur die Zeichen $01 bis $FF.")
    normalized = tuple(int(value) & 0xFF for value in rows)
    if len(normalized) != C64_CHARACTER_BYTES:
        raise ValueError("Ein C64-Zeichen muss genau acht Zeilen besitzen.")
    if len(charset) != C64_CHARACTER_FILE_SIZE:
        raise ValueError("Der Zeichensatz muss genau 2048 Bytes enthalten.")
    start = code * C64_CHARACTER_BYTES
    charset[start:start + 8] = bytes(normalized)


def c64_character_invert(rows: Sequence[int]) -> Tuple[int, ...]:
    return tuple((~int(value)) & 0xFF for value in rows)


def c64_character_mirror_horizontal(rows: Sequence[int]) -> Tuple[int, ...]:
    def reverse_bits(value: int) -> int:
        result = 0
        current = int(value) & 0xFF
        for _index in range(8):
            result = (result << 1) | (current & 1)
            current >>= 1
        return result

    return tuple(reverse_bits(value) for value in rows)


def c64_character_mirror_vertical(rows: Sequence[int]) -> Tuple[int, ...]:
    normalized = tuple(int(value) & 0xFF for value in rows)
    if len(normalized) != 8:
        raise ValueError("Ein C64-Zeichen muss genau acht Zeilen besitzen.")
    return tuple(reversed(normalized))


def c64_character_shift(
    rows: Sequence[int],
    delta_x: int,
    delta_y: int,
) -> Tuple[int, ...]:
    """Verschiebt ohne Wrap-Around; herausgeschobene Pixel gehen verloren."""
    source = tuple(int(value) & 0xFF for value in rows)
    if len(source) != 8:
        raise ValueError("Ein C64-Zeichen muss genau acht Zeilen besitzen.")

    shifted = [0] * 8
    dx = max(-7, min(7, int(delta_x)))
    dy = max(-7, min(7, int(delta_y)))
    for source_y, row in enumerate(source):
        target_y = source_y + dy
        if not 0 <= target_y < 8:
            continue
        if dx > 0:
            shifted[target_y] = (row >> dx) & 0xFF
        elif dx < 0:
            shifted[target_y] = (row << (-dx)) & 0xFF
        else:
            shifted[target_y] = row
    return tuple(shifted)


def format_c64_charset_asm(
    charset: Sequence[int],
    label: str = "C64CustomCharset",
) -> str:
    data = normalize_c64_charset_data(bytes(charset))
    lines = [
        "; 256 C64-Zeichen mit jeweils 8 Bitmapzeilen",
        "; Zeichen $00 ist reserviert, editierbar sind $01-$FF.",
        f"{label}:",
    ]
    for code in range(256):
        rows = c64_charset_character_rows(data, code)
        values = ", ".join(f"${value:02X}" for value in rows)
        lines.append(f"    .byte {values}    ; ${code:02X}")
    return "\n".join(lines) + "\n"


def format_c64_charset_c(
    charset: Sequence[int],
    identifier: str = "C64CustomCharset",
) -> str:
    data = normalize_c64_charset_data(bytes(charset))
    lines = [
        "/* 256 C64-Zeichen mit jeweils 8 Bitmapzeilen. */",
        f"const unsigned char {identifier}[256][8] = {{",
    ]
    for code in range(256):
        rows = c64_charset_character_rows(data, code)
        values = ", ".join(f"0x{value:02X}" for value in rows)
        comma = "," if code < 255 else ""
        lines.append(f"    {{ {values} }}{comma} /* 0x{code:02X} */")
    lines.append("};")
    return "\n".join(lines) + "\n"


def format_c64_charset_pascal(
    charset: Sequence[int],
    identifier: str = "C64CustomCharset",
) -> str:
    data = normalize_c64_charset_data(bytes(charset))
    lines = [
        "{ 256 C64-Zeichen mit jeweils 8 Bitmapzeilen. }",
        "const",
        f"    {identifier}: array[0..255, 0..7] of Byte = (",
    ]
    for code in range(256):
        rows = c64_charset_character_rows(data, code)
        values = ", ".join(f"${value:02X}" for value in rows)
        comma = "," if code < 255 else ""
        lines.append(f"        ({values}){comma} {{ ${code:02X} }}")
    lines.append("    );")
    return "\n".join(lines) + "\n"


C64_PALETTE_COLOR_COUNT = 16
C64_PALETTE_FILE_SIZE = C64_PALETTE_COLOR_COUNT * 3
C64_OUTPUT_FORMATS: Tuple[str, ...] = (
    "Assembler",
    "Pascal",
    "C",
    "BASIC",
)


def normalize_c64_color_hex(value: str) -> str:
    """Normalisiert eine RGB-Farbe auf #RRGGBB."""
    text = str(value).strip()
    if text.startswith("$"):
        text = text[1:]
    elif text.lower().startswith("0x"):
        text = text[2:]
    elif text.startswith("#"):
        text = text[1:]
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", text):
        raise ValueError("Eine Farbe muss als #RRGGBB angegeben werden.")
    return "#" + text.upper()


def normalize_c64_palette_entries(
    entries: Sequence[Sequence[str]],
) -> Tuple[Tuple[str, str], ...]:
    if len(entries) != C64_PALETTE_COLOR_COUNT:
        raise ValueError("Eine C64-Palette muss genau 16 Farben enthalten.")
    normalized = []
    for index, entry in enumerate(entries):
        if len(entry) != 2:
            raise ValueError("Jeder Paletteneintrag benötigt Name und RGB-Wert.")
        name = str(entry[0]).strip() or f"Farbe {index}"
        normalized.append((name, normalize_c64_color_hex(entry[1])))
    return tuple(normalized)


def encode_c64_palette_data(entries: Sequence[Sequence[str]]) -> bytes:
    palette = normalize_c64_palette_entries(entries)
    result = bytearray()
    for _name, color_hex in palette:
        result.extend(bytes.fromhex(color_hex[1:]))
    return bytes(result)


def decode_c64_palette_data(
    data: bytes,
    names: Optional[Sequence[str]] = None,
) -> Tuple[Tuple[str, str], ...]:
    payload = bytes(data)
    if len(payload) != C64_PALETTE_FILE_SIZE:
        raise ValueError("Eine rohe C64-Palette muss genau 48 Bytes enthalten.")
    if names is None:
        names = tuple(name for name, _color in C64_CHARACTER_PALETTE)
    if len(names) != C64_PALETTE_COLOR_COUNT:
        raise ValueError("Für eine Palette werden genau 16 Farbnamen benötigt.")
    entries = []
    for index in range(C64_PALETTE_COLOR_COUNT):
        red, green, blue = payload[index * 3:index * 3 + 3]
        entries.append((str(names[index]), f"#{red:02X}{green:02X}{blue:02X}"))
    return tuple(entries)


def format_c64_charset_basic(
    charset: Sequence[int],
    variable_name: str = "CS",
) -> str:
    data = normalize_c64_charset_data(bytes(charset))
    lines = [
        "10 REM 256 C64-ZEICHEN, JEWEILS 8 BITMAPZEILEN",
        "20 REM ZEICHEN 0 IST RESERVIERT, EDITIERBAR SIND 1 BIS 255",
        f"30 DIM {variable_name}(255,7)",
        "40 FOR C=0 TO 255:FOR R=0 TO 7:READ "
        f"{variable_name}(C,R):NEXT R:NEXT C",
    ]
    line_number = 100
    for code in range(256):
        rows = c64_charset_character_rows(data, code)
        values = ",".join(str(value) for value in rows)
        lines.append(f"{line_number} DATA {values}:REM ${code:02X}")
        line_number += 10
    return "\n".join(lines) + "\n"


def format_c64_palette_asm(
    entries: Sequence[Sequence[str]],
    label: str = "C64CustomPalette",
) -> str:
    palette = normalize_c64_palette_entries(entries)
    lines = [
        "; 16 C64-Farben als RGB-Tripel",
        f"{label}:",
    ]
    for index, (name, color_hex) in enumerate(palette):
        red, green, blue = bytes.fromhex(color_hex[1:])
        lines.append(
            f"    .byte ${red:02X}, ${green:02X}, ${blue:02X}"
            f"    ; {index:02d}: {name}"
        )
    return "\n".join(lines) + "\n"


def format_c64_palette_c(
    entries: Sequence[Sequence[str]],
    identifier: str = "C64CustomPalette",
) -> str:
    palette = normalize_c64_palette_entries(entries)
    lines = [
        "/* 16 C64-Farben als RGB-Tripel. */",
        f"const unsigned char {identifier}[16][3] = {{",
    ]
    for index, (name, color_hex) in enumerate(palette):
        red, green, blue = bytes.fromhex(color_hex[1:])
        comma = "," if index < 15 else ""
        lines.append(
            f"    {{ 0x{red:02X}, 0x{green:02X}, 0x{blue:02X} }}{comma}"
            f" /* {index:02d}: {name} */"
        )
    lines.append("};")
    return "\n".join(lines) + "\n"


def format_c64_palette_pascal(
    entries: Sequence[Sequence[str]],
    identifier: str = "C64CustomPalette",
) -> str:
    palette = normalize_c64_palette_entries(entries)
    lines = [
        "{ 16 C64-Farben als RGB-Tripel. }",
        "const",
        f"    {identifier}: array[0..15, 0..2] of Byte = (",
    ]
    for index, (name, color_hex) in enumerate(palette):
        red, green, blue = bytes.fromhex(color_hex[1:])
        comma = "," if index < 15 else ""
        lines.append(
            f"        (${red:02X}, ${green:02X}, ${blue:02X}){comma}"
            f" {{ {index:02d}: {name} }}"
        )
    lines.append("    );")
    return "\n".join(lines) + "\n"


def format_c64_palette_basic(
    entries: Sequence[Sequence[str]],
    variable_name: str = "CP",
) -> str:
    palette = normalize_c64_palette_entries(entries)
    lines = [
        "10 REM 16 C64-FARBEN ALS RGB-TRIPEL",
        f"20 DIM {variable_name}(15,2)",
        "30 FOR C=0 TO 15:FOR K=0 TO 2:READ "
        f"{variable_name}(C,K):NEXT K:NEXT C",
    ]
    line_number = 100
    for index, (name, color_hex) in enumerate(palette):
        red, green, blue = bytes.fromhex(color_hex[1:])
        basic_name = re.sub(r"[^A-Za-z0-9 ]+", "", name).upper()
        lines.append(
            f"{line_number} DATA {red},{green},{blue}:REM {index:02d} {basic_name}"
        )
        line_number += 10
    return "\n".join(lines) + "\n"


def normalize_c64_output_format(format_name: str) -> str:
    value = str(format_name).strip().lower()
    mapping = {
        "assembler": "Assembler",
        "asm": "Assembler",
        "pascal": "Pascal",
        "pas": "Pascal",
        "c": "C",
        "basic": "BASIC",
        "bas": "BASIC",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"Unbekanntes Ausgabeformat: {format_name}") from exc


def c64_output_format_extension(format_name: str) -> str:
    output_format = normalize_c64_output_format(format_name)
    return {
        "Assembler": ".asm",
        "Pascal": ".pas",
        "C": ".h",
        "BASIC": ".bas",
    }[output_format]


def c64_output_format_filter(format_name: str) -> str:
    output_format = normalize_c64_output_format(format_name)
    return {
        "Assembler": "MOS-6510-Assembler (*.asm *.inc)",
        "Pascal": "Pascal-Quellcode (*.pas *.inc)",
        "C": "C-Quellcode (*.c *.h)",
        "BASIC": "BASIC-Quellcode (*.bas)",
    }[output_format]


def format_c64_charset_output(
    charset: Sequence[int],
    format_name: str,
) -> str:
    output_format = normalize_c64_output_format(format_name)
    if output_format == "Assembler":
        return format_c64_charset_asm(charset)
    if output_format == "Pascal":
        return format_c64_charset_pascal(charset)
    if output_format == "C":
        return format_c64_charset_c(charset)
    return format_c64_charset_basic(charset)


def format_c64_palette_output(
    entries: Sequence[Sequence[str]],
    format_name: str,
) -> str:
    output_format = normalize_c64_output_format(format_name)
    if output_format == "Assembler":
        return format_c64_palette_asm(entries)
    if output_format == "Pascal":
        return format_c64_palette_pascal(entries)
    if output_format == "C":
        return format_c64_palette_c(entries)
    return format_c64_palette_basic(entries)


# ---------------------------------------------------------------------------
# C64-Textbildschirm- und Pixelbildschirm-Editoren.
# Der Textbildschirm speichert 40x25 Zeichenbytes und 40x25 Farbbytes.
# Der Pixelbildschirm verwendet eine plattformneutrale 320x200-Farbindex-
# Flaeche mit 16 Farben; im Rohformat werden je zwei Pixel in einem Byte
# zusammengefasst.
# ---------------------------------------------------------------------------
C64_TEXT_SCREEN_COLUMNS = 40
C64_TEXT_SCREEN_ROWS = 25
C64_TEXT_SCREEN_CELL_COUNT = C64_TEXT_SCREEN_COLUMNS * C64_TEXT_SCREEN_ROWS
C64_TEXT_SCREEN_FILE_SIZE = C64_TEXT_SCREEN_CELL_COUNT * 2

C64_PIXEL_SCREEN_WIDTH = 320
C64_PIXEL_SCREEN_HEIGHT = 200
C64_PIXEL_SCREEN_PIXEL_COUNT = C64_PIXEL_SCREEN_WIDTH * C64_PIXEL_SCREEN_HEIGHT
C64_PIXEL_SCREEN_PACKED_SIZE = C64_PIXEL_SCREEN_PIXEL_COUNT // 2


def normalize_c64_text_screen_data(
    characters: Sequence[int],
    colors: Optional[Sequence[int]] = None,
) -> Tuple[bytearray, bytearray]:
    chars = bytearray(int(value) & 0xFF for value in characters)
    if len(chars) != C64_TEXT_SCREEN_CELL_COUNT:
        raise ValueError("Ein C64-Textbildschirm benötigt genau 1000 Zeichenbytes.")
    if colors is None:
        cols = bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT)
    else:
        cols = bytearray(int(value) & 0x0F for value in colors)
    if len(cols) != C64_TEXT_SCREEN_CELL_COUNT:
        raise ValueError("Ein C64-Textbildschirm benötigt genau 1000 Farbbytes.")
    return chars, cols


def encode_c64_text_screen_data(
    characters: Sequence[int],
    colors: Sequence[int],
) -> bytes:
    chars, cols = normalize_c64_text_screen_data(characters, colors)
    return bytes(chars + cols)


def decode_c64_text_screen_data(data: bytes) -> Tuple[bytearray, bytearray]:
    payload = bytes(data)
    if len(payload) == C64_TEXT_SCREEN_CELL_COUNT:
        return normalize_c64_text_screen_data(payload, None)
    if len(payload) == C64_TEXT_SCREEN_FILE_SIZE:
        return normalize_c64_text_screen_data(
            payload[:C64_TEXT_SCREEN_CELL_COUNT],
            payload[C64_TEXT_SCREEN_CELL_COUNT:],
        )
    raise ValueError(
        "Eine Bildschirmseite muss 1000 Bytes (nur Zeichen) oder "
        "2000 Bytes (Zeichen und Farben) enthalten."
    )


def _format_asm_byte_rows(data: Sequence[int], width: int, comment: str) -> List[str]:
    values = [int(value) & 0xFF for value in data]
    lines = []
    for row_start in range(0, len(values), width):
        row = values[row_start:row_start + width]
        lines.append(
            "    .byte " + ", ".join(f"${value:02X}" for value in row)
            + f"    ; {comment} {row_start // width:02d}"
        )
    return lines


def format_c64_text_screen_asm(
    characters: Sequence[int],
    colors: Sequence[int],
) -> str:
    chars, cols = normalize_c64_text_screen_data(characters, colors)
    lines = [
        "; C64-Textbildschirm: 40 Spalten x 25 Zeilen",
        "C64TextScreenCharacters:",
    ]
    lines.extend(_format_asm_byte_rows(chars, 40, "Zeile"))
    lines.append("")
    lines.append("C64TextScreenColors:")
    lines.extend(_format_asm_byte_rows(cols, 40, "Farbzeile"))
    return "\n".join(lines) + "\n"


def format_c64_text_screen_c(
    characters: Sequence[int],
    colors: Sequence[int],
) -> str:
    chars, cols = normalize_c64_text_screen_data(characters, colors)
    lines = [
        "/* C64-Textbildschirm: 40 Spalten x 25 Zeilen. */",
        "const unsigned char C64TextScreenCharacters[25][40] = {",
    ]
    for row in range(25):
        start = row * 40
        values = ", ".join(f"0x{value:02X}" for value in chars[start:start + 40])
        lines.append(f"    {{ {values} }}{',' if row < 24 else ''}")
    lines.extend(["};", "", "const unsigned char C64TextScreenColors[25][40] = {"])
    for row in range(25):
        start = row * 40
        values = ", ".join(f"0x{value:02X}" for value in cols[start:start + 40])
        lines.append(f"    {{ {values} }}{',' if row < 24 else ''}")
    lines.append("};")
    return "\n".join(lines) + "\n"


def format_c64_text_screen_pascal(
    characters: Sequence[int],
    colors: Sequence[int],
) -> str:
    chars, cols = normalize_c64_text_screen_data(characters, colors)
    lines = [
        "{ C64-Textbildschirm: 40 Spalten x 25 Zeilen. }",
        "const",
        "    C64TextScreenCharacters: array[0..24, 0..39] of Byte = (",
    ]
    for row in range(25):
        start = row * 40
        values = ", ".join(f"${value:02X}" for value in chars[start:start + 40])
        lines.append(f"        ({values}){',' if row < 24 else ''}")
    lines.extend([
        "    );",
        "",
        "    C64TextScreenColors: array[0..24, 0..39] of Byte = (",
    ])
    for row in range(25):
        start = row * 40
        values = ", ".join(f"${value:02X}" for value in cols[start:start + 40])
        lines.append(f"        ({values}){',' if row < 24 else ''}")
    lines.append("    );")
    return "\n".join(lines) + "\n"


def format_c64_text_screen_basic(
    characters: Sequence[int],
    colors: Sequence[int],
) -> str:
    chars, cols = normalize_c64_text_screen_data(characters, colors)
    lines = [
        "10 REM C64-TEXTBILDSCHIRM 40 X 25",
        "20 DIM SC(999):DIM CO(999)",
        "30 FOR I=0 TO 999:READ SC(I):NEXT I",
        "40 FOR I=0 TO 999:READ CO(I):NEXT I",
    ]
    number = 100
    for data, label in ((chars, "ZEICHEN"), (cols, "FARBEN")):
        lines.append(f"{number} REM {label}")
        number += 10
        for start in range(0, 1000, 20):
            values = ",".join(str(value) for value in data[start:start + 20])
            lines.append(f"{number} DATA {values}")
            number += 10
    return "\n".join(lines) + "\n"


def format_c64_text_screen_output(
    characters: Sequence[int],
    colors: Sequence[int],
    format_name: str,
) -> str:
    output_format = normalize_c64_output_format(format_name)
    if output_format == "Assembler":
        return format_c64_text_screen_asm(characters, colors)
    if output_format == "Pascal":
        return format_c64_text_screen_pascal(characters, colors)
    if output_format == "C":
        return format_c64_text_screen_c(characters, colors)
    return format_c64_text_screen_basic(characters, colors)


def normalize_c64_pixel_screen(pixels: Sequence[int]) -> bytearray:
    result = bytearray(int(value) & 0x0F for value in pixels)
    if len(result) != C64_PIXEL_SCREEN_PIXEL_COUNT:
        raise ValueError("Ein Pixelbildschirm benötigt genau 320 x 200 Farbpixel.")
    return result


def encode_c64_pixel_screen_data(pixels: Sequence[int]) -> bytes:
    source = normalize_c64_pixel_screen(pixels)
    result = bytearray(C64_PIXEL_SCREEN_PACKED_SIZE)
    target = 0
    for index in range(0, len(source), 2):
        result[target] = ((source[index] & 0x0F) << 4) | (source[index + 1] & 0x0F)
        target += 1
    return bytes(result)


def decode_c64_pixel_screen_data(data: bytes) -> bytearray:
    payload = bytes(data)
    if len(payload) != C64_PIXEL_SCREEN_PACKED_SIZE:
        raise ValueError(
            "Ein 320x200-Pixelbildschirm mit 16 Farben muss genau 32000 Bytes enthalten."
        )
    result = bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT)
    target = 0
    for value in payload:
        result[target] = (value >> 4) & 0x0F
        result[target + 1] = value & 0x0F
        target += 2
    return result


def _pixel_offset(x: int, y: int) -> Optional[int]:
    x_value = int(x)
    y_value = int(y)
    if 0 <= x_value < C64_PIXEL_SCREEN_WIDTH and 0 <= y_value < C64_PIXEL_SCREEN_HEIGHT:
        return y_value * C64_PIXEL_SCREEN_WIDTH + x_value
    return None


def c64_pixel_screen_set(pixels: bytearray, x: int, y: int, color: int) -> None:
    offset = _pixel_offset(x, y)
    if offset is not None:
        pixels[offset] = int(color) & 0x0F


def c64_pixel_screen_draw_line(
    pixels: bytearray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: int,
) -> None:
    x = int(x1)
    y = int(y1)
    target_x = int(x2)
    target_y = int(y2)
    dx = abs(target_x - x)
    step_x = 1 if x < target_x else -1
    dy = -abs(target_y - y)
    step_y = 1 if y < target_y else -1
    error = dx + dy
    while True:
        c64_pixel_screen_set(pixels, x, y, color)
        if x == target_x and y == target_y:
            break
        doubled = error * 2
        if doubled >= dy:
            error += dy
            x += step_x
        if doubled <= dx:
            error += dx
            y += step_y


def _ordered_clipped_rect(x1: int, y1: int, x2: int, y2: int) -> Tuple[int, int, int, int]:
    left, right = sorted((int(x1), int(x2)))
    top, bottom = sorted((int(y1), int(y2)))
    return (
        max(0, left),
        max(0, top),
        min(C64_PIXEL_SCREEN_WIDTH - 1, right),
        min(C64_PIXEL_SCREEN_HEIGHT - 1, bottom),
    )


def c64_pixel_screen_draw_rect(
    pixels: bytearray, x1: int, y1: int, x2: int, y2: int, color: int
) -> None:
    left, top, right, bottom = _ordered_clipped_rect(x1, y1, x2, y2)
    c64_pixel_screen_draw_line(pixels, left, top, right, top, color)
    c64_pixel_screen_draw_line(pixels, left, bottom, right, bottom, color)
    c64_pixel_screen_draw_line(pixels, left, top, left, bottom, color)
    c64_pixel_screen_draw_line(pixels, right, top, right, bottom, color)


def c64_pixel_screen_fill_rect(
    pixels: bytearray, x1: int, y1: int, x2: int, y2: int, color: int
) -> None:
    left, top, right, bottom = _ordered_clipped_rect(x1, y1, x2, y2)
    if right < left or bottom < top:
        return
    value = int(color) & 0x0F
    width = right - left + 1
    row_data = bytes([value]) * width
    for y in range(top, bottom + 1):
        start = y * C64_PIXEL_SCREEN_WIDTH + left
        pixels[start:start + width] = row_data


def _circle_octants(center_x: int, center_y: int, x: int, y: int) -> Tuple[Tuple[int, int], ...]:
    return (
        (center_x + x, center_y + y),
        (center_x - x, center_y + y),
        (center_x + x, center_y - y),
        (center_x - x, center_y - y),
        (center_x + y, center_y + x),
        (center_x - y, center_y + x),
        (center_x + y, center_y - x),
        (center_x - y, center_y - x),
    )


def c64_pixel_screen_draw_circle(
    pixels: bytearray, center_x: int, center_y: int, radius: int, color: int
) -> None:
    r = max(0, int(radius))
    x = r
    y = 0
    decision = 1 - r
    while x >= y:
        for point_x, point_y in _circle_octants(int(center_x), int(center_y), x, y):
            c64_pixel_screen_set(pixels, point_x, point_y, color)
        y += 1
        if decision < 0:
            decision += 2 * y + 1
        else:
            x -= 1
            decision += 2 * (y - x) + 1


def c64_pixel_screen_fill_circle(
    pixels: bytearray, center_x: int, center_y: int, radius: int, color: int
) -> None:
    r = max(0, int(radius))
    cx = int(center_x)
    cy = int(center_y)
    x = r
    y = 0
    decision = 1 - r
    while x >= y:
        for row_y, left, right in (
            (cy + y, cx - x, cx + x),
            (cy - y, cx - x, cx + x),
            (cy + x, cx - y, cx + y),
            (cy - x, cx - y, cx + y),
        ):
            c64_pixel_screen_fill_rect(pixels, left, row_y, right, row_y, color)
        y += 1
        if decision < 0:
            decision += 2 * y + 1
        else:
            x -= 1
            decision += 2 * (y - x) + 1


def c64_pixel_screen_flood_fill(
    pixels: bytearray, x: int, y: int, color: int
) -> None:
    offset = _pixel_offset(x, y)
    if offset is None:
        return
    replacement = int(color) & 0x0F
    target = pixels[offset]
    if target == replacement:
        return
    stack = [(int(x), int(y))]
    while stack:
        current_x, current_y = stack.pop()
        current_offset = _pixel_offset(current_x, current_y)
        if current_offset is None or pixels[current_offset] != target:
            continue
        pixels[current_offset] = replacement
        stack.append((current_x - 1, current_y))
        stack.append((current_x + 1, current_y))
        stack.append((current_x, current_y - 1))
        stack.append((current_x, current_y + 1))


def format_c64_pixel_screen_asm(pixels: Sequence[int]) -> str:
    packed = encode_c64_pixel_screen_data(pixels)
    lines = [
        "; 320x200-Pixelbildschirm, 16 Farben, zwei Pixel pro Byte",
        "C64PixelScreenWidth = 320",
        "C64PixelScreenHeight = 200",
        "C64PixelScreenData:",
    ]
    lines.extend(_format_asm_byte_rows(packed, 16, "Block"))
    return "\n".join(lines) + "\n"


def format_c64_pixel_screen_c(pixels: Sequence[int]) -> str:
    packed = encode_c64_pixel_screen_data(pixels)
    lines = [
        "/* 320x200-Pixelbildschirm, 16 Farben, zwei Pixel pro Byte. */",
        "#define C64_PIXEL_SCREEN_WIDTH 320",
        "#define C64_PIXEL_SCREEN_HEIGHT 200",
        f"const unsigned char C64PixelScreenData[{len(packed)}] = {{",
    ]
    for start in range(0, len(packed), 16):
        values = ", ".join(f"0x{value:02X}" for value in packed[start:start + 16])
        lines.append(f"    {values}{',' if start + 16 < len(packed) else ''}")
    lines.append("};")
    return "\n".join(lines) + "\n"


def format_c64_pixel_screen_pascal(pixels: Sequence[int]) -> str:
    packed = encode_c64_pixel_screen_data(pixels)
    lines = [
        "{ 320x200-Pixelbildschirm, 16 Farben, zwei Pixel pro Byte. }",
        "const",
        "    C64PixelScreenWidth = 320;",
        "    C64PixelScreenHeight = 200;",
        f"    C64PixelScreenData: array[0..{len(packed) - 1}] of Byte = (",
    ]
    for start in range(0, len(packed), 16):
        values = ", ".join(f"${value:02X}" for value in packed[start:start + 16])
        lines.append(f"        {values}{',' if start + 16 < len(packed) else ''}")
    lines.append("    );")
    return "\n".join(lines) + "\n"


def format_c64_pixel_screen_basic(pixels: Sequence[int]) -> str:
    packed = encode_c64_pixel_screen_data(pixels)
    lines = [
        "10 REM 320X200-PIXELBILDSCHIRM, 16 FARBEN",
        f"20 DIM PX({len(packed) - 1})",
        f"30 FOR I=0 TO {len(packed) - 1}:READ PX(I):NEXT I",
    ]
    number = 100
    for start in range(0, len(packed), 16):
        values = ",".join(str(value) for value in packed[start:start + 16])
        lines.append(f"{number} DATA {values}")
        number += 10
    return "\n".join(lines) + "\n"


def format_c64_pixel_screen_output(pixels: Sequence[int], format_name: str) -> str:
    output_format = normalize_c64_output_format(format_name)
    if output_format == "Assembler":
        return format_c64_pixel_screen_asm(pixels)
    if output_format == "Pascal":
        return format_c64_pixel_screen_pascal(pixels)
    if output_format == "C":
        return format_c64_pixel_screen_c(pixels)
    return format_c64_pixel_screen_basic(pixels)


# ---------------------------------------------------------------------------
# CHM-Hilfe: Projekt-, Inhalts- und Indexdaten
# ---------------------------------------------------------------------------
@dataclass
class ChmSitemapEntry:
    title: str
    local: str = ""
    children: List["ChmSitemapEntry"] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Toleranter Parser für die OBJECT/PARAM-Struktur von HHC und HHK.
# ---------------------------------------------------------------------------
class ChmSitemapParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.roots: List[ChmSitemapEntry] = []
        self.parents: List[Optional[ChmSitemapEntry]] = []
        self.last_at_depth: Dict[int, ChmSitemapEntry] = {}
        self.params: Optional[Dict[str, str]] = None

    def handle_starttag(self, tag, attrs) -> None:
        tag = tag.lower()
        if tag == "ul":
            depth = len(self.parents)
            parent = self.last_at_depth.get(depth)
            if parent is None and self.parents:
                parent = self.parents[-1]
            self.parents.append(parent)
            return

        if tag == "object":
            self.params = {}
            return

        if tag == "param" and self.params is not None:
            values = {key.lower(): value or "" for key, value in attrs}
            name = values.get("name", "").strip().lower()
            if name:
                self.params[name] = values.get("value", "").strip()

    def handle_endtag(self, tag) -> None:
        tag = tag.lower()
        if tag == "object" and self.params is not None:
            title = self.params.get("name", "").strip()
            local = self.params.get("local", "").strip()
            if title or local:
                entry = ChmSitemapEntry(
                    title or Path(local).name or "(ohne Titel)",
                    local,
                )
                parent = self.parents[-1] if self.parents else None
                if parent is None:
                    self.roots.append(entry)
                else:
                    parent.children.append(entry)
                self.last_at_depth[len(self.parents)] = entry
            self.params = None
            return

        if tag == "ul" and self.parents:
            self.parents.pop()
            maximum_depth = len(self.parents)
            for depth in list(self.last_at_depth):
                if depth > maximum_depth:
                    del self.last_at_depth[depth]

def decode_chm_text(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")

    header = data[:8192].decode("ascii", errors="ignore")
    match = re.search(
        r"charset\s*=\s*[\"']?\s*([A-Za-z0-9._-]+)",
        header,
        re.IGNORECASE,
    )
    encodings = [match.group(1)] if match else []
    encodings.extend(["utf-8", "cp1252", "latin-1"])
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("latin-1", errors="replace")

def parse_chm_sitemap(path: Optional[Path]) -> List[ChmSitemapEntry]:
    if path is None or not path.is_file():
        return []
    parser = ChmSitemapParser()
    parser.feed(decode_chm_text(path))
    parser.close()
    return parser.roots

def iter_chm_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path

def find_chm_file_by_suffix(root: Path, suffix: str) -> Optional[Path]:
    suffix = suffix.lower()
    candidates = [
        path for path in iter_chm_files(root)
        if path.suffix.lower() == suffix
    ]
    return min(
        candidates,
        key=lambda path: (len(path.parts), str(path).lower()),
        default=None,
    )

# ---------------------------------------------------------------------------
# Zerlegt ein HHC/HHK-Local-Feld in relativen Pfad und Sprungmarke.
# ---------------------------------------------------------------------------
def clean_chm_local(value: str) -> Tuple[str, str]:
    value = html.unescape(value.strip()).strip("\"'").replace("\\", "/")
    lowered = value.lower()
    if "::/" in lowered:
        value = value[lowered.index("::/") + 3:]
    value = value.split("?", 1)[0]
    path_part, separator, fragment = value.partition("#")
    from urllib.parse import unquote
    path_part = unquote(path_part).lstrip("/")
    parts = [
        part for part in path_part.split("/")
        if part not in ("", ".")
    ]
    if any(part == ".." for part in parts):
        return "", ""
    return "/".join(parts), unquote(fragment) if separator else ""

# ---------------------------------------------------------------------------
# Loest Windows-typische, nicht case-sensitive CHM-Pfade sicher auf.
# ---------------------------------------------------------------------------
def resolve_chm_path(root: Path, relative: str) -> Optional[Path]:
    current = root
    for part in Path(relative).parts:
        exact = current / part
        if exact.exists():
            current = exact
            continue
        try:
            current = next(
                child for child in current.iterdir()
                if child.name.casefold() == part.casefold()
            )
        except (StopIteration, OSError):
            return None

    try:
        current.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return current if current.is_file() else None

def read_chm_project_options(project_file: Optional[Path]) -> Dict[str, str]:
    if project_file is None:
        return {}
    result: Dict[str, str] = {}
    in_options = False
    for raw_line in decode_chm_text(project_file).splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_options = line.casefold() == "[options]"
            continue
        if in_options and "=" in line:
            key, value = line.split("=", 1)
            result[key.strip().casefold()] = value.strip()
    return result

# ---------------------------------------------------------------------------
# Entpackt CHM per 7-Zip oder unter Windows per hh.exe.
# ---------------------------------------------------------------------------
class ChmExtractor:
    @staticmethod
    def seven_zip_command() -> Optional[str]:
        for command in ("7zz", "7z", "7za"):
            found = shutil.which(command)
            if found:
                return found
        if os.name == "nt":
            for variable in ("ProgramFiles", "ProgramFiles(x86)"):
                base = os.environ.get(variable)
                if base:
                    candidate = Path(base) / "7-Zip" / "7z.exe"
                    if candidate.is_file():
                        return str(candidate)
        return None

    @staticmethod
    def extract_with_7zip(command: str, source: Path, target: Path) -> None:
        completed = subprocess.run(
            [command, "x", "-y", f"-o{target}", str(source)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        if completed.returncode not in (0, 1):
            raise RuntimeError(
                "7-Zip konnte die CHM-Datei nicht entpacken.\n\n"
                + completed.stdout[-1500:].strip()
            )

    @staticmethod
    def extract_with_windows_help(source: Path, target: Path) -> None:
        helper = Path(os.environ.get("WINDIR", r"C:\Windows")) / "hh.exe"
        if not helper.is_file():
            raise RuntimeError("hh.exe wurde nicht gefunden.")

        process = subprocess.Popen(
            [str(helper), "-decompile", str(target), str(source)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()

        deadline = time.monotonic() + 30.0
        previous_count = -1
        stable_rounds = 0
        while time.monotonic() < deadline:
            count = sum(1 for _ in iter_chm_files(target))
            if count > 0 and count == previous_count:
                stable_rounds += 1
                if stable_rounds >= 4:
                    return
            else:
                stable_rounds = 0
            previous_count = count
            time.sleep(0.25)
        if previous_count <= 0:
            raise RuntimeError("Windows HTML Help hat keine Dateien extrahiert.")

    @classmethod
    def extract(cls, source: Path, target: Path) -> None:
        errors: List[str] = []
        command = cls.seven_zip_command()
        if command:
            try:
                cls.extract_with_7zip(command, source, target)
                if any(iter_chm_files(target)):
                    return
            except Exception as exc:
                errors.append(str(exc))

        if os.name == "nt":
            try:
                cls.extract_with_windows_help(source, target)
                if any(iter_chm_files(target)):
                    return
            except Exception as exc:
                errors.append(str(exc))

        hint = (
            "Installiere 7-Zip und stelle 7z/7zz ueber PATH bereit."
            if os.name == "nt"
            else "Installiere 7-Zip, z. B. mit 'sudo apt install p7zip-full'."
        )
        details = "\n\n".join(errors)
        raise RuntimeError(
            "Kein verwendbares CHM-Entpackprogramm gefunden.\n"
            f"{hint}\n\n{details}"
        )


# ---------------------------------------------------------------------------
# D64-Dateisystem
# Eine D64-Datei besitzt kein unterstütztes oder gültiges Layout.
# ---------------------------------------------------------------------------
class D64Error(Exception):
    pass

# ---------------------------------------------------------------------------
# Liefert die Sektoranzahl einer 1541-Spur.
# ---------------------------------------------------------------------------
def sectors_on_track(track: int) -> int:
    if 1  <= track <= 17:   return 21
    if 18 <= track <= 24:   return 19
    if 25 <= track <= 30:   return 18
    if 31 <= track <= 42:   return 17
    
    raise D64Error(f"Ungültige D64-Spur: {track}")

def sector_count_for_tracks(track_count: int) -> int:
    return sum(sectors_on_track(track) for track in range(1, track_count + 1))

# ---------------------------------------------------------------------------
# Erkennt 35- bis 42-Spur-Images, optional mit Fehlerbyte-Tabelle.
# ---------------------------------------------------------------------------
def detect_d64_layout(file_size: int) -> Tuple[int, int, bool]:
    for track_count in range(35, 43):
        sector_count = sector_count_for_tracks(track_count)
        data_size = sector_count * 256
        if file_size == data_size:
            return track_count, data_size, False
        if file_size == data_size + sector_count:
            return track_count, data_size, True

    raise D64Error(
        f"Nicht unterstützte D64-Größe: {file_size:,} Bytes. "
        "Erwartet wird ein 35- bis 42-Spur-Image, optional mit Fehlerbytes."
    )

# ---------------------------------------------------------------------------
# Konvertiert die für D64-Namen übliche PETSCII-Teilmenge.
# ---------------------------------------------------------------------------
def petscii_to_text(data: bytes) -> str:
    result = []
    for value in data:
        if value in (0x00, 0xA0):
            result.append(" ")
        elif 0x20 <= value <= 0x5F:
            result.append(chr(value))
        elif 0x61 <= value <= 0x7A:
            result.append(chr(value).upper())
        elif 0xC1 <= value <= 0xDA:
            result.append(chr(value - 0x80))
        else:
            result.append("·")
    return "".join(result).rstrip()


@dataclass(frozen=True)
class D64DirectoryEntry:
    name: str
    file_type: str
    blocks: int
    start_track: int
    start_sector: int
    closed: bool
    locked: bool

    @property
    def type_display(self) -> str:
        prefix = "" if self.closed else "*"
        suffix = "<" if self.locked else ""
        return f"{prefix}{self.file_type}{suffix}"

    def listing_line(self) -> str:
        quoted_name = f'"{self.name[:16]}"'
        return (
            f"{self.blocks:>5}  {quoted_name:<18} "
            f"{self.type_display:<5}  {self.start_track:02d}/{self.start_sector:02d}"
        )


@dataclass(frozen=True)
class D64Directory:
    disk_name: str
    disk_id: str
    dos_type: str
    track_count: int
    has_error_table: bool
    free_blocks: Optional[int]
    entries: Tuple[D64DirectoryEntry, ...]


class D64Image:
    FILE_TYPES = {
        0: "DEL",
        1: "SEQ",
        2: "PRG",
        3: "USR",
        4: "REL",
    }

    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            raw_data = self.path.read_bytes()
        except OSError as exc:
            raise D64Error(f"D64-Datei kann nicht gelesen werden: {exc}") from exc

        self.track_count, data_size, self.has_error_table = detect_d64_layout(
            len(raw_data)
        )
        self.data = raw_data[:data_size]

    def sector_offset(self, track: int, sector: int) -> int:
        if not 1 <= track <= self.track_count:
            raise D64Error(f"Spur {track} liegt außerhalb des Images.")

        sector_count = sectors_on_track(track)
        if not 0 <= sector < sector_count:
            raise D64Error(
                f"Sektor {track}/{sector} ist ungültig; Spur {track} "
                f"besitzt die Sektoren 0 bis {sector_count - 1}."
            )

        previous_sectors = sum(
            sectors_on_track(value) for value in range(1, track)
        )
        return (previous_sectors + sector) * 256

    def read_sector(self, track: int, sector: int) -> bytes:
        offset = self.sector_offset(track, sector)
        return self.data[offset : offset + 256]

    def _free_blocks(self, bam: bytes) -> Optional[int]:
        # Das Standard-BAM enthält Einträge für die Spuren 1 bis 35.
        if len(bam) < 144:
            return None
        return sum(bam[4 + (track - 1) * 4] for track in range(1, 36))

    def directory(self) -> D64Directory:
        bam = self.read_sector(18, 0)
        disk_name = petscii_to_text(bam[0x90:0xA0]) or "UNBENANNT"
        disk_id = petscii_to_text(bam[0xA2:0xA4])
        dos_type = petscii_to_text(bam[0xA5:0xA7])

        track = bam[0] or 18
        sector = bam[1] if bam[0] else 1
        visited = set()
        entries = []

        while track:
            location = (track, sector)
            if location in visited:
                raise D64Error(
                    f"Zyklische Verzeichniskette bei Spur/Sektor {track}/{sector}."
                )
            visited.add(location)

            directory_sector = self.read_sector(track, sector)
            for index in range(8):
                offset = 2 + index * 32
                raw_type = directory_sector[offset]
                # Typ 0 bezeichnet gelöschte/DEL-Einträge. Die Dateiliste soll
                # nur die aktuell im C64-Verzeichnis vorhandenen Dateien zeigen.
                if raw_type == 0 or (raw_type & 0x07) == 0:
                    continue

                type_number = raw_type & 0x07
                file_type = self.FILE_TYPES.get(type_number, f"T{type_number}")
                start_track = directory_sector[offset + 1]
                start_sector = directory_sector[offset + 2]
                name = petscii_to_text(directory_sector[offset + 3 : offset + 19])
                blocks = int.from_bytes(
                    directory_sector[offset + 28 : offset + 30], "little"
                )

                entries.append(
                    D64DirectoryEntry(
                        name=name or "(OHNE NAME)",
                        file_type=file_type,
                        blocks=blocks,
                        start_track=start_track,
                        start_sector=start_sector,
                        closed=bool(raw_type & 0x80),
                        locked=bool(raw_type & 0x40),
                    )
                )

            track = directory_sector[0]
            sector = directory_sector[1]

        return D64Directory(
            disk_name=disk_name,
            disk_id=disk_id,
            dos_type=dos_type,
            track_count=self.track_count,
            has_error_table=self.has_error_table,
            free_blocks=self._free_blocks(bam),
            entries=tuple(entries),
        )


# ---------------------------------------------------------------------------
# Projektdateien (*.pro): INI-basierte Sammlung der zum Projekt gehoerenden
# Quellen und Medien. Die sichtbaren Kategorien sind feste Root-Knoten und
# koennen in der GUI weder umbenannt noch geloescht werden.
# ---------------------------------------------------------------------------
PROJECT_CATEGORIES: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("basic", "BASIC - Programme", (".bas", ".basic")),
    ("assembler", "Assembler-Programme", (".asm", ".s", ".a65", ".m68k", ".inc")),
    ("pascal", "Pascal-Programme", (".pas", ".pp")),
    ("c", "C-Programme", (".c", ".h")),
    ("character_maps", "Character Map's", (".chr", ".charset")),
    ("palettes", "Paletten", (".pal", ".palette")),
    ("char_screens", "Char Screen's", (".scr", ".screen")),
    ("pixel_screens", "Pixel Screen's", (".px16", ".pixel", ".pix")),
    ("text_files", "Textdateien", (".txt", ".text", ".log", ".md")),
    ("sid_files", "SID's", (".sid",)),
    ("images", "Bilder", (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".iff", ".ilbm")),
    ("other", "Sonstiges", ()),
)

PROJECT_CATEGORY_TITLES: Dict[str, str] = {
    key: title for key, title, _extensions in PROJECT_CATEGORIES
}
PROJECT_CATEGORY_EXTENSIONS: Dict[str, Tuple[str, ...]] = {
    key: extensions for key, _title, extensions in PROJECT_CATEGORIES
}
PROJECT_CATEGORY_DEFAULT_EXTENSIONS: Dict[str, str] = {
    key: (extensions[0] if extensions else ".dat")
    for key, _title, extensions in PROJECT_CATEGORIES
}


def project_untitled_filename(
    category_key: str,
    existing_names: Iterable[str] = (),
    *,
    directory: Optional[Path] = None,
) -> str:
    """Liefert einen freien Namen ``Unbenannt_<n>.<ext>``.

    Geprueft werden sowohl die bereits sichtbaren Projekteintraege als auch
    vorhandene Dateien im Zielverzeichnis. Dadurch wird kein Eintrag und keine
    Datei versehentlich ueberschrieben.
    """
    extension = PROJECT_CATEGORY_DEFAULT_EXTENSIONS.get(category_key, ".dat")
    if extension and not extension.startswith("."):
        extension = "." + extension
    used_names = {str(value).casefold() for value in existing_names}
    used_stems = {Path(str(value)).stem.casefold() for value in existing_names}
    target_directory = Path(directory) if directory is not None else None
    number = 1
    while True:
        filename = f"Unbenannt_{number}{extension}"
        stem = Path(filename).stem.casefold()
        name_used = filename.casefold() in used_names or stem in used_stems
        file_used = bool(
            target_directory is not None
            and (target_directory / filename).exists()
        )
        if not name_used and not file_used:
            return filename
        number += 1


def empty_project_entries() -> Dict[str, List[Dict[str, str]]]:
    return {key: [] for key, _title, _extensions in PROJECT_CATEGORIES}


def project_category_for_path(path: Path) -> str:
    suffix = Path(path).suffix.casefold()
    for key, _title, extensions in PROJECT_CATEGORIES:
        if suffix in extensions:
            return key
    return "other"


def _project_storage_path(path_value: str, project_path: Path) -> str:
    candidate = Path(path_value).expanduser()
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate
    try:
        relative = os.path.relpath(
            str(resolved),
            str(project_path.parent.resolve()),
        )
        return Path(relative).as_posix()
    except (OSError, ValueError):
        return str(resolved)


def _project_loaded_path(path_value: str, project_path: Path) -> str:
    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute():
        candidate = project_path.parent / candidate
    try:
        return str(candidate.resolve())
    except OSError:
        return str(candidate)


def format_project_ini(
    entries: Dict[str, List[Dict[str, str]]],
    project_path: Path,
) -> str:
    project_path = Path(project_path)
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser["Project"] = {
        "Format": "dBase2Many Project",
        "Version": "1",
    }
    for key, title, _extensions in PROJECT_CATEGORIES:
        section = f"Category.{key}"
        parser[section] = {"Title": title}
        for index, entry in enumerate(entries.get(key, ()), 1):
            path_value = str(entry.get("path", "")).strip()
            if not path_value:
                continue
            payload = {
                "title": str(entry.get("title", "") or Path(path_value).name),
                "path": _project_storage_path(path_value, project_path),
            }
            parser[section][f"Item{index:04d}"] = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            )
    from io import StringIO
    stream = StringIO()
    parser.write(stream)
    return stream.getvalue()


def parse_project_ini(text: str, project_path: Path) -> Dict[str, List[Dict[str, str]]]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read_string(text)
    entries = empty_project_entries()
    for key, _title, _extensions in PROJECT_CATEGORIES:
        section = f"Category.{key}"
        if not parser.has_section(section):
            continue
        values = sorted(
            (
                (name, value)
                for name, value in parser.items(section)
                if name.casefold().startswith("item")
            ),
            key=lambda pair: pair[0].casefold(),
        )
        for _name, value in values:
            try:
                payload = json.loads(value)
            except json.JSONDecodeError:
                payload = {"path": value, "title": Path(value).name}
            path_value = str(payload.get("path", "")).strip()
            if not path_value:
                continue
            loaded_path = _project_loaded_path(path_value, Path(project_path))
            entries[key].append(
                {
                    "title": str(payload.get("title", "") or Path(loaded_path).name),
                    "path": loaded_path,
                }
            )
    return entries


def save_project_ini(
    project_path: Path,
    entries: Dict[str, List[Dict[str, str]]],
) -> None:
    project_path = Path(project_path)
    project_path.parent.mkdir(parents=True, exist_ok=True)
    project_path.write_text(
        format_project_ini(entries, project_path),
        encoding="utf-8",
        newline="\n",
    )


def load_project_ini(project_path: Path) -> Dict[str, List[Dict[str, str]]]:
    project_path = Path(project_path)
    return parse_project_ini(
        project_path.read_text(encoding="utf-8-sig"),
        project_path,
    )


# ---------------------------------------------------------------------------
# Qt5-Anwendung
# ---------------------------------------------------------------------------
def run_gui(initial_directory: Optional[Path] = None) -> int:
    try:
        from PyQt5.QtCore import (
            QDir,
            QEvent,
            QFileInfo,
            QObject,
            QPoint,
            QPointF,
            QRect,
            QRectF,
            QSettings,
            QSize,
            QTemporaryDir,
            QThread,
            QTimer,
            Qt,
            QUrl,
            pyqtSignal,
        )
        from PyQt5.QtGui import (
            QCloseEvent,
            QColor,
            QDesktopServices,
            QFont,
            QFontDatabase,
            QIcon,
            QImage,
            QKeySequence,
            QPainter,
            QPainterPath,
            QPalette,
            QPen,
            QPixmap,
            QSyntaxHighlighter,
            QTextCharFormat,
            QTextCursor,
            QTextFormat,
        )
        from PyQt5.QtWidgets import (
            QAbstractScrollArea,
            QAction,
            QApplication,
            QButtonGroup,
            QComboBox,
            QColorDialog,
            QDialog,
            QDockWidget,
            QFileDialog,
            QFileIconProvider,
            QFileSystemModel,
            QFrame,
            QGridLayout,
            QGroupBox,
            QHBoxLayout,
            QInputDialog,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QMenu,
            QMenuBar,
            QMessageBox,
            QPlainTextEdit,
            QPushButton,
            QRadioButton,
            QScrollArea,
            QSizePolicy,
            QSplitter,
            QStatusBar,
            QStyle,
            QTabBar,
            QTabWidget,
            QTextBrowser,
            QTextEdit,
            QToolBar,
            QToolButton,
            QTreeView,
            QTreeWidget,
            QTreeWidgetItem,
            QTreeWidgetItemIterator,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as exc:
        print(
            "PyQt5 ist nicht installiert.\n"
            "Installiere das Qt5-Paket mit:\n\n"
            "    py -m pip install PyQt5\n",
            file=sys.stderr,
        )
        print(f"Technischer Fehler: {exc}", file=sys.stderr)
        return 2

    try:
        from PyQt5.QtWebEngineWidgets import (
            QWebEnginePage,
            QWebEngineSettings,
            QWebEngineView,
        )
        QT_WEBENGINE_AVAILABLE = True
        QT_WEBENGINE_ERROR = ""
    except ImportError as exc:
        QWebEnginePage = QObject
        QWebEngineSettings = None
        QWebEngineView = None
        QT_WEBENGINE_AVAILABLE = False
        QT_WEBENGINE_ERROR = str(exc)

    # -----------------------------------------------------------------------
    # Hervorhebung für MOS-6510-Assembler, C64-Pascal und C64-C.
    # -----------------------------------------------------------------------
    class AssemblerSyntaxHighlighter(QSyntaxHighlighter):
        OPCODES = (
            "ADC", "AHX", "ANC", "AND", "ARR", "ASL", "ASR",
            "BCC", "BCS", "BEQ", "BIT", "BMI", "BNE", "BPL", "BRK",
            "BVC", "BVS", "CLC", "CLD", "CLI", "CLV", "CMP", "CPX",
            "CPY", "DCP", "DEC", "DEX", "DEY", "EOR", "INC", "INX",
            "INY", "ISC", "ISB", "JAM", "JMP", "JSR", "KIL", "LAS",
            "LAX", "LDA", "LDX", "LDY", "LSR", "NOP", "ORA", "PHA",
            "PHP", "PLA", "PLP", "RLA", "ROL", "ROR", "RRA", "RTI",
            "RTS", "SAX", "SBC", "SEC", "SED", "SEI", "SHX", "SHY",
            "SLO", "SRE", "STA", "STX", "STY", "TAS", "TAX", "TAY",
            "TSX", "TXA", "TXS", "TYA", "XAA",
            "ADD", "ADDA", "ADDI", "ADDQ", "ANDI", "BRA", "BSR",
            "BGE", "BGT", "BHI", "BHS", "BLE", "BLO", "BLS", "BLT",
            "CLR", "CMPI", "DIVS", "DIVU", "EORI", "EXT", "LEA",
            "LSL", "MOVE", "MOVEQ", "MULS", "MULU", "NEG", "ORI",
            "SUB", "SUBA", "SUBI", "SUBQ", "SWAP", "TST",
            "RTD", "BKPT", "EXTB", "FNOP",
            "MOV", "PUSH", "POP", "CALL", "JE", "JNE", "JZ", "JNZ",
            "JL", "JLE", "JG", "JGE", "TEST", "IMUL", "SHL", "SHR",
            "SAR", "INC", "LEAVE", "INT", "PUSHAD", "POPAD", "CDQ",
        )
        OPCODE_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:"
            + "|".join(OPCODES)
            + r")(?:\.[BWL])?(?![A-Za-z0-9_])",
            re.IGNORECASE,
        )
        LABEL_PATTERN = re.compile(
            r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*:",
        )
        JUMP_TARGET_PATTERN = re.compile(
            r"^\s*(?:[A-Za-z_.$][A-Za-z0-9_.$]*\s*:\s*)?"
            r"(?:BCC|BCS|BEQ|BGE|BGT|BHI|BHS|BLE|BLO|BLS|BLT|BMI|"
            r"BNE|BPL|BRA|BSR|BVC|BVS|JMP|JSR|CALL|JE|JNE|JZ|JNZ|"
            r"JL|JLE|JG|JGE)(?:\.[BWL])?\s+"
            r"(?:\(\s*)?"
            r"(?P<target>[A-Za-z_.$][A-Za-z0-9_.$]*)",
            re.IGNORECASE,
        )
        PASCAL_KEYWORD_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:"
            r"program|const|type|var|begin|end|if|then|else|while|do|"
            r"repeat|until|for|to|downto|break|continue|integer|"
            r"byte|char|boolean|true|false|div|mod|and|or|xor|not|"
            r"record|array|of|class|private|protected|public|published|"
            r"procedure|function|constructor|destructor"
            r")(?![A-Za-z0-9_])",
            re.IGNORECASE,
        )
        PASCAL_NUMBER_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:\$[0-9A-F]+|%[01]+|[0-9]+)"
            r"(?![A-Za-z0-9_])",
            re.IGNORECASE,
        )
        PASCAL_STRING_PATTERN = re.compile(r"'(?:''|[^'\r\n])*'")
        PASCAL_COMMENT_PATTERN = re.compile(r"//.*|\{.*?\}|\(\*.*?\*\)")
        C_KEYWORD_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:"
            r"const|typedef|struct|extern|static|unsigned|signed|int|char|"
            r"bool|_Bool|void|if|else|"
            r"while|do|for|break|continue|return|true|false"
            r")(?![A-Za-z0-9_])"
        )
        C_NUMBER_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:0[xX][0-9A-Fa-f]+|0[bB][01]+|[0-9]+)"
            r"[uUlL]*(?![A-Za-z0-9_])"
        )
        C_STRING_PATTERN = re.compile(
            r'"(?:\\.|[^"\\\r\n])*"|\'(?:\\.|[^\'\\\r\n])\''
        )
        C_COMMENT_PATTERN = re.compile(r"//.*|/\*.*?\*/")
        C_PREPROCESSOR_PATTERN = re.compile(r"^\s*#.*")

        def __init__(self, document):
            super().__init__(document)
            self.enabled = False
            self.pascal_enabled = False
            self.c_enabled = False
            self.dark_mode = False
            self._jump_target_names = set()
            self._jump_target_refresh_pending = False

            self.opcode_format = QTextCharFormat()
            self.opcode_format.setFontWeight(QFont.Bold)

            self.comment_format = QTextCharFormat()
            self.jump_target_format = QTextCharFormat()
            self.jump_target_format.setFontUnderline(True)
            self.pascal_keyword_format = QTextCharFormat()
            self.pascal_keyword_format.setFontWeight(QFont.Bold)
            self.pascal_string_format = QTextCharFormat()
            self.pascal_number_format = QTextCharFormat()
            self._update_theme_formats()
            self.document().contentsChanged.connect(
                self._schedule_jump_target_refresh
            )
            self._refresh_jump_target_names()

        # -------------------------------------------------------------------
        # Im Dunkelmodus sind Mnemonics weiss und Kommentare grau. Im
        # Hellmodus bleiben die Mnemonics schwarz; ein dunkleres Grau
        # sorgt dort fuer ausreichend Kontrast auf hellem Hintergrund.
        # -------------------------------------------------------------------
        def _update_theme_formats(self) -> None:
            opcode_color = (
                QColor(255, 255, 255)
                if self.dark_mode
                else QColor(0, 0, 0)
            )
            comment_color = (
                QColor(170, 170, 170)
                if self.dark_mode
                else QColor(100, 100, 100)
            )
            jump_target_color = (
                QColor(102, 204, 255)
                if self.dark_mode
                else QColor(0, 82, 170)
            )
            self.opcode_format.setForeground(opcode_color)
            self.comment_format.setForeground(comment_color)
            self.jump_target_format.setForeground(jump_target_color)
            self.pascal_keyword_format.setForeground(
                QColor(110, 210, 255) if self.dark_mode else QColor(0, 60, 170)
            )
            self.pascal_string_format.setForeground(
                QColor(255, 190, 90) if self.dark_mode else QColor(150, 55, 0)
            )
            self.pascal_number_format.setForeground(
                QColor(255, 135, 255) if self.dark_mode else QColor(125, 0, 125)
            )

        def set_dark_mode(self, enabled: bool) -> None:
            enabled = bool(enabled)
            self.dark_mode = enabled
            self._update_theme_formats()
            # -------------------------------------------------------------------
            # Auch bei unveraendertem Modus neu hervorheben. Beim Einfuegen
            # eines Editors in eine neue Registerkarte kann Qt die Palette
            # des Dokuments noch einmal vom Eltern-Widget uebernehmen.
            # -------------------------------------------------------------------
            self.rehighlight()

        def set_enabled(self, enabled: bool) -> None:
            enabled = bool(enabled)
            if self.enabled == enabled:
                return
            self.enabled = enabled
            if enabled:
                self._refresh_jump_target_names()
            self.rehighlight()

        def set_pascal_enabled(self, enabled: bool) -> None:
            enabled = bool(enabled)
            if self.pascal_enabled == enabled:
                return
            self.pascal_enabled = enabled
            self.rehighlight()

        def set_c_enabled(self, enabled: bool) -> None:
            enabled = bool(enabled)
            if self.c_enabled == enabled:
                return
            self.c_enabled = enabled
            self.rehighlight()

        def _schedule_jump_target_refresh(self) -> None:
            if self._jump_target_refresh_pending:
                return
            self._jump_target_refresh_pending = True
            QTimer.singleShot(0, self._refresh_jump_target_names)

        def _refresh_jump_target_names(self) -> None:
            self._jump_target_refresh_pending = False
            names = set()
            for line in self.document().toPlainText().splitlines():
                code = line.split(";", 1)[0]
                match = self.LABEL_PATTERN.match(code)
                if match is not None:
                    names.add(match.group("label").casefold())

            if names != self._jump_target_names:
                self._jump_target_names = names
                if self.enabled:
                    self.rehighlight()

        # -------------------------------------------------------------------
        # Liefert das klickbare Sprungziel an einer Blockposition.
        # -------------------------------------------------------------------
        def jump_target_at(self, text: str, position: int):
            if not self.enabled:
                return None

            code = text.split(";", 1)[0]
            match = self.JUMP_TARGET_PATTERN.match(code)
            if match is None:
                return None

            target = match.group("target")
            if target.casefold() not in self._jump_target_names:
                return None

            start, end = match.span("target")
            # -------------------------------------------------------------------
            # cursorForPosition() kann je nach angeklickter Zeichenhaelfte die
            # Position vor oder hinter dem Zeichen liefern.
            # -------------------------------------------------------------------
            if start <= position < end or start < position <= end:
                return target
            return None

        # -----------------------------------------------------------------------
        # Sucht ein Label ohne Beachtung der Gross-/Kleinschreibung.
        # -----------------------------------------------------------------------
        def label_position(self, target: str):
            wanted = target.casefold()
            block = self.document().firstBlock()
            while block.isValid():
                code = block.text().split(";", 1)[0]
                match = self.LABEL_PATTERN.match(code)
                if (
                    match is not None
                    and match.group("label").casefold() == wanted
                ):
                    return block.position() + match.start("label")
                block = block.next()
            return None

        def highlightBlock(self, text: str) -> None:
            if self.c_enabled:
                for match in self.C_KEYWORD_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.pascal_keyword_format,
                    )
                for match in self.C_NUMBER_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.pascal_number_format,
                    )
                for match in self.C_STRING_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.pascal_string_format,
                    )
                for pattern in (
                    self.C_COMMENT_PATTERN,
                    self.C_PREPROCESSOR_PATTERN,
                ):
                    for match in pattern.finditer(text):
                        self.setFormat(
                            match.start(),
                            match.end() - match.start(),
                            self.comment_format,
                        )
                return
            if self.pascal_enabled:
                for match in self.PASCAL_KEYWORD_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.pascal_keyword_format,
                    )
                for match in self.PASCAL_NUMBER_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.pascal_number_format,
                    )
                for match in self.PASCAL_STRING_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.pascal_string_format,
                    )
                for match in self.PASCAL_COMMENT_PATTERN.finditer(text):
                    self.setFormat(
                        match.start(),
                        match.end() - match.start(),
                        self.comment_format,
                    )
                return
            if not self.enabled:
                return

            # ---------------------------------------------------------------
            # Zuerst die Mnemonics markieren. Die Kommentarformatierung folgt
            # zuletzt und ueberdeckt deshalb auch Befehlsnamen im Kommentar.
            # ---------------------------------------------------------------
            for match in self.OPCODE_PATTERN.finditer(text):
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    self.opcode_format,
                )

            code = text.split(";", 1)[0]
            jump_match = self.JUMP_TARGET_PATTERN.match(code)
            if (
                jump_match is not None
                and jump_match.group("target").casefold()
                in self._jump_target_names
            ):
                start, end = jump_match.span("target")
                target_format = QTextCharFormat(self.jump_target_format)
                target_format.setAnchor(True)
                target_format.setAnchorHref(
                    "label:" + jump_match.group("target")
                )
                self.setFormat(
                    start,
                    end - start,
                    target_format,
                )

            comment_start = text.find(";")
            if comment_start >= 0:
                self.setFormat(
                    comment_start,
                    len(text) - comment_start,
                    self.comment_format,
                )

    # -----------------------------------------------------------------------
    # Schmale Zeichenflaeche links neben einem Quelltexteditor.
    # -----------------------------------------------------------------------
    class LineNumberArea(QWidget):
        def __init__(self, editor: "SourceTextEdit"):
            super().__init__(editor)
            self.editor = editor
            self.setObjectName("line_number_area")
            self.setMouseTracking(True)
            self.setToolTip(
                "Linke Markerspalte: Breakpoint (hellrot)\n"
                "Rechte Markerspalte: Favorit/Bookmark (hellblau)\n"
                "Linksklick setzt, Rechtsklick löscht den Marker."
            )

        def sizeHint(self) -> QSize:
            return QSize(self.editor.line_number_area_width(), 0)

        def paintEvent(self, event) -> None:
            self.editor.line_number_area_paint_event(event)

        def mousePressEvent(self, event) -> None:
            if self.editor.handle_line_number_area_mouse_press(event):
                event.accept()
                return
            super().mousePressEvent(event)

    # -----------------------------------------------------------------------
    # Anzeige- und Einfuegedaten fuer einen 6502/6510-Befehl.
    # -----------------------------------------------------------------------
    @dataclass(frozen=True)
    class AssemblerCommandInfo:
        mnemonic: str
        operands: str
        default_operand: str
        description: str

    _OFFICIAL_ASSEMBLER_COMMANDS = (
        ("ADC", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Addiert den Operanden und das Carry-Flag zum Akkumulator."),
        ("AND", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Verknuepft den Akkumulator bitweise mit dem Operanden (UND)."),
        ("ASL", "A | $nn | $nn,X | $hhhh | $hhhh,X", "A", "Schiebt alle Bits um eine Stelle nach links; Bit 7 gelangt ins Carry-Flag."),
        ("BCC", "label", "label", "Verzweigt, wenn das Carry-Flag geloescht ist."),
        ("BCS", "label", "label", "Verzweigt, wenn das Carry-Flag gesetzt ist."),
        ("BEQ", "label", "label", "Verzweigt, wenn das Zero-Flag gesetzt ist."),
        ("BIT", "$nn | $hhhh", "$00", "Testet Bits des Operanden gegen den Akkumulator und aktualisiert Z, N und V."),
        ("BMI", "label", "label", "Verzweigt, wenn das Negative-Flag gesetzt ist."),
        ("BNE", "label", "label", "Verzweigt, wenn das Zero-Flag geloescht ist."),
        ("BPL", "label", "label", "Verzweigt, wenn das Negative-Flag geloescht ist."),
        ("BRK", "implizit", "", "Loest einen Software-Interrupt aus."),
        ("BVC", "label", "label", "Verzweigt, wenn das Overflow-Flag geloescht ist."),
        ("BVS", "label", "label", "Verzweigt, wenn das Overflow-Flag gesetzt ist."),
        ("CLC", "implizit", "", "Loescht das Carry-Flag."),
        ("CLD", "implizit", "", "Loescht den Dezimalmodus."),
        ("CLI", "implizit", "", "Erlaubt maskierbare Interrupts."),
        ("CLV", "implizit", "", "Loescht das Overflow-Flag."),
        ("CMP", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Vergleicht den Akkumulator mit dem Operanden."),
        ("CPX", "#$nn | $nn | $hhhh", "#$00", "Vergleicht das X-Register mit dem Operanden."),
        ("CPY", "#$nn | $nn | $hhhh", "#$00", "Vergleicht das Y-Register mit dem Operanden."),
        ("DEC", "$nn | $nn,X | $hhhh | $hhhh,X", "$00", "Verringert den Speicherwert um eins."),
        ("DEX", "implizit", "", "Verringert das X-Register um eins."),
        ("DEY", "implizit", "", "Verringert das Y-Register um eins."),
        ("EOR", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Verknuepft den Akkumulator exklusiv-oder mit dem Operanden."),
        ("INC", "$nn | $nn,X | $hhhh | $hhhh,X", "$00", "Erhoeht den Speicherwert um eins."),
        ("INX", "implizit", "", "Erhoeht das X-Register um eins."),
        ("INY", "implizit", "", "Erhoeht das Y-Register um eins."),
        ("JMP", "$hhhh | ($hhhh)", "$0000", "Setzt die Programmausfuehrung an der angegebenen Adresse fort."),
        ("JSR", "$hhhh", "$0000", "Ruft ein Unterprogramm auf und legt die Ruecksprungadresse auf dem Stack ab."),
        ("LDA", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Laedt einen Wert in den Akkumulator."),
        ("LDX", "#$nn | $nn | $nn,Y | $hhhh | $hhhh,Y", "#$00", "Laedt einen Wert in das X-Register."),
        ("LDY", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X", "#$00", "Laedt einen Wert in das Y-Register."),
        ("LSR", "A | $nn | $nn,X | $hhhh | $hhhh,X", "A", "Schiebt alle Bits um eine Stelle nach rechts; Bit 0 gelangt ins Carry-Flag."),
        ("NOP", "implizit", "", "Fuehrt keine Operation aus."),
        ("ORA", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Verknuepft den Akkumulator bitweise mit dem Operanden (ODER)."),
        ("PHA", "implizit", "", "Legt den Akkumulator auf dem Stack ab."),
        ("PHP", "implizit", "", "Legt das Prozessorstatusregister auf dem Stack ab."),
        ("PLA", "implizit", "", "Holt den Akkumulator vom Stack."),
        ("PLP", "implizit", "", "Holt das Prozessorstatusregister vom Stack."),
        ("ROL", "A | $nn | $nn,X | $hhhh | $hhhh,X", "A", "Rotiert die Bits ueber das Carry-Flag nach links."),
        ("ROR", "A | $nn | $nn,X | $hhhh | $hhhh,X", "A", "Rotiert die Bits ueber das Carry-Flag nach rechts."),
        ("RTI", "implizit", "", "Kehrt aus einer Interrupt-Routine zurueck."),
        ("RTS", "implizit", "", "Kehrt aus einem mit JSR aufgerufenen Unterprogramm zurueck."),
        ("SBC", "#$nn | $nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "#$00", "Subtrahiert den Operanden und das invertierte Carry vom Akkumulator."),
        ("SEC", "implizit", "", "Setzt das Carry-Flag."),
        ("SED", "implizit", "", "Aktiviert den Dezimalmodus."),
        ("SEI", "implizit", "", "Sperrt maskierbare Interrupts."),
        ("STA", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Speichert den Akkumulator im angegebenen Speicherziel."),
        ("STX", "$nn | $nn,Y | $hhhh", "$00", "Speichert das X-Register im angegebenen Speicherziel."),
        ("STY", "$nn | $nn,X | $hhhh", "$00", "Speichert das Y-Register im angegebenen Speicherziel."),
        ("TAX", "implizit", "", "Uebertraegt den Akkumulator in das X-Register."),
        ("TAY", "implizit", "", "Uebertraegt den Akkumulator in das Y-Register."),
        ("TSX", "implizit", "", "Uebertraegt den Stackpointer in das X-Register."),
        ("TXA", "implizit", "", "Uebertraegt das X-Register in den Akkumulator."),
        ("TXS", "implizit", "", "Uebertraegt das X-Register in den Stackpointer."),
        ("TYA", "implizit", "", "Uebertraegt das Y-Register in den Akkumulator."),
    )
    _UNDOCUMENTED_ASSEMBLER_COMMANDS = (
        ("AHX", "$hhhh,Y | ($nn),Y", "$0000,Y", "Undokumentierter 6502-Befehl: speichert A UND X unter Einbeziehung des Adress-Highbytes."),
        ("ANC", "#$nn", "#$00", "Undokumentierter 6502-Befehl: AND mit anschliessender Uebernahme von Bit 7 in Carry."),
        ("ARR", "#$nn", "#$00", "Undokumentierter 6502-Befehl: AND mit anschliessender Rotation nach rechts."),
        ("ASR", "#$nn", "#$00", "Undokumentierter 6502-Befehl: AND mit anschliessendem logischem Rechtsschieben."),
        ("DCP", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: DEC und anschliessend CMP."),
        ("ISC", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: INC und anschliessend SBC."),
        ("ISB", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Alternativer Name fuer den undokumentierten Befehl ISC."),
        ("JAM", "implizit", "", "Undokumentierter 6502-Befehl: haelt den Prozessor bis zum Reset an."),
        ("KIL", "implizit", "", "Alternativer Name fuer den undokumentierten Befehl JAM."),
        ("LAS", "$hhhh,Y", "$0000,Y", "Undokumentierter 6502-Befehl: laedt Speicher UND Stackpointer in A, X und Stackpointer."),
        ("LAX", "$nn | $nn,Y | $hhhh | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: laedt denselben Wert in A und X."),
        ("RLA", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: ROL und anschliessend AND."),
        ("RRA", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: ROR und anschliessend ADC."),
        ("SAX", "$nn | $nn,Y | $hhhh | ($nn,X)", "$00", "Undokumentierter 6502-Befehl: speichert A UND X."),
        ("SHX", "$hhhh,Y", "$0000,Y", "Undokumentierter 6502-Befehl: speichert X unter Einbeziehung des Adress-Highbytes."),
        ("SHY", "$hhhh,X", "$0000,X", "Undokumentierter 6502-Befehl: speichert Y unter Einbeziehung des Adress-Highbytes."),
        ("SLO", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: ASL und anschliessend ORA."),
        ("SRE", "$nn | $nn,X | $hhhh | $hhhh,X | $hhhh,Y | ($nn,X) | ($nn),Y", "$00", "Undokumentierter 6502-Befehl: LSR und anschliessend EOR."),
        ("TAS", "$hhhh,Y", "$0000,Y", "Undokumentierter 6502-Befehl: setzt den Stackpointer auf A UND X und speichert das Ergebnis."),
        ("XAA", "#$nn", "#$00", "Undokumentierter und auf realer Hardware instabiler 6502-Befehl."),
    )
    ASSEMBLER_COMMANDS = {
        mnemonic: AssemblerCommandInfo(
            mnemonic,
            operands,
            default_operand,
            description,
        )
        for mnemonic, operands, default_operand, description in (
            _OFFICIAL_ASSEMBLER_COMMANDS
            + _UNDOCUMENTED_ASSEMBLER_COMMANDS
        )
    }
    _M68K_ASSEMBLER_COMMANDS = (
        ("ADD", ".B/.W/.L source,Dn", "", "Addiert den Quelloperanden zum Datenregister."),
        ("ADDA", ".W/.L source,An", "", "Addiert den Quelloperanden zu einem Adressregister."),
        ("ADDI", ".B/.W/.L #wert,ziel", "", "Addiert eine unmittelbare Konstante."),
        ("ADDQ", ".B/.W/.L #1..8,ziel", "", "Addiert eine kleine unmittelbare Konstante."),
        ("AND", ".B/.W/.L source,Dn", "", "Verknüpft den Operanden bitweise mit UND."),
        ("ANDI", ".B/.W/.L #wert,ziel", "", "Verknüpft das Ziel mit einer unmittelbaren UND-Maske."),
        ("BRA", "label", "label", "Verzweigt unbedingt zu einer Marke."),
        ("BSR", "label", "label", "Ruft ein PC-relatives Unterprogramm auf."),
        ("BEQ", "label", "label", "Verzweigt bei Gleichheit beziehungsweise gesetztem Zero-Flag."),
        ("BNE", "label", "label", "Verzweigt bei Ungleichheit beziehungsweise gelöschtem Zero-Flag."),
        ("BGE", "label", "label", "Verzweigt bei vorzeichenbehaftet größer oder gleich."),
        ("BGT", "label", "label", "Verzweigt bei vorzeichenbehaftet größer."),
        ("BLE", "label", "label", "Verzweigt bei vorzeichenbehaftet kleiner oder gleich."),
        ("BLT", "label", "label", "Verzweigt bei vorzeichenbehaftet kleiner."),
        ("CLR", ".B/.W/.L ziel", "", "Löscht den Zieloperanden."),
        ("CMP", ".B/.W/.L source,Dn", "", "Vergleicht Quelle und Datenregister."),
        ("CMPI", ".B/.W/.L #wert,ziel", "", "Vergleicht eine Konstante mit dem Ziel."),
        ("DIVS", ".W source,Dn", "", "Vorzeichenbehaftete 32/16-Bit-Division."),
        ("DIVU", ".W source,Dn", "", "Vorzeichenlose 32/16-Bit-Division."),
        ("EOR", ".B/.W/.L Dn,ziel", "", "Verknüpft den Operanden exklusiv-oder."),
        ("EXT", ".W/.L Dn", "", "Erweitert das Vorzeichen im Datenregister."),
        ("JMP", "ziel", "label", "Springt zum Ziel; Marken werden PC-relativ codiert."),
        ("JSR", "ziel", "label", "Ruft ein Unterprogramm auf."),
        ("LEA", "adresse,An", "label(pc),a0", "Lädt eine effektive Adresse in ein Adressregister."),
        ("LSL", ".B/.W/.L #1..8,Dn", "", "Schiebt logisch nach links."),
        ("LSR", ".B/.W/.L #1..8,Dn", "", "Schiebt logisch nach rechts."),
        ("MOVE", ".B/.W/.L source,ziel", "", "Überträgt einen Wert zwischen Registern oder Speicher."),
        ("MOVEQ", "#-128..255,Dn", "#0,d0", "Lädt eine kurze Konstante in ein Datenregister."),
        ("MULS", ".W source,Dn", "", "Vorzeichenbehaftete 16-Bit-Multiplikation."),
        ("MULU", ".W source,Dn", "", "Vorzeichenlose 16-Bit-Multiplikation."),
        ("NEG", ".B/.W/.L ziel", "", "Bildet das Zweierkomplement."),
        ("NOP", "implizit", "", "Führt keine Operation aus."),
        ("OR", ".B/.W/.L source,Dn", "", "Verknüpft den Operanden bitweise mit ODER."),
        ("RTS", "implizit", "", "Kehrt aus einem Unterprogramm zurück."),
        ("SUB", ".B/.W/.L source,Dn", "", "Subtrahiert die Quelle vom Datenregister."),
        ("SUBA", ".W/.L source,An", "", "Subtrahiert die Quelle vom Adressregister."),
        ("SUBI", ".B/.W/.L #wert,ziel", "", "Subtrahiert eine unmittelbare Konstante."),
        ("SUBQ", ".B/.W/.L #1..8,ziel", "", "Subtrahiert eine kleine unmittelbare Konstante."),
        ("SWAP", "Dn", "d0", "Vertauscht die beiden 16-Bit-Hälften eines Datenregisters."),
        ("TST", ".B/.W/.L ziel", "", "Prüft einen Operanden und aktualisiert die Statusflags."),
        ("RESET", "implizit", "", "Setzt externe Geräte zurück; privilegiert."),
        ("RTE", "implizit", "", "Kehrt aus einer Exception zurück."),
        ("RTR", "implizit", "", "Stellt CCR und PC vom Stack wieder her."),
        ("TRAP", "#0..15", "#0", "Löst einen Software-Trap aus."),
        ("TRAPV", "implizit", "", "Trap bei gesetztem Overflow-Flag."),
        ("STOP", "#status", "#$2700", "Lädt SR und stoppt die CPU; privilegiert."),
        ("LINK", ".W/.L An,#offset", "a6,#-4", "Legt einen Stackframe an; .L ab mk68020."),
        ("UNLK", "An", "a6", "Löst einen mit LINK erzeugten Stackframe auf."),
        ("RTD", "#stackoffset", "#0", "Return and Deallocate; verfügbar ab mk68010."),
        ("BKPT", "#0..7", "#0", "Breakpoint-Vektor; verfügbar ab mk68010."),
        ("MOVEC", "Rc,Rn | Rn,Rc", "vbr,d0", "Control-Registerzugriff; Registerauswahl CPU-abhängig."),
        ("EXTB", ".L Dn", "d0", "Erweitert Byte direkt auf Long; verfügbar ab mk68020."),
        ("FMOVE", "FPm,FPn", "fp0,fp1", "Verschiebt Extended-Float zwischen 68881/68882-Registern."),
        ("FADD", "FPm,FPn", "fp0,fp1", "Addiert zwei 68881/68882-FP-Register."),
        ("FSUB", "FPm,FPn", "fp0,fp1", "Subtrahiert zwei 68881/68882-FP-Register."),
        ("FMUL", "FPm,FPn", "fp0,fp1", "Multipliziert zwei 68881/68882-FP-Register."),
        ("FDIV", "FPm,FPn", "fp0,fp1", "Dividiert zwei 68881/68882-FP-Register."),
        ("FCMP", "FPm,FPn", "fp0,fp1", "Vergleicht zwei 68881/68882-FP-Register."),
        ("FTST", "FPn", "fp0", "Testet ein 68881/68882-FP-Register."),
        ("FABS", "FPm,FPn", "fp0,fp1", "Betrag eines FP-Registers."),
        ("FNEG", "FPm,FPn", "fp0,fp1", "Negiert einen FP-Wert."),
        ("FSQRT", "FPm,FPn", "fp0,fp1", "Quadratwurzel in der FPU."),
        ("FINT", "FPm,FPn", "fp0,fp1", "Rundet auf Integerwert im FP-Register."),
        ("FINTRZ", "FPm,FPn", "fp0,fp1", "Rundet gegen Null im FP-Register."),
        ("FNOP", "implizit", "", "FPU-No-Operation für 68881/68882."),
    )
    M68K_ASSEMBLER_COMMANDS = {
        mnemonic: AssemblerCommandInfo(
            mnemonic,
            operands,
            default_operand,
            description,
        )
        for mnemonic, operands, default_operand, description
        in _M68K_ASSEMBLER_COMMANDS
    }

    AMIGA_COMMAND_REQUIREMENTS = {
        "RTD": ("mk68010", False),
        "BKPT": ("mk68010", False),
        "MOVEC": ("mk68010", False),
        "EXTB": ("mk68020", False),
        "FMOVE": ("mk68000", True), "FADD": ("mk68000", True),
        "FSUB": ("mk68000", True), "FMUL": ("mk68000", True),
        "FDIV": ("mk68000", True), "FCMP": ("mk68000", True),
        "FTST": ("mk68000", True), "FABS": ("mk68000", True),
        "FNEG": ("mk68000", True), "FSQRT": ("mk68000", True),
        "FINT": ("mk68000", True), "FINTRZ": ("mk68000", True),
        "FNOP": ("mk68000", True),
    }

    _PE32_ASSEMBLER_COMMANDS = (
        ("MOV", "r32,r32|imm32|symbol", "eax,0", "Überträgt 32-Bit-Werte oder Symboladressen."),
        ("PUSH", "r32|imm32|symbol", "eax", "Legt einen 32-Bit-Wert auf dem IA-32-Stack ab."),
        ("POP", "r32", "eax", "Holt einen 32-Bit-Wert vom IA-32-Stack."),
        ("CALL", "label", "label", "Ruft ein relatives Unterprogramm auf; COFF32 erzeugt REL32-Relocations."),
        ("JMP", "label", "label", "Springt relativ zu einem Label."),
        ("JE", "label", "label", "Springt bei Gleichheit."),
        ("JNE", "label", "label", "Springt bei Ungleichheit."),
        ("JL", "label", "label", "Vorzeichenbehafteter kleiner-Sprung."),
        ("JLE", "label", "label", "Vorzeichenbehafteter kleiner-gleich-Sprung."),
        ("JG", "label", "label", "Vorzeichenbehafteter größer-Sprung."),
        ("JGE", "label", "label", "Vorzeichenbehafteter größer-gleich-Sprung."),
        ("ADD", "r32,r32|imm32", "eax,1", "Addiert einen 32-Bit-Operanden."),
        ("SUB", "r32,r32|imm32", "eax,1", "Subtrahiert einen 32-Bit-Operanden."),
        ("CMP", "r32,r32|imm32", "eax,0", "Vergleicht 32-Bit-Werte."),
        ("XOR", "r32,r32", "eax,eax", "Bitweises exklusives ODER."),
        ("AND", "r32,r32", "eax,eax", "Bitweises UND."),
        ("OR", "r32,r32", "eax,eax", "Bitweises ODER."),
        ("TEST", "r32,r32", "eax,eax", "Bitweiser Test ohne Ergebnisspeicherung."),
        ("IMUL", "r32,r32", "eax,ecx", "Vorzeichenbehaftete Multiplikation."),
        ("SHL", "r32,imm8", "eax,1", "Logisches Schieben nach links."),
        ("SHR", "r32,imm8", "eax,1", "Logisches Schieben nach rechts."),
        ("SAR", "r32,imm8", "eax,1", "Arithmetisches Schieben nach rechts."),
        ("INC", "r32", "eax", "Erhöht ein Register um eins."),
        ("DEC", "r32", "eax", "Verringert ein Register um eins."),
        ("RET", "implizit", "", "Kehrt aus einem IA-32-Unterprogramm zurück."),
        ("LEAVE", "implizit", "", "Beendet einen EBP-basierten Stackframe."),
        ("NOP", "implizit", "", "Keine Operation."),
        ("INT", "imm8", "3", "Löst einen Software-Interrupt aus."),
    )
    PE32_ASSEMBLER_COMMANDS = {
        mnemonic: AssemblerCommandInfo(mnemonic, operands, default_operand, description)
        for mnemonic, operands, default_operand, description
        in _PE32_ASSEMBLER_COMMANDS
    }

    @dataclass(frozen=True)
    # -----------------------------------------------------------------------
    # Positionen des per Kontextmenue angeklickten ASM-Operanden.
    # -----------------------------------------------------------------------
    class AssemblerOperandContext:
        insert_position: int
        replace_start: int
        replace_end: int
        original_value: str

    # -----------------------------------------------------------------------
    # Button-Rechner und Basisumrechner fuer ASM-Operanden.
    # -----------------------------------------------------------------------
    class NumberCalculatorDialog(QDialog):
        _memory_value: Optional[Fraction] = None

        PRIORITY_ITEMS = (
            ("Dezimal", "decimal"),
            ("Hexadezimal", "hex"),
            ("Binär", "binary"),
        )
        OPERATORS = ("+", "-", "*", "/")
        OPERATOR_LABELS = {
            "+": "+",
            "-": "−",
            "*": "×",
            "/": "÷",
        }
        PRECEDENCE = {
            "+": 1,
            "-": 1,
            "*": 2,
            "/": 2,
        }

        def __init__(
            self,
            editor: "SourceTextEdit",
            context: AssemblerOperandContext,
        ):
            super().__init__(editor)
            self.editor = editor
            self.context = context
            self._result: Optional[Fraction] = None
            self._tokens = []
            self._just_evaluated = False
            self._digit_buttons = {}

            self.setObjectName("assembler_number_calculator")
            self.setWindowTitle("Rechner für Assembler-Operand")
            self.setWindowModality(Qt.WindowModal)
            self.setMinimumWidth(620)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 12, 12, 12)
            layout.setSpacing(9)

            hint = QLabel(
                "Die Eingabe erfolgt über die Zahlentasten. "
                "Multiplikation und Division werden vor Addition und "
                "Subtraktion ausgewertet.",
                self,
            )
            hint.setWordWrap(True)
            layout.addWidget(hint)

            priority_layout = QHBoxLayout()
            priority_layout.addWidget(QLabel("Priorität der Umrechnung", self))
            self.priority_combo = self._make_combo(self.PRIORITY_ITEMS)
            self.priority_combo.setObjectName("calculator_priority")
            priority_layout.addWidget(self.priority_combo, 1)
            layout.addLayout(priority_layout)

            self.expression_display = QLineEdit(self)
            self.expression_display.setObjectName("calculator_expression")
            self.expression_display.setReadOnly(True)
            self.expression_display.setAlignment(Qt.AlignRight)
            expression_font = QFont(self.expression_display.font())
            expression_font.setPointSize(
                max(12, expression_font.pointSize() + 3)
            )
            expression_font.setBold(True)
            self.expression_display.setFont(expression_font)
            layout.addWidget(self.expression_display)

            keypad = QGridLayout()
            keypad.setHorizontalSpacing(6)
            keypad.setVerticalSpacing(6)
            for digit, row, column in (
                ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
                ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
                ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
                ("0", 3, 0),
                ("A", 0, 4), ("B", 0, 5),
                ("C", 1, 4), ("D", 1, 5),
                ("E", 2, 4), ("F", 2, 5),
            ):
                button = QPushButton(digit, self)
                button.setObjectName(f"calculator_digit_{digit}")
                button.setMinimumHeight(36)
                button.clicked.connect(
                    lambda checked=False, value=digit:
                    self._append_digit(value)
                )
                if digit == "0":
                    keypad.addWidget(button, row, column, 1, 3)
                else:
                    keypad.addWidget(button, row, column)
                self._digit_buttons[digit] = button

            for operator_name, row in (
                ("/", 0),
                ("*", 1),
                ("-", 2),
                ("+", 3),
            ):
                button = QPushButton(
                    self.OPERATOR_LABELS[operator_name],
                    self,
                )
                button.setObjectName(
                    "calculator_operator_" + {
                        "/": "divide",
                        "*": "multiply",
                        "-": "subtract",
                        "+": "add",
                    }[operator_name]
                )
                button.setMinimumHeight(36)
                button.clicked.connect(
                    lambda checked=False, value=operator_name:
                    self._append_operator(value)
                )
                keypad.addWidget(button, row, 3)

            self.backspace_button = QPushButton("←", self)
            self.backspace_button.setObjectName("calculator_backspace")
            self.backspace_button.setToolTip("Letzte Eingabe löschen")
            self.backspace_button.clicked.connect(self._backspace)
            keypad.addWidget(self.backspace_button, 3, 4)

            self.clear_button = QPushButton("Löschen", self)
            self.clear_button.setObjectName("calculator_clear")
            self.clear_button.setToolTip("Ausdruck und Ergebnis löschen")
            self.clear_button.clicked.connect(self._clear)
            keypad.addWidget(self.clear_button, 3, 5)

            self.equals_button = QPushButton("=", self)
            self.equals_button.setObjectName("calculator_equals")
            self.equals_button.setMinimumHeight(38)
            self.equals_button.setDefault(True)
            self.equals_button.clicked.connect(self._calculate_clicked)
            keypad.addWidget(self.equals_button, 4, 0, 1, 6)
            layout.addLayout(keypad)

            result_layout = QGridLayout()
            result_layout.setHorizontalSpacing(8)
            result_layout.setVerticalSpacing(6)
            self.result_copy_buttons = {}
            self.result_insert_buttons = {}
            self.decimal_result = self._add_result_row(
                result_layout,
                0,
                "Dezimal",
                "decimal",
            )
            self.hex_result = self._add_result_row(
                result_layout,
                1,
                "Hexadezimal",
                "hex",
            )
            self.binary_result = self._add_result_row(
                result_layout,
                2,
                "Binär",
                "binary",
            )
            layout.addLayout(result_layout)

            memory_layout = QHBoxLayout()
            self.memory_label = QLabel(self)
            self.memory_label.setObjectName("calculator_memory_label")
            memory_layout.addWidget(self.memory_label, 1)
            self.store_button = QPushButton("Speichern", self)
            self.recall_button = QPushButton("Abrufen", self)
            memory_layout.addWidget(self.store_button)
            memory_layout.addWidget(self.recall_button)
            layout.addLayout(memory_layout)

            self.error_label = QLabel(self)
            self.error_label.setObjectName("calculator_error")
            self.error_label.setWordWrap(True)
            self.error_label.setStyleSheet("color: #c02020; font-weight: bold;")
            layout.addWidget(self.error_label)

            button_layout = QHBoxLayout()
            self.calculate_button = QPushButton("Berechnen", self)
            self.change_button = QPushButton("Ändern", self)
            self.close_button = QPushButton("Schließen", self)
            button_layout.addWidget(self.calculate_button)
            button_layout.addStretch(1)
            button_layout.addWidget(self.change_button)
            button_layout.addWidget(self.close_button)
            layout.addLayout(button_layout)

            self.priority_combo.currentIndexChanged.connect(
                self._priority_changed
            )
            self.calculate_button.clicked.connect(self._calculate_clicked)
            self.change_button.clicked.connect(
                lambda checked=False: self._write_to_editor(replace=True)
            )
            self.store_button.clicked.connect(self._store_result)
            self.recall_button.clicked.connect(self._recall_result)
            self.close_button.clicked.connect(self.reject)

            original = context.original_value.strip()
            if original:
                self._select_detected_base(self.priority_combo, original)
                self._tokens = [self._strip_number_prefix(original)]
            else:
                self._tokens = ["0"]

            self._refresh_expression_display()
            self._update_digit_buttons()
            self._refresh_memory_label()
            self._update_result(silent=True)

        def _make_combo(self, items) -> QComboBox:
            combo = QComboBox(self)
            for label, item_data in items:
                combo.addItem(label, item_data)
            return combo

        def _add_result_row(
            self,
            layout: QGridLayout,
            row: int,
            label: str,
            base_name: str,
        ) -> QLineEdit:
            layout.addWidget(QLabel(label, self), row, 0)
            result = QLineEdit(self)
            result.setReadOnly(True)
            result.setObjectName("calculator_result")
            result.setAlignment(Qt.AlignRight)
            layout.addWidget(result, row, 1)

            copy_button = QPushButton("Kopieren", self)
            copy_button.setObjectName(
                f"calculator_copy_{base_name}"
            )
            copy_button.clicked.connect(
                lambda checked=False, selected_base=base_name:
                self._copy_result(selected_base)
            )
            layout.addWidget(copy_button, row, 2)

            insert_button = QPushButton("Einfügen", self)
            insert_button.setObjectName(
                f"calculator_insert_{base_name}"
            )
            insert_button.clicked.connect(
                lambda checked=False, selected_base=base_name:
                self._write_to_editor(
                    replace=False,
                    base_name=selected_base,
                )
            )
            layout.addWidget(insert_button, row, 3)

            self.result_copy_buttons[base_name] = copy_button
            self.result_insert_buttons[base_name] = insert_button
            return result

        @staticmethod
        def _select_detected_base(combo: QComboBox, text: str) -> None:
            value = text.strip().lstrip("#").lstrip("+-")
            if value.startswith("$") or value.lower().startswith("0x"):
                combo.setCurrentIndex(combo.findData("hex"))
            elif value.startswith("%") or value.lower().startswith("0b"):
                combo.setCurrentIndex(combo.findData("binary"))
            else:
                combo.setCurrentIndex(combo.findData("decimal"))

        @staticmethod
        def _strip_number_prefix(text: str) -> str:
            value = text.strip()
            if value.startswith("#"):
                value = value[1:].strip()
            sign = ""
            if value.startswith(("+", "-")):
                sign, value = value[0], value[1:]
            if value.startswith("$") or value.startswith("%"):
                value = value[1:]
            elif value.lower().startswith(("0x", "0b")):
                value = value[2:]
            return sign + value.upper()

        @staticmethod
        def _parse_integer(text: str, base_name: str) -> int:
            value = text.strip().replace("_", "")
            if value.startswith("#"):
                value = value[1:].strip()
            if not value:
                raise ValueError("Bitte einen Zahlenwert eingeben.")

            sign = 1
            if value[0] in "+-":
                if value[0] == "-":
                    sign = -1
                value = value[1:]
            if not value:
                raise ValueError("Der Zahlenwert ist unvollständig.")

            if base_name == "hex":
                if value.startswith("$"):
                    value = value[1:]
                elif value.lower().startswith("0x"):
                    value = value[2:]
                if value.lower().endswith("h"):
                    value = value[:-1]
                digits = r"[0-9A-Fa-f]+"
                radix = 16
                base_label = "Hexadezimalzahl"
            elif base_name == "binary":
                if value.startswith("%"):
                    value = value[1:]
                elif value.lower().startswith("0b"):
                    value = value[2:]
                digits = r"[01]+"
                radix = 2
                base_label = "Binärzahl"
            else:
                digits = r"[0-9]+"
                radix = 10
                base_label = "Dezimalzahl"

            if re.fullmatch(digits, value or "") is None:
                raise ValueError(f"Ungültige {base_label}: {text}")
            return sign * int(value, radix)

        @staticmethod
        def _decimal_text(value: Fraction) -> str:
            if value.denominator == 1:
                return str(value.numerator)
            with localcontext() as context:
                context.prec = 32
                decimal_value = (
                    Decimal(value.numerator) / Decimal(value.denominator)
                )
            text = format(decimal_value, "f")
            if "." in text:
                text = text.rstrip("0").rstrip(".")
            return text

        @staticmethod
        def _integer_text(
            value: Fraction,
            base_name: str,
            *,
            original: str = "",
            preserve_width: bool = False,
        ) -> Optional[str]:
            if value.denominator != 1:
                return None
            integer = value.numerator
            sign = "-" if integer < 0 else ""
            magnitude = abs(integer)

            original_body = original.strip().lstrip("#").lstrip("+-")
            if base_name == "hex":
                digits = format(magnitude, "X")
                prefix = "$"
                width = 0
                if preserve_width:
                    if original_body.startswith("$"):
                        width = len(original_body) - 1
                    elif original_body.lower().startswith("0x"):
                        width = len(original_body) - 2
                        prefix = original_body[:2]
                if width:
                    digits = digits.rjust(width, "0")
                return sign + prefix + digits

            if base_name == "binary":
                digits = format(magnitude, "b")
                prefix = "%"
                width = 0
                if preserve_width:
                    if original_body.startswith("%"):
                        width = len(original_body) - 1
                    elif original_body.lower().startswith("0b"):
                        width = len(original_body) - 2
                        prefix = original_body[:2]
                if width:
                    digits = digits.rjust(width, "0")
                return sign + prefix + digits

            return str(integer)

        def _priority_base(self) -> str:
            return str(self.priority_combo.currentData())

        @classmethod
        def _is_operator(cls, token) -> bool:
            return isinstance(token, str) and token in cls.OPERATORS

        def _token_display(self, token) -> str:
            if self._is_operator(token):
                return self.OPERATOR_LABELS[token]
            if isinstance(token, Fraction):
                if token.denominator != 1:
                    return self._decimal_text(token)
                text = self._integer_text(token, self._priority_base())
                if text is None:
                    return self._decimal_text(token)
                return self._strip_number_prefix(text)
            return str(token)

        def _refresh_expression_display(self) -> None:
            self.expression_display.setText(
                " ".join(self._token_display(token) for token in self._tokens)
            )

        def _digit_allowed(self, digit: str) -> bool:
            base_name = self._priority_base()
            if base_name == "binary":
                return digit in "01"
            if base_name == "decimal":
                return digit in "0123456789"
            return digit in "0123456789ABCDEF"

        def _update_digit_buttons(self) -> None:
            for digit, button in self._digit_buttons.items():
                button.setEnabled(self._digit_allowed(digit))

        def _append_digit(self, digit: str) -> None:
            digit = digit.upper()
            if not self._digit_allowed(digit):
                self.error_label.setText(
                    f"{digit} ist in dieser Zahlenbasis nicht zulässig."
                )
                return

            if self._just_evaluated:
                self._tokens = []
                self._just_evaluated = False

            if not self._tokens or self._is_operator(self._tokens[-1]):
                self._tokens.append(digit)
            elif isinstance(self._tokens[-1], Fraction):
                self._tokens = [digit]
            else:
                current = str(self._tokens[-1])
                if current == "0":
                    current = ""
                self._tokens[-1] = current + digit

            self._refresh_expression_display()
            self._update_result(silent=True)

        def _append_operator(self, operator_name: str) -> None:
            if operator_name not in self.OPERATORS:
                return
            if not self._tokens:
                self.error_label.setText("Zuerst einen Zahlenwert eingeben.")
                return

            if self._just_evaluated and self._result is not None:
                self._tokens = [self._result]
                self._just_evaluated = False

            if self._is_operator(self._tokens[-1]):
                self._tokens[-1] = operator_name
            else:
                self._tokens.append(operator_name)
            self.error_label.clear()
            self._refresh_expression_display()
            self._set_action_state()

        def _backspace(self, *_args) -> None:
            if not self._tokens:
                return
            self._just_evaluated = False
            last = self._tokens[-1]
            if self._is_operator(last) or isinstance(last, Fraction):
                self._tokens.pop()
            else:
                shortened = str(last)[:-1]
                if shortened and shortened not in ("+", "-"):
                    self._tokens[-1] = shortened
                else:
                    self._tokens.pop()
            if not self._tokens:
                self._tokens = ["0"]
            self._refresh_expression_display()
            self._update_result(silent=True)

        def _clear(self, *_args) -> None:
            self._tokens = ["0"]
            self._result = Fraction(0, 1)
            self._just_evaluated = False
            self.error_label.clear()
            self._refresh_expression_display()
            self._show_result()

        def _infix_to_rpn(self):
            if not self._tokens or self._is_operator(self._tokens[-1]):
                raise ValueError("Der Rechenausdruck ist unvollständig.")

            output = []
            operators = []
            expect_number = True
            base_name = self._priority_base()
            for token in self._tokens:
                if expect_number:
                    if self._is_operator(token):
                        raise ValueError("Zwei Operatoren folgen aufeinander.")
                    if isinstance(token, Fraction):
                        output.append(token)
                    else:
                        output.append(
                            Fraction(
                                self._parse_integer(str(token), base_name),
                                1,
                            )
                        )
                    expect_number = False
                    continue

                if not self._is_operator(token):
                    raise ValueError("Zwischen zwei Werten fehlt ein Operator.")
                while (
                    operators
                    and self.PRECEDENCE[operators[-1]]
                    >= self.PRECEDENCE[token]
                ):
                    output.append(operators.pop())
                operators.append(token)
                expect_number = True

            if expect_number:
                raise ValueError("Der Rechenausdruck ist unvollständig.")
            while operators:
                output.append(operators.pop())
            return output

        @classmethod
        def _evaluate_rpn(cls, rpn_tokens) -> Fraction:
            stack = []
            for token in rpn_tokens:
                if not cls._is_operator(token):
                    stack.append(Fraction(token))
                    continue
                if len(stack) < 2:
                    raise ValueError("Der Rechenausdruck ist unvollständig.")
                right = stack.pop()
                left = stack.pop()
                if token == "+":
                    stack.append(left + right)
                elif token == "-":
                    stack.append(left - right)
                elif token == "*":
                    stack.append(left * right)
                else:
                    if right == 0:
                        raise ValueError("Division durch 0 ist nicht zulässig.")
                    stack.append(left / right)
            if len(stack) != 1:
                raise ValueError("Der Rechenausdruck ist ungültig.")
            return stack[0]

        def _calculate(self) -> Fraction:
            return self._evaluate_rpn(self._infix_to_rpn())

        def _set_action_state(self) -> None:
            valid = self._result is not None
            for base_name, button in self.result_copy_buttons.items():
                available = self._result_text(base_name) is not None
                button.setEnabled(valid and available)
            for base_name, button in self.result_insert_buttons.items():
                available = self._result_text(base_name) is not None
                button.setEnabled(
                    valid and available and not self.editor.isReadOnly()
                )
            selected_available = self._selected_result_text() is not None
            self.change_button.setEnabled(
                valid and selected_available and not self.editor.isReadOnly()
            )
            self.store_button.setEnabled(valid)
            self.recall_button.setEnabled(self._memory_value is not None)

        def _show_result(self) -> None:
            if self._result is None:
                self.decimal_result.clear()
                self.hex_result.clear()
                self.binary_result.clear()
                self._set_action_state()
                return
            self.decimal_result.setText(self._decimal_text(self._result))
            hex_text = self._integer_text(self._result, "hex")
            binary_text = self._integer_text(self._result, "binary")
            self.hex_result.setText(
                hex_text if hex_text is not None else "nicht ganzzahlig"
            )
            self.binary_result.setText(
                binary_text if binary_text is not None else "nicht ganzzahlig"
            )
            self._set_action_state()

        def _update_result(self, *, silent: bool) -> bool:
            try:
                self._result = self._calculate()
            except ValueError as exc:
                self._result = None
                self._show_result()
                self.error_label.setText("" if silent else str(exc))
                return False
            self.error_label.clear()
            self._show_result()
            return True

        def _priority_changed(self, *_args) -> None:
            self._update_digit_buttons()
            self._refresh_expression_display()
            self._update_result(silent=True)

        def _calculate_clicked(self, *_args) -> None:
            if self._update_result(silent=False):
                self._just_evaluated = True

        def _selected_result_text(
            self,
            *,
            for_editor: bool = False,
        ) -> Optional[str]:
            return self._result_text(
                self._priority_base(),
                for_editor=for_editor,
            )

        def _result_text(
            self,
            base_name: str,
            *,
            for_editor: bool = False,
        ) -> Optional[str]:
            if self._result is None:
                return None
            if base_name == "decimal":
                return self._decimal_text(self._result)
            return self._integer_text(
                self._result,
                base_name,
                original=(
                    self.context.original_value if for_editor else ""
                ),
                preserve_width=for_editor,
            )

        def _copy_result(
            self,
            base_name: Optional[str] = None,
            *_args,
        ) -> None:
            selected_base = base_name or self._priority_base()
            text = self._result_text(selected_base)
            if text is None:
                self.error_label.setText(
                    "Hexadezimal und Binär benötigen ein ganzzahliges Ergebnis."
                )
                return
            QApplication.clipboard().setText(text)
            self.error_label.setText(f"Ergebnis kopiert: {text}")

        def _write_to_editor(
            self,
            *,
            replace: bool,
            base_name: Optional[str] = None,
        ) -> None:
            selected_base = base_name or self._priority_base()
            text = self._result_text(
                selected_base,
                for_editor=replace,
            )
            if text is None:
                self.error_label.setText(
                    "Dieses Ausgabeformat benötigt ein ganzzahliges Ergebnis."
                )
                return

            cursor = QTextCursor(self.editor.document())
            if replace:
                cursor.setPosition(self.context.replace_start)
                cursor.setPosition(
                    self.context.replace_end,
                    QTextCursor.KeepAnchor,
                )
            else:
                cursor.setPosition(self.context.insert_position)

            cursor.beginEditBlock()
            cursor.insertText(text)
            cursor.endEditBlock()
            self.editor.setTextCursor(cursor)
            self.editor.ensureCursorVisible()
            self.editor.setFocus(Qt.OtherFocusReason)
            self.accept()

        def _store_result(self, *_args) -> None:
            if self._result is None and not self._update_result(silent=False):
                return
            type(self)._memory_value = self._result
            self._refresh_memory_label()
            self._set_action_state()

        def _recall_result(self, *_args) -> None:
            if self._memory_value is None:
                return
            self._tokens = [self._memory_value]
            self._result = self._memory_value
            self._just_evaluated = True
            self.error_label.clear()
            self._refresh_expression_display()
            self._show_result()

        def _refresh_memory_label(self) -> None:
            if self._memory_value is None:
                self.memory_label.setText("Speicher: leer")
            else:
                self.memory_label.setText(
                    "Speicher: " + self._decimal_text(self._memory_value)
                )

        def keyPressEvent(self, event) -> None:
            text = event.text().upper()
            if text in "0123456789ABCDEF":
                self._append_digit(text)
                event.accept()
                return
            if text in self.OPERATORS:
                self._append_operator(text)
                event.accept()
                return
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._calculate_clicked()
                event.accept()
                return
            if event.key() == Qt.Key_Backspace:
                self._backspace()
                event.accept()
                return
            if event.key() == Qt.Key_Delete:
                self._clear()
                event.accept()
                return
            super().keyPressEvent(event)

    # ---------------------------------------------------------------------------
    # Quelltexteditor mit Gutter und intelligenter Assemblerhilfe.
    # ---------------------------------------------------------------------------
    class SourceTextEdit(QPlainTextEdit):
        assembler_help_requested = pyqtSignal(str, str)
        context_help_requested = pyqtSignal(str)
        breakpoints_changed = pyqtSignal()
        bookmarks_changed = pyqtSignal()

        GUTTER_MARKER_COLUMN_WIDTH = 13
        GUTTER_MARKER_COLUMNS = 2

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self._dark_mode = False
            self._completion_enabled = False
            self._completion_context = None
            self._assembler_target = "c64"
            self._amiga_cpu_model = "mk68000"
            self._amiga_fpu_model = "FPU: None"
            self._assembler_navigation_enabled = False
            self._assembler_highlighter = None
            self._breakpoint_cursors = []
            self._bookmark_cursors = []
            self.line_number_area = LineNumberArea(self)
            self.viewport().setMouseTracking(True)

            self.completion_ghost = QLabel(self.viewport())
            self.completion_ghost.setObjectName("assembler_completion_ghost")
            self.completion_ghost.setAttribute(
                Qt.WA_TransparentForMouseEvents,
                True,
            )
            self.completion_ghost.hide()

            self.completion_frame = QFrame(self.viewport())
            self.completion_frame.setObjectName("assembler_completion_frame")
            self.completion_frame.setFrameShape(QFrame.StyledPanel)
            self.completion_frame.setAttribute(
                Qt.WA_TransparentForMouseEvents,
                True,
            )
            completion_layout = QVBoxLayout(self.completion_frame)
            completion_layout.setContentsMargins(9, 7, 9, 8)
            completion_layout.setSpacing(0)

            self.completion_header = QLabel(self.completion_frame)
            self.completion_header.setObjectName("assembler_completion_header")
            self.completion_header.setTextFormat(Qt.PlainText)
            self.completion_header.setWordWrap(False)
            completion_layout.addWidget(self.completion_header)
            completion_layout.addSpacing(self.fontMetrics().height())

            self.completion_description = QLabel(self.completion_frame)
            self.completion_description.setObjectName(
                "assembler_completion_description"
            )
            self.completion_description.setTextFormat(Qt.PlainText)
            self.completion_description.setWordWrap(True)
            completion_layout.addWidget(self.completion_description)
            self.completion_frame.hide()

            self.blockCountChanged.connect(
                self.update_line_number_area_width
            )
            self.updateRequest.connect(self.update_line_number_area)
            self.textChanged.connect(self._schedule_completion_update)
            self.textChanged.connect(self._gutter_document_changed)
            self.cursorPositionChanged.connect(
                self._schedule_completion_update
            )
            self.cursorPositionChanged.connect(
                self._update_current_line_highlight
            )
            self.update_line_number_area_width(0)
            self._update_completion_theme()
            self._update_current_line_highlight()

        # -----------------------------------------------------------------------
        # Hebt die aktuelle Cursorzeile theme-abhaengig hervor.
        # -----------------------------------------------------------------------
        def _update_current_line_highlight(self) -> None:
            selection = QTextEdit.ExtraSelection()
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selection.format.setProperty(
                QTextFormat.FullWidthSelection,
                True,
            )

            if self._dark_mode:
                selection.format.setBackground(QColor("#182898"))
                selection.format.setForeground(QColor("#FFFFFF"))
            else:
                selection.format.setBackground(QColor("#FFF4B8"))
                selection.format.setForeground(QColor("#000000"))

            self.setExtraSelections([selection])

        def set_assembler_completion_enabled(self, enabled: bool) -> None:
            self._completion_enabled = bool(enabled) and not self.isReadOnly()
            if self._completion_enabled:
                self._schedule_completion_update()
            else:
                self._hide_completion()

        def set_assembler_target(self, target: str) -> None:
            normalized = str(target).strip().casefold()
            if normalized in {"pe32", "windows", "windows pe32"}:
                self._assembler_target = "pe32"
            elif normalized == "amiga":
                self._assembler_target = "amiga"
            else:
                self._assembler_target = "c64"
            self._hide_completion()
            if self._completion_enabled:
                self._schedule_completion_update()

        def set_amiga_profile(self, cpu_model: str, fpu_model: str) -> None:
            self._amiga_cpu_model = normalize_amiga_cpu_model(cpu_model)
            self._amiga_fpu_model = normalize_amiga_fpu_model(fpu_model)
            self._hide_completion()
            if self._completion_enabled:
                self._schedule_completion_update()

        def _assembler_commands(self):
            if self._assembler_target == "pe32":
                return PE32_ASSEMBLER_COMMANDS
            if self._assembler_target == "amiga":
                filtered = {}
                for mnemonic, info in M68K_ASSEMBLER_COMMANDS.items():
                    minimum_cpu, needs_fpu = AMIGA_COMMAND_REQUIREMENTS.get(
                        mnemonic, ("mk68000", False)
                    )
                    if not amiga_cpu_at_least(self._amiga_cpu_model, minimum_cpu):
                        continue
                    if needs_fpu and self._amiga_fpu_model == "FPU: None":
                        continue
                    filtered[mnemonic] = info
                return filtered
            return ASSEMBLER_COMMANDS

        def set_assembler_navigation_highlighter(self, highlighter) -> None:
            self._assembler_highlighter = highlighter

        def set_assembler_navigation_enabled(self, enabled: bool) -> None:
            self._assembler_navigation_enabled = bool(enabled)
            if not self._assembler_navigation_enabled:
                self.viewport().setCursor(Qt.IBeamCursor)

        def _jump_target_at_point(self, point):
            if (
                not self._assembler_navigation_enabled
                or self._assembler_highlighter is None
            ):
                return None
            cursor = self.cursorForPosition(point)
            return self._assembler_highlighter.jump_target_at(
                cursor.block().text(),
                cursor.positionInBlock(),
            )

        def _jump_to_label(self, target: str) -> bool:
            if self._assembler_highlighter is None:
                return False
            position = self._assembler_highlighter.label_position(target)
            if position is None:
                return False

            self._hide_completion()
            cursor = QTextCursor(self.document())
            cursor.setPosition(position)
            self.setTextCursor(cursor)
            self.centerCursor()
            self.setFocus(Qt.MouseFocusReason)
            self.viewport().setCursor(Qt.IBeamCursor)
            return True

        def _assembler_operand_context_at_point(self, point):
            """Ermittelt den editierbaren Hauptwert rechts vom Mnemonic."""
            if (
                not self._assembler_navigation_enabled
                or self.isReadOnly()
            ):
                return None

            cursor = self.cursorForPosition(point)
            block = cursor.block()
            block_text = block.text()
            position = cursor.positionInBlock()
            code = block_text.split(";", 1)[0]
            match = re.match(
                r"^\s*(?:[A-Za-z_.$][A-Za-z0-9_.$]*\s*:\s*)?"
                r"(?P<opcode>[A-Za-z]{2,8})(?:\.[BbWwLl])?"
                r"(?P<spacing>\s+)"
                r"(?P<operand>.*?)\s*$",
                code,
            )
            if (
                match is None
                or match.group("opcode").upper() not in self._assembler_commands()
            ):
                return None

            operand_start, operand_end = match.span("operand")
            while (
                operand_start < operand_end
                and code[operand_start].isspace()
            ):
                operand_start += 1
            while (
                operand_end > operand_start
                and code[operand_end - 1].isspace()
            ):
                operand_end -= 1
            if operand_start >= operand_end:
                return None

            # cursorForPosition() kann die Position direkt hinter dem
            # angeklickten Zeichen liefern; deshalb wird auch das rechte Ende
            # des Operanden als Treffer akzeptiert.
            if not (
                operand_start <= position < operand_end
                or operand_start < position <= operand_end
            ):
                return None

            operand = code[operand_start:operand_end]
            primary = re.match(
                r"\s*[#(]*\s*(?P<value>"
                r"[+-]?(?:\$[0-9A-Fa-f]+|%[01]+|"
                r"0[xX][0-9A-Fa-f]+|0[bB][01]+|[0-9]+)"
                r"|[A-Za-z_.$][A-Za-z0-9_.$]*"
                r")",
                operand,
            )
            if primary is None:
                replace_start = operand_start
                replace_end = operand_end
                original_value = ""
            else:
                local_start, local_end = primary.span("value")
                replace_start = operand_start + local_start
                replace_end = operand_start + local_end
                candidate = primary.group("value")
                original_value = (
                    candidate
                    if re.fullmatch(
                        r"[+-]?(?:\$[0-9A-Fa-f]+|%[01]+|"
                        r"0[xX][0-9A-Fa-f]+|0[bB][01]+|[0-9]+)",
                        candidate,
                    )
                    else ""
                )

            block_position = block.position()
            return AssemblerOperandContext(
                insert_position=block_position + max(
                    operand_start,
                    min(position, operand_end),
                ),
                replace_start=block_position + replace_start,
                replace_end=block_position + replace_end,
                original_value=original_value,
            )

        def _open_operand_calculator(
            self,
            context: AssemblerOperandContext,
        ) -> None:
            self._hide_completion()
            dialog = NumberCalculatorDialog(self, context)
            dialog.exec_()

        def _schedule_completion_update(self) -> None:
            QTimer.singleShot(0, self._update_completion)

        def _completion_candidates(self, prefix: str):
            wanted = prefix.upper()
            return tuple(
                info
                for mnemonic, info in self._assembler_commands().items()
                if mnemonic.startswith(wanted)
            )

        def _current_completion(self):
            if not self._completion_enabled or not self.hasFocus():
                return None

            cursor = self.textCursor()
            if cursor.hasSelection():
                return None

            block_text = cursor.block().text()
            position_in_block = cursor.positionInBlock()
            text_before_cursor = block_text[:position_in_block]
            if ";" in text_before_cursor:
                return None

            word_match = re.search(r"([A-Za-z]{1,8})$", text_before_cursor)
            if word_match is None:
                return None

            # -------------------------------------------------------------------
            # Nur die Opcode-Position vervollstaendigen: am Zeilenanfang oder
            # direkt hinter einer mit Doppelpunkt abgeschlossenen Marke.
            # -------------------------------------------------------------------
            prefix_text = text_before_cursor[:word_match.start()]
            if prefix_text.strip() and re.fullmatch(
                r"\s*[A-Za-z_.$][A-Za-z0-9_.$]*:\s*",
                prefix_text,
            ) is None:
                return None

            prefix = word_match.group(1)
            candidates = self._completion_candidates(prefix)
            if not candidates:
                return None

            start = cursor.block().position() + word_match.start(1)
            return (candidates[0], candidates, prefix, start, cursor.position())

        @staticmethod
        def _display_mnemonic(info: AssemblerCommandInfo, prefix: str) -> str:
            return info.mnemonic.lower() if prefix.islower() else info.mnemonic

        def _update_completion(self) -> None:
            context = self._current_completion()
            if context is None:
                self._hide_completion()
                return

            info, candidates, prefix, _start, _end = context
            self._completion_context = context
            display_mnemonic = self._display_mnemonic(info, prefix)
            suffix = display_mnemonic[len(prefix):]

            if suffix:
                self.completion_ghost.setFont(self.font())
                self.completion_ghost.setText(suffix)
                self.completion_ghost.adjustSize()
                self.completion_ghost.show()
            else:
                self.completion_ghost.hide()

            available = ", ".join(
                candidate.mnemonic for candidate in candidates[:8]
            )
            if len(candidates) > 8:
                available += ", ..."
            self.completion_header.setText(
                f"{info.mnemonic}    {info.operands}    Verfuegbar: {available}"
            )
            self.completion_description.setText(info.description)
            self.completion_frame.show()
            self.completion_frame.raise_()
            self.completion_ghost.raise_()
            self._position_completion_widgets()

        def _position_completion_widgets(self) -> None:
            if self._completion_context is None:
                return

            cursor_rectangle = self.cursorRect()
            if self.completion_ghost.isVisible():
                self.completion_ghost.move(
                    cursor_rectangle.right(),
                    cursor_rectangle.top(),
                )

            if not self.completion_frame.isVisible():
                return

            viewport_rectangle = self.viewport().rect()
            frame_width = max(
                280,
                min(620, viewport_rectangle.width() - 12),
            )
            self.completion_description.setFixedWidth(frame_width - 20)
            self.completion_frame.adjustSize()
            self.completion_frame.resize(
                frame_width,
                self.completion_frame.sizeHint().height(),
            )

            x_position = min(
                max(4, cursor_rectangle.left()),
                max(4, viewport_rectangle.width() - frame_width - 4),
            )
            y_position = cursor_rectangle.bottom() + 5
            if y_position + self.completion_frame.height() > viewport_rectangle.bottom():
                y_position = max(
                    4,
                    cursor_rectangle.top() - self.completion_frame.height() - 5,
                )
            self.completion_frame.move(x_position, y_position)

        def _hide_completion(self) -> None:
            self._completion_context = None
            self.completion_ghost.hide()
            self.completion_frame.hide()

        def _accept_completion(self) -> None:
            if self._completion_context is None:
                return

            info, _candidates, prefix, start, end = self._completion_context
            replacement = self._display_mnemonic(info, prefix)
            if info.default_operand:
                replacement += " " + info.default_operand

            cursor = self.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.insertText(replacement)
            self.setTextCursor(cursor)
            self._hide_completion()

        def _show_completion_help(self) -> None:
            if self._completion_context is None:
                return
            info = self._completion_context[0]
            help_text = (
                f"{info.mnemonic}\n\n"
                f"Syntax: {info.mnemonic} {info.operands}\n\n"
                f"{info.description}"
            )
            self.assembler_help_requested.emit(info.mnemonic, help_text)

        def help_word_at_cursor(self) -> str:
            """Liefert den Bezeichner direkt unter beziehungsweise am Cursor."""
            source = self.toPlainText()
            position = max(0, min(self.textCursor().position(), len(source)))
            identifier = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
            for match in identifier.finditer(source):
                if match.start() <= position <= match.end():
                    return match.group(0)
            if position > 0:
                for match in identifier.finditer(source):
                    if match.start() <= position - 1 < match.end():
                        return match.group(0)
            return ""

        def request_context_help(self) -> None:
            word = self.help_word_at_cursor()
            if not word and self._completion_context is not None:
                word = self._completion_context[0].mnemonic
            self.context_help_requested.emit(word)

        def _update_completion_theme(self) -> None:
            if self._dark_mode:
                ghost_color = "#aeb4bf"
                frame_background = "#202630"
                frame_border = "#718198"
                frame_text = "#ffffff"
            else:
                ghost_color = "#808080"
                frame_background = "#ffffdc"
                frame_border = "#808080"
                frame_text = "#000000"

            self.completion_ghost.setStyleSheet(
                f"color: {ghost_color}; background: transparent;"
            )
            self.completion_frame.setStyleSheet(
                "QFrame#assembler_completion_frame {"
                f"background-color: {frame_background};"
                f"border: 1px solid {frame_border};"
                "}"
                "QLabel {"
                f"color: {frame_text};"
                "background: transparent; border: 0;"
                "}"
                "QLabel#assembler_completion_header { font-weight: bold; }"
            )

        def keyPressEvent(self, event) -> None:
            if event.key() == Qt.Key_F1:
                self.request_context_help()
                event.accept()
                return
            if self.completion_frame.isVisible():
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    self._accept_completion()
                    event.accept()
                    return
                if event.key() == Qt.Key_Escape:
                    self._hide_completion()
                    event.accept()
                    return
            super().keyPressEvent(event)

        def focusOutEvent(self, event) -> None:
            self._hide_completion()
            super().focusOutEvent(event)

        def mouseMoveEvent(self, event) -> None:
            if self._jump_target_at_point(event.pos()) is not None:
                self.viewport().setCursor(Qt.PointingHandCursor)
            else:
                self.viewport().setCursor(Qt.IBeamCursor)
            super().mouseMoveEvent(event)

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.LeftButton:
                target = self._jump_target_at_point(event.pos())
                if target is not None and self._jump_to_label(target):
                    event.accept()
                    return
            super().mousePressEvent(event)

        def contextMenuEvent(self, event) -> None:
            operand_context = self._assembler_operand_context_at_point(
                event.pos()
            )
            menu = self.createStandardContextMenu()
            if operand_context is not None:
                menu.addSeparator()
                calculator_action = menu.addAction("Rechner für Operand...")
                calculator_action.triggered.connect(
                    lambda checked=False, value=operand_context:
                    self._open_operand_calculator(value)
                )
            menu.exec_(event.globalPos())
            menu.deleteLater()

        def leaveEvent(self, event) -> None:
            self.viewport().setCursor(Qt.IBeamCursor)
            super().leaveEvent(event)

        def _marker_area_width(self) -> int:
            return (
                self.GUTTER_MARKER_COLUMN_WIDTH
                * self.GUTTER_MARKER_COLUMNS
            )

        @staticmethod
        def _cursor_line_numbers(cursors) -> Tuple[int, ...]:
            result = set()
            for cursor in cursors:
                block = cursor.block()
                if block.isValid():
                    result.add(block.blockNumber() + 1)
            return tuple(sorted(result))

        def breakpoint_lines(self) -> Tuple[int, ...]:
            return self._cursor_line_numbers(self._breakpoint_cursors)

        def bookmark_lines(self) -> Tuple[int, ...]:
            return self._cursor_line_numbers(self._bookmark_cursors)

        def _marker_cursors(self, marker_kind: str):
            if marker_kind == "breakpoint":
                return self._breakpoint_cursors
            if marker_kind == "bookmark":
                return self._bookmark_cursors
            raise ValueError(f"Unbekannter Gutter-Marker: {marker_kind}")

        def _set_gutter_marker(self, marker_kind: str, line_number: int) -> bool:
            block = self.document().findBlockByNumber(int(line_number) - 1)
            if not block.isValid():
                return False
            cursors = self._marker_cursors(marker_kind)
            if int(line_number) in self._cursor_line_numbers(cursors):
                return False
            cursor = QTextCursor(self.document())
            cursor.setPosition(block.position())
            cursors.append(cursor)
            self.line_number_area.update()
            if marker_kind == "breakpoint":
                self.breakpoints_changed.emit()
            else:
                self.bookmarks_changed.emit()
            return True

        def _remove_gutter_marker(self, marker_kind: str, line_number: int) -> bool:
            cursors = self._marker_cursors(marker_kind)
            line_number = int(line_number)
            kept = []
            removed = False
            for cursor in cursors:
                block = cursor.block()
                current_line = block.blockNumber() + 1 if block.isValid() else -1
                if current_line == line_number:
                    removed = True
                    continue
                kept.append(cursor)
            if not removed:
                return False
            if marker_kind == "breakpoint":
                self._breakpoint_cursors = kept
                self.breakpoints_changed.emit()
            else:
                self._bookmark_cursors = kept
                self.bookmarks_changed.emit()
            self.line_number_area.update()
            return True

        def clear_gutter_markers(self) -> None:
            had_breakpoints = bool(self._breakpoint_cursors)
            had_bookmarks = bool(self._bookmark_cursors)
            self._breakpoint_cursors = []
            self._bookmark_cursors = []
            self.line_number_area.update()
            if had_breakpoints:
                self.breakpoints_changed.emit()
            if had_bookmarks:
                self.bookmarks_changed.emit()

        def _gutter_document_changed(self) -> None:
            if not (self._breakpoint_cursors or self._bookmark_cursors):
                return
            # QTextCursor-Positionen wandern bei Einfügungen/Löschungen mit.
            # Dadurch bleiben Marker an ihrem Textblock gebunden und das
            # Favoriten-Menü bekommt automatisch die aktualisierte Zeilennummer.
            self.line_number_area.update()
            self.breakpoints_changed.emit()
            self.bookmarks_changed.emit()

        def _line_number_at_gutter_y(self, y: int) -> Optional[int]:
            cursor = self.cursorForPosition(QPoint(0, int(y)))
            block = cursor.block()
            if not block.isValid():
                return None
            return block.blockNumber() + 1

        def handle_line_number_area_mouse_press(self, event) -> bool:
            x = int(event.pos().x())
            marker_width = self._marker_area_width()
            if x < 0 or x >= marker_width:
                return False
            line_number = self._line_number_at_gutter_y(event.pos().y())
            if line_number is None:
                return False
            marker_kind = (
                "breakpoint"
                if x < self.GUTTER_MARKER_COLUMN_WIDTH
                else "bookmark"
            )
            if event.button() == Qt.LeftButton:
                self._set_gutter_marker(marker_kind, line_number)
                return True
            if event.button() == Qt.RightButton:
                self._remove_gutter_marker(marker_kind, line_number)
                return True
            return False

        def line_number_area_width(self) -> int:
            digits = max(1, len(str(max(1, self.blockCount()))))
            return (
                self._marker_area_width()
                + 10
                + self.fontMetrics().horizontalAdvance("9") * digits
            )

        def update_line_number_area_width(self, _new_block_count: int = 0) -> None:
            self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
            self.line_number_area.update()

        def update_line_number_area(self, rect: QRect, dy: int) -> None:
            if dy:
                self.line_number_area.scroll(0, dy)
            else:
                self.line_number_area.update(
                    0,
                    rect.y(),
                    self.line_number_area.width(),
                    rect.height(),
                )

            if rect.contains(self.viewport().rect()):
                self.update_line_number_area_width(0)
            self._position_completion_widgets()

        def resizeEvent(self, event) -> None:
            super().resizeEvent(event)
            contents = self.contentsRect()
            self.line_number_area.setGeometry(
                QRect(
                    contents.left(),
                    contents.top(),
                    self.line_number_area_width(),
                    contents.height(),
                )
            )
            self._position_completion_widgets()

        def set_gutter_dark_mode(self, enabled: bool) -> None:
            self._dark_mode = bool(enabled)
            self.line_number_area.update()
            self._update_completion_theme()
            self._update_current_line_highlight()

        def line_number_area_paint_event(self, event) -> None:
            painter = QPainter(self.line_number_area)
            if self._dark_mode:
                background = QColor(16, 24, 95)
                foreground = QColor(220, 220, 220)
                separator = QColor(51, 69, 141)
            else:
                background = QColor(232, 232, 232)
                foreground = QColor(0, 0, 0)
                separator = QColor(184, 184, 184)

            painter.fillRect(event.rect(), background)
            painter.setFont(self.font())

            block = self.firstVisibleBlock()
            block_number = block.blockNumber()
            top = round(
                self.blockBoundingGeometry(block)
                .translated(self.contentOffset())
                .top()
            )
            bottom = top + round(self.blockBoundingRect(block).height())

            breakpoint_lines = set(self.breakpoint_lines())
            bookmark_lines = set(self.bookmark_lines())
            marker_column_width = self.GUTTER_MARKER_COLUMN_WIDTH
            marker_area_width = self._marker_area_width()
            painter.setRenderHint(QPainter.Antialiasing, True)

            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    line_number = block_number + 1
                    marker_diameter = min(9, max(6, self.fontMetrics().height() - 5))
                    marker_y = top + max(1, (self.fontMetrics().height() - marker_diameter) // 2)
                    if line_number in breakpoint_lines:
                        painter.setPen(QPen(QColor("#c85c5c"), 1))
                        painter.setBrush(QColor("#ff8f8f"))
                        painter.drawEllipse(
                            2, marker_y, marker_diameter, marker_diameter
                        )
                    if line_number in bookmark_lines:
                        painter.setPen(QPen(QColor("#4f8fbd"), 1))
                        painter.setBrush(QColor("#8fd0ff"))
                        painter.drawEllipse(
                            marker_column_width + 2,
                            marker_y,
                            marker_diameter,
                            marker_diameter,
                        )
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(foreground)
                    painter.drawText(
                        marker_area_width,
                        top,
                        self.line_number_area.width() - marker_area_width - 5,
                        self.fontMetrics().height(),
                        Qt.AlignRight,
                        str(line_number),
                    )

                block = block.next()
                top = bottom
                block_number += 1
                if block.isValid():
                    bottom = top + round(self.blockBoundingRect(block).height())

            painter.setPen(separator)
            painter.drawLine(
                self.GUTTER_MARKER_COLUMN_WIDTH,
                event.rect().top(),
                self.GUTTER_MARKER_COLUMN_WIDTH,
                event.rect().bottom(),
            )
            painter.drawLine(
                self._marker_area_width(),
                event.rect().top(),
                self._marker_area_width(),
                event.rect().bottom(),
            )
            painter.drawLine(
                self.line_number_area.width() - 1,
                event.rect().top(),
                self.line_number_area.width() - 1,
                event.rect().bottom(),
            )
            
    # -----------------------------------------------------------------------
    # Character-Editor für 255 editierbare C64-Zeichen ($01-$FF).
    # -----------------------------------------------------------------------
    def _c64_character_pixmap(
        rows: Sequence[int],
        foreground: QColor,
        background: QColor,
        size: int = 32,
    ) -> QPixmap:
        pixmap = QPixmap(max(8, int(size)), max(8, int(size)))
        pixmap.fill(background)
        painter = QPainter(pixmap)
        try:
            cell = max(1, pixmap.width() // 8)
            offset_x = (pixmap.width() - cell * 8) // 2
            offset_y = (pixmap.height() - cell * 8) // 2
            painter.setPen(Qt.NoPen)
            painter.setBrush(foreground)
            normalized = tuple(int(value) & 0xFF for value in rows)
            for y, row in enumerate(normalized[:8]):
                for x in range(8):
                    if row & (0x80 >> x):
                        painter.drawRect(
                            offset_x + x * cell,
                            offset_y + y * cell,
                            cell,
                            cell,
                        )
        finally:
            painter.end()
        return pixmap


    class CharacterPixelGrid(QWidget):
        rowsChanged = pyqtSignal(object)

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setObjectName("character_pixel_grid")
            self.setFocusPolicy(Qt.StrongFocus)
            self.setMouseTracking(True)
            self.setMinimumSize(336, 336)
            self._rows = [0] * 8
            self._foreground = QColor("#FFFFFF")
            self._background = QColor("#000000")
            self._cursor_x = 0
            self._cursor_y = 0
            self._drawing_value = None

        def rows(self) -> Tuple[int, ...]:
            return tuple(self._rows)

        def set_rows(self, rows: Sequence[int]) -> None:
            normalized = [int(value) & 0xFF for value in rows]
            if len(normalized) != 8:
                raise ValueError("Ein Zeichen muss genau acht Zeilen besitzen.")
            self._rows = normalized
            self.update()

        def set_colors(self, foreground: QColor, background: QColor) -> None:
            self._foreground = QColor(foreground)
            self._background = QColor(background)
            self.update()

        def sizeHint(self) -> QSize:
            return QSize(416, 416)

        def _geometry(self) -> Tuple[int, int, int]:
            margin = 12
            cell = max(
                8,
                min(
                    (self.width() - margin * 2) // 8,
                    (self.height() - margin * 2) // 8,
                ),
            )
            grid_size = cell * 8
            return (
                (self.width() - grid_size) // 2,
                (self.height() - grid_size) // 2,
                cell,
            )

        def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.fillRect(event.rect(), self.palette().window())
            origin_x, origin_y, cell = self._geometry()
            grid_rect = QRect(origin_x, origin_y, cell * 8, cell * 8)
            painter.fillRect(grid_rect, self._background)

            painter.setPen(Qt.NoPen)
            painter.setBrush(self._foreground)
            for y, row in enumerate(self._rows):
                for x in range(8):
                    if row & (0x80 >> x):
                        painter.drawRect(
                            origin_x + x * cell,
                            origin_y + y * cell,
                            cell,
                            cell,
                        )

            grid_color = self.palette().mid().color()
            painter.setPen(QPen(grid_color, 1))
            for index in range(9):
                x = origin_x + index * cell
                y = origin_y + index * cell
                painter.drawLine(x, origin_y, x, origin_y + cell * 8)
                painter.drawLine(origin_x, y, origin_x + cell * 8, y)

            cursor_color = self.palette().highlight().color()
            painter.setPen(QPen(cursor_color, 2))
            painter.drawRect(
                origin_x + self._cursor_x * cell + 1,
                origin_y + self._cursor_y * cell + 1,
                max(1, cell - 2),
                max(1, cell - 2),
            )

        def _position_to_cell(self, position) -> Optional[Tuple[int, int]]:
            origin_x, origin_y, cell = self._geometry()
            x = (int(position.x()) - origin_x) // cell
            y = (int(position.y()) - origin_y) // cell
            if 0 <= x < 8 and 0 <= y < 8:
                return x, y
            return None

        def _set_pixel(self, x: int, y: int, enabled: bool) -> None:
            mask = 0x80 >> int(x)
            previous = self._rows[y]
            if enabled:
                self._rows[y] |= mask
            else:
                self._rows[y] &= (~mask) & 0xFF
            self._cursor_x = int(x)
            self._cursor_y = int(y)
            if self._rows[y] != previous:
                self.rowsChanged.emit(tuple(self._rows))
            self.update()

        def mousePressEvent(self, event) -> None:
            cell = self._position_to_cell(event.pos())
            if cell is None:
                return
            x, y = cell
            if event.button() == Qt.RightButton:
                self._drawing_value = False
            elif event.button() == Qt.LeftButton:
                self._drawing_value = True
            else:
                return
            self._set_pixel(x, y, self._drawing_value)
            self.setFocus(Qt.MouseFocusReason)

        def mouseMoveEvent(self, event) -> None:
            if self._drawing_value is None:
                cell = self._position_to_cell(event.pos())
                if cell is not None:
                    self._cursor_x, self._cursor_y = cell
                    self.update()
                return
            cell = self._position_to_cell(event.pos())
            if cell is not None:
                self._set_pixel(cell[0], cell[1], self._drawing_value)

        def mouseReleaseEvent(self, event) -> None:
            self._drawing_value = None

        def keyPressEvent(self, event) -> None:
            key = event.key()
            if key == Qt.Key_Left:
                self._cursor_x = max(0, self._cursor_x - 1)
            elif key == Qt.Key_Right:
                self._cursor_x = min(7, self._cursor_x + 1)
            elif key == Qt.Key_Up:
                self._cursor_y = max(0, self._cursor_y - 1)
            elif key == Qt.Key_Down:
                self._cursor_y = min(7, self._cursor_y + 1)
            elif key in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
                mask = 0x80 >> self._cursor_x
                enabled = not bool(self._rows[self._cursor_y] & mask)
                self._set_pixel(self._cursor_x, self._cursor_y, enabled)
                return
            elif key in (Qt.Key_Delete, Qt.Key_Backspace):
                self._set_pixel(self._cursor_x, self._cursor_y, False)
                return
            else:
                super().keyPressEvent(event)
                return
            self.update()


    class CharacterPreviewWidget(QWidget):
        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setObjectName("character_preview")
            self.setMinimumSize(144, 144)
            self.setMaximumSize(224, 224)
            self._rows = [0] * 8
            self._foreground = QColor("#FFFFFF")
            self._background = QColor("#000000")

        def set_rows(self, rows: Sequence[int]) -> None:
            self._rows = [int(value) & 0xFF for value in rows]
            self.update()

        def set_colors(self, foreground: QColor, background: QColor) -> None:
            self._foreground = QColor(foreground)
            self._background = QColor(background)
            self.update()

        def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.fillRect(event.rect(), self.palette().window())
            side = min(self.width(), self.height()) - 16
            cell = max(1, side // 8)
            side = cell * 8
            left = (self.width() - side) // 2
            top = (self.height() - side) // 2
            painter.fillRect(QRect(left, top, side, side), self._background)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._foreground)
            for y, row in enumerate(self._rows):
                for x in range(8):
                    if row & (0x80 >> x):
                        painter.drawRect(
                            left + x * cell,
                            top + y * cell,
                            cell,
                            cell,
                        )


    class C64CharacterEditorDialog(QDialog):
        def __init__(
            self,
            parent: QWidget,
            *,
            initial_directory: Path,
            initial_path: Optional[Path] = None,
        ):
            super().__init__(parent)
            self.setObjectName("c64_character_editor_dialog")
            self.setWindowTitle("C64 Character-Editor")
            self.setModal(False)
            self.resize(1120, 760)

            self.initial_directory = Path(initial_directory)
            self.charset = bytearray(C64_CHARACTER_FILE_SIZE)
            self.current_code = 1
            self.current_path = None
            self.modified = False
            self.dirty_characters = set()
            self.character_items = {}

            self._create_ui()
            self._build_character_list()
            self._select_character(1)
            self._set_modified(False)

            if initial_path is not None:
                QTimer.singleShot(0, lambda: self.load_file(Path(initial_path)))

        def _create_ui(self) -> None:
            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(10, 10, 10, 10)
            root_layout.setSpacing(8)

            file_row = QHBoxLayout()
            self.new_button = QPushButton("Neu", self)
            self.load_button = QPushButton("Laden …", self)
            self.save_button = QPushButton("Speichern", self)
            self.save_as_button = QPushButton("Speichern unter …", self)
            file_row.addWidget(self.new_button)
            file_row.addWidget(self.load_button)
            file_row.addWidget(self.save_button)
            file_row.addWidget(self.save_as_button)
            file_row.addStretch(1)
            root_layout.addLayout(file_row)

            self.path_label = QLabel("Neuer Zeichensatz – 2048 Bytes", self)
            self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root_layout.addWidget(self.path_label)

            splitter = QSplitter(Qt.Horizontal, self)
            splitter.setChildrenCollapsible(False)
            root_layout.addWidget(splitter, 1)

            left_panel = QWidget(splitter)
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(6)

            search_row = QHBoxLayout()
            self.code_input = QLineEdit(left_panel)
            self.code_input.setPlaceholderText("Zeichen anspringen: $01, 0x41 oder 65")
            self.jump_button = QPushButton("Gehe zu", left_panel)
            search_row.addWidget(self.code_input, 1)
            search_row.addWidget(self.jump_button)
            left_layout.addLayout(search_row)

            self.character_list = QListWidget(left_panel)
            self.character_list.setObjectName("character_editor_list")
            self.character_list.setViewMode(QListWidget.IconMode)
            self.character_list.setResizeMode(QListWidget.Adjust)
            self.character_list.setMovement(QListWidget.Static)
            self.character_list.setIconSize(QSize(36, 36))
            self.character_list.setGridSize(QSize(62, 64))
            self.character_list.setSpacing(2)
            self.character_list.setUniformItemSizes(True)
            left_layout.addWidget(self.character_list, 1)
            splitter.addWidget(left_panel)

            right_panel = QWidget(splitter)
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(6, 0, 0, 0)
            right_layout.setSpacing(7)

            heading_row = QHBoxLayout()
            self.character_heading = QLabel(right_panel)
            heading_font = self.character_heading.font()
            heading_font.setBold(True)
            heading_font.setPointSize(max(11, heading_font.pointSize() + 1))
            self.character_heading.setFont(heading_font)
            self.previous_button = QPushButton("◀", right_panel)
            self.next_button = QPushButton("▶", right_panel)
            self.previous_button.setFixedWidth(40)
            self.next_button.setFixedWidth(40)
            heading_row.addWidget(self.character_heading, 1)
            heading_row.addWidget(self.previous_button)
            heading_row.addWidget(self.next_button)
            right_layout.addLayout(heading_row)

            editor_row = QHBoxLayout()
            self.pixel_grid = CharacterPixelGrid(right_panel)
            editor_row.addWidget(self.pixel_grid, 1)

            preview_column = QVBoxLayout()
            preview_label = QLabel("Vorschau", right_panel)
            preview_label.setAlignment(Qt.AlignCenter)
            self.preview = CharacterPreviewWidget(right_panel)
            preview_column.addWidget(preview_label)
            preview_column.addWidget(self.preview, 0, Qt.AlignHCenter)
            preview_column.addSpacing(12)

            self.output_format_box = QGroupBox("Ausgabe Format", right_panel)
            output_format_layout = QVBoxLayout(self.output_format_box)
            self.output_format_group = QButtonGroup(self.output_format_box)
            self.output_format_buttons = {}
            for output_index, output_name in enumerate(C64_OUTPUT_FORMATS):
                radio = QRadioButton(output_name, self.output_format_box)
                self.output_format_group.addButton(radio, output_index)
                self.output_format_buttons[output_name] = radio
                output_format_layout.addWidget(radio)
            self.output_format_buttons["Assembler"].setChecked(True)
            preview_column.addWidget(self.output_format_box)

            self.output_save_as_button = QPushButton(
                "Quellcode speichern unter...",
                right_panel,
            )
            self.output_save_as_button.setToolTip(
                "Charmap im ausgewählten Sprachformat speichern"
            )
            preview_column.addWidget(self.output_save_as_button)
            preview_column.addStretch(1)
            editor_row.addLayout(preview_column)
            right_layout.addLayout(editor_row, 1)

            palette_row = QHBoxLayout()
            palette_row.addWidget(QLabel("Pixel:", right_panel))
            self.foreground_combo = QComboBox(right_panel)
            palette_row.addWidget(self.foreground_combo)
            palette_row.addSpacing(12)
            palette_row.addWidget(QLabel("Hintergrund:", right_panel))
            self.background_combo = QComboBox(right_panel)
            palette_row.addWidget(self.background_combo)
            palette_row.addStretch(1)
            right_layout.addLayout(palette_row)

            for index, (name, color_name) in enumerate(C64_CHARACTER_PALETTE):
                color = QColor(color_name)
                icon = QPixmap(18, 18)
                icon.fill(color)
                self.foreground_combo.addItem(QIcon(icon), name, index)
                self.background_combo.addItem(QIcon(icon), name, index)
            self.foreground_combo.setCurrentIndex(1)
            self.background_combo.setCurrentIndex(0)

            operation_layout = QGridLayout()
            operation_layout.setHorizontalSpacing(5)
            operation_layout.setVerticalSpacing(5)
            self.clear_button = QPushButton("Leeren", right_panel)
            self.invert_button = QPushButton("Invertieren", right_panel)
            self.mirror_h_button = QPushButton("Horizontal spiegeln", right_panel)
            self.mirror_v_button = QPushButton("Vertikal spiegeln", right_panel)
            self.shift_left_button = QPushButton("←", right_panel)
            self.shift_right_button = QPushButton("→", right_panel)
            self.shift_up_button = QPushButton("↑", right_panel)
            self.shift_down_button = QPushButton("↓", right_panel)
            self.copy_button = QPushButton("Zeichen kopieren", right_panel)
            self.paste_button = QPushButton("Zeichen einfügen", right_panel)

            operation_layout.addWidget(self.clear_button, 0, 0)
            operation_layout.addWidget(self.invert_button, 0, 1)
            operation_layout.addWidget(self.mirror_h_button, 0, 2)
            operation_layout.addWidget(self.mirror_v_button, 0, 3)
            operation_layout.addWidget(self.shift_left_button, 1, 0)
            operation_layout.addWidget(self.shift_right_button, 1, 1)
            operation_layout.addWidget(self.shift_up_button, 1, 2)
            operation_layout.addWidget(self.shift_down_button, 1, 3)
            operation_layout.addWidget(self.copy_button, 2, 0, 1, 2)
            operation_layout.addWidget(self.paste_button, 2, 2, 1, 2)
            right_layout.addLayout(operation_layout)

            self.byte_label = QLabel(right_panel)
            self.byte_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            byte_font = QFont("Courier New")
            byte_font.setStyleHint(QFont.Monospace)
            byte_font.setFixedPitch(True)
            self.byte_label.setFont(byte_font)
            right_layout.addWidget(self.byte_label)

            help_label = QLabel(
                "Linke Maustaste zeichnet, rechte Maustaste löscht. "
                "Pfeiltasten bewegen den Rastercursor; Leertaste schaltet ein Pixel um.",
                right_panel,
            )
            help_label.setWordWrap(True)
            right_layout.addWidget(help_label)

            splitter.addWidget(right_panel)
            splitter.setStretchFactor(0, 2)
            splitter.setStretchFactor(1, 3)

            footer = QHBoxLayout()
            self.status_label = QLabel("Bereit", self)
            self.close_button = QPushButton("Schließen", self)
            footer.addWidget(self.status_label, 1)
            footer.addWidget(self.close_button)
            root_layout.addLayout(footer)

            self.new_button.clicked.connect(self.new_charset)
            self.load_button.clicked.connect(self.load_dialog)
            self.save_button.clicked.connect(self.save)
            self.save_as_button.clicked.connect(self.save_as)
            self.output_save_as_button.clicked.connect(
                self.save_selected_output
            )
            self.jump_button.clicked.connect(self.jump_to_code)
            self.code_input.returnPressed.connect(self.jump_to_code)
            self.character_list.itemSelectionChanged.connect(
                self._character_selection_changed
            )
            self.previous_button.clicked.connect(
                lambda: self._select_character(max(1, self.current_code - 1))
            )
            self.next_button.clicked.connect(
                lambda: self._select_character(min(255, self.current_code + 1))
            )
            self.pixel_grid.rowsChanged.connect(self._rows_changed)
            self.foreground_combo.currentIndexChanged.connect(self._colors_changed)
            self.background_combo.currentIndexChanged.connect(self._colors_changed)
            self.clear_button.clicked.connect(lambda: self._replace_rows((0,) * 8))
            self.invert_button.clicked.connect(
                lambda: self._replace_rows(c64_character_invert(self.pixel_grid.rows()))
            )
            self.mirror_h_button.clicked.connect(
                lambda: self._replace_rows(
                    c64_character_mirror_horizontal(self.pixel_grid.rows())
                )
            )
            self.mirror_v_button.clicked.connect(
                lambda: self._replace_rows(
                    c64_character_mirror_vertical(self.pixel_grid.rows())
                )
            )
            self.shift_left_button.clicked.connect(
                lambda: self._replace_rows(
                    c64_character_shift(self.pixel_grid.rows(), -1, 0)
                )
            )
            self.shift_right_button.clicked.connect(
                lambda: self._replace_rows(
                    c64_character_shift(self.pixel_grid.rows(), 1, 0)
                )
            )
            self.shift_up_button.clicked.connect(
                lambda: self._replace_rows(
                    c64_character_shift(self.pixel_grid.rows(), 0, -1)
                )
            )
            self.shift_down_button.clicked.connect(
                lambda: self._replace_rows(
                    c64_character_shift(self.pixel_grid.rows(), 0, 1)
                )
            )
            self.copy_button.clicked.connect(self.copy_character)
            self.paste_button.clicked.connect(self.paste_character)
            self.close_button.clicked.connect(self.close)

        def _colors(self) -> Tuple[QColor, QColor]:
            foreground = QColor(
                C64_CHARACTER_PALETTE[self.foreground_combo.currentIndex()][1]
            )
            background = QColor(
                C64_CHARACTER_PALETTE[self.background_combo.currentIndex()][1]
            )
            return foreground, background

        def _colors_changed(self) -> None:
            foreground, background = self._colors()
            self.pixel_grid.set_colors(foreground, background)
            self.preview.set_colors(foreground, background)
            self._refresh_all_icons()

        def _build_character_list(self) -> None:
            self.character_list.clear()
            self.character_items.clear()
            foreground, background = self._colors()
            for code in range(1, 256):
                rows = c64_charset_character_rows(self.charset, code)
                item = QListWidgetItem(
                    QIcon(_c64_character_pixmap(rows, foreground, background, 36)),
                    f"${code:02X}",
                    self.character_list,
                )
                item.setData(Qt.UserRole, code)
                item.setToolTip(
                    f"Zeichen ${code:02X} – dezimal {code} – "
                    f"Dateioffset ${code * 8:04X}"
                )
                item.setTextAlignment(Qt.AlignHCenter)
                item.setSizeHint(QSize(60, 62))
                self.character_items[code] = item

        def _refresh_all_icons(self) -> None:
            if not self.character_items:
                return
            foreground, background = self._colors()
            for code, item in self.character_items.items():
                rows = c64_charset_character_rows(self.charset, code)
                item.setIcon(
                    QIcon(_c64_character_pixmap(rows, foreground, background, 36))
                )

        def _refresh_character_item(self, code: int) -> None:
            item = self.character_items.get(int(code))
            if item is None:
                return
            foreground, background = self._colors()
            rows = c64_charset_character_rows(self.charset, code)
            item.setIcon(
                QIcon(_c64_character_pixmap(rows, foreground, background, 36))
            )
            item.setText(f"${code:02X}" + ("*" if code in self.dirty_characters else ""))

        def _select_character(self, code: int) -> None:
            code = max(1, min(255, int(code)))
            item = self.character_items.get(code)
            if item is None:
                return
            self.character_list.setCurrentItem(item)
            self.character_list.scrollToItem(item)
            self.current_code = code
            rows = c64_charset_character_rows(self.charset, code)
            self.pixel_grid.set_rows(rows)
            self.preview.set_rows(rows)
            self._update_character_labels()

        def _character_selection_changed(self) -> None:
            item = self.character_list.currentItem()
            if item is None:
                return
            code = int(item.data(Qt.UserRole))
            self.current_code = code
            rows = c64_charset_character_rows(self.charset, code)
            self.pixel_grid.set_rows(rows)
            self.preview.set_rows(rows)
            self._update_character_labels()

        def _update_character_labels(self) -> None:
            code = self.current_code
            rows = c64_charset_character_rows(self.charset, code)
            self.character_heading.setText(
                f"Zeichen ${code:02X} / {code} – Offset ${code * 8:04X}"
            )
            values = " ".join(f"${value:02X}" for value in rows)
            self.byte_label.setText(f"Bitmapzeilen: {values}")
            self.previous_button.setEnabled(code > 1)
            self.next_button.setEnabled(code < 255)

        def _rows_changed(self, rows: Sequence[int]) -> None:
            c64_charset_set_character_rows(self.charset, self.current_code, rows)
            self.dirty_characters.add(self.current_code)
            self.preview.set_rows(rows)
            self._refresh_character_item(self.current_code)
            self._update_character_labels()
            self._set_modified(True)

        def _replace_rows(self, rows: Sequence[int]) -> None:
            self.pixel_grid.set_rows(rows)
            self._rows_changed(rows)

        def _set_modified(self, modified: bool) -> None:
            self.modified = bool(modified)
            base_title = "C64 Character-Editor"
            self.setWindowTitle(base_title + (" *" if self.modified else ""))
            self.save_button.setEnabled(self.modified or self.current_path is None)

        def _confirm_discard(self) -> bool:
            if not self.modified:
                return True
            answer = QMessageBox.question(
                self,
                "Ungespeicherte Zeichen",
                "Der Zeichensatz wurde geändert. Vor dem Fortfahren speichern?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if answer == QMessageBox.Cancel:
                return False
            if answer == QMessageBox.Save:
                return self.save()
            return True

        def new_charset(self) -> None:
            if not self._confirm_discard():
                return
            self.charset = bytearray(C64_CHARACTER_FILE_SIZE)
            self.current_path = None
            self.dirty_characters.clear()
            self._build_character_list()
            self._select_character(1)
            self.path_label.setText("Neuer Zeichensatz – 2048 Bytes")
            self.status_label.setText("Neuer leerer Zeichensatz angelegt")
            self._set_modified(False)

        def load_dialog(self) -> None:
            if not self._confirm_discard():
                return
            filename, _selected = QFileDialog.getOpenFileName(
                self,
                "C64-Zeichensatz laden",
                str(self.current_path.parent if self.current_path else self.initial_directory),
                "C64-Zeichensätze (*.chr *.charset *.bin *.rom);;Alle Dateien (*)",
            )
            if filename:
                self.load_file(Path(filename), already_confirmed=True)

        def load_file(self, path: Path, already_confirmed: bool = False) -> bool:
            if not already_confirmed and not self._confirm_discard():
                return False
            try:
                normalized = normalize_c64_charset_data(Path(path).read_bytes())
            except (OSError, ValueError) as exc:
                QMessageBox.critical(
                    self,
                    "Zeichensatz konnte nicht geladen werden",
                    str(exc),
                )
                return False
            self.charset = normalized
            self.current_path = Path(path).resolve()
            self.initial_directory = self.current_path.parent
            self.dirty_characters.clear()
            self._build_character_list()
            self._select_character(1)
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(
                f"{self.current_path.name} geladen – Zeichen $01-$FF editierbar"
            )
            self._set_modified(False)
            return True

        def save(self) -> bool:
            if self.current_path is None:
                return self.save_as()
            try:
                self.current_path.write_bytes(bytes(self.charset))
            except OSError as exc:
                QMessageBox.critical(self, "Speichern fehlgeschlagen", str(exc))
                return False
            self.dirty_characters.clear()
            for code in self.character_items:
                self._refresh_character_item(code)
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(
                f"Gespeichert: {self.current_path.name} – 2048 Bytes"
            )
            self._set_modified(False)
            return True

        def save_as(self) -> bool:
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                "C64-Zeichensatz speichern",
                str(
                    self.current_path
                    if self.current_path is not None
                    else self.initial_directory / "custom_charset.chr"
                ),
                "C64-Zeichensatz (*.chr);;Binärdatei (*.bin);;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(".chr")
            self.current_path = target.resolve()
            self.initial_directory = self.current_path.parent
            return self.save()

        def _selected_output_format(self) -> str:
            for output_name, radio in self.output_format_buttons.items():
                if radio.isChecked():
                    return output_name
            return "Assembler"

        def save_selected_output(self) -> bool:
            output_format = self._selected_output_format()
            extension = c64_output_format_extension(output_format)
            filename, _selected_filter = QFileDialog.getSaveFileName(
                self,
                f"Charmap als {output_format} speichern",
                str(self.initial_directory / f"custom_charset{extension}"),
                c64_output_format_filter(output_format) + ";;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(extension)
            output = format_c64_charset_output(self.charset, output_format)
            try:
                target.write_text(output, encoding="utf-8", newline="\n")
            except OSError as exc:
                QMessageBox.critical(self, "Export fehlgeschlagen", str(exc))
                return False
            self.initial_directory = target.parent
            self.status_label.setText(
                f"Charmap als {output_format} gespeichert: {target.name}"
            )
            return True

        def export_source(self) -> None:
            # Bestehende Toolbar-/Dateischaltfläche bleibt kompatibel und
            # verwendet nun ebenfalls die rechts gewählte Ausgabesprache.
            self.save_selected_output()

        def copy_character(self) -> None:
            rows = self.pixel_grid.rows()
            text = " ".join(f"{value:02X}" for value in rows)
            QApplication.clipboard().setText(text)
            self.status_label.setText(
                f"Zeichen ${self.current_code:02X} als acht Hexbytes kopiert"
            )

        def paste_character(self) -> None:
            text = QApplication.clipboard().text()
            matches = re.findall(
                r"(?i)(?:\$|0x)?([0-9a-f]{2})(?![0-9a-f])",
                text,
            )
            if len(matches) != 8:
                QMessageBox.warning(
                    self,
                    "Zeichen konnte nicht eingefügt werden",
                    "Die Zwischenablage muss genau acht Hexbytes enthalten, "
                    "zum Beispiel: 18 3C 66 7E 66 66 66 00.",
                )
                return
            self._replace_rows(tuple(int(value, 16) for value in matches))
            self.status_label.setText(
                f"Zeichen ${self.current_code:02X} aus Zwischenablage eingefügt"
            )

        def jump_to_code(self) -> None:
            value = self.code_input.text().strip()
            if not value:
                return
            try:
                if value.startswith("$"):
                    code = int(value[1:], 16)
                elif value.lower().startswith("0x"):
                    code = int(value, 16)
                else:
                    code = int(value, 10)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Ungültiger Zeichencode",
                    "Bitte einen Wert von $01 bis $FF oder 1 bis 255 eingeben.",
                )
                return
            if not 1 <= code <= 255:
                QMessageBox.warning(
                    self,
                    "Ungültiger Zeichencode",
                    "Editierbar sind ausschließlich die Zeichen $01 bis $FF.",
                )
                return
            self._select_character(code)
            self.code_input.clear()

        def closeEvent(self, event: QCloseEvent) -> None:
            if self._confirm_discard():
                event.accept()
            else:
                event.ignore()


    class C64PaletteEditorDialog(QDialog):
        def __init__(
            self,
            parent: QWidget,
            *,
            initial_directory: Path,
            initial_path: Optional[Path] = None,
        ):
            super().__init__(parent)
            self.setObjectName("c64_palette_editor_dialog")
            self.setWindowTitle("C64 Paletten-Editor")
            self.setModal(False)
            self.resize(900, 650)

            self.initial_directory = Path(initial_directory)
            self.current_path = None
            self.palette_entries = [list(entry) for entry in C64_CHARACTER_PALETTE]
            self.current_index = 0
            self.modified = False
            self.palette_items = {}

            self._create_ui()
            self._build_palette_list()
            self._select_color(0)
            self._set_modified(False)

            if initial_path is not None:
                QTimer.singleShot(0, lambda: self.load_file(Path(initial_path)))

        def _create_ui(self) -> None:
            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(10, 10, 10, 10)
            root_layout.setSpacing(8)

            file_row = QHBoxLayout()
            self.new_button = QPushButton("Standardpalette", self)
            self.load_button = QPushButton("Laden …", self)
            self.save_button = QPushButton("Palette speichern", self)
            self.save_as_button = QPushButton("Palette speichern unter …", self)
            file_row.addWidget(self.new_button)
            file_row.addWidget(self.load_button)
            file_row.addWidget(self.save_button)
            file_row.addWidget(self.save_as_button)
            file_row.addStretch(1)
            root_layout.addLayout(file_row)

            self.path_label = QLabel("Neue Palette – 16 RGB-Farben / 48 Bytes", self)
            self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root_layout.addWidget(self.path_label)

            palette_note = QLabel(
                "Hinweis: Die 16 VIC-II-Hardwarefarbnummern sind fest. "
                "Der Editor bearbeitet ihre RGB-Darstellung für Vorschau, "
                "Emulatoren und Quellcodeexport.",
                self,
            )
            palette_note.setWordWrap(True)
            root_layout.addWidget(palette_note)

            splitter = QSplitter(Qt.Horizontal, self)
            splitter.setChildrenCollapsible(False)
            root_layout.addWidget(splitter, 1)

            left_panel = QWidget(splitter)
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(6)
            left_layout.addWidget(QLabel("C64-Farben 0–15", left_panel))

            self.palette_list = QListWidget(left_panel)
            self.palette_list.setObjectName("palette_editor_list")
            self.palette_list.setViewMode(QListWidget.IconMode)
            self.palette_list.setResizeMode(QListWidget.Adjust)
            self.palette_list.setMovement(QListWidget.Static)
            self.palette_list.setIconSize(QSize(64, 48))
            self.palette_list.setGridSize(QSize(118, 86))
            self.palette_list.setSpacing(4)
            self.palette_list.setUniformItemSizes(True)
            left_layout.addWidget(self.palette_list, 1)
            splitter.addWidget(left_panel)

            right_panel = QWidget(splitter)
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(8, 0, 0, 0)
            right_layout.setSpacing(8)

            self.color_heading = QLabel(right_panel)
            heading_font = self.color_heading.font()
            heading_font.setBold(True)
            heading_font.setPointSize(max(11, heading_font.pointSize() + 1))
            self.color_heading.setFont(heading_font)
            right_layout.addWidget(self.color_heading)

            self.color_swatch = QPushButton("Farbe auswählen …", right_panel)
            self.color_swatch.setMinimumHeight(110)
            right_layout.addWidget(self.color_swatch)

            edit_grid = QGridLayout()
            edit_grid.addWidget(QLabel("Name:", right_panel), 0, 0)
            self.name_input = QLineEdit(right_panel)
            edit_grid.addWidget(self.name_input, 0, 1)
            edit_grid.addWidget(QLabel("RGB-Hex:", right_panel), 1, 0)
            self.hex_input = QLineEdit(right_panel)
            self.hex_input.setPlaceholderText("#RRGGBB")
            edit_grid.addWidget(self.hex_input, 1, 1)
            right_layout.addLayout(edit_grid)

            edit_buttons = QHBoxLayout()
            self.apply_button = QPushButton("Übernehmen", right_panel)
            self.reset_color_button = QPushButton("Farbe zurücksetzen", right_panel)
            self.reset_all_button = QPushButton("Alle zurücksetzen", right_panel)
            edit_buttons.addWidget(self.apply_button)
            edit_buttons.addWidget(self.reset_color_button)
            edit_buttons.addWidget(self.reset_all_button)
            right_layout.addLayout(edit_buttons)

            self.rgb_label = QLabel(right_panel)
            self.rgb_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            right_layout.addWidget(self.rgb_label)
            right_layout.addStretch(1)

            self.output_format_box = QGroupBox("Ausgabe Format", right_panel)
            output_layout = QVBoxLayout(self.output_format_box)
            self.output_format_group = QButtonGroup(self.output_format_box)
            self.output_format_buttons = {}
            for output_index, output_name in enumerate(C64_OUTPUT_FORMATS):
                radio = QRadioButton(output_name, self.output_format_box)
                self.output_format_group.addButton(radio, output_index)
                self.output_format_buttons[output_name] = radio
                output_layout.addWidget(radio)
            self.output_format_buttons["Assembler"].setChecked(True)
            right_layout.addWidget(self.output_format_box)

            self.output_save_as_button = QPushButton("Speichern als...", right_panel)
            self.output_save_as_button.setToolTip(
                "Palette im ausgewählten Sprachformat speichern"
            )
            right_layout.addWidget(self.output_save_as_button)
            splitter.addWidget(right_panel)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 2)

            footer = QHBoxLayout()
            self.status_label = QLabel("Bereit", self)
            self.close_button = QPushButton("Schließen", self)
            footer.addWidget(self.status_label, 1)
            footer.addWidget(self.close_button)
            root_layout.addLayout(footer)

            self.new_button.clicked.connect(self.reset_all_colors)
            self.load_button.clicked.connect(self.load_dialog)
            self.save_button.clicked.connect(self.save)
            self.save_as_button.clicked.connect(self.save_as)
            self.palette_list.itemSelectionChanged.connect(
                self._palette_selection_changed
            )
            self.color_swatch.clicked.connect(self.choose_color)
            self.apply_button.clicked.connect(self.apply_current_color)
            self.hex_input.returnPressed.connect(self.apply_current_color)
            self.name_input.returnPressed.connect(self.apply_current_color)
            self.reset_color_button.clicked.connect(self.reset_current_color)
            self.reset_all_button.clicked.connect(self.reset_all_colors)
            self.output_save_as_button.clicked.connect(self.save_selected_output)
            self.close_button.clicked.connect(self.close)

        def _entry(self, index: int) -> Tuple[str, str]:
            name, color_hex = self.palette_entries[int(index)]
            return str(name), normalize_c64_color_hex(color_hex)

        def _color_icon(self, color_hex: str) -> QIcon:
            pixmap = QPixmap(64, 48)
            pixmap.fill(QColor(color_hex))
            return QIcon(pixmap)

        def _build_palette_list(self) -> None:
            self.palette_list.clear()
            self.palette_items.clear()
            for index in range(C64_PALETTE_COLOR_COUNT):
                name, color_hex = self._entry(index)
                item = QListWidgetItem(
                    self._color_icon(color_hex),
                    f"{index:02d}  {name}",
                    self.palette_list,
                )
                item.setData(Qt.UserRole, index)
                item.setToolTip(f"Farbe {index}: {name} – {color_hex}")
                item.setTextAlignment(Qt.AlignHCenter)
                item.setSizeHint(QSize(114, 82))
                self.palette_items[index] = item

        def _refresh_palette_item(self, index: int) -> None:
            item = self.palette_items.get(int(index))
            if item is None:
                return
            name, color_hex = self._entry(index)
            item.setIcon(self._color_icon(color_hex))
            item.setText(f"{index:02d}  {name}")
            item.setToolTip(f"Farbe {index}: {name} – {color_hex}")

        def _select_color(self, index: int) -> None:
            index = max(0, min(15, int(index)))
            item = self.palette_items.get(index)
            if item is not None:
                self.palette_list.setCurrentItem(item)
                self.palette_list.scrollToItem(item)
            self.current_index = index
            self._load_current_fields()

        def _palette_selection_changed(self) -> None:
            item = self.palette_list.currentItem()
            if item is None:
                return
            self.current_index = int(item.data(Qt.UserRole))
            self._load_current_fields()

        def _load_current_fields(self) -> None:
            name, color_hex = self._entry(self.current_index)
            self.color_heading.setText(
                f"Farbe {self.current_index:02d} – {name}"
            )
            self.name_input.setText(name)
            self.hex_input.setText(color_hex)
            self._update_swatch(color_hex)

        def _update_swatch(self, color_hex: str) -> None:
            color = QColor(color_hex)
            text_color = "#000000" if color.lightness() > 140 else "#FFFFFF"
            self.color_swatch.setStyleSheet(
                "QPushButton {"
                f"background-color: {color_hex}; color: {text_color};"
                "font-weight: bold; border: 1px solid #64748b;"
                "}"
            )
            red, green, blue = bytes.fromhex(color_hex[1:])
            self.rgb_label.setText(
                f"RGB: {red}, {green}, {blue}   Hex: {color_hex}"
            )

        def choose_color(self) -> None:
            _name, current_hex = self._entry(self.current_index)
            color = QColorDialog.getColor(
                QColor(current_hex),
                self,
                f"C64-Farbe {self.current_index} auswählen",
            )
            if not color.isValid():
                return
            self.hex_input.setText(color.name(QColor.HexRgb).upper())
            self.apply_current_color()

        def apply_current_color(self) -> bool:
            try:
                color_hex = normalize_c64_color_hex(self.hex_input.text())
            except ValueError as exc:
                QMessageBox.warning(self, "Ungültige Farbe", str(exc))
                return False
            name = self.name_input.text().strip() or f"Farbe {self.current_index}"
            self.palette_entries[self.current_index] = [name, color_hex]
            self._refresh_palette_item(self.current_index)
            self._load_current_fields()
            self._set_modified(True)
            self.status_label.setText(
                f"Farbe {self.current_index:02d} geändert: {name} {color_hex}"
            )
            return True

        def reset_current_color(self) -> None:
            name, color_hex = C64_CHARACTER_PALETTE[self.current_index]
            self.palette_entries[self.current_index] = [name, color_hex]
            self._refresh_palette_item(self.current_index)
            self._load_current_fields()
            self._set_modified(True)
            self.status_label.setText(
                f"Farbe {self.current_index:02d} auf Standard zurückgesetzt"
            )

        def reset_all_colors(self) -> None:
            if self.modified:
                answer = QMessageBox.question(
                    self,
                    "Palette zurücksetzen",
                    "Alle 16 Farben auf die Standardpalette zurücksetzen?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    return
            self.palette_entries = [list(entry) for entry in C64_CHARACTER_PALETTE]
            self.current_path = None
            self._build_palette_list()
            self._select_color(0)
            self.path_label.setText("Neue Palette – 16 RGB-Farben / 48 Bytes")
            self._set_modified(True)
            self.status_label.setText("C64-Standardpalette wiederhergestellt")

        def _set_modified(self, modified: bool) -> None:
            self.modified = bool(modified)
            self.setWindowTitle(
                "C64 Paletten-Editor" + (" *" if self.modified else "")
            )
            self.save_button.setEnabled(self.modified or self.current_path is None)

        def _confirm_discard(self) -> bool:
            if not self.modified:
                return True
            answer = QMessageBox.question(
                self,
                "Ungespeicherte Palette",
                "Die Palette wurde geändert. Vor dem Fortfahren speichern?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if answer == QMessageBox.Cancel:
                return False
            if answer == QMessageBox.Save:
                return self.save()
            return True

        def load_dialog(self) -> None:
            if not self._confirm_discard():
                return
            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "C64-Palette laden",
                str(self.current_path.parent if self.current_path else self.initial_directory),
                "C64-Paletten (*.pal *.palette *.bin);;Alle Dateien (*)",
            )
            if filename:
                self.load_file(Path(filename), already_confirmed=True)

        def load_file(self, path: Path, already_confirmed: bool = False) -> bool:
            if not already_confirmed and not self._confirm_discard():
                return False
            try:
                entries = decode_c64_palette_data(Path(path).read_bytes())
            except (OSError, ValueError) as exc:
                QMessageBox.critical(
                    self,
                    "Palette konnte nicht geladen werden",
                    str(exc),
                )
                return False
            self.palette_entries = [list(entry) for entry in entries]
            self.current_path = Path(path).resolve()
            self.initial_directory = self.current_path.parent
            self._build_palette_list()
            self._select_color(0)
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(f"Palette geladen: {self.current_path.name}")
            self._set_modified(False)
            return True

        def save(self) -> bool:
            if not self.apply_current_color():
                return False
            if self.current_path is None:
                return self.save_as()
            try:
                self.current_path.write_bytes(
                    encode_c64_palette_data(self.palette_entries)
                )
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Speichern fehlgeschlagen", str(exc))
                return False
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(
                f"Palette gespeichert: {self.current_path.name} – 48 Bytes"
            )
            self._set_modified(False)
            return True

        def save_as(self) -> bool:
            filename, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "C64-Palette speichern",
                str(
                    self.current_path
                    if self.current_path is not None
                    else self.initial_directory / "custom_palette.pal"
                ),
                "C64-Palette (*.pal);;Binärdatei (*.bin);;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(".pal")
            self.current_path = target.resolve()
            self.initial_directory = self.current_path.parent
            return self.save()

        def _selected_output_format(self) -> str:
            for output_name, radio in self.output_format_buttons.items():
                if radio.isChecked():
                    return output_name
            return "Assembler"

        def save_selected_output(self) -> bool:
            if not self.apply_current_color():
                return False
            output_format = self._selected_output_format()
            extension = c64_output_format_extension(output_format)
            filename, _selected_filter = QFileDialog.getSaveFileName(
                self,
                f"Palette als {output_format} speichern",
                str(self.initial_directory / f"custom_palette{extension}"),
                c64_output_format_filter(output_format) + ";;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(extension)
            output = format_c64_palette_output(
                self.palette_entries,
                output_format,
            )
            try:
                target.write_text(output, encoding="utf-8", newline="\n")
            except OSError as exc:
                QMessageBox.critical(self, "Export fehlgeschlagen", str(exc))
                return False
            self.initial_directory = target.parent
            self.status_label.setText(
                f"Palette als {output_format} gespeichert: {target.name}"
            )
            return True

        def closeEvent(self, event: QCloseEvent) -> None:
            if self._confirm_discard():
                event.accept()
            else:
                event.ignore()


    # -----------------------------------------------------------------------
    # C64-Textbildschirm-Editor: 40x25 Zeichen mit separaten Farbbytes.
    # -----------------------------------------------------------------------
    class C64TextScreenCanvas(QWidget):
        screenChanged = pyqtSignal()
        cursorChanged = pyqtSignal(int, int, int, int)

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setObjectName("c64_text_screen_canvas")
            self.setFocusPolicy(Qt.StrongFocus)
            self.setMouseTracking(True)
            self.setMinimumSize(720, 450)
            self._characters = bytearray([32] * C64_TEXT_SCREEN_CELL_COUNT)
            self._colors = bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT)
            self._brush_character = 65
            self._brush_color = 1
            self._cursor_x = 0
            self._cursor_y = 0
            self._drawing = False
            self._erase = False

        def sizeHint(self) -> QSize:
            return QSize(880, 570)

        def set_screen(self, characters: Sequence[int], colors: Sequence[int]) -> None:
            chars, cols = normalize_c64_text_screen_data(characters, colors)
            self._characters = chars
            self._colors = cols
            self.update()
            self._emit_cursor()

        def characters(self) -> bytearray:
            return bytearray(self._characters)

        def colors(self) -> bytearray:
            return bytearray(self._colors)

        def set_brush(self, character: int, color: int) -> None:
            self._brush_character = int(character) & 0xFF
            self._brush_color = int(color) & 0x0F

        def clear_screen(self, character: int = 32, color: int = 1) -> None:
            self._characters[:] = bytes([int(character) & 0xFF]) * C64_TEXT_SCREEN_CELL_COUNT
            self._colors[:] = bytes([int(color) & 0x0F]) * C64_TEXT_SCREEN_CELL_COUNT
            self.screenChanged.emit()
            self.update()
            self._emit_cursor()

        def _screen_rect(self) -> QRectF:
            margin = 10
            available_width = max(1, self.width() - margin * 2)
            available_height = max(1, self.height() - margin * 2)
            cell_width = available_width / C64_TEXT_SCREEN_COLUMNS
            cell_height = available_height / C64_TEXT_SCREEN_ROWS
            scale = max(4.0, min(cell_width, cell_height))
            width = scale * C64_TEXT_SCREEN_COLUMNS
            height = scale * C64_TEXT_SCREEN_ROWS
            return QRectF(
                (self.width() - width) / 2.0,
                (self.height() - height) / 2.0,
                width,
                height,
            )

        def _position_to_cell(self, position) -> Optional[Tuple[int, int]]:
            rect = self._screen_rect()
            if not rect.contains(QPointF(position)):
                return None
            cell_width = rect.width() / C64_TEXT_SCREEN_COLUMNS
            cell_height = rect.height() / C64_TEXT_SCREEN_ROWS
            x = int((position.x() - rect.left()) / cell_width)
            y = int((position.y() - rect.top()) / cell_height)
            if 0 <= x < C64_TEXT_SCREEN_COLUMNS and 0 <= y < C64_TEXT_SCREEN_ROWS:
                return x, y
            return None

        def _offset(self, x: int, y: int) -> int:
            return int(y) * C64_TEXT_SCREEN_COLUMNS + int(x)

        def _emit_cursor(self) -> None:
            offset = self._offset(self._cursor_x, self._cursor_y)
            self.cursorChanged.emit(
                self._cursor_x,
                self._cursor_y,
                self._characters[offset],
                self._colors[offset],
            )

        def _paint_cell(self, x: int, y: int, erase: bool = False) -> None:
            offset = self._offset(x, y)
            character = 32 if erase else self._brush_character
            color = 0 if erase else self._brush_color
            changed = (
                self._characters[offset] != character
                or self._colors[offset] != color
            )
            self._characters[offset] = character
            self._colors[offset] = color
            self._cursor_x = x
            self._cursor_y = y
            if changed:
                self.screenChanged.emit()
            self._emit_cursor()
            self.update()

        def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.fillRect(event.rect(), self.palette().window())
            screen_rect = self._screen_rect()
            cell_width = screen_rect.width() / C64_TEXT_SCREEN_COLUMNS
            cell_height = screen_rect.height() / C64_TEXT_SCREEN_ROWS
            font = QFont("C64 Pro Mono")
            font.setPixelSize(max(6, int(cell_height * 0.82)))
            font.setFixedPitch(True)
            painter.setFont(font)

            for y in range(C64_TEXT_SCREEN_ROWS):
                for x in range(C64_TEXT_SCREEN_COLUMNS):
                    offset = self._offset(x, y)
                    cell_rect = QRectF(
                        screen_rect.left() + x * cell_width,
                        screen_rect.top() + y * cell_height,
                        cell_width + 0.5,
                        cell_height + 0.5,
                    )
                    painter.fillRect(cell_rect, QColor(C64_CHARACTER_PALETTE[0][1]))
                    painter.setPen(QColor(C64_CHARACTER_PALETTE[self._colors[offset] & 0x0F][1]))
                    painter.drawText(
                        cell_rect,
                        Qt.AlignCenter,
                        C64_PRO_PETSCII_GLYPHS[self._characters[offset]],
                    )

            grid_pen = QPen(self.palette().mid().color(), 1)
            painter.setPen(grid_pen)
            for x in range(C64_TEXT_SCREEN_COLUMNS + 1):
                px = screen_rect.left() + x * cell_width
                painter.drawLine(QPointF(px, screen_rect.top()), QPointF(px, screen_rect.bottom()))
            for y in range(C64_TEXT_SCREEN_ROWS + 1):
                py = screen_rect.top() + y * cell_height
                painter.drawLine(QPointF(screen_rect.left(), py), QPointF(screen_rect.right(), py))

            painter.setPen(QPen(self.palette().highlight().color(), 2))
            painter.drawRect(
                QRectF(
                    screen_rect.left() + self._cursor_x * cell_width + 1,
                    screen_rect.top() + self._cursor_y * cell_height + 1,
                    max(1.0, cell_width - 2),
                    max(1.0, cell_height - 2),
                )
            )

        def mousePressEvent(self, event) -> None:
            cell = self._position_to_cell(event.pos())
            if cell is None:
                return
            if event.button() not in (Qt.LeftButton, Qt.RightButton):
                return
            self._drawing = True
            self._erase = event.button() == Qt.RightButton
            self._paint_cell(cell[0], cell[1], self._erase)
            self.setFocus(Qt.MouseFocusReason)

        def mouseMoveEvent(self, event) -> None:
            cell = self._position_to_cell(event.pos())
            if cell is None:
                return
            self._cursor_x, self._cursor_y = cell
            self._emit_cursor()
            if self._drawing and event.buttons() & (Qt.LeftButton | Qt.RightButton):
                self._paint_cell(cell[0], cell[1], self._erase)
            else:
                self.update()

        def mouseReleaseEvent(self, event) -> None:
            self._drawing = False

        def keyPressEvent(self, event) -> None:
            key = event.key()
            if key == Qt.Key_Left:
                self._cursor_x = max(0, self._cursor_x - 1)
            elif key == Qt.Key_Right:
                self._cursor_x = min(C64_TEXT_SCREEN_COLUMNS - 1, self._cursor_x + 1)
            elif key == Qt.Key_Up:
                self._cursor_y = max(0, self._cursor_y - 1)
            elif key == Qt.Key_Down:
                self._cursor_y = min(C64_TEXT_SCREEN_ROWS - 1, self._cursor_y + 1)
            elif key in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
                self._paint_cell(self._cursor_x, self._cursor_y, False)
                return
            elif key in (Qt.Key_Delete, Qt.Key_Backspace):
                self._paint_cell(self._cursor_x, self._cursor_y, True)
                return
            else:
                super().keyPressEvent(event)
                return
            self._emit_cursor()
            self.update()


    class C64TextScreenEditorDialog(QDialog):
        def __init__(
            self,
            parent: QWidget,
            *,
            initial_directory: Path,
            initial_path: Optional[Path] = None,
        ):
            super().__init__(parent)
            self.setObjectName("c64_text_screen_editor_dialog")
            self.setWindowTitle("C64 Text-Bildschirm-Editor")
            self.setModal(False)
            self.resize(1280, 820)
            self.initial_directory = Path(initial_directory)
            self.current_path = None
            self.modified = False
            self._create_ui()
            self.canvas.set_screen(
                bytearray([32] * C64_TEXT_SCREEN_CELL_COUNT),
                bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT),
            )
            self._select_character(65)
            self._set_modified(False)
            if initial_path is not None:
                QTimer.singleShot(0, lambda: self.load_file(Path(initial_path)))

        def _create_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(10, 10, 10, 10)
            root.setSpacing(8)
            file_row = QHBoxLayout()
            self.new_button = QPushButton("Neu", self)
            self.load_button = QPushButton("Laden …", self)
            self.save_button = QPushButton("Speichern", self)
            self.save_as_button = QPushButton("Speichern unter …", self)
            for button in (self.new_button, self.load_button, self.save_button, self.save_as_button):
                file_row.addWidget(button)
            file_row.addStretch(1)
            root.addLayout(file_row)
            self.path_label = QLabel("Neue Bildschirmseite – 1000 Zeichen + 1000 Farben", self)
            self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root.addWidget(self.path_label)

            splitter = QSplitter(Qt.Horizontal, self)
            splitter.setChildrenCollapsible(False)
            root.addWidget(splitter, 1)

            scroll = QScrollArea(splitter)
            scroll.setWidgetResizable(True)
            self.canvas = C64TextScreenCanvas(scroll)
            scroll.setWidget(self.canvas)
            splitter.addWidget(scroll)

            controls = QWidget(splitter)
            controls_layout = QVBoxLayout(controls)
            controls_layout.setContentsMargins(8, 0, 0, 0)
            controls_layout.setSpacing(8)

            character_box = QGroupBox("Zeichen", controls)
            character_layout = QVBoxLayout(character_box)
            self.character_list = QListWidget(character_box)
            self.character_list.setViewMode(QListWidget.IconMode)
            self.character_list.setResizeMode(QListWidget.Adjust)
            self.character_list.setMovement(QListWidget.Static)
            self.character_list.setGridSize(QSize(58, 42))
            self.character_list.setUniformItemSizes(True)
            character_font = QFont("C64 Pro Mono")
            character_font.setPointSize(11)
            self.character_list.setFont(character_font)
            for code in range(256):
                item = QListWidgetItem(
                    f"{C64_PRO_PETSCII_GLYPHS[code]}\n${code:02X}",
                    self.character_list,
                )
                item.setData(Qt.UserRole, code)
                item.setTextAlignment(Qt.AlignCenter)
                item.setToolTip(f"Zeichen ${code:02X} / {code}")
            character_layout.addWidget(self.character_list)
            controls_layout.addWidget(character_box, 1)

            color_box = QGroupBox("Zeichenfarbe", controls)
            color_layout = QVBoxLayout(color_box)
            self.color_combo = QComboBox(color_box)
            for index, (name, color_name) in enumerate(C64_CHARACTER_PALETTE):
                pixmap = QPixmap(20, 20)
                pixmap.fill(QColor(color_name))
                self.color_combo.addItem(QIcon(pixmap), f"{index:02d} – {name}", index)
            self.color_combo.setCurrentIndex(1)
            color_layout.addWidget(self.color_combo)
            controls_layout.addWidget(color_box)

            operation_box = QGroupBox("Bildschirmseite", controls)
            operation_layout = QHBoxLayout(operation_box)
            self.clear_button = QPushButton("Leeren", operation_box)
            self.fill_button = QPushButton("Mit Auswahl füllen", operation_box)
            operation_layout.addWidget(self.clear_button)
            operation_layout.addWidget(self.fill_button)
            controls_layout.addWidget(operation_box)

            self.output_format_box = QGroupBox("Ausgabe Format", controls)
            output_layout = QVBoxLayout(self.output_format_box)
            self.output_format_group = QButtonGroup(self.output_format_box)
            self.output_format_buttons = {}
            for index, name in enumerate(C64_OUTPUT_FORMATS):
                radio = QRadioButton(name, self.output_format_box)
                self.output_format_group.addButton(radio, index)
                self.output_format_buttons[name] = radio
                output_layout.addWidget(radio)
            self.output_format_buttons["Assembler"].setChecked(True)
            controls_layout.addWidget(self.output_format_box)
            self.output_save_button = QPushButton("Quellcode speichern unter...", controls)
            controls_layout.addWidget(self.output_save_button)
            splitter.addWidget(controls)
            splitter.setStretchFactor(0, 4)
            splitter.setStretchFactor(1, 2)

            footer = QHBoxLayout()
            self.status_label = QLabel("Bereit", self)
            self.close_button = QPushButton("Schließen", self)
            footer.addWidget(self.status_label, 1)
            footer.addWidget(self.close_button)
            root.addLayout(footer)

            self.new_button.clicked.connect(self.new_screen)
            self.load_button.clicked.connect(self.load_dialog)
            self.save_button.clicked.connect(self.save)
            self.save_as_button.clicked.connect(self.save_as)
            self.output_save_button.clicked.connect(self.save_selected_output)
            self.close_button.clicked.connect(self.close)
            self.character_list.itemSelectionChanged.connect(self._character_changed)
            self.color_combo.currentIndexChanged.connect(self._brush_changed)
            self.clear_button.clicked.connect(lambda: self.canvas.clear_screen(32, 1))
            self.fill_button.clicked.connect(self._fill_screen)
            self.canvas.screenChanged.connect(lambda: self._set_modified(True))
            self.canvas.cursorChanged.connect(self._cursor_changed)

        def _select_character(self, code: int) -> None:
            item = self.character_list.item(max(0, min(255, int(code))))
            if item is not None:
                self.character_list.setCurrentItem(item)
                self.character_list.scrollToItem(item)
            self._brush_changed()

        def _character_changed(self) -> None:
            self._brush_changed()

        def _brush_changed(self) -> None:
            item = self.character_list.currentItem()
            code = int(item.data(Qt.UserRole)) if item is not None else 32
            self.canvas.set_brush(code, self.color_combo.currentIndex())

        def _cursor_changed(self, x: int, y: int, character: int, color: int) -> None:
            self.status_label.setText(
                f"Position {x:02d},{y:02d} – Zeichen ${character:02X} – Farbe {color}"
            )

        def _fill_screen(self) -> None:
            item = self.character_list.currentItem()
            character = int(item.data(Qt.UserRole)) if item is not None else 32
            self.canvas.clear_screen(character, self.color_combo.currentIndex())

        def _set_modified(self, modified: bool) -> None:
            self.modified = bool(modified)
            self.setWindowTitle(
                "C64 Text-Bildschirm-Editor" + (" *" if self.modified else "")
            )
            self.save_button.setEnabled(self.modified or self.current_path is None)

        def _confirm_discard(self) -> bool:
            if not self.modified:
                return True
            answer = QMessageBox.question(
                self,
                "Ungespeicherte Bildschirmseite",
                "Die Bildschirmseite wurde geändert. Vor dem Fortfahren speichern?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if answer == QMessageBox.Cancel:
                return False
            if answer == QMessageBox.Save:
                return self.save()
            return True

        def new_screen(self) -> None:
            if not self._confirm_discard():
                return
            self.current_path = None
            self.canvas.set_screen(
                bytearray([32] * C64_TEXT_SCREEN_CELL_COUNT),
                bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT),
            )
            self.path_label.setText("Neue Bildschirmseite – 1000 Zeichen + 1000 Farben")
            self.status_label.setText("Neue leere Bildschirmseite angelegt")
            self._set_modified(False)

        def load_dialog(self) -> None:
            if not self._confirm_discard():
                return
            filename, _selected = QFileDialog.getOpenFileName(
                self,
                "C64-Bildschirmseite laden",
                str(self.current_path.parent if self.current_path else self.initial_directory),
                "C64-Bildschirmseiten (*.scr *.screen);;Binärdateien (*.bin);;Alle Dateien (*)",
            )
            if filename:
                self.load_file(Path(filename), already_confirmed=True)

        def load_file(self, path: Path, already_confirmed: bool = False) -> bool:
            if not already_confirmed and not self._confirm_discard():
                return False
            try:
                chars, colors = decode_c64_text_screen_data(Path(path).read_bytes())
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Bildschirmseite konnte nicht geladen werden", str(exc))
                return False
            self.current_path = Path(path).resolve()
            self.initial_directory = self.current_path.parent
            self.canvas.set_screen(chars, colors)
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(f"Bildschirmseite geladen: {self.current_path.name}")
            self._set_modified(False)
            return True

        def save(self) -> bool:
            if self.current_path is None:
                return self.save_as()
            try:
                self.current_path.write_bytes(
                    encode_c64_text_screen_data(self.canvas.characters(), self.canvas.colors())
                )
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Speichern fehlgeschlagen", str(exc))
                return False
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(
                f"Bildschirmseite gespeichert: {self.current_path.name} – 2000 Bytes"
            )
            self._set_modified(False)
            return True

        def save_as(self) -> bool:
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                "C64-Bildschirmseite speichern",
                str(self.current_path or self.initial_directory / "text_screen.scr"),
                "C64-Bildschirmseite (*.scr);;Binärdatei (*.bin);;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(".scr")
            self.current_path = target.resolve()
            self.initial_directory = self.current_path.parent
            return self.save()

        def _selected_output_format(self) -> str:
            for name, radio in self.output_format_buttons.items():
                if radio.isChecked():
                    return name
            return "Assembler"

        def save_selected_output(self) -> bool:
            output_format = self._selected_output_format()
            extension = c64_output_format_extension(output_format)
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                f"Bildschirmseite als {output_format} speichern",
                str(self.initial_directory / f"text_screen{extension}"),
                c64_output_format_filter(output_format) + ";;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(extension)
            try:
                target.write_text(
                    format_c64_text_screen_output(
                        self.canvas.characters(),
                        self.canvas.colors(),
                        output_format,
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Quellcodeexport fehlgeschlagen", str(exc))
                return False
            self.initial_directory = target.parent
            self.status_label.setText(
                f"Bildschirmseite als {output_format} gespeichert: {target.name}"
            )
            return True

        def closeEvent(self, event: QCloseEvent) -> None:
            if self._confirm_discard():
                event.accept()
            else:
                event.ignore()


    # -----------------------------------------------------------------------
    # 320x200-Pixelbildschirm-Editor mit 16 Farbindizes und Formwerkzeugen.
    # -----------------------------------------------------------------------
    class C64PixelScreenCanvas(QWidget):
        pixelsChanged = pyqtSignal()
        positionChanged = pyqtSignal(int, int, int)

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setObjectName("c64_pixel_screen_canvas")
            self.setFocusPolicy(Qt.StrongFocus)
            self.setMouseTracking(True)
            self.setMinimumSize(640, 400)
            self._pixels = bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT)
            self._tool = "Pencil"
            self._color = 1
            self._image = QImage(
                C64_PIXEL_SCREEN_WIDTH,
                C64_PIXEL_SCREEN_HEIGHT,
                QImage.Format_RGB32,
            )
            self._image_dirty = True
            self._drawing = False
            self._right_button = False
            self._start = None
            self._current = None
            self._last = None

        def sizeHint(self) -> QSize:
            return QSize(960, 600)

        def set_pixels(self, pixels: Sequence[int]) -> None:
            self._pixels = normalize_c64_pixel_screen(pixels)
            self._image_dirty = True
            self.update()

        def pixels(self) -> bytearray:
            return bytearray(self._pixels)

        def set_tool(self, tool: str) -> None:
            self._tool = str(tool)

        def set_color(self, color: int) -> None:
            self._color = int(color) & 0x0F

        def clear_screen(self, color: int = 0) -> None:
            self._pixels[:] = bytes([int(color) & 0x0F]) * C64_PIXEL_SCREEN_PIXEL_COUNT
            self._image_dirty = True
            self.pixelsChanged.emit()
            self.update()

        def _display_rect(self) -> QRectF:
            margin = 10
            available_width = max(1, self.width() - margin * 2)
            available_height = max(1, self.height() - margin * 2)
            scale = min(
                available_width / C64_PIXEL_SCREEN_WIDTH,
                available_height / C64_PIXEL_SCREEN_HEIGHT,
            )
            scale = max(0.5, scale)
            width = C64_PIXEL_SCREEN_WIDTH * scale
            height = C64_PIXEL_SCREEN_HEIGHT * scale
            return QRectF(
                (self.width() - width) / 2.0,
                (self.height() - height) / 2.0,
                width,
                height,
            )

        def _position_to_pixel(self, position) -> Optional[Tuple[int, int]]:
            rect = self._display_rect()
            if not rect.contains(QPointF(position)):
                return None
            x = int((position.x() - rect.left()) * C64_PIXEL_SCREEN_WIDTH / rect.width())
            y = int((position.y() - rect.top()) * C64_PIXEL_SCREEN_HEIGHT / rect.height())
            if 0 <= x < C64_PIXEL_SCREEN_WIDTH and 0 <= y < C64_PIXEL_SCREEN_HEIGHT:
                return x, y
            return None

        def _rebuild_image(self) -> None:
            if not self._image_dirty:
                return
            palette = [QColor(color_name).rgb() for _name, color_name in C64_CHARACTER_PALETTE]
            for y in range(C64_PIXEL_SCREEN_HEIGHT):
                row = y * C64_PIXEL_SCREEN_WIDTH
                for x in range(C64_PIXEL_SCREEN_WIDTH):
                    self._image.setPixel(x, y, palette[self._pixels[row + x] & 0x0F])
            self._image_dirty = False

        def _active_color(self) -> int:
            return 0 if self._right_button or self._tool == "Eraser" else self._color

        def _notify_change(self) -> None:
            self._image_dirty = True
            self.pixelsChanged.emit()
            self.update()

        def _draw_pencil_segment(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
            c64_pixel_screen_draw_line(
                self._pixels,
                start[0],
                start[1],
                end[0],
                end[1],
                self._active_color(),
            )
            self._notify_change()

        def _apply_shape(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
            color = self._active_color()
            if self._tool == "Line":
                c64_pixel_screen_draw_line(self._pixels, *start, *end, color)
            elif self._tool == "Rect":
                c64_pixel_screen_draw_rect(self._pixels, *start, *end, color)
            elif self._tool == "FillRect":
                c64_pixel_screen_fill_rect(self._pixels, *start, *end, color)
            elif self._tool in ("Circle", "FillCircle"):
                radius = int(round(((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5))
                if self._tool == "Circle":
                    c64_pixel_screen_draw_circle(self._pixels, start[0], start[1], radius, color)
                else:
                    c64_pixel_screen_fill_circle(self._pixels, start[0], start[1], radius, color)
            self._notify_change()

        def paintEvent(self, event) -> None:
            self._rebuild_image()
            painter = QPainter(self)
            painter.fillRect(event.rect(), self.palette().window())
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            rect = self._display_rect()
            painter.drawImage(rect, self._image)
            painter.setPen(QPen(self.palette().mid().color(), 1))
            painter.drawRect(rect)

            if self._drawing and self._start is not None and self._current is not None:
                scale_x = rect.width() / C64_PIXEL_SCREEN_WIDTH
                scale_y = rect.height() / C64_PIXEL_SCREEN_HEIGHT
                start_x = rect.left() + self._start[0] * scale_x
                start_y = rect.top() + self._start[1] * scale_y
                end_x = rect.left() + self._current[0] * scale_x
                end_y = rect.top() + self._current[1] * scale_y
                preview_color = QColor(C64_CHARACTER_PALETTE[self._active_color()][1])
                painter.setPen(QPen(preview_color, 2))
                if self._tool == "Line":
                    painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
                elif self._tool in ("Rect", "FillRect"):
                    shape_rect = QRectF(QPointF(start_x, start_y), QPointF(end_x, end_y)).normalized()
                    if self._tool == "FillRect":
                        fill = QColor(preview_color)
                        fill.setAlpha(90)
                        painter.fillRect(shape_rect, fill)
                    painter.drawRect(shape_rect)
                elif self._tool in ("Circle", "FillCircle"):
                    radius = (((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5)
                    circle_rect = QRectF(start_x - radius, start_y - radius, radius * 2, radius * 2)
                    if self._tool == "FillCircle":
                        fill = QColor(preview_color)
                        fill.setAlpha(90)
                        painter.setBrush(fill)
                    painter.drawEllipse(circle_rect)

        def mousePressEvent(self, event) -> None:
            point = self._position_to_pixel(event.pos())
            if point is None or event.button() not in (Qt.LeftButton, Qt.RightButton):
                return
            self._drawing = True
            self._right_button = event.button() == Qt.RightButton
            self._start = point
            self._current = point
            self._last = point
            color = self._pixels[point[1] * C64_PIXEL_SCREEN_WIDTH + point[0]]
            self.positionChanged.emit(point[0], point[1], color)
            if self._tool in ("Pencil", "Eraser"):
                self._draw_pencil_segment(point, point)
            elif self._tool == "Fill":
                c64_pixel_screen_flood_fill(
                    self._pixels,
                    point[0],
                    point[1],
                    self._active_color(),
                )
                self._notify_change()
                self._drawing = False
            self.setFocus(Qt.MouseFocusReason)

        def mouseMoveEvent(self, event) -> None:
            point = self._position_to_pixel(event.pos())
            if point is None:
                return
            color = self._pixels[point[1] * C64_PIXEL_SCREEN_WIDTH + point[0]]
            self.positionChanged.emit(point[0], point[1], color)
            if not self._drawing:
                return
            self._current = point
            if self._tool in ("Pencil", "Eraser"):
                self._draw_pencil_segment(self._last, point)
                self._last = point
            else:
                self.update()

        def mouseReleaseEvent(self, event) -> None:
            if not self._drawing:
                return
            point = self._position_to_pixel(event.pos()) or self._current or self._start
            if self._tool not in ("Pencil", "Eraser", "Fill") and self._start is not None:
                self._apply_shape(self._start, point)
            self._drawing = False
            self._right_button = False
            self._start = None
            self._current = None
            self._last = None
            self.update()


    class C64PixelScreenEditorDialog(QDialog):
        TOOL_NAMES = (
            ("Pencil", "Stift"),
            ("Eraser", "Radierer"),
            ("Line", "Linie"),
            ("Rect", "Rechteck"),
            ("FillRect", "Gefülltes Rechteck"),
            ("Circle", "Kreis"),
            ("FillCircle", "Gefüllter Kreis"),
            ("Fill", "Fläche füllen"),
        )

        def __init__(
            self,
            parent: QWidget,
            *,
            initial_directory: Path,
            initial_path: Optional[Path] = None,
        ):
            super().__init__(parent)
            self.setObjectName("c64_pixel_screen_editor_dialog")
            self.setWindowTitle("C64 Pixel-Bildschirm-Editor")
            self.setModal(False)
            self.resize(1320, 860)
            self.initial_directory = Path(initial_directory)
            self.current_path = None
            self.modified = False
            self._create_ui()
            self.canvas.set_pixels(bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT))
            self._set_modified(False)
            if initial_path is not None:
                QTimer.singleShot(0, lambda: self.load_file(Path(initial_path)))

        def _create_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(10, 10, 10, 10)
            root.setSpacing(8)
            file_row = QHBoxLayout()
            self.new_button = QPushButton("Neu", self)
            self.load_button = QPushButton("Laden …", self)
            self.save_button = QPushButton("Speichern", self)
            self.save_as_button = QPushButton("Speichern unter …", self)
            for button in (self.new_button, self.load_button, self.save_button, self.save_as_button):
                file_row.addWidget(button)
            file_row.addStretch(1)
            root.addLayout(file_row)
            self.path_label = QLabel("Neuer Pixelbildschirm – 320x200 / 16 Farben", self)
            self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root.addWidget(self.path_label)

            splitter = QSplitter(Qt.Horizontal, self)
            splitter.setChildrenCollapsible(False)
            root.addWidget(splitter, 1)
            scroll = QScrollArea(splitter)
            scroll.setWidgetResizable(True)
            self.canvas = C64PixelScreenCanvas(scroll)
            scroll.setWidget(self.canvas)
            splitter.addWidget(scroll)

            controls = QWidget(splitter)
            controls_layout = QVBoxLayout(controls)
            controls_layout.setContentsMargins(8, 0, 0, 0)
            controls_layout.setSpacing(8)

            tool_box = QGroupBox("Werkzeuge", controls)
            tool_layout = QGridLayout(tool_box)
            self.tool_group = QButtonGroup(tool_box)
            self.tool_buttons = {}
            for index, (tool_name, label) in enumerate(self.TOOL_NAMES):
                radio = QRadioButton(label, tool_box)
                self.tool_group.addButton(radio, index)
                self.tool_buttons[tool_name] = radio
                tool_layout.addWidget(radio, index // 2, index % 2)
                radio.toggled.connect(
                    lambda checked, value=tool_name: checked and self.canvas.set_tool(value)
                )
            self.tool_buttons["Pencil"].setChecked(True)
            controls_layout.addWidget(tool_box)

            color_box = QGroupBox("16 Farben", controls)
            color_layout = QGridLayout(color_box)
            self.color_group = QButtonGroup(color_box)
            self.color_group.setExclusive(True)
            self.color_buttons = {}
            for index, (name, color_name) in enumerate(C64_CHARACTER_PALETTE):
                button = QPushButton(f"{index:X}", color_box)
                button.setCheckable(True)
                button.setFixedSize(54, 36)
                text_color = "#000000" if index in (1, 3, 7, 10, 13, 15) else "#FFFFFF"
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {color_name}; color: {text_color}; }}"
                    "QPushButton:checked { border: 3px solid #FF8800; font-weight: bold; }"
                )
                button.setToolTip(f"{index:02d} – {name}")
                self.color_group.addButton(button, index)
                self.color_buttons[index] = button
                color_layout.addWidget(button, index // 4, index % 4)
                button.toggled.connect(
                    lambda checked, value=index: checked and self.canvas.set_color(value)
                )
            self.color_buttons[1].setChecked(True)
            controls_layout.addWidget(color_box)

            operation_box = QGroupBox("Bild", controls)
            operation_layout = QHBoxLayout(operation_box)
            self.clear_button = QPushButton("Schwarz löschen", operation_box)
            self.fill_screen_button = QPushButton("Mit Farbe füllen", operation_box)
            operation_layout.addWidget(self.clear_button)
            operation_layout.addWidget(self.fill_screen_button)
            controls_layout.addWidget(operation_box)

            self.output_format_box = QGroupBox("Ausgabe Format", controls)
            output_layout = QVBoxLayout(self.output_format_box)
            self.output_format_group = QButtonGroup(self.output_format_box)
            self.output_format_buttons = {}
            for index, name in enumerate(C64_OUTPUT_FORMATS):
                radio = QRadioButton(name, self.output_format_box)
                self.output_format_group.addButton(radio, index)
                self.output_format_buttons[name] = radio
                output_layout.addWidget(radio)
            self.output_format_buttons["Assembler"].setChecked(True)
            controls_layout.addWidget(self.output_format_box)
            self.output_save_button = QPushButton("Quellcode speichern unter...", controls)
            controls_layout.addWidget(self.output_save_button)
            controls_layout.addStretch(1)
            splitter.addWidget(controls)
            splitter.setStretchFactor(0, 5)
            splitter.setStretchFactor(1, 2)

            footer = QHBoxLayout()
            self.status_label = QLabel("Bereit", self)
            self.close_button = QPushButton("Schließen", self)
            footer.addWidget(self.status_label, 1)
            footer.addWidget(self.close_button)
            root.addLayout(footer)

            self.new_button.clicked.connect(self.new_screen)
            self.load_button.clicked.connect(self.load_dialog)
            self.save_button.clicked.connect(self.save)
            self.save_as_button.clicked.connect(self.save_as)
            self.output_save_button.clicked.connect(self.save_selected_output)
            self.clear_button.clicked.connect(lambda: self.canvas.clear_screen(0))
            self.fill_screen_button.clicked.connect(
                lambda: self.canvas.clear_screen(self.color_group.checkedId())
            )
            self.close_button.clicked.connect(self.close)
            self.canvas.pixelsChanged.connect(lambda: self._set_modified(True))
            self.canvas.positionChanged.connect(self._position_changed)

        def _position_changed(self, x: int, y: int, color: int) -> None:
            self.status_label.setText(f"Pixel {x:03d},{y:03d} – Farbe {color:02d}")

        def _set_modified(self, modified: bool) -> None:
            self.modified = bool(modified)
            self.setWindowTitle(
                "C64 Pixel-Bildschirm-Editor" + (" *" if self.modified else "")
            )
            self.save_button.setEnabled(self.modified or self.current_path is None)

        def _confirm_discard(self) -> bool:
            if not self.modified:
                return True
            answer = QMessageBox.question(
                self,
                "Ungespeicherter Pixelbildschirm",
                "Der Pixelbildschirm wurde geändert. Vor dem Fortfahren speichern?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if answer == QMessageBox.Cancel:
                return False
            if answer == QMessageBox.Save:
                return self.save()
            return True

        def new_screen(self) -> None:
            if not self._confirm_discard():
                return
            self.current_path = None
            self.canvas.set_pixels(bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT))
            self.path_label.setText("Neuer Pixelbildschirm – 320x200 / 16 Farben")
            self.status_label.setText("Neuer schwarzer Pixelbildschirm angelegt")
            self._set_modified(False)

        def load_dialog(self) -> None:
            if not self._confirm_discard():
                return
            filename, _selected = QFileDialog.getOpenFileName(
                self,
                "Pixelbildschirm laden",
                str(self.current_path.parent if self.current_path else self.initial_directory),
                "16-Farben-Pixelbilder (*.px16 *.pixel *.pix);;Binärdateien (*.bin);;Alle Dateien (*)",
            )
            if filename:
                self.load_file(Path(filename), already_confirmed=True)

        def load_file(self, path: Path, already_confirmed: bool = False) -> bool:
            if not already_confirmed and not self._confirm_discard():
                return False
            try:
                pixels = decode_c64_pixel_screen_data(Path(path).read_bytes())
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Pixelbildschirm konnte nicht geladen werden", str(exc))
                return False
            self.current_path = Path(path).resolve()
            self.initial_directory = self.current_path.parent
            self.canvas.set_pixels(pixels)
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(f"Pixelbildschirm geladen: {self.current_path.name}")
            self._set_modified(False)
            return True

        def save(self) -> bool:
            if self.current_path is None:
                return self.save_as()
            try:
                self.current_path.write_bytes(encode_c64_pixel_screen_data(self.canvas.pixels()))
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Speichern fehlgeschlagen", str(exc))
                return False
            self.path_label.setText(str(self.current_path))
            self.status_label.setText(
                f"Pixelbildschirm gespeichert: {self.current_path.name} – 32000 Bytes"
            )
            self._set_modified(False)
            return True

        def save_as(self) -> bool:
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                "Pixelbildschirm speichern",
                str(self.current_path or self.initial_directory / "pixel_screen.px16"),
                "16-Farben-Pixelbild (*.px16);;Binärdatei (*.bin);;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(".px16")
            self.current_path = target.resolve()
            self.initial_directory = self.current_path.parent
            return self.save()

        def _selected_output_format(self) -> str:
            for name, radio in self.output_format_buttons.items():
                if radio.isChecked():
                    return name
            return "Assembler"

        def save_selected_output(self) -> bool:
            output_format = self._selected_output_format()
            extension = c64_output_format_extension(output_format)
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                f"Pixelbildschirm als {output_format} speichern",
                str(self.initial_directory / f"pixel_screen{extension}"),
                c64_output_format_filter(output_format) + ";;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(extension)
            try:
                target.write_text(
                    format_c64_pixel_screen_output(self.canvas.pixels(), output_format),
                    encoding="utf-8",
                    newline="\n",
                )
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "Quellcodeexport fehlgeschlagen", str(exc))
                return False
            self.initial_directory = target.parent
            self.status_label.setText(
                f"Pixelbildschirm als {output_format} gespeichert: {target.name}"
            )
            return True

        def closeEvent(self, event: QCloseEvent) -> None:
            if self._confirm_discard():
                event.accept()
            else:
                event.ignore()


    # -----------------------------------------------------------------------
    # Wählt eines der 255 PETSCII-Zeichen fuer ein Hex-Editor-Byte.
    # -----------------------------------------------------------------------
    class PetsciiCharacterDialog(QDialog):
        byteSelected = pyqtSignal(int)

        def __init__(
            self,
            parent: QWidget,
            *,
            byte_index: int,
            current_value: int,
            font_family: str,
            point_size: int,
        ):
            super().__init__(parent)
            self.setObjectName("petscii_character_dialog")
            self.setWindowTitle("PETSCII-Zeichen auswählen")
            self.setModal(True)
            self.resize(720, 690)

            dialog_layout = QVBoxLayout(self)
            dialog_layout.setContentsMargins(12, 12, 12, 12)
            dialog_layout.setSpacing(8)

            heading = QLabel(
                f"PETSCII-Zeichen für Byte an Offset ${byte_index & 0xFFFF:04X}",
                self,
            )
            heading.setObjectName("petscii_dialog_heading")
            dialog_layout.addWidget(heading)

            explanation = QLabel(
                "Ein Klick ersetzt das Byte sofort in der Hex- und "
                "Zeichenansicht. $00 ist NUL und daher kein Zeichenbutton.",
                self,
            )
            explanation.setWordWrap(True)
            dialog_layout.addWidget(explanation)

            scroll_area = QScrollArea(self)
            scroll_area.setObjectName("petscii_character_scroll_area")
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.StyledPanel)

            table_widget = QWidget(scroll_area)
            table_widget.setObjectName("petscii_character_table")
            table_layout = QGridLayout(table_widget)
            table_layout.setContentsMargins(8, 8, 8, 8)
            table_layout.setHorizontalSpacing(4)
            table_layout.setVerticalSpacing(4)

            corner_label = QLabel("HEX", table_widget)
            corner_label.setAlignment(Qt.AlignCenter)
            table_layout.addWidget(corner_label, 0, 0)

            for nibble in range(0x10):
                column_label = QLabel(f"{nibble:X}", table_widget)
                column_label.setAlignment(Qt.AlignCenter)
                table_layout.addWidget(column_label, 0, nibble + 1)

                row_label = QLabel(f"{nibble:X}", table_widget)
                row_label.setAlignment(Qt.AlignCenter)
                table_layout.addWidget(row_label, nibble + 1, 0)

            glyph_font = QFont(font_family, max(11, int(point_size) + 2))
            glyph_font.setFixedPitch(True)
            glyph_font.setStyleHint(QFont.Monospace)

            self.button_group = QButtonGroup(self)
            self.button_group.setExclusive(True)
            self.character_buttons = {}

            for byte_value in range(0x01, 0x100):
                high_nibble = byte_value >> 4
                low_nibble = byte_value & 0x0F
                button = QPushButton(
                    C64_PRO_PETSCII_GLYPHS[byte_value],
                    table_widget,
                )
                button.setObjectName(f"petscii_byte_{byte_value:02X}")
                button.setProperty("byteValue", byte_value)
                button.setAccessibleName(
                    f"PETSCII-Byte ${byte_value:02X}"
                )
                button.setToolTip(
                    f"PETSCII ${byte_value:02X} "
                    f"(dezimal {byte_value})"
                )
                button.setFont(glyph_font)
                button.setCheckable(True)
                button.setFixedSize(35, 35)
                button.clicked.connect(
                    lambda checked=False, value=byte_value:
                    self._select_byte(value)
                )
                self.button_group.addButton(button, byte_value)
                self.character_buttons[byte_value] = button
                table_layout.addWidget(
                    button,
                    high_nibble + 1,
                    low_nibble + 1,
                )

            selected_button = self.character_buttons.get(current_value)
            if selected_button is not None:
                selected_button.setChecked(True)
                QTimer.singleShot(
                    0,
                    lambda button=selected_button:
                    scroll_area.ensureWidgetVisible(button, 20, 20),
                )

            scroll_area.setWidget(table_widget)
            dialog_layout.addWidget(scroll_area, 1)

            footer_layout = QHBoxLayout()
            footer_layout.addStretch(1)
            close_button = QPushButton("Schließen", self)
            close_button.setObjectName("petscii_dialog_close_button")
            close_button.clicked.connect(self.accept)
            footer_layout.addWidget(close_button)
            dialog_layout.addLayout(footer_layout)

        def _select_byte(self, byte_value: int) -> None:
            self.byteSelected.emit(int(byte_value) & 0xFF)

    # -----------------------------------------------------------------------
    # Byteorientierter Hex-Editor mit acht Bytes pro Zeile.
    # -----------------------------------------------------------------------
    class HexEditor(QAbstractScrollArea):
        BYTES_PER_ROW = 8
        BYTES_PER_GROUP = 4
        C64_FONT_FAMILY = "C64 Pro Mono"

        dataChanged = pyqtSignal()
        modificationChanged = pyqtSignal(bool)
        saveRequested = pyqtSignal(bool)

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.setObjectName("hex_editor")
            self.setFocusPolicy(Qt.StrongFocus)
            self.setMouseTracking(True)

            self._data = bytearray()
            self._modified = False
            self._cursor_index = 0
            self._active_nibble = 0
            self._selection_anchor = None
            self._selection_end = None
            self._dragging = False

            self.verticalScrollBar().valueChanged.connect(
                self.viewport().update
            )
            self.horizontalScrollBar().valueChanged.connect(
                self.viewport().update
            )
            self._update_scrollbars()

        @property
        def is_modified(self) -> bool:
            return self._modified

        def data(self) -> bytes:
            return bytes(self._data)

        def set_data(self, data: bytes, *, modified: bool = False) -> None:
            self._data = bytearray(data)
            if self._data:
                self._cursor_index = min(
                    self._cursor_index,
                    len(self._data) - 1,
                )
            else:
                self._cursor_index = 0
            self._active_nibble = 0
            self._selection_anchor = None
            self._selection_end = None
            self._set_modified(modified)
            self._update_scrollbars()
            self.viewport().update()

        def set_c64_font_size(self, point_size: int) -> None:
            font = QFont(self.C64_FONT_FAMILY, max(1, int(point_size)))
            font.setFixedPitch(True)
            font.setStyleHint(QFont.Monospace)
            self.setFont(font)
            self._update_scrollbars()
            self.viewport().update()

        def _set_modified(self, modified: bool) -> None:
            modified = bool(modified)
            if self._modified == modified:
                return
            self._modified = modified
            self.modificationChanged.emit(modified)

        def mark_saved(self) -> None:
            self._set_modified(False)

        def _font_geometry(self):
            metrics = self.fontMetrics()
            character_width = max(1, metrics.horizontalAdvance("0"))
            row_height = max(1, metrics.height() + 4)
            byte_cell_width = character_width * 3
            # ---------------------------------------------------------------
            # Vierstelliger 16-Bit-Offset plus drei Zeichen Abstand vor den
            # beiden Hex-Byte-Gruppen.
            # ---------------------------------------------------------------
            left_x = 12 + character_width * 7
            separator_x = left_x + self.BYTES_PER_GROUP * byte_cell_width
            right_x = separator_x + character_width * 3
            character_x = (
                right_x
                + self.BYTES_PER_GROUP * byte_cell_width
                + character_width * 3
            )
            content_width = (
                character_x
                + self.BYTES_PER_ROW * character_width
                + 12
            )
            return (
                metrics,
                character_width,
                row_height,
                byte_cell_width,
                left_x,
                separator_x,
                right_x,
                character_x,
                content_width,
            )

        def _row_count(self) -> int:
            return max(
                1,
                (len(self._data) + self.BYTES_PER_ROW - 1)
                // self.BYTES_PER_ROW,
            )

        def _update_scrollbars(self) -> None:
            (
                _metrics,
                _character_width,
                row_height,
                _byte_cell_width,
                _left_x,
                _separator_x,
                _right_x,
                _character_x,
                content_width,
            ) = self._font_geometry()

            visible_rows = max(1, self.viewport().height() // row_height)
            vertical = self.verticalScrollBar()
            vertical.setRange(0, max(0, self._row_count() - visible_rows))
            vertical.setPageStep(visible_rows)
            vertical.setSingleStep(1)

            horizontal = self.horizontalScrollBar()
            horizontal.setRange(
                0,
                max(0, content_width - self.viewport().width()),
            )
            horizontal.setPageStep(max(1, self.viewport().width()))
            horizontal.setSingleStep(max(1, self.fontMetrics().horizontalAdvance("0")))

        def resizeEvent(self, event) -> None:
            super().resizeEvent(event)
            self._update_scrollbars()

        def scrollContentsBy(self, dx: int, dy: int) -> None:
            del dx, dy
            self.viewport().update()

        def _selection_range(self):
            if (
                self._selection_anchor is None
                or self._selection_end is None
                or not self._data
            ):
                return None
            first = max(
                0,
                min(self._selection_anchor, self._selection_end),
            )
            last = min(
                len(self._data) - 1,
                max(self._selection_anchor, self._selection_end),
            )
            return first, last

        def _is_selected(self, index: int) -> bool:
            selection = self._selection_range()
            return (
                selection is not None
                and selection[0] <= index <= selection[1]
            )

        @staticmethod
        def _display_character(value: int) -> str:
            return C64_PRO_PETSCII_GLYPHS[value & 0xFF]

        def paintEvent(self, event) -> None:
            painter = QPainter(self.viewport())
            painter.fillRect(event.rect(), self.palette().color(QPalette.Base))
            painter.setFont(self.font())

            (
                metrics,
                character_width,
                row_height,
                byte_cell_width,
                left_x,
                separator_x,
                right_x,
                character_x,
                _content_width,
            ) = self._font_geometry()
            horizontal_offset = self.horizontalScrollBar().value()
            first_row = self.verticalScrollBar().value()
            visible_rows = self.viewport().height() // row_height + 2
            normal_color = self.palette().color(QPalette.Text)
            selected_background = self.palette().color(QPalette.Highlight)
            selected_text = self.palette().color(QPalette.HighlightedText)
            separator_color = QColor(120, 128, 140)
            address_color = QColor(128, 136, 148)

            for visible_row in range(visible_rows):
                row = first_row + visible_row
                if row >= self._row_count():
                    break
                top = visible_row * row_height
                baseline = top + metrics.ascent() + 2

                painter.setPen(address_color)
                painter.drawText(
                    12 - horizontal_offset,
                    baseline,
                    f"{(row * self.BYTES_PER_ROW) & 0xFFFF:04X}",
                )

                painter.setPen(separator_color)
                separator_screen_x = separator_x - horizontal_offset + character_width
                painter.drawLine(
                    separator_screen_x,
                    top + 1,
                    separator_screen_x,
                    top + row_height - 2,
                )

                for column in range(self.BYTES_PER_ROW):
                    index = row * self.BYTES_PER_ROW + column
                    if index >= len(self._data):
                        break

                    if column < self.BYTES_PER_GROUP:
                        x = left_x + column * byte_cell_width
                    else:
                        x = right_x + (
                            column - self.BYTES_PER_GROUP
                        ) * byte_cell_width
                    x -= horizontal_offset

                    selected = self._is_selected(index)
                    if selected:
                        painter.fillRect(
                            QRect(
                                x - 1,
                                top,
                                character_width * 2 + 2,
                                row_height,
                            ),
                            selected_background,
                        )
                        painter.setPen(selected_text)
                    else:
                        painter.setPen(normal_color)

                    painter.drawText(
                        x,
                        baseline,
                        f"{self._data[index]:02X}",
                    )

                    painter.setPen(normal_color)
                    painter.drawText(
                        character_x
                        + column * character_width
                        - horizontal_offset,
                        baseline,
                        self._display_character(self._data[index]),
                    )

                    if (
                        self.hasFocus()
                        and index == self._cursor_index
                        and not self._dragging
                    ):
                        cursor_x = x + self._active_nibble * character_width
                        painter.setPen(QPen(normal_color, 1))
                        painter.drawRect(
                            QRect(
                                cursor_x - 1,
                                top + 1,
                                character_width + 1,
                                row_height - 3,
                            )
                        )

        def _index_at_position(self, position) -> Optional[int]:
            (
                _metrics,
                character_width,
                row_height,
                byte_cell_width,
                left_x,
                _separator_x,
                right_x,
                character_x,
                _content_width,
            ) = self._font_geometry()
            x = position.x() + self.horizontalScrollBar().value()
            row = position.y() // row_height + self.verticalScrollBar().value()

            column = None
            left_width = self.BYTES_PER_GROUP * byte_cell_width
            if left_x <= x < left_x + left_width:
                local = x - left_x
                candidate = local // byte_cell_width
                if local % byte_cell_width < character_width * 2:
                    column = candidate
            elif right_x <= x < right_x + left_width:
                local = x - right_x
                candidate = local // byte_cell_width
                if local % byte_cell_width < character_width * 2:
                    column = self.BYTES_PER_GROUP + candidate
            elif (
                character_x
                <= x
                < character_x + self.BYTES_PER_ROW * character_width
            ):
                column = (x - character_x) // character_width

            if column is None:
                return None
            index = row * self.BYTES_PER_ROW + int(column)
            if not self._data or index < 0 or index >= len(self._data):
                return None
            return index

        def _place_cursor_from_mouse(self, position, *, extend: bool) -> bool:
            index = self._index_at_position(position)
            if index is None:
                return False
            if not extend or self._selection_anchor is None:
                self._selection_anchor = index
            self._selection_end = index
            self._cursor_index = index
            self._active_nibble = 0
            self.viewport().update()
            return True

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.LeftButton:
                self.setFocus(Qt.MouseFocusReason)
                extend = bool(event.modifiers() & Qt.ShiftModifier)
                if self._place_cursor_from_mouse(event.pos(), extend=extend):
                    self._dragging = True
                    event.accept()
                    return
            elif event.button() == Qt.RightButton:
                index = self._index_at_position(event.pos())
                if index is not None and not self._is_selected(index):
                    self._selection_anchor = index
                    self._selection_end = index
                    self._cursor_index = index
                    self._active_nibble = 0
                    self.viewport().update()
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event) -> None:
            if self._dragging and event.buttons() & Qt.LeftButton:
                self._place_cursor_from_mouse(event.pos(), extend=True)
                event.accept()
                return
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event) -> None:
            if event.button() == Qt.LeftButton and self._dragging:
                self._dragging = False
                self.viewport().update()
                event.accept()
                return
            super().mouseReleaseEvent(event)

        def _selected_bytes(self) -> bytes:
            selection = self._selection_range()
            if selection is None:
                return b""
            return bytes(self._data[selection[0] : selection[1] + 1])

        @classmethod
        def _format_clipboard_bytes(cls, data: bytes) -> str:
            lines = []
            for start in range(0, len(data), cls.BYTES_PER_ROW):
                row = data[start : start + cls.BYTES_PER_ROW]
                left = " ".join(f"{value:02X}" for value in row[:4])
                right = " ".join(f"{value:02X}" for value in row[4:])
                lines.append(f"{left}  |  {right}" if right else left)
            return "\n".join(lines)

        @staticmethod
        def _parse_clipboard_bytes(text: str) -> bytes:
            stripped = text.strip()
            if re.fullmatch(r"[0-9A-Fa-f]+", stripped or ""):
                if len(stripped) % 2:
                    return b""
                try:
                    return bytes.fromhex(stripped)
                except ValueError:
                    return b""

            tokens = re.findall(
                r"(?i)(?<![0-9a-f])[0-9a-f]{2}(?![0-9a-f])",
                stripped,
            )
            try:
                return bytes(int(token, 16) for token in tokens)
            except ValueError:
                return b""

        def copy_selection(self) -> None:
            data = self._selected_bytes()
            if data:
                QApplication.clipboard().setText(
                    self._format_clipboard_bytes(data)
                )

        def cut_selection(self) -> None:
            selection = self._selection_range()
            if selection is None:
                return
            self.copy_selection()
            first, last = selection
            del self._data[first : last + 1]
            self._cursor_index = min(first, max(0, len(self._data) - 1))
            self._selection_anchor = None
            self._selection_end = None
            self._active_nibble = 0
            self._set_modified(True)
            self._update_scrollbars()
            self.viewport().update()
            self.dataChanged.emit()

        def paste_bytes(self) -> None:
            pasted = self._parse_clipboard_bytes(
                QApplication.clipboard().text()
            )
            if not pasted:
                return

            selection = self._selection_range()
            if selection is not None:
                first, last = selection
                self._data[first : last + 1] = pasted
                insertion = first
            else:
                insertion = min(self._cursor_index, len(self._data))
                self._data[insertion:insertion] = pasted

            self._cursor_index = insertion + len(pasted) - 1
            self._selection_anchor = insertion
            self._selection_end = self._cursor_index
            self._active_nibble = 0
            self._set_modified(True)
            self._update_scrollbars()
            self._ensure_cursor_visible()
            self.viewport().update()
            self.dataChanged.emit()

        # ---------------------------------------------------------------
        # Ersetzt genau ein Byte und synchronisiert beide Ansichten.
        # ---------------------------------------------------------------
        def _replace_byte(self, index: int, byte_value: int) -> None:
            if index < 0 or index >= len(self._data):
                return

            byte_value = int(byte_value) & 0xFF
            changed = self._data[index] != byte_value
            self._data[index] = byte_value
            self._cursor_index = index
            self._active_nibble = 0
            self._selection_anchor = index
            self._selection_end = index
            self._ensure_cursor_visible()
            self.viewport().update()

            if changed:
                self._set_modified(True)
                self.dataChanged.emit()

        def _open_petscii_dialog(self, byte_index: int) -> None:
            if byte_index < 0 or byte_index >= len(self._data):
                return

            dialog = PetsciiCharacterDialog(
                self,
                byte_index=byte_index,
                current_value=self._data[byte_index],
                font_family=self.C64_FONT_FAMILY,
                point_size=self.font().pointSize(),
            )
            dialog.byteSelected.connect(
                lambda value, index=byte_index:
                self._replace_byte(index, value)
            )
            dialog.exec_()

        def contextMenuEvent(self, event) -> None:
            menu = QMenu(self)
            selection_exists = self._selection_range() is not None
            byte_index = self._index_at_position(event.pos())

            copy_action = menu.addAction("Kopieren")
            cut_action = menu.addAction("Ausschneiden")
            paste_action = menu.addAction("Einfügen")
            menu.addSeparator()
            petscii_action = menu.addAction(
                "PETSCII-Zeichen auswählen..."
            )
            menu.addSeparator()
            save_action = menu.addAction("Speichern")
            save_as_action = menu.addAction("Speichern unter...")

            copy_action.setEnabled(selection_exists)
            cut_action.setEnabled(selection_exists)
            paste_action.setEnabled(
                bool(
                    self._parse_clipboard_bytes(
                        QApplication.clipboard().text()
                    )
                )
            )
            petscii_action.setEnabled(byte_index is not None)

            copy_action.triggered.connect(self.copy_selection)
            cut_action.triggered.connect(self.cut_selection)
            paste_action.triggered.connect(self.paste_bytes)
            if byte_index is not None:
                petscii_action.triggered.connect(
                    lambda checked=False, index=byte_index:
                    self._open_petscii_dialog(index)
                )
            save_action.triggered.connect(
                lambda checked=False: self.saveRequested.emit(False)
            )
            save_as_action.triggered.connect(
                lambda checked=False: self.saveRequested.emit(True)
            )
            menu.exec_(event.globalPos())

        def _ensure_cursor_visible(self) -> None:
            row = self._cursor_index // self.BYTES_PER_ROW
            vertical = self.verticalScrollBar()
            page = max(1, vertical.pageStep())
            if row < vertical.value():
                vertical.setValue(row)
            elif row >= vertical.value() + page:
                vertical.setValue(row - page + 1)

        def _move_cursor(self, delta: int, *, extend: bool = False) -> None:
            maximum = max(0, len(self._data) - 1)
            target = max(0, min(maximum, self._cursor_index + delta))
            if not extend or self._selection_anchor is None:
                self._selection_anchor = target
            self._selection_end = target
            self._cursor_index = target
            self._active_nibble = 0
            self._ensure_cursor_visible()
            self.viewport().update()

        def _replace_nibble(self, digit: int) -> None:
            if not self._data:
                self._data.append(0)
                self._cursor_index = 0

            selection = self._selection_range()
            if selection is not None and selection[0] != selection[1]:
                self._cursor_index = selection[0]
            self._selection_anchor = self._cursor_index
            self._selection_end = self._cursor_index

            current = self._data[self._cursor_index]
            if self._active_nibble == 0:
                self._data[self._cursor_index] = (digit << 4) | (current & 0x0F)
                self._active_nibble = 1
            else:
                self._data[self._cursor_index] = (current & 0xF0) | digit
                self._active_nibble = 0
                if self._cursor_index + 1 < len(self._data):
                    self._cursor_index += 1
                    self._selection_anchor = self._cursor_index
                    self._selection_end = self._cursor_index

            self._set_modified(True)
            self._update_scrollbars()
            self._ensure_cursor_visible()
            self.viewport().update()
            self.dataChanged.emit()

        def keyPressEvent(self, event) -> None:
            if event.matches(QKeySequence.Copy):
                self.copy_selection()
                event.accept()
                return
            if event.matches(QKeySequence.Cut):
                self.cut_selection()
                event.accept()
                return
            if event.matches(QKeySequence.Paste):
                self.paste_bytes()
                event.accept()
                return

            text = event.text().upper()
            if len(text) == 1 and text in "0123456789ABCDEF":
                self._replace_nibble(int(text, 16))
                event.accept()
                return

            extend = bool(event.modifiers() & Qt.ShiftModifier)
            movements = {
                Qt.Key_Left: -1,
                Qt.Key_Right: 1,
                Qt.Key_Up: -self.BYTES_PER_ROW,
                Qt.Key_Down: self.BYTES_PER_ROW,
                Qt.Key_Home: -(self._cursor_index % self.BYTES_PER_ROW),
                Qt.Key_End: (
                    self.BYTES_PER_ROW
                    - 1
                    - self._cursor_index % self.BYTES_PER_ROW
                ),
            }
            if event.key() in movements:
                self._move_cursor(movements[event.key()], extend=extend)
                event.accept()
                return
                
            # -------------------------------------------------------------------
            # Navigation und Hexziffern sind die einzigen direkten Eingaben.
            # Andere druckbare Zeichen werden bewusst nicht an das Widget
            # weitergereicht, damit der Puffer stets gueltige Bytes enthaelt.
            # -------------------------------------------------------------------
            if event.text():
                event.accept()
                return
            super().keyPressEvent(event)

    class DocumentEditor(QWidget):
        """Ein Dateidokument mit Rohdaten-, Hex- und Hinweisansicht."""

        modification_changed = pyqtSignal(bool)
        assemble_requested = pyqtSignal(object)
        start_requested = pyqtSignal(object)
        assemble_generated_requested = pyqtSignal(object)
        start_generated_requested = pyqtSignal(object)
        coff_requested = pyqtSignal(object)
        context_help_requested = pyqtSignal(object, str, str)

        BASIC_EXTENSIONS     = {".bas", ".basic"}
        ASSEMBLER_EXTENSIONS = {".asm", ".s", ".a65", ".m68k", ".inc"}
        PASCAL_EXTENSIONS    = {".pas", ".pp"}
        C_EXTENSIONS         = {".c"}
        C_HEADER_EXTENSIONS  = {".h"}
        BINARY_EXTENSIONS    = {
            ".prg", ".amiga", ".adf", ".ram", ".bin",
            ".exe", ".o", ".obj", ".a", ".lib",
            ".exe", ".o", ".obj", ".a", ".lib",
        }

        def __init__(
            self,
            parent: QWidget,
            *,
            untitled_number : int,
            path            : Optional[Path] = None,
            text            : str = "",
            encoding        : str = "utf-8",
            newline         : str = "\n",
            raw_bytes       : Optional[bytes] = None,
            editor_font     : Optional[QFont] = None,
            dark_mode       : bool = False,
        ):
            super().__init__(parent)
            self.path = Path(path).resolve() if path is not None else None
            self.custom_display_name: Optional[str] = None
            self.untitled_number         = untitled_number
            self.encoding                = encoding
            self.newline                 = newline
            self._syncing_views          = False
            self._data_source            = "text"
            self._last_modified_state    = False
            self.assembled_program       = None
            self.assembled_program_path: Optional[Path] = None
            self.assembled_source_digest = ""
            self.assembled_assembly_digest = ""
            self.assembled_input_kind = ""
            self.assembled_target = ""
            self.build_target = "c64"
            self.amiga_cpu_model = "mk68000"
            self.amiga_fpu_model = "FPU: None"
            self.windows_graphics_backend = "Direct2D"
            self.windows_application_mode = "Console"
            self._syncing_build_target = False
            self._syncing_platform_profile = False
            self.generated_assembly_path: Optional[Path] = None
            self.generated_source_kind = "program"
            self.generated_linked_assembly_files: Tuple[str, ...] = ()
            self.generated_pe32_modules: Tuple[Tuple[str, str], ...] = ()
            self._syncing_generated_assembly = False

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

            self.views = QTabWidget(self)
            self.views.setDocumentMode(True)
            self.views.setMovable(False)

            fixed_font = QFont(editor_font) if editor_font is not None else QFont(
                "Courier New", 9
            )
            fixed_font.setFixedPitch(True)
            fixed_font.setStyleHint(QFont.Monospace)

            self.source_page = QWidget(self.views)
            source_layout = QVBoxLayout(self.source_page)
            source_layout.setContentsMargins(0, 0, 0, 0)
            source_layout.setSpacing(0)

            self.assembler_panel = QFrame(self.source_page)
            self.assembler_panel.setObjectName("assembler_action_panel")
            self.assembler_panel.setFrameShape(QFrame.StyledPanel)
            assembler_panel_layout = QHBoxLayout(self.assembler_panel)
            assembler_panel_layout.setContentsMargins(6, 5, 6, 5)
            assembler_panel_layout.setSpacing(6)

            self.assemble_button = QPushButton(
                "Assemble",
                self.assembler_panel,
            )
            self.assemble_button.setObjectName("assemble_button")
            self.assemble_button.setToolTip(
                "Quelltext in ein C64-PRG übersetzen"
            )
            self.assemble_button.clicked.connect(
                lambda checked=False: self.assemble_requested.emit(self)
            )

            self.start_assembled_button = QPushButton(
                "Start",
                self.assembler_panel,
            )
            self.start_assembled_button.setObjectName(
                "start_assembled_button"
            )
            self.start_assembled_button.setToolTip(
                "Das zuletzt assemblierte Programm in VICE starten"
            )
            self.start_assembled_button.setEnabled(False)
            self.start_assembled_button.clicked.connect(
                lambda checked=False: self.start_requested.emit(self)
            )

            # Kompakte Zielauswahl statt drei dauerhaft sichtbarer RadioButtons.
            # Die plattformspezifischen Zusatzfelder werden rechts daneben
            # dynamisch ein-/ausgeblendet.
            self.build_target_combo = QComboBox(self.assembler_panel)
            self.build_target_combo.setObjectName("build_target_combo")
            self.build_target_combo.addItems(("C= 64", "Amiga", "Windows PE32"))
            self.build_target_combo.setCurrentIndex(0)
            self.build_target_combo.setFixedWidth(132)
            self.build_target_combo.setToolTip(
                "Compiler-/Assemblerziel auswählen"
            )
            self.build_target_combo.currentTextChanged.connect(
                self.set_build_target
            )

            self.amiga_cpu_combo = QComboBox(self.assembler_panel)
            self.amiga_cpu_combo.setObjectName("amiga_cpu_combo")
            self.amiga_cpu_combo.addItems(AMIGA_CPU_MODELS)
            self.amiga_cpu_combo.setCurrentText(self.amiga_cpu_model)
            self.amiga_cpu_combo.setFixedWidth(104)
            self.amiga_cpu_combo.setToolTip("680x0-CPU-Profil für den Amiga-Assembler")
            self.amiga_cpu_combo.currentTextChanged.connect(self.set_amiga_cpu_model)

            self.amiga_fpu_combo = QComboBox(self.assembler_panel)
            self.amiga_fpu_combo.setObjectName("amiga_fpu_combo")
            self.amiga_fpu_combo.addItems(AMIGA_FPU_MODELS)
            self.amiga_fpu_combo.setCurrentText(self.amiga_fpu_model)
            self.amiga_fpu_combo.setFixedWidth(118)
            self.amiga_fpu_combo.currentTextChanged.connect(self.set_amiga_fpu_model)

            self.windows_graphics_combo = QComboBox(self.assembler_panel)
            self.windows_graphics_combo.setObjectName("windows_graphics_combo")
            self.windows_graphics_combo.addItem("Console")
            self.windows_graphics_combo.addItem("GUI")
            self.windows_graphics_combo.insertSeparator(2)
            self.windows_graphics_combo.addItem("Direct2D")
            self.windows_graphics_combo.addItem("Direct3D")
            self.windows_graphics_combo.setCurrentText(self.windows_application_mode)
            self.windows_graphics_combo.setFixedWidth(122)
            self.windows_graphics_combo.setToolTip(
                "Windows-Anwendungsart: Konsole, GUI, Direct2D oder Direct3D"
            )
            self.windows_graphics_combo.currentTextChanged.connect(
                self.set_windows_application_mode
            )

            self.assembly_status_label = QLabel(
                "Noch nicht assembliert",
                self.assembler_panel,
            )
            self.assembly_status_label.setObjectName(
                "assembly_status_label"
            )
            self.assembly_status_label.setTextFormat(Qt.PlainText)

            assembler_panel_layout.addWidget(self.assemble_button)
            assembler_panel_layout.addWidget(self.start_assembled_button)
            assembler_panel_layout.addSpacing(6)
            assembler_panel_layout.addWidget(self.build_target_combo)
            assembler_panel_layout.addSpacing(4)
            assembler_panel_layout.addWidget(self.amiga_cpu_combo)
            assembler_panel_layout.addWidget(self.amiga_fpu_combo)
            assembler_panel_layout.addWidget(self.windows_graphics_combo)
            assembler_panel_layout.addSpacing(6)
            assembler_panel_layout.addWidget(self.assembly_status_label, 1)
            source_layout.addWidget(self.assembler_panel)

            self.raw_editor = SourceTextEdit(self.source_page)
            self.raw_editor.setObjectName("raw_data_editor")
            self.raw_editor.setFont(fixed_font)
            self.raw_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
            self.raw_editor.assembler_help_requested.connect(
                self._show_assembler_help
            )
            self.raw_editor.context_help_requested.connect(
                lambda word: self._emit_context_help("source", word)
            )
            self.raw_editor.breakpoints_changed.connect(
                self._source_breakpoints_changed
            )
            self.raw_editor.setPlainText(text)
            self.raw_editor.document().setModified(False)
            source_layout.addWidget(self.raw_editor, 1)
            self.views.addTab(self.source_page, "Rohdaten")

            self.syntax_highlighter = AssemblerSyntaxHighlighter(
                self.raw_editor.document()
            )
            self.raw_editor.set_assembler_navigation_highlighter(
                self.syntax_highlighter
            )

            self.generated_assembly_page = QWidget(self.views)
            generated_assembly_layout = QVBoxLayout(
                self.generated_assembly_page
            )
            generated_assembly_layout.setContentsMargins(0, 0, 0, 0)
            generated_assembly_layout.setSpacing(0)

            self.generated_assembly_panel = QFrame(
                self.generated_assembly_page
            )
            self.generated_assembly_panel.setObjectName(
                "generated_assembler_action_panel"
            )
            self.generated_assembly_panel.setFrameShape(QFrame.StyledPanel)
            generated_assembly_panel_layout = QHBoxLayout(
                self.generated_assembly_panel
            )
            generated_assembly_panel_layout.setContentsMargins(6, 5, 6, 5)
            generated_assembly_panel_layout.setSpacing(6)

            self.assemble_generated_button = QPushButton(
                "Assemble",
                self.generated_assembly_panel,
            )
            self.assemble_generated_button.setObjectName(
                "assemble_generated_button"
            )
            self.assemble_generated_button.setToolTip(
                "Angezeigten Assemblercode in ein C64-PRG übersetzen"
            )
            self.assemble_generated_button.setEnabled(False)
            self.assemble_generated_button.clicked.connect(
                lambda checked=False: self.assemble_generated_requested.emit(
                    self
                )
            )

            self.start_generated_button = QPushButton(
                "Start",
                self.generated_assembly_panel,
            )
            self.start_generated_button.setObjectName(
                "start_generated_button"
            )
            self.start_generated_button.setToolTip(
                "Das aus dem ASM-Tab erzeugte Programm in VICE starten"
            )
            self.start_generated_button.setEnabled(False)
            self.start_generated_button.clicked.connect(
                lambda checked=False: self.start_generated_requested.emit(self)
            )

            self.generated_build_target_combo = QComboBox(
                self.generated_assembly_panel
            )
            self.generated_build_target_combo.setObjectName(
                "generated_build_target_combo"
            )
            self.generated_build_target_combo.addItems(
                ("C= 64", "Amiga", "Windows PE32")
            )
            self.generated_build_target_combo.setCurrentIndex(0)
            self.generated_build_target_combo.setFixedWidth(132)
            self.generated_build_target_combo.setToolTip(
                "Compiler-/Assemblerziel auswählen"
            )
            self.generated_build_target_combo.currentTextChanged.connect(
                self.set_build_target
            )

            self.generated_amiga_cpu_combo = QComboBox(self.generated_assembly_panel)
            self.generated_amiga_cpu_combo.setObjectName("generated_amiga_cpu_combo")
            self.generated_amiga_cpu_combo.addItems(AMIGA_CPU_MODELS)
            self.generated_amiga_cpu_combo.setCurrentText(self.amiga_cpu_model)
            self.generated_amiga_cpu_combo.setFixedWidth(104)
            self.generated_amiga_cpu_combo.currentTextChanged.connect(self.set_amiga_cpu_model)

            self.generated_amiga_fpu_combo = QComboBox(self.generated_assembly_panel)
            self.generated_amiga_fpu_combo.setObjectName("generated_amiga_fpu_combo")
            self.generated_amiga_fpu_combo.addItems(AMIGA_FPU_MODELS)
            self.generated_amiga_fpu_combo.setCurrentText(self.amiga_fpu_model)
            self.generated_amiga_fpu_combo.setFixedWidth(118)
            self.generated_amiga_fpu_combo.currentTextChanged.connect(self.set_amiga_fpu_model)

            self.generated_windows_graphics_combo = QComboBox(self.generated_assembly_panel)
            self.generated_windows_graphics_combo.setObjectName("generated_windows_graphics_combo")
            self.generated_windows_graphics_combo.addItem("Console")
            self.generated_windows_graphics_combo.addItem("GUI")
            self.generated_windows_graphics_combo.insertSeparator(2)
            self.generated_windows_graphics_combo.addItem("Direct2D")
            self.generated_windows_graphics_combo.addItem("Direct3D")
            self.generated_windows_graphics_combo.setCurrentText(
                self.windows_application_mode
            )
            self.generated_windows_graphics_combo.setFixedWidth(122)
            self.generated_windows_graphics_combo.currentTextChanged.connect(
                self.set_windows_application_mode
            )

            self.coff_object_button = QPushButton("COFF32 .o", self.generated_assembly_panel)
            self.coff_object_button.setObjectName("coff_object_button")
            self.coff_object_button.setToolTip(
                "Angezeigten PE32-Assemblercode als relocierbares COFF32-Objekt speichern"
            )
            self.coff_object_button.clicked.connect(
                lambda checked=False: self.coff_requested.emit(self)
            )

            self.generated_assembly_status_label = QLabel(
                "ASM-Daten werden beim Kompilieren erzeugt",
                self.generated_assembly_panel,
            )
            self.generated_assembly_status_label.setObjectName(
                "generated_assembly_status_label"
            )
            self.generated_assembly_status_label.setTextFormat(Qt.PlainText)

            generated_assembly_panel_layout.addWidget(
                self.assemble_generated_button
            )
            generated_assembly_panel_layout.addWidget(
                self.start_generated_button
            )
            generated_assembly_panel_layout.addSpacing(6)
            generated_assembly_panel_layout.addWidget(
                self.generated_build_target_combo
            )
            generated_assembly_panel_layout.addSpacing(4)
            generated_assembly_panel_layout.addWidget(self.generated_amiga_cpu_combo)
            generated_assembly_panel_layout.addWidget(self.generated_amiga_fpu_combo)
            generated_assembly_panel_layout.addWidget(self.generated_windows_graphics_combo)
            generated_assembly_panel_layout.addWidget(self.coff_object_button)
            generated_assembly_panel_layout.addSpacing(6)
            generated_assembly_panel_layout.addWidget(
                self.generated_assembly_status_label,
                1,
            )
            generated_assembly_layout.addWidget(self.generated_assembly_panel)

            self.generated_assembly_editor = SourceTextEdit(
                self.generated_assembly_page
            )
            self.generated_assembly_editor.setObjectName(
                "generated_assembly_editor"
            )
            self.generated_assembly_editor.setFont(fixed_font)
            self.generated_assembly_editor.setLineWrapMode(
                QPlainTextEdit.NoWrap
            )
            self.generated_assembly_editor.setPlaceholderText(
                "Nach dem Kompilieren werden hier die ASM-Daten angezeigt."
            )
            self.generated_assembly_editor.assembler_help_requested.connect(
                self._show_assembler_help
            )
            self.generated_assembly_editor.context_help_requested.connect(
                lambda word: self._emit_context_help("assembler", word)
            )
            generated_assembly_layout.addWidget(
                self.generated_assembly_editor,
                1,
            )
            self.views.addTab(self.generated_assembly_page, "ASM")

            self.generated_assembly_highlighter = AssemblerSyntaxHighlighter(
                self.generated_assembly_editor.document()
            )
            self.generated_assembly_highlighter.set_enabled(True)
            self.generated_assembly_editor.set_assembler_navigation_highlighter(
                self.generated_assembly_highlighter
            )
            self.generated_assembly_editor.set_assembler_completion_enabled(
                True
            )
            self.generated_assembly_editor.set_assembler_navigation_enabled(
                True
            )
            self.generated_assembly_editor.set_assembler_target(
                self.build_target
            )

            self.hex_editor = HexEditor(self.views)
            self.hex_editor.set_c64_font_size(fixed_font.pointSize())
            if raw_bytes is None:
                raw_bytes = self.text_for_saving().encode(self.encoding)
            self.hex_editor.set_data(raw_bytes, modified=False)
            self.hex_editor.dataChanged.connect(self._hex_data_changed)
            self.hex_editor.modificationChanged.connect(
                self._view_modification_changed
            )
            self.hex_editor.saveRequested.connect(self._request_hex_save)
            self.views.addTab(self.hex_editor, "Hex-Editor")

            self.hints_editor = SourceTextEdit(self.views)
            self.hints_editor.setObjectName("hints_editor")
            self.hints_editor.setFont(fixed_font)
            self.hints_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
            self.hints_editor.setReadOnly(True)
            self.hints_editor.context_help_requested.connect(
                lambda word: self._emit_context_help("source", word)
            )
            self.hints_editor.setPlaceholderText(
                "Hinweise werden später an dieser Stelle angezeigt."
            )
            self.views.addTab(self.hints_editor, "Hinweise")

            self.raw_editor.textChanged.connect(self._raw_text_changed)
            self.raw_editor.document().modificationChanged.connect(
                self._view_modification_changed
            )
            self.generated_assembly_editor.textChanged.connect(
                self._generated_assembly_text_changed
            )

            self.update_syntax_highlighting()

            if (
                self.path is not None
                and self.path.suffix.lower() in self.BINARY_EXTENSIONS
            ):
                self.views.setCurrentWidget(self.hex_editor)

            layout.addWidget(self.views)
            self.set_dark_mode(dark_mode)

        @property
        def display_name(self) -> str:
            if self.custom_display_name:
                return self.custom_display_name
            if self.path is not None:
                return self.path.name
            return f"Unbenannt {self.untitled_number}"

        @property
        def effective_suffix(self) -> str:
            """Dateiendung auch für noch nicht gespeicherte Dokumente."""
            if self.path is not None:
                return self.path.suffix.casefold()
            if self.custom_display_name:
                return Path(self.custom_display_name).suffix.casefold()
            return ""

        def source_language(self) -> str:
            suffix = self.effective_suffix
            if suffix in {".bas", ".basic"}:
                return "basic"
            if suffix in self.ASSEMBLER_EXTENSIONS:
                return "assembler"
            if suffix in self.PASCAL_EXTENSIONS:
                return "pascal"
            if suffix in self.C_EXTENSIONS | self.C_HEADER_EXTENSIONS:
                return "c"
            return "text"

        def _emit_context_help(self, view_kind: str, word: str) -> None:
            language = (
                "assembler"
                if view_kind == "assembler"
                else self.source_language()
            )
            self.context_help_requested.emit(self, language, word)

        def active_text_editor(self) -> Optional[SourceTextEdit]:
            current = self.views.currentWidget()
            if current is self.source_page:
                return self.raw_editor
            if current is self.generated_assembly_page:
                return self.generated_assembly_editor
            if current is self.hints_editor:
                return self.hints_editor
            return None

        def current_help_context(self) -> Tuple[str, str]:
            editor = self.active_text_editor() or self.raw_editor
            language = (
                "assembler"
                if editor is self.generated_assembly_editor
                else self.source_language()
            )
            return language, editor.help_word_at_cursor()

        @property
        def is_modified(self) -> bool:
            return (
                self.raw_editor.document().isModified()
                or self.hex_editor.is_modified
            )

        def text_for_saving(self) -> str:
            text = self.raw_editor.toPlainText()
            if self.newline != "\n":
                text = text.replace("\n", self.newline)
            return text

        def data_for_saving(self) -> bytes:
            if self._data_source == "hex":
                return self.hex_editor.data()
            return self.text_for_saving().encode(self.encoding)

        def mark_saved(self) -> None:
            self.raw_editor.document().setModified(False)
            self.hex_editor.mark_saved()
            self._view_modification_changed(False)

        def focus_preferred_editor(self) -> None:
            if (
                self.path is not None
                and self.path.suffix.lower() in self.BINARY_EXTENSIONS
            ):
                self.views.setCurrentWidget(self.hex_editor)
                self.hex_editor.setFocus()
            else:
                self.views.setCurrentWidget(self.source_page)
                self.raw_editor.setFocus()

        def _view_modification_changed(self, _modified: bool) -> None:
            if self._syncing_views:
                return
            modified = self.is_modified
            if self._last_modified_state != modified:
                self._last_modified_state = modified
                self.modification_changed.emit(modified)

        def _source_breakpoints_changed(self) -> None:
            if self.build_target == "pe32" and self.is_pascal_document:
                self.invalidate_assembly_result("Breakpoints geändert")
                count = len(self.raw_editor.breakpoint_lines())
                if count:
                    self.assembly_status_label.setText(
                        f"{count} Breakpoint(s) – erneut Compile/Assemble ausführen"
                    )

        def _raw_text_changed(self) -> None:
            if self._syncing_views:
                return
            self.invalidate_assembly_result("Quelltext geändert")
            if (
                self.is_basic_document
                or self.is_pascal_document
                or self.is_c_document
            ) and self.generated_assembly_editor.toPlainText().strip():
                self.assemble_generated_button.setEnabled(False)
                self.generated_assembly_status_label.setText(
                    "Quelltext geändert – erneut Compile ausführen"
                )
            try:
                data = self.text_for_saving().encode(self.encoding)
            except UnicodeError:
                self._view_modification_changed(True)
                return

            self._syncing_views = True
            try:
                self.hex_editor.set_data(data, modified=False)
                self._data_source = "text"
            finally:
                self._syncing_views = False
            self._view_modification_changed(True)

        def _generated_assembly_text_changed(self) -> None:
            if self._syncing_generated_assembly:
                return
            self.invalidate_assembly_result("Assemblercode geändert")
            has_source = bool(
                self.generated_assembly_editor.toPlainText().strip()
            )
            self.assemble_generated_button.setEnabled(has_source)
            if has_source:
                self.generated_assembly_status_label.setText(
                    "Assemblercode geändert"
                )

        def _hex_data_changed(self) -> None:
            if self._syncing_views:
                return
            data = self.hex_editor.data()
            try:
                text = data.decode(self.encoding)
            except UnicodeError:
                text = data.decode("latin-1")

            self._syncing_views = True
            try:
                self.raw_editor.setPlainText(text)
                self.raw_editor.document().setModified(False)
                self._data_source = "hex"
            finally:
                self._syncing_views = False
            self._view_modification_changed(True)

        def _request_hex_save(self, save_as: bool) -> None:
            window = self.window()
            if not hasattr(window, "_save_document"):
                return
            if hasattr(window, "document_tabs"):
                window.document_tabs.setCurrentWidget(self)
            window._save_document(self, save_as=bool(save_as))

        def set_build_target(self, target: str) -> None:
            value = str(target).strip().casefold()
            if value in {"pe32", "windows", "windows pe32", "windowspe32"}:
                normalized = "pe32"
            elif value == "amiga":
                normalized = "amiga"
            elif value in {"c64", "c-64", "c=64", "c= 64", "c 64"}:
                normalized = "c64"
            else:
                normalized = "c64"
            if self.is_basic_document and normalized != "c64":
                normalized = "c64"
            if self._syncing_build_target:
                return
            changed = normalized != self.build_target
            self._syncing_build_target = True
            try:
                self.build_target = normalized
                display_name = {
                    "c64": "C= 64",
                    "amiga": "Amiga",
                    "pe32": "Windows PE32",
                }[normalized]
                self.build_target_combo.setCurrentText(display_name)
                self.generated_build_target_combo.setCurrentText(display_name)
            finally:
                self._syncing_build_target = False

            self.raw_editor.set_assembler_target(normalized)
            self.generated_assembly_editor.set_assembler_target(normalized)
            self.raw_editor.set_amiga_profile(
                self.amiga_cpu_model, self.amiga_fpu_model
            )
            self.generated_assembly_editor.set_amiga_profile(
                self.amiga_cpu_model, self.amiga_fpu_model
            )
            self._update_platform_profile_visibility()
            if changed:
                self.invalidate_assembly_result("Compilerziel geändert")
                self.generated_assembly_path = None
                self._syncing_generated_assembly = True
                try:
                    self.generated_assembly_editor.clear()
                    self.generated_assembly_editor.document().setModified(False)
                finally:
                    self._syncing_generated_assembly = False
                self.assemble_generated_button.setEnabled(False)
                target_name = self._build_target_name()
                self.generated_assembly_status_label.setText(
                    f"ASM-Daten für {target_name} werden beim Kompilieren erzeugt"
                )
            self.update_syntax_highlighting()

        def set_amiga_cpu_model(self, value: str) -> None:
            try:
                normalized = normalize_amiga_cpu_model(value)
            except ValueError:
                return
            if self._syncing_platform_profile:
                return
            changed = normalized != self.amiga_cpu_model
            self._syncing_platform_profile = True
            try:
                self.amiga_cpu_model = normalized
                self.amiga_cpu_combo.setCurrentText(normalized)
                self.generated_amiga_cpu_combo.setCurrentText(normalized)
            finally:
                self._syncing_platform_profile = False
            self.raw_editor.set_amiga_profile(normalized, self.amiga_fpu_model)
            self.generated_assembly_editor.set_amiga_profile(
                normalized, self.amiga_fpu_model
            )
            if changed and self.build_target == "amiga":
                self.invalidate_assembly_result("Amiga-CPU geändert")
                self.assemble_generated_button.setEnabled(
                    bool(self.generated_assembly_editor.toPlainText().strip())
                )
                self.assembly_status_label.setText(
                    f"CPU: {normalized} – erneut Compile/Assemble ausführen"
                )

        def set_amiga_fpu_model(self, value: str) -> None:
            try:
                normalized = normalize_amiga_fpu_model(value)
            except ValueError:
                return
            if self._syncing_platform_profile:
                return
            changed = normalized != self.amiga_fpu_model
            self._syncing_platform_profile = True
            try:
                self.amiga_fpu_model = normalized
                self.amiga_fpu_combo.setCurrentText(normalized)
                self.generated_amiga_fpu_combo.setCurrentText(normalized)
            finally:
                self._syncing_platform_profile = False
            self.raw_editor.set_amiga_profile(self.amiga_cpu_model, normalized)
            self.generated_assembly_editor.set_amiga_profile(
                self.amiga_cpu_model, normalized
            )
            if changed and self.build_target == "amiga":
                self.invalidate_assembly_result("Amiga-FPU geändert")
                self.assembly_status_label.setText(
                    f"{normalized} – erneut Compile/Assemble ausführen"
                )

        def set_windows_application_mode(self, value: str) -> None:
            try:
                normalized = normalize_windows_application_mode(value)
            except ValueError:
                return
            if self._syncing_platform_profile:
                return
            changed = normalized != self.windows_application_mode
            self._syncing_platform_profile = True
            try:
                self.windows_application_mode = normalized
                if normalized in WINDOWS_GRAPHICS_BACKENDS:
                    self.windows_graphics_backend = normalized
                self.windows_graphics_combo.setCurrentText(normalized)
                self.generated_windows_graphics_combo.setCurrentText(normalized)
            finally:
                self._syncing_platform_profile = False
            if changed and self.build_target == "pe32":
                self.invalidate_assembly_result("Windows-Anwendungsmodus geändert")
                self.assembly_status_label.setText(
                    f"{normalized} – erneut Compile/Assemble ausführen"
                )

        def set_windows_graphics_backend(self, value: str) -> None:
            """Kompatibilitätshelfer für ältere Aufrufer und gespeicherte Zustände."""
            try:
                normalized = normalize_windows_graphics_backend(value)
            except ValueError:
                return
            self.set_windows_application_mode(normalized)

        def _update_platform_profile_visibility(self) -> None:
            is_amiga = self.build_target == "amiga"
            is_pe32 = self.build_target == "pe32"
            for widget in (
                self.amiga_cpu_combo, self.amiga_fpu_combo,
                self.generated_amiga_cpu_combo, self.generated_amiga_fpu_combo,
            ):
                widget.setVisible(is_amiga)
            for widget in (
                self.windows_graphics_combo, self.generated_windows_graphics_combo
            ):
                widget.setVisible(is_pe32)
            self.coff_object_button.setVisible(
                is_pe32 and (self.is_pascal_document or self.is_c_document)
            )

        def _build_target_name(self) -> str:
            if self.build_target == "amiga":
                return f"Amiga {self.amiga_cpu_model}"
            if self.build_target == "pe32":
                return "Windows PE32"
            return "C-64"

        def _build_emulator_name(self) -> str:
            if self.build_target == "amiga":
                return "WinUAE"
            if self.build_target == "pe32":
                return "Windows"
            return "VICE"

        def _build_output_name(self) -> str:
            if self.build_target == "amiga":
                return "Amiga-Hunk-Programm"
            if self.build_target == "pe32":
                return "PE32-EXE"
            return "C64-PRG"

        def update_syntax_highlighting(self) -> None:
            suffix = self.effective_suffix
            is_basic = suffix in self.BASIC_EXTENSIONS
            is_assembler = suffix in self.ASSEMBLER_EXTENSIONS
            is_pascal = suffix in self.PASCAL_EXTENSIONS
            is_c = suffix in self.C_EXTENSIONS
            is_c_header = suffix in self.C_HEADER_EXTENSIONS
            is_compiled_language = is_basic or is_pascal or is_c
            has_generated_assembly = bool(
                self.generated_assembly_editor.toPlainText().strip()
            )

            assembly_tab_index = self.views.indexOf(
                self.generated_assembly_page
            )
            if assembly_tab_index >= 0:
                # Der ASM-Tab erscheint erst nach erfolgreichem Compile.
                self.views.setTabVisible(
                    assembly_tab_index,
                    is_compiled_language and has_generated_assembly,
                )

            self.assembler_panel.setVisible(
                is_assembler or is_compiled_language
            )
            # C/Pascal: Compile im Quelltext-Tab. Assemble/Start erscheinen
            # nach dem Compile im erzeugten ASM-Tab. Reiner ASM-Code zeigt
            # Assemble/Start direkt über dem Quelltext.
            self.start_assembled_button.setVisible(is_assembler)
            self.syntax_highlighter.set_enabled(is_assembler)
            self.syntax_highlighter.set_pascal_enabled(is_pascal)
            self.syntax_highlighter.set_c_enabled(is_c or is_c_header)
            self.raw_editor.set_assembler_completion_enabled(is_assembler)
            self.raw_editor.set_assembler_navigation_enabled(is_assembler)
            self.raw_editor.set_assembler_target(self.build_target)
            self.generated_assembly_editor.set_assembler_target(
                self.build_target
            )
            self._update_platform_profile_visibility()
            target_name = self._build_target_name()
            emulator_name = self._build_emulator_name()
            output_name = self._build_output_name()
            self.start_assembled_button.setToolTip(
                f"Das zuletzt erzeugte Programm in {emulator_name} starten"
            )
            self.start_generated_button.setToolTip(
                f"Das aus dem ASM-Tab erzeugte Programm in {emulator_name} starten"
            )
            self.assemble_generated_button.setText("Assemble")
            self.assemble_generated_button.setToolTip(
                f"Angezeigten {target_name}-Assemblercode in ein "
                f"{output_name} übersetzen"
            )
            # BASIC bleibt wie bisher auf C64 beschränkt. Bei den ComboBoxen
            # werden deshalb die beiden anderen Ziele deaktiviert.
            for combo in (
                self.build_target_combo,
                self.generated_build_target_combo,
            ):
                model = combo.model()
                for index in (1, 2):
                    item = model.item(index) if hasattr(model, "item") else None
                    if item is not None:
                        item.setEnabled(not is_basic)
            if is_basic and self.build_target != "c64":
                self.set_build_target("c64")

            if is_basic:
                self.assemble_button.setText("Compile")
                self.assemble_button.setToolTip(
                    "C64 BASIC in MOS-6510-Assembler übersetzen"
                )
                if not has_generated_assembly:
                    self.assembly_status_label.setText("Noch nicht kompiliert")
            elif is_pascal:
                self.assemble_button.setText("Compile")
                self.assemble_button.setToolTip(
                    f"Pascal mit ANTLR in {target_name}-Assembler übersetzen"
                )
                if not has_generated_assembly:
                    self.assembly_status_label.setText("Noch nicht kompiliert")
            elif is_c:
                self.assemble_button.setText("Compile")
                self.assemble_button.setToolTip(
                    f"C mit ANTLR in {target_name}-Assembler übersetzen"
                )
                if not has_generated_assembly:
                    self.assembly_status_label.setText("Noch nicht kompiliert")
            else:
                self.assemble_button.setText("Assemble")
                self.assemble_button.setToolTip(
                    f"{target_name}-Assemblerquelltext in ein "
                    f"{output_name} übersetzen"
                )
                if is_assembler and self.assembled_program is None:
                    self.assembly_status_label.setText("Noch nicht assembliert")

        @property
        def is_basic_document(self) -> bool:
            return self.effective_suffix in self.BASIC_EXTENSIONS

        @property
        def is_assembler_document(self) -> bool:
            return self.effective_suffix in self.ASSEMBLER_EXTENSIONS

        @property
        def is_pascal_document(self) -> bool:
            return self.effective_suffix in self.PASCAL_EXTENSIONS

        @property
        def is_c_document(self) -> bool:
            return self.effective_suffix in self.C_EXTENSIONS

        @property
        def is_build_document(self) -> bool:
            return (
                self.is_basic_document
                or self.is_assembler_document
                or self.is_pascal_document
                or self.is_c_document
            )

        def invalidate_assembly_result(self, reason: str = "") -> None:
            had_result = bool(
                self.assembled_program is not None
                or self.assembled_program_path is not None
                or self.assembled_source_digest
                or self.assembled_assembly_digest
            )
            self.assembled_program = None
            self.assembled_program_path = None
            self.assembled_source_digest = ""
            self.assembled_assembly_digest = ""
            self.assembled_input_kind = ""
            self.assembled_target = ""
            self.start_assembled_button.setEnabled(False)
            self.start_generated_button.setEnabled(False)
            if reason and had_result and self.is_build_document:
                self.assembly_status_label.setText(reason)
                if self.generated_assembly_path is not None:
                    self.generated_assembly_status_label.setText(reason)

        def set_generated_assembly(
            self,
            assembly: str,
            assembly_path: Path,
            *,
            select_tab: bool = False,
        ) -> None:
            self.generated_assembly_path = Path(assembly_path).resolve()
            self._syncing_generated_assembly = True
            try:
                self.generated_assembly_editor.setPlainText(assembly)
                self.generated_assembly_editor.document().setModified(False)
            finally:
                self._syncing_generated_assembly = False
            self.assemble_generated_button.setEnabled(bool(assembly.strip()))
            self.generated_assembly_status_label.setText(
                f"Erzeugt: {self.generated_assembly_path.name}"
            )
            assembly_tab_index = self.views.indexOf(
                self.generated_assembly_page
            )
            if assembly_tab_index >= 0:
                self.views.setTabVisible(assembly_tab_index, True)
            if select_tab:
                self.views.setCurrentWidget(self.generated_assembly_page)

        def generated_assembly_digest(self) -> str:
            return hashlib.sha256(
                self.generated_assembly_editor.toPlainText().encode("utf-8")
            ).hexdigest()

        def set_assembly_result(
            self,
            program,
            output_path: Path,
            source_digest: str,
            assembly_digest: str = "",
            input_kind: str = "source",
        ) -> None:
            self.assembled_program = program
            self.assembled_program_path = Path(output_path).resolve()
            self.assembled_source_digest = str(source_digest)
            self.assembled_assembly_digest = str(assembly_digest)
            self.assembled_input_kind = str(input_kind)
            self.assembled_target = self.build_target
            self.start_assembled_button.setEnabled(True)
            self.assembly_status_label.setText(
                f"Erzeugt: {self.assembled_program_path.name}"
            )
            has_generated_assembly = bool(
                self.generated_assembly_editor.toPlainText().strip()
            )
            self.start_generated_button.setEnabled(has_generated_assembly)
            if has_generated_assembly:
                self.generated_assembly_status_label.setText(
                    f"Erzeugt: {self.assembled_program_path.name}"
                )

        def show_assembly_error(
            self,
            message: str,
            line: int = 0,
            status_text: str = "Assemblerfehler",
        ) -> None:
            self.invalidate_assembly_result()
            self.assembly_status_label.setText(status_text)
            self.hints_editor.setPlainText(message)
            self.views.setCurrentWidget(self.source_page)
            if line > 0:
                block = self.raw_editor.document().findBlockByNumber(line - 1)
                if block.isValid():
                    cursor = QTextCursor(block)
                    cursor.select(QTextCursor.LineUnderCursor)
                    self.raw_editor.setTextCursor(cursor)
                    self.raw_editor.centerCursor()
            self.raw_editor.setFocus(Qt.OtherFocusReason)

        def show_generated_assembly_error(
            self,
            message: str,
            line: int = 0,
            status_text: str = "Assemblerfehler",
        ) -> None:
            self.invalidate_assembly_result()
            self.assembly_status_label.setText(status_text)
            self.generated_assembly_status_label.setText(status_text)
            self.hints_editor.setPlainText(message)
            self.views.setCurrentWidget(self.generated_assembly_page)
            if line > 0:
                block = (
                    self.generated_assembly_editor.document()
                    .findBlockByNumber(line - 1)
                )
                if block.isValid():
                    cursor = QTextCursor(block)
                    cursor.select(QTextCursor.LineUnderCursor)
                    self.generated_assembly_editor.setTextCursor(cursor)
                    self.generated_assembly_editor.centerCursor()
            self.generated_assembly_editor.setFocus(Qt.OtherFocusReason)

        def _show_assembler_help(self, mnemonic: str, help_text: str) -> None:
            window = self.window()
            if hasattr(window, "_show_message_box"):
                window._show_message_box(
                    QMessageBox.Information,
                    f"Assembler-Befehl {mnemonic}",
                    help_text,
                )
            else:
                QMessageBox.information(
                    self,
                    f"Assembler-Befehl {mnemonic}",
                    help_text,
                )

        def set_editor_font(self, font: QFont) -> None:
            for editor in (
                self.raw_editor,
                self.generated_assembly_editor,
                self.hints_editor,
            ):
                editor.setFont(QFont(font))
                editor.update_line_number_area_width(0)
            self.hex_editor.set_c64_font_size(font.pointSize())

        def set_dark_mode(self, enabled: bool) -> None:
            enabled = bool(enabled)
            for editor in (
                self.raw_editor,
                self.generated_assembly_editor,
                self.hints_editor,
            ):
                palette = QPalette(QApplication.palette())
                if enabled:
                    palette.setColor(QPalette.Base, QColor(0, 0, 128))
                    palette.setColor(QPalette.Text, QColor(255, 255, 0))
                    palette.setColor(QPalette.Highlight, QColor(0, 90, 170))
                    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
                    if hasattr(QPalette, "PlaceholderText"):
                        palette.setColor(
                            QPalette.PlaceholderText,
                            QColor(210, 210, 80),
                        )
                else:
                    # Die Editorfarben werden absichtlich explizit gesetzt.
                    # Nur so sind neu erzeugte oder gerade geoeffnete Tabs
                    # unabhaengig von geerbten Windows-/Qt-Paletten sofort
                    # korrekt dargestellt.
                    palette.setColor(QPalette.Base, QColor(255, 255, 255))
                    palette.setColor(QPalette.Text, QColor(0, 0, 0))
                    palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
                    palette.setColor(
                        QPalette.HighlightedText,
                        QColor(255, 255, 255),
                    )
                    if hasattr(QPalette, "PlaceholderText"):
                        palette.setColor(
                            QPalette.PlaceholderText,
                            QColor(100, 100, 100),
                        )
                editor.setPalette(palette)
                editor.viewport().setPalette(palette)
                editor.set_gutter_dark_mode(enabled)
                editor.viewport().update()

            hex_palette = QPalette(QApplication.palette())
            if enabled:
                hex_palette.setColor(QPalette.Base, QColor(0, 0, 128))
                hex_palette.setColor(QPalette.Text, QColor(255, 255, 0))
                hex_palette.setColor(QPalette.Highlight, QColor(0, 90, 170))
                hex_palette.setColor(
                    QPalette.HighlightedText,
                    QColor(255, 255, 255),
                )
            else:
                hex_palette.setColor(QPalette.Base, QColor(255, 255, 255))
                hex_palette.setColor(QPalette.Text, QColor(0, 0, 0))
                hex_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
                hex_palette.setColor(
                    QPalette.HighlightedText,
                    QColor(255, 255, 255),
                )
            self.hex_editor.setPalette(hex_palette)
            self.hex_editor.viewport().setPalette(hex_palette)
            self.hex_editor.viewport().update()

            self.syntax_highlighter.set_dark_mode(enabled)
            self.generated_assembly_highlighter.set_dark_mode(enabled)

    class DismWorker(QObject):
        """Fuehrt die unveraenderte d64info-Programmlogik ausserhalb der GUI aus."""

        finished = pyqtSignal(int, str, str)

        def __init__(self, arguments: list[str]):
            super().__init__()
            self.arguments = list(arguments)

        def run(self) -> None:
            import io
            from contextlib import redirect_stderr, redirect_stdout

            standard_output = io.StringIO()
            error_output = io.StringIO()
            exit_code = 1

            try:
                with redirect_stdout(standard_output), redirect_stderr(error_output):
                    exit_code = int(_D64INFO_MODULE.main(self.arguments))
            except Exception as exc:
                print(
                    f"Fehler: {type(exc).__name__}: {exc}",
                    file=error_output,
                )

            self.finished.emit(
                exit_code,
                standard_output.getvalue(),
                error_output.getvalue(),
            )

    CHM_ROLE_LOCAL = Qt.UserRole + 100
    CHM_ROLE_TITLE = Qt.UserRole + 101

    class ChmSearchTab(QWidget):
        search_requested = pyqtSignal(str)

        def __init__(self, placeholder: str, parent=None):
            super().__init__(parent)
            self.search_edit = QLineEdit(self)
            self.search_edit.setPlaceholderText(placeholder)
            self.search_edit.setClearButtonEnabled(True)

            self.search_button = QPushButton(self)
            self.search_button.setObjectName("chm_search_button")
            self.search_button.setIcon(self._magnifier_icon())
            self.search_button.setIconSize(QSize(18, 18))
            self.search_button.setFixedWidth(36)
            self.search_button.setToolTip("Ersten Treffer suchen")

            self.tree = QTreeWidget(self)
            self.tree.setHeaderHidden(True)
            self.tree.setUniformRowHeights(True)

            search_layout = QHBoxLayout()
            search_layout.setContentsMargins(0, 0, 0, 0)
            search_layout.addWidget(self.search_edit, 1)
            search_layout.addWidget(self.search_button)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.addLayout(search_layout)
            layout.addWidget(self.tree, 1)

            self.search_edit.returnPressed.connect(self.emit_search)
            self.search_button.clicked.connect(self.emit_search)

        def _magnifier_icon(self) -> QIcon:
            pixmap = QPixmap(22, 22)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            color = self.palette().color(QPalette.ButtonText)
            painter.setPen(
                QPen(color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            )
            painter.drawEllipse(4, 3, 10, 10)
            painter.drawLine(13, 12, 19, 18)
            painter.end()
            return QIcon(pixmap)

        def emit_search(self) -> None:
            self.search_requested.emit(self.search_edit.text().strip())

    class ChmWebPage(QWebEnginePage):
        """QWebEnginePage fuer lokale CHM-Inhalte."""

        def acceptNavigationRequest(
            self,
            url: QUrl,
            navigation_type,
            is_main_frame: bool,
        ) -> bool:
            if (
                is_main_frame
                and url.scheme().lower() in ("mk", "ms-its")
            ):
                view = self.view()
                dialog = view.window() if view is not None else None
                if dialog is not None and hasattr(dialog, "load_local"):
                    dialog.load_local(url.toString())
                return False
            if (
                is_main_frame
                and navigation_type == QWebEnginePage.NavigationTypeLinkClicked
                and url.scheme().lower() in ("http", "https", "mailto")
            ):
                QDesktopServices.openUrl(url)
                return False
            return super().acceptNavigationRequest(
                url,
                navigation_type,
                is_main_frame,
            )

    class ChmSourceDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Seiten-Quelltext")
            self.resize(900, 650)
            self.editor = QPlainTextEdit(self)
            self.editor.setReadOnly(True)
            self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
            close_button = QPushButton("Schließen", self)
            close_button.clicked.connect(self.accept)
            button_layout = QHBoxLayout()
            button_layout.addStretch(1)
            button_layout.addWidget(close_button)
            layout = QVBoxLayout(self)
            layout.addWidget(self.editor, 1)
            layout.addLayout(button_layout)

    class ChmViewerDialog(QDialog):
        """In die D64-Anwendung integrierter CHM-Hilfedialog."""

        CONTENT_THEME_STYLE_ID = "d64-chm-content-theme"

        def __init__(self, parent=None, dark_mode: bool = False):
            super().__init__(parent)
            # Der Modus muss feststehen, bevor WebEngine oder ein sichtbares
            # Dialog-Widget erzeugt wird. Andernfalls zeichnet Chromium beim
            # ersten Anzeigen kurz seine weisse Standardflaeche.
            self.dark_mode_enabled = bool(dark_mode)
            self.setObjectName("chm_viewer_dialog")
            self.setWindowTitle("CHM Viewer")
            self.setWindowFlags(
                self.windowFlags()
                | Qt.WindowMinMaxButtonsHint
                | Qt.WindowSystemMenuHint
            )
            self.resize(1180, 760)
            self.setMinimumSize(800, 500)

            self.settings = QSettings(
                ExplorerWindow.ORGANIZATION,
                ExplorerWindow.APPLICATION,
            )
            self.temporary = None
            self.content_root = None
            self.chm_path = None
            self.home_local = ""
            self.source_dialogs = []
            self.pending_context_language = ""
            self.pending_context_word = ""

            self.create_actions()
            self.create_menu()
            self.create_toolbar()
            self.create_content()
            self.create_statusbar()
            self.connect_signals()
            self.restore_state()
            self.update_navigation()

        # ----- Aufbau --------------------------------------------------

        def create_actions(self) -> None:
            style = self.style()
            self.open_action = QAction(
                style.standardIcon(QStyle.SP_DialogOpenButton),
                "Hilfe öffnen …",
                self,
            )
            self.open_action.setShortcut(QKeySequence.Open)
            self.open_action.setToolTip("CHM-Datei öffnen")

            self.quit_action = QAction("Programm beenden", self)
            self.quit_action.setShortcut(QKeySequence.Quit)
            self.copy_action = QAction("Kopieren", self)
            self.copy_action.setShortcut(QKeySequence.Copy)
            self.source_action = QAction("Seiten Quelltext", self)
            self.source_action.setShortcut(QKeySequence("Ctrl+U"))
            self.about_action = QAction("Über …", self)

            self.home_action = QAction(
                style.standardIcon(QStyle.SP_DirHomeIcon),
                "Start",
                self,
            )
            self.home_action.setToolTip("index.html anzeigen")
            self.back_action = QAction(
                style.standardIcon(QStyle.SP_ArrowBack),
                "Zurück",
                self,
            )
            self.forward_action = QAction(
                style.standardIcon(QStyle.SP_ArrowForward),
                "Vor",
                self,
            )

        def create_menu(self) -> None:
            self.menu_bar = QMenuBar(self)
            file_menu = self.menu_bar.addMenu("Datei")
            file_menu.addAction(self.open_action)
            file_menu.addSeparator()
            file_menu.addAction(self.quit_action)

            edit_menu = self.menu_bar.addMenu("Bearbeiten")
            edit_menu.addAction(self.copy_action)
            edit_menu.addAction(self.source_action)

            help_menu = self.menu_bar.addMenu("Hilfe")
            help_menu.addAction(self.about_action)

        def create_toolbar(self) -> None:
            self.navigation_toolbar = QToolBar("Navigation", self)
            self.navigation_toolbar.setObjectName("chm_navigation_toolbar")
            self.navigation_toolbar.setMovable(False)
            self.navigation_toolbar.setIconSize(QSize(20, 20))
            self.navigation_toolbar.setToolButtonStyle(
                Qt.ToolButtonTextBesideIcon
            )
            self.navigation_toolbar.addAction(self.open_action)
            self.navigation_toolbar.addSeparator()
            self.navigation_toolbar.addAction(self.home_action)
            self.navigation_toolbar.addAction(self.back_action)
            self.navigation_toolbar.addAction(self.forward_action)

        def create_content(self) -> None:
            self.tabs = QTabWidget(self)
            self.topics_tab = ChmSearchTab(
                "Thema/Topic suchen …",
                self.tabs,
            )
            self.keywords_tab = ChmSearchTab(
                "Schlüsselwort suchen …",
                self.tabs,
            )
            self.favorites_tab = ChmSearchTab(
                "Favorit suchen …",
                self.tabs,
            )
            self.tabs.addTab(self.topics_tab, "Themen")
            self.tabs.addTab(self.keywords_tab, "Schlüsselwörter")
            self.tabs.addTab(self.favorites_tab, "Favoriten")

            favorites_layout = QHBoxLayout()
            self.add_favorite_button = QPushButton(
                "Aktuelle Seite hinzufügen",
                self.favorites_tab,
            )
            self.remove_favorite_button = QPushButton(
                "Entfernen",
                self.favorites_tab,
            )
            favorites_layout.addWidget(self.add_favorite_button)
            favorites_layout.addWidget(self.remove_favorite_button)
            favorites_layout.addStretch(1)
            self.favorites_tab.layout().addLayout(favorites_layout)

            self.web_view = QWebEngineView(self)
            self.web_view.setObjectName("chm_content_view")
            self.apply_content_view_theme()
            self.web_page = ChmWebPage(self.web_view)
            self.web_page.setBackgroundColor(
                self.content_background_color()
            )
            self.web_view.setPage(self.web_page)
            web_settings = self.web_page.settings()
            web_settings.setAttribute(
                QWebEngineSettings.LocalContentCanAccessFileUrls,
                True,
            )
            web_settings.setAttribute(
                QWebEngineSettings.LocalContentCanAccessRemoteUrls,
                False,
            )
            self.show_empty_page()

            self.splitter = QSplitter(Qt.Horizontal, self)
            self.splitter.setChildrenCollapsible(False)
            self.splitter.addWidget(self.tabs)
            self.splitter.addWidget(self.web_view)
            self.splitter.setSizes([360, 820])
            self.splitter.setStretchFactor(0, 0)
            self.splitter.setStretchFactor(1, 1)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setMenuBar(self.menu_bar)
            layout.addWidget(self.navigation_toolbar)
            layout.addWidget(self.splitter, 1)

        def create_statusbar(self) -> None:
            self.status_bar = QStatusBar(self)
            self.file_status = QLabel("Keine CHM-Datei geöffnet", self)
            self.file_status.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Preferred,
            )
            self.status_bar.addPermanentWidget(self.file_status, 1)
            self.layout().addWidget(self.status_bar)
            self.status_bar.showMessage("Bereit", 3000)

        def connect_signals(self) -> None:
            self.open_action.triggered.connect(self.choose_chm)
            self.quit_action.triggered.connect(self.close)
            self.copy_action.triggered.connect(
                lambda: self.web_page.triggerAction(QWebEnginePage.Copy)
            )
            self.source_action.triggered.connect(self.show_page_source)
            self.about_action.triggered.connect(self.show_about)
            self.home_action.triggered.connect(self.go_home)
            self.back_action.triggered.connect(self.web_view.back)
            self.forward_action.triggered.connect(self.web_view.forward)

            self.topics_tab.search_requested.connect(
                lambda text: self.find_first(self.topics_tab.tree, text)
            )
            self.keywords_tab.search_requested.connect(
                lambda text: self.find_first(self.keywords_tab.tree, text)
            )
            self.favorites_tab.search_requested.connect(
                lambda text: self.find_first(self.favorites_tab.tree, text)
            )
            self.topics_tab.tree.currentItemChanged.connect(
                self.tree_item_changed
            )
            self.keywords_tab.tree.currentItemChanged.connect(
                self.tree_item_changed
            )
            self.favorites_tab.tree.currentItemChanged.connect(
                self.tree_item_changed
            )
            self.favorites_tab.tree.currentItemChanged.connect(
                lambda *_args: self.update_navigation()
            )
            self.add_favorite_button.clicked.connect(
                self.add_current_favorite
            )
            self.remove_favorite_button.clicked.connect(
                self.remove_current_favorite
            )

            self.web_view.loadStarted.connect(
                lambda: self.status_bar.showMessage("Lade Seite …")
            )
            self.web_view.loadProgress.connect(
                lambda value: self.status_bar.showMessage(
                    f"Lade Seite … {value} %"
                )
            )
            self.web_view.loadFinished.connect(self.load_finished)
            self.web_view.urlChanged.connect(
                lambda _url: self.update_navigation()
            )
            self.web_view.titleChanged.connect(self.title_changed)

        # ----- Theme des HTML-Inhalts --------------------------------

        def content_background_color(self) -> QColor:
            return QColor("#000000" if self.dark_mode_enabled else "#ffffff")

        def content_foreground_color(self) -> QColor:
            return QColor("#ffffff" if self.dark_mode_enabled else "#000000")

        # -------------------------------------------------------------------
        # Färbt die Web-Oberfläche schon vor dem ersten Seitenbild.
        # -------------------------------------------------------------------
        def apply_content_view_theme(self) -> None:
            if not hasattr(self, "web_view"):
                return

            background = self.content_background_color()
            foreground = self.content_foreground_color()
            
            palette = QPalette(self.web_view.palette())
            palette.setColor(QPalette.Window, background)
            palette.setColor(QPalette.Base, background)
            palette.setColor(QPalette.WindowText, foreground)
            palette.setColor(QPalette.Text, foreground)
            
            self.web_view.setPalette(palette)
            self.web_view.setAutoFillBackground(True)
            self.web_view.setStyleSheet(
                "QWebEngineView#chm_content_view {"
                f" background-color: {background.name()};"
                f" color: {foreground.name()};"
                "}"
            )

        def content_theme_css(self) -> str:
            if self.dark_mode_enabled:
                background  = "#000000"
                foreground  = "#ffffff"
                link        = "#66b3ff"
                visited     = "#c792ea"
                active      = "#ffcc66"
                scheme      = "dark"
            else:
                background  = "#ffffff"
                foreground  = "#000000"
                link        = "#0000ee"
                visited     = "#551a8b"
                active      = "#ee0000"
                scheme      = "light"

            return (
                ":root { color-scheme: " + scheme + "; }\n"
                "html, body {"
                f" background-color: {background} !important;"
                f" color: {foreground} !important;"
                "}\n"
                f"a:link {{ color: {link}; }}\n"
                f"a:visited {{ color: {visited}; }}\n"
                f"a:active {{ color: {active}; }}\n"
            )
            
        # -------------------------------------------------------------------
        # Wendet das Anwendungstheme auf die aktuelle HTML-Seite an.
        # -------------------------------------------------------------------
        def apply_content_theme(self) -> None:
            self.apply_content_view_theme()
            if not hasattr(self, "web_page"):
                return

            background = (
                "#000000" if self.dark_mode_enabled else "#ffffff"
            )
            foreground = (
                "#ffffff" if self.dark_mode_enabled else "#000000"
            )
            css = self.content_theme_css()
            self.web_page.setBackgroundColor(QColor(background))

            script = (
                "(function () {"
                f"var id = {json.dumps(self.CONTENT_THEME_STYLE_ID)};"
                "var style = document.getElementById(id);"
                "if (!style) {"
                "style = document.createElement('style');"
                "style.id = id;"
                "(document.head || document.documentElement)"
                ".appendChild(style);"
                "}"
                f"style.textContent = {json.dumps(css)};"
                f"document.documentElement.style.backgroundColor = "
                f"{json.dumps(background)};"
                "if (document.body) {"
                f"document.body.style.backgroundColor = "
                f"{json.dumps(background)};"
                f"document.body.style.color = {json.dumps(foreground)};"
                "}"
                "})();"
            )
            self.web_page.runJavaScript(script)

        def set_dark_mode(self, enabled: bool) -> None:
            self.dark_mode_enabled = bool(enabled)
            self.apply_content_theme()

        # ----- CHM laden ----------------------------------------------
        def choose_chm(self) -> None:
            start_directory = str(
                self.settings.value("chm/last_directory", "") or ""
            )
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "CHM-Hilfedatei öffnen",
                start_directory,
                "CHM-Hilfedateien (*.chm);;Alle Dateien (*)",
            )
            if filename:
                self.settings.setValue(
                    "chm/last_directory",
                    str(Path(filename).parent),
                )
                self.open_chm(filename)

        def open_chm(self, filename: str) -> bool:
            source = Path(filename).expanduser().resolve()
            if not source.is_file():
                QMessageBox.warning(
                    self,
                    "CHM Viewer",
                    f"Datei nicht gefunden:\n{source}",
                )
                return False

            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.status_bar.showMessage("CHM-Datei wird entpackt …")
            QApplication.processEvents()
            new_temporary = None
            try:
                new_temporary = tempfile.TemporaryDirectory(
                    prefix="d64_chm_viewer_"
                )
                root = Path(new_temporary.name)
                ChmExtractor.extract(source, root)
                topics, keywords, home_local = self.read_metadata(root)
            except Exception as exc:
                if new_temporary is not None:
                    new_temporary.cleanup()
                QMessageBox.critical(self, "CHM Viewer", str(exc))
                self.status_bar.showMessage(
                    "CHM-Datei konnte nicht geöffnet werden",
                    6000,
                )
                return False
            finally:
                QApplication.restoreOverrideCursor()

            old_temporary = self.temporary
            self.web_view.setUrl(QUrl("about:blank"))
            QApplication.processEvents()
            self.temporary = new_temporary
            self.content_root = root
            self.chm_path = source
            self.home_local = home_local
            if old_temporary is not None:
                try:
                    old_temporary.cleanup()
                except OSError:
                    pass

            self.populate_tree(self.topics_tab.tree, topics)
            self.populate_tree(self.keywords_tab.tree, keywords)
            self.load_favorites()
            self.tabs.setCurrentWidget(self.topics_tab)
            self.file_status.setText(str(source))
            self.settings.setValue("chm/last_file", str(source))
            self.setWindowTitle(f"{source.name} – CHM Viewer")

            topic_count = self.tree_count(self.topics_tab.tree)
            keyword_count = self.tree_count(self.keywords_tab.tree)
            self.status_bar.showMessage(
                f"{topic_count} Themen und {keyword_count} "
                "Schlüsselwörter geladen",
                6000,
            )

            first_item = self.first_local_item(self.topics_tab.tree)
            if first_item is not None:
                self.topics_tab.tree.setCurrentItem(first_item)
                self.topics_tab.tree.scrollToItem(first_item)
            elif self.home_local:
                self.load_local(self.home_local)
            else:
                self.show_empty_page("Keine anzeigbare Hilfeseite gefunden.")
            self.update_navigation()
            if self.pending_context_word:
                QTimer.singleShot(
                    0,
                    lambda: self.open_context_topic(
                        self.pending_context_language,
                        self.pending_context_word,
                    ),
                )
            return True

        def set_pending_context(self, language: str, word: str) -> None:
            self.pending_context_language = str(language or "").casefold()
            self.pending_context_word = str(word or "").strip()

        def open_context_topic(self, language: str, word: str) -> bool:
            """Sucht ein kontextbezogenes Thema in Index und Themenbaum."""
            needle = str(word or "").strip().casefold()
            language_name = str(language or "").strip().casefold()
            if not needle:
                return False

            best_item = None
            best_score = -1
            for tree in (self.keywords_tab.tree, self.topics_tab.tree):
                iterator = QTreeWidgetItemIterator(tree)
                while iterator.value() is not None:
                    item = iterator.value()
                    title = item.text(0).strip().casefold()
                    local = str(item.data(0, CHM_ROLE_LOCAL) or "").casefold()
                    score = 0
                    if title == needle:
                        score += 100
                    elif needle in title:
                        score += 50
                    if Path(local.split("#", 1)[0]).stem.casefold() == needle:
                        score += 80
                    if language_name and language_name in local:
                        score += 20
                    if score > best_score and local:
                        best_item = item
                        best_score = score
                    iterator += 1
                if best_score >= 100:
                    break

            if best_item is None or best_score <= 0:
                self.status_bar.showMessage(
                    f"Kein Hilfethema für „{word}“ gefunden",
                    5000,
                )
                return False

            parent = best_item.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()
            tree = best_item.treeWidget()
            tree.setCurrentItem(best_item)
            tree.scrollToItem(best_item)
            self.tabs.setCurrentWidget(
                self.keywords_tab if tree is self.keywords_tab.tree
                else self.topics_tab
            )
            local = str(best_item.data(0, CHM_ROLE_LOCAL) or "")
            self.load_local(local)
            self.status_bar.showMessage(
                f"Kontexthilfe: {language_name or 'allgemein'} / {word}",
                5000,
            )
            return True

        def read_metadata(self, root: Path):
            project = find_chm_file_by_suffix(root, ".hhp")
            options = read_chm_project_options(project)
            contents = self.metadata_file(
                root,
                options.get("contents file", ""),
                ".hhc",
            )
            index = self.metadata_file(
                root,
                options.get("index file", ""),
                ".hhk",
            )
            topics = parse_chm_sitemap(contents)
            keywords = parse_chm_sitemap(index)

            if not topics:
                html_files = [
                    path for path in iter_chm_files(root)
                    if path.suffix.casefold() in (".html", ".htm")
                ]
                html_files.sort(
                    key=lambda path: str(path.relative_to(root)).casefold()
                )
                topics = [
                    ChmSitemapEntry(
                        path.stem,
                        path.relative_to(root).as_posix(),
                    )
                    for path in html_files
                ]

            home_local = self.find_index(root)
            if not home_local:
                default_topic = options.get("default topic", "")
                relative, fragment = clean_chm_local(default_topic)
                if relative and resolve_chm_path(root, relative):
                    home_local = relative
                    if fragment:
                        home_local += "#" + fragment
            if not home_local:
                home_local = self.first_entry_local(topics)
            return topics, keywords, home_local

        def metadata_file(
            self,
            root: Path,
            configured: str,
            suffix: str,
        ) -> Optional[Path]:
            if configured:
                relative, _fragment = clean_chm_local(configured)
                resolved = resolve_chm_path(root, relative) if relative else None
                if resolved is not None:
                    return resolved
            return find_chm_file_by_suffix(root, suffix)

        def find_index(self, root: Path) -> str:
            candidates = [
                path for path in iter_chm_files(root)
                if path.name.casefold() in ("index.html", "index.htm")
            ]
            if not candidates:
                return ""
            result = min(
                candidates,
                key=lambda path: (
                    len(path.relative_to(root).parts),
                    str(path).casefold(),
                ),
            )
            return result.relative_to(root).as_posix()

        def first_entry_local(self, entries) -> str:
            for entry in entries:
                if entry.local:
                    return entry.local
                nested = self.first_entry_local(entry.children)
                if nested:
                    return nested
            return ""

        # ----- Themen, Suche und Anzeige ------------------------------

        def populate_tree(self, tree: QTreeWidget, entries) -> None:
            tree.blockSignals(True)
            tree.clear()

            def add_entries(parent, values) -> None:
                for entry in values:
                    item = QTreeWidgetItem(parent, [entry.title])
                    item.setData(0, CHM_ROLE_LOCAL, entry.local)
                    item.setData(0, CHM_ROLE_TITLE, entry.title)
                    item.setIcon(
                        0,
                        tree.style().standardIcon(
                            QStyle.SP_DirClosedIcon
                            if entry.children
                            else QStyle.SP_FileIcon
                        ),
                    )
                    if entry.children:
                        add_entries(item, entry.children)

            add_entries(tree, entries)
            tree.blockSignals(False)
            if tree.topLevelItemCount():
                tree.topLevelItem(0).setExpanded(True)

        def tree_count(self, tree: QTreeWidget) -> int:
            iterator = QTreeWidgetItemIterator(tree)
            count = 0
            while iterator.value() is not None:
                count += 1
                iterator += 1
            return count

        def first_local_item(self, tree: QTreeWidget):
            iterator = QTreeWidgetItemIterator(tree)
            while iterator.value() is not None:
                item = iterator.value()
                if str(item.data(0, CHM_ROLE_LOCAL) or "").strip():
                    return item
                iterator += 1
            return None

        def tree_item_changed(self, current, _previous) -> None:
            if current is None:
                return
            local = str(current.data(0, CHM_ROLE_LOCAL) or "").strip()
            if local:
                self.load_local(local)

        def find_first(self, tree: QTreeWidget, text: str) -> None:
            if not text:
                return
            needle = text.casefold()
            iterator = QTreeWidgetItemIterator(tree)
            while iterator.value() is not None:
                item = iterator.value()
                if needle in item.text(0).casefold():
                    parent = item.parent()
                    while parent is not None:
                        parent.setExpanded(True)
                        parent = parent.parent()
                    tree.setCurrentItem(item)
                    tree.scrollToItem(item)
                    self.status_bar.showMessage(
                        f"Treffer: {item.text(0)}",
                        4000,
                    )
                    return
                iterator += 1
            QApplication.beep()
            self.status_bar.showMessage(
                f"Kein Treffer für „{text}“",
                5000,
            )

        def local_url(self, value: str) -> Optional[QUrl]:
            if self.content_root is None:
                return None
            relative, fragment = clean_chm_local(value)
            if not relative:
                return None
            target = resolve_chm_path(self.content_root, relative)
            if target is None:
                return None
            url = QUrl.fromLocalFile(str(target))
            if fragment:
                url.setFragment(fragment)
            return url

        def load_local(self, value: str) -> None:
            url = self.local_url(value)
            if url is None:
                self.status_bar.showMessage(
                    f"Hilfeseite nicht gefunden: {value}",
                    6000,
                )
                return
            self.web_view.setUrl(url)

        def go_home(self) -> None:
            if self.home_local:
                self.load_local(self.home_local)

        def show_empty_page(self, message="Öffne eine CHM-Hilfedatei.") -> None:
            css = self.content_theme_css()
            self.web_view.setHtml(
                "<html><head><style id='"
                + self.CONTENT_THEME_STYLE_ID
                + "'>"
                + css
                + "</style></head>"
                "<body style='font-family:sans-serif;margin:3em'>"
                "<h2>CHM Viewer</h2>"
                f"<p>{html.escape(message)}</p>"
                "</body></html>"
            )

        # ----- Favoriten ---------------------------------------------
        def current_local(self) -> str:
            if self.content_root is None:
                return ""
            url = self.web_view.url()
            if not url.isLocalFile():
                return ""
            try:
                relative = Path(url.toLocalFile()).resolve().relative_to(
                    self.content_root.resolve()
                )
            except (OSError, ValueError):
                return ""
            result = relative.as_posix()
            if url.fragment():
                result += "#" + url.fragment()
            return result

        def favorites_key(self) -> str:
            if self.chm_path is None:
                return ""
            digest = hashlib.sha256(
                str(self.chm_path).casefold().encode("utf-8")
            ).hexdigest()
            return "chm/favorites/" + digest

        def favorite_values(self):
            key = self.favorites_key()
            if not key:
                return []
            raw = str(self.settings.value(key, "[]") or "[]")
            try:
                values = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                return []
            if not isinstance(values, list):
                return []
            return [
                {
                    "title": str(item.get("title", "")),
                    "local": str(item.get("local", "")),
                }
                for item in values
                if isinstance(item, dict) and item.get("local")
            ]

        def save_favorite_values(self, values) -> None:
            key = self.favorites_key()
            if key:
                self.settings.setValue(
                    key,
                    json.dumps(values, ensure_ascii=False),
                )

        def load_favorites(self) -> None:
            tree = self.favorites_tab.tree
            tree.blockSignals(True)
            tree.clear()
            for favorite in self.favorite_values():
                item = QTreeWidgetItem(
                    tree,
                    [favorite["title"] or favorite["local"]],
                )
                item.setData(0, CHM_ROLE_LOCAL, favorite["local"])
                item.setData(0, CHM_ROLE_TITLE, favorite["title"])
                item.setIcon(
                    0,
                    tree.style().standardIcon(QStyle.SP_FileIcon),
                )
            tree.blockSignals(False)
            self.update_navigation()

        def add_current_favorite(self) -> None:
            local = self.current_local()
            if not local:
                self.status_bar.showMessage(
                    "Die aktuelle Seite kann nicht gespeichert werden",
                    5000,
                )
                return
            title = self.web_view.title().strip()
            if not title:
                title = Path(local.split("#", 1)[0]).name
            values = self.favorite_values()
            if any(
                value["local"].casefold() == local.casefold()
                for value in values
            ):
                self.status_bar.showMessage(
                    "Diese Seite ist bereits als Favorit gespeichert",
                    4000,
                )
                return
            values.append({"title": title, "local": local})
            self.save_favorite_values(values)
            self.load_favorites()
            self.status_bar.showMessage(
                f"Favorit gespeichert: {title}",
                4000,
            )

        def remove_current_favorite(self) -> None:
            item = self.favorites_tab.tree.currentItem()
            if item is None:
                return
            local = str(item.data(0, CHM_ROLE_LOCAL) or "")
            values = [
                value for value in self.favorite_values()
                if value["local"].casefold() != local.casefold()
            ]
            self.save_favorite_values(values)
            self.load_favorites()
            self.status_bar.showMessage("Favorit entfernt", 3000)

        # ----- Menuefunktionen und Status ----------------------------

        def show_page_source(self) -> None:
            dialog = ChmSourceDialog(self)
            dialog.editor.setPlainText("Quelltext wird geladen …")
            dialog.setAttribute(Qt.WA_DeleteOnClose, True)
            self.source_dialogs.append(dialog)

            def remove_dialog(*_args) -> None:
                if dialog in self.source_dialogs:
                    self.source_dialogs.remove(dialog)

            def receive_source(source: str) -> None:
                try:
                    dialog.editor.setPlainText(source)
                    cursor = dialog.editor.textCursor()
                    cursor.movePosition(QTextCursor.Start)
                    dialog.editor.setTextCursor(cursor)
                except RuntimeError:
                    pass

            dialog.destroyed.connect(remove_dialog)
            dialog.show()
            self.web_page.toHtml(receive_source)

        def show_about(self) -> None:
            QMessageBox.about(
                self,
                "Über CHM Viewer",
                "<h3>CHM Viewer</h3>"
                "<p>Integrierte HTML-Hilfeanzeige mit Themen, "
                "Schlüsselwörtern und Favoriten.</p>"
                "<p>Die Inhalte werden mit QWebEnginePage angezeigt.</p>",
            )

        def load_finished(self, success: bool) -> None:
            self.apply_content_theme()
            if success:
                self.status_bar.showMessage("Seite geladen", 2500)
            else:
                self.status_bar.showMessage(
                    "Die Seite konnte nicht geladen werden",
                    5000,
                )
            self.update_navigation()

        def title_changed(self, title: str) -> None:
            if self.chm_path is not None:
                visible_title = title.strip() or self.chm_path.name
                self.setWindowTitle(f"{visible_title} – CHM Viewer")

        def update_navigation(self) -> None:
            history = self.web_view.history()
            has_content = self.content_root is not None
            self.home_action.setEnabled(
                has_content and bool(self.home_local)
            )
            self.back_action.setEnabled(history.canGoBack())
            self.forward_action.setEnabled(history.canGoForward())
            self.copy_action.setEnabled(has_content)
            self.source_action.setEnabled(has_content)
            self.add_favorite_button.setEnabled(has_content)
            self.remove_favorite_button.setEnabled(
                self.favorites_tab.tree.currentItem() is not None
            )

        def restore_state(self) -> None:
            geometry = self.settings.value("chm/window_geometry")
            splitter_sizes = self.settings.value("chm/splitter_sizes")
            if geometry is not None:
                self.restoreGeometry(geometry)
            if splitter_sizes:
                try:
                    self.splitter.setSizes(
                        [int(value) for value in splitter_sizes]
                    )
                except (TypeError, ValueError):
                    pass

        def done(self, result: int) -> None:
            self.settings.setValue(
                "chm/window_geometry",
                self.saveGeometry(),
            )
            self.settings.setValue(
                "chm/splitter_sizes",
                self.splitter.sizes(),
            )
            self.web_view.setUrl(QUrl("about:blank"))
            QApplication.processEvents()
            if self.temporary is not None:
                try:
                    self.temporary.cleanup()
                except OSError:
                    pass
                self.temporary = None
            super().done(result)

    class DockTitleBar(QWidget):
        """Dunkle Dock-Leiste mit weißen Mini-Symbolen und Zusatzaktion."""

        def __init__(
            self,
            dock: QDockWidget,
            *,
            extra_text: str = "",
            extra_callback=None,
        ):
            super().__init__(dock)
            self.dock = dock
            self._drag_offset = None
            self.setObjectName("custom_dock_title_bar")

            layout = QHBoxLayout(self)
            layout.setContentsMargins(7, 2, 3, 2)
            layout.setSpacing(3)
            self.title_label = QLabel(dock.windowTitle(), self)
            self.title_label.setObjectName("custom_dock_title_label")
            layout.addWidget(self.title_label)
            layout.addStretch(1)

            self.extra_button = None
            if extra_text and extra_callback is not None:
                self.extra_button = QToolButton(self)
                self.extra_button.setObjectName("dock_title_extra_button")
                self.extra_button.setText(extra_text)
                self.extra_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
                self.extra_button.clicked.connect(
                    lambda _checked=False: extra_callback()
                )
                layout.addWidget(self.extra_button)

            self.float_button = QToolButton(self)
            self.float_button.setObjectName("dock_title_float_button")
            self.float_button.setIcon(self._symbol_icon("float"))
            self.float_button.setToolTip("Andocken / Abdocken")
            self.float_button.setAutoRaise(True)
            self.float_button.clicked.connect(
                lambda _checked=False: dock.setFloating(not dock.isFloating())
            )
            layout.addWidget(self.float_button)

            self.close_button = QToolButton(self)
            self.close_button.setObjectName("dock_title_close_button")
            self.close_button.setIcon(self._symbol_icon("close"))
            self.close_button.setToolTip("Dock-Fenster schließen")
            self.close_button.setAutoRaise(True)
            self.close_button.clicked.connect(
                lambda _checked=False: dock.close()
            )
            layout.addWidget(self.close_button)

            dock.windowTitleChanged.connect(self.title_label.setText)
            self.setStyleSheet(
                "QWidget#custom_dock_title_bar {"
                "background-color:#343e4d; border:0; }"
                "QLabel#custom_dock_title_label {"
                "color:#ffffff; background:transparent; font-weight:bold; }"
                "QToolButton { color:#ffffff; background:transparent;"
                "border:1px solid transparent; border-radius:2px; padding:2px; }"
                "QToolButton:hover { background-color:#4b586a;"
                "border-color:#718198; }"
                "QToolButton:pressed { background-color:#202630; }"
                "QToolButton#dock_title_extra_button {"
                "padding-left:7px; padding-right:7px; }"
            )

        @staticmethod
        def _symbol_icon(symbol: str) -> QIcon:
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = QPen(QColor("#ffffff"), 1.8, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            if symbol == "close":
                painter.drawLine(QPointF(4, 4), QPointF(12, 12))
                painter.drawLine(QPointF(12, 4), QPointF(4, 12))
            else:
                painter.drawRect(QRectF(3.5, 5.5, 8.0, 7.0))
                painter.drawRect(QRectF(5.5, 3.5, 7.0, 7.0))
            painter.end()
            return QIcon(pixmap)

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.LeftButton:
                self._drag_offset = event.globalPos() - self.dock.frameGeometry().topLeft()
                event.accept()
                return
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event) -> None:
            if (
                self._drag_offset is not None
                and event.buttons() & Qt.LeftButton
            ):
                if not self.dock.isFloating():
                    self.dock.setFloating(True)
                self.dock.move(event.globalPos() - self._drag_offset)
                event.accept()
                return
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event) -> None:
            self._drag_offset = None
            super().mouseReleaseEvent(event)

        def mouseDoubleClickEvent(self, event) -> None:
            if event.button() == Qt.LeftButton:
                self.dock.setFloating(not self.dock.isFloating())
                event.accept()
                return
            super().mouseDoubleClickEvent(event)

    class ExplorerWindow(QMainWindow):
        ORGANIZATION = "paule32"
        APPLICATION = "Qt5D64Explorer"
        DEFAULT_EDITOR_FONT_SIZE = 9
        MIN_EDITOR_FONT_SIZE = 9
        MAX_EDITOR_FONT_SIZE = 72
        EDITOR_EXTENSIONS = {
            ".asm", ".s", ".a65", ".m68k", ".inc",
            ".pas", ".pp",
            ".c", ".h",
            ".bas", ".basic",
            ".txt", ".text", ".log", ".md",
            ".prg", ".amiga", ".adf", ".ram", ".bin",
            ".chr", ".charset",
            ".pal", ".palette",
            ".scr", ".screen",
            ".px16", ".pixel", ".pix",
            ".pro",
        }
        FILTERS = {
            "D64": {".d64"},
            "RAM": {".ram"},
            "BASIC": {".bas", ".basic"},
            "ASM": {".asm", ".s", ".a65", ".m68k", ".inc"},
            "PAS": {".pas", ".pp"},
            "C": {".c", ".h"},
            "PRG": {".prg"},
            "AMIGA": {".amiga", ".adf"},
            "PE32": {".exe"},
            "OBJ": {".o", ".obj", ".a", ".lib"},
            "TXT": {".txt", ".text", ".log", ".md"},
            "CHR": {".chr", ".charset"},
            "PAL": {".pal", ".palette"},
            "SCREEN": {".scr", ".screen"},
            "PIXEL": {".px16", ".pixel", ".pix"},
            "ALLE": None,
        }

        def __init__(self, requested_directory: Optional[Path]):
            super().__init__()
            self.settings = QSettings(self.ORGANIZATION, self.APPLICATION)
            self.current_filter = "ALLE"
            self.current_directory = Path.cwd().resolve()
            self.workspace_root = self.current_directory
            self.icon_provider = QFileIconProvider()
            self.untitled_counter = 0
            self.editor_font_size = self.DEFAULT_EDITOR_FONT_SIZE
            self.dark_mode_enabled = False
            self.dism_vice_path = str(
                self.settings.value("dism/vice_path", "") or ""
            )
            self.winuae_path = str(
                self.settings.value("emulator/winuae_path", "") or ""
            )
            self._winuae_boot_directories = []
            self.dism_thread = None
            self.dism_worker = None
            self.character_editor_dialog = None
            self.palette_editor_dialog = None
            self.text_screen_editor_dialog = None
            self.pixel_screen_editor_dialog = None
            self.current_project_path = None
            self.project_modified = False
            self.project_root_items = {}
            self._caps_lock_fallback = False
            self._num_lock_fallback = False
            application = QApplication.instance()
            self.light_application_palette = QPalette(application.palette())
            self.light_application_stylesheet = application.styleSheet()
            self.theme_asset_directory = QTemporaryDir()
            self.scrollbar_arrow_assets = self._create_scrollbar_arrow_assets()

            self.setWindowTitle("Qt5 D64- und Dateisystem-Explorer")
            self.setWindowIcon(
                self.style().standardIcon(QStyle.SP_ComputerIcon)
            )
            self.resize(1360, 860)
            self.setDockNestingEnabled(True)
            self.setAnimated(True)
            self.setCorner(Qt.BottomLeftCorner, Qt.BottomDockWidgetArea)
            self.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidgetArea)

            self._create_actions()
            self._create_menu()
            self._create_toolbar()
            self._create_central_widget()
            self._create_left_dock()
            self._create_right_dock()
            self._create_bottom_dock()
            self._create_status_panels()

            application.installEventFilter(self)
            self.statusBar().showMessage("Bereit")

            start_directory = self._choose_start_directory(requested_directory)
            self.set_workspace_root(start_directory, select=True)
            self._restore_window_state()

            # Sinnvolle Startgrößen, sofern noch kein gespeicherter Zustand besteht.
            if not self.settings.contains("window/state"):
                self.resizeDocks(
                    [self.left_dock, self.right_dock],
                    [470, 520],
                    Qt.Horizontal,
                )
                self.resizeDocks([self.bottom_dock], [190], Qt.Vertical)

        # ----- Aufbau ------------------------------------------------------

        def _create_actions(self) -> None:
            self.new_project_action = QAction("Projekt", self)
            self.new_project_action.setStatusTip(
                "Das geöffnete Projekt speichern und ein neues leeres Projekt anlegen"
            )
            self.new_project_action.triggered.connect(
                lambda _checked=False: self.new_project()
            )

            self.new_file_action = QAction(
                self.style().standardIcon(QStyle.SP_FileIcon),
                "Textdatei",
                self,
            )
            self.new_file_action.setShortcut(QKeySequence.New)
            self.new_file_action.setStatusTip("Eine neue Textdatei anlegen")
            self.new_file_action.triggered.connect(
                lambda _checked=False: self.new_source_document("text")
            )

            self.new_basic_action = QAction("BASIC-Programm", self)
            self.new_basic_action.triggered.connect(
                lambda _checked=False: self.new_source_document("basic")
            )
            self.new_assembler_action = QAction("Assembler-Programm", self)
            self.new_assembler_action.triggered.connect(
                lambda _checked=False: self.new_source_document("assembler")
            )
            self.new_pascal_action = QAction("Pascal-Programm", self)
            self.new_pascal_action.triggered.connect(
                lambda _checked=False: self.new_source_document("pascal")
            )
            self.new_c_action = QAction("C-Programm", self)
            self.new_c_action.triggered.connect(
                lambda _checked=False: self.new_source_document("c")
            )
            self.new_character_map_action = QAction("C-64 Character Map", self)
            self.new_character_map_action.triggered.connect(
                self.new_character_map
            )
            self.new_text_screen_action = QAction("C-64 Text Screen", self)
            self.new_text_screen_action.triggered.connect(
                self.new_text_screen
            )
            self.new_pixel_screen_action = QAction("C-64 Pixel Screen", self)
            self.new_pixel_screen_action.triggered.connect(
                self.new_pixel_screen
            )
            self.new_text_file_action = self.new_file_action

            self.open_file_action = QAction(
                self.style().standardIcon(QStyle.SP_DialogOpenButton),
                "Öffnen …",
                self,
            )
            self.open_file_action.setShortcut(QKeySequence.Open)
            self.open_file_action.setStatusTip(
                "Eine Text-, Assembler-, Pascal- oder C-Datei öffnen"
            )
            self.open_file_action.triggered.connect(self.open_document_dialog)

            self.save_file_action = QAction(
                self.style().standardIcon(QStyle.SP_DialogSaveButton),
                "Speichern",
                self,
            )
            self.save_file_action.setShortcut(QKeySequence.Save)
            self.save_file_action.triggered.connect(self.save_current_document)

            self.save_as_action = QAction(
                self.style().standardIcon(QStyle.SP_DialogSaveButton),
                "Speichern unter ...",
                self,
            )
            self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
            self.save_as_action.triggered.connect(self.save_current_document_as)

            self.close_document_action = QAction("Registerkarte schließen", self)
            self.close_document_action.setShortcut(QKeySequence.Close)
            self.close_document_action.triggered.connect(
                self.close_current_document
            )

            self.choose_directory_action = QAction(
                self.style().standardIcon(QStyle.SP_DirOpenIcon),
                "Arbeitsverzeichnis wählen …",
                self,
            )
            self.choose_directory_action.setShortcut(QKeySequence("Ctrl+Shift+D"))
            self.choose_directory_action.triggered.connect(
                self.choose_workspace_directory
            )

            self.parent_action = QAction(
                self.style().standardIcon(QStyle.SP_ArrowUp),
                "Übergeordnetes Verzeichnis",
                self,
            )
            self.parent_action.setShortcut(QKeySequence("Alt+Up"))
            self.parent_action.triggered.connect(self.go_to_parent_directory)

            self.refresh_action = QAction(
                self.style().standardIcon(QStyle.SP_BrowserReload),
                "Aktualisieren",
                self,
            )
            self.refresh_action.setShortcut(QKeySequence.Refresh)
            self.refresh_action.triggered.connect(self.refresh_views)

            self.quit_action = QAction("Beenden", self)
            self.quit_action.setShortcut(QKeySequence.Quit)
            self.quit_action.triggered.connect(self.close)

            self.about_action = QAction("Über …", self)
            self.about_action.triggered.connect(self.show_about_dialog)

            self.chm_viewer_action = QAction(
                self._toolbar_symbol_icon("help"),
                "CHM-Viewer …",
                self,
            )
            self.chm_viewer_action.setObjectName("main_help_action")
            self.chm_viewer_action.setShortcut(QKeySequence.HelpContents)
            self.chm_viewer_action.setToolTip("Hilfe öffnen")
            self.chm_viewer_action.setStatusTip(
                "CHM-Hilfedatei mit Themen und Schlüsselwörtern öffnen"
            )
            self.chm_viewer_action.triggered.connect(self.show_chm_viewer)

            self.character_editor_action = QAction(
                self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
                "C64 Character-Editor …",
                self,
            )
            self.character_editor_action.setShortcut(QKeySequence("Ctrl+Alt+C"))
            self.character_editor_action.setStatusTip(
                "255 frei editierbare C64-Zeichen im 8x8-Raster bearbeiten"
            )
            self.character_editor_action.triggered.connect(
                self.show_character_editor
            )

            self.palette_editor_action = QAction(
                self.style().standardIcon(QStyle.SP_DialogResetButton),
                "C64 Paletten-Editor …",
                self,
            )
            self.palette_editor_action.setShortcut(QKeySequence("Ctrl+Alt+P"))
            self.palette_editor_action.setStatusTip(
                "Die 16 C64-Farben bearbeiten und als Quellcode exportieren"
            )
            self.palette_editor_action.triggered.connect(
                self.show_palette_editor
            )

            self.text_screen_editor_action = QAction(
                self.style().standardIcon(QStyle.SP_FileDialogContentsView),
                "C64 Text-Bildschirm-Editor …",
                self,
            )
            self.text_screen_editor_action.setShortcut(QKeySequence("Ctrl+Alt+T"))
            self.text_screen_editor_action.setStatusTip(
                "Eine 40x25-C64-Bildschirmseite mit Zeichen und Farben bearbeiten"
            )
            self.text_screen_editor_action.triggered.connect(
                self.show_text_screen_editor
            )

            self.pixel_screen_editor_action = QAction(
                self.style().standardIcon(QStyle.SP_DesktopIcon),
                "C64 Pixel-Bildschirm-Editor …",
                self,
            )
            self.pixel_screen_editor_action.setShortcut(QKeySequence("Ctrl+Alt+X"))
            self.pixel_screen_editor_action.setStatusTip(
                "Einen 320x200-Pixelbildschirm mit 16 Farben und Formwerkzeugen bearbeiten"
            )
            self.pixel_screen_editor_action.triggered.connect(
                self.show_pixel_screen_editor
            )

            self.coff32_archive_action = QAction(
                "COFF32-Archiv (.a) erstellen …", self
            )
            self.coff32_archive_action.setStatusTip(
                "Mehrere COFF32-.o-Dateien in ein statisches .a-Archiv schreiben"
            )
            self.coff32_archive_action.triggered.connect(
                self.create_coff32_archive_dialog
            )

            self.pe32_linker_action = QAction(
                "Windows PE32 Linker …", self
            )
            self.pe32_linker_action.setStatusTip(
                "COFF32-.o- und .a-Dateien zu einer Windows-PE32-EXE linken"
            )
            self.pe32_linker_action.triggered.connect(
                self.link_pe32_dialog
            )

            self.windows_graphics_header_action = QAction(
                "Windows Direct2D/Direct3D Runtime schreiben …", self
            )
            self.windows_graphics_header_action.setStatusTip(
                "Gemeinsame Grafik-API und Direct2D/Direct3D-Runtime speichern"
            )
            self.windows_graphics_header_action.triggered.connect(
                self.write_windows_graphics_header_dialog
            )

            self.windows_graphics_build_action = QAction(
                "Windows Direct2D/Direct3D Runtime DLL bauen …", self
            )
            self.windows_graphics_build_action.setStatusTip(
                "d64graphics.dll als 32-Bit-MinGW-DLL für Direct2D oder Direct3D bauen"
            )
            self.windows_graphics_build_action.triggered.connect(
                self.build_windows_graphics_runtime_dialog
            )

            self.zoom_in_action = QAction(
                self._toolbar_symbol_icon("zoom_in"),
                "Schrift vergrößern",
                self,
            )
            self.zoom_in_action.setObjectName("zoom_in_action")
            self.zoom_in_action.setToolTip("Schrift um 1 Punkt vergrößern")
            self.zoom_in_action.setStatusTip("Editor-Schrift um 1 Punkt vergrößern")
            self.zoom_in_action.triggered.connect(self.increase_editor_font)

            self.zoom_out_action = QAction(
                self._toolbar_symbol_icon("zoom_out"),
                "Schrift verkleinern",
                self,
            )
            self.zoom_out_action.setObjectName("zoom_out_action")
            self.zoom_out_action.setToolTip("Schrift um 1 Punkt verkleinern")
            self.zoom_out_action.setStatusTip("Editor-Schrift um 1 Punkt verkleinern")
            self.zoom_out_action.triggered.connect(self.decrease_editor_font)

            self.theme_action = QAction(
                self._toolbar_symbol_icon("moon"),
                "Dunkelmodus einschalten",
                self,
            )
            self.theme_action.setObjectName("theme_action")
            self.theme_action.setToolTip("Dunkelmodus einschalten")
            self.theme_action.setStatusTip(
                "Gesamte Anwendung auf Dunkelmodus umschalten"
            )
            self.theme_action.triggered.connect(self.toggle_editor_theme)

            self.dism_extract_action = QAction("Extract Programs", self)
            self.dism_extract_action.setCheckable(True)
            self.dism_extract_action.setStatusTip(
                "Entspricht dem Optionsschalter --extract-prg"
            )

            self.dism_bam_action = QAction("BAM", self)
            self.dism_bam_action.setCheckable(True)
            self.dism_bam_action.setStatusTip(
                "Entspricht dem Optionsschalter --bam"
            )

            self.dism_startup_action = QAction("Start-Up", self)
            self.dism_startup_action.setCheckable(True)
            self.dism_startup_action.setStatusTip(
                "Entspricht dem Optionsschalter --startup"
            )

            self.dism_verbose_action = QAction("Verbose", self)
            self.dism_verbose_action.setCheckable(True)
            self.dism_verbose_action.setStatusTip(
                "Entspricht dem Optionsschalter --verbose"
            )

            self.dism_analyze_action = QAction("Analyze Program", self)
            self.dism_analyze_action.setCheckable(True)
            self.dism_analyze_action.setStatusTip(
                "Entspricht dem Optionsschalter --analyze-prg"
            )

            self.dism_disassemble_action = QAction("Disassemble", self)
            self.dism_disassemble_action.setCheckable(True)
            self.dism_disassemble_action.setStatusTip(
                "Entspricht dem Optionsschalter --disassemble"
            )

            self.dism_ram_image_action = QAction("RAM Image", self)
            self.dism_ram_image_action.setCheckable(True)
            self.dism_ram_image_action.setStatusTip(
                "Entspricht dem Optionsschalter --image-ram"
            )

            self.dism_vice_action = QAction("VICE", self)
            self.dism_vice_action.setCheckable(True)
            self.dism_vice_action.setStatusTip(
                "VICE-Programm auswaehlen und als --vice <Pfad> verwenden"
            )
            self.dism_vice_action.triggered.connect(self.choose_dism_vice)
            self._update_dism_vice_action_text()

            self.winuae_action = QAction("WinUAE", self)
            self.winuae_action.setStatusTip(
                "WinUAE-Programm für das Starten von Amiga-Builds auswählen"
            )
            self.winuae_action.triggered.connect(self.choose_winuae)
            self._update_winuae_action_text()

            self.dism_start_action = QAction("Disketten Image", self)
            self.dism_start_action.setStatusTip(
                "Disketten-Image mit den ausgewaehlten DISM-Optionen starten"
            )
            self.dism_start_action.triggered.connect(self.start_dism)

            self.dism_program_action = QAction("Programm", self)
            self.dism_program_action.setStatusTip(
                "Das direkte Starten eines Programms wird spaeter ergaenzt"
            )
            self.dism_program_action.setEnabled(False)
            self._update_zoom_action_state()

        def _populate_new_document_menu(self, menu: QMenu) -> QMenu:
            """Baut das identische Neu-Untermenü für Haupt- und Tabmenü."""
            menu.addAction(self.new_project_action)
            menu.addSeparator()
            menu.addAction(self.new_basic_action)
            menu.addAction(self.new_assembler_action)
            menu.addAction(self.new_pascal_action)
            menu.addAction(self.new_c_action)
            menu.addSeparator()
            menu.addAction(self.new_character_map_action)
            menu.addAction(self.new_text_screen_action)
            menu.addAction(self.new_pixel_screen_action)
            menu.addSeparator()
            menu.addAction(self.new_text_file_action)
            return menu

        def create_coff32_archive_dialog(self) -> None:
            filenames, _selected = QFileDialog.getOpenFileNames(
                self,
                "COFF32-Objektdateien auswählen",
                str(self.current_directory),
                "COFF32-Objekte (*.o *.obj);;Alle Dateien (*)",
            )
            if not filenames:
                return
            target_name, _selected = QFileDialog.getSaveFileName(
                self,
                "COFF32-Archiv speichern",
                str(self.current_directory / "library.a"),
                "Statisches Archiv (*.a);;Alle Dateien (*)",
            )
            if not target_name:
                return
            target = Path(target_name)
            if not target.suffix:
                target = target.with_suffix(".a")
            try:
                members = [(Path(name).name, Path(name).read_bytes()) for name in filenames]
                target.write_bytes(create_coff32_archive(members))
            except (OSError, PE32AssemblerError) as exc:
                self.show_error("COFF32-Archiv fehlgeschlagen", str(exc))
                return
            self.log(f"COFF32 ARCHIVE: {len(filenames)} Objekt(e) -> {target}")
            self.statusBar().showMessage(f"COFF32-Archiv erzeugt: {target.name}")
            if target.parent.resolve() == self.current_directory:
                self.populate_file_list()

        def link_pe32_dialog(self) -> None:
            filenames, _selected = QFileDialog.getOpenFileNames(
                self,
                "COFF32-Objekte/Archive linken",
                str(self.current_directory),
                "COFF32 (*.o *.obj *.a *.lib);;Alle Dateien (*)",
            )
            if not filenames:
                return
            target_name, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Windows-PE32 EXE/DLL speichern",
                str(self.current_directory / "program.exe"),
                "Windows PE32 EXE (*.exe);;Windows PE32 DLL (*.dll);;Alle Dateien (*)",
            )
            if not target_name:
                return
            target = Path(target_name)
            if not target.suffix:
                target = target.with_suffix(
                    ".dll" if "DLL" in selected_filter else ".exe"
                )
            is_dll = target.suffix.casefold() == ".dll"
            try:
                program = link_coff32_inputs(
                    [Path(name) for name in filenames],
                    entry_symbol="__d64_dll_entry" if is_dll else "_start",
                    gui=True,
                    dll=is_dll,
                    dll_name=target.name if is_dll else None,
                )
                target.write_bytes(program.executable)
            except (OSError, PE32AssemblerError) as exc:
                self.show_error("PE32-Linkerfehler", str(exc))
                return
            self.log(
                f"PE32 LINK: {len(filenames)} Eingabe(n) -> {target}, "
                f"{len(program.executable)} Bytes"
            )
            self.statusBar().showMessage(f"PE32-Programm gelinkt: {target.name}")
            if target.parent.resolve() == self.current_directory:
                self.populate_file_list()

        def write_windows_graphics_header_dialog(self) -> None:
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                "Windows-Grafik-API Header speichern",
                str(self.current_directory / "graphics_windows.h"),
                "C Header (*.h);;Alle Dateien (*)",
            )
            if not filename:
                return
            target = Path(filename)
            if not target.suffix:
                target = target.with_suffix(".h")
            try:
                header_path = write_windows_graphics_runtime_header(target)
                source_path = write_windows_graphics_runtime_source(
                    target.with_name("graphics_windows_runtime.cpp")
                )
            except OSError as exc:
                self.show_error("Windows-Grafik-Runtime konnte nicht gespeichert werden", str(exc))
                return
            self.statusBar().showMessage(
                f"Windows-Grafik-Runtime geschrieben: {header_path.name}, {source_path.name}"
            )

        def build_windows_graphics_runtime_dialog(self) -> None:
            backend, accepted = QInputDialog.getItem(
                self,
                "Windows-Grafik-Runtime",
                "Grafikbackend:",
                list(WINDOWS_GRAPHICS_BACKENDS),
                0,
                False,
            )
            if not accepted:
                return
            filename, _selected = QFileDialog.getSaveFileName(
                self,
                "Windows-Grafik-Runtime DLL speichern",
                str(self.current_directory / "d64graphics.dll"),
                "Windows DLL (*.dll);;Alle Dateien (*)",
            )
            if not filename:
                return
            try:
                dll_path = build_windows_graphics_runtime_dll(
                    Path(filename), backend
                )
            except (OSError, PE32AssemblerError) as exc:
                self.show_error(
                    "Windows-Grafik-Runtime konnte nicht gebaut werden",
                    str(exc),
                )
                return
            self.log(
                f"WINDOWS GRAPHICS RUNTIME: {backend} -> {dll_path}"
            )
            self.statusBar().showMessage(
                f"Windows-Grafik-Runtime gebaut: {dll_path.name} ({backend})"
            )

        def _create_menu(self) -> None:
            file_menu = self.menuBar().addMenu("&Datei")
            self.new_document_menu = file_menu.addMenu(
                self.style().standardIcon(QStyle.SP_FileIcon),
                "Neu",
            )
            self._populate_new_document_menu(self.new_document_menu)
            file_menu.addAction(self.open_file_action)
            file_menu.addAction(self.save_file_action)
            file_menu.addAction(self.save_as_action)
            file_menu.addAction(self.close_document_action)
            file_menu.addSeparator()
            file_menu.addAction(self.choose_directory_action)
            file_menu.addAction(self.parent_action)
            file_menu.addAction(self.refresh_action)
            file_menu.addSeparator()
            file_menu.addAction(self.quit_action)

            self.view_menu = self.menuBar().addMenu("&Ansicht")
            self.favorites_menu = self.menuBar().addMenu("&Favoriten")
            self._refresh_favorites_menu()
            self.dism_menu = self.menuBar().addMenu("&DISM")
            self.dism_menu.addAction(self.dism_extract_action)
            self.dism_menu.addAction(self.dism_bam_action)
            self.dism_menu.addAction(self.dism_startup_action)
            self.dism_menu.addAction(self.dism_verbose_action)
            self.dism_menu.addAction(self.dism_analyze_action)
            self.dism_menu.addAction(self.dism_disassemble_action)
            self.dism_menu.addAction(self.dism_ram_image_action)
            self.dism_menu.addAction(self.dism_vice_action)
            self.dism_menu.addAction(self.winuae_action)
            self.dism_menu.addSeparator()
            
            self.dism_start_menu = QMenu("START", self.dism_menu)
            self.dism_start_menu.setObjectName("dism_start_menu")
            self.dism_start_menu.setIcon(self._toolbar_symbol_icon("play"))
            self.dism_start_menu.addAction(self.dism_start_action)
            self.dism_start_menu.addAction(self.dism_program_action)
            
            self.dism_menu.addMenu(self.dism_start_menu)

            tools_menu = self.menuBar().addMenu("&Werkzeuge")
            tools_menu.addAction(self.character_editor_action)
            tools_menu.addAction(self.palette_editor_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.text_screen_editor_action)
            tools_menu.addAction(self.pixel_screen_editor_action)
            tools_menu.addSeparator()
            tools_menu.addAction(self.coff32_archive_action)
            tools_menu.addAction(self.pe32_linker_action)
            tools_menu.addAction(self.windows_graphics_header_action)
            tools_menu.addAction(self.windows_graphics_build_action)
            
            help_menu = self.menuBar().addMenu("&Hilfe")
            help_menu.addAction(self.chm_viewer_action)
            help_menu.addSeparator()
            help_menu.addAction(self.about_action)

        def _favorite_editor_name(
            self, document: DocumentEditor, editor: SourceTextEdit
        ) -> str:
            if editor is document.generated_assembly_editor:
                if document.generated_assembly_path is not None:
                    return document.generated_assembly_path.name
                return document.display_name + " [ASM]"
            if document.path is not None:
                return document.path.name
            return document.display_name

        def _refresh_favorites_menu(self) -> None:
            menu = getattr(self, "favorites_menu", None)
            if menu is None:
                return
            menu.clear()
            document_tabs = getattr(self, "document_tabs", None)
            entries = []
            if document_tabs is not None:
                for index in range(document_tabs.count()):
                    document = document_tabs.widget(index)
                    if not isinstance(document, DocumentEditor):
                        continue
                    for editor in (
                        document.raw_editor,
                        document.generated_assembly_editor,
                    ):
                        filename = self._favorite_editor_name(document, editor)
                        for line_number in editor.bookmark_lines():
                            entries.append(
                                (filename.casefold(), line_number, filename, document, editor)
                            )
            if not entries:
                empty_action = menu.addAction("(keine Favoriten)")
                empty_action.setEnabled(False)
                return
            for _sort_name, line_number, filename, document, editor in sorted(entries):
                action = menu.addAction(
                    f"Zeile {line_number} — {filename}"
                )
                action.triggered.connect(
                    lambda checked=False, d=document, e=editor, line=line_number:
                    self._jump_to_favorite(d, e, line)
                )

        def _jump_to_favorite(
            self,
            document: DocumentEditor,
            editor: SourceTextEdit,
            line_number: int,
        ) -> None:
            if self._document_index(document) < 0:
                return
            block = editor.document().findBlockByNumber(int(line_number) - 1)
            if not block.isValid():
                return
            self.document_tabs.setCurrentWidget(document)
            if editor is document.generated_assembly_editor:
                document.views.setCurrentWidget(document.generated_assembly_page)
            else:
                document.views.setCurrentWidget(document.source_page)
            cursor = QTextCursor(block)
            cursor.clearSelection()
            editor.setTextCursor(cursor)
            editor.centerCursor()
            editor.setFocus(Qt.OtherFocusReason)
            self.statusBar().showMessage(
                f"Favorit: {self._favorite_editor_name(document, editor)}, "
                f"Zeile {line_number}"
            )

        def _create_toolbar(self) -> None:
            self.toolbar = QToolBar("Datei und Navigation", self)
            self.toolbar.setObjectName("main_toolbar")
            self.toolbar.setMovable(True)
            self.toolbar.setFloatable(True)
            self.toolbar.setAllowedAreas(Qt.AllToolBarAreas)
            self.toolbar.setIconSize(QSize(22, 22))
            
            self.addToolBar(Qt.TopToolBarArea, self.toolbar)

            self.toolbar.addAction(self.new_file_action)
            self.toolbar.addAction(self.open_file_action)
            self.toolbar.addAction(self.save_file_action)
            self.toolbar.addAction(self.save_as_action)
            self.toolbar.addSeparator()
            self.toolbar.addAction(self.choose_directory_action)
            self.toolbar.addAction(self.parent_action)
            self.toolbar.addAction(self.refresh_action)
            self.toolbar.addSeparator()
            self.toolbar.addAction(self.character_editor_action)
            self.toolbar.addAction(self.palette_editor_action)
            self.toolbar.addAction(self.text_screen_editor_action)
            self.toolbar.addAction(self.pixel_screen_editor_action)

            # Ein dehnbarer Platzhalter richtet die Zoom- und Theme-Symbole
            # dauerhaft an der rechten Kante der (auch verschiebbaren) Toolbar aus.
            toolbar_spacer = QWidget(self.toolbar)
            toolbar_spacer.setObjectName("toolbar_right_spacer")
            toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            self.toolbar.addWidget(toolbar_spacer)
            # Hilfe steht unmittelbar links neben der Lupe mit Pluszeichen.
            self.toolbar.addAction(self.chm_viewer_action)
            self.toolbar.addSeparator()
            self.toolbar.addAction(self.zoom_in_action)
            self.toolbar.addAction(self.zoom_out_action)
            self.toolbar.addAction(self.theme_action)

            self.view_menu.addAction(self.toolbar.toggleViewAction())

        # ----- DISM -------------------------------------------------------

        def _update_dism_vice_action_text(self) -> None:
            if self.dism_vice_path:
                native_path = QDir.toNativeSeparators(self.dism_vice_path)
                self.dism_vice_action.setText(f"VICE: {native_path}")
                self.dism_vice_action.setToolTip(native_path)
            else:
                self.dism_vice_action.setText("VICE")
                self.dism_vice_action.setToolTip("Pfad zu VICE auswaehlen")

        def choose_dism_vice(self, _checked: bool = False) -> None:
            if self.dism_vice_path:
                saved_path = Path(self.dism_vice_path)
                initial_path = (
                    saved_path.parent if saved_path.parent.is_dir()
                    else self.current_directory
                )
            else:
                initial_path = self.current_directory

            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "VICE-Programm auswählen",
                str(initial_path),
                "VICE/Programme (x64sc.exe x64.exe *.exe);;Alle Dateien (*)",
            )
            if filename:
                self.dism_vice_path = str(Path(filename).resolve())
                self.settings.setValue("dism/vice_path", self.dism_vice_path)
                self.dism_vice_action.setChecked(True)
                self._update_dism_vice_action_text()
                self.log(f"VICE ausgewählt: {self.dism_vice_path}")
            elif not self.dism_vice_path:
                self.dism_vice_action.setChecked(False)

        def _update_winuae_action_text(self) -> None:
            if self.winuae_path:
                native_path = QDir.toNativeSeparators(self.winuae_path)
                self.winuae_action.setText(f"WinUAE: {native_path}")
                self.winuae_action.setToolTip(native_path)
            else:
                self.winuae_action.setText("WinUAE")
                self.winuae_action.setToolTip("Pfad zu WinUAE auswählen")

        def choose_winuae(self, _checked: bool = False) -> None:
            if self.winuae_path:
                saved_path = Path(self.winuae_path)
                initial_path = (
                    saved_path.parent
                    if saved_path.parent.is_dir()
                    else self.current_directory
                )
            else:
                initial_path = self.current_directory

            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "WinUAE-Programm auswählen",
                str(initial_path),
                "WinUAE (winuae64.exe winuae.exe *.exe);;Alle Dateien (*)",
            )
            if filename:
                self.winuae_path = str(Path(filename).resolve())
                self.settings.setValue(
                    "emulator/winuae_path",
                    self.winuae_path,
                )
                self._update_winuae_action_text()
                self.log(f"WinUAE ausgewählt: {self.winuae_path}")

        def _choose_dism_image(self) -> Optional[Path]:
            selected_path = self.selected_file_path()
            if (
                selected_path is not None
                and selected_path.is_file()
                and selected_path.suffix.lower() == ".d64"
            ):
                return selected_path.resolve()

            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "D64-Diskettenabbild für DISM auswählen",
                str(self.current_directory),
                "D64-Diskettenabbilder (*.d64);;Alle Dateien (*)",
            )
            return Path(filename).resolve() if filename else None

        def _dism_arguments(self, image_path: Path) -> Optional[list[str]]:
            arguments = [str(image_path)]
            option_actions = (
                (self.dism_extract_action, "--extract-prg"),
                (self.dism_bam_action, "--bam"),
                (self.dism_startup_action, "--startup"),
                (self.dism_verbose_action, "--verbose"),
                (self.dism_analyze_action, "--analyze-prg"),
                (self.dism_disassemble_action, "--disassemble"),
                (self.dism_ram_image_action, "--image-ram"),
            )
            for action, option in option_actions:
                if action.isChecked():
                    arguments.append(option)

            if self.dism_vice_action.isChecked():
                if not self.dism_vice_path:
                    self.show_error(
                        "VICE-Pfad fehlt",
                        "Bitte über den DISM-Menüeintrag VICE das "
                        "VICE-Programm auswählen.",
                    )
                    return None
                vice_path = Path(self.dism_vice_path)
                if not vice_path.is_file():
                    self.show_error(
                        "VICE nicht gefunden",
                        f"Das ausgewählte VICE-Programm existiert nicht:\n{vice_path}",
                    )
                    return None
                arguments.extend(("--vice", str(vice_path)))

            return arguments

        @staticmethod
        def _display_dism_command(arguments: list[str]) -> str:
            displayed = []
            for argument in arguments:
                if any(character.isspace() for character in argument):
                    displayed.append(f'"{argument}"')
                else:
                    displayed.append(argument)
            return " ".join(displayed)

        def start_dism(self) -> None:
            if self.dism_thread is not None and self.dism_thread.isRunning():
                self.statusBar().showMessage("DISM wird bereits ausgeführt")
                return

            image_path = self._choose_dism_image()
            if image_path is None:
                self.statusBar().showMessage("DISM-Start abgebrochen")
                return

            arguments = self._dism_arguments(image_path)
            if arguments is None:
                return

            self.dism_content_list.clear()
            self.dism_summary.setText(
                f"<b>DISM läuft:</b><br>{image_path.name}"
            )
            self.right_panel_tabs.setCurrentWidget(self.information_panel_tab)
            self.right_info_tabs.setCurrentWidget(self.dism_info_tab)
            self.right_dock.show()
            self.right_dock.raise_()
            self.bottom_dock.show()
            self.dism_start_action.setEnabled(False)
            self.statusBar().showMessage(f"DISM analysiert {image_path.name} …")
            self.log(
                "DISM START: " + self._display_dism_command(arguments)
            )

            self.dism_thread = QThread(self)
            self.dism_worker = DismWorker(arguments)
            self.dism_worker.moveToThread(self.dism_thread)
            self.dism_thread.started.connect(self.dism_worker.run)
            self.dism_worker.finished.connect(self._dism_finished)
            self.dism_worker.finished.connect(self.dism_thread.quit)
            self.dism_worker.finished.connect(self.dism_worker.deleteLater)
            self.dism_thread.finished.connect(self._dism_thread_finished)
            self.dism_thread.finished.connect(self.dism_thread.deleteLater)
            self.dism_thread.start()

        def _dism_finished(
            self,
            exit_code: int,
            standard_output: str,
            error_output: str,
        ) -> None:
            complete_output = standard_output + error_output
            self.dism_content_list.clear()
            if complete_output:
                for line in complete_output.split("\n"):
                    self.dism_content_list.addItem(line)
                self.log(complete_output.rstrip("\n"))
            else:
                self.dism_content_list.addItem("(keine Konsolenausgabe)")

            if exit_code == 0:
                self.dism_summary.setText("<b>DISM erfolgreich beendet</b>")
                self.statusBar().showMessage("DISM erfolgreich beendet")
                self.populate_file_list()
            else:
                self.dism_summary.setText(
                    f"<b>DISM mit Fehlercode {exit_code} beendet</b>"
                )
                self.statusBar().showMessage(
                    f"DISM mit Fehlercode {exit_code} beendet"
                )
                self.show_error(
                    "DISM-Fehler",
                    error_output.strip()
                    or f"Die Programmlogik wurde mit Code {exit_code} beendet.",
                )

        def _dism_thread_finished(self) -> None:
            self.dism_start_action.setEnabled(True)
            self.dism_worker = None
            self.dism_thread = None

        def _create_central_widget(self) -> None:
            self.document_tabs = QTabWidget(self)
            self.document_tabs.setObjectName("document_tabs")
            self.document_tabs.setDocumentMode(True)
            self.document_tabs.setMovable(True)
            self.document_tabs.setTabsClosable(False)
            self.document_tabs.setUsesScrollButtons(True)
            self.document_tabs.currentChanged.connect(
                self._current_document_changed
            )
            self.document_tabs.tabBar().setContextMenuPolicy(
                Qt.CustomContextMenu
            )
            self.document_tabs.tabBar().customContextMenuRequested.connect(
                self._show_document_tab_context_menu
            )
            self.setCentralWidget(self.document_tabs)
            self._update_document_actions()

        # ----- Dokument-Editor --------------------------------------------

        def _toolbar_symbol_icon(self, symbol: str) -> QIcon:
            """Erzeugt skalierbare Toolbar-Symbole ohne externe Bilddateien."""
            pixmap = QPixmap(28, 28)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            if symbol in {"zoom_in", "zoom_out"}:
                icon_color = (
                    QColor(238, 238, 238)
                    if self.dark_mode_enabled
                    else QColor(45, 45, 45)
                )
                painter.setPen(
                    QPen(icon_color, 2.2, Qt.SolidLine, Qt.RoundCap)
                )
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(3.5, 3.5, 14.0, 14.0))
                painter.drawLine(QPointF(15.5, 15.5), QPointF(24.0, 24.0))
                painter.drawLine(QPointF(7.0, 10.5), QPointF(14.0, 10.5))
                if symbol == "zoom_in":
                    painter.drawLine(QPointF(10.5, 7.0), QPointF(10.5, 14.0))
            elif symbol == "help":
                icon_color = (
                    QColor(238, 238, 238)
                    if self.dark_mode_enabled
                    else QColor(45, 45, 45)
                )
                painter.setPen(QPen(icon_color, 2.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(3.0, 3.0, 22.0, 22.0))
                help_font = QFont(painter.font())
                help_font.setBold(True)
                help_font.setPointSize(14)
                painter.setFont(help_font)
                painter.drawText(QRectF(3.0, 1.0, 22.0, 24.0), Qt.AlignCenter, "?")
            elif symbol == "play":
                icon_color = (
                    QColor(255, 255, 255)
                    if self.dark_mode_enabled
                    else QColor(0, 0, 0)
                )
                triangle = QPainterPath()
                triangle.moveTo(QPointF(8.0, 5.0))
                triangle.lineTo(QPointF(23.0, 14.0))
                triangle.lineTo(QPointF(8.0, 23.0))
                triangle.closeSubpath()
                painter.setPen(Qt.NoPen)
                painter.setBrush(icon_color)
                painter.drawPath(triangle)
            elif symbol == "sun":
                painter.setPen(QPen(QColor(230, 150, 0), 1.8, Qt.SolidLine, Qt.RoundCap))
                painter.setBrush(QColor(255, 205, 35))
                painter.drawEllipse(QRectF(9.0, 9.0, 10.0, 10.0))
                for start, end in (
                    ((14, 2), (14, 6)), ((14, 22), (14, 26)),
                    ((2, 14), (6, 14)), ((22, 14), (26, 14)),
                    ((5.5, 5.5), (8, 8)), ((20, 20), (22.5, 22.5)),
                    ((20, 8), (22.5, 5.5)), ((5.5, 22.5), (8, 20)),
                ):
                    painter.drawLine(QPointF(*start), QPointF(*end))
            elif symbol == "close_white":
                painter.setPen(
                    QPen(QColor(255, 255, 255), 2.0, Qt.SolidLine, Qt.RoundCap)
                )
                painter.drawLine(QPointF(7.0, 7.0), QPointF(21.0, 21.0))
                painter.drawLine(QPointF(21.0, 7.0), QPointF(7.0, 21.0))
            elif symbol == "moon":
                moon = QPainterPath()
                moon.addEllipse(QRectF(5.0, 3.0, 18.0, 22.0))
                cutout = QPainterPath()
                cutout.addEllipse(QRectF(11.0, 0.5, 17.0, 20.0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(55, 70, 125))
                painter.drawPath(moon.subtracted(cutout))

            painter.end()
            return QIcon(pixmap)

        def _make_editor_font(self) -> QFont:
            available = {
                family.casefold(): family
                for family in QFontDatabase().families()
            }
            family = available.get("consolas", "Courier New")
            font = QFont(family, self.editor_font_size)
            font.setFixedPitch(True)
            font.setStyleHint(QFont.Monospace)
            return font

        def _documents(self) -> Iterable[DocumentEditor]:
            for index in range(self.document_tabs.count()):
                document = self.document_tabs.widget(index)
                if isinstance(document, DocumentEditor):
                    yield document

        def _apply_editor_font(self) -> None:
            font = self._make_editor_font()
            for document in self._documents():
                document.set_editor_font(font)

        def increase_editor_font(self) -> None:
            self._change_editor_font_size(1)

        def decrease_editor_font(self) -> None:
            self._change_editor_font_size(-1)

        def _update_zoom_action_state(self) -> None:
            self.zoom_out_action.setEnabled(
                self.editor_font_size > self.MIN_EDITOR_FONT_SIZE
            )
            self.zoom_in_action.setEnabled(
                self.editor_font_size < self.MAX_EDITOR_FONT_SIZE
            )

        def _change_editor_font_size(self, step: int) -> None:
            new_size = max(
                self.MIN_EDITOR_FONT_SIZE,
                min(self.MAX_EDITOR_FONT_SIZE, self.editor_font_size + step),
            )
            if new_size == self.editor_font_size:
                self.statusBar().showMessage(
                    f"Minimale Editor-Schriftgröße: {self.MIN_EDITOR_FONT_SIZE} Punkt"
                )
                self._update_zoom_action_state()
                return

            self.editor_font_size = new_size
            self._apply_editor_font()
            self._update_zoom_action_state()
            self.statusBar().showMessage(
                f"Editor-Schriftgröße: {self.editor_font_size} Punkt"
            )

        @staticmethod
        def _dark_application_palette() -> QPalette:
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(32, 38, 48))
            palette.setColor(QPalette.WindowText, QColor(235, 238, 242))
            palette.setColor(QPalette.Base, QColor(22, 27, 35))
            palette.setColor(QPalette.AlternateBase, QColor(40, 47, 59))
            palette.setColor(QPalette.ToolTipBase, QColor(45, 55, 70))
            palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(235, 238, 242))
            palette.setColor(QPalette.Button, QColor(45, 53, 66))
            palette.setColor(QPalette.ButtonText, QColor(235, 238, 242))
            palette.setColor(QPalette.BrightText, QColor(255, 90, 90))
            palette.setColor(QPalette.Link, QColor(95, 175, 255))
            palette.setColor(QPalette.Highlight, QColor(42, 105, 170))
            palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
            palette.setColor(
                QPalette.Disabled,
                QPalette.WindowText,
                QColor(125, 132, 142),
            )
            palette.setColor(
                QPalette.Disabled,
                QPalette.Text,
                QColor(125, 132, 142),
            )
            palette.setColor(
                QPalette.Disabled,
                QPalette.ButtonText,
                QColor(125, 132, 142),
            )
            return palette
        
        # Erzeugt die gelben Scrollpfeile fuer das dunkle Qt-Theme.
        def _create_scrollbar_arrow_assets(self) -> dict:
            if not self.theme_asset_directory.isValid():
                return {}

            asset_directory = Path(self.theme_asset_directory.path())
            directions = {
                "up"   : ((7.0, 3.0), (3.0, 10.0), (11.0, 10.0)),
                "down" : ((3.0, 4.0), (11.0, 4.0), ( 7.0, 11.0)),
                "left" : ((3.0, 7.0), (10.0, 3.0), (10.0, 11.0)),
                "right": ((4.0, 3.0), (11.0, 7.0), ( 4.0, 11.0)),
            }
            assets = {}

            for direction, points in directions.items():
                pixmap = QPixmap(14, 14)
                pixmap.fill(Qt.transparent)

                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 230, 0))

                arrow = QPainterPath()
                arrow.moveTo(QPointF(*points[0]))
                arrow.lineTo(QPointF(*points[1]))
                arrow.lineTo(QPointF(*points[2]))
                arrow.closeSubpath()
                
                painter.drawPath(arrow)
                painter.end()

                filename = asset_directory / f"scrollbar_{direction}.png"
                if pixmap.save(str(filename), "PNG"):
                    assets[direction] = filename.as_posix()

            return assets

        def _dark_application_stylesheet(self) -> str:
            _CSS_ZLIB_B85 = (
                b'c-p;I%Wj-76y5U`RM}=Ez~;T`v|UtcrACRGwT;bSg~13+GisH8?`3$uW|~MT8yH{voO|y%w&(6a%Jf0x`X4QlsVoBhCO$u*MoIK^'
                b'C}fqfT^F(#a<Ky;SuhR*W`5F3nF^-gIM~G=4YiywCbC1Iqx=+VFWTLAo>hBN-0J5qc-4%}z`Y`>D&ZU0*VqipK}Ogo#wq8qH3kg='
                b'q4+T<dCDWjS<5jS-2f+!Pe{0^x&;qlc}@zVWSv~X#UWAWddGc%Wj1mQ7jin1;vlj>$Iub4t-LL?=3n*;JGSZIP%Cp1P5Sj&Mo*7|'
                b'9k>btB~;2c^7oO2&1G}?{@XR4;wQBusW?DtDUVf?7oi<NPBOlpUsqT&|J-Xu=)dK{VvacpFTwU{IuJ9Bu44n!75Nasp3PR}8-pbB'
                b'7bNiE3Kl{fx6%`lJ&KIU=aB(wr{<|p3ZR07WNb^5p=a9NkE%@el~OVrZ!IIXVtaLKAq+{d^`7~T>-t@2R}dzuvNcTK$FcDS?xq3j'
                b'*<uqjJMLk-Vb}Cb-<#v)1ux6Zz2qVj@dXmL8;ehoqJ&3Jn@HHEzPUt-eKU$z)gB=;Q4*SNLi<*X`~@_0-LcUC?J^JhMx)_3k?}7~'
                b'C@{cBTB?FX>OL3QUY=m&lRQ!hpCfs@J-EVdIwrM%rg5T>+3v!bG)!8Y$=f?><_>G(4)98IAiNA!1+k2(a#>qH-c{HP^vA?Pl`&?g'
                b'!3u02(gx&_WOD&7TnH}%!a(yC&itQ(KmS)fYM0zcg-q*%K7g&JL_|_Z;aM=1fKIq>dUrY0zjUL0%`OrH9?uvQZps|6+k<D!aTM9E'
                b'yO}J!xSA}CiBH!(<GCIs>z=vDx^kY>d&smYT_g<N+oj-(e(~)jTvl`%o_DRkbeE->hUwYs+W{eLdu*P|8X1g5GE*>Tm&;Pr`Ubj^'
                b'c{q;9LY$>*B)nSU7A%!;LLFa;oRh<)=1szLNjf`C4VnPyZ{R=ApZ2%&s4;fw8$CLqsa@LY`pzaDXy0VhVfltpCuP0ARVQ?-u4?|#'
                b'z22?Yk&C*Xx7hVk6K4~)EjwNq$s$`y+0Xq8nHE5V'
            )
            stylesheet = _d64info_zlib.decompress(
                _d64info_base64.b85decode(_CSS_ZLIB_B85)
            ).decode("utf-8")
 
            arrows = self.scrollbar_arrow_assets
            if len(arrows) == 4:
                _SCROLLBAR_ARROWS_ZLIB_B85 = (
                    b'c-jjLPA<yN$#F_7va%{I&`m5V$}hJnOD!tNOis*EsOHMdO-xU<QYbCT(NI#=C@s(|R?@WQD$h(Q$*@u|G%2XC=E_LTOwTBR@o'
                    b'KpOk&H~qFV7=nC`b*7#^$7^l|YTn$S=yQ%FipoVlYS*i3S&eqzIb~Rz}!p0KZ6cw*'
                )
                _SCROLLBAR_ARROWS_TEMPLATE = _d64info_zlib.decompress(
                    _d64info_base64.b85decode(_SCROLLBAR_ARROWS_ZLIB_B85)
                ).decode("utf-8")
                stylesheet += _SCROLLBAR_ARROWS_TEMPLATE % arrows

            # Der Projekt-Oeffnen-Button muss im Dunkelmodus dieselbe dunkle
            # Flaeche wie die uebrigen Projekt-Steuerelemente verwenden. Der
            # native Windows-Stil zeichnet QToolButton sonst grau.
            stylesheet += """
QToolButton#project_open_button {
    color: #ffffff;
    background-color: #2d3746;
    border: 1px solid #596779;
    border-radius: 3px;
    padding: 3px;
}
QToolButton#project_open_button:hover {
    background-color: #414d5f;
    border-color: #718198;
}
QToolButton#project_open_button:pressed {
    background-color: #202630;
}
QToolButton#project_open_button:disabled {
    color: #7d848e;
    background-color: #252c37;
    border-color: #3d4755;
}
QToolButton#document_tab_close_button {
    background-color: #475365;
    border: 1px solid #66758a;
    border-radius: 3px;
    padding: 1px;
}
QToolButton#document_tab_close_button:hover {
    background-color: #b23b3b;
    border-color: #e06a6a;
}
QFrame#status_keyboard_panel,
QFrame#status_file_panel,
QFrame#status_cursor_panel {
    background-color: #202630;
    border-left: 1px solid #596779;
}
"""

            return stylesheet

        # Liefert eine explizite Palette fuer modale Meldungsdialoge.
        def _message_box_palette(self) -> QPalette:
            if self.dark_mode_enabled:
                palette = self._dark_application_palette()
                palette.setColor(QPalette.Window, QColor(32, 38, 48))
                palette.setColor(QPalette.Base, QColor(22, 27, 35))
                palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
                palette.setColor(QPalette.Text, QColor(255, 255, 255))
                palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
                return palette

            palette = QPalette(self.light_application_palette)
            palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
            return palette

        # Erzwingt lesbare Dialogfarben unabhaengig vom Windows-Stil.
        def _message_box_stylesheet(self) -> str:
            if self.dark_mode_enabled:
                return """
QMessageBox {
color: #ffffff;
background-color: #202630;
}
QMessageBox QLabel {
color: #ffffff;
background-color: transparent;
}
QMessageBox QPushButton {
min-width: 78px;
color: #ffffff;
background-color: #343e4d;
border: 1px solid #596779;
border-radius: 3px;
padding: 5px 10px;
}
QMessageBox QPushButton:hover {
background-color: #414d5f;
border-color: #718198;
}
QMessageBox QPushButton:pressed {
background-color: #27313e;
}
QMessageBox QPushButton:default {
border: 2px solid #4f91cf;
}
"""

            return """
QMessageBox {
color: #000000;
background-color: #f0f0f0;
}
QMessageBox QLabel {
color: #000000;
background-color: transparent;
}
QMessageBox QPushButton {
min-width: 78px;
color: #000000;
background-color: #f5f5f5;
border: 1px solid #9b9b9b;
border-radius: 3px;
padding: 5px 10px;
}
QMessageBox QPushButton:hover {
background-color: #e4f1fb;
border-color: #5b9bd5;
}
QMessageBox QPushButton:pressed {
background-color: #d5e8f6;
}
QMessageBox QPushButton:default {
border: 2px solid #2a69aa;
}
"""

        def _create_message_box(
            self,
            icon,
            title: str,
            text: str,
            *,
            buttons=QMessageBox.Ok,
            default_button=QMessageBox.NoButton,
            rich_text: bool = False,
        ) -> QMessageBox:
            """Erzeugt eine garantiert zum aktuellen Modus passende MessageBox."""
            dialog = QMessageBox(self)
            dialog.setObjectName("themed_message_box")
            dialog.setWindowIcon(self.windowIcon())
            dialog.setWindowTitle(title)
            dialog.setIcon(icon)
            dialog.setTextFormat(Qt.RichText if rich_text else Qt.PlainText)
            dialog.setText(text)
            dialog.setStandardButtons(buttons)
            if default_button != QMessageBox.NoButton:
                dialog.setDefaultButton(default_button)

            dialog.setAttribute(Qt.WA_StyledBackground, True)
            dialog.setPalette(self._message_box_palette())
            dialog.setStyleSheet(self._message_box_stylesheet())
            return dialog

        def _show_message_box(self, icon, title: str, text: str, **options):
            dialog = self._create_message_box(icon, title, text, **options)
            return dialog.exec_()

        def _apply_application_theme(self, enabled: bool) -> None:
            application = QApplication.instance()
            if enabled:
                application.setPalette(self._dark_application_palette())
                dark_stylesheet = self._dark_application_stylesheet()
                if self.light_application_stylesheet:
                    dark_stylesheet = (
                        self.light_application_stylesheet
                        + "\n"
                        + dark_stylesheet
                    )
                application.setStyleSheet(dark_stylesheet)
            else:
                application.setPalette(self.light_application_palette)
                application.setStyleSheet(self.light_application_stylesheet)

            # QApplication verteilt den Palettenwechsel an alle vorhandenen
            # Widgets. update() sorgt zusaetzlich dafuer, dass auch Dock-Titel
            # und bereits sichtbare Item-Views sofort neu gezeichnet werden.
            for widget in application.allWidgets():
                widget.update()
                if isinstance(widget, ChmViewerDialog):
                    widget.set_dark_mode(enabled)

        def toggle_editor_theme(self) -> None:
            self.dark_mode_enabled = not self.dark_mode_enabled
            self._apply_application_theme(self.dark_mode_enabled)
            for document in self._documents():
                document.set_dark_mode(self.dark_mode_enabled)

            self.chm_viewer_action.setIcon(self._toolbar_symbol_icon("help"))
            self.zoom_in_action.setIcon(self._toolbar_symbol_icon("zoom_in"))
            self.zoom_out_action.setIcon(self._toolbar_symbol_icon("zoom_out"))
            self.dism_start_menu.setIcon(self._toolbar_symbol_icon("play"))

            if self.dark_mode_enabled:
                self.theme_action.setIcon(self._toolbar_symbol_icon("sun"))
                self.theme_action.setText("Hellmodus einschalten")
                self.theme_action.setToolTip("Hellmodus einschalten")
                self.theme_action.setStatusTip(
                    "Gesamte Anwendung auf Hellmodus umschalten"
                )
                mode_text = "Dunkelmodus"
            else:
                self.theme_action.setIcon(self._toolbar_symbol_icon("moon"))
                self.theme_action.setText("Dunkelmodus einschalten")
                self.theme_action.setToolTip("Dunkelmodus einschalten")
                self.theme_action.setStatusTip(
                    "Gesamte Anwendung auf Dunkelmodus umschalten"
                )
                mode_text = "Hellmodus"

            self.statusBar().showMessage(f"{mode_text} eingeschaltet")

        def current_document(self) -> Optional[DocumentEditor]:
            widget = self.document_tabs.currentWidget()
            return widget if isinstance(widget, DocumentEditor) else None

        def _document_index(self, document: DocumentEditor) -> int:
            return self.document_tabs.indexOf(document)

        def _find_open_document(self, path: Path) -> Optional[DocumentEditor]:
            wanted = os.path.normcase(str(Path(path).resolve()))
            for index in range(self.document_tabs.count()):
                document = self.document_tabs.widget(index)
                if not isinstance(document, DocumentEditor):
                    continue
                if document.path is None:
                    continue
                current = os.path.normcase(str(document.path.resolve()))
                if current == wanted:
                    return document
            return None

        @staticmethod
        def _decode_text_file(path: Path) -> Tuple[str, str, str, bytes]:
            raw = path.read_bytes()

            if raw.startswith(b"\xef\xbb\xbf"):
                encodings = ("utf-8-sig",)
            elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                encodings = ("utf-16",)
            else:
                encodings = ("utf-8", "cp1252", "latin-1")

            text = None
            selected_encoding = "utf-8"
            for encoding in encodings:
                try:
                    text = raw.decode(encoding)
                    selected_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if text is None:
                raise UnicodeError("Die Zeichenkodierung konnte nicht erkannt werden.")

            crlf_count = raw.count(b"\r\n")
            lf_count = raw.count(b"\n") - crlf_count
            cr_count = raw.count(b"\r") - crlf_count
            if crlf_count >= max(lf_count, cr_count) and crlf_count:
                newline = "\r\n"
            elif cr_count > lf_count:
                newline = "\r"
            else:
                newline = "\n"

            return text, selected_encoding, newline, raw

        def new_document(
            self,
            _checked: bool = False,
            *,
            text: str = "",
            display_name: Optional[str] = None,
        ) -> DocumentEditor:
            self.untitled_counter += 1
            dark_mode = self.application_dark_mode(
                self.dark_mode_enabled
            )
            document = DocumentEditor(
                self.document_tabs,
                untitled_number=self.untitled_counter,
                text=text,
                editor_font=self._make_editor_font(),
                dark_mode=dark_mode,
            )
            if display_name:
                document.custom_display_name = display_name
                document.update_syntax_highlighting()
            self._add_document_tab(document)
            document.focus_preferred_editor()
            self.log(f"Neue Textdatei angelegt: {document.display_name}")
            return document

        def _ensure_project_for_new_document(self) -> Path:
            """Stellt eine speicherbare .pro-Datei für neue Dokumente bereit."""
            if self.current_project_path is None:
                number = 1
                while True:
                    candidate = self.current_directory / (
                        f"Unbenannt_Projekt_{number}.pro"
                    )
                    if not candidate.exists():
                        break
                    number += 1
                self.current_project_path = candidate.resolve()
                if hasattr(self, "project_path_edit"):
                    self.project_path_edit.setText(
                        str(self.current_project_path)
                    )
                save_project_ini(
                    self.current_project_path,
                    self.collect_project_entries()
                    if hasattr(self, "project_tree")
                    else empty_project_entries(),
                )
                self.set_project_modified(False)
                self.log(
                    f"Automatisches Projekt angelegt: {self.current_project_path}"
                )
            return Path(self.current_project_path)

        def _new_project_item_for_category(
            self, category_key: str
        ) -> Optional[QTreeWidgetItem]:
            self._ensure_project_for_new_document()
            root = self.project_root_items.get(category_key)
            if root is None:
                return None
            return self.create_new_project_item(root)

        def new_source_document(self, language: str) -> Optional[DocumentEditor]:
            key = str(language).casefold()
            category_map = {
                "basic": "basic",
                "assembler": "assembler",
                "pascal": "pascal",
                "c": "c",
                "text": "text_files",
            }
            category_key = category_map.get(key, "text_files")
            child = self._new_project_item_for_category(category_key)
            if child is None:
                return None
            return self.current_document()

        def new_character_map(self, _checked: bool = False) -> None:
            self._new_project_item_for_category("character_maps")

        def new_text_screen(self, _checked: bool = False) -> None:
            self._new_project_item_for_category("char_screens")

        def new_pixel_screen(self, _checked: bool = False) -> None:
            self._new_project_item_for_category("pixel_screens")
            self._update_editor_status_panels()

        def open_document_dialog(self) -> None:
            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "Datei öffnen",
                str(self.current_directory),
                (
                    "Unterstützte Dateien "
                    "(*.txt *.text *.log *.md *.asm *.s *.a65 *.m68k *.inc "
                    "*.pas *.pp *.c *.bas *.basic *.pro *.prg *.amiga *.adf *.ram *.bin "
                    "*.chr *.charset *.pal *.palette *.scr *.screen "
                    "*.px16 *.pixel *.pix);;"
                    "Projektdateien (*.pro);;"
                    "BASIC-Dateien (*.bas *.basic);;"
                    "C-Dateien (*.c *.h);;"
                    "Pascaldateien (*.pas *.pp);;"
                    "Assemblerdateien (*.asm *.s *.a65 *.m68k *.inc);;"
                    "C64-Zeichensätze (*.chr *.charset);;"
                    "C64-Paletten (*.pal *.palette);;"
                    "C64-Textbildschirme (*.scr *.screen);;"
                    "C64-Pixelbildschirme (*.px16 *.pixel *.pix);;"
                    "Binärdateien (*.prg *.amiga *.adf *.ram *.bin);;"
                    "Alle Dateien (*)"
                ),
            )
            if filename:
                self.open_document(Path(filename))

        def open_document(self, path: Path) -> bool:
            try:
                path = Path(path).expanduser().resolve()
            except OSError as exc:
                self.show_error("Pfadfehler", str(exc))
                return False

            if path.suffix.lower() in {".chr", ".charset"}:
                self.show_character_editor(initial_path=path)
                return True

            if path.suffix.lower() in {".pal", ".palette"}:
                self.show_palette_editor(initial_path=path)
                return True

            if path.suffix.lower() in {".scr", ".screen"}:
                self.show_text_screen_editor(initial_path=path)
                return True

            if path.suffix.lower() in {".px16", ".pixel", ".pix"}:
                self.show_pixel_screen_editor(initial_path=path)
                return True

            if path.suffix.lower() == ".pro":
                return self.load_project_file(path)

            existing = self._find_open_document(path)
            if existing is not None:
                self.document_tabs.setCurrentWidget(existing)
                self._apply_document_theme(existing)
                existing.focus_preferred_editor()
                self.statusBar().showMessage(f"Bereits geöffnet: {path.name}")
                return True

            try:
                text, encoding, newline, raw_bytes = self._decode_text_file(path)
            except (OSError, UnicodeError) as exc:
                self.show_error(
                    "Datei konnte nicht geöffnet werden",
                    f"Die Datei konnte nicht als Text geladen werden:\n{path}\n\n{exc}",
                )
                return False

            self.untitled_counter += 1
            dark_mode = self.application_dark_mode(
                self.dark_mode_enabled
            )
            document = DocumentEditor(
                self.document_tabs,
                untitled_number=self.untitled_counter,
                path=path,
                text=text,
                encoding=encoding,
                newline=newline,
                raw_bytes=raw_bytes,
                editor_font=self._make_editor_font(),
                dark_mode=dark_mode,
            )
            self._add_document_tab(document)
            document.focus_preferred_editor()
            self.log(f"Datei im Editor geöffnet: {path}")
            self.statusBar().showMessage(
                f"{path.name} - Kodierung: {encoding}"
            )
            return True

        def show_character_editor(
            self,
            _checked: bool = False,
            *,
            initial_path: Optional[Path] = None,
        ) -> None:
            dialog = self.character_editor_dialog
            if dialog is None or dialog.isHidden():
                dialog = C64CharacterEditorDialog(
                    self,
                    initial_directory=self.current_directory,
                    initial_path=initial_path,
                )
                dialog.setAttribute(Qt.WA_DeleteOnClose, True)
                dialog.destroyed.connect(
                    lambda _object=None: setattr(
                        self,
                        "character_editor_dialog",
                        None,
                    )
                )
                self.character_editor_dialog = dialog
            elif initial_path is not None:
                dialog.load_file(Path(initial_path))

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            self.statusBar().showMessage("C64 Character-Editor geöffnet")

        def show_palette_editor(
            self,
            _checked: bool = False,
            *,
            initial_path: Optional[Path] = None,
        ) -> None:
            dialog = self.palette_editor_dialog
            if dialog is None or dialog.isHidden():
                dialog = C64PaletteEditorDialog(
                    self,
                    initial_directory=self.current_directory,
                    initial_path=initial_path,
                )
                dialog.setAttribute(Qt.WA_DeleteOnClose, True)
                dialog.destroyed.connect(
                    lambda _object=None: setattr(
                        self,
                        "palette_editor_dialog",
                        None,
                    )
                )
                self.palette_editor_dialog = dialog
            elif initial_path is not None:
                dialog.load_file(Path(initial_path))

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            self.statusBar().showMessage("C64 Paletten-Editor geöffnet")

        def show_text_screen_editor(
            self,
            _checked: bool = False,
            *,
            initial_path: Optional[Path] = None,
        ) -> None:
            dialog = self.text_screen_editor_dialog
            if dialog is None or dialog.isHidden():
                dialog = C64TextScreenEditorDialog(
                    self,
                    initial_directory=self.current_directory,
                    initial_path=initial_path,
                )
                dialog.setAttribute(Qt.WA_DeleteOnClose, True)
                dialog.destroyed.connect(
                    lambda _object=None: setattr(
                        self,
                        "text_screen_editor_dialog",
                        None,
                    )
                )
                self.text_screen_editor_dialog = dialog
            elif initial_path is not None:
                dialog.load_file(Path(initial_path))

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            self.statusBar().showMessage("C64 Text-Bildschirm-Editor geöffnet")

        def show_pixel_screen_editor(
            self,
            _checked: bool = False,
            *,
            initial_path: Optional[Path] = None,
        ) -> None:
            dialog = self.pixel_screen_editor_dialog
            if dialog is None or dialog.isHidden():
                dialog = C64PixelScreenEditorDialog(
                    self,
                    initial_directory=self.current_directory,
                    initial_path=initial_path,
                )
                dialog.setAttribute(Qt.WA_DeleteOnClose, True)
                dialog.destroyed.connect(
                    lambda _object=None: setattr(
                        self,
                        "pixel_screen_editor_dialog",
                        None,
                    )
                )
                self.pixel_screen_editor_dialog = dialog
            elif initial_path is not None:
                dialog.load_file(Path(initial_path))

            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            self.statusBar().showMessage("C64 Pixel-Bildschirm-Editor geöffnet")

        def _add_document_tab(self, document: DocumentEditor) -> None:
            index = self.document_tabs.addTab(document, document.display_name)
            self.document_tabs.setTabToolTip(index, self._document_tooltip(document))

            close_button = QToolButton(self.document_tabs.tabBar())
            close_button.setObjectName("document_tab_close_button")
            close_button.setAutoRaise(True)
            close_button.setIcon(self._toolbar_symbol_icon("close_white"))
            close_button.setIconSize(QSize(12, 12))
            close_button.setFixedSize(18, 18)
            close_button.setStyleSheet(
                "QToolButton { background-color:#475365;"
                "border:1px solid #66758a; border-radius:3px; padding:1px; }"
                "QToolButton:hover { background-color:#b23b3b;"
                "border-color:#e06a6a; }"
                "QToolButton:pressed { background-color:#7d2828; }"
            )
            close_button.setToolTip("Registerkarte schließen")
            close_button.clicked.connect(
                lambda checked=False, value=document: self.close_document(value)
            )
            self.document_tabs.tabBar().setTabButton(
                index, QTabBar.LeftSide, close_button
            )
            self.document_tabs.tabBar().setTabButton(index, QTabBar.RightSide, None)

            document.modification_changed.connect(
                lambda modified=False, value=document: self._document_modified(
                    value, modified
                )
            )
            document.assemble_requested.connect(self.assemble_document)
            document.start_requested.connect(self.start_assembled_document)
            document.assemble_generated_requested.connect(
                self.assemble_generated_document
            )
            document.start_generated_requested.connect(
                self.start_generated_assembly_document
            )
            document.coff_requested.connect(self.create_coff32_object_document)
            document.context_help_requested.connect(
                self.show_context_help_for_document
            )
            document.raw_editor.bookmarks_changed.connect(
                self._refresh_favorites_menu
            )
            document.generated_assembly_editor.bookmarks_changed.connect(
                self._refresh_favorites_menu
            )
            document.raw_editor.cursorPositionChanged.connect(
                self._update_editor_status_panels
            )
            document.raw_editor.textChanged.connect(
                self._update_editor_status_panels
            )
            document.generated_assembly_editor.cursorPositionChanged.connect(
                self._update_editor_status_panels
            )
            document.generated_assembly_editor.textChanged.connect(
                self._update_editor_status_panels
            )
            document.views.currentChanged.connect(
                self._update_editor_status_panels
            )
            document.hex_editor.dataChanged.connect(
                self._update_editor_status_panels
            )
            self.document_tabs.setCurrentWidget(document)
            self._update_document_actions()
            self._update_document_tab(document)
            self._apply_document_theme(document)
            self._refresh_favorites_menu()

            # Nach der Rueckkehr in die Qt-Ereignisschleife ist der neue Tab
            # vollstaendig in seine Widget-Hierarchie eingebunden. Eine zweite
            # explizite Anwendung verhindert, dass eine spaete PaletteChange-
            # Verarbeitung die ASM-Farben wieder mit Standardwerten ersetzt.
            QTimer.singleShot(
                0,
                lambda value=document: self._apply_document_theme(value),
            )

        def _apply_document_theme(self, document: DocumentEditor) -> None:
            """Setzt die aktiven Editorfarben nach Erzeugen/Oeffnen erneut."""
            if self._document_index(document) < 0:
                return
            dark_mode = self.application_dark_mode(
                self.dark_mode_enabled
            )
            document.set_dark_mode(dark_mode)

        @staticmethod
        def _document_tooltip(document: DocumentEditor) -> str:
            if document.path is None:
                return "Noch nicht gespeichert"
            return str(document.path)

        def _document_modified(
            self, document: DocumentEditor, _modified: bool
        ) -> None:
            self._update_document_tab(document)

        def _update_document_tab(self, document: DocumentEditor) -> None:
            index = self._document_index(document)
            if index < 0:
                return
            marker = " *" if document.is_modified else ""
            self.document_tabs.setTabText(
                index, f"{document.display_name}{marker}"
            )
            self.document_tabs.setTabToolTip(
                index, self._document_tooltip(document)
            )
            if document is self.current_document():
                self.setWindowTitle(
                    f"{document.display_name}{marker} - Qt5 D64-Explorer"
                )

        def _current_document_changed(self, _index: int) -> None:
            self._update_document_actions()
            document = self.current_document()
            if document is None:
                self.setWindowTitle("Qt5 D64- und Dateisystem-Explorer")
                self._update_editor_status_panels()
                return
            self._update_document_tab(document)
            self._update_editor_status_panels()

        def _update_document_actions(self) -> None:
            has_document = self.current_document() is not None
            self.save_file_action.setEnabled(has_document)
            self.save_as_action.setEnabled(has_document)
            self.close_document_action.setEnabled(has_document)

        def save_current_document(self) -> bool:
            document = self.current_document()
            if document is None:
                return False
            return self._save_document(document, save_as=False)

        def save_current_document_as(self) -> bool:
            document = self.current_document()
            if document is None:
                return False
            return self._save_document(document, save_as=True)

        def _choose_document_filename(
            self, document: DocumentEditor
        ) -> Optional[Path]:
            if document.path is not None:
                initial = str(document.path)
            else:
                suggested_name = document.display_name
                if not Path(suggested_name).suffix:
                    suggested_name += ".txt"
                initial = str(self.current_directory / suggested_name)

            filename, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "Datei speichern unter",
                initial,
                (
                    "BASIC-Dateien (*.bas *.basic);;"
                    "C-Dateien (*.c *.h);;"
                    "Pascaldateien (*.pas *.pp);;"
                    "Assemblerdateien (*.asm *.s *.a65 *.m68k *.inc);;"
                    "Textdateien (*.txt);;"
                    "Binärdateien (*.prg *.amiga *.adf *.ram *.bin);;"
                    "Alle Dateien (*)"
                ),
            )
            return Path(filename).resolve() if filename else None

        def _save_document(
            self, document: DocumentEditor, *, save_as: bool
        ) -> bool:
            previous_path = document.path
            target = document.path
            if save_as or target is None:
                target = self._choose_document_filename(document)
                if target is None:
                    self.statusBar().showMessage("Speichern abgebrochen")
                    return False

            conflicting = self._find_open_document(target)
            if conflicting is not None and conflicting is not document:
                self.show_error(
                    "Datei bereits geöffnet",
                    "Die Zieldatei ist bereits in einer anderen Registerkarte "
                    f"geöffnet:\n{target}",
                )
                return False

            try:
                data = document.data_for_saving()
                target.parent.mkdir(parents=True, exist_ok=True)
                file_descriptor, temporary_name = tempfile.mkstemp(
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    dir=str(target.parent),
                )
                try:
                    with os.fdopen(file_descriptor, "wb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary_name, target)
                except Exception:
                    try:
                        os.unlink(temporary_name)
                    except OSError:
                        pass
                    raise
            except (OSError, UnicodeError) as exc:
                self.show_error(
                    "Datei konnte nicht gespeichert werden",
                    f"Die Datei wurde nicht gespeichert:\n{target}\n\n{exc}",
                )
                self.document_tabs.setCurrentWidget(document)
                return False

            document.path = target.resolve()
            document.custom_display_name = None
            document.update_syntax_highlighting()
            self._apply_document_theme(document)
            if previous_path != document.path:
                document.invalidate_assembly_result("Dateipfad geändert")
            document.mark_saved()
            self._update_document_tab(document)
            self.log(f"Datei gespeichert: {document.path}")
            self.statusBar().showMessage(f"Gespeichert: {document.path}")
            self._update_editor_status_panels()
            self._refresh_favorites_menu()
            if document.path.parent == self.current_directory:
                self.populate_file_list()
            return True

        @staticmethod
        def _assembler_output_path(
            document: DocumentEditor,
            assembly_source: str = "",
        ) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der Quelltext muss vor dem Erzeugen eines Programms "
                    "gespeichert werden."
                )
            suffix = ".prg"
            if document.build_target == "pe32":
                suffix = (
                    ".dll"
                    if getattr(document, "generated_source_kind", "program") == "library"
                    else ".exe"
                )
            elif document.build_target == "amiga":
                suffix = ".amiga"
                if assembly_source:
                    #from amiga500 import is_amiga_boot_source
                    if is_amiga_boot_source(assembly_source):
                        suffix = ".adf"
            return document.path.with_suffix(suffix)

        @staticmethod
        def _basic_assembly_output_path(document: DocumentEditor) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der BASIC-Quelltext muss zuerst gespeichert werden."
                )
            return document.path.with_name(
                document.path.stem + ".generated.asm"
            )

        @staticmethod
        def _pascal_assembly_output_path(document: DocumentEditor) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der Pascal-Quelltext muss zuerst gespeichert werden."
                )
            return document.path.with_name(
                document.path.stem
                + (
                    ".generated.amiga.asm"
                    if document.build_target == "amiga"
                    else (
                        ".generated.pe32.asm"
                        if document.build_target == "pe32"
                        else ".generated.asm"
                    )
                )
            )

        @staticmethod
        def _c_assembly_output_path(document: DocumentEditor) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der C-Quelltext muss zuerst gespeichert werden."
                )
            return document.path.with_name(
                document.path.stem
                + (
                    ".generated.amiga.asm"
                    if document.build_target == "amiga"
                    else (
                        ".generated.pe32.asm"
                        if document.build_target == "pe32"
                        else ".generated.asm"
                    )
                )
            )

        @staticmethod
        def _write_assembled_program(path: Path, data: bytes) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            file_descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=str(path.parent),
            )
            try:
                with os.fdopen(file_descriptor, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary_name, path)
            except Exception:
                try:
                    os.unlink(temporary_name)
                except OSError:
                    pass
                raise

        def _finish_compile_stage(
            self,
            document: DocumentEditor,
            generated,
            assembly_path: Path,
            language_name: str,
            *,
            is_unit: bool = False,
        ) -> bool:
            """Beendet nur Compile: ASM speichern, aber noch nicht assemblieren."""
            open_assembly = self._find_open_document(assembly_path)
            if open_assembly is not None and open_assembly.is_modified:
                message = (
                    "Die erzeugte ASM-Datei ist bereits geöffnet und enthält "
                    "ungespeicherte Änderungen:\n"
                    f"{assembly_path}\n\n"
                    "Speichere oder schließe diese Registerkarte vor dem "
                    "erneuten Kompilieren."
                )
                document.show_assembly_error(
                    message,
                    status_text="Ausgabe ist geöffnet",
                )
                self.show_error("ASM-Ausgabe kann nicht ersetzt werden", message)
                return False

            try:
                self._write_assembled_program(
                    assembly_path,
                    generated.assembly.encode("utf-8"),
                )
            except OSError as exc:
                message = (
                    "Die erzeugte Assemblerdatei konnte nicht gespeichert werden:\n"
                    f"{assembly_path}\n\n{exc}"
                )
                document.show_assembly_error(
                    message,
                    status_text="Ausgabefehler",
                )
                self.show_error("ASM-Ausgabe konnte nicht gespeichert werden", message)
                return False

            if open_assembly is not None:
                open_assembly.raw_editor.setPlainText(generated.assembly)
                open_assembly.mark_saved()
                open_assembly.invalidate_assembly_result("Neu erzeugt")
                self._update_document_tab(open_assembly)

            document.invalidate_assembly_result("Neu kompiliert")
            document.set_generated_assembly(
                generated.assembly,
                assembly_path,
                select_tab=True,
            )
            document.generated_source_kind = getattr(
                generated, "source_kind", "program"
            )
            document.generated_linked_assembly_files = tuple(
                getattr(generated, "linked_assembly_files", ()) or ()
            )
            document.generated_pe32_modules = tuple(
                getattr(generated, "linked_pe32_modules", ()) or ()
            )
            if is_unit:
                document.assemble_generated_button.setEnabled(False)
                document.generated_assembly_status_label.setText(
                    "Unit-ASM erzeugt – kein eigenständiges Programm"
                )

            target_name = document._build_target_name()
            warnings = tuple(getattr(generated, "warnings", ()) or ())
            notes = tuple(getattr(generated, "notes", ()) or ())
            diagnostic_lines = []
            if notes:
                diagnostic_lines.append("Hinweise:")
                diagnostic_lines.extend(f"  {item}" for item in notes)
            if warnings:
                if diagnostic_lines:
                    diagnostic_lines.append("")
                diagnostic_lines.append("Warnungen:")
                diagnostic_lines.extend(f"  {item}" for item in warnings)
            diagnostics = (
                "\n\n" + "\n".join(diagnostic_lines)
                if diagnostic_lines
                else ""
            )
            unit_note = (
                "\nProgramm     : Unit – kein eigenständiges Programm"
                if is_unit
                else "\nProgramm     : noch nicht erzeugt – jetzt Assemble verwenden"
            )
            document.hints_editor.setPlainText(
                f"{language_name} erfolgreich nach {target_name}-Assembler "
                "kompiliert\n\n"
                f"Quelle       : {document.display_name}\n"
                f"Assembler    : {assembly_path}"
                f"{unit_note}"
                f"{diagnostics}"
            )
            document.assembly_status_label.setText(
                f"ASM erzeugt: {assembly_path.name}"
            )
            self.log(
                f"COMPILE {language_name.upper()}: "
                f"{document.display_name} -> {assembly_path.name} "
                f"({target_name})"
            )
            message = (
                f"{language_name} mit {len(warnings)} Warnung(en) nach "
                f"Assembler kompiliert: {assembly_path.name}"
                if warnings
                else f"{language_name} nach Assembler kompiliert: "
                f"{assembly_path.name}"
            )
            self.statusBar().showMessage(message)
            if assembly_path.parent == self.current_directory:
                self.populate_file_list()
            return True

        def _compile_basic_document(self, document: DocumentEditor) -> bool:
            """C64 BASIC -> editierbarer MOS-6510-Assemblercode."""
            if document.build_target != "c64":
                document.set_build_target("c64")
            source = document.raw_editor.toPlainText()
            try:
                from c64basic import C64BasicError, compile_basic_to_assembly
                assembly_path = self._basic_assembly_output_path(document)
                generated = compile_basic_to_assembly(
                    source,
                    filename=str(document.path),
                    target="c64",
                )
            except (ImportError, C64BasicError) as exc:
                message = str(exc)
                error_line = getattr(exc, "line", 0) or 0
                document.show_assembly_error(
                    message,
                    error_line,
                    "Compilerfehler",
                )
                self.show_error("BASIC-Compilerfehler", message)
                self.statusBar().showMessage("BASIC-Kompilierung fehlgeschlagen")
                return False
            return self._finish_compile_stage(
                document, generated, assembly_path, "C64 BASIC"
            )

        def _compile_pascal_document(self, document: DocumentEditor) -> bool:
            """ANTLR-Pascal -> zielabhängiger ASM-Code; kein Binärprogramm."""
            source = document.raw_editor.toPlainText()
            try:
                from c64pascal import C64PascalError, compile_pascal_to_assembly
            except ImportError as exc:
                message = (
                    "Der ANTLR-basierte Pascal-Compiler konnte nicht geladen "
                    "werden. Stelle sicher, dass der Ordner 'c64pascal' neben "
                    "d64_dism.py liegt und installiere:\n\n"
                    "py -m pip install antlr4-python3-runtime==4.13.2\n\n"
                    f"Technischer Fehler: {exc}"
                )
                document.show_assembly_error(
                    message,
                    status_text="Compiler nicht verfügbar",
                )
                self.show_error("Pascal-Compiler nicht verfügbar", message)
                return False

            try:
                compiler_parameters = inspect.signature(
                    compile_pascal_to_assembly
                ).parameters.values()
                compiler_supports_target = any(
                    parameter.name == "target"
                    or parameter.kind is inspect.Parameter.VAR_KEYWORD
                    for parameter in compiler_parameters
                )
            except (TypeError, ValueError):
                compiler_supports_target = False

            if not compiler_supports_target:
                compiler_file = inspect.getsourcefile(
                    compile_pascal_to_assembly
                ) or getattr(
                    sys.modules.get(compile_pascal_to_assembly.__module__),
                    "__file__",
                    "<unbekannt>",
                )
                message = (
                    "Die geladene Pascal-Compiler-Version ist zu alt für "
                    "die Zielauswahl C-64/Amiga/Windows PE32. Ihre Funktion "
                    "compile_pascal_to_assembly() besitzt keinen Parameter "
                    "'target'.\n\nGeladenes Modul:\n"
                    f"{compiler_file}"
                )
                document.show_assembly_error(
                    message,
                    status_text="Pascal-Compiler ist veraltet",
                )
                self.show_error("Pascal-Compiler ist veraltet", message)
                return False

            try:
                assembly_path = self._pascal_assembly_output_path(document)
                include_paths = [
                    document.path.parent,
                    ".",
                    "./include",
                    self.current_directory,
                ]
                if self.workspace_root not in include_paths:
                    include_paths.append(self.workspace_root)
                compiler_kwargs = {
                    "filename": str(document.path),
                    "include_paths": include_paths,
                    "target": document.build_target,
                }
                try:
                    parameter_map = inspect.signature(
                        compile_pascal_to_assembly
                    ).parameters
                except (TypeError, ValueError):
                    parameter_map = {}
                if document.build_target == "amiga":
                    if "cpu_model" in parameter_map:
                        compiler_kwargs["cpu_model"] = document.amiga_cpu_model
                    if "fpu_model" in parameter_map:
                        compiler_kwargs["fpu_model"] = document.amiga_fpu_model
                if document.build_target == "pe32":
                    if "graphics_backend" in parameter_map:
                        compiler_kwargs["graphics_backend"] = (
                            document.windows_graphics_backend
                        )
                    if "windows_application_mode" in parameter_map:
                        compiler_kwargs["windows_application_mode"] = (
                            document.windows_application_mode
                        )
                    if "predefined_macros" in parameter_map:
                        compiler_kwargs["predefined_macros"] = (
                            windows_application_predefined_macros(
                                document.windows_application_mode
                            )
                        )
                    if (
                        "breakpoint_lines" in parameter_map
                        and normalize_windows_application_mode(
                            document.windows_application_mode
                        ) == "Console"
                    ):
                        compiler_kwargs["breakpoint_lines"] = (
                            document.raw_editor.breakpoint_lines()
                        )
                generated = compile_pascal_to_assembly(
                    source, **compiler_kwargs
                )
            except C64PascalError as exc:
                message = str(exc)
                document.show_assembly_error(
                    message,
                    exc.line or 0,
                    "Compilerfehler",
                )
                self.show_error("Pascal-Compilerfehler", message)
                self.statusBar().showMessage("Pascal-Kompilierung fehlgeschlagen")
                return False

            return self._finish_compile_stage(
                document,
                generated,
                assembly_path,
                "Pascal",
                is_unit=(
                    getattr(generated, "source_kind", "program") == "unit"
                ),
            )

        def _compile_c_document(self, document: DocumentEditor) -> bool:
            """ANTLR-C -> zielabhängiger ASM-Code; kein Binärprogramm."""
            source = document.raw_editor.toPlainText()
            try:
                from c64c import C64CError, compile_c_to_assembly
            except ImportError as exc:
                message = (
                    "Der ANTLR-basierte C-Compiler konnte nicht geladen "
                    "werden. Stelle sicher, dass die Ordner 'c64c' und "
                    "'c64pascal' neben d64_dism.py liegen und installiere:\n\n"
                    "py -m pip install antlr4-python3-runtime==4.13.2\n\n"
                    f"Technischer Fehler: {exc}"
                )
                document.show_assembly_error(
                    message,
                    status_text="Compiler nicht verfügbar",
                )
                self.show_error("C-Compiler nicht verfügbar", message)
                return False

            try:
                assembly_path = self._c_assembly_output_path(document)
                include_paths = [
                    document.path.parent,
                    ".",
                    "./include",
                    self.current_directory,
                ]
                if self.workspace_root not in include_paths:
                    include_paths.append(self.workspace_root)
                compiler_kwargs = {
                    "filename": str(document.path),
                    "include_paths": include_paths,
                    "target": document.build_target,
                }
                try:
                    parameter_map = inspect.signature(
                        compile_c_to_assembly
                    ).parameters
                except (TypeError, ValueError):
                    parameter_map = {}
                if document.build_target == "amiga":
                    if "cpu_model" in parameter_map:
                        compiler_kwargs["cpu_model"] = document.amiga_cpu_model
                    if "fpu_model" in parameter_map:
                        compiler_kwargs["fpu_model"] = document.amiga_fpu_model
                if document.build_target == "pe32":
                    if "graphics_backend" in parameter_map:
                        compiler_kwargs["graphics_backend"] = (
                            document.windows_graphics_backend
                        )
                    if "windows_application_mode" in parameter_map:
                        compiler_kwargs["windows_application_mode"] = (
                            document.windows_application_mode
                        )
                    if "predefined_macros" in parameter_map:
                        compiler_kwargs["predefined_macros"] = (
                            windows_application_predefined_macros(
                                document.windows_application_mode
                            )
                        )
                generated = compile_c_to_assembly(source, **compiler_kwargs)
            except C64CError as exc:
                message = str(exc)
                error_line = 0
                if exc.line and exc.filename:
                    try:
                        if Path(exc.filename).resolve() == document.path.resolve():
                            error_line = exc.line
                    except (OSError, RuntimeError):
                        pass
                document.show_assembly_error(
                    message,
                    error_line,
                    "Compilerfehler",
                )
                self.show_error("C-Compilerfehler", message)
                self.statusBar().showMessage("C-Kompilierung fehlgeschlagen")
                return False

            return self._finish_compile_stage(
                document,
                generated,
                assembly_path,
                "C",
            )

        def create_coff32_object_document(
            self,
            document: DocumentEditor,
        ) -> bool:
            """Erzeugt Hauptmodul und PE32-Abhaengigkeiten als COFF32-.o."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)
            if document.build_target != "pe32":
                self.show_error(
                    "COFF32 nur für Windows PE32",
                    "Wähle zuerst das Ziel 'Windows PE32'.",
                )
                return False
            source = document.generated_assembly_editor.toPlainText()
            if not source.strip():
                self.show_error(
                    "Keine PE32-Assemblerdaten",
                    "Kompiliere zuerst die Pascal- oder C-Quelle.",
                )
                return False
            if document.path is None:
                if not self._save_document(document, save_as=True):
                    return False

            assembly_path = (
                document.generated_assembly_path
                if document.generated_assembly_path is not None
                else document.path.with_suffix(".generated.pe32.asm")
            )
            proxy = argparse.Namespace(
                assembly=source,
                linked_pe32_modules=getattr(
                    document, "generated_pe32_modules", ()
                ),
                linked_assembly_files=getattr(
                    document, "generated_linked_assembly_files", ()
                ),
            )
            try:
                object_paths = _write_pe32_generated_objects(
                    proxy,
                    source_path=document.path,
                    assembly_path=assembly_path,
                    main_object_path=document.path.with_suffix(".o"),
                )
            except (OSError, PE32AssemblerError) as exc:
                message = str(exc)
                document.show_generated_assembly_error(
                    message, getattr(exc, "line", 0) or 0, "COFF32-Fehler"
                )
                self.show_error(
                    "COFF32-Objekt konnte nicht erzeugt werden", message
                )
                return False

            details = []
            total_size = 0
            for path in object_paths:
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                total_size += size
                details.append(f"  {path.name} ({size} Bytes)")
            document.hints_editor.setPlainText(
                "COFF32-Objekt(e) erfolgreich erzeugt\n\n"
                f"Quelle : {document.display_name}\n"
                "Objekte:\n"
                + "\n".join(details)
                + f"\nGesamt : {total_size} Bytes\n"
                "Format : Microsoft COFF i386 / relocierbar\n"
            )
            document.generated_assembly_status_label.setText(
                f"COFF32 erzeugt: {len(object_paths)} Objekt(e)"
            )
            self.log(
                f"COFF32 OBJECTS: {document.display_name} -> "
                + ", ".join(path.name for path in object_paths)
            )
            self.statusBar().showMessage(
                f"COFF32 erzeugt: {len(object_paths)} Objekt(e)"
            )
            if any(
                path.parent.resolve() == self.current_directory
                for path in object_paths
            ):
                self.populate_file_list()
            return True

        def assemble_generated_document(
            self,
            document: DocumentEditor,
        ) -> bool:
            """Übersetzt den editierbaren ASM-Tab für das gewählte Ziel."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)
            if not (
                document.is_basic_document
                or document.is_pascal_document
                or document.is_c_document
            ):
                return False

            assembly_source = (
                document.generated_assembly_editor.toPlainText()
            )
            if not assembly_source.strip():
                message = (
                    "Es sind noch keine ASM-Daten vorhanden. Kompiliere "
                    "zuerst den BASIC-, C- oder Pascal-Quelltext."
                )
                document.show_generated_assembly_error(
                    message,
                    status_text="Keine ASM-Daten",
                )
                self.show_error("Keine ASM-Daten", message)
                return False

            try:
                #from amiga500 import (
                #    AmigaAssemblerError,
                #    assemble_amiga_boot_source,
                #    assemble_amiga_source,
                #    is_amiga_boot_source,
                #)
                amiga_bootable = (
                    document.build_target == "amiga"
                    and is_amiga_boot_source(assembly_source)
                )
                output_path = self._assembler_output_path(
                    document,
                    assembly_source,
                )
                assembly_path = document.generated_assembly_path
                if assembly_path is None:
                    if document.is_basic_document:
                        assembly_path = self._basic_assembly_output_path(document)
                    elif document.is_pascal_document:
                        assembly_path = self._pascal_assembly_output_path(document)
                    else:
                        assembly_path = self._c_assembly_output_path(document)
                if document.build_target == "amiga":
                    assembler = (
                        assemble_amiga_boot_source
                        if amiga_bootable
                        else assemble_amiga_source
                    )
                    program = assembler(
                        assembly_source,
                        filename=assembly_path.name,
                        cpu_model=document.amiga_cpu_model,
                        fpu_model=document.amiga_fpu_model,
                    )
                elif document.build_target == "pe32":
                    proxy = argparse.Namespace(
                        assembly=assembly_source,
                        linked_pe32_modules=getattr(
                            document, "generated_pe32_modules", ()
                        ),
                        linked_assembly_files=getattr(
                            document, "generated_linked_assembly_files", ()
                        ),
                    )
                    object_paths = _write_pe32_generated_objects(
                        proxy,
                        source_path=document.path,
                        assembly_path=assembly_path,
                    )
                    is_library = (
                        getattr(document, "generated_source_kind", "program")
                        == "library"
                    )
                    program = link_coff32_inputs(
                        object_paths,
                        entry_symbol=(
                            "__d64_dll_entry" if is_library else "_start"
                        ),
                        gui=True,
                        dll=is_library,
                        dll_name=(
                            document.path.with_suffix(".dll").name
                            if is_library else None
                        ),
                    )
                else:
                    program = assemble_mos6510_source(
                        assembly_source,
                        filename=assembly_path.name,
                    )
            except (AssemblerError, AmigaAssemblerError, PE32AssemblerError) as exc:
                message = str(exc)
                document.show_generated_assembly_error(
                    message,
                    exc.line or 0,
                )
                self.show_error("Assemblerfehler", message)
                self.statusBar().showMessage("Assemblieren fehlgeschlagen")
                return False

            open_assembly = self._find_open_document(assembly_path)
            if open_assembly is not None and open_assembly.is_modified:
                message = (
                    "Die erzeugte ASM-Datei ist zusätzlich geöffnet und "
                    "enthält ungespeicherte Änderungen:\n"
                    f"{assembly_path}\n\n"
                    "Speichere oder schließe diese Registerkarte vor dem "
                    "Assemblieren des ASM-Tabs."
                )
                document.show_generated_assembly_error(
                    message,
                    status_text="ASM-Datei ist geöffnet",
                )
                self.show_error("ASM-Ausgabe kann nicht ersetzt werden", message)
                return False

            try:
                self._write_assembled_program(
                    assembly_path,
                    assembly_source.encode("utf-8"),
                )
                program_data = (
                    program.adf
                    if amiga_bootable
                    else program.executable
                    if document.build_target in {"amiga", "pe32"}
                    else program.prg
                )
                self._write_assembled_program(output_path, program_data)
            except OSError as exc:
                message = (
                    "Die Assembler-Ausgabe konnte nicht gespeichert werden:\n"
                    f"ASM: {assembly_path}\n"
                    f"Programm: {output_path}\n\n{exc}"
                )
                document.show_generated_assembly_error(
                    message,
                    status_text="Ausgabefehler",
                )
                self.show_error(
                    "Assembler-Ausgabe konnte nicht gespeichert werden",
                    message,
                )
                return False

            if open_assembly is not None:
                open_assembly.raw_editor.setPlainText(assembly_source)
                open_assembly.mark_saved()
                open_assembly.invalidate_assembly_result("Neu erzeugt")
                self._update_document_tab(open_assembly)

            document.generated_assembly_path = Path(assembly_path).resolve()
            document.generated_assembly_editor.document().setModified(False)
            source_digest = hashlib.sha256(
                document.raw_editor.toPlainText().encode("utf-8")
            ).hexdigest()
            assembly_digest = hashlib.sha256(
                assembly_source.encode("utf-8")
            ).hexdigest()
            document.set_assembly_result(
                program,
                output_path,
                source_digest,
                assembly_digest,
                "assembly",
            )
            if document.build_target == "amiga":
                if amiga_bootable:
                    document.hints_editor.setPlainText(
                        "Amiga-Standalone-Assembler aus dem ASM-Tab beendet\n"
                        "\n"
                        f"Quelle        : {assembly_path}\n"
                        f"Boot-ADF      : {output_path}\n"
                        f"Boot-Einsprung: +${program.entry_offset:08X}\n"
                        f"Code-Größe    : {len(program.code)} Bytes\n"
                        f"ADF-Größe     : {len(program.adf)} Bytes\n"
                        f"Instruktionen : {program.instruction_count}\n"
                        "Workbench-Libs : keine\n"
                    )
                    self.log(
                        "ASSEMBLE AMIGA BOOT ASM-TAB: "
                        f"{assembly_path.name} -> {output_path.name}, "
                        f"{len(program.adf)} Bytes"
                    )
                else:
                    document.hints_editor.setPlainText(
                        "Amiga-Assembler aus dem ASM-Tab erfolgreich beendet\n"
                        "\n"
                        f"Quelle        : {assembly_path}\n"
                        f"Hunk-Ausgabe  : {output_path}\n"
                        f"Einsprung     : +${program.entry_offset:08X}\n"
                        f"Code-Größe    : {len(program.code)} Bytes\n"
                        f"Hunk-Größe    : {len(program.executable)} Bytes\n"
                        f"Instruktionen : {program.instruction_count}\n"
                    )
                    self.log(
                        "ASSEMBLE AMIGA ASM-TAB: "
                        f"{assembly_path.name} -> {output_path.name}, "
                        f"{len(program.executable)} Bytes"
                    )
            elif document.build_target == "pe32":
                document.hints_editor.setPlainText(
                    "Windows-PE32-Assembler aus dem ASM-Tab erfolgreich beendet\n"
                    "\n"
                    f"Quelle       : {assembly_path}\n"
                    f"PE32-Ausgabe : {output_path}\n"
                    f"Einsprung    : +${program.entry_offset:08X}\n"
                    f"Code-Größe   : {len(program.code)} Bytes\n"
                    f"EXE-Größe    : {len(program.executable)} Bytes\n"
                    f"Windows-Modus: {document.windows_application_mode}\n"
                )
                self.log(
                    "ASSEMBLE PE32 ASM-TAB: "
                    f"{assembly_path.name} -> {output_path.name}, "
                    f"{len(program.executable)} Bytes"
                )
            else:
                document.hints_editor.setPlainText(
                    "C64-Assembler aus dem ASM-Tab erfolgreich beendet\n"
                    "\n"
                    f"Quelle       : {assembly_path}\n"
                    f"Ausgabe      : {output_path}\n"
                    f"Ladeadresse  : ${program.load_address:04X}\n"
                    f"Einsprung    : ${program.entry_address:04X}\n"
                    f"Letztes Byte : ${program.end_address:04X}\n"
                    f"PRG-Größe    : {len(program.prg)} Bytes\n"
                    f"Instruktionen: {program.instruction_count}\n"
                    f"BASIC-Stub   : {'ja' if program.has_basic_stub else 'nein'}\n"
                )
                self.log(
                    "ASSEMBLE C64 ASM-TAB: "
                    f"{assembly_path.name} -> {output_path.name}, "
                    f"${program.load_address:04X}-${program.end_address:04X}, "
                    f"Start ${program.entry_address:04X}"
                )
            self.statusBar().showMessage(
                f"ASM-Tab erfolgreich assembliert: {output_path.name}"
            )
            if output_path.parent == self.current_directory:
                self.populate_file_list()
            return True

        def assemble_document(self, document: DocumentEditor) -> bool:
            """Compile für BASIC/C/Pascal oder Assemble für ASM-Quelltext."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)
            if document.is_build_document and document.path is None:
                # Neue Dokumente aus Datei -> Neu erhalten vor dem ersten
                # Build denselben Save-As-Ablauf wie geöffnete Dateien.
                if not self._save_document(document, save_as=True):
                    return False
            if document.is_basic_document:
                return self._compile_basic_document(document)
            if document.is_pascal_document:
                return self._compile_pascal_document(document)
            if document.is_c_document:
                return self._compile_c_document(document)
            if not document.is_assembler_document:
                self.show_error(
                    "Kein übersetzbares Dokument",
                    "Compile/Assemble steht für .bas, .basic, .c, .pas, "
                    ".pp, .asm, .s, .a65 und .inc zur Verfügung.",
                )
                return False

            source = document.raw_editor.toPlainText()
            source_digest = hashlib.sha256(
                source.encode("utf-8")
            ).hexdigest()
            try:
                #from amiga500 import (
                #    AmigaAssemblerError,
                #    assemble_amiga_boot_source,
                #    assemble_amiga_source,
                #    is_amiga_boot_source,
                #)
                amiga_bootable = (
                    document.build_target == "amiga"
                    and is_amiga_boot_source(source)
                )
                output_path = self._assembler_output_path(document, source)
                if document.build_target == "amiga":
                    assembler = (
                        assemble_amiga_boot_source
                        if amiga_bootable
                        else assemble_amiga_source
                    )
                    program = assembler(
                        source,
                        filename=document.display_name,
                        cpu_model=document.amiga_cpu_model,
                        fpu_model=document.amiga_fpu_model,
                    )
                    program_data = (
                        program.adf
                        if amiga_bootable
                        else program.executable
                    )
                elif document.build_target == "pe32":
                    program = assemble_pe32_source(
                        source,
                        filename=document.display_name,
                        gui=True,
                    )
                    program_data = program.executable
                else:
                    program = assemble_mos6510_source(
                        source,
                        filename=document.display_name,
                    )
                    program_data = program.prg
                self._write_assembled_program(output_path, program_data)
            except (AssemblerError, AmigaAssemblerError, PE32AssemblerError) as exc:
                message = str(exc)
                document.show_assembly_error(message, exc.line or 0)
                self.show_error("Assemblerfehler", message)
                self.statusBar().showMessage("Assemblieren fehlgeschlagen")
                return False
            except OSError as exc:
                message = (
                    "Das Zielprogramm konnte nicht gespeichert werden:\n"
                    f"{output_path}\n\n{exc}"
                )
                document.show_assembly_error(message)
                self.show_error("PRG konnte nicht gespeichert werden", message)
                self.statusBar().showMessage("Assemblieren fehlgeschlagen")
                return False

            document.set_assembly_result(
                program,
                output_path,
                source_digest,
            )
            if document.build_target == "amiga":
                if amiga_bootable:
                    document.hints_editor.setPlainText(
                        "Amiga-Standalone-Assembler erfolgreich beendet\n"
                        "\n"
                        f"Quelle        : {document.display_name}\n"
                        f"Boot-ADF      : {output_path}\n"
                        f"Boot-Einsprung: +${program.entry_offset:08X}\n"
                        f"Code-Größe    : {len(program.code)} Bytes\n"
                        f"ADF-Größe     : {len(program.adf)} Bytes\n"
                        f"Instruktionen : {program.instruction_count}\n"
                        "Workbench-Libs : keine\n"
                    )
                    self.log(
                        "ASSEMBLE AMIGA BOOT: "
                        f"{document.display_name} -> {output_path.name}, "
                        f"{len(program.adf)} Bytes"
                    )
                else:
                    document.hints_editor.setPlainText(
                        "Amiga-Assembler erfolgreich beendet\n"
                        "\n"
                        f"Quelle        : {document.display_name}\n"
                        f"Hunk-Ausgabe  : {output_path}\n"
                        f"Einsprung     : +${program.entry_offset:08X}\n"
                        f"Code-Größe    : {len(program.code)} Bytes\n"
                        f"Hunk-Größe    : {len(program.executable)} Bytes\n"
                        f"Instruktionen : {program.instruction_count}\n"
                    )
                    self.log(
                        "ASSEMBLE AMIGA: "
                        f"{document.display_name} -> {output_path.name}, "
                        f"{len(program.executable)} Bytes"
                    )
            elif document.build_target == "pe32":
                document.hints_editor.setPlainText(
                    "Windows-PE32-Assembler erfolgreich beendet\n"
                    "\n"
                    f"Quelle       : {document.display_name}\n"
                    f"PE32-Ausgabe : {output_path}\n"
                    f"Einsprung    : +${program.entry_offset:08X}\n"
                    f"Code-Größe   : {len(program.code)} Bytes\n"
                    f"EXE-Größe    : {len(program.executable)} Bytes\n"
                    f"Windows-Modus: {document.windows_application_mode}\n"
                )
                self.log(
                    "ASSEMBLE PE32: "
                    f"{document.display_name} -> {output_path.name}, "
                    f"{len(program.executable)} Bytes"
                )
            else:
                document.hints_editor.setPlainText(
                    "C64-Assembler erfolgreich beendet\n"
                    "\n"
                    f"Quelle       : {document.display_name}\n"
                    f"Ausgabe      : {output_path}\n"
                    f"Ladeadresse  : ${program.load_address:04X}\n"
                    f"Einsprung    : ${program.entry_address:04X}\n"
                    f"Letztes Byte : ${program.end_address:04X}\n"
                    f"PRG-Größe    : {len(program.prg)} Bytes\n"
                    f"Instruktionen: {program.instruction_count}\n"
                    f"BASIC-Stub   : {'ja' if program.has_basic_stub else 'nein'}\n"
                )
                self.log(
                    "ASSEMBLE C64: "
                    f"{document.display_name} -> {output_path.name}, "
                    f"${program.load_address:04X}-${program.end_address:04X}, "
                    f"Start ${program.entry_address:04X}"
                )
            self.statusBar().showMessage(
                f"Assemblieren erfolgreich: {output_path.name}"
            )
            if output_path.parent == self.current_directory:
                self.populate_file_list()
            return True

        def _resolve_vice_for_program_start(self) -> Optional[Path]:
            if self.dism_vice_path:
                configured = Path(self.dism_vice_path).expanduser()
                if configured.is_file():
                    return configured.resolve()
                self.show_error(
                    "VICE nicht gefunden",
                    "Das gespeicherte VICE-Programm existiert nicht mehr:\n"
                    f"{configured}\n\nBitte wähle VICE erneut aus.",
                )
                self.dism_vice_path = ""

            executable = (
                shutil.which("x64sc.exe")
                or shutil.which("x64sc")
                or shutil.which("x64.exe")
                or shutil.which("x64")
            )
            if executable:
                return Path(executable).resolve()

            self.choose_dism_vice()
            if self.dism_vice_path:
                selected = Path(self.dism_vice_path)
                if selected.is_file():
                    return selected.resolve()
            self.statusBar().showMessage("VICE-Start abgebrochen")
            return None

        def _resolve_winuae_for_program_start(self) -> Optional[Path]:
            if self.winuae_path:
                configured = Path(self.winuae_path).expanduser()
                if configured.is_file():
                    return configured.resolve()
                self.show_error(
                    "WinUAE nicht gefunden",
                    "Das gespeicherte WinUAE-Programm existiert nicht mehr:\n"
                    f"{configured}\n\nBitte wähle WinUAE erneut aus.",
                )
                self.winuae_path = ""

            executable = (
                shutil.which("winuae64.exe")
                or shutil.which("winuae.exe")
                or shutil.which("winuae64")
                or shutil.which("winuae")
            )
            if executable:
                return Path(executable).resolve()

            self.choose_winuae()
            if self.winuae_path:
                selected = Path(self.winuae_path)
                if selected.is_file():
                    return selected.resolve()
            self.statusBar().showMessage("WinUAE-Start abgebrochen")
            return None

        def start_assembled_document(self, document: DocumentEditor) -> bool:
            """Lädt den letzten Build per VICE-Autostart und führt ihn aus."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)

            current_digest = hashlib.sha256(
                document.raw_editor.toPlainText().encode("utf-8")
            ).hexdigest()
            output_path = document.assembled_program_path
            if (
                output_path is None
                or document.assembled_target != document.build_target
                or document.assembled_input_kind != "source"
                or document.assembled_source_digest != current_digest
                or not output_path.is_file()
            ):
                if not self.assemble_document(document):
                    return False
            return self._launch_assembled_document(document)

        def start_generated_assembly_document(
            self,
            document: DocumentEditor,
        ) -> bool:
            """Startet den aktuellen Build des editierbaren ASM-Tabs."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)
            current_digest = document.generated_assembly_digest()
            output_path = document.assembled_program_path
            if (
                output_path is None
                or document.assembled_target != document.build_target
                or document.assembled_assembly_digest != current_digest
                or not output_path.is_file()
            ):
                if not self.assemble_generated_document(document):
                    return False
            return self._launch_assembled_document(document)

        def _launch_assembled_document(
            self,
            document: DocumentEditor,
        ) -> bool:
            output_path = document.assembled_program_path
            if output_path is None:
                return False
            if document.build_target == "amiga":
                return self._launch_amiga_document(document, output_path)
            if document.build_target == "pe32":
                if os.name != "nt":
                    self.show_error(
                        "Windows-PE32-Start",
                        "PE32-Programme können aus d64_dism nur unter Windows "
                        "direkt gestartet werden. Die erzeugte EXE bleibt erhalten:\n"
                        f"{output_path}",
                    )
                    return False
                # Konsolenprogramme duerfen ihre Standard-Handles nicht auf
                # DEVNULL umgeleitet bekommen. Der PE32-Code oeffnet seine
                # Konsole mit AllocConsole und verwendet CONIN$/CONOUT$ fuer
                # ReadLn/WriteLn. Eine Popen-Umleitung auf DEVNULL fuehrt sonst
                # exakt dazu, dass WriteFile unsichtbar schreibt und ReadFile
                # sofort EOF liefert.
                console_mode = (
                    normalize_windows_application_mode(
                        document.windows_application_mode
                    ) == "Console"
                )
                options = {"cwd": str(output_path.parent)}
                if not console_mode:
                    options.update({
                        "stdin": subprocess.DEVNULL,
                        "stdout": subprocess.DEVNULL,
                        "stderr": subprocess.DEVNULL,
                    })
                if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
                    options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                try:
                    process = subprocess.Popen([str(output_path)], **options)
                except OSError as exc:
                    self.show_error(
                        "PE32-Programm konnte nicht gestartet werden",
                        f"Programm: {output_path}\n\n{exc}",
                    )
                    return False
                processes = [
                    running for running in getattr(self, "_pe32_processes", [])
                    if running.poll() is None
                ]
                processes.append(process)
                self._pe32_processes = processes
                document.assembly_status_label.setText(
                    f"Unter Windows gestartet: {output_path.name}"
                )
                if document.generated_assembly_path is not None:
                    document.generated_assembly_status_label.setText(
                        f"Unter Windows gestartet: {output_path.name}"
                    )
                self.log(f"PE32 START: {output_path}")
                self.statusBar().showMessage(
                    f"Windows-PE32 gestartet: {output_path.name}"
                )
                return True
            vice_path = self._resolve_vice_for_program_start()
            if vice_path is None:
                return False

            command = [
                str(vice_path),
                "-autostartprgmode",
                "1",
                "-autostart",
                str(output_path),
            ]
            options = {
                "cwd": str(output_path.parent),
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if os.name == "nt" and hasattr(
                subprocess,
                "CREATE_NEW_PROCESS_GROUP",
            ):
                options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            try:
                process = subprocess.Popen(command, **options)
            except OSError as exc:
                self.show_error(
                    "VICE konnte nicht gestartet werden",
                    f"Programm: {vice_path}\nPRG: {output_path}\n\n{exc}",
                )
                return False

            processes = [
                running
                for running in getattr(self, "_vice_processes", [])
                if running.poll() is None
            ]
            processes.append(process)
            self._vice_processes = processes
            document.assembly_status_label.setText(
                f"In VICE gestartet: {output_path.name}"
            )
            if document.generated_assembly_path is not None:
                document.generated_assembly_status_label.setText(
                    f"In VICE gestartet: {output_path.name}"
                )
            self.log(
                "VICE START: "
                + self._display_dism_command(command)
            )
            self.statusBar().showMessage(
                f"In VICE gestartet: {output_path.name}"
            )
            return True

        def _launch_amiga_document(
            self,
            document: DocumentEditor,
            output_path: Path,
        ) -> bool:
            winuae_path = self._resolve_winuae_for_program_start()
            if winuae_path is None:
                return False

            if output_path.suffix.casefold() == ".adf":
                command = [
                    str(winuae_path),
                    "-s",
                    "quickstart=a500,1",
                    "-s",
                    f"cpu_model={document.amiga_cpu_model.replace('mk', '')}",
                    "-s",
                    f"fpu_model={document.amiga_fpu_model.split(':', 1)[1].strip() if document.amiga_fpu_model != 'FPU: None' else '0'}",
                    "-s",
                    "use_gui=no",
                    "-0",
                    str(output_path),
                ]
                options = {
                    "cwd": str(output_path.parent),
                    "stdin": subprocess.DEVNULL,
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL,
                }
                if os.name == "nt" and hasattr(
                    subprocess,
                    "CREATE_NEW_PROCESS_GROUP",
                ):
                    options["creationflags"] = (
                        subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                try:
                    process = subprocess.Popen(command, **options)
                except OSError as exc:
                    self.show_error(
                        "WinUAE konnte nicht gestartet werden",
                        f"Programm: {winuae_path}\n"
                        f"Boot-ADF: {output_path}\n\n{exc}",
                    )
                    return False

                processes = [
                    running
                    for running in getattr(self, "_winuae_processes", [])
                    if running.poll() is None
                ]
                processes.append(process)
                self._winuae_processes = processes
                document.assembly_status_label.setText(
                    f"Standalone in WinUAE gestartet: {output_path.name}"
                )
                if document.generated_assembly_path is not None:
                    document.generated_assembly_status_label.setText(
                        f"Standalone in WinUAE gestartet: {output_path.name}"
                    )
                self.log(
                    "WINUAE ADF START: "
                    + self._display_dism_command(command)
                )
                self.statusBar().showMessage(
                    f"Standalone-ADF in WinUAE gestartet: {output_path.name}"
                )
                return True

            active_directories = []
            for process, temporary in self._winuae_boot_directories:
                if process.poll() is None:
                    active_directories.append((process, temporary))
                else:
                    temporary.cleanup()
            self._winuae_boot_directories = active_directories

            temporary = tempfile.TemporaryDirectory(
                prefix="d64_dism_winuae_"
            )
            boot_root = Path(temporary.name)
            startup_directory = boot_root / "S"
            startup_directory.mkdir(parents=True, exist_ok=True)
            mounted_program = boot_root / "program"
            shutil.copy2(output_path, mounted_program)
            (startup_directory / "startup-sequence").write_text(
                "program\n",
                encoding="ascii",
                newline="\n",
            )

            command = [
                str(winuae_path),
                "-s",
                "quickstart=a500,1",
                "-s",
                f"cpu_model={document.amiga_cpu_model.replace('mk', '')}",
                "-s",
                f"fpu_model={document.amiga_fpu_model.split(':', 1)[1].strip() if document.amiga_fpu_model != 'FPU: None' else '0'}",
                "-s",
                "use_gui=no",
                "-s",
                f"filesystem2=rw,DH0:DH0:{boot_root},0",
            ]
            options = {
                "cwd": str(output_path.parent),
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if os.name == "nt" and hasattr(
                subprocess,
                "CREATE_NEW_PROCESS_GROUP",
            ):
                options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            try:
                process = subprocess.Popen(command, **options)
            except OSError as exc:
                temporary.cleanup()
                self.show_error(
                    "WinUAE konnte nicht gestartet werden",
                    f"Programm: {winuae_path}\n"
                    f"Amiga-Hunk: {output_path}\n\n{exc}",
                )
                return False

            self._winuae_boot_directories.append((process, temporary))
            document.assembly_status_label.setText(
                f"In WinUAE gestartet: {output_path.name}"
            )
            if document.generated_assembly_path is not None:
                document.generated_assembly_status_label.setText(
                    f"In WinUAE gestartet: {output_path.name}"
                )
            self.log(
                "WINUAE START: "
                + self._display_dism_command(command)
            )
            self.statusBar().showMessage(
                f"In WinUAE gestartet: {output_path.name}"
            )
            return True

        def _confirm_close_document(self, document: DocumentEditor) -> bool:
            if not document.is_modified:
                return True

            answer = self._show_message_box(
                QMessageBox.Question,
                "Änderungen speichern?",
                f"Soll die Datei '{document.display_name}' vor dem Schließen "
                "gespeichert werden?",
                buttons=(
                    QMessageBox.Save
                    | QMessageBox.Discard
                    | QMessageBox.Cancel
                ),
                default_button=QMessageBox.Save,
            )
            if answer == QMessageBox.Save:
                self.document_tabs.setCurrentWidget(document)
                return self._save_document(document, save_as=False)
            return answer == QMessageBox.Discard

        def close_current_document(self) -> bool:
            document = self.current_document()
            if document is None:
                return True
            return self.close_document(document)

        def close_document(self, document: DocumentEditor) -> bool:
            index = self._document_index(document)
            if index < 0:
                return True
            if not self._confirm_close_document(document):
                self.document_tabs.setCurrentWidget(document)
                return False

            name = document.display_name
            self.document_tabs.removeTab(index)
            document.deleteLater()
            self._refresh_favorites_menu()
            self._update_document_actions()
            self._update_editor_status_panels()
            self.log(f"Editor geschlossen: {name}")
            return True

        @staticmethod
        def _dock_features():
            return (
                QDockWidget.DockWidgetMovable
                | QDockWidget.DockWidgetFloatable
                | QDockWidget.DockWidgetClosable
            )

        def _create_left_dock(self) -> None:
            self.left_dock = QDockWidget("Dateisystem und Dateien", self)
            self.left_dock.setObjectName("filesystem_dock")
            self.left_dock.setFeatures(self._dock_features())
            self.left_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.left_dock.setMinimumWidth(320)

            container = QWidget(self.left_dock)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(6)

            path_layout = QHBoxLayout()
            self.browse_button = QPushButton(container)
            self.browse_button.setIcon(
                self.style().standardIcon(QStyle.SP_DirOpenIcon)
            )
            self.browse_button.setToolTip("Arbeitsverzeichnis auswählen")
            self.browse_button.setFixedWidth(38)
            self.browse_button.clicked.connect(self.choose_workspace_directory)

            self.path_edit = QLineEdit(container)
            self.path_edit.setClearButtonEnabled(True)
            self.path_edit.setPlaceholderText("Ordnerpfad eingeben und Enter drücken")
            self.path_edit.returnPressed.connect(self.navigate_from_path_edit)

            path_layout.addWidget(self.browse_button)
            path_layout.addWidget(self.path_edit, 1)
            layout.addLayout(path_layout)

            self.file_system_model = QFileSystemModel(self)
            self.file_system_model.setFilter(
                QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives
            )
            self.file_system_model.setReadOnly(True)

            self.directory_tree = QTreeView(container)
            self.directory_tree.setObjectName("directory_tree")
            self.directory_tree.setModel(self.file_system_model)
            self.directory_tree.setAnimated(True)
            self.directory_tree.setUniformRowHeights(True)
            self.directory_tree.setHeaderHidden(True)
            self.directory_tree.setExpandsOnDoubleClick(True)
            self.directory_tree.setMinimumHeight(120)
            for column in range(1, 4):
                self.directory_tree.hideColumn(column)
            self.directory_tree.clicked.connect(self.directory_tree_clicked)

            filter_widget = QWidget(container)
            filter_layout = QHBoxLayout(filter_widget)
            filter_layout.setContentsMargins(0, 0, 0, 0)
            filter_layout.setSpacing(4)
            # Die frühere große Filtermatrix bleibt funktional über FILTERS,
            # sichtbar sind aber nur noch die drei Plattform-Schaltflächen.
            self.filter_group = QButtonGroup(self)
            self.filter_group.setExclusive(False)
            self.filter_buttons = {}
            self.platform_filter_buttons = {}

            def add_filter_action(menu: QMenu, text: str, filter_name: str):
                action = menu.addAction(text)
                action.triggered.connect(
                    lambda _checked=False, name=filter_name: self.set_filter(name)
                )
                return action

            platform_tools = {
                "C-64": (
                    ("D64 Disketten-Images", "D64"),
                    ("PRG Programme", "PRG"),
                    ("RAM Images", "RAM"),
                    ("Character Maps", "CHR"),
                    ("Paletten", "PAL"),
                    ("Screens", "SCREEN"),
                    ("Pixel Screens", "PIXEL"),
                ),
                "Amiga": (
                    ("Amiga Programme / ADF", "AMIGA"),
                    ("RAM Images", "RAM"),
                ),
                "Windows": (
                    ("PE32 Programme", "PE32"),
                    ("COFF32 Objekte / Archive", "OBJ"),
                ),
            }

            for platform_name in ("C-64", "Amiga", "Windows"):
                button = QPushButton(platform_name, filter_widget)
                button.setObjectName(
                    "platform_filter_"
                    + platform_name.casefold().replace("-", "").replace(" ", "_")
                )
                button.setMinimumWidth(78)
                button.setMaximumHeight(26)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

                menu = QMenu(button)
                source_menu = menu.addMenu("Quellcode")
                add_filter_action(source_menu, "BASIC", "BASIC")
                add_filter_action(source_menu, "Pascal", "PAS")
                add_filter_action(source_menu, "C", "C")
                add_filter_action(source_menu, "Assembler", "ASM")

                tools_menu = menu.addMenu("Tools")
                for tool_text, filter_name in platform_tools[platform_name]:
                    add_filter_action(tools_menu, tool_text, filter_name)

                menu.addSeparator()
                add_filter_action(menu, "Alle", "ALLE")
                button.setMenu(menu)
                button.setToolTip(
                    f"{platform_name}-Dateifilter auswählen; 'Alle' löscht den Filter"
                )
                self.platform_filter_buttons[platform_name] = button
                filter_layout.addWidget(button, 1)

            self.file_list = QListWidget(container)
            self.file_list.setObjectName("file_icon_list")
            self.file_list.setViewMode(QListWidget.IconMode)
            self.file_list.setResizeMode(QListWidget.Adjust)
            self.file_list.setMovement(QListWidget.Static)
            self.file_list.setIconSize(QSize(44, 44))
            self.file_list.setGridSize(QSize(116, 84))
            self.file_list.setWordWrap(True)
            self.file_list.setSpacing(3)
            self.file_list.itemClicked.connect(self.file_item_clicked)
            self.file_list.itemDoubleClicked.connect(self.file_item_double_clicked)

            splitter = QSplitter(Qt.Vertical, container)
            splitter.setChildrenCollapsible(False)
            splitter.addWidget(self.directory_tree)

            lower_widget = QWidget(splitter)
            lower_layout = QVBoxLayout(lower_widget)
            lower_layout.setContentsMargins(0, 0, 0, 0)
            lower_layout.setSpacing(5)
            lower_layout.addWidget(filter_widget)
            lower_layout.addWidget(self.file_list, 1)
            splitter.addWidget(lower_widget)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 2)

            layout.addWidget(splitter, 1)
            self.left_dock.setWidget(container)
            self.left_dock.setTitleBarWidget(DockTitleBar(self.left_dock))
            self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
            self.view_menu.addAction(self.left_dock.toggleViewAction())

        def _create_project_tab(self, parent: QWidget) -> QWidget:
            tab = QWidget(parent)
            tab.setObjectName("project_panel_tab")
            layout = QVBoxLayout(tab)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(6)

            path_layout = QHBoxLayout()
            path_layout.setContentsMargins(0, 0, 0, 0)
            self.project_open_button = QToolButton(tab)
            self.project_open_button.setObjectName("project_open_button")
            self.project_open_button.setIcon(
                self.style().standardIcon(QStyle.SP_DialogOpenButton)
            )
            self.project_open_button.setToolTip("Projektdatei (*.pro) öffnen")
            self.project_open_button.setFixedWidth(34)
            self.project_path_edit = QLineEdit(tab)
            self.project_path_edit.setObjectName("project_path_edit")
            self.project_path_edit.setPlaceholderText("Pfad zur Projektdatei (*.pro)")
            self.project_path_edit.setClearButtonEnabled(True)
            path_layout.addWidget(self.project_open_button)
            path_layout.addWidget(self.project_path_edit, 1)
            layout.addLayout(path_layout)

            self.project_tree = QTreeWidget(tab)
            self.project_tree.setObjectName("project_tree")
            self.project_tree.setHeaderHidden(True)
            self.project_tree.setUniformRowHeights(True)
            self.project_tree.setAlternatingRowColors(True)
            self.project_tree.setContextMenuPolicy(Qt.CustomContextMenu)
            self.project_tree.setToolTip(
                "Ein Klick öffnet den ausgewählten Dateieintrag"
            )
            layout.addWidget(self.project_tree, 1)

            button_layout = QHBoxLayout()
            self.project_new_button = QPushButton("Neu", tab)
            self.project_save_button = QPushButton("Speichern", tab)
            self.project_save_as_button = QPushButton("Speichern unter...", tab)
            button_layout.addWidget(self.project_new_button)
            button_layout.addWidget(self.project_save_button)
            button_layout.addWidget(self.project_save_as_button)
            layout.addLayout(button_layout)

            self.project_open_button.clicked.connect(self.choose_project_file)
            self.project_path_edit.returnPressed.connect(
                self.load_project_from_path_edit
            )
            self.project_new_button.clicked.connect(self.new_project)
            self.project_save_button.clicked.connect(self.save_project)
            self.project_save_as_button.clicked.connect(self.save_project_as)
            self.project_tree.customContextMenuRequested.connect(
                self.show_project_context_menu
            )
            self.project_tree.itemClicked.connect(self.open_project_item)

            self.reset_project_tree()
            return tab

        def reset_project_tree(
            self,
            entries: Optional[Dict[str, List[Dict[str, str]]]] = None,
        ) -> None:
            if not hasattr(self, "project_tree"):
                return
            values = entries or empty_project_entries()
            self.project_tree.blockSignals(True)
            self.project_tree.clear()
            self.project_root_items = {}
            folder_icon = self.style().standardIcon(QStyle.SP_DirClosedIcon)
            for key, title, _extensions in PROJECT_CATEGORIES:
                root = QTreeWidgetItem(self.project_tree, [title])
                root.setData(0, Qt.UserRole + 301, key)
                root.setIcon(0, folder_icon)
                root.setToolTip(0, "Geschützte Projektkategorie")
                self.project_root_items[key] = root
                for entry in values.get(key, ()):
                    self._add_project_entry(
                        key,
                        Path(str(entry.get("path", ""))),
                        title=str(entry.get("title", "")),
                        mark_modified=False,
                    )
                root.setExpanded(True)
            self.project_tree.blockSignals(False)

        def _add_project_entry(
            self,
            category_key: str,
            path: Path,
            *,
            title: str = "",
            mark_modified: bool = True,
        ) -> Optional[QTreeWidgetItem]:
            root = self.project_root_items.get(category_key)
            if root is None:
                return None
            try:
                resolved = Path(path).expanduser().resolve()
            except OSError:
                resolved = Path(path).expanduser()
            path_text = str(resolved)
            for index in range(root.childCount()):
                child = root.child(index)
                if str(child.data(0, Qt.UserRole + 302) or "").casefold() == path_text.casefold():
                    self.project_tree.setCurrentItem(child)
                    return child
            display_title = title.strip() or resolved.name or path_text
            child = QTreeWidgetItem(root, [display_title])
            child.setData(0, Qt.UserRole + 301, category_key)
            child.setData(0, Qt.UserRole + 302, path_text)
            child.setToolTip(0, path_text)
            child.setIcon(0, self.icon_provider.icon(QFileInfo(path_text)))
            root.setExpanded(True)
            if mark_modified:
                self.set_project_modified(True)
            return child

        def collect_project_entries(self) -> Dict[str, List[Dict[str, str]]]:
            entries = empty_project_entries()
            for key, _title, _extensions in PROJECT_CATEGORIES:
                root = self.project_root_items.get(key)
                if root is None:
                    continue
                for index in range(root.childCount()):
                    child = root.child(index)
                    path_value = str(child.data(0, Qt.UserRole + 302) or "")
                    if path_value:
                        entries[key].append(
                            {
                                "title": child.text(0),
                                "path": path_value,
                            }
                        )
            return entries

        def project_has_entries(self) -> bool:
            return any(
                root.childCount() > 0
                for root in self.project_root_items.values()
            )

        def set_project_modified(self, modified: bool) -> None:
            self.project_modified = bool(modified)
            if hasattr(self, "right_panel_tabs") and hasattr(self, "project_tab"):
                index = self.right_panel_tabs.indexOf(self.project_tab)
                if index >= 0:
                    self.right_panel_tabs.setTabText(
                        index,
                        "Projekt *" if self.project_modified else "Projekt",
                    )

        def choose_project_file(self) -> None:
            start_directory = (
                self.current_project_path.parent
                if self.current_project_path is not None
                else self.current_directory
            )
            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "Projekt öffnen",
                str(start_directory),
                "dBase2Many-Projekte (*.pro);;Alle Dateien (*)",
            )
            if filename:
                self.load_project_file(Path(filename))

        def load_project_from_path_edit(self) -> None:
            value = self.project_path_edit.text().strip()
            if value:
                self.load_project_file(Path(value))

        def _confirm_project_replacement(self, title: str) -> bool:
            if not self.project_modified and not self.project_has_entries():
                return True
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setIcon(QMessageBox.Question)
            box.setText(
                "Sollen die gesammelten Projekt-Informationen vor dem "
                "Zurücksetzen gespeichert werden?"
            )
            save_button = box.addButton("Ja, speichern", QMessageBox.AcceptRole)
            discard_button = box.addButton(
                "Nein, nicht speichern", QMessageBox.DestructiveRole
            )
            cancel_button = box.addButton("Abbrechen", QMessageBox.RejectRole)
            box.setDefaultButton(save_button)
            box.exec_()
            clicked = box.clickedButton()
            if clicked is cancel_button:
                return False
            if clicked is save_button:
                return bool(self.save_project())
            return clicked is discard_button

        def _save_project_before_new(self) -> bool:
            """Sichert ein vorhandenes Projekt, bevor der Baum geleert wird."""
            if self.current_project_path is not None:
                return bool(self.save_project())
            if self.project_modified or self.project_has_entries():
                return bool(self.save_project_as())
            return True

        def new_project(self) -> None:
            # Ein geöffnetes/gefülltes Projekt wird vor dem Neuanlegen immer
            # gesichert. Bei einem noch namenlosen Projekt fragt save_project_as
            # einmalig nach der gewünschten *.pro-Datei.
            if not self._save_project_before_new():
                return
            self.current_project_path = None
            self.project_path_edit.clear()
            # reset_project_tree() baut ausschließlich die geschützten
            # Hauptknoten aus PROJECT_CATEGORIES wieder auf.
            self.reset_project_tree()
            self.set_project_modified(False)
            self.right_panel_tabs.setCurrentWidget(self.project_tab)
            self.right_dock.show()
            self.right_dock.raise_()
            self.statusBar().showMessage("Neues leeres Projekt angelegt")
            self.log("Neues Projekt: Projektbaum auf Hauptknoten zurückgesetzt")

        def load_project_file(
            self,
            path: Path,
            *,
            ask_before_replace: bool = True,
        ) -> bool:
            if ask_before_replace and not self._confirm_project_replacement(
                "Projekt öffnen"
            ):
                return False
            try:
                resolved = Path(path).expanduser().resolve()
                entries = load_project_ini(resolved)
            except (OSError, UnicodeError, configparser.Error, ValueError) as exc:
                self.show_error(
                    "Projekt konnte nicht geöffnet werden",
                    f"Die Projektdatei konnte nicht geladen werden:\n{path}\n\n{exc}",
                )
                return False
            self.current_project_path = resolved
            self.project_path_edit.setText(str(resolved))
            self.reset_project_tree(entries)
            self.set_project_modified(False)
            self.right_panel_tabs.setCurrentWidget(self.project_tab)
            self.right_dock.show()
            self.right_dock.raise_()
            self.statusBar().showMessage(f"Projekt geöffnet: {resolved.name}")
            self.log(f"Projekt geöffnet: {resolved}")
            return True

        def save_project(self) -> bool:
            if self.current_project_path is None:
                return self.save_project_as()
            try:
                save_project_ini(
                    self.current_project_path,
                    self.collect_project_entries(),
                )
            except OSError as exc:
                self.show_error(
                    "Projekt konnte nicht gespeichert werden",
                    str(exc),
                )
                return False
            self.project_path_edit.setText(str(self.current_project_path))
            self.set_project_modified(False)
            self.statusBar().showMessage(
                f"Projekt gespeichert: {self.current_project_path.name}"
            )
            self.log(f"Projekt gespeichert: {self.current_project_path}")
            return True

        def save_project_as(self) -> bool:
            start_path = (
                self.current_project_path
                if self.current_project_path is not None
                else self.current_directory / "project.pro"
            )
            filename, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "Projekt speichern unter",
                str(start_path),
                "dBase2Many-Projekte (*.pro);;Alle Dateien (*)",
            )
            if not filename:
                return False
            target = Path(filename)
            if target.suffix.casefold() != ".pro":
                target = target.with_suffix(".pro")
            try:
                self.current_project_path = target.expanduser().resolve()
            except OSError:
                self.current_project_path = target.expanduser()
            return self.save_project()

        def _project_new_file_directory(self) -> Path:
            """Zielordner fuer neue, ueber das Projekt erzeugte Dateien."""
            if self.current_project_path is not None:
                directory = self.current_project_path.parent
            else:
                directory = self.current_directory
            directory = Path(directory).expanduser()
            directory.mkdir(parents=True, exist_ok=True)
            return directory

        def _project_existing_names(self) -> List[str]:
            names: List[str] = []
            for root in self.project_root_items.values():
                for index in range(root.childCount()):
                    child = root.child(index)
                    names.append(child.text(0))
                    path_value = str(child.data(0, Qt.UserRole + 302) or "")
                    if path_value:
                        path = Path(path_value)
                        names.extend((path.name, path.stem))
            return names

        def _write_new_project_file(self, category_key: str, path: Path) -> None:
            """Erzeugt eine gueltige leere Datei fuer die Projektkategorie."""
            path.parent.mkdir(parents=True, exist_ok=True)
            if category_key == "character_maps":
                path.write_bytes(bytes(C64_CHARACTER_FILE_SIZE))
                return
            if category_key == "palettes":
                path.write_bytes(encode_c64_palette_data(C64_CHARACTER_PALETTE))
                return
            if category_key == "char_screens":
                path.write_bytes(
                    encode_c64_text_screen_data(
                        bytearray([32] * C64_TEXT_SCREEN_CELL_COUNT),
                        bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT),
                    )
                )
                return
            if category_key == "pixel_screens":
                path.write_bytes(
                    encode_c64_pixel_screen_data(
                        bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT)
                    )
                )
                return
            if category_key == "images":
                image = QImage(320, 200, QImage.Format_ARGB32)
                image.fill(QColor(0, 0, 0))
                if not image.save(str(path), "PNG"):
                    raise OSError(f"Die Bilddatei konnte nicht erzeugt werden: {path}")
                return
            if category_key == "sid_files":
                # Minimale, syntaktisch gueltige PSID-v2-Datei mit einer RTS-
                # Routine bei $1000. Sie kann danach in einem SID-Werkzeug
                # weiterbearbeitet werden.
                payload = bytearray(0x7C)
                payload[0:4] = b"PSID"
                payload[4:6] = (2).to_bytes(2, "big")
                payload[6:8] = (0x7C).to_bytes(2, "big")
                payload[8:10] = (0).to_bytes(2, "big")
                payload[10:12] = (0x1000).to_bytes(2, "big")
                payload[12:14] = (0x1000).to_bytes(2, "big")
                payload[14:16] = (1).to_bytes(2, "big")
                payload[16:18] = (1).to_bytes(2, "big")
                payload[22:54] = b"Unbenannter SID".ljust(32, b"\0")
                payload[54:86] = b"dBase2Many".ljust(32, b"\0")
                payload[86:118] = b"2026".ljust(32, b"\0")
                payload.extend(b"\x00\x10\x60")
                path.write_bytes(payload)
                return
            source_templates = {
                "basic": (
                    "10 REM NEUES C64 BASIC-PROGRAMM\n"
                    "20 PRINT \"HALLO C64\"\n"
                    "30 END\n"
                ),
                "assembler": (
                    "; Neues MOS-6510-Assemblerprogramm\n"
                    ".org $080D\n"
                    ".entry start\n\n"
                    "start:\n"
                    "    rts\n"
                ),
                "pascal": (
                    "program Unbenannt;\n\n"
                    "begin\n"
                    "end.\n"
                ),
                "c": (
                    "int main(void)\n"
                    "{\n"
                    "    return 0;\n"
                    "}\n"
                ),
                "text_files": "",
            }
            path.write_text(
                source_templates.get(category_key, ""),
                encoding="utf-8",
                newline="\n",
            )

        def _open_new_project_file(self, category_key: str, path: Path) -> None:
            if category_key == "character_maps":
                self.show_character_editor(initial_path=path)
            elif category_key == "palettes":
                self.show_palette_editor(initial_path=path)
            elif category_key == "char_screens":
                self.show_text_screen_editor(initial_path=path)
            elif category_key == "pixel_screens":
                self.show_pixel_screen_editor(initial_path=path)
            elif category_key in {"images", "sid_files"}:
                self.open_path(path)
            else:
                self.open_document(path)

        def create_new_project_item(
            self, item: QTreeWidgetItem
        ) -> Optional[QTreeWidgetItem]:
            root = item if item.parent() is None else item.parent()
            category_key = str(root.data(0, Qt.UserRole + 301) or "other")
            directory = self._project_new_file_directory()
            filename = project_untitled_filename(
                category_key,
                self._project_existing_names(),
                directory=directory,
            )
            path = directory / filename
            try:
                self._write_new_project_file(category_key, path)
            except (OSError, ValueError) as exc:
                self.show_error(
                    "Neue Projektdatei konnte nicht angelegt werden",
                    f"Die Datei konnte nicht erzeugt werden:\n{path}\n\n{exc}",
                )
                return None
            child = self._add_project_entry(
                category_key,
                path,
                title=filename,
            )
            if child is None:
                return None
            self.project_tree.setCurrentItem(child)
            self.statusBar().showMessage(f"Neue Projektdatei angelegt: {filename}")
            self.log(f"Neue Projektdatei angelegt: {path}")
            if self.current_project_path is not None:
                self.save_project()
            self._open_new_project_file(category_key, path)
            return child

        def show_project_context_menu(self, position) -> None:
            item = self.project_tree.itemAt(position)
            if item is None:
                return
            self.project_tree.setCurrentItem(item)
            menu = QMenu(self.project_tree)
            help_action = menu.addAction("Hilfe")
            add_action = menu.addAction("Hinzufügen")
            clear_action = menu.addAction("Einträge löschen")
            root = item if item.parent() is None else item.parent()
            clear_action.setEnabled(root.childCount() > 0)
            selected = menu.exec_(
                self.project_tree.viewport().mapToGlobal(position)
            )
            if selected is help_action:
                self.show_project_item_help(item)
            elif selected is add_action:
                self.add_project_entries(item)
            elif selected is clear_action:
                self.clear_project_entries(item)

        def add_project_entries(self, item: QTreeWidgetItem) -> None:
            """Fügt vorhandene Dateien in die angewählte Projektkategorie ein."""
            root = item if item.parent() is None else item.parent()
            category_key = str(root.data(0, Qt.UserRole + 301) or "other")
            extensions = PROJECT_CATEGORY_EXTENSIONS.get(category_key, ())
            if extensions:
                patterns = " ".join(f"*{extension}" for extension in extensions)
                file_filter = (
                    f"{root.text(0)} ({patterns});;Alle Dateien (*)"
                )
            else:
                file_filter = "Alle Dateien (*)"
            initial = str(
                self.current_project_path.parent
                if self.current_project_path is not None
                else self.current_directory
            )
            filenames, _selected = QFileDialog.getOpenFileNames(
                self,
                f"Dateien zu '{root.text(0)}' hinzufügen",
                initial,
                file_filter,
            )
            added = 0
            for filename in filenames:
                path = Path(filename)
                child = self._add_project_entry(
                    category_key, path, title=path.name
                )
                if child is not None:
                    added += 1
            if added and self.current_project_path is not None:
                self.save_project()
            if added:
                root.setExpanded(True)
                self.statusBar().showMessage(
                    f"{added} Projekteintrag/Projekteinträge hinzugefügt"
                )

        def clear_project_entries(self, item: QTreeWidgetItem) -> None:
            """Entfernt nur Referenzen; Dateien bleiben unverändert erhalten."""
            root = item if item.parent() is None else item.parent()
            count = root.childCount()
            if count <= 0:
                return
            answer = self._show_message_box(
                QMessageBox.Question,
                "Projekteinträge löschen",
                f"Sollen alle {count} Einträge aus '{root.text(0)}' "
                "entfernt werden?\n\n"
                "Die Dateien auf dem Datenträger werden nicht gelöscht oder "
                "umbenannt.",
                buttons=QMessageBox.Yes | QMessageBox.No,
                default_button=QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
            root.takeChildren()
            self.set_project_modified(True)
            if self.current_project_path is not None:
                self.save_project()
            self.statusBar().showMessage(
                f"{count} Projekteinträge aus '{root.text(0)}' entfernt"
            )

        def show_project_item_help(self, item: QTreeWidgetItem) -> None:
            root = item if item.parent() is None else item.parent()
            key = str(root.data(0, Qt.UserRole + 301) or "other")
            extensions = PROJECT_CATEGORY_EXTENSIONS.get(key, ())
            extension_text = ", ".join(extensions) if extensions else "beliebige Dateien"
            self._show_message_box(
                QMessageBox.Information,
                f"Projektkategorie: {root.text(0)}",
                "Diese Kategorie sammelt Projektdateien des entsprechenden "
                f"Typs. Unterstützte Erweiterungen: {extension_text}.\n\n"
                "Ein Eintrag wird mit einem Klick geöffnet. "
                "Löschen entfernt nur die Referenz aus dem Projekt, nicht die "
                "Datei vom Datenträger.",
            )

        def rename_project_item(self, item: QTreeWidgetItem) -> None:
            if item.parent() is None:
                return
            value, accepted = QInputDialog.getText(
                self,
                "Projekteintrag umbenennen",
                "Anzeigename:",
                QLineEdit.Normal,
                item.text(0),
            )
            value = value.strip()
            if accepted and value and value != item.text(0):
                item.setText(0, value)
                self.set_project_modified(True)

        def copy_project_item(self, item: QTreeWidgetItem) -> None:
            if item.parent() is None:
                return
            payload = {
                "title": item.text(0),
                "path": str(item.data(0, Qt.UserRole + 302) or ""),
            }
            QApplication.clipboard().setText(
                "D64PROJECTITEM:" + json.dumps(payload, ensure_ascii=False)
            )
            self.statusBar().showMessage("Projekteintrag kopiert")

        def paste_project_item(self, item: QTreeWidgetItem) -> None:
            root = item if item.parent() is None else item.parent()
            category_key = str(root.data(0, Qt.UserRole + 301) or "other")
            clipboard_text = QApplication.clipboard().text().strip()
            if not clipboard_text:
                return
            title = ""
            path_value = clipboard_text
            if clipboard_text.startswith("D64PROJECTITEM:"):
                try:
                    payload = json.loads(
                        clipboard_text[len("D64PROJECTITEM:"):]
                    )
                    title = str(payload.get("title", ""))
                    path_value = str(payload.get("path", ""))
                except json.JSONDecodeError:
                    return
            candidate = Path(path_value.strip().strip('"'))
            if not str(candidate):
                return
            child = self._add_project_entry(
                category_key,
                candidate,
                title=title,
            )
            if child is not None:
                self.project_tree.setCurrentItem(child)

        def delete_project_item(self, item: QTreeWidgetItem) -> None:
            parent = item.parent()
            if parent is None:
                return
            answer = self._show_message_box(
                QMessageBox.Question,
                "Projekteintrag löschen",
                f"Soll '{item.text(0)}' aus dem Projekt entfernt werden?\n\n"
                "Die Datei auf dem Datenträger bleibt erhalten.",
                buttons=QMessageBox.Yes | QMessageBox.No,
                default_button=QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
            parent.takeChild(parent.indexOfChild(item))
            self.set_project_modified(True)

        def open_project_item(
            self,
            item: QTreeWidgetItem,
            _column: int = 0,
        ) -> None:
            if item.parent() is None:
                item.setExpanded(not item.isExpanded())
                return
            path_value = str(item.data(0, Qt.UserRole + 302) or "")
            if not path_value:
                return
            path = Path(path_value)
            if not path.exists():
                self.show_error(
                    "Projektdatei nicht gefunden",
                    f"Der Projekteintrag verweist auf eine nicht vorhandene Datei:\n{path}",
                )
                return
            if path.suffix.casefold() in self.EDITOR_EXTENSIONS:
                self.open_document(path)
            else:
                self.open_path(path)

        def _create_right_dock(self) -> None:
            self.right_dock = QDockWidget("Projekt / Informationen", self)
            self.right_dock.setObjectName("d64_content_dock")
            self.right_dock.setFeatures(self._dock_features())
            self.right_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.right_dock.setMinimumWidth(360)

            container = QWidget(self.right_dock)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(7, 7, 7, 7)
            layout.setSpacing(6)

            self.right_panel_tabs = QTabWidget(container)
            self.right_panel_tabs.setObjectName("right_panel_tabs")
            self.right_panel_tabs.setDocumentMode(True)
            self.right_panel_tabs.setMovable(False)
            self.right_panel_tabs.setTabsClosable(False)

            self.project_tab = self._create_project_tab(self.right_panel_tabs)

            self.information_panel_tab = QWidget(self.right_panel_tabs)
            self.information_panel_tab.setObjectName("information_panel_tab")
            information_layout = QVBoxLayout(self.information_panel_tab)
            information_layout.setContentsMargins(0, 0, 0, 0)
            information_layout.setSpacing(0)

            self.right_info_tabs = QTabWidget(self.information_panel_tab)
            self.right_info_tabs.setObjectName("right_information_tabs")
            self.right_info_tabs.setDocumentMode(True)
            self.right_info_tabs.setMovable(False)
            self.right_info_tabs.setTabsClosable(False)
            self.right_info_tabs.setUsesScrollButtons(True)

            self.dism_info_tab = QWidget(self.right_info_tabs)
            self.dism_info_tab.setObjectName("dism_start_information_tab")
            dism_layout = QVBoxLayout(self.dism_info_tab)
            dism_layout.setContentsMargins(5, 5, 5, 5)
            dism_layout.setSpacing(6)

            self.dism_summary = QLabel(
                "Noch keine DISM-START-Ausgabe vorhanden",
                self.dism_info_tab,
            )
            self.dism_summary.setObjectName("dism_start_summary")
            self.dism_summary.setWordWrap(True)
            self.dism_summary.setFrameShape(QFrame.StyledPanel)
            self.dism_summary.setMargin(7)
            dism_layout.addWidget(self.dism_summary)

            self.dism_content_list = QListWidget(self.dism_info_tab)
            self.dism_content_list.setObjectName("dism_start_content_list")
            self.dism_content_list.setAlternatingRowColors(True)
            self.dism_content_list.setSelectionMode(QListWidget.SingleSelection)
            self.dism_content_list.setFont(
                QFontDatabase.systemFont(QFontDatabase.FixedFont)
            )
            dism_layout.addWidget(self.dism_content_list, 1)

            self.file_info_tab = QWidget(self.right_info_tabs)
            self.file_info_tab.setObjectName("file_information_tab")
            file_layout = QVBoxLayout(self.file_info_tab)
            file_layout.setContentsMargins(5, 5, 5, 5)
            file_layout.setSpacing(6)

            self.d64_summary = QLabel(
                "Keine Datei ausgewählt",
                self.file_info_tab,
            )
            self.d64_summary.setWordWrap(True)
            self.d64_summary.setFrameShape(QFrame.StyledPanel)
            self.d64_summary.setMargin(7)
            file_layout.addWidget(self.d64_summary)

            self.content_list = QListWidget(self.file_info_tab)
            self.content_list.setObjectName("d64_content_list")
            self.content_list.setAlternatingRowColors(True)
            self.content_list.setSelectionMode(QListWidget.SingleSelection)
            self.content_list.setFont(
                QFontDatabase.systemFont(QFontDatabase.FixedFont)
            )
            file_layout.addWidget(self.content_list, 1)

            self.right_info_tabs.addTab(self.dism_info_tab, "DISM START")
            self.right_info_tabs.addTab(self.file_info_tab, "Datei-Informationen")
            self.right_info_tabs.setCurrentWidget(self.file_info_tab)
            information_layout.addWidget(self.right_info_tabs, 1)

            self.right_panel_tabs.addTab(self.project_tab, "Projekt")
            self.right_panel_tabs.addTab(
                self.information_panel_tab,
                "Informationen",
            )
            self.right_panel_tabs.setCurrentWidget(self.information_panel_tab)
            layout.addWidget(self.right_panel_tabs, 1)

            self.right_dock.setWidget(container)
            self.right_dock.setTitleBarWidget(DockTitleBar(self.right_dock))
            self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)
            self.view_menu.addAction(self.right_dock.toggleViewAction())

        def _create_bottom_dock(self) -> None:
            self.bottom_dock = QDockWidget("Protokoll", self)
            self.bottom_dock.setObjectName("log_dock")
            self.bottom_dock.setFeatures(self._dock_features())
            self.bottom_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.bottom_dock.setMinimumHeight(110)

            container = QWidget(self.bottom_dock)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(6, 6, 6, 6)
            layout.setSpacing(4)

            self.log_edit = QTextEdit(container)
            self.log_edit.setReadOnly(True)
            self.log_edit.setAcceptRichText(False)
            self.log_edit.setFont(
                QFontDatabase.systemFont(QFontDatabase.FixedFont)
            )

            layout.addWidget(self.log_edit, 1)
            self.bottom_dock.setWidget(container)
            self.bottom_dock.setTitleBarWidget(
                DockTitleBar(
                    self.bottom_dock,
                    extra_text="Protokoll löschen",
                    extra_callback=self.log_edit.clear,
                )
            )
            self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
            self.view_menu.addAction(self.bottom_dock.toggleViewAction())

        # ----- Statusleiste, Registerkarten und Kontexthilfe ----------------

        def _create_status_panels(self) -> None:
            status = self.statusBar()

            self.keyboard_status_panel = QFrame(status)
            self.keyboard_status_panel.setObjectName("status_keyboard_panel")
            keyboard_layout = QHBoxLayout(self.keyboard_status_panel)
            keyboard_layout.setContentsMargins(7, 1, 7, 1)
            keyboard_layout.setSpacing(8)
            self.insert_status_label = QLabel("INS", self.keyboard_status_panel)
            self.caps_status_label = QLabel("CAPS", self.keyboard_status_panel)
            self.num_status_label = QLabel("NUM", self.keyboard_status_panel)
            for label in (
                self.insert_status_label,
                self.caps_status_label,
                self.num_status_label,
            ):
                label.setMinimumWidth(34)
                label.setAlignment(Qt.AlignCenter)
                keyboard_layout.addWidget(label)

            self.file_status_panel = QFrame(status)
            self.file_status_panel.setObjectName("status_file_panel")
            file_layout = QHBoxLayout(self.file_status_panel)
            file_layout.setContentsMargins(8, 1, 8, 1)
            self.file_size_status_label = QLabel(
                "Dateigröße: –",
                self.file_status_panel,
            )
            self.file_size_status_label.setMinimumWidth(150)
            file_layout.addWidget(self.file_size_status_label)

            self.cursor_status_panel = QFrame(status)
            self.cursor_status_panel.setObjectName("status_cursor_panel")
            cursor_layout = QHBoxLayout(self.cursor_status_panel)
            cursor_layout.setContentsMargins(8, 1, 8, 1)
            self.cursor_status_label = QLabel(
                "Zeile: –  Spalte: –",
                self.cursor_status_panel,
            )
            self.cursor_status_label.setMinimumWidth(160)
            cursor_layout.addWidget(self.cursor_status_label)

            status.addPermanentWidget(self.keyboard_status_panel)
            status.addPermanentWidget(self.file_status_panel)
            status.addPermanentWidget(self.cursor_status_panel)

            self.status_refresh_timer = QTimer(self)
            self.status_refresh_timer.setInterval(250)
            self.status_refresh_timer.timeout.connect(
                self._update_editor_status_panels
            )
            self.status_refresh_timer.start()
            self._update_editor_status_panels()

        @staticmethod
        def _format_byte_count(value: int) -> str:
            return f"{max(0, int(value)):,}".replace(",", ".") + " Bytes"

        @staticmethod
        def _set_indicator_state(label: QLabel, enabled: bool) -> None:
            color = "#32d26f" if enabled else "#ff5b5b"
            label.setStyleSheet(
                f"color:{color}; background:transparent; font-weight:bold;"
            )

        def _windows_toggle_key_state(self, virtual_key: int) -> Optional[bool]:
            if os.name != "nt":
                return None
            try:
                import ctypes
                return bool(ctypes.windll.user32.GetKeyState(virtual_key) & 1)
            except (AttributeError, OSError):
                return None

        def eventFilter(self, watched, event):
            if event.type() == QEvent.KeyPress and not event.isAutoRepeat():
                if event.key() == Qt.Key_CapsLock:
                    self._caps_lock_fallback = not self._caps_lock_fallback
                elif event.key() == Qt.Key_NumLock:
                    self._num_lock_fallback = not self._num_lock_fallback
                QTimer.singleShot(0, self._update_editor_status_panels)
            return super().eventFilter(watched, event)

        def _update_editor_status_panels(self, *_args) -> None:
            if not hasattr(self, "insert_status_label"):
                return
            document = self.current_document()
            editor = document.active_text_editor() if document else None
            insert_enabled = not editor.overwriteMode() if editor else False
            caps_enabled = self._windows_toggle_key_state(0x14)
            num_enabled = self._windows_toggle_key_state(0x90)
            if caps_enabled is None:
                caps_enabled = self._caps_lock_fallback
            if num_enabled is None:
                num_enabled = self._num_lock_fallback

            self._set_indicator_state(
                self.insert_status_label,
                insert_enabled,
            )
            self._set_indicator_state(self.caps_status_label, caps_enabled)
            self._set_indicator_state(self.num_status_label, num_enabled)

            if document is None:
                self.file_size_status_label.setText("Dateigröße: –")
                self.cursor_status_label.setText("Zeile: –  Spalte: –")
                return

            try:
                size = len(document.data_for_saving())
                self.file_size_status_label.setText(
                    "Dateigröße: " + self._format_byte_count(size)
                )
            except (UnicodeError, ValueError):
                self.file_size_status_label.setText("Dateigröße: ?")

            if editor is not None:
                cursor = editor.textCursor()
                self.cursor_status_label.setText(
                    f"Zeile: {cursor.blockNumber() + 1}  "
                    f"Spalte: {cursor.positionInBlock() + 1}"
                )
            elif document.views.currentWidget() is document.hex_editor:
                index = max(0, int(document.hex_editor._cursor_index))
                self.cursor_status_label.setText(
                    f"Zeile: {index // document.hex_editor.BYTES_PER_ROW + 1}  "
                    f"Spalte: {index % document.hex_editor.BYTES_PER_ROW + 1}"
                )
            else:
                self.cursor_status_label.setText("Zeile: –  Spalte: –")

        def _show_document_tab_context_menu(self, position) -> None:
            tab_bar = self.document_tabs.tabBar()
            index = tab_bar.tabAt(position)
            if index < 0:
                return
            document = self.document_tabs.widget(index)
            if not isinstance(document, DocumentEditor):
                return
            self.document_tabs.setCurrentIndex(index)

            menu = QMenu(tab_bar)
            new_menu = menu.addMenu("Neu")
            self._populate_new_document_menu(new_menu)
            menu.addSeparator()
            save_action = menu.addAction("Speichern")
            save_as_action = menu.addAction("Speichern unter...")

            selected = menu.exec_(tab_bar.mapToGlobal(position))
            if selected is save_action:
                self._save_document(document, save_as=False)
            elif selected is save_as_action:
                self._save_document(document, save_as=True)

        def rename_document_tab(self, document: DocumentEditor) -> bool:
            old_name = document.display_name
            new_name, accepted = QInputDialog.getText(
                self,
                "Registerkarte umbenennen",
                "Neuer Datei-/Registerkartenname:",
                QLineEdit.Normal,
                old_name,
            )
            if not accepted:
                return False
            new_name = new_name.strip()
            if not new_name or Path(new_name).name != new_name:
                self.show_error(
                    "Ungültiger Name",
                    "Bitte nur einen Dateinamen ohne Verzeichnis angeben.",
                )
                return False

            if document.path is None:
                document.custom_display_name = new_name
                document.update_syntax_highlighting()
                self._apply_document_theme(document)
                self._update_document_tab(document)
                self.log(f"Registerkarte umbenannt: {old_name} -> {new_name}")
                return True

            old_path = document.path
            if not Path(new_name).suffix and old_path.suffix:
                new_name += old_path.suffix
            target = old_path.with_name(new_name)
            if target.resolve() == old_path.resolve():
                return True
            if target.exists() and target.resolve() != old_path.resolve():
                self.show_error(
                    "Datei existiert bereits",
                    f"Die Datei existiert bereits:\n{target}",
                )
                return False
            try:
                old_path.rename(target)
            except OSError as exc:
                self.show_error(
                    "Datei konnte nicht umbenannt werden",
                    f"{old_path}\n\n{exc}",
                )
                return False

            document.path = target.resolve()
            document.custom_display_name = None
            document.update_syntax_highlighting()
            document.invalidate_assembly_result("Dateiname geändert")
            self._apply_document_theme(document)
            self._replace_project_path_reference(old_path, document.path)
            self._update_document_tab(document)
            self.populate_file_list()
            self.log(f"Datei umbenannt: {old_path} -> {document.path}")
            return True

        def _replace_project_path_reference(
            self,
            old_path: Path,
            new_path: Path,
        ) -> None:
            if not hasattr(self, "project_tree"):
                return
            old_value = os.path.normcase(str(Path(old_path).resolve()))
            iterator = QTreeWidgetItemIterator(self.project_tree)
            changed = False
            while iterator.value() is not None:
                item = iterator.value()
                value = str(item.data(0, Qt.UserRole + 302) or "")
                if value and os.path.normcase(str(Path(value).resolve())) == old_value:
                    item.setData(0, Qt.UserRole + 302, str(new_path))
                    item.setText(0, Path(new_path).name)
                    changed = True
                iterator += 1
            if changed:
                self.set_project_modified(True)

        @staticmethod
        def _help_language_folder(language: str) -> str:
            return {
                "basic": "basic",
                "assembler": "assembler",
                "pascal": "pascal",
                "c": "c",
            }.get(str(language).casefold(), "allgemein")

        def _context_help_link(
            self,
            chm_path: Path,
            language: str,
            word: str,
        ) -> str:
            folder = self._help_language_folder(language)
            topic = re.sub(r"[^A-Za-z0-9_.-]+", "_", word.strip()) or "index"
            native = QDir.toNativeSeparators(str(chm_path))
            return f"mk:@MSITStore:{native}::/{folder}/{topic}.html"

        def show_context_help_for_document(
            self,
            document: DocumentEditor,
            language: str,
            word: str,
        ) -> None:
            if self._document_index(document) >= 0:
                self.document_tabs.setCurrentWidget(document)
            word = str(word or "").strip()
            if not word:
                self._show_message_box(
                    QMessageBox.Information,
                    "Kontexthilfe",
                    "Am Cursor wurde kein Bezeichner gefunden.",
                )
                return

            last_file = str(self.settings.value("chm/last_file", "") or "")
            chm_path = (
                Path(last_file)
                if last_file and Path(last_file).is_file()
                else Path(__file__).resolve().with_name("Hilfe.chm")
            )
            link = self._context_help_link(chm_path, language, word)

            # DEBUG: Diese MessageBox zeigt vorläufig den erzeugten CHM-Link.
            # Nach Abschluss der Hilfethemen-Zuordnung kann sie entfernt werden.
            self._show_message_box(
                QMessageBox.Information,
                "DEBUG – F1-Kontexthilfe",
                f"Sprache: {language.upper()}\n"
                f"Bezeichner: {word}\n\n"
                f"Link: {link}",
            )
            self.show_chm_viewer(
                context_language=language,
                context_word=word,
            )

        # ----- Navigation --------------------------------------------------

        def _choose_start_directory(self, requested: Optional[Path]) -> Path:
            candidates = [
                requested,
                Path(str(self.settings.value("workspace/root", "")))
                if self.settings.value("workspace/root", "")
                else None,
                Path.cwd(),
            ]
            for candidate in candidates:
                if candidate is None:
                    continue
                try:
                    resolved = candidate.expanduser().resolve()
                except OSError:
                    continue
                if resolved.is_file():
                    resolved = resolved.parent
                if resolved.is_dir():
                    return resolved
            return Path.cwd().resolve()

        @staticmethod
        def _native_path(path: Path) -> str:
            return QDir.toNativeSeparators(str(path))

        @staticmethod
        def _path_is_within(path: Path, root: Path) -> bool:
            try:
                return os.path.commonpath((str(path), str(root))) == str(root)
            except ValueError:
                return False

        def set_workspace_root(self, path: Path, *, select: bool = True) -> None:
            path = Path(path).expanduser().resolve()
            if not path.is_dir():
                self.show_error("Ungültiger Ordner", f"Der Ordner existiert nicht:\n{path}")
                return

            self.workspace_root = path
            root_index = self.file_system_model.setRootPath(str(path))
            self.directory_tree.setRootIndex(root_index)
            self.directory_tree.setCurrentIndex(root_index)
            self.directory_tree.expand(root_index)
            if select:
                self.set_current_directory(path, select_tree=False)
            self.log(f"Arbeitsverzeichnis gesetzt: {path}")

        def set_current_directory(
            self, path: Path, *, select_tree: bool = True
        ) -> None:
            path = Path(path).expanduser().resolve()
            if not path.is_dir():
                self.show_error("Ungültiger Ordner", f"Der Ordner existiert nicht:\n{path}")
                return

            if not self._path_is_within(path, self.workspace_root):
                self.set_workspace_root(path, select=False)

            try:
                os.chdir(path)
            except OSError as exc:
                self.show_error(
                    "Arbeitsverzeichnis nicht erreichbar",
                    f"Das Arbeitsverzeichnis konnte nicht gewechselt werden:\n{exc}",
                )
                return

            self.current_directory = path
            self.path_edit.setText(self._native_path(path))
            if select_tree:
                self.select_tree_path(path)
            self.populate_file_list()
            self.statusBar().showMessage(f"Arbeitsverzeichnis: {path}")

        def select_tree_path(self, path: Path) -> None:
            index = self.file_system_model.index(str(path))
            if not index.isValid():
                return

            parents = []
            parent = index.parent()
            root_index = self.directory_tree.rootIndex()
            while parent.isValid() and parent != root_index:
                parents.append(parent)
                parent = parent.parent()
            for value in reversed(parents):
                self.directory_tree.expand(value)

            self.directory_tree.setCurrentIndex(index)
            self.directory_tree.scrollTo(index, QTreeView.PositionAtCenter)

        def choose_workspace_directory(self) -> None:
            selected = QFileDialog.getExistingDirectory(
                self,
                "Arbeitsverzeichnis auswählen",
                str(self.current_directory),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            )
            if selected:
                self.set_workspace_root(Path(selected), select=True)

        def navigate_from_path_edit(self) -> None:
            raw_path = self.path_edit.text().strip()
            if not raw_path:
                self.path_edit.setText(self._native_path(self.current_directory))
                return

            expanded = os.path.expandvars(os.path.expanduser(raw_path))
            path = Path(expanded)
            if not path.is_absolute():
                path = self.current_directory / path
            try:
                path = path.resolve()
            except OSError as exc:
                self.show_error("Pfadfehler", str(exc))
                return

            if not path.is_dir():
                self.show_error(
                    "Verzeichnis nicht gefunden",
                    f"Der eingegebene Ordner existiert nicht:\n{path}",
                )
                self.path_edit.selectAll()
                return

            self.set_current_directory(path)
            self.log(f"Per Pfadeingabe gewechselt: {path}")

        def directory_tree_clicked(self, index) -> None:
            path = Path(self.file_system_model.filePath(index))
            if path.is_dir():
                self.set_current_directory(path, select_tree=False)
                self.log(f"Ordner ausgewählt: {path}")

        def go_to_parent_directory(self) -> None:
            parent = self.current_directory.parent
            if parent == self.current_directory:
                return
            self.set_current_directory(parent)
            self.log(f"Zum übergeordneten Ordner gewechselt: {parent}")

        # ----- Dateiliste --------------------------------------------------

        def matching_files(self) -> Iterable[Path]:
            extensions = self.FILTERS[self.current_filter]
            try:
                paths = sorted(
                    (path for path in self.current_directory.iterdir() if path.is_file()),
                    key=lambda path: path.name.casefold(),
                )
            except OSError as exc:
                self.show_error("Verzeichnisfehler", str(exc))
                return ()

            if extensions is None:
                return paths
            return [path for path in paths if path.suffix.lower() in extensions]

        def populate_file_list(self) -> None:
            self.file_list.clear()
            paths = list(self.matching_files())
            for path in paths:
                item = QListWidgetItem(self.icon_provider.icon(QFileInfo(str(path))), path.name)
                item.setData(Qt.UserRole, str(path))
                try:
                    size = path.stat().st_size
                    item.setToolTip(f"{path}\n{size:,} Bytes")
                except OSError:
                    item.setToolTip(str(path))
                self.file_list.addItem(item)

            self.log(
                f"{len(paths)} Datei(en) angezeigt; Filter: {self.current_filter}"
            )

        def set_filter(self, filter_name: str) -> None:
            if filter_name not in self.FILTERS:
                return
            self.current_filter = filter_name
            button = self.filter_buttons.get(filter_name)
            if button is not None and button.isCheckable():
                button.setChecked(True)
            self.populate_file_list()
            self.statusBar().showMessage(
                f"Filter {filter_name}: {self.file_list.count()} Datei(en)"
            )

        def selected_file_path(self) -> Optional[Path]:
            item = self.file_list.currentItem()
            if item is None:
                return None
            return Path(item.data(Qt.UserRole))

        def file_item_clicked(self, item: QListWidgetItem) -> None:
            path = Path(item.data(Qt.UserRole))
            if path.suffix.lower() == ".d64":
                self.show_d64_directory(path)
            else:
                self.show_file_information(path)

        def file_item_double_clicked(self, item: QListWidgetItem) -> None:
            path = Path(item.data(Qt.UserRole))
            if path.suffix.lower() == ".d64":
                self.show_d64_directory(path)
            elif path.suffix.lower() in self.EDITOR_EXTENSIONS:
                self.show_file_information(path)
                self.open_document(path)
            else:
                self.show_file_information(path)
                self.open_path(path)

        def open_selected_file(self) -> None:
            path = self.selected_file_path()
            if path is None:
                self.show_error("Keine Auswahl", "Bitte zuerst eine Datei auswählen.")
                return
            if path.suffix.lower() in self.EDITOR_EXTENSIONS:
                self.open_document(path)
            else:
                self.open_path(path)

        def open_path(self, path: Path) -> None:
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
                self.show_error(
                    "Datei konnte nicht geöffnet werden",
                    f"Für diese Datei ist keine Anwendung registriert:\n{path}",
                )
                return
            self.log(f"Datei geöffnet: {path}")

        # ----- Inhaltsanzeige ---------------------------------------------

        def show_d64_directory(self, path: Path) -> None:
            self.right_panel_tabs.setCurrentWidget(self.information_panel_tab)
            self.right_info_tabs.setCurrentWidget(self.file_info_tab)
            self.content_list.clear()
            try:
                directory = D64Image(path).directory()
            except D64Error as exc:
                self.d64_summary.setText(f"D64-Fehler: {path.name}")
                self.content_list.addItem(str(exc))
                self.log(f"D64-Fehler in {path}: {exc}")
                self.statusBar().showMessage("D64-Datei konnte nicht gelesen werden")
                return

            error_note = "mit Fehlerbyte-Tabelle" if directory.has_error_table else "ohne Fehlerbyte-Tabelle"
            free_text = (
                f"{directory.free_blocks} Blöcke frei"
                if directory.free_blocks is not None
                else "freie Blöcke unbekannt"
            )
            self.d64_summary.setText(
                f"<b>{path.name}</b><br>"
                f"Disk: {directory.disk_name} &nbsp; "
                f"ID: {directory.disk_id or '–'} &nbsp; "
                f"DOS: {directory.dos_type or '–'}<br>"
                f"{directory.track_count} Spuren, {error_note}, "
                f"{len(directory.entries)} Einträge, {free_text}"
            )

            header = QListWidgetItem("BLÖCKE  DATEINAME           TYP    START")
            header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
            self.content_list.addItem(header)

            for entry in directory.entries:
                item = QListWidgetItem(entry.listing_line())
                item.setToolTip(
                    f"Name: {entry.name}\n"
                    f"Typ: {entry.type_display}\n"
                    f"Blöcke: {entry.blocks}\n"
                    f"Start: Spur {entry.start_track}, Sektor {entry.start_sector}"
                )
                self.content_list.addItem(item)

            if not directory.entries:
                self.content_list.addItem("(Kein aktiver Verzeichniseintrag)")

            self.right_dock.show()
            self.right_dock.raise_()
            self.log(
                f"D64 analysiert: {path.name}; "
                f"{len(directory.entries)} Eintrag/Einträge"
            )
            self.statusBar().showMessage(
                f"D64: {directory.disk_name} – {len(directory.entries)} Einträge"
            )

        def show_file_information(self, path: Path) -> None:
            self.right_panel_tabs.setCurrentWidget(self.information_panel_tab)
            self.right_info_tabs.setCurrentWidget(self.file_info_tab)
            self.content_list.clear()
            try:
                stat = path.stat()
                size_text = f"{stat.st_size:,} Bytes"
            except OSError as exc:
                size_text = f"nicht lesbar: {exc}"

            self.d64_summary.setText(f"<b>{path.name}</b><br>Normale Datei")
            self.content_list.addItem(f"Pfad: {path}")
            self.content_list.addItem(f"Erweiterung: {path.suffix or '(keine)'}")
            self.content_list.addItem(f"Größe: {size_text}")
            self.right_dock.show()
            self.right_dock.raise_()
            self.statusBar().showMessage(f"Datei ausgewählt: {path.name}")

        # ----- Allgemeines -------------------------------------------------

        def refresh_views(self) -> None:
            current_root = self.workspace_root
            root_index = self.file_system_model.setRootPath("")
            del root_index
            root_index = self.file_system_model.setRootPath(str(current_root))
            self.directory_tree.setRootIndex(root_index)
            self.select_tree_path(self.current_directory)
            self.populate_file_list()
            self.log("Ansichten aktualisiert")

        def log(self, text: str) -> None:
            self.log_edit.append(text)

        def show_error(self, title: str, text: str) -> None:
            self._show_message_box(QMessageBox.Warning, title, text)
            if hasattr(self, "log_edit"):
                self.log(f"FEHLER: {title}: {text.replace(chr(10), ' ')}")

        @staticmethod
        def application_dark_mode(fallback: bool = False) -> bool:
            """Ermittelt den aktiven Modus direkt aus der App-Palette."""
            application = QApplication.instance()
            if application is None:
                return bool(fallback)
            palette = application.palette()
            background = palette.color(QPalette.Window)
            foreground = palette.color(QPalette.WindowText)
            return background.lightness() < foreground.lightness()

        def show_chm_viewer(
            self,
            _checked: bool = False,
            *,
            context_language: str = "",
            context_word: str = "",
        ) -> None:
            if not QT_WEBENGINE_AVAILABLE:
                self._show_message_box(
                    QMessageBox.Warning,
                    "CHM-Viewer nicht verfügbar",
                    "Für den CHM-Viewer wird PyQtWebEngine benötigt.<br><br>"
                    "Installation:<br>"
                    "<code>py -m pip install PyQtWebEngine</code><br><br>"
                    f"Technische Meldung: {html.escape(QT_WEBENGINE_ERROR)}",
                    rich_text=True,
                )
                return

            # Unmittelbar vor dem Oeffnen wird die tatsaechlich aktive
            # Anwendungspalette abgefragt. Das ist verlaesslicher als ein
            # moeglicherweise noch nicht synchronisiertes Umschalt-Flag.
            dark_mode = self.application_dark_mode(
                self.dark_mode_enabled
            )

            dialog = ChmViewerDialog(
                self,
                dark_mode=dark_mode,
            )
            # Noch vor CHM-Extraktion, erstem Seitenladen und exec_() wird die
            # Web-Oberflaeche auf den zuvor ermittelten Modus festgelegt.
            dialog.set_dark_mode(dark_mode)
            dialog.set_pending_context(context_language, context_word)
            last_file = str(
                self.settings.value("chm/last_file", "") or ""
            )
            if last_file and Path(last_file).is_file():
                dialog.open_chm(last_file)
            else:
                QTimer.singleShot(0, dialog.choose_chm)
            dialog.exec_()

        def show_about_dialog(self) -> None:
            self._show_message_box(
                QMessageBox.Information,
                "Über Qt5 D64-Explorer",
                "<b>Qt5 D64- und Dateisystem-Explorer</b><br><br>"
                "PyQt5-Anwendung mit verschiebbaren Dock-Fenstern, "
                "Dateifiltern, Texteditor mit Registerkarten und integriertem "
                "Commodore-1541-D64-Verzeichnisleser.",
                rich_text=True,
            )

        def _restore_window_state(self) -> None:
            geometry = self.settings.value("window/geometry")
            state = self.settings.value("window/state")
            if geometry is not None:
                self.restoreGeometry(geometry)
            if state is not None:
                self.restoreState(state)

        def closeEvent(self, event: QCloseEvent) -> None:
            if self.project_modified:
                if not self._confirm_project_replacement("Anwendung schließen"):
                    event.ignore()
                    return

            documents = [
                self.document_tabs.widget(index)
                for index in range(self.document_tabs.count())
            ]
            for document in documents:
                if not isinstance(document, DocumentEditor):
                    continue
                if not self._confirm_close_document(document):
                    event.ignore()
                    return

            if self.dism_thread is not None and self.dism_thread.isRunning():
                self._show_message_box(
                    QMessageBox.Information,
                    "DISM läuft",
                    "Die Anwendung kann erst geschlossen werden, wenn der "
                    "laufende DISM-Vorgang beendet ist.",
                )
                event.ignore()
                return

            self.settings.setValue("window/geometry", self.saveGeometry())
            self.settings.setValue("window/state", self.saveState())
            self.settings.setValue("workspace/root", str(self.workspace_root))
            super().closeEvent(event)

    if hasattr(QApplication, "setAttribute"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setOrganizationName(ExplorerWindow.ORGANIZATION)
    app.setApplicationName(ExplorerWindow.APPLICATION)
    app.setApplicationDisplayName("Qt5 D64-Explorer")

    c64_font_path = Path(__file__).resolve().with_name("C64Pro.ttf")
    c64_font_id = QFontDatabase.addApplicationFont(str(c64_font_path))
    if c64_font_id < 0:
        QMessageBox.critical(
            None,
            "C64-Font fehlt",
            "Der Hex-Editor benötigt die Font-Datei C64Pro.ttf im "
            "Verzeichnis der Anwendung:\n\n"
            f"{c64_font_path}",
        )
        return 1

    c64_font_families = QFontDatabase.applicationFontFamilies(c64_font_id)
    if not c64_font_families:
        QMessageBox.critical(
            None,
            "C64-Font ungültig",
            f"Die Font-Datei enthält keine verwendbare Schriftfamilie:\n\n"
            f"{c64_font_path}",
        )
        return 1

    HexEditor.C64_FONT_FAMILY = c64_font_families[0]
    window = ExplorerWindow(initial_directory)
    window.show()
    return app.exec_()

# ---------------------------------------------------------------------------
# Unveraenderte Programmlogik aus d64info.py
# SHA-256: 6ee8bc995af1df0d450d67b47f41a2407cfe5e978766d02dc2fba3f27c5cbcd1
# Der Quelltext wird in einem eigenen Modul-Namensraum ausgefuehrt, damit
# gleichnamige Klassen der vorhandenen GUI nicht ueberschrieben werden.
# ---------------------------------------------------------------------------
import types  as _d64info_types

# Generated with zlib.compress(source_bytes, level=9).
_D64INFO_COMPRESSED_B85 = (
    b"c-"
    b"ri}+jbgBwkZ0}S7g&(yP*m&Aap@x)!Ilxw%WS2Bv*Bnmj+HCk+KB|oe7pLZM~h(IAg4r`i6e0H~rX|mx#!S$Veo)T(#F4XL)p&fV"
    b"j_?F=O82&wqNkNaC0MFnSq8AHCV<`PDR9DHMyv!p}i?IrsLX(KMd;^Kcpkk++D3-q26r*DHTKPd*0mZ4eHwqA>A-"
    b"FbWcHXF8cohtoKy?yj|}`xE~Xe)OYSq0m{3;>BpQ;K4s0#v87+Lg>CW`|Rx>c3yXD@WW%}UbWiyCr_v~xbnj&c|yfx?#J`R?CCY("
    b"6D+(xO@b%12|mqZe=x7k;>#!0_9K7%`8IfB?O~YsNfJ!@<EP9d#LcM2{siYA4g&AfS}PgUf=|KohN=#x!ywxSqD)~FPbXflH(JaW"
    b"anS2|;bb<A=YRmwbWS*w6bkaU_;TjQ07LQp%1^GwVPAd?r}7gZ-<AA4P2{KKYB3MT>f3a19n96YdAt~;-xmE@JRJl{+V-"
    b">hI1eWQ&w4N&kAnftQBHdp{Bxm7qd9CPOi&ia!7z-WK`)sPr;9mP8~Ss9Fh)qFoyecK#tc@Y^>TuXqk{S8Sr}c)-}mQ1>;teX-"
    b"Z>1re_SXO&bmA2$EUrs{hzzume*WeE9~x{(r-WY&QCi#Z{gR*Mq#^i*yF13y{^^i9-W`=ch7n!-"
    b"P5$fMxn5`f6(on|8&wlgYS2Q3-wK}xZ6D_R_I#;zMXadCcZV{+sWx`@ofdZy*oP<-&*kPl-"
    b"k`F3cH<y?%Q7H{2Zp%J3oV2z3ITLVUQA4F0M8E1HZAhw$fi44C{l@V6@U-UFr7+!;Sj-%4)kgSP$B(tA4*83`dP-"
    b"V{J6(H|wKDf6({W+QZdip)5z)hqWDN27v0LjaI+4IttcTnyc%>*6PN_#%Q$C9{KIjV0~?4V`VUC_g9;(#$a`Qy&jB)>wX`m;kO%&"
    b"^*RmkXKyzQlEB-8-N8K>#t**&vU%4*6fyAwx)^-"
    b"&uVJghz)QlQ4?jeU$s~xwAf5*ic7e03GAydQ{yYewj=x9%#U?;hVY8FP;0o%(U<qI{eDeGKa6GJeyFhMF;^`<Hdtow%zWjayqXH@"
    b"puDlscW|ZJqFu6WZ=OEhjI*TNMqaJw=zxIRJ3$Nn9y9_2kpc8)*cxP}ruHk$_S2sZnEdWJ_ix_%~uwR(g$h%#P9)1~*!%Oesm#c_"
    b"|f>psWo(JA24kkbV#44Z{8V0Bw3|SNVarEwRyL;N*?E$91|Bn&JQuHeJ+x>RiUtg)OZM0WlcUrB{`k>ujZx4rS8?9yo{`sqo=E`c"
    b"LJ!p?snsva1Q7~FvSsx5n{Xx43cvi0qq$_R!#M>LN%k7n+zZ$H!2BY?{vEi?-4TtN4dZQV@Si#z8t=?$2g4H#@-"
    b"QQ^Wt<}L`B^cEE>(pCA_SW1O1*<C?!vJxyzS>;rH`jfCwY|F0_lFIb(r|rcWz^cJ5Bsh9XrsQd-UgfrnyWtGXM3$dy)|WTYpvDRV"
    b"51M642FH*hgJ7iR)c1Jtr7U6MyuXj^VjRcjg{f*a8Pd#gO!aDtiK5e8*H>;snpww?9Ctc8^d<p5B&9EyD{t!HrCf#YpZ~^8!Kz@-"
    b"$tw1Y^}6cg3<cA50Gj%hwD&ft-dxK0bXxVZ!I;qdOcWQ8#MdtupT^8>i}msXM-m6HXIE60f2vfurX-"
    b"2>cdgL)gCrs<tvSqX0zVd0Qh5Xs|s%GqhTM8D~#OU7y`Hkt;Vq48VumjHJklrW3>@9R{Fu}1{}q~$X{7qZ?{|RW^1EeZ}r=2)Y}@"
    b"9jvx1rc8`BNgJb<e=U{)ghv;+EIqdd!-gHh8kAPy{22m2sOMiLw{bupyfBeV)`S)-"
    b"BQdSL5yJy|gAG&Evvk}dhagpY}b9^M0L0?Z!jjx?|f7ibry*tppep4Dj^TRth@Nf$5iyp8`9)Iz|$cueAn59O=Yt+kSv(>@L`7>J"
    b"GGc7tEjl$b7fUC+oIy^qBuC3OaFV|KZ_3H5q@8zWCy^Ds^>jhARIguYv6v)FKPN16uASHO)=(NNi6BBnEjHAG-"
    b"^*_&nhl3mLdLDjcVs#l@B5gyG#PkC0r?8JC2?<|k7{e6{)ne>%0i6diGKoP{@uol|fz-"
    b"v&&p!e$@}cbsZbp(!<2d*jCUEN#WxGLw8bmnVA7pcy7_gC8g6r9j5~5%saw~p(yGZ5;51>5&5Clc<_+;mJw|lk;^BT<Ghta&^0oy"
    b"hX-b2F*at9X|=~efs4!2#YxPAJzSn-N*{T2npp`?K&$EO`Cx&5S-"
    b"tZF5<dXqIQ=$sv73O2Cd<jqNTl(s&~WTKUHw9fp&Kr7kR+Q24iC0)IZUee%oo=`~~jI|PTou9Q5bDbIl8s<Xv5?blb!A@qSjkY;!"
    b"eIRQ=dVki6w4x?0>95FtSc`4ak~&AbnXPNK2n_q@_6{{ywI)UZE%o#`v!_ko(}V1uHrx8}`kppBT4%<dHg~j%nTy%gdNWJ9dT)Bk"
    b"3h(yeerC5<OweeXuwp_$1KNrS0=<M_0Q_VI1}klI*7`u!g7p5Z6=_8+TGHwHerBi^Evb8an%V8vs#c=!U5i$9aF#6)2ep$OrLB*m"
    b"Z)&Tfb!Kd8i#GMIhbNg0YVB&hnI&DlH@#$)H}!{|%%-"
    b"lI5YS+~YC=GR&8i6ky+j=0ETmW4=B)LBtOe=)Su4_t*2JcsWrkW~Jl);NZ0g#oR-"
    b"*6Snn2Ucrml&Tn%&g3wmyo!scRjrGh<WN^i2(;p;of1^=53{T37E)FIg9xdY0MLbrS*_tk+ElXs}r~L7<n2lbYSs^|m={eIRQ=dV"
    b"ki6w4x1~_}O{(;@oI)$xrqUZLDfdjDj^T_<N>+*0bCFDYKpp+PU+;XLoyJM;qSQg^gWpe6yshO~5E=^Um#Lk7L^efCkXE2>=Z=Z4"
    b"&}|i3tL|H-f?WPuZ2W+va-oMglz9BiFWopv|E}YdzTgDRWLb4KB%UcBjcDf6umQX}#&2+F8{)GYZzUzKj9}K_`m_owhzPV|a!@=k"
    b"M7zJKDsI&F<`Ky_qFlZE8lzwm^{V(cU(JrtQwQ2^tNY+a_%E5)(LjZ-SElkXh+=+gy*{h{1D~1<$qx9(@iLeDop<K-"
    b"y3{1fiXiEL!algmwgx)zNCFrM1yfVP{oqVic?~smNRyI|QEnqb&05wDsYQiFLTMEOd5uw22vru(PZ6W|nldsTn1^j66r(4D#%npw"
    b"Ym&YeGN++O7!#y+okMZe~5ZZFAQ8K-Plv{;U;gMP0GmS%T1Ig1Mc&?7J<kjlOr?Rjr9pu*RF3EfBk%-"
    b"MMaCAKsW4?e@`emdEezXcIGbuDh%CW|nldsTn1EyxXW|wRU^Y1dX-{dnN=lpzWC;&`SgtklpRQwmEBkAZtN-"
    b"f7Xhq=)Rz2@k5ZrrOsMt|8UezuOW3>gMs!9VZZ4$#kbp;@#T~8?X&g`F-HHUmmx6IZwT~FZzcWq$^80R`--"
    b"d`eS`HB{_Jgs(Zers5PLuD?{uq&(<q!z<BHcg*{}W(#HhpYnzaHJ_TabP58czV{o^Cl!hfna`FFU(jqlwbx<}`|)9&Bib<fUw`@2"
    b"-QC;k<<&d%X(@34D_D*V^ob8g;9i+0|0cix^H??XRlqPWpai+A50p3sjitxfmu`&_frNq_v?JMrW8cKYMV{?TjtaYJjq-"
    b"8p)D*6aMx*+1xPA9T4~8?*E7{1}*sQ|@keS1jbTdv<bsbk^0T%+qaH<!9%|CnsG7##+-"
    b"Vgb(iyW#Nid_}9)M7c|6}0JyW04u0tDi>;`OiQ*&x65SpCxm75fb`A+%5?@hg0{^6u0gKUy@)MN5KI)vmJH<+<C`)Q+!nq1Q3ByC"
    b"D={459?NzVd@Y=gxz3w&Y-cASqySL$W+FpIlgF34%uT%G08)Rp|-"
    b"nUOXM>}tNhexp8NBcXP##}I&f|U?tLP+=GiV&I|Asv!Dk(yz!_p_f4w~r6bbk$b_m0!h6e-"
    b"iYD!OS0A2XQggej(p!7WRhIC`fB;G*t6s?q3GYUJ%XW&&5>bgnF3bWRZk}-"
    b"fZmaB`9Z$k`PW(TC$4*5uCkwJnfCbIOqkRwBi;|nTyFFs}&)66-8nE&)zUhX8wF|mDXrBsRoqIr!(zm)H)Ptuo-GGgP~T2$^~jN3"
    b"5UaRpp|UMlKyl)pH8%rUAQ%hA7N?G8xRStQERuQ<`_>G^Dqi}t=6!W)>uXH#jdfs;cGRJPtVk7Ym;6>y@Oq2tu@eU?4~s)ei)@C>"
    b"nL#*hXHI?FS(lP0A5G=NfeEz(WO?>MoZveI-bV8WDrls<Fss}u?=NOFb6orLqMWF;L;^bE7E4X(L}={H-(M+7!Ea5Y;B-"
    b"w3Me^t68p&<I+>$+RIAZysu~J8<^i7p#Qry()7>9Cr(MS}*sY@mv<PIOw{w1a&?u%XSfeQlPCIAk-BZ0}O>5HB3pPXn(4LcXqe)w"
    b"o?4SOvw|CHaeWn+7w8F#A*;}m)^_*0;eSErW%%UkLzTMe*`}*|w-"
    b"O+AcFK%Xv_0=_3GR4|TT6EIR_L1P9b+z9c>*Dvl{R0CiEm}L4{BV2#R5~r$L0x)rXTQ_vogAN@_qO$-U0H-n-"
    b"#JEG?tv<Yix44mbci=9TCMdGJhs?KmEcWH)^=}qt<{a=X<X`l8U!=67L?ifq*yHO1y^IZ$NNDz@eTlGB5w-"
    b"l=Ix^)76<?uPSB`J9xbUKOO0F{3jbSK^h<0}+B%OHL0Js@LpTToYj7GQvuTtBJZvn!_2!>v!KMc|N<RlU$MkEAE(Zyq@G$+YKOKJ"
    b"F<a_4P;ZOYu+egTgfk*a-"
    b"WSY?i@o!{*_;nHm6PWQ}6HO!h3xI>aNobx20Xic57>58N1xNaOHn@t>4&?nKK>HF_^WgMG^Dr4)p*3p~K!rG<5;P<EXhbSd+wCCq"
    b"K73G~H6K2BH(`t}Mw4(Z%+b*z#+~p!PGi5%W~iHoU#`Y559l!*_X9FGQFpLOvw-bHHSe!59WO%XrE%cB1<+5&K_tfa(8BZ)NKG<-"
    b"_$3;KXe~d9r<bumnT-9#C=uO_{pfP;-"
    b"7YT2*ex#R!v`_f9=XZPKg~aUs3~~RhhZ@CdUUDvdZi>7k1F0b0L#Fiz#gzWhd@RAhZSm~7-"
    b"*9Cl=gIkAQ#=B3kvN^*{gn!+nIKQ21IU)v(!6H>(FrYV~u;o{>rKt5PuOz9zaPHs5y+ri{y&tKm#8E6Y#|&b6?PT0een@0i2YiH;"
    b"sDeCv{z-{}QU2YXs;Xguy6?+0CL8-TGH!v?+RL!8Km7d|qR(vD#`>&t{9bCJ{6oc@6K?mPcLV2cTc}qMHp>b;GFJY-"
    b"Q>;+OlqQ)u_8t&(__Lbyv(ez;%_WyDm;=m;@>L8WrC~mk+;==YXUhu4~h~qh9Wd5{UEZ+#mM@C>esi0bH+h2OPy%$zoD+!@f)#%J"
    b"bAs(OS3Ow_c+x2cHG=WDthHQ1uXNN=TjrbpgC5b89&3&437n(Ipg2r(-~KqFFdGC^pH-kA4IU2JiCd;n$c5@DZ?><j*oD`>=P?Jw"
    b"Myo->?46_F}-"
    b"<r0<jIoXF2&BIwKO*dHMo3hWjY?i&XIN^p&+gZMKH76fNWE{1+g*5yUS{&<%_=PJ^Yj&|vjMRYyajpN2z23OF2(;J7$9Bt2Nb$)-"
    b"rGeaPM^v8<;CrvO@=m5yVC0kppcr}g@^;z?0Gniee=oQoR8;qeP8buMmxQAC;tf<fL0f={r>XtJd?KG^8fUA8%M_v`h!Mf335-"
    b"eLptte;>A`rl+SgieH8b&3mRo2lKE7W2_DOx+i%0Mt0i>f_(RlW|UlK`X@o*ALHc1McCk^X>v^^)*bySuOaq(}ERGoy^$ypsP-"
    b"V?h5`(_u<RK}hV88zyyB8jRtHq~FuiT9k7ureK?(Bojz%k`;86l4!+CNe}PJYQ<}<lr3t^>x1SF>XDR<x@zfoKZ$nVc$z<A!Ke;<"
    b"k}e97I0c<iPg|8jqOqJoMUGTSn^(L&ICDCtDs0Ue5Ga-0$lp3Np-#D=pVDYLSKDHAZ;|lK(4*oJ@iy%FH-Gqbemkf7)z|UEzaIV*"
    b"P~k3J(Y?1#ItH(p>8RL^Z-"
    b"5&K=FB%CpR}@C_4;7~7YyBk%)3^+DY3x**h9|B(Gg#s%ovmJ&pEJ3<8e?k>uLZHM^XUbef{Fm6Sqqav(xx<H&W+r6pooC?%}A~`9"
    b"m(NmvRHzkGwnSuh>Nd7evax_QzA>Fc0Oxc86(!-DxtO^7Sds^DLgufcf~W4l~UehfVn+b(d-"
    b"2Nxf@pm%*Is*330~{|i+q>lLr~@BjYqk`iXe3zObpJWYaOIv$dn%z*e~?l3@>m-LTN`)&QV^82TXsF4}_pL0M4qSq+=L>B-"
    b"Nb{s@4n<;zon-m|D#Yj|tWz^?oi26l){-fd@k8^)V4b(ouck1x|aUpLHR=$Jr1)Jtw!Cq$kUvfKx|6EkOTCH}G-"
    b"XX*qWduL~g!g}lvxWuXpGPOL?I+>j>~o?WrZMVy*o`n9z!3i)>+~eP>|hK+5+<8DhikCb>Scc=WH7JCng4k_^@rB4^pid(v20Zs4"
    b"0}M2Geybggtd#C=E{vaSAG+{TI8ev8Lp%0P1GBL40zr1=X2y?=gCA~)sI1gS8#^03&}hj2$<kBrZbqx2ugWXizo!ao%XgzT#&ZIv"
    b"lu=hgV6JdQ-"
    b"*Uf2#`5Xo8JcU)b;yl<oXp=Z>S^){<(mgo5qY6(bG0~+n<~h4NSQnjgrPeph*r)OT+oZpY>ct%sE&;Qbp@T&{?2Uu!Oh)%MCz=r9"
    b"MJ{nD(gY;C)X&WhN>FlpA2{r#DG2@kfC|+>(L8B&dx1@wiXmz_SQc<=qi_4(}E-a>{lP!*z+#QFv=c-"
    b"VR*c<PIN^m_m{TUd2E1$Xo{aI}avGD5cq8eU0BueT;iWozFl%*dNT<H+Z>kv}y)?;4~hVRMWEe%3Em~EP2|m!9E(JNib23a>{xum"
    b"R+zx>2gpTpuRv4cfj7m-Bzm=?=_`|wt5M7scyiyB3Y*D)!^O;=OyZ^Q3htCwg9#*E|ujZ^mZDQvX0<6lPLD?)c1R#$dL#qe-"
    b"{WP&iX9A%tfaKTv*fujzAKy@RvcOZhRXo6cU9|L>|w5(oOvw24mPi_$krkQV@JkUu&qQu&M7SYAMU{odGrgAv***!ArkW&F^clDu"
    b"JN#c5N~+Zmyt*v|()kZAR1auvA8PYYSHJ%^k!m$*Z=Uj;D?J?UvWzLDOz)aAlNSqZ{&}s-UZZi38ruQ_W#O)+WVa*-"
    b"AMqfvMx4l<QS@tx+}hZ$!;n9KiiXcYH~cfJq1K9iNdv;Q0yuvQ%am6=|EjYd?yFCiF5GldhW84<I5yANN3=D0~b)7tHBj3K0<|CZ"
    b")xiErFu0PcA?ctLP`ZM!YSxzW1AEw>2djU6}1OiCBeV*}!_A)0MY*VT+PxO-tmq1VI2`U*q^R4JKbmz3FI_2rj&$U4ByHbLh)78f"
    b"Pl-%y|j*!84^m6wstL516;$5>-hc{-"
    b"tz4M9>x;jZ2MM?anm|I90hqn}CD3IdjynWqajyUNF{$Yeetk*()Yxtz7fVJMQZqL)(C^3O(m{&h;9=>IX>(LNh7wlmfU;0MQm$^&"
    b"0p2umCY&5RlSni}ax`{YVNKW~<A2kvbOOGFtUgI-"
    b"1l;lwC>`L{=gpT;~a>%JM{d@e_*6gKOeFbt8KyI~glHitj}qo3gWS^?BwpaeaTHv2Nz9^da=+Ss|<yFAZPKl_Wukynce@Z7ZgkN%"
    b"SZ0$#EAIs~5|M2!~%hK&OcVv@R_5_ZI7~az~veBu{_&u&X%i`ZI^Ug8c~M9$&t{amni!OIP=i{iMEdkmlyf(xvgvNsSIlX(8Og#_"
    b"dF$ei#kLiy?ZojDvYFR7MHvi#c7K8!1{%oz+D;S<(Hbvl?q<Q=S3u3@N4{v@R@ytQR)YLX3=~2_g?^sTD4$&Ag-$G-"
    b"lCwv_EZmmf>JL9Z(29UdlOyK#+V@6V0w-3K@d@7_Dcb{qyJRF&kihNOMI{fHPX($)5F6+zG{;F6_IamaS;6Kuno9M!A%-"
    b"siL;^eu~f0NRtI4qdnO?$8a;MD_~iieK`xgKYLwhs=*{crxpJapfW}_;2*(F5RMZN*+}_YBTIQ#)TukVlcC(`y%e#+*sH&6q_%6c"
    b"R>61(dkoG*<^nhie}Vz(+3vKNCA2+>2WR&NLo?^!k=d2lQ=nEb<4cfT=Cq&RHfx#A(hCUz_KhxuDsY;b#I4N!yjK@d^CHt)Qxz|5"
    b"x{}va;Xr=d)<q%H7*0ybsmd*r<<0|Hgt#Z0+&J+Z6HJ8BA}Bb4BSbr!GCF(8U&N|@qc<BDkDQ}alMX`z>ap~|qRlf$Ua9LtuQV?z"
    b"&JKzo<Ij~>R}R~zgWpXuENt3x92ioJ!u}Yzv#g>7#IicL*@nWzSiy7mU0g8IKILp}UOVnOS&(d*Un{xIH0W$;pC4<$yT7G>sVtou"
    b"0&Giu$gj$Ku*HA!t6A2btw-i;W9`;sGe$bLh5vC^DL;n1xs<AY;SfPw6&n{BGn~K{ONgM2rc6jekPsSl6K{yyv1}URgi-yPeM&5;"
    b"PguHS2c=TE;?>KA4F8kqEXxJyRrtqeGDDh&0W5`?Ge>2OJ4=l+lrSe>)3cntdIpR295%}d;9S(Cm6mAj<s}%eR=ng`66>}|=vuc~"
    b"uwowOXMT3`Vi_Wc6PAQ7zZxC<C$MUEy9n+|#UD^7_EA%{6e4o9hWpyrJ9HufGg12!4{rQhO6x-"
    b"=0A_Uifyf&)CqB(<SRQRTy)kE~m^)18Gq@Uu!NY%2`i>!HDN4Mb(KnJ~5(>-"
    b"r9@VT9|5K@6@g{&%`tqw@qvADJTjjE|k3PWuItv)HYiORSA@?AKUzQ`28=%d{R-"
    b";Ox!>vcP4~uaoblgWtvIOnRS*M1_TbEsw7K<Mxw3cRs9UBu?WgRW%w|%+2lF23yG5B&CgjYc{nvO36O6nwCA4!~2rhw-"
    b"Y?!I(f{l7)4;~-g#=OUKIk7NJye;cWmHpnf{K1psZJdap@2?czd`aOm6J%#F#wMO2g&nGR61~sUR*8oqW335XdM258M3&*{XrAN-"
    b"bHm$agkRvB4%DBUjIK;zgG@<WLxW^>bbrCNj?e7-`1yG+;QgAl+(fxE--R>Nw&Z>xDa0N8T#cO4?md*$B#9gDwixHFDprL8?48Bc"
    b"#r7#aC9{tKViq7?<Re1R2lHF}pe=DnEu$tEe!5{tpG5HePBd#C*6`|4cc9A^%GQTCST<RCk1D!CWUlY~YRlt6<@Mjj>hU}9IWR_B"
    b"k;<#6_^qsXKA{{eL=;gUR8anxjV0&!?Nd*>HCMRYShn1$H1%-U15MNPGZ{B6P_d%+-<L2hkVyA?x{A@MC$><U?YL2Ba?7-"
    b"RHGtD@*Uj}-8(!G{*{bqF#sPE$Apa7hmiId9}5cpqSso}kP<)l!K73Pb*5(V6}`B8~4-MX#xqq}Oxp=1lqr8*pQcx=rtW-AM&CG!"
    b"&9Zs}htk7#MK%nJiBPYusLQp+{)A{T2-"
    b"t4kK*+EwrggJqJr3g8%p5fEl{$m%H%t&(tiqIjB~9uVO60IL*eCN8%wE7S;+WGd<caJ~*AxHBosCVAm(ch2^Asxp#?GtFU&O(H*$"
    b"clOhnpqRTzOBYDBke|X-uaWn2fEozk%`bzPQyu%)w-`ExK_?U;Fr<8V-"
    b"c^WxyVx<$>Zh~nIZnkZy=ZsK0MUSQ*g=KckfM(`H(pTl-cBcQ>^>o_#EEtmiA*PY6SB(a!w2ZjJLz`cmRc+2Zvp(@@RwHk!v{ro*"
    b"&!eyzckeCQdCsHj=-b{HscV8`$>ULY}BXvM!k{QdG<Ush#~8{42}-"
    b"jIMe*VOj=66&|r+GMMnaS+71>m5d68C(3UyBZ$(dr6O`2?kBehwz{OHoJ!l7qF8FjV%XFRkf*f{ITeF$fXqv`#W8e%^Wid9Id*>I"
    b"-5+-"
    b"L|F;AW;4GbuaDrl|e8Xo>qzxW@YFd3`XwXsIk_|+4ZXN{mK;Jr=NQ+maQQSYCNDKngGy)#&X*%WpknCMCxY7+qbf*81z682^>0A}"
    b"P(vzcXa^#NJ8FTNLY6}xt5gz7;>0MT)5cQ*@9Qw}o*aPT|AODqz32#3DPsQro#C9Rw^*7)hYUgJV6-"
    b"ND@(9i=W>Rxx9VUe__FQeNkbCTflamzEuK8xncZ=8j0gF-j}#!XsLDZK&)j@Jy!V-"
    b"x~{YNQ+D~jf>08muN?KOZ)8R1q4CZf)ifK?9isR<k~R6+^(e}ITjbo<)wxbA~uSw8>FXd(BBM&5{&@B;uDGvTEX{AiG7wTo0AZ<z"
    b"L2?wh{1r%c;ZI_UL0YT`o8Gylq^i7m-"
    b"TBux+RqwM!cW{CCVHV?;I{myq)72hVCh~Ng5r%LsagIAYjkN{s6#RArDp+Z#nSCgT)wVNKd)AD-ZFK_(^a)G|L<}a^XqLnm`yUo("
    b">ncF#o<Er&+q`R!`+W^#4R95&AerdW0(yBRRBvsb|JFaa6doZ`Esc6MwQ!?ORrj9M|@2SGt3HwlsBf&z8BJ-SvqG6es2y>GJ#f1x"
    b"Rd|AYX3}jW9ueL1#bYZz>`aJ#9ZZZwmoiorj_E-"
    b"c#KRCM5=$hn|3duo+n0Dx#bBTnxhHg%ud7&CKXByA)KgXunkSwo79#U5gjdeRPV&O7&0&D5@GRa)7LTzaIk6@EKr@Pc+oV)5~T_`"
    b"@L*>m6NCnAZ4%_oE<sq8~3)>J2WYA<Ciqc3in$!Ln~|-"
    b"zHFbg1(kFj>DKa$44%aqMO)C2?eUW(PnGzaqO0Rn;naCzh%gRtX@ouR$fcn8#%t8!7)f{)oM%vAFXltK$ZesWOI3ewFTZ}yS=F&r"
    b"0<plJXP<ny!ca)U#5*6u;3gA44k&qv9@-"
    b"&kI#!y?=srquooM7^955yC;FMj$c8?w~*C2rT*FaI<1fQyVs7hBvR7}9*@X`01Jn%)q&`=jW5v!ptihA?!B7eK08loo^n}DZ^?nK"
    b"yLu^e0X{VjG~tJRFlNR**(RB0Rpak(hqHkl@rTn$BgUn)sd(hi2PC^IB)Q|P8d^g<-ZV9z8K?u10X1kA_Wy-"
    b"K?<Rf*{%FHK6X<!aY2E1W7)Lrw)}UssNLlq4=wuOsXh1o#cu9kFJq-!?~@WP2DD|NP?LU;~TZzllyV?QUnTW{<b}l-"
    b"sPbyy55khCeN7NEz_54NGFk^3tZC^P85Jj!L=pQcF5TcMbx4d%)Y0+aiUk4HN)BZPeLMU;I?%Bx|X**N-"
    b"oWGc2XL0M!5MU6;wtiZbM7CVg<nJ#5xncr0OT(IXs7Msgk=Kx)*~5UH`26|N;>Z8kHCSv6xETy&6*E_-wgZ`93VJmx9PX!d9<S6%"
    b"1kixu7j#<|*jUfSj-$7#iUhz>-NZOTP0fyocJyflSLKe(pnV`7g818c;9nk=Hr1O`|D@wvl+(yS)hlT$rO@Z#VS-G_}kf(?*5X-"
    b"lmw7<Xl=5O-CtN>U&*hL3OPTs`~(Hx*Geit!s<k>KXXLTkuT`|js8=rIf?hx~+w2--"
    b")xjC^hbqZ}x=5o22rj~B^&1Ot(_5uKw4S7Fefv*MDKoC^iINQ@=YmC)_w3(cajMvy6{@i57Hzod3=p<dNL>wYns@-"
    b"M62dzD^jDK@0qvy!nPN|)z2wNqY>xNvRr37t7%+O=Nxpip{lZDwRh+k}agrbq*fv@J*)Q}J@Nc?~%23?}@qWwMmDY%V>kw2=w6D&"
    b"i=m(@c%(%ztOHroP7(7se9h<fzH_uDy8bQa6_^&r;5XX;v|F!*qC=(O|h#(E6%az|kg=!WX+0(WYrjiD0CPyR-"
    b"4oVExs=J$<+ynX-6}I)G&jL?M)_Rdo5ilT|YH;Kp!E)~SuXnKw8k1AzXxz6+l-"
    b"I>!9F*>OLY9NJAa;r9;rU=nNf8sbLJx~}3KXH~UtdWYff%kF+Lv-"
    b"F;KB8kIUk2aDl1Kie1fRt_p1~H4*9`LQ1dlKn$Zfav878hYagko9THr}ta8kG_vn}X_VpsHqw5oe-cYdqE2N8U)@(8%v>7B#v}a-"
    b"vNA^c49@n{4^Z4-e%B6-QxIqzA9O7kBy|)h~E-"
    b">&#6=qvFDRX)BiZGbNK;L`HtWgj|Ip9HqEKIU^WNRPVTCJR^S*3{zQtgf|_2_HxT}FldYaRF<4m9dIegSp_NQFSy)0S$^-"
    b"`iK2XP7Bi-xQ4zn~sR1`%H8$?O?_iq@Wb*D53T?jHxHoeraQ|7{#ES*{zY{gIW(Mlw7n%2<Y-"
    b")d~o+Xl#haeSvA(yJj*{r=FRj<J;hSF9Ij4M8<2J!_no00)se(1%;svJ4$m6VC7Kxev+^J)=Y=im2@wTs`x0J8cE_r8*z`xp5KpQ"
    b"ckT<d7KriI4G}NWt=Iy`4puVmWUQ={;IG?@~^(P35o29s$C{UxB4n`QX2(vRX^n{u^u6?QmX|E&y_ighrS%+6nBcji)zyP7A8T4w"
    b"lJHIKL_tUlg^?kzEw)pNarw`if`1knvtu>MOJ;2}NjKD0tbWHkH;gPPHt~$>(}&o%oVS-udTQ;Bb;O(p8E@W5!BY=AUBijA>~L>_"
    b"Brd+gCCd{+CZhjIRgP<5>yk&KYG@Zvrncay$GO^eDrK@ZXwJq8NI1xW<2kZrK@_joCgXvk{7ybMaX0hYwW!!w2Ed{Slzi=NASd<A"
    b"njuMCEXkO{FtD!@>^{_%bUxUmj$fY7N%&u_PnpwPu;Pe`@u-5PwW3-"
    b"Sw_~c48C@^2Ac`+3YYHV*DZ8h=Z%~6r&Y05&CW?PVMl!eJ`~P%s@H)__G*QZNb|y>ne9Z_K)VNQ7zS7stM~GQ0<)T*Oq1Xbs$3~!"
    b"LRV!of?kRP(T*YH0!gcOOu?11lCTOQ|UG8_m2G1NZzTiq&c8c(zLvkz3wC?gd5y0FLR06YKE^`YbiFOp#TV8slLeJRnhZTBk~rD*"
    b"$f*709<fc4m3jsr<V${@(m+PNj}3-@$82>Ecy3a@r-y4`zsY+;ZqBER&X^>sG82st}7-"
    b"YU{uNUg#$QzaMCS8K>Ooyi5Hql<Ddae3sE2nCbLO|lVG}#DaFjRbF??PNzA2m!X4-"
    b"mavnax#V=}?#NV>!6^w}oye%hzl|2AQ(liJYw?ZTDpSC=?ozKlfqFqvS)H~7qW*P%X>Ywh^0K|e2yF2$_j9faEPO6bkO2e$LksQ<"
    b"}NZy?q^4^^<B`{Kh-r18{k{AUsu*Zff&Pa~9y@(LsdU$IK6z2(4yk=PsC=giaK%tWDp`Yf%-x7;ivji4O^&<<{t-"
    b"=)1w;rA22F}rJj;q{Sj(Hj&$`w~yAu$Cj$3#IFZWJ9fz-"
    b"!P$?Oo`KMtEnzU>*$9_X5m=n%1<AGv*<eP85%y<}BqUIxeXbO*X~!A%IiJW;kjMWV`7c<+~F4(~F7Np*xs<&{j_3lOvpYM|D}vbZ"
    b"IL^(q^xm@h49V-U-4vJz1a7!v&NL0b_UQglz|-;A)(kivp;F+*70tkEWu?T(mmor*S+?oYnHI{Kk9(3-"
    b"&^iURUVbe;F8<y!|thpgnyBG}9kaeiCOdCT>kIcOicNGU&%sj6{*i)SkK&LPp-jns$Qzw531b;Rvos`8g@J%5KU}b|6&)2U(8ndG"
    b"PZl!FUK4gm?}G;AZtr;6upffzS={M~{Uwb%R0hGRk+`3seKYc8}l=82vov4EhXY6D)!OCi77jT>E#quuAXaMLZ0!8<WI83391;O5"
    b">(CQSeb_PPO^F$L|2tvGh`XkV*<DP_>*fEt&L7V)Se}8waDgi*9F+%9dc0>=*EIoov;TpMRn<RM^Z$#?&{%oj#rJJ}MLEklTs(qf"
    b"enL{$fPXuvxM!@p*nC$-<LpXF8Qfh@zctlJsT({X9`qz}RAw@SpL<pvCs-"
    b"2V*Ozq7iKw>4BERa6o!bjyE>cVAjREY+BYUhfkVeZkw`^Zh}M}aV89L&u|ud<u#Y?EYt8YzlsyEKGL!}c-sIOR09V!-"
    b"QuF+23>6Pn<5*DQAMaT_A1T*Q^J}mnoSGjXpy}y<k1(770g6lsQ!gFxx=XK0s=;IG20@SN^Ta2#|h@Inv<inMU&>iL_TOis%<&;g"
    b"`?VIVHQ-2!ydE--=>3PB0$vWue=qsQK=rjf6l^F5jIwt!9=D26CTFalK=uGg5h6|0O@+lnV4~W^ij!(1Vm%?O-"
    b"FSJN~7XRww{O~Nt=AD50{D8kWIc<fP5bC5Kxq0>*F*MWVoD}lw4#wt4%qu9fm;<_>#rCSat-"
    b"ZQx{Uzk4HsphpAdi51U+6A*<+N9d)XJoA-iG!JtR38?$Ms7=n!1$)wRpf>LCdWrAw~CEje~KP&Hx)0F7^u~Es(X#zLTc^r&@gaKQ"
    b"3<&W)jba^fP>v{MQtz-"
    b"`3tzLG0+9UwJvuXVBOPuY>cs{n0r<GfNkC+eiW_1vcUM!AxbDg)KznD)6GsUiRp64{bb%oP_QRqP)Dg+T?G9JHaQX3`wwS<XM(%z"
    b"8kosNNJDw`Gqq+OytdO9~(SD(oy?IIHNq3?xw4d-O!4~d$ysvfu<qHHJebUwX?dk*cN_(Wf>W=>$XQxn{%Jfg-"
    b"$I+#K%M~$m5I@_Tr`7*>&&nSNZ&Mav!IN7Z=Bh<!FY9)(F@EaI9d|vuVGc+q|Q@HWNc@Nlz-fZ9?VNMChoaNILRjKO(2qm+DL(BG"
    b"mO_v37xgU<5URun=dk2(SD)ue|7USXL$<C(t;!dsxjomf3G>WH{Yw3b^=E)ql4EjtZLlBcEEqT}Ic6bhAuif!V?;p*MV{`8;@#ZM"
    b"azN((2+JzNdMqx5qrYQL`t%qBc;Bf2Fd>k`}&VD()@`S459rdSF{cGniTkYPdmJ!zERJ180JKuav4I`0p2}f%5DrJ)|g|AXS*pPE"
    b"CO3rR8<6fGlRw53qutX8EbTR<&FU8kg;bG5doY+MjHFzdj@JcX5IX@#6c{BwROgV|J);Z=4W`j-"
    b"RMvygkFng>0>Pmz5I1joFOz0bn1Fh$<bnGF2hFOauWG=7gf$hQ;TZvd;;*}>efZDn$&Yb_xQ8d69m^b=$_e(GOybkhidW&bX&g(P"
    b"P4h(ARE#*_03d)c@$&YXNh-ESNtZTCtf}~8cO!A`i7LsXw^^r0+tUVKaAb$7V;R!#)kO8-<S1RFHRh~fV&{j5-0(@|69S^1-"
    b"Gh!7=OJ=02u^m$HG^UN?fy&Ejm%qS!r;59GK%p=&t#C3CPjPQL&CHVh*t#>8a9{C2tin*tAlkaqW(x(&tkqk0)>7`5xCikAl+>>#"
    b"21ouZxtdBTD1DiU-uQWr$RnG6C4q-"
    b"%GXeNaOfeO3lpvFlU4)zgl&(=RMl6>d0>%@_4dVG15}It&M}>)hF2ecq+>o5JH&*bsceZ@7WX|r&a^9<Ux`B-Tza;msBDL-"
    b"n%O+5Ec|~!eh-nnToY=cy!sZuV*A+<WTCnbHYFwnIcq4*wbNt$#F6j^hAfB7-"
    b"(&A9T<Pdj6#!b7oS86Ox8qB)BSv}@&cIpxbZ3l6H2{i=7FvzcjFscw}%1YwfYS!xIOgHFdgny^Ac}euQe{ynqe16<J-"
    b"#JnH1)qCI$GhEw&QJJ?T*36FCz!&7GH|9YowaLZ`EXk3M2!qKDIAh$RdyP2(!Ih&t6A$a0Wa76O2NhU=99=(OU6MkE7faF>Cv8ZF"
    b"^r0D>3-L&MYoHI;f>_o;YQtW-r-K6Gk!XEA=H(XA1#qlJ`Sj<Tu{P-"
    b"5}e#|H~@)1)l~^366sT9z&z%))$6(;p!{Twx;6L)tid8dwQEYzZI@T!a~dX;(YI87<dHV1j}rOj#5--HMZ_<(ac}p<@-"
    b"p3R3JE+8SBrT#uE7x;T$PHS)>_E`W*!vF^sr*KuvktZqq@n&yDYo+xgTMbHdjzXUuod+s#V-"
    b"F?_{sD>*0;wH=K6MW=4$pRVkf{4r!S@X9gAVq+=>P%n;#=yd9)r+*B|283_sqWisedc>*m>mEro2$h)WSHKs4vrpnQZNGih=+@{F"
    b"1;zi{A9T=GzzbVAuui>Z>&g(zQj;GQ1v;KSH!vT>jj9!4g)6+!tK_`Pldqso^!X*tO=}2X8Fek++K$U`wlNl;wD2qdAvF+aM>a)l"
    b"miyR=DMYQA?(*dd9l0{#9uANM0LByk9IEcQWfSXx@>ZlAboGs=(_0j>_JxJkf7qA{$pqxMHiANeU?O$T_5!I!49BcUa>OJCG4d|F"
    b"~<u<M)>GH1ci^UUZ$25<WDLgG_qMSIa>%HR*npi(DSze`B?Gy9_K#Pyo5K0P1#ZfVwwKiYAG)T5pFY^K;;j_a%iIyb2E{avGW*NK"
    b"$rciPo6K$k}p&7m{aXg!2s#JFTmP#v~em@)!i>^weqQpA+Z_~W7a$3DXTNLF8ldWFdX|zN{5*4!igOlk?d6|k$Q_6;>gi>b<?t<M"
    b"K44VOSxL6<!hq^V<kdckboU4#WFv078^uw{h>NE^1ftd!w64ke?8c*~uLGt0<sVV+RJo3mF%*Sbb<?{{W5(a_W7(M)Y+4q5Z+^Gr"
    b"P=Q=D)fVnK7>Bn-WerhpGDTUkSli^-v7s6Ol&U>T4Y(>w0DW~%v_%*x$J(1?O^m<q19iTH%AG1%)6K}YP2Ungl<XC-"
    b";V3WS1m!>&CcaV5!Q4wh-)Vr|&%qiUMF=pwm<pgl(OVW)mDfBA(eOJyZJ7jB@+K^OrpX%_>Qs0sGB&$|S-"
    b"W%9^k&!IjUR~lksNKW>4dKl#v<_d_fhr|A=KH+p-"
    b"W4Kuq~7RtVfUS!=>3yCtmJt%7y~CRD$Pgs4Yns;kF}4<DEEws`!Qu^oKqli|H(w1AxV@XrOk?D<WXh~`m&AMdilPzu5jW2yRx%4*"
    b"E_RsI@RXtnsHs2`LIRDdN%C)Cn>2a3P(k@2)MP!W0MJy7fG&gCqZq?b{UnTynXXrY2}k;YD+Vv^2(k8n~3jxCuS#>aO8A$mt7!HD"
    b"QQ|4w~u?uC7g5B?xz{x>@dGyAbS&l;ye{F5X6E5>H&1&W)#8m+3aWJj|M;NLoay4WS%M!d^WP&o4S<aN1sa~qpq?E;YZXCQ?7inF"
    b"VI)%_Lk`L>%&ijs~%@+(DOoUdZ+$mU(0V`gv#Y6@X&go=d~Lb1$WX8QEDgduoHI3YI@QRL(J3XTzgWw4sCOUi^sE<FUHQ#s=?E?G"
    b"HdX_m=vF6%^s<D3+dfuWXMymx+;|5ba*<pINuZ#m_mM#^sBiLD+?7eIFxr@rEnKka?Jf2af+-"
    b"Rn5W1)^*Xo=B61)W+4eXq6}~H_r?W!sjCco>j4yLc<uF$1;{7q(Em6V?Bg!(%{`&zZkY~BxOdOxCAlb}c9Q%9HMKc&IW}!1rJQn|"
    b"R5m3lFhpS?Lw3FAt=cFV+Up6wzQ-"
    b"k#MlZlvqOTEoC6f=D_T!dgYsL11(bwC|h$weqdH~*^EmGk&aCWpt8#8r%T?`MOHjDNr*`K#RHJt4gmZTr(wOr^k3DW(kT*i&YN*<"
    b"pY}mZ%e%{Xv7GGYtg}RxWQo<#iu38I_5QrM!$MTd?;Iqx#L3+K)}OXh+@@3FR#XZf8c8t!!GBa^Bn%!~x36pnftDNr0=im|+r-"
    b"62l2mSWUF-"
    b"c<YG{Nhz)3I3SYO&{7=XCU2j1j&|Pk4v)Hr$4C1+XW7kAsg0K2V$O$PT*r}{<{U}+kI%c%GuWw`49Xyu|HM4{Ish<{6Xte$EVWYx"
    b"21_op|E5qlJaMc!KQ-mofy{4(&XXbJq9%5(ukF*fs0lee-"
    b"{(JP#rr3bB?I~<$C93TjS&(Vk+ip*m#{*4iF%2&f1dQGW8;R#v_EzhUvWL?3={q&n424`2!1L2-U)j(UiE*H_5QKRdY?<lWy~C-"
    b"8Zk2RWZG$W1qb&$YS8!DUrOuWnrnKi;$8KobGrLu=M;FDpANT=56)^Cjg#Gq#rrSK5UlB-Dw;g>XwF_-"
    b"*V8lhV(sVU>*W^D$<|9Pj9k4P5FujR3f6c{IIpU(+2UInmf-"
    b"Y6vEV7h$x48hm*6uoQAT9z&&|atqt0|j(c<lEoFh!P@LHnsl1!Rk!Up{wIVwwetYs}fdu2w;<6JZ1a;~E1i>~=UCaWdo-"
    b"k&a#o^(WYIk;%4FL5%$*kRz;W=`f?gMAl$7|IrX0_d41wN9DmXlV)A73(?eik8mON_bbB#+TXTb~!mZ<uP2=;hm_Y7DkCW4UGG0S"
    b"wGWEml;;bNJc91QOfz3O>a`633Fk7CNH!d7npWHuP<N@JyGwgq$Z^o6WzHAtt$!tt0%c^t}Rb;nMqn_Bfgg^CBG$~!OXPsQXqy&Z"
    b"|IMMYa;k$A1E1GGPgQ3U6AgUx|QcwOEMM<-"
    b"StncM!mj?e;Rdqd~COK(0$v(hTWs{)1RQ_>!Z&3yVI`WO2iSDVy?*`4uXhrM@zctx?i~6FgG`*+DPh0N1=xC9!zu1O0CTO$_*Y|#"
    b"ig~DOv+fc&XDtUnMeC`cBSTfhxRqhLfP1%|L)x{?XdVCQE}NLL00uq@s)=2-"
    b"xn1EarAc%Fv%@3MEQUZj_9;pOJ?J6&Ph`BWTWH2kH`^M9W_e6O0`R-"
    b">#eA}>3Z~8F7Z1$(xPU5cE|oA91j(P(@UQn_?)XH{wDPpvYd$M{ZrTDrb-ACe#4sYc8+>&nHkbBf?={n)8NG^%hpzFt1BusY{og4"
    b"ELQ;R$BkR*m1{V#0D!B%`JcvDLw|?IXH}*AMy<5zp){dKUNwgg?WrPY{kH|GyMa>5jk&if2-"
    b"6<a;HBB+U7(XQRHLJ_hq;xO3{d>eocP-"
    b"*KJzplkH(86!RK%TbV554_IIV)Pm@3=Qd3X5d9yQosOV!5PXa(6@w9eUPj5E)x*H)rUnu!M_gW}#8V_ED7K*Tuzfo^Ch$z)t8@2;"
    b"LV|P8{6o6Mkh5mNC^tag*e_IXyyV1zBY3_EYthL*szpESkeYL$yf7e<&nKo;?L@ZnD8*AdP_}*U0)ZJ)oQ`ttd$$wW?`ERS4*45J"
    b"Bk+v!Wj1t+?m{522_AGC&l7I)n#Z{^xv$48Tb`2{Y)Ud2w()uj6Na@l{?gZH&bGCq3ySVM>;R<JJ)AAI9V$XYlbAloF@c>lM(D3Q"
    b"52EbO;-uR0dzQ;HY!cpL?j&Q(7UH4DB_)PL8OxRhkzR{?^d{O5);Ik>0!5Gk!(y^b-!T<=toDyZ)esjfacUz8s-"
    b"ac?4$5pi6ILjaD^&4A$#{X0_CP!#5%3nCS)4x^EJKNoZgD;w$kRafEt=c7+P-"
    b"NN*<A3(ZEitq8_#croe+3TZs~3Dozo);zy`K6BZUGdM2^agB&X#o27M<V;|DOJ8owQXalW;g32TS^??{YsIqMr@DpZc!sr$3#~r<"
    b"31=66f8&pMMcb<npd5PrR|(LY}y@w|Y^2+7?0!_ZEr)Xh=$FZcoRNx!ySuL3dgP-AU=)B0}#DBRjS2dnM}Nql0j2H}Owv19`@Dyl"
    b"oZ+wpTVTT+LWks5kM^LZjKr1~%JqH0$NxOE?Rg&esKntv8s?!{0XlUD+0Y_p)tTD_pj^!GG5q;%_@!x4p(?otF43+I05#FWh6U`$"
    b"Vk9P2e5*EkpwgeJr4uh3`xH`tkn3JBOe|&}yxhFY=xTcikROJWfZQoj2ZY_mI!kla3Tf$A~J`7kk~kJx*{-"
    b"PiE0|P<^qzQ{VHhr!(ZjYL2#uchwj5c59v64t;8kd{<Xq7qUaVS@OHW>{IB;!H<TCeDjf)gdpOggFP_f$-"
    b"^&j(IFeh&YibGI2X@$MYZQ%A37Q=zeX5!Ovx@~N=kf+a9?*Yfb}912jj5B860trL5_b^Z$4Q~jIWwRx14QxZ#27j4*TLnxbEp`cY"
    b"o*2cIUKv>V4&#{q8<XAEo&VWbRa~O)xwUe-dIS`FG|^q0Zo#e9=_;8H&t5xw2_qWJwxx^+k~xV}9`N3!*dpWa5g>&^r|Vy{Xky5x"
    b"z$xdBazOaVzWpDMZID!==;_ZK?xv%S3b2`@>E%0CR(tY!w&tQFX&YswlWY+}P5Q&3LCH&u{s0WkKpG_W5~E%dk^A^s`ROw!^Z^=U"
    b"4jfqFi5<&mppNt+BPX-"
    b"|rJ;&m|7MMO}j7AxQ?Q2(GXSJaom7Gbm0f>$qJs#R(AW=~+gX<F8VzrYn<A%&^;Pk9FQ;MR+{;jn5l2(c{7N=P?KL^lw^5kcws)m"
    b"zIf^`=3a<{75<-AUbp|HuXnp)OIKj>dao)X4mwUMRi2f9=ScevjHb6tAuP=gZ&r^C)nR1z@ZDM>-"
    b"PinJPS>VF%FWaggDS7AB}Oa@+my77yZH&JX1?*dGV)_hC28iF~q-"
    b"52%EMVJLEx9OOw;H;|(w_EjRF1O+TeP@}Hs>Tk4Zp0ZGOdMYmb`E93bVg}Y@R6(tg~r9~EH)9TO-tUg&T9E!SZr5`KyyO=ty*|NT"
    b"8L?TsD`)pQ1O0<RlF@IJBX-"
    b"j=_&jg9nmj1=8X3(lF<D0b~j9y#fZzeFxV!TwiMmSnRq^w4daH31F#l=)f3{(u2%@65(R31_+S+;K0kt4WnUS<xNlb9!y?7AG*9K"
    b"tXC89)729;~%`RvXjOBc15GG4L7VF})Z^IghSkwv?GGeHofwkXG+J-"
    b"`)i9`(i}7l$1o8sAvHEJ`cR3#r&3E2Nbph6ky51pc@LHT5QOnDiC0MI-SFO{24!7cN&bR*W@>z_-"
    b"t7M7AJ^gqyQN)0(~fDsS&O_z)j6yD@ar}AOJV|u$Mj%Xa#U6D7&6lpZTA$H9iKZs;Nv${AeFl=q0eUproZFQ>n;Y>Ba=ch{o?ZmZ"
    b"xe?bkpNxPx_ByV6^a{v!^*Y>PYIW`Pry%3%51}V`pvFDQz@%B_fZf1KI-Sbe)YFWYDO$Wh26lVNWC$&(v>o{dQ+}L%vuaj=B4us{"
    b"vM|2HTDXeP@F`(O_>wkfA?&yTl=5HttlTBGf1zM%T$l?;`I74k)!P>w9%#zgZ(A`pVSb+tAcKH5%)dLSWUi?OL||J_f_~gHUva$V"
    b";VT)=|LM^B^48P?dweX2Pg?8-"
    b"$m0s{Hc;u!Gb&ad0i3W*>?y#gxGqE4`(qNsC5Q0geu;eZ)|(*~2dwn;Uy)!MLByCm{ZfLOy3N1#A}4Wv!sA=S1$$RF$glSvgbnJ$"
    b"V%1<5i6&X-4%O(-8~MgowI`1tE1~m!iB-"
    b"&sE4V^rC5$&blT;=2%&U(Y?4;^uF<Q%O3WD##<y$Atlr%E=DJ!_!^_x;N<i*H@J)+{`K&m0f~#i!YNW9gFCHu2R>#h;<q0~=)Qi4"
    b"v&LL+yK}a`!`3UoU^Uw9x_9=|nb)kZw#~}$YgL(wxqm#$Rwa@a(^{LtQdYuK!B}M2wqq|vhO*mkoga~!0>lhT%{N&8xWDt}eE;>P"
    b"`Rgu-3jlPAAWsNgrMw#r`J7$GQ``u7&R!sSsp1h{$3|vvm-<D8S%K(iW5PfYz=qe<=;7C^7_XSvlX-LyMJ@aGJM*b!@zQeQ(V4@T"
    b"IP-"
    b";Eyq(A(RCAcMe<$CC^C>_nOvF>r8bZN0%D{=2gV|&Wj(y$P(S6m!3FsT{GW}3ZafLO?e;DwHM*?Dr5+);qVooafJPMqT#RxMbP(l"
    b"O*nd8X47558X3%jV_Z|ul>qQ18cKQ#6_A_)%2RhM&3#s9myQ!tN<^EIHaGvsn7;@}cv*!t<>1vBx7?L>wP++@ERW;8X>T9hLU_`Z"
    b")YS$i}R7xtL4e4rDU+=Kew-"
    b"tP)*jfEnY${vpU7}nc-*ZWPjcVgRo(02s&0*ajwZ{zuWMyKymn1%8pqOy%<v*wsB+{*$<(8BpdB(Z$otQD-"
    b"nHL(g;vE$~ya2h=e4vn?7U``4u<BI7hb>co|Dq-xfq=*>AXmsFnFPQuaddPr0wmXk4)VWA+)3MCm?o*cewU5+m`yQ;p{du!Ul6iV"
    b"jRnj1BZv_9r99`Z{_9D#SRixj+zw5~oa)xC8an#3lP7_U(%<_kUT^U=MqaX4;?BM_D-iRz#h{O_r>NapTAU~350_1C>yO*iANA>n"
    b"ZJ+eU8+x0!KWJw`7^8YJFMw-!QCaRpFq?#N;_GuwQh}$pa6JKUU3XuxP>=IZb<T3+H7lc-"
    b"6kv_odM0DYbgh7aL(SlP9sKf+;cQ%KcxAyyP6>^qoDg@N%0p+;V^$%x3Fl4V#pgqCmTy4m@b)QJNC<!Drz=}`4cy-"
    b"?imaR6?W$&U)_zOMd<1am55}^zj2EZf3A{3iUyGV@xEdW>|rnWCcOEU~KaJcknz0KN^j>ne>5<mwouTTRLbSQz7s6Wa8W+8w8*c1"
    b"?e9?C9H(Is|nLjecZM-T%qI*Tv=7!{nZeZz!@F`+!>;F706w~W$5GgK4MEDZWs4+J8W2T@olQhCcvm!64-"
    b"c#8OpJ^+^60>8+)Nn8~Pz^Es^diZ5Lcja3rIa!l=YkH4TG5qyaa2(v1Fy}(05$5YcNkjcy5{)ay1j<=|1S6e|YF@M7TfjtEYDiaN"
    b"BYLkvU+b%_Y<I9}MjZ~45mPn8B8-"
    b"Y!+~+I~M&T!^NHLdE%{Jodsq*aorq;nlLGyu;6|{1x?)?9sX2x*JPxCN3T=P|vZ@p5{D+%%Yr?YY~7iYwCH(rU7)K4dqASxHjzq{"
    b"t;Ox>&w0#x&kuV7}1b&34(XP9Jael`2LUEtO5@Jo`wZFze`-"
    b"A2SVR)isd#9fU`xF!9>gzA`m@q6=wE4)vnMWL3fc!9e!M4ypdElV0az?i&gg~A1&=9y5qY;sgYHMk?8{Y&0bUKJ`<hp-CagMn5Oi"
    b"6yS|s54e9^~6jZRh-N#)wU>?qxanWsd}(#X1(vNJA!fAf!Y~|-"
    b"6iY``=FU#cKL2>7umdCOYiPK?9Tr2;g>66F9ZBmSetlfv*0%L$1`^3A*&Vgv;KID&rsmSsGlWyY3GGHxzBEDFXdJ;B(ZaT-"
    b"r0HEJ3l+@0ad^-qD-j&V<tx1$;@HcCQ->WA!`8J(!b<bL7%{9x#!>*|B<oF%B$(JC-"
    b"Q!d{m&rvmohwu9*bSk*$Telv`9I2#i6%k(Lu+`oOZzP&d|2U0f5?TtW~$edG$;rwkGiaZ;OC#OJv^o7?P`Q{O~K(p~rGZKGNXMaL"
    b"5mBUQdybkfs(}PP})MF{WbWv}-TuX&EeF3`Z3g@s-Gay$L?SwRRg${IR^-"
    b"fGhW2G@6ZOlTEQ?h<yWCEF6vlei=Z_o&AOvJRsB`!ZZihWUC!w*gJEuR%*79$-"
    b"`uGzKavhdWC*KPq~0BRjhb>AVes?0DT{<r*hJiCfQrsD~$t$q||AYRlkbp`LPH_wwNtr#Hx5XM})+SHm~G!K2MuW6@F8V1rwpq<|"
    b"amAe<-Juj-ygzIl1?ou?QFNVts)rZDDM!dxlNQjucCdJ=P_Dd{NLmP1n)%CX(lg340HC7O4pPvQuTnK?4?T2TC)6W>uu6$ki!Z4W"
    b"K<LH|L1VLSjNTF+FGO5KwyrAt{HRzTvN2DE9v13(-"
    b"b%Y1gY)yotEOxVMUYsi}P7z_#zR$Y#2+i{!;F%qgo_=u1i&sLL^`9chyHD)<t7Je~QMfzD@IQ5R6_B%a>FBBn7KkOtRw<(8<t-"
    b"d%^vXK0=F;~`+#c!>O4JdsKM?S{fTp}j|=MAH~37OHGJhgHE|NfVsdU8{qRSj;we0PUD-"
    b"Bwma=I6XeJ8tv56I0I-j?UOMabs0RgRee`f-?hise|Zcz37o(c>dw$ZCh&fybw-"
    b"Ilzjch<6<zJQru(*gdek}4TZxUNqm~=fF3zJ!@G8C$f>ELhN@vKJpl1+4&N`6!avVLY-VyCo=k&$MA-kD<#SY`3{7)roUTHsN`;|"
    b"Lv5Jn|^>T0A+#uk<2*7>Tov9L5(z>7O}!x5BOkz~`Y+W?B`1&=$RWhMDb#rq30rADJNKQ;qUmt6~DLhaLp79ag_C>0ZUfO~^0ANr"
    b"C)fzGIAiK~_H0*D>RBfpNs^BJh1oX-QGk*`7a7)s|Z!F$X#i*V$b2Q0~@n}6C8)>rw=n?6z0H)R=5?WPl1HK7mT?VW`4+;ps?DNM"
    b"R2UXRkROUj=ry86~@Ap&G(q9txv#4*SmnkvVl+}x9qzrkvPoW7W<>ouj6VbK;vX@RVcv;;Ghh%Z;;WoOD(>v}Jiy_v4RX<3q_dMx"
    b"KnMRVZH+k=viQLrx<lCik^^eNR)vsUUC{{wCj;A_%-F<+yTjbG)AXadpLdt^c^$SFiJmg7)u>8lov0A0i<Kw-"
    b"V$`=xlq9#w~!O)Efw{x%55WVDGE^gIHpzJcOj(xb<bzo0WHV(w5^Zgu4MbzOYq0jmc8JM?4nrDQux>`fL)!rodTGeM-"
    b"*vbus^E@f_H3#taNw$fer)@yKlfL4yby&?#>@|i1;<T#<5J0i|hAxj20oQ(4QpuabYeo2BF9FYc{bV?zRx0Cp?BfjJb?m4_;H@*!"
    b"Pmvdd6Uh&8VEOK82XdF*`^j}4b2Qrptf;c`?m;Sz(D#1aB3Fo(N9XL7w;-"
    b"vAjt_v>;&T^?1n^bc1aFCFn{CKb!qvwEPI90K!Bfj#Jp7aDQX&Pt-"
    b"Y0c(_ox18J_mk9|J3B0Ex*L@`D$86*K&z>4X7gvc(^3^X6Nb7U;VYg1d!#~uf4JdnA{h|_so#Q@Ap_+F=?En^-"
    b";QfD!WN!6Cw{Zcfen?%=Vs1JY7(<~a+nDc`(H!V+I03A3E6sWO}#ZMN*7W1&jr6c(&O}k^!oK`{pl-"
    b"2WWSnX$`|OQ+NI$_cC|oi_d^ih1pE$P<X;813)Fp~w-nUAp>t;~GnvH!DTR?GyJq{A^vkPw*VD-"
    b"?4kvtKNu35nXcS&oU(#U~F5fof!sy|bIE=3Fg(Sy@E`iuH0fDRfh;s|axMDO@#{nG8@FOOZyqbUK3G+i7czv3c$gtx_*d_}M49mX"
    b"puY}Ve1!c!{t&o=IhNwI~VxE`|i5P178!<O$Ijo!k1|F41a#2Q%fOjsk_*XKg3k^oJX^Y6%NY;_lVkZy(x}<l1GI%ZXxvF_fhB-"
    b">`9aUBw0+IYmT3#~^ql_|6FCgt|nc$m)W9G1xQvlg9#C|Oj@eG2pLdh)?4<Gy%%`ZP+@wta9AZyr`u^8lN=#4}9Lz#k?3(vUGv{k"
    b"#+!dq_ru%V2#r|D27qn>2ToR1Zxr72XltV|gCU9**{m-J#*csUA{waryV8?eP7H;dpZWYrgI(ET~;K2VXq^{6Vo@-"
    b"@xf8YkxD7SgpF_rA-bY)EcZ?Tv6Ui#a&HJd<<bG5lGAJ5R)$$8pBMm(2PqPDpGSTDgJ)f6|YYtOLN7+o?bsH`hLwgK57R%gT;`vb"
    b"2|89AMaE$;oBs#fLF7Jq%297Z9@m{crkc$bnme?rxfz$5VR=Q<KIGblhjF7#SFVMoQs_%n0P^OwMN*l7N<gg@`&c_$H2O5k~LoUK"
    b"m~CD>y?CC9WwY9r7N*9Aqb-UC~4^7*gtf5KiDCizo*l_j8K3U4junmq4xq^tlG!;|8N3(P6(s@vQ1~n#G8`&mMlcia1IQy}tYYVl"
    b"G|?<%>=R$)&Vk`t!|W|I&WHM%fHdZNqoDFsb9if|9RR?h=KqC;lrG8Z}n=5T8^qT-yo-ITlAA3&#P+aE1p(>S6#uhiUer1*&07Mm"
    b"sut(zl`@_4Vw1yS%l2cvT0MJBEs7X?Ue(z11!kUIV)|L{p-"
    b"2WfK+H<FUY8^v}d>d9KKrf*mZQ!ewxXRT#n!lu@BF1^Xp76O4Sm?+XRZ^<4OOvhO+b2q=T3d;+>rA=}D0t1mx{3I}uz0Mk7L0i${"
    b"vgupjbav${94Y5Tc^#dxyPeL8>fB?4o268Hep$|-qp`IY1!C@^lYi4Xn!S;-"
    b"V1;HpCmT;6pLdm`|+mI(km(4<f2hRSp{K9w=1pvLXw%W@}VzNdw{|KW-"
    b"F^rG**iyjfzQsY!eN3k`3}_Ls8MhS9s$ooFXU(gxFPjM*6u{#Nv`3^Ww7cF)(_5)~E34j0+pE`&`V@deh=<JLu4#}ZTr41&L|%8s"
    b"6g4$laDq($rHQ<RTcW31|7uLXnmxoW^DiMd2TT#w#(2SPR%2;FE=s;&njEl5Ae}zBk3s>cwh&ZsD?d(S%uxa}Jvi>{7VYbxSlOsF"
    b"3a9Um3iuz7!V?$~^^*#>15a+~15r*7g-kS>0)Qy%C3!DHA2Q1+^uUjm9{Ol-iYTc~prV{`)`gW?Dn5Ol6*4%klsdR(iV2f8`J`eA"
    b"G>Ph|<{feP<;1&Qz_l3_%s4B4RE^@St>`uAgeZZ0svXZKs*DQ4n;OHd@%Es@m+p{By_jxk-qH#Ox@re8b#zj|LnM>85`n9D$rL?("
    b"Q6DDGRJNfW?Ts*O)jV2Rl`vWq`F%7Y7xG=JY3t!+0<WP0rTC!2FRK3vJ9cY4Dc0w8%HZ01LqFiI)=i57Kpk!A39p?IgGhRzD?GM<"
    b"!qGZ5=_=h7!44@30Wkb)5cEUo?6HrHVoV!aBO*%741r8pOOf$H%uH!+Lvkpm$A?uF!Y+`ZKy(V7GsYHML+*A%J|AQ;Wc}}u9!5|3"
    b"An7DW$gXZ72_zBy!u*)nUCVgxEhZc<RNx#3aG0ij;j}lT#o+Y#5Z4GD1p3GF!qc%=c$tTh2!;lNfvmL_eTc&#k4w+OLx-"
    b"z8Z4o=oI~oXX6z~8>{^ct6)*7|O`ntH|fXTBKQJ^%e>+5^f7kg{#>(K3*m}iF+@TgxO8sV+N2PRAj;I&Rz7*n8ECO+&tgW7sQ9+k"
    b"2#u#cUWId*u8R`L4Ah=PT<P}PB!AvA@@;}r@8Ld#9*N|fmR(8K^TE`y)ggEVlF=qhU(D4-"
    b"lRL;w^pup9FtQ_i81a@WFOA2Crt62@#c5c=B%MHgt1k_cm1JpogjwK^PWNCKU9!8sY!P-"
    b"d=%d7Z%=U}7Tcg0=&25H25n9g};A$;rXsd&-+$_s~Np5?p|EZp8(QGfz}?Xi#8er<4{5RX<4lF-AEMiXy6|wxZ_Ipa`>fWGr3`u7"
    b"s#l5VryDjfN<Z!a{*yJ_b_=Gz5v};Xjc=(A(LB+LD3+MWS1?;KUYnP&Kq?7qdt>Az)-=3~Nyg-"
    b"8s65(%FBDY!5mm7X+MTvZX?yYDj?ab!R&J9EX=z^Xi*0Vy_5dIkvZVI6!YW31c6w^yz4R1E7K?s-"
    b"k4_cBYfb6bMdGg}o84l0&_d)9%?BrAG74k3D{Yyo!dM8)SuKs02%9NJ9hy088urb^00Azt?I~neKLukIwgx-gTkib?30_9skfhh0"
    b"h1wAG!xnczANqJ;%Zyy9Wo}?(q?RK70o!%G>_QJA|q1|Mkc_+j;Zu{JeWq@lFmpKXp&BY_D^$bL^dT-"
    b"W@=TACC8TV7OC&6_oza{1%$*caPw=)@lRF0~B%lY$2ey8lcGa)t8Ot%XYI+=qymTOpeAf{9?!)qzLF!>_n=ER<{gt7_V8IUMc8~D"
    b"i!Z=k-)FCJqI8ob8Ic5*E%vy55JCx>;WYyR9$>iD$Y=xzK{bz?)Jn{q@IOX-KPwH5gwI@E?SdisyMk2^LC+H>Ygw-Ccdf=n+;>D;"
    b"uJwBkCGAM$6}Jw2ONqilR6VfgisZ6JH1T3&kKd07YXvmz!)aUg4o`w9wg3$kX<xsSwgnNolOaotQTd^q!cx)%!~r3x~XN~QI-"
    b";ud6c!0EG?2vLxsYM>g<*jP$iL79C40jp)>kI^Q;-"
    b"|By>rzT{Fa_1jQ%B@detzfyki$Y$Qo9azdPuov*3XE9G}Eml__z6|YBL4o=76Tr+AVTdeCfDh_Swe^uR&9dcvV({;B0Mf61cYDGF"
    b"cDILB{gLG%?`Mq0<w6-"
    b"Ay@m9VTNe!cgo!_F!!4;mNMM9b4&F6j`4psJ!mxg$otFXyu8F!`jM%b%E3IM$v6BzVGBhjEZE@Q;sPqV{BvR(J;Yfn_az;0;jm)7"
    b"&uFR+P)&N$)9Dv6}7O2K#6;cyxIUcmn<4iOF>GP^Q;ht!k^F`U`yt5CRjMy8&vQjh{T=`JX8p02rsaJ)t;bR3BJ)jr)aEJ^H6XEW"
    b"e4Wnclak_?>d>1>pc{a6o9!sQ$LDAXZZx(JaB0=8@!>L|8XU5;VE&&UYv;25>z^G%jb8lI=`f9Gh&`|}I+bz#PF#f)yO?xE%@o~P"
    b"r(_RfyL5@yZ4PCec5gWaF7?>d$3dfvK*bZ6at`nl_Q-"
    b"8Cc<{BQpV`)d>^J|4Pnd(Ay>rOUl_yca9o=3eC|D#n?#fsGU60pCf<Lpq`uX1Jq`w|~SxuY-"
    b"V7_x7YZar>ytvG`Qj_Po{(_Q&)2>*0wY4g~}g@effrnao+vI+D*25w{lwm*{Z-"
    b"GKOHv`r%y4n>&6Sf3EJ0eUNr`eY$mF=dbBJQiW}(yAGluo}ux>zhE=r<|EOIn&LU&UkPgf=!K6UfZtH^F(bH7sbscUW*_=8+)wHz"
    b"B)&7n7J3g9{gI%VluXA&&QU;gm3h!sP0Qgy(~<)JVgj9j$OBaiPo;n`)l;De0Wmj@=bHX2Rp}73446a1X;JY;IDH|j?0JDCK}h2#"
    b"_ye5hh13|qeL<QXTqQ<0C<paQA$9(y5%*sne@9><x57ZY4+aN?cv+bM?h3P?pwHU`{oVi`WH7^FZ)mQ4)E@Fn0y5JbPUB1@g-"
    b"g@e!GYzcs*F2{jzIOr%3iZu_?fRTqZp3><uGa&ekAn{y>O$Fi!nMQ5u?Vmt-"
    b"}DAS4wZkN_ZK4Ah`C#vjPngg9;Xa8zvM>NFcps5k{C*uE(5pi}kFCs1ggAldO_hSg>?qD*u;IWh9nYH1xxo=$b9*@HigpBfNf?Ai"
    b"TO8teF_gpfEDKG&W?qK%~@s0|}K3S~bbBir^27FlL=fL{f}kev5V1>+*I|mLxu61)s!0x^fs<n6qK0laQx!{qV0S;t16%%6){&$I"
    b"hW<ctVB7<l$GkfTVH2%+JXVuUJ<co#-"
    b"0xExzVJs0cp#5$0zL0Zgpa*$((}yTYszN};|Tpd@4DG=S}V_yxoi;UyGSM505#k2fSxEY{Ttr4{>(;n_(zCQimBFD4_9TD{jnKlT"
    b"?e<B5-2BG$E?3HDzk4`E42aNdPS3C0;fEt*ED=i4SfjcIz5ZPr#s_cSr-I<--"
    b"$19=B>`x3XTkov<3V4B@z9rd_3z>mT%TD$R<O}x(8&i=kN14_wEsf&Q5hG7qg+5lhetTkXp|5i9!jK>D2Y_`6I6KFSivA4%W+udX"
    b"|vKvquCd!xgnpjEFqZ@6;Q;Zgw_kw>e{4p;R2*tg}tf#P77L-"
    b"UJ*i#B`Cu7zCVcMf7MS~k9#R*$0d8uW***I%w!l^4Fxa=@hR7{e;c8y8bx&kY^ly{=xmzW9jVLX%`ek`!EqgUbQ#pvM|4#V`vvn#"
    b"-3fq8qRRzs~U)dV3K=r&nxr9+({QLLkxEC`^IKvDh=Kbf;rSsGb|o`8W+1WKYsitEA>?w=$)VXEUdZoKyg7e!XR5CMEi+!%`=iBi"
    b"mjfhN`<%OUCaOQP1wDU|$0)q$D$L|Sea9LLJ0sMN#5koW1{m0+I;jV3Jbj17)~^2I~Ik@7`aF%wPmf;>6#3BuZhiZz{qj@ej4Z!6"
    b"&KsmmA0LTk(ov`o1I<QMqPc=&&ix=EK6Wq|Ob>nh&A39**dl)O_$r!@DUyf>>>exBGec(H|wETWq7hyj*LpGu9S$(+@f)=h`X^66"
    b"E^OP%()J3)mB?kSUW&FP0M03t+K6K)EW77XKnmHxgTT;U^nWXE};-"
    b"Z0e}Vt1%RH#Ap#HfuoD0Zn*k`L6GeG3RGg*qH+5!(XKOh)%We2oJB!EYni!b`xCkbxqLKB^lI5b`y`T$+74q37{L(Ll=!?c$+C*9"
    b"7u8&(;<{tn%Yyfxq0{(`x9k&jarUMjuj%o@XNJwq$2~;3*2@fy35Z_#QHiGIt5$KQs-+p12bJ!C#VTUvJgn?Yk#1+4r82?-"
    b"%n+ihR|}XGmP{|9Q0QlQNHl4l3$F9RqqbR67PHC$27E)XCdPQ;Ou-1hj`D*iQlEs-"
    b"}QQN)3aT{HC>qCXNB55FG95jG6*nVq%pCaz=tAR967uv9L<E+FdN?SlP2o`g0ZbT(*41;+%5ISmrqxTS3)8aZs;x-"
    b"{M78omlacDji|p%B~7W<5!5MX-"
    b"p%FnMh2cNw914Eb0=D>QUT7r5k|cm6w#VHUY1Nl>nm^|1c4^YsgrOazaK}eJg~Z=?ID{9S!Oi8gIP3WvS9*%&S;h;Yx4NvUxVv_Z"
    b"sI&Bto*@HX#SUkLdyY#P)kA$x7K1bHxheDP5}rj95kGU%znVR<L!w{Mhx9xBqzo`7Xb)Va2H`>lC#ek8KCkcpgtm%d#w)9nTwb)l"
    b"R=pfZ*@a#@6abE8TB;4(nW#D<(OXTR+rNe%D0jUOQk?cbwb8DAr#XtC<bQCjG@&Tx}Cw9zRIT@t53l_1FtMZlqnF2IkATKQ3bO|_"
    b"z`Ws2L=1CxNu-nU?Wm#KX0CE%jek#3XcYNm|PBdqj{Qy(1twjdBiCW#2MRFBw0}Ck@Ql~>7FEqc89QGqwtaff?OMLpC&n>JIDx2D"
    b"E`$qlYXjmpk*foHj?TXxk@f!uv<OAD;zNwU`8txk5Ca&{2$ZXA7^^IOPRd-"
    b"#b&+v_j~=P2LI$X&D}X!CXvy{U3iZ^+E#KUhY`<6Vk9T3a8eril*a^>N2q303Grf*Ai01ABdJ7tjuFqEYav%LEgh>VpRBEOP#1vm"
    b"&!K2mLCrxHzSEdT82Zj;1m9aCz=cqs7*6M`X;pK+B~MXQ#<2!ZcMultO<l|wU^=vuV+t!Ly<zGFpJER6mAYUhESaGSPnf1&Q$d2q"
    b"K}Ezm1&+dVa{LwwDI*wyEOzzqFMy}vmVi<Gw+rF&MUPO*As3U8;0=L<qAPx(i1r}e`>9BiDx%HG{F%&qW9ltTDE?Pu%SGSObgdQ1"
    b"TTY-"
    b"p+0_n%_!=)HQgvWtt(=uQ!hOMj@I3(~<mj(7#oK5l`_5`C9Y!M$q~nP&Dk3(^=uFX^6qeW+WNFw4TNBDxsLJxVURmF0(q*(>*;q?"
    b";pV)z_gwu#@(9VHAqlU=88Vg?~Vy{?lMt3XYe1ZJ<E6NL2_H&tHi_o$m5GEKNj&4JV*V<rk;8YZkLWqem4AKLRb4@Zd&}N|$n&X;"
    b"KoRJ|0M!Ie<lYmO1nH}CFV_*TlwBY9jpaNNPP#yF0VgwMP?De7WGA&3JGu<^*iz7No*Z}cndtIv3*Fd7;bq&p8Md|WI+CuUNh290"
    b"Cp2$Z<Ngt3NLuHd&rdBsXQ=WN5|3~5eUtZyE>UaC(%N)#A+}wOR5q<(c@Do&ITpH7Dp@?09>C{9!>OgcTBZ_b)V4EPIGV7gCoDs>"
    b"zuR*G#lThH$f2Izebld={;Qb>QP6?kEnzWIp&o7810~HYJKZ5ANCqld`A(IXew>+5+7vmr`EXhy^{pF1(nw9|7I}^{|f#4HvAleR"
    b"Z0uiPZc*>#KP*meJ!ii##Y0+Jh5$}aR;!kJN--ONdDimP}-"
    b"&N3~e$rPUQiU@RF#T~oWgTVT9FF<lMoS|)4Od9%qtPR|XNqc}T|p92MOv9&-"
    b"jcC^x=1wX(k0e^oK6aFPy;=a939HZ+W}k_BWW7tjg{`Q?2;~B$%!d3jT3Z@kb@6`kSRi{ttER39F}WJE;B+e_qZa0%xC~}iMkFyG"
    b"VYgxw9%3piU~2gYXiYY%wDMH7*R0NynQ3jSZ`9$2)U)#7nuq~(oHQ;<mnFN-GtMdL_#AX4QjAEhDD9MkAzW%^q4xTkol@WRJHo@q"
    b"<c;u&K`b&%CJWx@(INqk<Rv}35_El*#IM=a)ZL*LcG+3*(G4VkT}KOj|OsF2b%A*OwtFR4yM!V#Z1`U94RYUjY5k~&jDHrC%~$b+"
    b"f@3jC3<Hkntcu13YED^!=~FOuq$BN0OK)qClFk=u&(IN%TVhkB=bL9*%Xq3xvuBJ`+gr^o6QIdhe)URIO4rvGXD3_%+`sS`V3PKR"
    b"$-"
    b"^`s(h6*Nu~?Dj?j4=x=N3BY6*kQO%H(NNNG|g^DZ5s7eeJn^$4ql+Gi+ZwvsQfDj`G6?h(kq#vJJZ{PmP`@MQg@WlSsO)m2nCFOw"
    b"5dj?@ufUNsXWPJ+5J#ut<fgPV?veJuod9P~uVADW~kLqY<1cH!7)F(td9W)My|@MszjBN_W+*rzhroiJP{ETvRgN~xw79Em>~F&6"
    b"@lX6DJ5s`T{EUudUtW@O1tPQWlqWypwpbGAil0<v`C6~e&715K$5e31l9WGO%ms2M1r2T_TH&HUCa$KZt%W5_-"
    b"DB91IAc04A*HVq1@DidXf_Ig6gNAm><2$g)|(#?s+l2i%#)T>|-OYS>To`6Xv-"
    b"++J9Q*hReahNuypRv^$)zMxjGsqYPWlAE&$~M`@e;b>g>&=R%=mhl_1?b6&Rz2t89YZCk7v#P-"
    b"WIQnOM5Uq8<{1h^qup;*CYtm9jf%z0GYz?U>&&#`&w9PVrGm6nd#?8yTrmULH0HUlE@ZQF<sU0E`y?;UmB5RE?o!4U9rf<aldY7r"
    b"=FdV=Tg=J#m_M0O@!7iFqSZmJuD4itWG18H6STp_r!1rBQW={Q{npEFL-8MeCC7S~-"
    b"HVLP!n9qW0y+==<?PXLz9aKxXJb@!MZMf*hpJIdNWn@vu?@B6u7+|?9Y>5BWg}{q^x{IJ3@T;EE<fv>K8v`x;76M7eA%4i9b6>G1"
    b"&(KsoM$}r@+4D6G5^&T=l7;ikBBSPE?)BbUf!cHzvs1JCI5K%HNF*j7%7aHb#uCaz=7e!sJk|A`D<uO<A4K*bU=EDrmIJJNu~YP9"
    b"!2EeiBJ^t@*7D;)s@T0wWcNMjrJ!?la;%A<J_xw+yv*GbJ$WnL-FyqllX*anQQbj{wQrkLBK_zNP(dzvT=@@Cbywrlt*YPMv=M3d"
    b"X$7d50A_|hB7n!Z$5V8hhK)2Dg`kIKqE3{5Csu9#L`%r!Pm8WX)=2f?H)k{#u(NV=bt%=E*y{}ooYB)jEHwvDM3XtxZ3Y`$7FL)n"
    b";PN_t)WDG@Z%ooVqD8q@}*RoUuR`&UB8{$eqFuMb8+gmJ60Jf4JE#oH4<h$^#)WJ$do0n{)Q@zjh1^RNaM$(e{&>M|GJ)&{PVuT9"
    b"r@^Ow^CCUFt!J<CN+8D?e`mQLm^3hDa-d9V_VU6&*j<QoD}WLZF0`;9CkXV?DJ&XopY4u+w+{=JlDqO?8I&Ndu-"
    b"89vIXX>{h9W`;`5#(bRw<ur2u&WRZJaKx%_2h)HP2Px#JBbVo6hhFfd{W8>voN$DvyWTpj9`PzrDmWKb9n$VyMgVO~Q^DH#X&;-"
    b"g?BSC?oJiYaKE$iDPe_M|E0rREX9`g&I{GI1MIr!Tp!g!Ei|OVdczK51xQqPqulgj;}8veb&kD^-7_i#-"
    b"rcz2nWVhd|rvfil}A#QDPK)13PMi0i9m*;O97uO91emohjBz4uTV(uT&H>gh}BifJQL5Zf5-"
    b"E|KTZ(+6iXJ`}BP1^^PjAkP;j;j%j=Cl$^7k_M`pk9<1VmkfwFjg5E*lv6&S7vFcOOI4b@s9N#Pv=?w?#FpKquvI(LnLYdp^h0Gk"
    b")^a~;HV?bMG(fBPb)R6BN6s+({5}c#ovDQY1T*EDXQq!PN^0b*CgP;r6;-"
    b"^FTm$81cRe`p6`v@z6&bl1z?VMgnxEpkoK+K&5+}_hPC=hfc{SEZ2bJEz>HS-91($hpoTGP#+uhUdZVvzs|3BW_Kj@y-"
    b"E`zi$F*P-1yC<i%!ZA^2keq!dJn4B`YX+5^cPetto^B{<M~3L!Vg|4sO~uR3y!wfM38=rj*4oEU74;^4sGk4Z1%Y-"
    b"jhr1E^_0Jc%&mjp*ss3<<W$+jI8D+`<EwKSbJ)nP;mcuZ$mhN&wKFYlSH-+&65=e>jDXp&BnZvaE3n09hVu$2-U^j*#K*PHX$1-"
    b"nYqH-4q5$~F!a&R(TL_Ht9hfoy7n10GH{0$`(CXt@rWH!y6%D7iFFO`yRE|uI!S-!+H3Sn^ELh+Q9_Fks-Rv`f0M4@Ty39VWrx5|"
    b"F8kTovz&$B>0-?8PPt*l6I^>85}3e`ZmNDuD0Vnx!&D^eno&OJv1DmgXU1Kp;`KG+2CSckY$c;uN(il$oHrI#+-"
    b"N0mCzIhNFRW6$eOElC+W{}fC6joWrJD#{#?O12_=GS?MOJPmWd)5NCHUv%8MfoozYTv(-"
    b"g3J=L&Y%8*39<&;c{IRV^Ad{slBed+nv<BCk_2%&YWu`2lgHDA;C=1}rX7>8QYYT}+Ee?R?RX>+huY#5TGzeyMJjC5N2HeHmk)H;"
    b"ed3H6+s3$j?BOkre9kjhK|4wM~$kR1TjCeV-R<egzLVdff=x?$Z{J6RCx1#^=`4G$_+vj{W`_3}A$}3$N3~;39y?LT8^QRac-"
    b"1g)QkYC(A$pVPhKZnt;A`=8Vbn>R*^Ukfy-(&^6!<P9NzE~D!Ez=b*O!=1vb1g}nNQWV_SXl9Qsqw&-"
    b"_ulye+S3&G&N*lHVu?{R)%>b!<hKII;#^dUkMBfwESXJJso#rFS71D{&~T#Z&OK=lNEPObY-"
    b"nVT9=hlj-0f);MS9}&A`?tk>SvgVol3c`y<j}l?=@1MYZq+#P=LrNqr6XnCyM;5Nua_ev&4%ZW5Y|PH(ktUi+OJ-xzUovy7F6U{`"
    b"^Xl)!;fFj~T;Lhfy*t;G;X}yC|~1P;4vEnk1qMluQFVO;f?z!>h}021CMs@cmuyrT&}oBAVU2Mn3mRsm#x#0-"
    b"4Ix00|Agl*;;h?C54IFH)O&QN}YBQ7hJ%suwgiWHUpI?(EU;Gq_{$0GY{7u5qpmhGYw0(yee<L2r6ZUkzU1_{_};Jifq>nixRNk&"
    b"OC*+-"
    b"i{`{0R#LrVm*OZJi$8i8vuc=CT_Kq$H(&4>qrt_#Xp9zWQ>>N>fe1Li<y63&dx)#pA?6X)&G5#&CRSETj?PG+Oeypnf9wVJk&R5K"
    b"jQdF|?B6xAxNxIcXHlyed#h1HF*V$n5svgKI(`K6vObE}l%;TSV6s65#hSjDMb>+dI_5x8gAq9NqmCgWYGpY(+z)x|keS$w!-"
    b"C{?JX?83hdW_jVd3Q{d)=BBmnp;(hp_Z&hvnX%17RfC^^5DGtp51c#MV%CA7i>Z{`=DWqE@%$2<fIVutz%1bFs4&^f%A;E$AnJ!*"
    b">MSHp8+2M4BMxeZFFO4V59p%nvec7|j(&BmF(ocm)$O@6qn>d7F=7wl&&Aehs%D{(&(dAZgF&|YoG7ppgCfY;D7#in82GFP*8W5O"
    b"6LmwkTxW32f4?tTIf#>YNruC>hkg1XmGt};G6*Y0e<W$l|Wyf#!hPvvEirVqvs8U#~zVu?*L13{&KHH5HHCM^2)!!uY_9cqmCsId"
    b"gLyBl$>4}F0hj5dkH&y8t<l`dVA{MH0seq@L9YGAY1InU`)&gQOj*#6D=AaKB&QA8b2Q^qYkR(cfcDvAjWnyK&?T3J|&Oe`@aDGL"
    b"~pOXG7X@lSt5+x`*NWmi-cKeimCC#)!1++DNO)7x@qTmJ*cdPhysRQDHL=}xIc@j;~R{Lb0L~A3C48zH>ZOQM*jnEN-yJZ}_r*nv"
    b"kg;XEhk<mzV&I7<|zbI9YJ^X@qAVtk!^epUg>|ar6CnCPc4*MtrzVv!TfQVHZ;TNV>b*V=6w`o&ZN3uwQAvFb9CxLpJ9zF^xt2S-"
    b"$|8;j{yKP(9cYg(kFBV%#wbR%woG5^sCauv1$;6o{kTy^li?&o-"
    b"q@X1${4MhreVVuY*qr4q=Pr~e$xWL<fIz;yyu8b~XJ4vCiCNh8>S=(FofT%rZS`VGQomEcLtDfwIDf0?MVcbE(4j-"
    b"Yyu@7CLN5<oCqJ-$kb%C+pGe!=6{R<qXBC~B8b_6_R{lNMQ)8Z%Ju*T>;&`$cl8ZA|;xo-vqx9u0hUpL-mXf{5#2T5F90csGJfbD"
    b">Ao0syvcJ>t*dx9?0taYKyTtAk98}{@?<!)iIns^@J0MAC8UL8dfDPAFQFD9FQysk)aX;s!UnkyeDvgvG<zJS-En#RvZ_2`pGrt+"
    b"cTw#I^#Qlt#*TvQz%4Un3#=~=I8q*h;OH{&-$E-"
    b"ckoY9!9bhHM|3}LQyKsQRwLik>38>5;QE*@w;Zd0}BEfF<q^^DNT!)D5Fqf)&}e7_A*DUe;qX+ZXiW91JQ$aP#;pD$(@Ax;CJPGe"
    b"pSF>61%t11(ZN<B2<;T#Fn##olRQYUkIs8Sr~z|`H<z;&;Vvs;_qeO3fd-"
    b"3I7oDIRG7E=QAz)4B;ABoHQz!{<%{y?tuC8}xrf66L;10VC9t8jR-"
    b"~y`#smggh~&p@d1g^oODZVj(f|MAx*XQ)3t#Ul#Us<zpAPiL}-W;f_dDuORVEc<u*R2sKTF8&}9-oVS*U(^UOYC-"
    b"Q84z=ED7&CfT+f;446!jt#Woy%7J4cWjAIlV%L^EKu4w&v!1Gj7P*dHa7Y_>6Wak~{bG+AR*`+xa%e+{6@~VW^d23e^kfg)6ihe-"
    b"4)zPjm6m7D{)iC>gM+rX$-"
    b"5l&_ZO_NaIs!T!BpOh5kj>{4Z`VHb0^il|47+r(c<E|AmYB)Sl?J_eJNsnVKxed_PsVwr3?(5aFLb@7f4(TA1u7QyNUG*M1V!`5y"
    b"1+*B?L+9_im<{nZt4OAH*#s5uJrRE{~g#K%c33GI{Wo?bfmEFLk-=oBQRKzA^{*Yu=-P1W1dOLaCQuhEAdjNI}YW>-"
    b"KfT=3@1z{_!5jV{JwqPV##8Kh-D;mh@nO|-"
    b"PbtQY&J{7tx^5oD3lOk+dSp@nGvbz!3ul3s%`C1AGqN%j2)a{;9T~iY_(Y?8&S*5F6_l$1h2(*>x6C8!m31G6cmoGaV_4Su8*}Fn"
    b"k-wm{e`Gq-(&(VjHy?t@dffNWy&8+1`;9;pPJ8V<?^@Tjwl~+hv8vRe|^B<Uq$f9pP`YBb$_`fn-JAc$GB{;R62;`jC!HaNtC=}@"
    b"I$RhB{e^Zv<)cHfX*0c1`<XnF2r@5u1{<-`AHWkGwAD|y|yR}5V#QS&+nOvxF))L4WP|4K2(@eAuU5neS2(c!L<{~v-"
    b"J0Lmw4gIpP_L(MQ>dR;2G}~F%bvLxj*^e!kJmnl~4S3ehXz%j7Rz$M9h#4AJ2s?qm6FCD{#P}N+5$#2JXLLoYeGE2mB8Uo2#}v3m"
    b";SF>*YMtVJ-@}&jdXISZNBx@PB3me<J0~CWxQ$BZOFrrBu>OhztDLKB=~R7RNf_e?o#6L-8K8^q-"
    b"Ce@0HeKhPz;AOAk4_}Sc^@Pn9m{E=?i{+;O_y?e5^d?-Y&*BpV*<rZ{F8V;Az=o&7-BM};=&!rn^l~6b4EPQ{J6eZZHK+in()-"
    b"@8ptfb3V%SwE6s-"
    b"0oBpeOER8tSb~emM<t%7c{IYBxm1kFr0bGUxor4CBpl^xfMNy55x$s`q4e~V2LjymWYixO6>3M(i_P|0o%EXRjn_9+Dq3)!K!qHd"
    b"Ky3k&m7zFP7gPSyvFL0rF-"
    b"0n1glO45nVn3j4ldJr!Xr=A64MZ@_+_Ag_ROY)n^_1)_!fAfs{TdY_Zz1nsm)CcloK6;$pxBARF}*m%2D?#CSnT-"
    b"W^uhgSkDvBWPo6(e)BlQ}O2=q#Dk+s1ovM7{Zq$#TFYY}3Jx^L<s|ut)eacA@L7a+im?;nQSzo-dvnqjH7R;JZFPEU;WRYgO;R;^"
    b"%-"
    b"Eb@UO6TPJ;DqRv(IE1|<I~Qwca!jiYDSE1_{NU~RcU^{z^uaJjUl!7XN&Xm(cAckFv~n@#{3Vx=63%j2kKKHnA8E<hh0^IVfX0X;"
    b"dPRH*oCF-9^E~l-{g)6PriY_95~y>v<SqR!PEUccx+O1rjcX$u-"
    b"n;9zDW23^z*>}{Ko#Ik@W9F!;Ne7MA)CDI+q5tlZQZ|?_;+YXaH2gYfOZ(XqiThaH!PoyHM~HbW8(3ZF8&ePDB=gk}{xveLii`^D"
    b"ed0W;u#)en=4SiV=2{FF~G4{*mr1=W3K@n?mzuM~4I4Lm`;~AOnhe$7h<x-wk8-"
    b"WV?vhi;Q5Vs~{m%w5O3YkEm@3jzqz2i?gsB?=2I!bv`XXAfR>P4ll+nnsS%g+2ny|PK|ixmL6o*UTn#YGm_lIDCD^JEFdl_F{~vQ"
    b"`nBL%V{cvBhPy}S<-"
    b"hk3OPraad>l?{_v1QgUF8c*;`YdF7m&@WoQ+Unf&9y_yji?EHT$HGhP#q)i5}sFJ~}z9Jv&2+i4KzUE?xm@&fL$*0Ydf}R?zt+pO"
    b"z|C=_q-"
    b"Q;zBX~>buc=oKMiXpEK7Cuwo9;LD=go`JgDHgEjhZU?gDKTsMWl4lV9t7P>E}=Qwr712xw;@KCpC$bL%oEWP=Ku0uZ&A$y~DLRBJ"
    b"DR|+LE97t*`9G=Y`t|o%Sj}LH0QdoDD_JzQiiEi3t@4O_y)fqc*Bj6wtsX!-"
    b"|_KD6HP!ppgl~{%vQPY8K<|~^2*{QdcDnK_A2+h6D+*(&fG4;3?L*4?6hbTb59UKvI;H!2OE<w`ThYvG{M)eJ|bcJ{e1RE{`P~_W"
    b"0M)4i<2L<5F6_pQg_%7cq^_Yq&8qRT<sH<r8ZA-Sr&%@}?{oB_boJ7!&dl=(<dP$i#(iAr_f}0eBh_uqpcY#pQN4|j&lfX+POEF%"
    b"epZI-"
    b"2OceZN&8*TN1ZF+DO$68{Ox&C<dAXYBSE}#fioUPtwEALnc;f?a6MkH*`#Ngm_IYoGyzeDnA2f~82y;X!oy8G(*qvekLOvaI5RwN"
    b"4mZUKeS0uS4`&4k@>jOaOcVY?nup}5Jq{M<dKoU4mm8;R}aJ*4Dgf3`K?FP$qR1VG544+0!W(F36L!#;o&mwWE4Tqs2T*klXJV45"
    b"Ca!fXG5iX(w$yB^YiIw9iN6G|*57hAh1J71!sw#pSCS^-"
    b"Dk#o_Iw$QX@%d7>{#erR$#to?gwl|i>l_^V1q#8(i`bXq3!%I*6j&xEx*L#=)3Tu1OCrj5J7-"
    b"5(40Zk*Wng$bQ&5%MQNGpoi8bmom%dQWCyK($hr#ds!cj8%0teYNPdP3b0rl`RPo)3j=COhl<!fzJZMA;nm(B`@DJ$7(VBp^-"
    b"4#ZnNBsTHm8MyXO1J6FB)Gw|OtjdBt{LJcvHh|PzVasKf?7llfItVZtY@ZL^GX+U*U+Mt*cBH;m1=?yru8UyySF4HIg;K&+RVFH6"
    b"uaRCSu5gK}3v#W*9vxMc?a5$kE$xB)wTVkDDN-{E7c>q-"
    b"t1Z0fNMUupu%zQfM#<jjot};2f$ftS9#qZuP#!lrM;n5@y#0#d>c(RtFMex)T9JLZZIk?Gn`DlceK5?+IX0YX5+KEK*p-"
    b"QExH{6XnG5HC{)x~Zy$9hMZb!HeX)e`?`GcTR>KCTZ)qOVo+s52Br#a73LOhjLLF;|nKY^86~c4%}JhSm&isf_$x!U>qC$j5-"
    b"tnR!FhcJjELbi3UbzEJ7l+<?-"
    b"lfiM`JzthG{LS1G{vOwqEWPr?dV2<)T&x!)){0qY5wDpA=B+Kf2oNFVwKey=i+Td?sGG;|TpI$652lK22zg{2Nbb~}Cp^dtAF{)-"
    b"Z$<NezP$SBtro*us=LtQr>mI;@rXwO6J<r1Xyck`~6JzLU6Gi!{nw;CLvN9PV(_hc9d%qfws{sh<9gK?d>u&?1>DHJ_XquSk$?QN"
    b"YrCSBp0hPu*_L>?NSCd})<UB{2VVZOYx)xVjKaQ*k1|&x~FEF0%0rrL&gP^~VX`uO2lC}>>+llGsj<2*bC3%!jlHXZ`gynGw)wI2"
    b"0X>v+T=eC;_e!cURsJ6(pzikQkjb^6E=Xz5ku7(Qbn)ndpg04RPF(cno-"
    b"!~1_>6=YY5e2vC8#TI3qzmgzK$MUVuv$4RL@*U=t<$?ZZrUuF2deE?iQwAdstT-MMkF;Uy+l1Cy*s8zvnR)TL&T(T^vdvg6f2s`Y"
    b"wZnIlO)Q-"
    b"Jc>dzcWe?SF4m0RG~RGZ+PBaf#sk`DQ{OGG8CWO=ssqD$aKH}&7!VxVHXsnh`n!>%&L&58)!Qg<lSPhz4Yx({c;U7vdBS_ZTO%05"
    b"ZMKHsqIQ4W`b{E-"
    b"bYY`Nz1?wwO6x%gJ&zoK(1nH4SZ;D1$s;QX;6de!*@k;ASj%m;PgG^`T{v5Bs5b40Ja&Iezxa)Ob~7iZgtu5iA~}aIQ+7K-"
    b"ODg+1Ibi+Fo>KnC=Cj}&%sy|pK}6v@(=~~*zdbo!6*{YbpWJ^y2gpetfmh7O00QuZ&MV+BFNq3ZL<?&aBPj)Ovt5Xs3{l)btPc0_"
    b"r_pzvr@$9|mzS4>RlV2m(uKX(hc9+tVd6%O9k&Oe4yBviW}`yV0ZReUI;Vv0?1W~$^2h^^YKZ%beDwIVV_fxU7v!=LPRRF<JpTYV"
    b"u{eAUx%(dTiFb~PJ=DH_CzuAkojlFay|Q!i^q=kI;mOknoQ_RZAMl3ZWc@njKd>9B#P6$u!kaKb<Q$mW4bK3fXH){aF80^*q)WHl"
    b"@<1TQRYSUA-Gi?WDWd}cl3F{;=Y^_#MQS37HBJ4}5I#6?L>3mDp`4~LzPbUXdXw7K4VV6UbXKgtYQ>)?Zx3(J&br0hA}E<oPww#S"
    b"k4tL^@D@znR1(rB$IpJml`gOV%;pDa(SW}$C4l)gPCz!x7gzJ%-rL*zdwa_lE-QCwb`P~{#}eUCAwoDi!Qpw!Ho%aywAJb;;qPbL"
    b"EFExG8ZIn#@o#KhNN*`d1Y`dQ!Z5Aq6(%z+ZFvwxiN2Gxoj-"
    b"g99rradog(hZwgAh{u$s+d%h|v6O?MCe?FX{Su{siDu2fleUQXvxRgTcSDmUDWlcj6V4fP;Cd|}#=V77+`d$;^)KB*|Qr^y`g^$n"
    b"(njsbwu2F2S(lUxDy#EQ^pm^%|mF)@5JX_GH^31sX6Trht_BW(o~XH{7i!0gRO<Dv>N_W4znM;3Ss&e=Z&kftd*hAuEL?{F9cy4Q"
    b">ISNXzn8)6~1_BJ>RKmcpbcK_RD(?uILP8o^IkBD_9n1s{;>~A-jr{3AByn43{7eYyS%VGiW&FI~*YO|`OYFo4lm1F{Qo-"
    b"!)*;3s-"
    b"FEE(MphAxX@;uF0FN)G}ABdiFr4meMo!A0@$kMr}gn8UJ=<68d^%Bu4wpH4QIosrFPb`Pd1N?fTq;oANJ!@@QW7BhVy>(35E*~x5"
    b"J%{NzOaf&66Nu?7$RbwZu?(5lkCK&5=rfKXT+dweNTdr6cq(pIZM{xu{+cP(3#n>3R&BUc<h|Pl>W|C{0Dp@aW)IM|p7MxQAM51`"
    b"u6W<otQ~WzS$qYxOhybctvr>kur5g=6E5EhN%ox3&J#Dy~@|kqwBklW%10bj2>C@4wfusDoe?+0i_*+L(vbUD{s4|=2FkJ&LCJhf"
    b"YM~!;1s43o}qeMWS$|AGCED@ZsfoO>fP&Evp=H~sPVo1+>%4`FITP(4O+Ui@*^01@?Nj6TnH7=DNvt@J|dI#1m(nv}KTtdG0%qnK"
    b"(fB8Dik;<4Tl&scYGCCCymW_yMfEYk@!4w&va7m^Mx+daxTG@(VNWCng5hIez*kQu0&Wt$&oex}ZzbKsbesZ_RQ%7>rM<yCu4i65"
    b"b7vS>qFzk0SUd*thJV_hq+=n1ZLjf8oE^g!`aMFA3q$y&9nc<D5Zdr400ed&PfY3rscNL4tDZiqYMFFli7q!>BbT#l`T4AhrJVoe"
    b"hfj67)F+#m!9&IuA5Were%UUFXOwUL5VQ--"
    b"!=iZ_r>@Dy@&&N7pZ|lC{(xSSpV4~eK_g`@g?HZr+(44=ChtDTG$5q~m>z#GB6Z5{88@HA(f<IV2pU^N<(Ta_&b^2K!dSou0<-"
    b"ik3@OGuw8g(LCH}%i9i(Y3L(G!b$11*o6{_7VonO0}TY=)d#pB(~MXH+u0UC(9p++IFc)Qj>;?mLDn=($XSm%NE6d_Euc4DEC~pn"
    b"A_f>*Jqp2Lzv<%PqJatg6?}#I|{T^OECnMOSEwq!=XH+=~%>FYzGjOZrN;Bi`_yc)PbKBd>^7w>xSB1h8P=vcedyiQ5kq8-"
    b"0AtgPK3%b4DFcWWw0&IgC>TmlDmz8@ef;u&W-"
    b"pn^jIU0f>rqVwbD7&j1B%&%Wb=wFmMgT>Cy9d%sV)g8F@wHv9dQKgQl;r|;0&`@!4MyhXBTmhJox0?N(?"
)

_D64INFO_SOURCE = _d64info_zlib.decompress(
    _d64info_base64.b85decode(_D64INFO_COMPRESSED_B85)
).decode('utf-8')

_D64INFO_MODULE = _d64info_types.ModuleType("_d64info_embedded")
_D64INFO_MODULE.__file__ = str(Path(__file__).with_name('d64info(2).py'))
sys.modules[_D64INFO_MODULE.__name__] = _D64INFO_MODULE
exec(
    compile(_D64INFO_SOURCE, _D64INFO_MODULE.__file__, "exec"),
    _D64INFO_MODULE.__dict__,
)
del _d64info_types

# ---------------------------------------------------------------------------
# Integrierter MOS-6502/6510-Assembler
# ---------------------------------------------------------------------------
class AssemblerError(Exception):
    """Quelltextfehler mit optionaler ASM-Zeilennummer."""

    def __init__(self, message: str, line: Optional[int] = None):
        self.message = str(message)
        self.line = int(line) if line else None
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.line is None:
            return self.message
        return f"Zeile {self.line}: {self.message}"


@dataclass(frozen=True)
class AssemblerStatement:
    line: int
    source: str
    label: str = ""
    kind: str = "empty"
    operation: str = ""
    operand: str = ""


@dataclass(frozen=True)
class AssemblerLayoutItem:
    statement: AssemblerStatement
    address: int
    size: int = 0
    mode: str = ""


@dataclass(frozen=True)
class AssemblerLayout:
    symbols: Dict[str, int]
    items: Tuple[AssemblerLayoutItem, ...]
    basic_mode: Optional[bool]


@dataclass(frozen=True)
class AssembledProgram:
    prg: bytes
    load_address: int
    entry_address: int
    end_address: int
    instruction_count: int
    has_basic_stub: bool
    symbols: Dict[str, int]


_ASSEMBLER_SYMBOL = r"[A-Za-z_.$][A-Za-z0-9_.$]*"
_ASSEMBLER_BRANCHES = frozenset(
    {"BCC", "BCS", "BEQ", "BMI", "BNE", "BPL", "BVC", "BVS"}
)
_ASSEMBLER_DIRECTIVE_ALIASES = {
    "org": "org",
    "entry": "entry",
    "byte": "byte",
    "db": "byte",
    "word": "word",
    "dw": "word",
    "text": "text",
    "ascii": "text",
    "fill": "fill",
    "nostub": "nostub",
    "basic": "basic",
    "end": "empty",
}


def _assembler_opcode_map() -> Dict[Tuple[str, str], int]:
    """Verwendet dieselbe offizielle Opcode-Tabelle wie der Disassembler."""
    return {
        (mnemonic.upper(), mode): opcode
        for opcode, (mnemonic, mode)
        in _D64INFO_MODULE.MOS6510_OPCODES.items()
    }


def _assembler_mode_sizes() -> Dict[str, int]:
    return dict(_D64INFO_MODULE.MOS6510_MODE_SIZE)


def _strip_assembler_comment(line: str) -> str:
    quote = ""
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote:
            escaped = True
            continue
        if quote:
            if character == quote:
                quote = ""
            continue
        if character in {"'", '"'}:
            quote = character
            continue
        if character == ";":
            return line[:index]
    return line


def _split_assembler_arguments(text: str, line: int) -> List[str]:
    if not text.strip():
        return []
    arguments: List[str] = []
    start = 0
    quote = ""
    escaped = False
    depth = 0
    for index, character in enumerate(text):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote:
            escaped = True
            continue
        if quote:
            if character == quote:
                quote = ""
            continue
        if character in {"'", '"'}:
            quote = character
            continue
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                raise AssemblerError("Unerwartete schließende Klammer.", line)
        elif character == "," and depth == 0:
            argument = text[start:index].strip()
            if not argument:
                raise AssemblerError("Leeres Direktivenargument.", line)
            arguments.append(argument)
            start = index + 1
    if quote:
        raise AssemblerError("Nicht abgeschlossene Zeichenkette.", line)
    if depth:
        raise AssemblerError("Nicht abgeschlossene Klammer.", line)
    argument = text[start:].strip()
    if not argument:
        raise AssemblerError("Leeres Direktivenargument.", line)
    arguments.append(argument)
    return arguments


def _assembler_string_bytes(text: str, line: int) -> Optional[bytes]:
    stripped = text.strip()
    if len(stripped) < 2 or stripped[0] not in {"'", '"'}:
        return None
    if stripped[-1] != stripped[0]:
        raise AssemblerError("Nicht abgeschlossene Zeichenkette.", line)
    try:
        value = ast.literal_eval(stripped)
    except (SyntaxError, ValueError) as exc:
        raise AssemblerError("Ungültige Zeichenkette.", line) from exc
    if not isinstance(value, str):
        return None
    result = bytearray()
    for character in value:
        codepoint = ord(character)
        if codepoint > 0xFF:
            raise AssemblerError(
                f"Zeichen U+{codepoint:04X} passt nicht in ein Byte.",
                line,
            )
        result.append(codepoint)
    return bytes(result)


def _parse_assembler_source(source: str) -> Tuple[AssemblerStatement, ...]:
    statements: List[AssemblerStatement] = []
    label_pattern = re.compile(
        rf"^\s*(?P<label>{_ASSEMBLER_SYMBOL})\s*:\s*(?P<rest>.*)$"
    )
    equ_pattern = re.compile(
        rf"^(?P<name>{_ASSEMBLER_SYMBOL})\s+(?:\.equ|equ)\s+"
        rf"(?P<value>.+)$",
        re.IGNORECASE,
    )
    assignment_pattern = re.compile(
        rf"^(?P<name>{_ASSEMBLER_SYMBOL})\s*=\s*(?P<value>.+)$"
    )

    for line_number, original in enumerate(source.splitlines(), 1):
        code = _strip_assembler_comment(original).strip()
        if not code:
            statements.append(AssemblerStatement(line_number, original))
            continue

        label = ""
        match = label_pattern.match(code)
        if match is not None:
            label = match.group("label")
            code = match.group("rest").strip()
            if not code:
                statements.append(
                    AssemblerStatement(
                        line_number,
                        original,
                        label=label,
                    )
                )
                continue

        if re.match(r"^\*\s*=", code):
            operand = code.split("=", 1)[1].strip()
            statements.append(
                AssemblerStatement(
                    line_number,
                    original,
                    label=label,
                    kind="org",
                    operation=".org",
                    operand=operand,
                )
            )
            continue

        match = equ_pattern.match(code) or assignment_pattern.match(code)
        if match is not None:
            if label:
                raise AssemblerError(
                    "Eine Konstantendefinition darf nicht zusätzlich eine "
                    "Marke besitzen.",
                    line_number,
                )
            statements.append(
                AssemblerStatement(
                    line_number,
                    original,
                    kind="const",
                    operation=match.group("name"),
                    operand=match.group("value").strip(),
                )
            )
            continue

        parts = code.split(None, 1)
        operation = parts[0]
        operand = parts[1].strip() if len(parts) == 2 else ""
        directive_name = operation.lstrip(".!").lower()
        kind = _ASSEMBLER_DIRECTIVE_ALIASES.get(directive_name)
        if directive_name == "equ":
            arguments = _split_assembler_arguments(operand, line_number)
            if len(arguments) != 2 or not re.fullmatch(
                _ASSEMBLER_SYMBOL,
                arguments[0],
            ):
                raise AssemblerError(
                    ".equ erwartet '.equ NAME, Ausdruck'.",
                    line_number,
                )
            statements.append(
                AssemblerStatement(
                    line_number,
                    original,
                    label=label,
                    kind="const",
                    operation=arguments[0],
                    operand=arguments[1],
                )
            )
            continue
        if kind is not None:
            statements.append(
                AssemblerStatement(
                    line_number,
                    original,
                    label=label,
                    kind=kind,
                    operation=operation,
                    operand=operand,
                )
            )
            continue

        statements.append(
            AssemblerStatement(
                line_number,
                original,
                label=label,
                kind="instruction",
                operation=operation.upper(),
                operand=operand,
            )
        )

    return tuple(statements)


def _tokenize_assembler_expression(
    expression: str,
    line: int,
) -> List[Tuple[str, object]]:
    tokens: List[Tuple[str, object]] = []
    index = 0
    length = len(expression)
    while index < length:
        character = expression[index]
        if character.isspace():
            index += 1
            continue

        if character == "$" and index + 1 < length and expression[index + 1] in "0123456789abcdefABCDEF":
            end = index + 1
            while end < length and expression[end] in "0123456789abcdefABCDEF":
                end += 1
            tokens.append(("number", int(expression[index + 1:end], 16)))
            index = end
            continue
        if character == "%" and index + 1 < length and expression[index + 1] in "01":
            end = index + 1
            while end < length and expression[end] in "01":
                end += 1
            tokens.append(("number", int(expression[index + 1:end], 2)))
            index = end
            continue
        if expression[index:index + 2].lower() in {"0x", "0b"}:
            base = 16 if expression[index + 1].lower() == "x" else 2
            valid = (
                "0123456789abcdefABCDEF"
                if base == 16
                else "01"
            )
            end = index + 2
            while end < length and expression[end] in valid:
                end += 1
            if end == index + 2:
                raise AssemblerError("Ungültiger Zahlenwert.", line)
            tokens.append(("number", int(expression[index + 2:end], base)))
            index = end
            continue
        if character.isdigit():
            end = index + 1
            while end < length and expression[end].isdigit():
                end += 1
            tokens.append(("number", int(expression[index:end], 10)))
            index = end
            continue
        if character in {"'", '"'}:
            quote = character
            end = index + 1
            escaped = False
            while end < length:
                current = expression[end]
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == quote:
                    break
                end += 1
            if end >= length:
                raise AssemblerError("Nicht abgeschlossenes Zeichenliteral.", line)
            literal = expression[index:end + 1]
            try:
                value = ast.literal_eval(literal)
            except (SyntaxError, ValueError) as exc:
                raise AssemblerError("Ungültiges Zeichenliteral.", line) from exc
            if not isinstance(value, str) or len(value) != 1:
                raise AssemblerError(
                    "In Ausdrücken ist genau ein Zeichen erlaubt.",
                    line,
                )
            tokens.append(("number", ord(value)))
            index = end + 1
            continue
        symbol_match = re.match(_ASSEMBLER_SYMBOL, expression[index:])
        if symbol_match is not None:
            symbol = symbol_match.group(0)
            tokens.append(("symbol", symbol))
            index += len(symbol)
            continue
        two_character = expression[index:index + 2]
        if two_character in {"<<", ">>"}:
            tokens.append(("operator", two_character))
            index += 2
            continue
        if character in "+-*/&|^~()<>":
            tokens.append(("operator", character))
            index += 1
            continue
        raise AssemblerError(
            f"Ungültiges Zeichen im Ausdruck: {character!r}.",
            line,
        )
    tokens.append(("end", ""))
    return tokens


class _AssemblerExpressionParser:
    PRECEDENCE = {
        "|": 1,
        "^": 2,
        "&": 3,
        "<<": 4,
        ">>": 4,
        "+": 5,
        "-": 5,
        "*": 6,
        "/": 6,
    }

    def __init__(
        self,
        expression: str,
        symbols: Dict[str, int],
        pc: int,
        line: int,
    ):
        self.tokens = _tokenize_assembler_expression(expression, line)
        self.symbols = symbols
        self.pc = pc
        self.line = line
        self.index = 0
        self.unresolved: set[str] = set()

    def _peek(self) -> Tuple[str, object]:
        return self.tokens[self.index]

    def _take(self) -> Tuple[str, object]:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def parse(self) -> Tuple[int, set[str]]:
        value = self._expression(0)
        if self._peek()[0] != "end":
            raise AssemblerError("Unerwarteter Ausdrucksteil.", self.line)
        return value, self.unresolved

    def _expression(self, minimum_precedence: int) -> int:
        token_kind, token_value = self._take()
        if token_kind == "number":
            left = int(token_value)
        elif token_kind == "symbol":
            name = str(token_value).casefold()
            if name in self.symbols:
                left = int(self.symbols[name])
            else:
                self.unresolved.add(str(token_value))
                left = 0
        elif token_kind == "operator" and token_value == "(":
            left = self._expression(0)
            if self._take() != ("operator", ")"):
                raise AssemblerError("Schließende Klammer fehlt.", self.line)
        elif token_kind == "operator" and token_value in {"+", "-", "~", "<", ">"}:
            right = self._expression(7)
            if token_value == "+":
                left = right
            elif token_value == "-":
                left = -right
            elif token_value == "~":
                left = ~right
            elif token_value == "<":
                left = right & 0xFF
            else:
                left = (right >> 8) & 0xFF
        elif token_kind == "operator" and token_value == "*":
            left = self.pc
        else:
            raise AssemblerError("Ausdruck erwartet.", self.line)

        while True:
            next_kind, next_value = self._peek()
            if next_kind != "operator" or next_value not in self.PRECEDENCE:
                break
            precedence = self.PRECEDENCE[str(next_value)]
            if precedence < minimum_precedence:
                break
            self._take()
            right = self._expression(precedence + 1)
            operator = str(next_value)
            if operator == "+":
                left += right
            elif operator == "-":
                left -= right
            elif operator == "*":
                left *= right
            elif operator == "/":
                if right == 0:
                    raise AssemblerError("Division durch null.", self.line)
                quotient = abs(left) // abs(right)
                left = -quotient if (left < 0) != (right < 0) else quotient
            elif operator == "<<":
                if right < 0:
                    raise AssemblerError("Negative Schiebeweite.", self.line)
                left <<= right
            elif operator == ">>":
                if right < 0:
                    raise AssemblerError("Negative Schiebeweite.", self.line)
                left >>= right
            elif operator == "&":
                left &= right
            elif operator == "^":
                left ^= right
            elif operator == "|":
                left |= right
        return left


def _evaluate_assembler_expression(
    expression: str,
    symbols: Dict[str, int],
    pc: int,
    line: int,
) -> Tuple[int, set[str]]:
    if not expression.strip():
        raise AssemblerError("Ausdruck erwartet.", line)
    return _AssemblerExpressionParser(expression, symbols, pc, line).parse()


def _assembler_operand_expression(mode: str, operand: str, line: int) -> str:
    text = operand.strip()
    if mode in {"imp", "acc"}:
        return ""
    if mode == "imm":
        return text[1:].strip()
    if mode == "izx":
        match = re.fullmatch(r"\(\s*(.+?)\s*,\s*[Xx]\s*\)", text)
    elif mode == "izy":
        match = re.fullmatch(r"\(\s*(.+?)\s*\)\s*,\s*[Yy]", text)
    elif mode == "ind":
        match = re.fullmatch(r"\(\s*(.+?)\s*\)", text)
    elif mode in {"zpx", "absx"}:
        match = re.fullmatch(r"(.+?)\s*,\s*[Xx]", text)
    elif mode in {"zpy", "absy"}:
        match = re.fullmatch(r"(.+?)\s*,\s*[Yy]", text)
    else:
        return text
    if match is None:
        raise AssemblerError("Ungültige Operandenform.", line)
    return match.group(1).strip()


def _select_assembler_mode(
    statement: AssemblerStatement,
    pc: int,
    symbols: Dict[str, int],
    opcode_map: Dict[Tuple[str, str], int],
    *,
    final: bool,
) -> str:
    mnemonic = statement.operation.upper()
    operand = statement.operand.strip()
    available = {
        mode
        for candidate, mode in opcode_map
        if candidate == mnemonic
    }
    if not available:
        raise AssemblerError(
            f"Unbekannter oder nicht unterstützter Opcode: {mnemonic}.",
            statement.line,
        )

    if not operand:
        if "imp" in available:
            return "imp"
        if "acc" in available:
            return "acc"
        raise AssemblerError(
            f"{mnemonic} benötigt einen Operanden.",
            statement.line,
        )
    if operand.upper() == "A" and "acc" in available:
        return "acc"
    if mnemonic in _ASSEMBLER_BRANCHES:
        if "rel" not in available:
            raise AssemblerError("Relativer Sprung nicht unterstützt.", statement.line)
        return "rel"
    if operand.startswith("#"):
        if "imm" not in available:
            raise AssemblerError(
                f"{mnemonic} unterstützt keine unmittelbare Adressierung.",
                statement.line,
            )
        return "imm"

    explicit_modes = (
        ("izx", r"\(\s*(.+?)\s*,\s*[Xx]\s*\)"),
        ("izy", r"\(\s*(.+?)\s*\)\s*,\s*[Yy]"),
        ("ind", r"\(\s*(.+?)\s*\)"),
    )
    for mode, pattern in explicit_modes:
        if re.fullmatch(pattern, operand):
            if mode not in available:
                raise AssemblerError(
                    f"{mnemonic} unterstützt den Adressierungsmodus "
                    f"'{operand}' nicht.",
                    statement.line,
                )
            return mode

    index_match = re.fullmatch(r"(.+?)\s*,\s*([XxYy])", operand)
    if index_match is not None:
        expression = index_match.group(1).strip()
        register = index_match.group(2).upper()
        value, unresolved = _evaluate_assembler_expression(
            expression,
            symbols,
            pc,
            statement.line,
        )
        short_mode, long_mode = (
            ("zpx", "absx") if register == "X" else ("zpy", "absy")
        )
    else:
        value, unresolved = _evaluate_assembler_expression(
            operand,
            symbols,
            pc,
            statement.line,
        )
        short_mode, long_mode = "zp", "abs"

    if final and unresolved:
        names = ", ".join(sorted(unresolved, key=str.casefold))
        raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
    if not unresolved and 0 <= value <= 0xFF and short_mode in available:
        return short_mode
    if long_mode in available:
        return long_mode
    if short_mode in available:
        return short_mode
    raise AssemblerError(
        f"{mnemonic} unterstützt den Operanden '{operand}' nicht.",
        statement.line,
    )


def _define_assembler_symbol(
    symbols: Dict[str, int],
    defined: set[str],
    name: str,
    value: int,
    line: int,
) -> None:
    key = name.casefold()
    if key in defined:
        raise AssemblerError(f"Symbol mehrfach definiert: {name}.", line)
    defined.add(key)
    symbols[key] = int(value)


def _assembler_directive_size(
    statement: AssemblerStatement,
    pc: int,
    symbols: Dict[str, int],
    *,
    final: bool,
) -> int:
    arguments = _split_assembler_arguments(statement.operand, statement.line)
    if statement.kind in {"byte", "text"}:
        if not arguments:
            raise AssemblerError("Mindestens ein Wert wird erwartet.", statement.line)
        size = 0
        for argument in arguments:
            string_data = _assembler_string_bytes(argument, statement.line)
            size += len(string_data) if string_data is not None else 1
        return size
    if statement.kind == "word":
        if not arguments:
            raise AssemblerError("Mindestens ein Wort wird erwartet.", statement.line)
        for argument in arguments:
            if _assembler_string_bytes(argument, statement.line) is not None:
                raise AssemblerError(
                    ".word akzeptiert keine Zeichenketten.",
                    statement.line,
                )
        return len(arguments) * 2
    if statement.kind == "fill":
        if not 1 <= len(arguments) <= 2:
            raise AssemblerError(
                ".fill erwartet Anzahl und optional einen Bytewert.",
                statement.line,
            )
        count, unresolved = _evaluate_assembler_expression(
            arguments[0],
            symbols,
            pc,
            statement.line,
        )
        if unresolved:
            names = ", ".join(sorted(unresolved, key=str.casefold))
            raise AssemblerError(
                f"Die .fill-Anzahl muss bereits bekannt sein: {names}.",
                statement.line,
            )
        if not 0 <= count <= 0x10000:
            raise AssemblerError(
                ".fill-Anzahl liegt außerhalb 0..65536.",
                statement.line,
            )
        return count
    raise AssertionError(statement.kind)


def _layout_assembler(
    statements: Tuple[AssemblerStatement, ...],
    seed_symbols: Dict[str, int],
    *,
    final: bool,
) -> AssemblerLayout:
    opcode_map = _assembler_opcode_map()
    mode_sizes = _assembler_mode_sizes()
    symbols: Dict[str, int] = {}
    defined: set[str] = set()
    items: List[AssemblerLayoutItem] = []
    pc = 0x080D
    basic_mode: Optional[bool] = None

    for statement in statements:
        visible_symbols = dict(seed_symbols)
        visible_symbols.update(symbols)
        if statement.label:
            _define_assembler_symbol(
                symbols,
                defined,
                statement.label,
                pc,
                statement.line,
            )
            visible_symbols[statement.label.casefold()] = pc

        address = pc
        size = 0
        mode = ""
        if statement.kind == "const":
            value, unresolved = _evaluate_assembler_expression(
                statement.operand,
                visible_symbols,
                pc,
                statement.line,
            )
            if final and unresolved:
                names = ", ".join(sorted(unresolved, key=str.casefold))
                raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
            key = statement.operation.casefold()
            if unresolved and key in seed_symbols:
                value = seed_symbols[key]
            _define_assembler_symbol(
                symbols,
                defined,
                statement.operation,
                value,
                statement.line,
            )
        elif statement.kind == "org":
            value, unresolved = _evaluate_assembler_expression(
                statement.operand,
                visible_symbols,
                pc,
                statement.line,
            )
            if unresolved:
                names = ", ".join(sorted(unresolved, key=str.casefold))
                raise AssemblerError(
                    f"Die .org-Adresse muss bereits bekannt sein: {names}.",
                    statement.line,
                )
            if not 0 <= value <= 0xFFFF:
                raise AssemblerError(
                    ".org-Adresse liegt außerhalb $0000..$FFFF.",
                    statement.line,
                )
            pc = value
            address = pc
        elif statement.kind == "entry":
            if not statement.operand:
                raise AssemblerError(".entry erwartet eine Adresse.", statement.line)
        elif statement.kind == "nostub":
            if statement.operand:
                raise AssemblerError(".nostub hat keinen Operanden.", statement.line)
            basic_mode = False
        elif statement.kind == "basic":
            if statement.operand:
                raise AssemblerError(".basic hat keinen Operanden.", statement.line)
            basic_mode = True
        elif statement.kind in {"byte", "word", "text", "fill"}:
            size = _assembler_directive_size(
                statement,
                pc,
                visible_symbols,
                final=final,
            )
        elif statement.kind == "instruction":
            mode = _select_assembler_mode(
                statement,
                pc,
                visible_symbols,
                opcode_map,
                final=final,
            )
            size = mode_sizes[mode]
        elif statement.kind != "empty":
            raise AssemblerError(
                f"Unbekannte Direktive: {statement.operation}.",
                statement.line,
            )

        items.append(AssemblerLayoutItem(statement, address, size, mode))
        if size:
            if pc + size > 0x10000:
                raise AssemblerError(
                    "Ausgabe überschreitet das Ende des C64-Adressraums.",
                    statement.line,
                )
            pc += size

    return AssemblerLayout(symbols, tuple(items), basic_mode)


def _converged_assembler_layout(
    statements: Tuple[AssemblerStatement, ...],
) -> AssemblerLayout:
    seed: Dict[str, int] = {}
    previous_signature = None
    for _iteration in range(16):
        layout = _layout_assembler(statements, seed, final=False)
        signature = tuple(
            (item.address, item.size, item.mode)
            for item in layout.items
        )
        if layout.symbols == seed and signature == previous_signature:
            return _layout_assembler(statements, layout.symbols, final=True)
        seed = dict(layout.symbols)
        previous_signature = signature
    raise AssemblerError(
        "Symboladressen konnten nach 16 Durchläufen nicht stabilisiert werden."
    )


def _check_assembler_byte(value: int, line: int, description: str) -> int:
    if not -128 <= value <= 0xFF:
        raise AssemblerError(
            f"{description} liegt außerhalb -128..255: {value}.",
            line,
        )
    return value & 0xFF


def _check_assembler_word(value: int, line: int, description: str) -> int:
    if not -32768 <= value <= 0xFFFF:
        raise AssemblerError(
            f"{description} liegt außerhalb -32768..65535: {value}.",
            line,
        )
    return value & 0xFFFF

def _basic_sys_stub(entry_address: int) -> bytes:
    digits = str(entry_address).encode("ascii")
    next_line = 0x0801 + 2 + 2 + 1 + len(digits) + 1
    return bytes(
        (
            next_line & 0xFF,
            (next_line >> 8) & 0xFF,
            10,
            0,
            0x9E,
        )
    ) + digits + b"\x00\x00\x00"

def assemble_mos6510_source(
    source: str,
    *,
    filename: str = "<ASM-Editor>",
) -> AssembledProgram:
    """Übersetzt offiziellen MOS-6502/6510-Quelltext in ein C64-PRG."""
    del filename  # Der Anzeigename wird von der GUI geführt.
    statements = _parse_assembler_source(source)
    if not any(statement.kind != "empty" for statement in statements):
        raise AssemblerError("Der Assemblerquelltext ist leer.")
    layout = _converged_assembler_layout(statements)
    opcode_map = _assembler_opcode_map()
    memory: Dict[int, int] = {}
    first_instruction: Optional[int] = None
    instruction_count = 0

    def write_byte(address: int, value: int, line: int) -> None:
        if not 0 <= address <= 0xFFFF:
            raise AssemblerError("Adresse außerhalb $0000..$FFFF.", line)
        if address in memory:
            raise AssemblerError(
                f"Adresse ${address:04X} wird mehrfach beschrieben.",
                line,
            )
        memory[address] = value & 0xFF

    entry_address: Optional[int] = None
    for item in layout.items:
        statement = item.statement
        symbols = layout.symbols
        if statement.kind == "entry":
            value, unresolved = _evaluate_assembler_expression(
                statement.operand,
                symbols,
                item.address,
                statement.line,
            )
            if unresolved:
                names = ", ".join(sorted(unresolved, key=str.casefold))
                raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
            if not 0 <= value <= 0xFFFF:
                raise AssemblerError(
                    ".entry-Adresse liegt außerhalb $0000..$FFFF.",
                    statement.line,
                )
            entry_address = value
            continue
        if statement.kind in {"byte", "text"}:
            address = item.address
            for argument in _split_assembler_arguments(
                statement.operand,
                statement.line,
            ):
                string_data = _assembler_string_bytes(argument, statement.line)
                if string_data is not None:
                    for value in string_data:
                        write_byte(address, value, statement.line)
                        address += 1
                    continue
                value, unresolved = _evaluate_assembler_expression(
                    argument,
                    symbols,
                    address,
                    statement.line,
                )
                if unresolved:
                    names = ", ".join(sorted(unresolved, key=str.casefold))
                    raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
                write_byte(
                    address,
                    _check_assembler_byte(value, statement.line, "Bytewert"),
                    statement.line,
                )
                address += 1
            continue
        if statement.kind == "word":
            address = item.address
            for argument in _split_assembler_arguments(
                statement.operand,
                statement.line,
            ):
                value, unresolved = _evaluate_assembler_expression(
                    argument,
                    symbols,
                    address,
                    statement.line,
                )
                if unresolved:
                    names = ", ".join(sorted(unresolved, key=str.casefold))
                    raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
                value = _check_assembler_word(value, statement.line, "Wortwert")
                write_byte(address, value & 0xFF, statement.line)
                write_byte(address + 1, value >> 8, statement.line)
                address += 2
            continue
        if statement.kind == "fill":
            arguments = _split_assembler_arguments(
                statement.operand,
                statement.line,
            )
            fill_value = 0
            if len(arguments) == 2:
                fill_value, unresolved = _evaluate_assembler_expression(
                    arguments[1],
                    symbols,
                    item.address,
                    statement.line,
                )
                if unresolved:
                    names = ", ".join(sorted(unresolved, key=str.casefold))
                    raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
                fill_value = _check_assembler_byte(
                    fill_value,
                    statement.line,
                    "Füllbyte",
                )
            for offset in range(item.size):
                write_byte(item.address + offset, fill_value, statement.line)
            continue
        if statement.kind != "instruction":
            continue

        instruction_count += 1
        if first_instruction is None:
            first_instruction = item.address
        opcode = opcode_map[(statement.operation, item.mode)]
        write_byte(item.address, opcode, statement.line)
        if item.mode in {"imp", "acc"}:
            continue

        expression = _assembler_operand_expression(
            item.mode,
            statement.operand,
            statement.line,
        )
        value, unresolved = _evaluate_assembler_expression(
            expression,
            layout.symbols,
            item.address,
            statement.line,
        )
        if unresolved:
            names = ", ".join(sorted(unresolved, key=str.casefold))
            raise AssemblerError(f"Unbekanntes Symbol: {names}.", statement.line)
        if item.mode == "rel":
            if not 0 <= value <= 0xFFFF:
                raise AssemblerError("Sprungziel außerhalb des Adressraums.", statement.line)
            displacement = (
                (value - (item.address + 2) + 0x8000) & 0xFFFF
            ) - 0x8000
            if not -128 <= displacement <= 127:
                raise AssemblerError(
                    f"Relativer Sprung nach ${value:04X} ist außer Reichweite "
                    f"({displacement:+d} Bytes).",
                    statement.line,
                )
            write_byte(item.address + 1, displacement & 0xFF, statement.line)
        elif item.mode in {"imm", "zp", "zpx", "zpy", "izx", "izy"}:
            write_byte(
                item.address + 1,
                _check_assembler_byte(value, statement.line, "Operand"),
                statement.line,
            )
        else:
            value = _check_assembler_word(value, statement.line, "Adresse")
            write_byte(item.address + 1, value & 0xFF, statement.line)
            write_byte(item.address + 2, value >> 8, statement.line)

    if not memory:
        raise AssemblerError("Der Quelltext erzeugt keine Programmdaten.")

    # Zielmodule können einen exklusiven VIC-II-Speicherbereich markieren.
    # Das ist bei der C64-HiRes-Grafik notwendig: Programmcode oder statische
    # Daten im vom Zielmodul markierten VIC-II-Bankbereich würden beim Laden
    # bzw. Zeichnen gegenseitig überschrieben und als zufällige farbige 8x8-Blöcke sichtbar werden.
    reserve_start = layout.symbols.get(
        "__d64_graphics_reserve_start"
    )
    reserve_end = layout.symbols.get(
        "__d64_graphics_reserve_end"
    )
    if reserve_start is not None or reserve_end is not None:
        if reserve_start is None or reserve_end is None:
            raise AssemblerError(
                "Grafikspeicher-Reservierung benötigt Start und Ende."
            )
        if not 0 <= reserve_start <= reserve_end <= 0xFFFF:
            raise AssemblerError(
                "Ungültiger reservierter C64-Grafikspeicherbereich."
            )
        collisions = [
            address for address in memory
            if reserve_start <= address <= reserve_end
        ]
        if collisions:
            first = min(collisions)
            last = max(collisions)
            raise AssemblerError(
                "Programmcode oder Daten überschneiden den reservierten "
                f"C64-Grafikspeicher ${reserve_start:04X}-${reserve_end:04X} "
                f"bei ${first:04X}-${last:04X}."
            )

    runtime_start = layout.symbols.get(
        "__d64_graphics_runtime_start"
    )
    runtime_limit = layout.symbols.get(
        "__d64_graphics_runtime_limit"
    )
    if runtime_start is not None or runtime_limit is not None:
        if runtime_start is None or runtime_limit is None:
            raise AssemblerError(
                "Grafik-Runtime benötigt Startadresse und Obergrenze."
            )
        runtime_bytes = [
            address for address in memory if address >= runtime_start
        ]
        if runtime_bytes and max(runtime_bytes) >= runtime_limit:
            raise AssemblerError(
                "C64-Grafik-Runtime überschreitet den sicheren Bereich "
                f"${runtime_start:04X}-${runtime_limit - 1:04X}."
            )

    if entry_address is None:
        entry_address = first_instruction
    if entry_address is None:
        entry_address = min(memory)

    source_start = min(memory)
    add_basic_stub = (
        layout.basic_mode is True
        or (layout.basic_mode is None and source_start >= 0x080D)
    )
    if add_basic_stub:
        stub = _basic_sys_stub(entry_address)
        for offset, value in enumerate(stub):
            address = 0x0801 + offset
            if address in memory:
                directive = "Entferne .basic oder verwende .nostub."
                raise AssemblerError(
                    f"Der BASIC-SYS-Stub überschneidet Programmdaten bei "
                    f"${address:04X}. {directive}"
                )
            memory[address] = value

    load_address = min(memory)
    end_address = max(memory)
    payload = bytes(
        memory.get(address, 0)
        for address in range(load_address, end_address + 1)
    )
    prg = bytes((load_address & 0xFF, load_address >> 8)) + payload
    return AssembledProgram(
        prg=prg,
        load_address=load_address,
        entry_address=entry_address,
        end_address=end_address,
        instruction_count=instruction_count,
        has_basic_stub=add_basic_stub,
        symbols=dict(layout.symbols),
    )

def parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="D64-DISM GUI und BASIC-/C-/Pascal-Kommandozeilencompiler"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        help="optionales Arbeitsverzeichnis beim Programmstart",
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--write-amiga",
        metavar="QUELLE",
        type=Path,
        help="C-/Pascal-Quelle als bootfähiges Amiga-ADF speichern",
    )
    target.add_argument(
        "--write-c64",
        metavar="QUELLE",
        type=Path,
        help="BASIC-/C-/Pascal-Quelle als C64-PRG speichern",
    )
    target.add_argument(
        "--write-pe32",
        metavar="QUELLE",
        type=Path,
        help="C-/Pascal-Quelle intern zu COFF32 und anschließend als PE32-EXE bzw. Pascal-LIBRARY als DLL linken",
    )
    target.add_argument(
        "--write-coff32",
        metavar="QUELLE",
        type=Path,
        help="C-/Pascal-Quelle als relocierbares internes COFF32-.o erzeugen",
    )
    target.add_argument(
        "--archive-coff32",
        metavar="ARCHIV",
        type=Path,
        help="COFF32-Objekte aus --object in ein .a-Archiv schreiben",
    )
    target.add_argument(
        "--link-pe32",
        metavar="EXE",
        type=Path,
        help="COFF32-Objekte/Archive aus --object intern zu PE32-EXE oder bei .dll-Ziel zu DLL linken",
    )
    target.add_argument(
        "--write-pui",
        metavar="UNIT",
        type=Path,
        help="Pascal-Unit-Interface als .pui speichern",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Ausgabedatei (Standard: Quellenname mit .adf bzw. .prg)",
    )
    parser.add_argument(
        "-Fi",
        "--include-path",
        action="append",
        default=[],
        type=Path,
        metavar="PFAD",
        help="Suchpfad für Pascal-Units/PUI und C-Header; wiederholbar",
    )
    parser.add_argument(
        "-D",
        "--define",
        action="append",
        default=[],
        metavar="NAME[=WERT]",
        help="vordefiniertes C-/Pascal-Makro; wiederholbar",
    )
    parser.add_argument(
        "--amiga-cpu",
        choices=AMIGA_CPU_MODELS,
        default="mk68000",
        help="Amiga-CPU-Profil für Compiler und 68k-Assembler",
    )
    parser.add_argument(
        "--amiga-fpu",
        choices=AMIGA_FPU_MODELS,
        default="FPU: None",
        help="optionales 68881/68882-FPU-Profil",
    )
    parser.add_argument(
        "--windows-graphics",
        choices=WINDOWS_GRAPHICS_BACKENDS,
        default="Direct2D",
        help="Grafikbackend für Windows PE32",
    )
    parser.add_argument(
        "--object",
        action="append",
        default=[],
        type=Path,
        metavar="DATEI",
        help="COFF32-.o/.obj oder .a/.lib; für Archiv/Linker wiederholbar",
    )
    return parser.parse_args(argv)

def _cli_defines(values: Sequence[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in values:
        name, separator, value = str(item).partition("=")
        if not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise ValueError(f"Ungültiger Makroname für -D: {name or item!r}")
        result[name] = value if separator else "1"
    return result

def _write_cli_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _write_pe32_generated_objects(
    generated,
    *,
    source_path: Path,
    assembly_path: Path,
    main_object_path: Optional[Path] = None,
) -> List[Path]:
    """Assembliert Hauptmodul und PE32-Abhängigkeiten separat zu COFF32."""
    result: List[Path] = []
    seen: set[str] = set()

    def add_object(path: Path, assembly: str, asm_name: str) -> None:
        resolved = path.expanduser().resolve()
        key = str(resolved).casefold()
        if key in seen:
            return
        data = assemble_pe32_coff_object(assembly, filename=asm_name)
        _write_cli_file(resolved, data)
        seen.add(key)
        result.append(resolved)

    main_path = (
        main_object_path.expanduser().resolve()
        if main_object_path is not None
        else source_path.with_suffix(".o").resolve()
    )
    add_object(main_path, generated.assembly, assembly_path.name)

    # Separat kompilierte C-Translation-Units (#pragma link).
    for module_name, module_assembly in getattr(generated, "linked_pe32_modules", ()):
        module_source = Path(module_name).expanduser().resolve()
        module_asm = module_source.with_suffix(".generated.pe32.asm")
        _write_cli_file(module_asm, str(module_assembly).encode("utf-8"))
        add_object(module_source.with_suffix(".o"), str(module_assembly), module_asm.name)

    # Bereits vorhandene ASM-Module aus Pascal-Units bzw. #pragma link.
    for module_name in getattr(generated, "linked_assembly_files", ()):
        module_path = Path(module_name).expanduser().resolve()
        try:
            module_assembly = module_path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            module_assembly = module_path.read_text(encoding="cp1252")
        add_object(module_path.with_suffix(".o"), module_assembly, module_path.name)

    return result


def _compile_cli(args: argparse.Namespace) -> int:
    if args.write_amiga is not None:
        target = "amiga"
        source_arg = args.write_amiga
    elif args.write_pe32 is not None or args.write_coff32 is not None:
        target = "pe32"
        source_arg = args.write_pe32 or args.write_coff32
    else:
        target = "c64"
        source_arg = args.write_c64
    source_path = source_arg.expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"Quelldatei nicht gefunden: {source_path}")
    try:
        source = source_path.read_text(encoding="utf-8-sig")
    except UnicodeError:
        source = source_path.read_text(encoding="cp1252")
    include_paths = [source_path.parent]
    for item in args.include_path:
        path = item.expanduser().resolve()
        if path not in include_paths:
            include_paths.append(path)
    defines = _cli_defines(args.define)
    if target == "pe32":
        defines.update(windows_graphics_predefined_macros(args.windows_graphics))
    suffix = source_path.suffix.casefold()
    if suffix in {".bas", ".basic"}:
        if target != "c64":
            raise ValueError("C64 BASIC kann nur für das Ziel C-64 kompiliert werden.")
        from c64basic import compile_basic_to_assembly
        generated = compile_basic_to_assembly(
            source, filename=str(source_path), target="c64"
        )
    elif suffix in {".pas", ".pp"}:
        from c64pascal import compile_pascal_to_assembly
        kwargs = dict(
            filename=str(source_path), include_paths=include_paths,
            predefined_macros=defines, target=target,
        )
        try:
            params = inspect.signature(compile_pascal_to_assembly).parameters
        except (TypeError, ValueError):
            params = {}
        if target == "amiga":
            if "cpu_model" in params:
                kwargs["cpu_model"] = args.amiga_cpu
            if "fpu_model" in params:
                kwargs["fpu_model"] = args.amiga_fpu
        if target == "pe32" and "graphics_backend" in params:
            kwargs["graphics_backend"] = args.windows_graphics
        generated = compile_pascal_to_assembly(source, **kwargs)
    elif suffix == ".c":
        from c64c import compile_c_to_assembly
        kwargs = dict(
            filename=str(source_path), include_paths=include_paths,
            predefined_macros=defines, target=target,
        )
        try:
            params = inspect.signature(compile_c_to_assembly).parameters
        except (TypeError, ValueError):
            params = {}
        if target == "amiga":
            if "cpu_model" in params:
                kwargs["cpu_model"] = args.amiga_cpu
            if "fpu_model" in params:
                kwargs["fpu_model"] = args.amiga_fpu
        if target == "pe32" and "graphics_backend" in params:
            kwargs["graphics_backend"] = args.windows_graphics
        generated = compile_c_to_assembly(source, **kwargs)
    else:
        raise ValueError(
            "CLI-Compiler erwartet eine .bas-, .basic-, .pas-, .pp- oder .c-Datei."
        )

    assembly_suffix = (
        ".generated.amiga.asm" if target == "amiga"
        else ".generated.pe32.asm" if target == "pe32"
        else ".generated.asm"
    )
    assembly_path = source_path.with_suffix(assembly_suffix).resolve()
    _write_cli_file(assembly_path, generated.assembly.encode("utf-8"))

    source_kind = getattr(generated, "source_kind", "program")

    if target == "pe32":
        explicit_object_only = args.write_coff32 is not None
        if explicit_object_only or source_kind == "unit":
            object_path = (
                args.output.expanduser().resolve()
                if args.output is not None
                else source_path.with_suffix(".o").resolve()
            )
            object_paths = _write_pe32_generated_objects(
                generated,
                source_path=source_path,
                assembly_path=assembly_path,
                main_object_path=object_path,
            )
            pui_path = getattr(generated, "pui_path", None)
            if pui_path:
                print(f"PUI: {Path(pui_path).resolve()}")
            print(
                f"COFF32: {source_path} -> {assembly_path} -> "
                + ", ".join(str(path) for path in object_paths)
            )
            return 0

        object_paths = _write_pe32_generated_objects(
            generated,
            source_path=source_path,
            assembly_path=assembly_path,
        )
        for item in getattr(args, "object", ()):
            path = item.expanduser().resolve()
            if path not in object_paths:
                object_paths.append(path)

        if source_kind == "library":
            linked = link_coff32_inputs(
                object_paths,
                entry_symbol="__d64_dll_entry",
                gui=True,
                dll=True,
                dll_name=f"{generated.program_name}.dll",
            )
            image = linked.executable
            default_output = source_path.with_suffix(".dll")
        else:
            linked = link_coff32_inputs(
                object_paths,
                entry_symbol="_start",
                gui=True,
                dll=False,
            )
            image = linked.executable
            default_output = source_path.with_suffix(".exe")
    elif source_kind == "unit":
        pui_path = (
            Path(generated.pui_path).resolve()
            if getattr(generated, "pui_path", None)
            else source_path.with_suffix(".pui").resolve()
        )
        print(f"{target.upper()} UNIT: {source_path} -> {pui_path} -> {assembly_path}")
        return 0
    elif target == "amiga":
        if not is_amiga_boot_source(generated.assembly):
            raise ValueError(
                "Das Amiga-Backend erzeugte kein eigenständig bootfähiges Programm."
            )
        assembled = assemble_amiga_boot_source(
            generated.assembly, filename=assembly_path.name,
            cpu_model=args.amiga_cpu, fpu_model=args.amiga_fpu,
        )
        image = assembled.adf
        default_output = source_path.with_suffix(".adf")
    else:
        assembled = assemble_mos6510_source(
            generated.assembly, filename=assembly_path.name
        )
        image = assembled.prg
        default_output = source_path.with_suffix(".prg")

    output_path = (
        args.output.expanduser().resolve() if args.output is not None
        else default_output.resolve()
    )
    _write_cli_file(output_path, image)
    for note in getattr(generated, "notes", ()):
        print(note, file=sys.stderr)
    for warning in getattr(generated, "warnings", ()):
        print(warning, file=sys.stderr)
    print(f"{target.upper()}: {source_path} -> {assembly_path} -> {output_path}")
    return 0

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_arguments(argv)
    if args.archive_coff32 is not None:
        if args.directory is not None:
            print("Fehler: Kein GUI-Arbeitsverzeichnis bei --archive-coff32.", file=sys.stderr)
            return 2
        if not args.object:
            print("Fehler: --archive-coff32 benötigt mindestens ein --object.", file=sys.stderr)
            return 2
        try:
            target = args.archive_coff32.expanduser().resolve()
            members = []
            for path_value in args.object:
                path = path_value.expanduser().resolve()
                members.append((path.name, path.read_bytes()))
            _write_cli_file(target, create_coff32_archive(members))
            print(f"COFF32 ARCHIVE: {len(members)} Objekt(e) -> {target}")
            return 0
        except Exception as exc:
            print(f"Archivfehler: {exc}", file=sys.stderr)
            return 1
    if args.link_pe32 is not None:
        if args.directory is not None:
            print("Fehler: Kein GUI-Arbeitsverzeichnis bei --link-pe32.", file=sys.stderr)
            return 2
        if not args.object:
            print("Fehler: --link-pe32 benötigt mindestens ein --object.", file=sys.stderr)
            return 2
        try:
            target = args.link_pe32.expanduser().resolve()
            is_dll = target.suffix.casefold() == ".dll"
            program = link_coff32_inputs(
                [item.expanduser().resolve() for item in args.object],
                entry_symbol="__d64_dll_entry" if is_dll else "_start",
                gui=True,
                dll=is_dll,
                dll_name=target.name if is_dll else None,
            )
            _write_cli_file(target, program.executable)
            print(f"PE32 LINK: {len(args.object)} Eingabe(n) -> {target}")
            return 0
        except Exception as exc:
            print(f"Linkerfehler: {exc}", file=sys.stderr)
            return 1
    if args.write_pui is not None:
        if args.directory is not None:
            print(
                "Fehler: Das GUI-Arbeitsverzeichnis darf nicht zusammen mit "
                "--write-pui angegeben werden.",
                file=sys.stderr,
            )
            return 2
        try:
            from c64pascal import write_pascal_unit_interface
            source_path = args.write_pui.expanduser().resolve()
            destination = write_pascal_unit_interface(
                source_path,
                predefined_macros=_cli_defines(args.define),
            )
            print(f"PUI: {source_path} -> {destination}")
            return 0
        except Exception as exc:
            print(f"Compilerfehler: {exc}", file=sys.stderr)
            return 1
    if any((
        args.write_amiga is not None,
        args.write_c64 is not None,
        args.write_pe32 is not None,
        args.write_coff32 is not None,
    )):
        if args.directory is not None:
            print(
                "Fehler: Das GUI-Arbeitsverzeichnis darf nicht zusammen mit "
                "einem Compiler-Ausgabeziel angegeben werden.",
                file=sys.stderr,
            )
            return 2
        try:
            return _compile_cli(args)
        except Exception as exc:
            print(f"Compilerfehler: {exc}", file=sys.stderr)
            return 1
    if args.output is not None or args.include_path or args.define or args.object:
        print(
            "Fehler: -o, -Fi/--include-path, -D und --object benötigen "
            "ein Compiler-, Archiv- oder Linkerziel.",
            file=sys.stderr,
        )
        return 2
    return run_gui(args.directory)

if __name__ == "__main__":
    raise SystemExit(main())

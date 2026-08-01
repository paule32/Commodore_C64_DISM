#!/usr/bin/env python3
"""
Zeigt Informationen und das Inhaltsverzeichnis eines Commodore-D64-Images an.

Aufruf:
    python d64info.py IMAGE.d64
    python d64info.py IMAGE.d64 --bam
    python d64info.py IMAGE.d64 --chains
    python d64info.py IMAGE.d64 --startup
    python d64info.py IMAGE.d64 --startup --verbose
    python d64info.py IMAGE.d64 --extract-prg
    python d64info.py IMAGE.d64 --analyze-prg
    python d64info.py IMAGE.d64 --disassemble
    python d64info.py IMAGE.d64 --image-ram --vice x64sc.exe
    python d64info.py IMAGE.d64 --disassemble-code --vice x64sc.exe
"""

from __future__ import annotations

import argparse
import hashlib
import io
import math
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
from collections import deque
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TextIO


SECTOR_SIZE = 256
DIRECTORY_TRACK = 18
BAM_SECTOR = 0
DIRECTORY_ENTRIES_PER_SECTOR = 8

FILE_TYPES = {
    0: "DEL",
    1: "SEQ",
    2: "PRG",
    3: "USR",
    4: "REL",
}

DALEK_ATTACK_TSM_SHA256 = (
    "62bca1663b6cd0cfcf3b53bbcd8073592c7e955ab0edf1216fcb20f1bcba69d5"
)

DALEK_INTRO_SHA256 = (
    "cb2f84b45fe73257d45888ff39fa9fc76883cc9b5241c5770efd7abf3ba91170"
)

# Diese Fingerabdrücke kennzeichnen exakt die sieben nummerierten
# DALEK-ATTACK-Dateien aus dem untersuchten Diskettenabbild. Das Profil ist
# absichtlich prüfsummengebunden: Aussagen über ihre gemeinsame Struktur
# werden dadurch nicht auf zufällig ähnlich benannte fremde Dateien
# übertragen.
DALEK_NUMBERED_PRG_PROFILES = {
    "b9b99a73068935fe44f7c9979dd68421111a5123519c9f32092cfef537cd5ac9": "00",
    "8ebe9845f93da5e74cf9d18a56dd7c012e9a7e6f60194e56a9b84a45cc3ec0b7": "01",
    "28fe538deb53b0523b27aa5958bad1351d733f480db40f808797abe25a6fc961": "02",
    "6454c8b3b2cdbaa99ab35e2061eaf14026a70d83d5dc09de38f4212fe7e895ac": "03",
    "adb1d90aea7d91dbc876465efd836efd14224393ef77ad5a92d7876606dfabf8": "04",
    "600e76c2b73f4ba697092121c2836dccac19c7c8c940dfb49d233f3132201800": "05",
    "27fdb95577a98d958c41d04cc45822b2151e13be58325cfa3579949248904b96": "06",
}

WINDOWS_INVALID_FILENAME_CHARS = frozenset('<>:"/\\|?*')
WINDOWS_RESERVED_FILENAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)

# Offizielle NMOS-6502/6510-Opcodes. Undokumentierte Opcodes werden im
# Listing absichtlich als einzelne .byte-Direktiven ausgegeben. Dadurch bleibt
# die Adressausrichtung erhalten, ohne deren je nach Prozessorrevision
# abweichendes Verhalten als gesicherte Instruktion darzustellen.
MOS6510_OPCODES: dict[int, tuple[str, str]] = {
    0x00: ("BRK", "imp"),
    0x01: ("ORA", "izx"),
    0x05: ("ORA", "zp"),
    0x06: ("ASL", "zp"),
    0x08: ("PHP", "imp"),
    0x09: ("ORA", "imm"),
    0x0A: ("ASL", "acc"),
    0x0D: ("ORA", "abs"),
    0x0E: ("ASL", "abs"),
    0x10: ("BPL", "rel"),
    0x11: ("ORA", "izy"),
    0x15: ("ORA", "zpx"),
    0x16: ("ASL", "zpx"),
    0x18: ("CLC", "imp"),
    0x19: ("ORA", "absy"),
    0x1D: ("ORA", "absx"),
    0x1E: ("ASL", "absx"),
    0x20: ("JSR", "abs"),
    0x21: ("AND", "izx"),
    0x24: ("BIT", "zp"),
    0x25: ("AND", "zp"),
    0x26: ("ROL", "zp"),
    0x28: ("PLP", "imp"),
    0x29: ("AND", "imm"),
    0x2A: ("ROL", "acc"),
    0x2C: ("BIT", "abs"),
    0x2D: ("AND", "abs"),
    0x2E: ("ROL", "abs"),
    0x30: ("BMI", "rel"),
    0x31: ("AND", "izy"),
    0x35: ("AND", "zpx"),
    0x36: ("ROL", "zpx"),
    0x38: ("SEC", "imp"),
    0x39: ("AND", "absy"),
    0x3D: ("AND", "absx"),
    0x3E: ("ROL", "absx"),
    0x40: ("RTI", "imp"),
    0x41: ("EOR", "izx"),
    0x45: ("EOR", "zp"),
    0x46: ("LSR", "zp"),
    0x48: ("PHA", "imp"),
    0x49: ("EOR", "imm"),
    0x4A: ("LSR", "acc"),
    0x4C: ("JMP", "abs"),
    0x4D: ("EOR", "abs"),
    0x4E: ("LSR", "abs"),
    0x50: ("BVC", "rel"),
    0x51: ("EOR", "izy"),
    0x55: ("EOR", "zpx"),
    0x56: ("LSR", "zpx"),
    0x58: ("CLI", "imp"),
    0x59: ("EOR", "absy"),
    0x5D: ("EOR", "absx"),
    0x5E: ("LSR", "absx"),
    0x60: ("RTS", "imp"),
    0x61: ("ADC", "izx"),
    0x65: ("ADC", "zp"),
    0x66: ("ROR", "zp"),
    0x68: ("PLA", "imp"),
    0x69: ("ADC", "imm"),
    0x6A: ("ROR", "acc"),
    0x6C: ("JMP", "ind"),
    0x6D: ("ADC", "abs"),
    0x6E: ("ROR", "abs"),
    0x70: ("BVS", "rel"),
    0x71: ("ADC", "izy"),
    0x75: ("ADC", "zpx"),
    0x76: ("ROR", "zpx"),
    0x78: ("SEI", "imp"),
    0x79: ("ADC", "absy"),
    0x7D: ("ADC", "absx"),
    0x7E: ("ROR", "absx"),
    0x81: ("STA", "izx"),
    0x84: ("STY", "zp"),
    0x85: ("STA", "zp"),
    0x86: ("STX", "zp"),
    0x88: ("DEY", "imp"),
    0x8A: ("TXA", "imp"),
    0x8C: ("STY", "abs"),
    0x8D: ("STA", "abs"),
    0x8E: ("STX", "abs"),
    0x90: ("BCC", "rel"),
    0x91: ("STA", "izy"),
    0x94: ("STY", "zpx"),
    0x95: ("STA", "zpx"),
    0x96: ("STX", "zpy"),
    0x98: ("TYA", "imp"),
    0x99: ("STA", "absy"),
    0x9A: ("TXS", "imp"),
    0x9D: ("STA", "absx"),
    0xA0: ("LDY", "imm"),
    0xA1: ("LDA", "izx"),
    0xA2: ("LDX", "imm"),
    0xA4: ("LDY", "zp"),
    0xA5: ("LDA", "zp"),
    0xA6: ("LDX", "zp"),
    0xA8: ("TAY", "imp"),
    0xA9: ("LDA", "imm"),
    0xAA: ("TAX", "imp"),
    0xAC: ("LDY", "abs"),
    0xAD: ("LDA", "abs"),
    0xAE: ("LDX", "abs"),
    0xB0: ("BCS", "rel"),
    0xB1: ("LDA", "izy"),
    0xB4: ("LDY", "zpx"),
    0xB5: ("LDA", "zpx"),
    0xB6: ("LDX", "zpy"),
    0xB8: ("CLV", "imp"),
    0xB9: ("LDA", "absy"),
    0xBA: ("TSX", "imp"),
    0xBC: ("LDY", "absx"),
    0xBD: ("LDA", "absx"),
    0xBE: ("LDX", "absy"),
    0xC0: ("CPY", "imm"),
    0xC1: ("CMP", "izx"),
    0xC4: ("CPY", "zp"),
    0xC5: ("CMP", "zp"),
    0xC6: ("DEC", "zp"),
    0xC8: ("INY", "imp"),
    0xC9: ("CMP", "imm"),
    0xCA: ("DEX", "imp"),
    0xCC: ("CPY", "abs"),
    0xCD: ("CMP", "abs"),
    0xCE: ("DEC", "abs"),
    0xD0: ("BNE", "rel"),
    0xD1: ("CMP", "izy"),
    0xD5: ("CMP", "zpx"),
    0xD6: ("DEC", "zpx"),
    0xD8: ("CLD", "imp"),
    0xD9: ("CMP", "absy"),
    0xDD: ("CMP", "absx"),
    0xDE: ("DEC", "absx"),
    0xE0: ("CPX", "imm"),
    0xE1: ("SBC", "izx"),
    0xE4: ("CPX", "zp"),
    0xE5: ("SBC", "zp"),
    0xE6: ("INC", "zp"),
    0xE8: ("INX", "imp"),
    0xE9: ("SBC", "imm"),
    0xEA: ("NOP", "imp"),
    0xEC: ("CPX", "abs"),
    0xED: ("SBC", "abs"),
    0xEE: ("INC", "abs"),
    0xF0: ("BEQ", "rel"),
    0xF1: ("SBC", "izy"),
    0xF5: ("SBC", "zpx"),
    0xF6: ("INC", "zpx"),
    0xF8: ("SED", "imp"),
    0xF9: ("SBC", "absy"),
    0xFD: ("SBC", "absx"),
    0xFE: ("INC", "absx"),
}

MOS6510_MODE_SIZE = {
    "imp": 1,
    "acc": 1,
    "imm": 2,
    "zp": 2,
    "zpx": 2,
    "zpy": 2,
    "izx": 2,
    "izy": 2,
    "rel": 2,
    "abs": 3,
    "absx": 3,
    "absy": 3,
    "ind": 3,
}


# Binärer VICE-Monitor, API-Version 2.
VICE_API_VERSION = 0x02
VICE_STX = 0x02
VICE_EVENT_REQUEST_ID = 0xFFFFFFFF

VICE_CMD_MEMORY_GET = 0x01
VICE_CMD_CHECKPOINT_SET = 0x12
VICE_CMD_DUMP = 0x41
VICE_CMD_EXIT = 0xAA
VICE_CMD_QUIT = 0xBB
VICE_CMD_PING = 0x81
VICE_CMD_BANKS_AVAILABLE = 0x82
VICE_CMD_AUTOSTART = 0xDD

VICE_RESPONSE_CHECKPOINT = 0x11
VICE_RESPONSE_STOPPED = 0x62
VICE_RESPONSE_RESUMED = 0x63
VICE_RESPONSE_JAM = 0x61

VICE_MEMSPACE_MAIN = 0x00
VICE_CHECK_EXEC = 0x04

RAM_DUMP_SIZE = 0x10000

DALEK_RAM_ENTRY_SIGNATURE = bytes.fromhex(
    "A2 17 B5 01 9D 00 10 CA 10 F8 A9 06 A2 54 A0 48"
)

RAM_BRANCH_MNEMONICS = {
    "BCC", "BCS", "BEQ", "BMI", "BNE", "BPL", "BVC", "BVS",
}

DALEK_RAM_SYMBOLS = {
    0x0100: "game_depacker",
    0x0196: "game_depacker_done",
    0x0810: "game_stage2_entry",
    0x1021: "music_play",
    0x1048: "music_init",
    0x1D70: "intro_fire_exit",
    0x4100: "intro_start",
    0x41EE: "intro_irq_dispatch",
    0x422E: "irq_top",
    0x423E: "fire_pressed",
    0x4241: "irq_middle",
    0x4281: "irq_bottom",
    0x42DA: "vic_restore",
    0x44D4: "intro_routine_44d4",
    0x458A: "intro_routine_458a",
    0x459D: "intro_routine_459d",
    0x464C: "intro_routine_464c",
    0x46DC: "intro_main",
    0x4786: "delay_short",
    0x478C: "delay_long",
    0x4793: "color_scroll",
    0x481B: "set_border_background",
    0x4822: "scroll_divider",
    0x4835: "reset_raster_table",
    0x4842: "reset_intro_state",
}

RAM_HARDWARE_SYMBOLS = {
    0xD011: "VIC_CTRL1",
    0xD012: "VIC_RASTER",
    0xD016: "VIC_CTRL2",
    0xD018: "VIC_MEMPTR",
    0xD019: "VIC_IRQ_FLAGS",
    0xD01A: "VIC_IRQ_MASK",
    0xD020: "VIC_BORDER",
    0xD021: "VIC_BACKGROUND0",
    0xD022: "VIC_BACKGROUND1",
    0xD023: "VIC_BACKGROUND2",
    0xD400: "SID_BASE",
    0xD417: "SID_FILTER",
    0xD418: "SID_VOLUME",
    0xDC01: "CIA1_PORT_B",
    0xDC0D: "CIA1_IRQ_CONTROL",
    0xFFFA: "NMI_VECTOR",
    0xFFFE: "IRQ_VECTOR",
}


class D64Error(Exception):
    """Fehler beim Lesen oder Interpretieren eines D64-Images."""


@dataclass(frozen=True)
class ViceMonitorResponse:
    response_type: int
    error: int
    request_id: int
    body: bytes


@dataclass(frozen=True)
class RamInstruction:
    address: int
    raw: bytes
    mnemonic: str
    mode: str


class TeeTextWriter:
    """
    Schreibt jeden Text identisch in mehrere Textausgaben.

    Bei ``--startup`` wird damit nicht nur ein vorab ausgewählter Teilbericht
    gespeichert. Jede normale Konsolenausgabe des vollständigen Programmlaufs
    gelangt zugleich in ``startup_info.txt``.
    """

    def __init__(self, *streams: TextIO):
        self.streams = streams

    def write(self, text: str) -> int:
        for stream in self.streams:
            stream.write(text)
        return len(text)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def sectors_on_track(track: int) -> int:
    """Liefert die Anzahl der Sektoren einer 1541-Spur."""
    if 1 <= track <= 17:
        return 21
    if 18 <= track <= 24:
        return 19
    if 25 <= track <= 30:
        return 18
    if 31 <= track <= 42:
        return 17
    raise D64Error(f"Ungültige Spur: {track}")


def total_sectors(track_count: int) -> int:
    return sum(sectors_on_track(track) for track in range(1, track_count + 1))


def petscii_to_text(data: bytes, *, strip_padding: bool = True) -> str:
    """
    Wandelt die für D64-Namen üblichen PETSCII-Zeichen lesbar in Text um.

    Grafische PETSCII-Zeichen, für die es keine eindeutige Konsolendarstellung
    gibt, werden als Punkt ausgegeben.
    """
    chars: list[str] = []

    for value in data:
        if value == 0xA0:
            chars.append(" ")
        elif 0x20 <= value <= 0x7E:
            chars.append(chr(value))
        elif 0xC1 <= value <= 0xDA:
            chars.append(chr(value - 0x80))
        else:
            chars.append(".")

    text = "".join(chars)
    return text.rstrip(" ") if strip_padding else text


@dataclass(frozen=True)
class Geometry:
    tracks: int
    sectors: int
    data_size: int
    has_error_table: bool

    @classmethod
    def from_image_size(cls, image_size: int) -> "Geometry":
        matches: list[Geometry] = []

        for tracks in range(35, 43):
            sectors = total_sectors(tracks)
            data_size = sectors * SECTOR_SIZE

            if image_size == data_size:
                matches.append(cls(tracks, sectors, data_size, False))
            elif image_size == data_size + sectors:
                matches.append(cls(tracks, sectors, data_size, True))

        if not matches:
            raise D64Error(
                f"Nicht unterstützte D64-Größe: {image_size} Bytes. "
                "Erwartet wird ein 35- bis 42-Spur-Image, optional mit "
                "einer Fehlerbyte-Tabelle."
            )

        return matches[0]


@dataclass(frozen=True)
class DirectoryEntry:
    file_type_byte: int
    start_track: int
    start_sector: int
    filename: str
    blocks: int
    directory_track: int
    directory_sector: int
    slot: int

    @property
    def type_name(self) -> str:
        return FILE_TYPES.get(self.file_type_byte & 0x07, "???")

    @property
    def is_closed(self) -> bool:
        return bool(self.file_type_byte & 0x80)

    @property
    def is_locked(self) -> bool:
        return bool(self.file_type_byte & 0x40)

    @property
    def type_display(self) -> str:
        prefix = "" if self.is_closed else "*"
        suffix = "<" if self.is_locked else ""
        return f"{prefix}{self.type_name}{suffix}"


@dataclass(frozen=True)
class FileChain:
    sectors: tuple[tuple[int, int], ...]
    data_bytes: int
    error: str | None = None


@dataclass(frozen=True)
class BasicSysEntry:
    line_number: int
    address: int


@dataclass(frozen=True)
class PrgAnalysis:
    filename: str
    c64_filename: str
    file_size: int
    payload_size: int
    load_address: int | None
    loaded_end: int | None
    sys_entry: BasicSysEntry | None
    sha256: str
    is_known_dalek_attack_tsm: bool


@dataclass(frozen=True)
class PayloadStatistics:
    entropy: float
    unique_byte_values: int
    printable_ascii_percent: float
    zero_percent: float
    ff_percent: float
    longest_equal_byte_run: int


@dataclass(frozen=True)
class BamTrack:
    track: int
    free_count: int
    bitmap_free_count: int
    total_count: int
    free_sectors: tuple[int, ...]

    @property
    def is_consistent(self) -> bool:
        return self.free_count == self.bitmap_free_count


def windows_safe_filename(filename: str, *, fallback: str = "UNNAMED") -> str:
    """Bereinigt einen C64-Dateinamen für ein Windows-Dateisystem."""
    safe_name = "".join(
        "_"
        if character in WINDOWS_INVALID_FILENAME_CHARS
        or ord(character) < 32
        else character
        for character in filename
    ).rstrip(" .")

    if not safe_name or safe_name in {".", ".."}:
        safe_name = fallback

    device_name = safe_name.split(".", 1)[0].upper()
    if device_name in WINDOWS_RESERVED_FILENAMES:
        safe_name = f"_{safe_name}"

    return safe_name


def unique_prg_filename(filename: str, used_names: set[str]) -> str:
    """Erzeugt einen innerhalb des Zielordners eindeutigen PRG-Dateinamen."""
    base_name = windows_safe_filename(filename)
    candidate = f"{base_name}.prg"
    suffix = 2

    while candidate.casefold() in used_names:
        candidate = f"{base_name} ({suffix}).prg"
        suffix += 1

    used_names.add(candidate.casefold())
    return candidate


class D64Image:
    def __init__(self, path: Path):
        self.path = path

        try:
            self.raw = path.read_bytes()
        except OSError as exc:
            raise D64Error(f"Datei kann nicht gelesen werden: {exc}") from exc

        self.geometry = Geometry.from_image_size(len(self.raw))
        self.data = self.raw[: self.geometry.data_size]
        self.error_table = (
            self.raw[self.geometry.data_size :]
            if self.geometry.has_error_table
            else b""
        )

    def sector_offset(self, track: int, sector: int) -> int:
        if not 1 <= track <= self.geometry.tracks:
            raise D64Error(
                f"Spur {track} liegt außerhalb des Images "
                f"(1..{self.geometry.tracks})."
            )

        sector_count = sectors_on_track(track)
        if not 0 <= sector < sector_count:
            raise D64Error(
                f"Sektor {track}/{sector} ist ungültig; "
                f"Spur {track} besitzt die Sektoren 0..{sector_count - 1}."
            )

        preceding = sum(
            sectors_on_track(number) for number in range(1, track)
        )
        return (preceding + sector) * SECTOR_SIZE

    def read_sector(self, track: int, sector: int) -> bytes:
        offset = self.sector_offset(track, sector)
        return self.data[offset : offset + SECTOR_SIZE]

    @property
    def bam(self) -> bytes:
        return self.read_sector(DIRECTORY_TRACK, BAM_SECTOR)

    @property
    def disk_name(self) -> str:
        return petscii_to_text(self.bam[0x90:0xA0])

    @property
    def disk_id(self) -> str:
        return petscii_to_text(self.bam[0xA2:0xA4], strip_padding=False)

    @property
    def dos_type(self) -> str:
        return petscii_to_text(self.bam[0xA5:0xA7], strip_padding=False)

    @property
    def header_suffix(self) -> str:
        return petscii_to_text(self.bam[0xA2:0xA7])

    @property
    def dos_version(self) -> str:
        return petscii_to_text(self.bam[2:3], strip_padding=False)

    def directory_entries(
        self, *, include_deleted: bool = False
    ) -> list[DirectoryEntry]:
        entries: list[DirectoryEntry] = []
        track = self.bam[0]
        sector = self.bam[1]
        visited: set[tuple[int, int]] = set()

        while track != 0:
            location = (track, sector)
            if location in visited:
                raise D64Error(
                    f"Zyklische Verzeichniskette bei Spur/Sektor "
                    f"{track}/{sector}."
                )
            visited.add(location)

            directory_sector = self.read_sector(track, sector)

            for slot in range(DIRECTORY_ENTRIES_PER_SECTOR):
                # Ein Verzeichniseintrag belegt jeweils 32 Byte. Bei Eintrag 0
                # werden dessen Bytes 0/1 zugleich als Verkettung des gesamten
                # Verzeichnissektors verwendet; der Dateityp beginnt bei +2.
                offset = slot * 32
                file_type_byte = directory_sector[offset + 2]
                start_track = directory_sector[offset + 3]
                start_sector = directory_sector[offset + 4]

                if (file_type_byte & 0x07) == 0 and not include_deleted:
                    continue

                filename = petscii_to_text(
                    directory_sector[offset + 5 : offset + 21]
                )
                blocks = int.from_bytes(
                    directory_sector[offset + 30 : offset + 32],
                    "little",
                )

                if (
                    file_type_byte == 0
                    and start_track == 0
                    and blocks == 0
                    and not filename
                ):
                    continue

                entries.append(
                    DirectoryEntry(
                        file_type_byte=file_type_byte,
                        start_track=start_track,
                        start_sector=start_sector,
                        filename=filename,
                        blocks=blocks,
                        directory_track=track,
                        directory_sector=sector,
                        slot=slot,
                    )
                )

            track = directory_sector[0]
            sector = directory_sector[1]

        return entries

    def read_file_chain(self, entry: DirectoryEntry) -> FileChain:
        if entry.start_track == 0:
            return FileChain((), 0)

        track = entry.start_track
        sector = entry.start_sector
        visited: set[tuple[int, int]] = set()
        chain: list[tuple[int, int]] = []
        data_bytes = 0

        try:
            while track != 0:
                location = (track, sector)
                if location in visited:
                    return FileChain(
                        tuple(chain),
                        data_bytes,
                        f"Zyklus bei {track}/{sector}",
                    )

                visited.add(location)
                chain.append(location)
                block = self.read_sector(track, sector)
                next_track = block[0]
                next_sector = block[1]

                if next_track == 0:
                    # Im letzten Dateisektor bezeichnet Byte 1 die Anzahl der
                    # belegten Bytes einschließlich dieses Zählbytes.
                    data_bytes += max(0, min(next_sector - 1, 254))
                    break

                data_bytes += 254
                track = next_track
                sector = next_sector
        except D64Error as exc:
            return FileChain(tuple(chain), data_bytes, str(exc))

        return FileChain(tuple(chain), data_bytes)

    def read_file_data(self, entry: DirectoryEntry) -> bytes:
        """Liest die Nutzbytes einer Datei in der Reihenfolge ihrer Sektorkette."""
        if entry.start_track == 0:
            return b""

        track = entry.start_track
        sector = entry.start_sector
        visited: set[tuple[int, int]] = set()
        result = bytearray()

        while track != 0:
            location = (track, sector)
            if location in visited:
                raise D64Error(
                    f"Zyklische Dateikette bei Spur/Sektor {track}/{sector}."
                )

            visited.add(location)
            block = self.read_sector(track, sector)
            next_track = block[0]
            next_sector = block[1]

            if next_track == 0:
                used_bytes = max(0, min(next_sector - 1, 254))
                result.extend(block[2 : 2 + used_bytes])
                break

            result.extend(block[2:])
            track = next_track
            sector = next_sector

        return bytes(result)

    def bam_tracks(self) -> list[BamTrack]:
        """
        Liest die Standard-BAM für die Spuren 1 bis 35.

        Das klassische 1541-BAM-Schema besitzt im BAM-Sektor nur Einträge für
        35 Spuren. Erweiterte Images können zusätzliche BAM-Daten in einem
        herstellerspezifischen Format führen.
        """
        tracks: list[BamTrack] = []

        for track in range(1, min(self.geometry.tracks, 35) + 1):
            offset = 4 + (track - 1) * 4
            free_count = self.bam[offset]
            bitmap = int.from_bytes(self.bam[offset + 1 : offset + 4], "little")
            track_sector_count = sectors_on_track(track)
            free_sectors = tuple(
                sector
                for sector in range(track_sector_count)
                if bitmap & (1 << sector)
            )
            tracks.append(
                BamTrack(
                    track=track,
                    free_count=free_count,
                    bitmap_free_count=len(free_sectors),
                    total_count=track_sector_count,
                    free_sectors=free_sectors,
                )
            )

        return tracks

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw).hexdigest()


def find_basic_sys_entry(
    program_data: bytes,
    load_address: int,
) -> BasicSysEntry | None:
    """
    Sucht in einem tokenisierten C64-BASIC-Programm nach dem ersten SYS.

    Die Suche folgt den Zeilenzeigern und akzeptiert eine direkt hinter dem
    SYS-Token ($9E) stehende dezimale Adresse. Komplexe BASIC-Ausdrücke wie
    ``SYS PEEK(43)+256*PEEK(44)`` können nicht statisch ausgewertet werden.
    """
    if load_address != 0x0801:
        return None

    offset = 0
    visited: set[int] = set()

    while offset + 4 <= len(program_data):
        current_address = load_address + offset
        if current_address in visited:
            break
        visited.add(current_address)

        next_address = int.from_bytes(
            program_data[offset : offset + 2],
            "little",
        )
        if next_address == 0:
            break

        line_number = int.from_bytes(
            program_data[offset + 2 : offset + 4],
            "little",
        )
        line_end = program_data.find(b"\x00", offset + 4)
        if line_end < 0:
            break

        line = program_data[offset + 4 : line_end]
        in_quotes = False

        for position, value in enumerate(line):
            if value == 0x22:
                in_quotes = not in_quotes
                continue
            if in_quotes or value != 0x9E:
                continue

            number_start = position + 1
            while number_start < len(line) and line[number_start] == 0x20:
                number_start += 1

            number_end = number_start
            while (
                number_end < len(line)
                and 0x30 <= line[number_end] <= 0x39
            ):
                number_end += 1

            if number_end > number_start:
                return BasicSysEntry(
                    line_number=line_number,
                    address=int(line[number_start:number_end].decode("ascii")),
                )

        next_offset = next_address - load_address
        if next_offset <= offset or next_offset >= len(program_data):
            break
        offset = next_offset

    return None


def german_number(value: int) -> str:
    """Formatiert eine Ganzzahl mit deutschem Tausenderpunkt."""
    return f"{value:,}".replace(",", ".")


def calculate_payload_statistics(payload: bytes) -> PayloadStatistics:
    """Berechnet reproduzierbare Strukturwerte für die PRG-Nutzdaten."""
    if not payload:
        return PayloadStatistics(
            entropy=0.0,
            unique_byte_values=0,
            printable_ascii_percent=0.0,
            zero_percent=0.0,
            ff_percent=0.0,
            longest_equal_byte_run=0,
        )

    counts = [0] * 256
    longest_run = 1
    current_run = 1

    for index, value in enumerate(payload):
        counts[value] += 1
        if index > 0 and value == payload[index - 1]:
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 1

    size = len(payload)
    entropy = -sum(
        probability * math.log2(probability)
        for count in counts
        if count
        for probability in (count / size,)
    )
    printable = sum(
        count
        for value, count in enumerate(counts)
        if 0x20 <= value <= 0x7E
    )

    return PayloadStatistics(
        entropy=entropy,
        unique_byte_values=sum(count > 0 for count in counts),
        printable_ascii_percent=printable * 100.0 / size,
        zero_percent=counts[0x00] * 100.0 / size,
        ff_percent=counts[0xFF] * 100.0 / size,
        longest_equal_byte_run=longest_run,
    )


def hexadecimal_preview(data: bytes, *, length: int = 32) -> str:
    """Formatiert den Anfang eines Binärblocks als kompakte Hex-Folge."""
    preview = data[:length]
    result = " ".join(f"{value:02X}" for value in preview)
    if len(data) > length:
        result += " ..."
    return result or "(leer)"


def mos6510_operand(
    mode: str,
    operand: bytes,
    address: int,
    *,
    labels: set[int],
) -> str:
    """Formatiert den Operanden einer offiziellen 6502/6510-Instruktion."""
    if mode == "imp":
        return ""
    if mode == "acc":
        return "A"

    value8 = operand[0]
    if mode == "imm":
        return f"#$%02X" % value8
    if mode == "zp":
        return f"$%02X" % value8
    if mode == "zpx":
        return f"$%02X,X" % value8
    if mode == "zpy":
        return f"$%02X,Y" % value8
    if mode == "izx":
        return f"($%02X,X)" % value8
    if mode == "izy":
        return f"($%02X),Y" % value8
    if mode == "rel":
        displacement = value8 if value8 < 0x80 else value8 - 0x100
        target = (address + 2 + displacement) & 0xFFFF
        return f"L{target:04X}" if target in labels else f"${target:04X}"

    value16 = int.from_bytes(operand[:2], "little")
    target = f"L{value16:04X}" if value16 in labels else f"${value16:04X}"
    if mode == "abs":
        return target
    if mode == "absx":
        return f"{target},X"
    if mode == "absy":
        return f"{target},Y"
    if mode == "ind":
        return f"({target})"
    raise ValueError(f"Unbekannter 6510-Adressierungsmodus: {mode}")


def disassemble_mos6510_region(data: bytes, start_address: int) -> list[str]:
    """
    Disassembliert einen zusammenhängenden Bereich linear.

    Nicht dokumentierte Opcodes bleiben einzelne Bytes. Das Listing ist damit
    verlustfrei und verschiebt nach einem unbekannten Opcode keine Folgeadresse.
    """
    records: list[tuple[int, bytes, str | None, str | None]] = []
    offset = 0

    while offset < len(data):
        address = (start_address + offset) & 0xFFFF
        opcode = data[offset]
        operation = MOS6510_OPCODES.get(opcode)

        if operation is None:
            records.append((address, data[offset : offset + 1], None, None))
            offset += 1
            continue

        mnemonic, mode = operation
        size = MOS6510_MODE_SIZE[mode]
        if offset + size > len(data):
            records.append((address, data[offset:], None, None))
            break

        instruction = data[offset : offset + size]
        records.append((address, instruction, mnemonic, mode))
        offset += size

    instruction_addresses = {
        address
        for address, _, mnemonic, _ in records
        if mnemonic is not None
    }
    labels: set[int] = set()

    for address, instruction, mnemonic, mode in records:
        if mnemonic is None or mode is None:
            continue
        if mode == "rel":
            displacement = (
                instruction[1]
                if instruction[1] < 0x80
                else instruction[1] - 0x100
            )
            target = (address + 2 + displacement) & 0xFFFF
            if target in instruction_addresses:
                labels.add(target)
        elif mnemonic in {"JMP", "JSR"} and mode == "abs":
            target = int.from_bytes(instruction[1:3], "little")
            if target in instruction_addresses:
                labels.add(target)

    lines: list[str] = []
    for address, instruction, mnemonic, mode in records:
        if address in labels:
            lines.append(f"L{address:04X}:")

        byte_text = " ".join(f"{value:02X}" for value in instruction)
        if mnemonic is None or mode is None:
            statement = f".byte ${instruction[0]:02X}"
            comment = "undokumentierter Opcode oder unvollständiges Datenbyte"
        else:
            operand = mos6510_operand(
                mode,
                instruction[1:],
                address,
                labels=labels,
            )
            statement = mnemonic if not operand else f"{mnemonic} {operand}"
            comment = ""

        line = f"    {statement:<18} ; ${address:04X}: {byte_text:<8}"
        if comment:
            line += f"  {comment}"
        lines.append(line.rstrip())

    return lines


def mos6510_data_lines(data: bytes, start_address: int) -> list[str]:
    """Formatiert Binärdaten verlustfrei in Zeilen zu je 16 Bytes."""
    lines: list[str] = []
    for offset in range(0, len(data), 16):
        chunk = data[offset : offset + 16]
        address = (start_address + offset) & 0xFFFF
        values = ", ".join(f"${value:02X}" for value in chunk)
        lines.append(f"    .byte {values:<79} ; ${address:04X}")
    return lines


def parse_address(text: str) -> int:
    """Liest eine dezimale, 0x- oder $-hexadezimale 16-Bit-Adresse."""
    value = text.strip().lower()
    if value.startswith("$"):
        value = "0x" + value[1:]
    try:
        result = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Ungültige Adresse: {text!r}"
        ) from exc
    if not 0 <= result <= 0xFFFF:
        raise argparse.ArgumentTypeError(
            f"Adresse außerhalb 16 Bit: {text!r}"
        )
    return result


def receive_vice_bytes(sock: socket.socket, count: int) -> bytes:
    """Empfängt exakt ``count`` Bytes vom binären VICE-Monitor."""
    result = bytearray()
    while len(result) < count:
        chunk = sock.recv(count - len(result))
        if not chunk:
            raise D64Error(
                "VICE hat die binäre Monitorverbindung geschlossen."
            )
        result.extend(chunk)
    return bytes(result)


class ViceBinaryMonitor:
    """Kleiner Client für die offizielle binäre VICE-Monitor-API."""

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.next_request_id = 1
        self.pending: deque[ViceMonitorResponse] = deque()

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def send(self, command: int, body: bytes = b"") -> int:
        request_id = self.next_request_id
        self.next_request_id += 1
        packet = (
            bytes((VICE_STX, VICE_API_VERSION))
            + struct.pack("<I", len(body))
            + struct.pack("<I", request_id)
            + bytes((command,))
            + body
        )
        self.sock.sendall(packet)
        return request_id

    def receive(self, timeout: float | None = None) -> ViceMonitorResponse:
        if timeout is not None:
            self.sock.settimeout(timeout)
        header = receive_vice_bytes(self.sock, 12)
        if header[0] != VICE_STX:
            raise D64Error(
                f"Ungültige VICE-Antwort: 0x{header[0]:02X} statt STX."
            )
        if header[1] != VICE_API_VERSION:
            raise D64Error(
                f"Nicht unterstützte VICE-Monitor-API {header[1]}; "
                f"erwartet wird {VICE_API_VERSION}."
            )

        body_length = struct.unpack_from("<I", header, 2)[0]
        return ViceMonitorResponse(
            response_type=header[6],
            error=header[7],
            request_id=struct.unpack_from("<I", header, 8)[0],
            body=receive_vice_bytes(self.sock, body_length),
        )

    def request(
        self,
        command: int,
        body: bytes = b"",
        *,
        expected_type: int | None = None,
        timeout: float = 30.0,
    ) -> ViceMonitorResponse:
        request_id = self.send(command, body)
        deadline = time.monotonic() + timeout

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise D64Error(
                    f"Zeitüberschreitung bei VICE-Befehl "
                    f"0x{command:02X}."
                )
            try:
                response = self.receive(remaining)
            except socket.timeout as exc:
                raise D64Error(
                    f"Zeitüberschreitung bei VICE-Befehl "
                    f"0x{command:02X}."
                ) from exc
            except OSError as exc:
                raise D64Error(
                    f"VICE-Verbindung bei Befehl 0x{command:02X} "
                    f"abgebrochen: {exc}"
                ) from exc
            if response.request_id != request_id:
                self.pending.append(response)
                continue
            if response.error:
                raise D64Error(
                    f"VICE meldet Fehler 0x{response.error:02X} bei "
                    f"Befehl 0x{command:02X}."
                )
            if (
                expected_type is not None
                and response.response_type != expected_type
            ):
                raise D64Error(
                    f"VICE-Antwort 0x{response.response_type:02X}; "
                    f"erwartet wurde 0x{expected_type:02X}."
                )
            return response

    def event(self, timeout: float) -> ViceMonitorResponse:
        for _ in range(len(self.pending)):
            response = self.pending.popleft()
            if response.request_id == VICE_EVENT_REQUEST_ID:
                return response
            self.pending.append(response)
        try:
            return self.receive(timeout)
        except socket.timeout as exc:
            raise D64Error(
                "Zeitüberschreitung beim Warten auf VICE."
            ) from exc
        except OSError as exc:
            raise D64Error(
                f"VICE-Verbindung beim Warten abgebrochen: {exc}"
            ) from exc

    def ping(self) -> None:
        self.request(
            VICE_CMD_PING,
            expected_type=VICE_CMD_PING,
        )

    def banks(self) -> dict[str, int]:
        response = self.request(
            VICE_CMD_BANKS_AVAILABLE,
            expected_type=VICE_CMD_BANKS_AVAILABLE,
        )
        data = response.body
        if len(data) < 2:
            raise D64Error("VICE lieferte eine unvollständige Bankliste.")

        count = struct.unpack_from("<H", data, 0)[0]
        position = 2
        result: dict[str, int] = {}

        for _ in range(count):
            if position >= len(data):
                raise D64Error("Die VICE-Bankliste ist abgeschnitten.")
            item_size = data[position]
            item_start = position + 1
            item_end = item_start + item_size
            if item_size < 3 or item_end > len(data):
                raise D64Error("Ungültiger Eintrag in der VICE-Bankliste.")

            bank_id = struct.unpack_from("<H", data, item_start)[0]
            name_length = data[item_start + 2]
            name_start = item_start + 3
            name_end = name_start + name_length
            if name_end > item_end:
                raise D64Error("Ungültiger Bankname von VICE.")
            name = data[name_start:name_end].decode("ascii", "replace")
            result[name.lower()] = bank_id
            position = item_end

        return result

    def set_exec_breakpoint(self, address: int) -> None:
        body = struct.pack(
            "<HHBBBBB",
            address,
            address,
            1,                    # beim Treffer anhalten
            1,                    # aktiviert
            VICE_CHECK_EXEC,
            1,                    # temporär
            VICE_MEMSPACE_MAIN,
        )
        self.request(
            VICE_CMD_CHECKPOINT_SET,
            body,
            expected_type=VICE_RESPONSE_CHECKPOINT,
        )

    def autostart(self, image_path: Path, file_index: int) -> None:
        encoded = os.fsencode(str(image_path.resolve()))
        if len(encoded) > 255:
            raise D64Error(
                "Der absolute D64-Pfad ist für das VICE-Protokoll zu lang."
            )
        body = (
            bytes((1,))
            + struct.pack("<H", file_index)
            + bytes((len(encoded),))
            + encoded
        )
        self.request(
            VICE_CMD_AUTOSTART,
            body,
            expected_type=VICE_CMD_AUTOSTART,
            timeout=60.0,
        )

    def resume(self) -> None:
        self.request(
            VICE_CMD_EXIT,
            expected_type=VICE_CMD_EXIT,
        )

    def wait_for_pc(self, address: int, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        last_pc: int | None = None

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                detail = (
                    f" Letzter gemeldeter PC: ${last_pc:04X}."
                    if last_pc is not None else ""
                )
                raise D64Error(
                    f"VICE erreichte ${address:04X} nicht.{detail}"
                )

            response = self.event(remaining)
            if response.error:
                raise D64Error(
                    f"VICE-Ereignisfehler 0x{response.error:02X}."
                )
            if (
                response.response_type
                in {
                    VICE_RESPONSE_STOPPED,
                    VICE_RESPONSE_RESUMED,
                    VICE_RESPONSE_JAM,
                }
                and len(response.body) >= 2
            ):
                last_pc = struct.unpack_from("<H", response.body, 0)[0]

            if (
                response.response_type == VICE_RESPONSE_STOPPED
                and last_pc == address
            ):
                return

            if response.response_type == VICE_RESPONSE_JAM:
                raise D64Error(
                    f"Der 6510 blockierte bei ${last_pc:04X} (JAM)."
                )

    def memory_get(
        self,
        start: int,
        end: int,
        bank_id: int,
    ) -> bytes:
        body = struct.pack(
            "<BHHBH",
            0,                    # keine Seiteneffekte
            start,
            end,
            VICE_MEMSPACE_MAIN,
            bank_id,
        )
        response = self.request(
            VICE_CMD_MEMORY_GET,
            body,
            expected_type=VICE_CMD_MEMORY_GET,
            timeout=60.0,
        )
        if len(response.body) < 2:
            raise D64Error("VICE lieferte keine vollständigen RAM-Daten.")

        stated_length = struct.unpack_from("<H", response.body, 0)[0]
        if start == 0 and end == 0xFFFF and stated_length == 0:
            stated_length = RAM_DUMP_SIZE
        expected_length = ((end - start) & 0xFFFF) + 1
        memory = response.body[2:]

        if (
            stated_length != expected_length
            or len(memory) != expected_length
        ):
            raise D64Error(
                "VICE-RAM-Länge stimmt nicht: "
                f"gemeldet={stated_length}, empfangen={len(memory)}, "
                f"erwartet={expected_length}."
            )
        return memory

    def snapshot(self, filename: Path) -> None:
        encoded = os.fsencode(str(filename.resolve()))
        if len(encoded) > 255:
            raise D64Error("Der VICE-Snapshot-Pfad ist zu lang.")
        body = bytes((0, 1, len(encoded))) + encoded
        self.request(
            VICE_CMD_DUMP,
            body,
            expected_type=VICE_CMD_DUMP,
            timeout=60.0,
        )

    def quit(self) -> None:
        try:
            self.request(
                VICE_CMD_QUIT,
                expected_type=VICE_CMD_QUIT,
                timeout=5.0,
            )
        except (D64Error, OSError, socket.timeout):
            pass


def connect_vice_monitor(
    host: str,
    port: int,
    timeout: float,
) -> ViceBinaryMonitor:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        sock: socket.socket | None = None
        try:
            sock = socket.create_connection((host, port), timeout=2.0)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            monitor = ViceBinaryMonitor(sock)
            monitor.ping()
            return monitor
        except (OSError, D64Error) as exc:
            last_error = exc
            if sock is not None:
                sock.close()
            time.sleep(0.2)

    raise D64Error(
        f"Keine Verbindung zum VICE-Monitor {host}:{port}: {last_error}"
    )


def resolve_vice_executable(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        result = explicit_path.expanduser().resolve()
        if not result.is_file():
            raise D64Error(f"VICE-Programm nicht gefunden: {result}")
        return result

    executable = shutil.which("x64sc.exe") or shutil.which("x64sc")
    if executable is None:
        raise D64Error(
            "x64sc wurde nicht gefunden. Bitte --vice PFAD angeben."
        )
    return Path(executable).resolve()


def capture_complete_ram(
    image: D64Image,
    *,
    vice_path: Path | None,
    host: str,
    port: int,
    breakpoint: int,
    bank_name: str,
    file_index: int,
    connect_timeout: float,
    run_timeout: float,
    warp: bool,
    keep_vice: bool,
    connect_only: bool,
    save_snapshot: bool,
    verbose: bool,
) -> tuple[bytes, Path]:
    """Autostartet das D64 und speichert die vollständige physische RAM-Bank."""
    process: subprocess.Popen[bytes] | None = None
    monitor: ViceBinaryMonitor | None = None
    output_directory = image_output_directory(image)
    ram_path = output_directory / f"{image.path.stem}_ram.bin"

    try:
        if not connect_only:
            executable = resolve_vice_executable(vice_path)
            command = [
                str(executable),
                "-binarymonitor",
                "-binarymonitoraddress",
                f"ip4://{host}:{port}",
            ]
            if warp:
                command.append("-warp")
            process = subprocess.Popen(command)

        if verbose:
            print()
            print("VICE-RAM-Abbild")
            print(f"Monitor         : {host}:{port}")
            print(f"Haltepunkt      : ${breakpoint:04X}")

        monitor = connect_vice_monitor(host, port, connect_timeout)
        banks = monitor.banks()
        selected_bank = bank_name.lower()
        if selected_bank not in banks:
            available = ", ".join(sorted(banks))
            raise D64Error(
                f"VICE-Bank {bank_name!r} ist nicht vorhanden. "
                f"Verfügbar: {available}"
            )

        monitor.set_exec_breakpoint(breakpoint)
        monitor.autostart(image.path, file_index)
        try:
            monitor.resume()
        except D64Error:
            # Einige VICE-Versionen setzen den Lauf bereits durch AUTOSTART
            # fort; ein weiteres EXIT ist dann nicht erforderlich.
            pass

        monitor.wait_for_pc(breakpoint, run_timeout)
        memory = monitor.memory_get(
            0x0000,
            0xFFFF,
            banks[selected_bank],
        )

        try:
            ram_path.write_bytes(memory)
        except OSError as exc:
            raise D64Error(
                f"RAM-Abbild kann nicht geschrieben werden: "
                f"{ram_path}: {exc}"
            ) from exc

        if save_snapshot:
            monitor.snapshot(
                output_directory / f"{image.path.stem}.vsf"
            )

        if not keep_vice:
            monitor.quit()

        if verbose:
            print(f"RAM-Bank        : {bank_name}")
            print(f"RAM-Abbild      : {ram_path.name} ({len(memory)} Bytes)")
            print(
                f"SHA-256         : {hashlib.sha256(memory).hexdigest()}"
            )
        return memory, ram_path

    finally:
        if monitor is not None:
            monitor.close()
        if (
            process is not None
            and not keep_vice
            and process.poll() is None
        ):
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.terminate()


def ram_address_allowed(
    address: int,
    ranges: Iterable[tuple[int, int]],
) -> bool:
    return any(start <= address <= end for start, end in ranges)


def ram_branch_target(instruction: RamInstruction) -> int:
    displacement = (
        instruction.raw[1]
        if instruction.raw[1] < 0x80
        else instruction.raw[1] - 0x100
    )
    return (instruction.address + 2 + displacement) & 0xFFFF


def ram_absolute_target(instruction: RamInstruction) -> int:
    return int.from_bytes(instruction.raw[1:3], "little")


def trace_ram_code(
    memory: bytes,
    entries: Iterable[int],
    ranges: list[tuple[int, int]],
) -> dict[int, RamInstruction]:
    """
    Verfolgt statisch erreichbaren 6510-Code.

    Gegenüber einer linearen Disassemblierung werden Datentabellen nicht als
    scheinbare Befehle ausgegeben.
    """
    instructions: dict[int, RamInstruction] = {}
    occupied: set[int] = set()
    queue = deque(dict.fromkeys(entries))

    while queue:
        pc = queue.popleft() & 0xFFFF

        while ram_address_allowed(pc, ranges):
            if pc in instructions or pc in occupied:
                break
            operation = MOS6510_OPCODES.get(memory[pc])
            if operation is None:
                break
            mnemonic, mode = operation
            size = MOS6510_MODE_SIZE[mode]
            if pc + size > RAM_DUMP_SIZE:
                break
            if any((pc + offset) in occupied for offset in range(size)):
                break

            instruction = RamInstruction(
                address=pc,
                raw=memory[pc:pc + size],
                mnemonic=mnemonic,
                mode=mode,
            )
            instructions[pc] = instruction
            occupied.update(range(pc, pc + size))
            next_pc = (pc + size) & 0xFFFF

            if mnemonic in RAM_BRANCH_MNEMONICS:
                target = ram_branch_target(instruction)
                if ram_address_allowed(target, ranges):
                    queue.append(target)
                pc = next_pc
                continue

            if mnemonic == "JSR" and mode == "abs":
                target = ram_absolute_target(instruction)
                if ram_address_allowed(target, ranges):
                    queue.append(target)
                pc = next_pc
                continue

            if mnemonic == "JMP":
                if mode == "abs":
                    target = ram_absolute_target(instruction)
                    if ram_address_allowed(target, ranges):
                        queue.append(target)
                break

            if mnemonic in {"BRK", "RTI", "RTS"}:
                break

            pc = next_pc

    return instructions


def ram_operand_text(
    instruction: RamInstruction,
    labels: set[int],
    symbols: dict[int, str],
) -> str:
    mode = instruction.mode
    raw = instruction.raw

    if mode == "imp":
        return ""
    if mode == "acc":
        return "A"

    value8 = raw[1]
    if mode == "imm":
        return f"#$%02X" % value8
    if mode == "zp":
        return f"$%02X" % value8
    if mode == "zpx":
        return f"$%02X,X" % value8
    if mode == "zpy":
        return f"$%02X,Y" % value8
    if mode == "izx":
        return f"($%02X,X)" % value8
    if mode == "izy":
        return f"($%02X),Y" % value8
    if mode == "rel":
        target = ram_branch_target(instruction)
        return symbols.get(target, f"L{target:04X}")

    target = ram_absolute_target(instruction)
    base = symbols.get(
        target,
        RAM_HARDWARE_SYMBOLS.get(
            target,
            f"L{target:04X}" if target in labels else f"${target:04X}",
        ),
    )
    if mode == "abs":
        return base
    if mode == "absx":
        return f"{base},X"
    if mode == "absy":
        return f"{base},Y"
    if mode == "ind":
        return f"({base})"
    raise AssertionError(mode)


def render_ram_code(
    instructions: dict[int, RamInstruction],
    symbols: dict[int, str],
) -> list[str]:
    instruction_addresses = set(instructions)
    labels: set[int] = set()
    for instruction in instructions.values():
        if instruction.mode == "rel":
            target = ram_branch_target(instruction)
            if target in instruction_addresses:
                labels.add(target)
        elif (
            instruction.mnemonic in {"JMP", "JSR"}
            and instruction.mode == "abs"
        ):
            target = ram_absolute_target(instruction)
            if target in instruction_addresses:
                labels.add(target)

    lines: list[str] = []
    previous_end: int | None = None

    for address in sorted(instructions):
        instruction = instructions[address]
        if previous_end != address:
            if lines:
                lines.append("")
            lines.append(f".org ${address:04X}")

        if address in symbols:
            lines.append(f"{symbols[address]}:")
        elif address in labels:
            lines.append(f"L{address:04X}:")

        operand = ram_operand_text(instruction, labels, symbols)
        statement = instruction.mnemonic
        if operand:
            statement += " " + operand
        byte_text = " ".join(f"{value:02X}" for value in instruction.raw)
        lines.append(
            f"    {statement:<26} ; ${address:04X}: {byte_text}"
        )
        previous_end = address + len(instruction.raw)

    return lines


def is_dalek_ram_image(memory: bytes) -> bool:
    return (
        len(memory) == RAM_DUMP_SIZE
        and memory[0x4100:0x4110] == DALEK_RAM_ENTRY_SIGNATURE
    )


def decode_dalek_screen_text(data: bytes) -> list[str]:
    decoded: list[str] = []
    for value in data:
        if 1 <= value <= 26:
            decoded.append(chr(64 + value))
        elif 0x20 <= value <= 0x7E:
            decoded.append(chr(value))
        elif value in {0x00, 0x1C, 0x1F}:
            decoded.append("\n")
        else:
            decoded.append(f"<{value:02X}>")

    result: list[str] = []
    for line in "".join(decoded).splitlines():
        cleaned = " ".join(line.split())
        if cleaned:
            result.append("; " + cleaned)
    return result


def build_ram_code_disassembly(
    memory: bytes,
    *,
    filename: str,
    entry_address: int,
) -> str:
    if len(memory) != RAM_DUMP_SIZE:
        raise D64Error(
            f"RAM-Abbild hat {len(memory)} statt 65.536 Bytes."
        )

    digest = hashlib.sha256(memory).hexdigest()
    lines = [
        "; ------------------------------------------------------------------",
        "; MOS-6510-Code aus vollständigem C64-RAM-Abbild",
        f"; Quelle: {filename}",
        f"; SHA-256: {digest}",
        f"; Einsprung: ${entry_address:04X}",
        ";",
        "; Kontrollflussbasiert: Nicht erreichbare Datenbytes werden nicht",
        "; als vermeintliche Befehle ausgegeben.",
        "; ------------------------------------------------------------------",
        "",
    ]

    if is_dalek_ram_image(memory):
        entries = [
            0x1021, 0x1048,
            0x1D70,
            0x4100, 0x41EE, 0x422E, 0x4241, 0x4281,
            0x42DA, 0x44D4, 0x458A, 0x459D, 0x464C,
            0x46DC, 0x4786, 0x478C, 0x4793,
            0x481B, 0x4822, 0x4835, 0x4842,
        ]
        ranges = [
            (0x1000, 0x1AFF),
            (0x1D70, 0x1DFF),
            (0x4100, 0x4853),
        ]
        code = trace_ram_code(memory, entries, ranges)
        lines += [
            "; Dalek-Profil:",
            ";   $4100 = Intro-Start",
            ";   $46DC = Intro-Hauptschleife",
            ";   $1D70 = FIRE-Ausgang",
            ";   $0810/$0100 = nachgelagerter Spielentpacker",
            "",
            "; ==================== INTRO-CODE ====================",
            "",
            *render_ram_code(code, DALEK_RAM_SYMBOLS),
            "",
            "; ==================== IRQ-TABELLE ====================",
            "",
            ".org $4225",
            "intro_irq_table:",
            "    .byte $31, <$422E, >$422E ; Raster $31 -> irq_top",
            "    .byte $91, <$4241, >$4241 ; Raster $91 -> irq_middle",
            "    .byte $0D, <$4281, >$4281 ; Raster $0D -> irq_bottom",
            "",
            "; ==================== INTRO-TEXT ====================",
            "",
            *decode_dalek_screen_text(memory[0x4854:0x4AF5]),
            "",
            ".org $4854",
            "intro_screen_code_text:",
            *mos6510_data_lines(memory[0x4854:0x4AF5], 0x4854),
        ]

        runtime = bytearray(memory)
        runtime[0x0810:0x0848] = memory[0x4B00:0x4B38]
        runtime[0x0100:0x0200] = memory[0x4B38:0x4C38]
        runtime_entries = [
            0x0810,
            0x0100, 0x0122, 0x0129, 0x013B, 0x013F,
            0x0143, 0x0158, 0x0171, 0x0179,
            0x0196, 0x01A4, 0x01A8, 0x01AF, 0x01DA,
        ]
        runtime_code = trace_ram_code(
            bytes(runtime),
            runtime_entries,
            [(0x0100, 0x01FF), (0x0810, 0x0847)],
        )
        lines += [
            "",
            "; ==================== NACH DEM INTRO ====================",
            "; $4B00-$FEFF wird nach $0810-$BC0F kopiert.",
            "; $0848-$0947 wird danach als Entpacker nach $0100 kopiert.",
            "; Die folgenden Adressen sind die tatsächlichen Laufzeitadressen.",
            "",
            *render_ram_code(runtime_code, DALEK_RAM_SYMBOLS),
        ]
    else:
        ranges = [(0x0200, 0xCFFF)]
        if not ram_address_allowed(entry_address, ranges):
            ranges.append((entry_address, entry_address))
        code = trace_ram_code(memory, [entry_address], ranges)
        lines += [
            "; ==================== ERREICHBARER CODE ====================",
            "",
            *render_ram_code(code, {}),
        ]

    return "\n".join(lines) + "\n"


def save_ram_code_disassembly(
    image: D64Image,
    memory: bytes,
    *,
    ram_path: Path,
    entry_address: int,
    verbose: bool,
) -> Path:
    output_directory = image_output_directory(image)
    listing_path = output_directory / f"{image.path.stem}_ram.asm"

    try:
        listing_path.write_text(
            build_ram_code_disassembly(
                memory,
                filename=ram_path.name,
                entry_address=entry_address,
            ),
            encoding="utf-8",
            newline="",
        )
    except OSError as exc:
        raise D64Error(
            f"RAM-Disassembly kann nicht geschrieben werden: "
            f"{listing_path}: {exc}"
        ) from exc

    if verbose:
        print(f"Code-Listing    : {listing_path.name}")
        if is_dalek_ram_image(memory):
            print(
                "Dalek-Profil    : Intro, Raster-IRQ, FIRE-Ausgang und "
                "Spielentpacker erkannt"
            )
    return listing_path


def process_ram_options(
    image: D64Image,
    *,
    image_ram: bool,
    disassemble_code: bool,
    ram_input: Path | None,
    vice_path: Path | None,
    host: str,
    port: int,
    breakpoint: int,
    bank_name: str,
    file_index: int,
    connect_timeout: float,
    run_timeout: float,
    warp: bool,
    keep_vice: bool,
    connect_only: bool,
    save_snapshot: bool,
    verbose: bool,
) -> tuple[Path | None, Path | None]:
    if not image_ram and not disassemble_code:
        return None, None

    if ram_input is not None:
        try:
            memory = ram_input.read_bytes()
        except OSError as exc:
            raise D64Error(
                f"RAM-Eingabedatei kann nicht gelesen werden: "
                f"{ram_input}: {exc}"
            ) from exc
        if len(memory) != RAM_DUMP_SIZE:
            raise D64Error(
                f"RAM-Eingabedatei hat {len(memory)} statt 65.536 Bytes."
            )
        ram_path = ram_input.resolve()
        if verbose:
            print()
            print("VICE-RAM-Abbild")
            print(f"RAM-Eingabe     : {ram_path}")
    else:
        memory, ram_path = capture_complete_ram(
            image,
            vice_path=vice_path,
            host=host,
            port=port,
            breakpoint=breakpoint,
            bank_name=bank_name,
            file_index=file_index,
            connect_timeout=connect_timeout,
            run_timeout=run_timeout,
            warp=warp,
            keep_vice=keep_vice,
            connect_only=connect_only,
            save_snapshot=save_snapshot,
            verbose=verbose,
        )

    listing_path = None
    if disassemble_code:
        listing_path = save_ram_code_disassembly(
            image,
            memory,
            ram_path=ram_path,
            entry_address=breakpoint,
            verbose=verbose,
        )
    return ram_path, listing_path


def build_dalek_tsm_disassembly(
    filename: str,
    file_data: bytes,
    *,
    c64_filename: str,
) -> str:
    """
    Erstellt ein strukturiertes Listing des bekannten zweistufigen Entpackers.

    Gepackte Nutzdaten werden als Daten ausgegeben. Nur tatsächlich als
    Bootstrap oder Relokationsabbild erkennbare Bereiche werden als 6510-Code
    interpretiert.
    """
    load_address = int.from_bytes(file_data[:2], "little")
    payload = file_data[2:]

    def payload_slice(start: int, end: int) -> bytes:
        return payload[start - load_address : end - load_address]

    basic = payload_slice(0x0801, 0x080B)
    bootstrap = payload_slice(0x080B, 0x081D)
    relocation_image = payload_slice(0x081D, 0x091D)
    packed_data = payload_slice(0x091D, 0x9AD8)
    tail_image_a = payload_slice(0x9AD8, 0x9BD8)
    tail_image_b = payload_slice(0x9AF8, 0x9BF8)

    # Der erste Entpacker kopiert 256 Bytes von $9AD8 nach $07F0 und danach
    # 256 Bytes von $9AF8 nach $0810. Der zweite Bereich überschreibt dabei
    # den überlappenden Teil. Dieses Abbild zeigt den Zustand direkt nach den
    # beiden Kopierschleifen, noch vor späterer Selbstmodifikation/Entpackung.
    runtime_tail = bytearray(tail_image_a)
    runtime_tail[0x20 : 0x120] = tail_image_b
    relocated_code_size = 0x01DE - 0x0100

    lines = [
        f"; 6510-Disassembly: {filename}",
        "; " + "=" * 70,
        f"; C64-Dateiname   : {c64_filename!r}",
        f"; PRG-Dateigröße : {len(file_data)} Bytes",
        f"; Ladeadresse    : ${load_address:04X}",
        "; BASIC-Start     : 1990 SYS 2059",
        "; SYS-Einsprung   : $080B",
        "; Spieleinsprung  : $4100 (erst nach vollständiger Entpackung)",
        f"; SHA-256        : {hashlib.sha256(file_data).hexdigest()}",
        ";",
        "; WICHTIG:",
        "; Das PRG ist selbstentpackend. Der große Bereich $091D-$9AD7 ist",
        "; gepackte Nutzlast und kein linear ausführbarer Programmcode.",
        "; Undokumentierte Opcodes erscheinen verlustfrei als .byte.",
        "",
        "; ------------------------------------------------------------------",
        "; Tokenisierter BASIC-Starter bei $0801",
        "; 1990 SYS 2059",
        "; ------------------------------------------------------------------",
        "basic_0801:",
        *mos6510_data_lines(basic, 0x0801),
        "",
        "; ------------------------------------------------------------------",
        "; Erster sichtbarer Bootstrap, aufgerufen durch SYS $080B",
        "; Kopiert $081D-$091C nach $00FB-$01FA und springt nach $0100.",
        "; ------------------------------------------------------------------",
        "entry_080B:",
        *disassemble_mos6510_region(bootstrap, 0x080B),
        "",
        "; ------------------------------------------------------------------",
        "; Relokationsabbild: Quelldaten $081D-$091C",
        "; Die ersten fünf Bytes landen in $00FB-$00FF.",
        "; ------------------------------------------------------------------",
        "relocation_state_00FB:",
        *mos6510_data_lines(relocation_image[:5], 0x00FB),
        "",
        "; Ausführungskopie ab $0100; Quelldateiadresse ab $0822.",
        "relocated_entry_0100:",
        *disassemble_mos6510_region(
            relocation_image[5 : 5 + relocated_code_size],
            0x0100,
        ),
        "",
        "; Längentabelle und Arbeitsdaten der Relokationsroutine.",
        "relocated_table_01DE:",
        *mos6510_data_lines(
            relocation_image[5 + relocated_code_size :],
            0x01DE,
        ),
        "",
        "; ------------------------------------------------------------------",
        "; Gepackte Nutzlast. Bewusst als .byte, nicht als falscher Code.",
        "; Quelldateiadressen $091D-$9AD7.",
        "; ------------------------------------------------------------------",
        "packed_payload_091D:",
        *mos6510_data_lines(packed_data, 0x091D),
        "",
        "; ------------------------------------------------------------------",
        "; Laufzeitabbild der beiden überlappenden Kopien:",
        "; $9AD8-$9BD7 -> $07F0-$08EF",
        "; $9AF8-$9BF7 -> $0810-$090F (überschreibt den Überlappungsbereich)",
        "; Dieses Abbild wird später durch Entpackung/Selbstmodifikation weiter",
        "; verändert; die lineare Ansicht ist daher nur eine statische Stufe.",
        "; ------------------------------------------------------------------",
        "; Der statisch eindeutig erkennbare Seed-Code belegt $07F0-$07FF.",
        "runtime_seed_code_07F0:",
        *disassemble_mos6510_region(bytes(runtime_tail[:0x10]), 0x07F0),
        "",
        "; Der anschließende Bereich wird erst zur Laufzeit verändert und ist",
        "; deshalb verlustfrei als Datenabbild wiedergegeben.",
        "runtime_seed_data_0800:",
        *mos6510_data_lines(bytes(runtime_tail[0x10:]), 0x0800),
        "",
    ]
    return "\n".join(lines)


def build_generic_prg_disassembly(
    filename: str,
    file_data: bytes,
    *,
    c64_filename: str,
) -> str:
    """Erstellt eine vorsichtige lineare Disassembly für eine beliebige PRG."""
    if len(file_data) < 2:
        return (
            f"; 6510-Disassembly: {filename}\n"
            "; Fehler: Die Datei enthält keine vollständige PRG-Ladeadresse.\n"
        )

    load_address = int.from_bytes(file_data[:2], "little")
    payload = file_data[2:]
    sys_entry = find_basic_sys_entry(payload, load_address)
    entry_address = (
        sys_entry.address
        if sys_entry is not None
        and load_address <= sys_entry.address < load_address + len(payload)
        else load_address
    )
    prefix_size = entry_address - load_address
    prefix = payload[:prefix_size]
    code = payload[prefix_size:]

    lines = [
        f"; 6510-Disassembly: {filename}",
        "; " + "=" * 70,
        f"; C64-Dateiname   : {c64_filename!r}",
        f"; PRG-Dateigröße : {len(file_data)} Bytes",
        f"; Ladeadresse    : ${load_address:04X}",
        f"; Einsprung      : ${entry_address:04X}"
        + (" (BASIC-SYS)" if sys_entry is not None else " (angenommen)"),
        f"; SHA-256        : {hashlib.sha256(file_data).hexdigest()}",
        ";",
        "; Statische lineare Disassembly. Ohne Laufzeitanalyse kann nicht",
        "; zuverlässig zwischen Code, Daten und selbstmodifiziertem Code",
        "; unterschieden werden. Undokumentierte Opcodes bleiben .byte.",
        "",
    ]

    if prefix:
        lines.extend(
            [
                "; Präfix/BASIC-Daten vor dem erkannten Einsprung",
                "program_prefix:",
                *mos6510_data_lines(prefix, load_address),
                "",
            ]
        )

    lines.extend(
        [
            f"entry_{entry_address:04X}:",
            *disassemble_mos6510_region(code, entry_address),
            "",
        ]
    )
    return "\n".join(lines)


def build_prg_disassembly(
    filename: str,
    file_data: bytes,
    *,
    c64_filename: str,
) -> str:
    """Wählt ein verifiziertes Spezialprofil oder die allgemeine Disassembly."""
    digest = hashlib.sha256(file_data).hexdigest()
    if digest == DALEK_ATTACK_TSM_SHA256:
        return build_dalek_tsm_disassembly(
            filename,
            file_data,
            c64_filename=c64_filename,
        )
    return build_generic_prg_disassembly(
        filename,
        file_data,
        c64_filename=c64_filename,
    )


def prg_memory_layout(
    load_address: int | None,
    payload_size: int,
) -> tuple[str, bool]:
    """
    Liefert die reale 16-Bit-Speicherbelegung eines PRG.

    Die frühere einfache Addition konnte bei einem Umlauf über $FFFF eine
    fünfstellige Hexadezimaladresse wie $12122 ausgeben. Hier wird der
    16-Bit-Adressumlauf ausdrücklich dargestellt.
    """
    if load_address is None:
        return "nicht bestimmbar", False
    if payload_size == 0:
        return f"${load_address:04X} (leere Nutzlast)", False

    linear_end = load_address + payload_size - 1
    if linear_end <= 0xFFFF:
        return f"${load_address:04X}-${linear_end:04X}", False

    wrapped_end = linear_end & 0xFFFF
    return (
        f"${load_address:04X}-$FFFF und $0000-${wrapped_end:04X} "
        "(16-Bit-Adressumlauf)",
        True,
    )


def known_memory_region_notes(
    load_address: int | None,
    payload_size: int,
) -> list[str]:
    """Beschreibt von der PRG-Nutzlast berührte wichtige C64-Speicherbereiche."""
    if load_address is None or payload_size <= 0:
        return []

    linear_end = load_address + payload_size - 1
    ranges = [(load_address, min(linear_end, 0xFFFF))]
    if linear_end > 0xFFFF:
        ranges.append((0x0000, linear_end & 0xFFFF))

    regions = (
        (0x0000, 0x00FF, "Zeropage"),
        (0x0100, 0x01FF, "Prozessor-Stack"),
        (0x0400, 0x07E7, "Standard-Bildschirmspeicher"),
        (0x0801, 0x9FFF, "normaler RAM-/BASIC-Programmbereich"),
        (0xA000, 0xBFFF, "RAM unter dem BASIC-ROM"),
        (0xC000, 0xCFFF, "oberer freier RAM"),
        (0xD000, 0xDFFF, "RAM unter I/O beziehungsweise Zeichensatz-ROM"),
        (0xE000, 0xFFFF, "RAM unter dem KERNAL-ROM"),
    )

    notes: list[str] = []
    for region_start, region_end, label in regions:
        intersections: list[str] = []
        for range_start, range_end in ranges:
            start = max(region_start, range_start)
            end = min(region_end, range_end)
            if start <= end:
                intersections.append(f"${start:04X}-${end:04X}")
        if intersections:
            notes.append(f"{', '.join(intersections)}: {label}")
    return notes


def is_valid_basic_line_chain(program_data: bytes, load_address: int) -> bool:
    """Prüft die verkettete Grundstruktur eines tokenisierten BASIC-Programms."""
    if load_address != 0x0801 or len(program_data) < 6:
        return False

    offset = 0
    visited: set[int] = set()
    found_line = False

    while offset + 4 <= len(program_data):
        current_address = load_address + offset
        if current_address in visited:
            return False
        visited.add(current_address)

        next_address = int.from_bytes(
            program_data[offset : offset + 2],
            "little",
        )
        if next_address == 0:
            return found_line

        line_end = program_data.find(b"\x00", offset + 4)
        if line_end < 0:
            return False
        found_line = True

        next_offset = next_address - load_address
        if next_offset <= offset or next_offset >= len(program_data):
            # Manche Einzeiler benutzen als Zeiger genau die Adresse des
            # abschließenden 00-00-Markers. Dieser muss noch in der Datei
            # liegen.
            return next_offset == line_end + 1 and next_offset + 1 < len(
                program_data
            )
        offset = next_offset

    return False


def structure_assessment(
    analysis: PrgAnalysis,
    file_data: bytes,
) -> list[str]:
    """Erzeugt vorsichtige, datenbasierte Aussagen zur PRG-Struktur."""
    if len(file_data) < 2:
        return ["Die Datei besitzt keine vollständige zweibyteige Ladeadresse."]

    payload = file_data[2:]
    statistics = calculate_payload_statistics(payload)
    has_basic = (
        analysis.load_address is not None
        and is_valid_basic_line_chain(payload, analysis.load_address)
    )
    statements: list[str] = []

    if has_basic:
        statements.append(
            "Am Dateianfang befindet sich eine formal verkettete "
            "C64-BASIC-Struktur."
        )
    else:
        statements.append(
            "Am Dateianfang wurde keine vollständige, formal verkettete "
            "BASIC-Struktur erkannt."
        )

    if statistics.entropy >= 7.6 and statistics.unique_byte_values >= 250:
        statements.append(
            "Die hohe Byte-Entropie und die Verwendung nahezu aller Bytewerte "
            "sprechen stark für gepackte, komprimierte oder grafik-/datenreiche "
            "Binärinhalte."
        )
    elif statistics.entropy >= 7.0:
        statements.append(
            "Die Byteverteilung ist relativ dicht; größere binäre Datenanteile "
            "sind wahrscheinlicher als überwiegend lesbarer Programmtext."
        )
    else:
        statements.append(
            "Die Byteverteilung ist nicht maximal dicht; strukturierte Tabellen, "
            "Code oder unkomprimierte Daten sind möglich."
        )

    return statements


def inspect_prg_data(
    filename: str,
    file_data: bytes,
    *,
    c64_filename: str | None = None,
) -> PrgAnalysis:
    """Ermittelt die statisch und sicher aus einer PRG-Datei lesbaren Daten."""
    digest = hashlib.sha256(file_data).hexdigest()
    display_c64_name = c64_filename or Path(filename).stem

    if len(file_data) < 2:
        return PrgAnalysis(
            filename=filename,
            c64_filename=display_c64_name,
            file_size=len(file_data),
            payload_size=0,
            load_address=None,
            loaded_end=None,
            sys_entry=None,
            sha256=digest,
            is_known_dalek_attack_tsm=digest == DALEK_ATTACK_TSM_SHA256,
        )

    load_address = int.from_bytes(file_data[:2], "little")
    program_data = file_data[2:]
    loaded_end = (
        load_address + len(program_data) - 1
        if program_data
        else load_address
    )

    return PrgAnalysis(
        filename=filename,
        c64_filename=display_c64_name,
        file_size=len(file_data),
        payload_size=len(program_data),
        load_address=load_address,
        loaded_end=loaded_end,
        sys_entry=find_basic_sys_entry(program_data, load_address),
        sha256=digest,
        is_known_dalek_attack_tsm=digest == DALEK_ATTACK_TSM_SHA256,
    )


def build_dalek_attack_tsm_report(analysis: PrgAnalysis) -> str:
    """
    Erzeugt den verifizierten Detailbericht für DALEK ATTACK/TSM.

    Das Profil wird ausschließlich nach Übereinstimmung des vollständigen
    SHA-256-Fingerabdrucks verwendet. Dadurch werden die beim manuellen
    Reverse Engineering gewonnenen Angaben nicht auf nur ähnlich aufgebaute
    oder unbekannte PRG-Dateien übertragen.
    """
    return f"""Programmanalyse: {analysis.filename}
========================================

1. Grunddaten
-------------

Programmdatei     : {analysis.filename}
Dateigröße        : {german_number(analysis.file_size)} Bytes
PRG-Nutzdaten     : {german_number(analysis.payload_size)} Bytes
Ladeadresse       : $0801 (2049)
Geladener Bereich : $0801-$9BF7
BASIC-Zeile       : 1990 SYS 2059
SYS-Einsprung     : $080B (2059)
Spieleinsprung    : $4100
SHA-256           : {analysis.sha256}

Die ersten beiden Bytes einer C64-PRG-Datei enthalten die Ladeadresse in
Little-Endian-Reihenfolge. Bei dieser Datei sind dies die Bytes 01 08 und
damit die Adresse $0801.


2. BASIC-Starter
----------------

Der Anfang der Datei besitzt folgende Struktur:

01 08                   PRG-Ladeadresse $0801
0B 08                   BASIC-Zeiger auf die nächste Zeile beziehungsweise
                        auf das Ende der einzigen BASIC-Zeile
C6 07                   BASIC-Zeilennummer 1990
9E 32 30 35 39 00       BASIC-Token SYS und Dezimaladresse 2059

Das entspricht dem BASIC-Befehl:

1990 SYS 2059

Die Dezimalzahl 2059 entspricht der Hexadezimaladresse $080B. Der für den
Benutzer sichtbare Programmeinstieg ist deshalb $080B.

Üblicher Ladevorgang:

LOAD"DALEK ATTACK/TSM",8,1
RUN

RUN führt die BASIC-Zeile aus. Der darin enthaltene Befehl SYS 2059
übergibt die Kontrolle an den Maschinencode bei $080B.


3. Programmtyp
--------------

Die Datei ist kein einfaches, unkomprimiertes Programm. Nach dem kurzen
BASIC-Starter folgt ein selbstentpackendes C64-Programm mit zwei
Entpackstufen.

Der sichtbare SYS-Einsprung $080B ist daher nicht der Einstieg in das
eigentliche Spiel, sondern zunächst der Einstieg in den Entpacker.


4. Start- und Entpackablauf
--------------------------

RUN
  -> SYS $080B
     -> Entpacker, Stufe 1
        -> Sprung nach $0801
           -> Entpacker, Stufe 2
              -> eigentliches Spiel bei $4100

Erkannter Ablauf:

1. Der Code bei $080B deaktiviert die Interrupts.

2. Über den Prozessorport an Adresse $01 werden ROM-Bereiche des C64
   ausgeblendet. Dadurch kann der darunterliegende RAM verwendet werden.

3. Die erste Entpackroutine wird in den Speicherbereich um $0100
   verschoben und dort ausgeführt.

4. Nach der ersten Entpackstufe wird ein zweiter Loader bei $0801
   gestartet.

5. Die zweite Stufe erzeugt ungefähr 61.177 Bytes im Speicherbereich
   $077F-$F677.

6. Nach Abschluss der Entpackung wird die Programmkontrolle an $4100
   übergeben. Dies ist der erkannte Einstieg in das eigentliche Spiel.


5. Bedeutung der Einsprungadressen
----------------------------------

$080B:
    Dieser Einsprung ist im tokenisierten BASIC-Loader durch SYS 2059
    direkt gespeichert. Er ist die Adresse, die beim normalen Start mit
    RUN zuerst aufgerufen wird.

$4100:
    Diese Adresse wird erst nach beiden Entpackstufen erreicht. Sie ist
    der erkannte endgültige Spieleinsprung.

Für eine allgemeine D64-Startanalyse ist $080B daher der sichtbare und
statisch aus dem PRG ermittelbare Einsprung. Für die Untersuchung des
entpackten eigentlichen Programms ist dagegen $4100 maßgeblich.


6. Erkannte Inhalte
-------------------

Nach der Entpackung konnten unter anderem folgende Texte und Kennungen
erkannt werden:

- DALEK ATTACK
- Copyright-Hinweise für BBC und Admiral Software
- Hinweise auf die Commodore-64-Version
- PRESS FIRE TO START
- Auswahl für ein oder zwei Spieler
- Joystick-Hinweise
- PRESS FIRE TO CONTINUE
- GAME OVER
- LEVEL COMPLETE
- WELL DONE
- MUSIC BY MARTIJN SCHUTTEN, PLAYER BY FALCO PAUL
- VOICE TRACKER V2+ SCIENCE 451
- eingebettetes Datum 05/12/92

Außerdem enthält das entpackte Programm größere Bereiche mit Grafik-,
Zeichensatz-, Musik- und Leveldaten.


7. Prüfergebnis
---------------

Die PRG-Datei ist strukturell gültig und nicht abgeschnitten. Der
BASIC-Starter, der Einstieg in den ersten Entpacker, die zweite
Entpackstufe und der abschließende Kontrolltransfer zum Spieleinstieg
$4100 konnten nachvollzogen werden.

Zusammenfassung:

- sichtbarer Start über BASIC: $080B
- endgültiger Start nach der Entpackung: $4100
- Dateityp: zweistufig gepacktes C64-Programm
- Dateistatus: vollständig und strukturell gültig
"""


def build_dalek_intro_report(
    analysis: PrgAnalysis,
    file_data: bytes,
) -> str:
    """Erzeugt die prüfsummengebundene Tiefenanalyse des Intro-Loaders."""
    payload = file_data[2:]
    statistics = calculate_payload_statistics(payload)
    memory_layout, _ = prg_memory_layout(
        analysis.load_address,
        analysis.payload_size,
    )

    return f"""Programmanalyse: {analysis.filename}
========================================

1. Grunddaten
-------------

Programmdatei     : {analysis.filename}
C64-Dateiname     : {analysis.c64_filename}
Dateigröße        : {german_number(analysis.file_size)} Bytes
PRG-Nutzdaten     : {german_number(analysis.payload_size)} Bytes
Ladebytes         : 01 08
Ladeadresse       : $0801 (2049)
Geladener Bereich : {memory_layout}
BASIC-Zeile       : 1680 SYS 2049
SYS-Einsprung     : $0801 (2049)
Relokationsziel   : $0100
SHA-256           : {analysis.sha256}


2. Hybrider BASIC-/Maschinencode-Starter
----------------------------------------

Der Dateianfang ist zugleich BASIC-Zeile und 6510-Maschinencode:

01 08                   PRG-Ladeadresse $0801
0B 08                   BASIC-Zeiger auf $080B
90 06                   BASIC-Zeilennummer 1680
9E 32 30 34 39 00       BASIC-Token SYS und Dezimaladresse 2049

Als BASIC gelesen entspricht dies:

1680 SYS 2049

2049 ist $0801. RUN springt deshalb nicht direkt hinter den BASIC-Starter,
sondern an dessen erstes Byte. Das ist eine absichtliche Doppelbelegung des
Zeilenkopfs als BASIC-Daten und Maschinencode.


3. Ausführung ab $0801
----------------------

Der statisch nachvollziehbare Anfang lautet:

$0801  0B 08       ANC #$08       undokumentierter 6510-Befehl
$0803  90 06       BCC $080B
$080B  A0 00       LDY #$00
$080D  78          SEI
$080E  E6 01       INC $01
$0810  B9 2F 3E    LDA $3E2F,Y
$0813  99 FA 00    STA $00FA,Y
$0816  C8          INY
$0817  D0 F7       BNE $0810
$0819  4C 00 01    JMP $0100

ANC übernimmt beim NMOS-6510 das negative Ergebnisbit in das Carry-Flag.
Da die Maske $08 das Bit 7 immer löscht, wird Carry gelöscht und BCC
verzweigt zuverlässig nach $080B. Die dazwischenliegenden BASIC-Bytes
werden bei der Maschinencode-Ausführung übersprungen.


4. Relokation und Speicherumschaltung
-------------------------------------

Die Routine sperrt zunächst Interrupts mit SEI und verändert anschließend
den Prozessorport $01. Dieser Port steuert die Einblendung von BASIC-ROM,
KERNAL-ROM und I/O; der genaue resultierende Zustand hängt vom vorherigen
Portwert ab.

Danach kopiert die Schleife 256 Bytes:

Quelle           : $3E2F-$3F2E
Ziel             : $00FA-$01F9
Weiterer Sprung  : $0100

Das Ziel überdeckt Teile der Zeropage und des Prozessor-Stacks. Das ist ein
typisches Kennzeichen einer kleinen selbstverlegenden Loader- oder
Entpackroutine und kein normales BASIC-Programmverhalten.

Die PRG-Datei selbst reicht bis $3EE8. Sie liefert damit 186 Bytes des
adressierten 256-Byte-Quellfensters; die letzten 70 gelesenen Bytes liegen
außerhalb der geladenen Datei. Sie können vorhandenen RAM enthalten und
müssen für den tatsächlich benutzten Routinenkern nicht relevant sein.
Diese Besonderheit ist kein Beweis für eine beschädigte Datei, zeigt aber,
dass der Loader stark von seinem Laufzeitumfeld Gebrauch macht.


5. Statistische Strukturanalyse
-------------------------------

Shannon-Entropie : {statistics.entropy:.3f} von maximal 8,000 Bit/Byte
Bytewerte benutzt: {statistics.unique_byte_values} von 256
Druckbares ASCII : {statistics.printable_ascii_percent:.1f} %
Nullbytes        : {statistics.zero_percent:.1f} %
$FF-Bytes        : {statistics.ff_percent:.1f} %
Längster Gleichlauf: {statistics.longest_equal_byte_run} gleiche Bytes
Nutzdatenanfang  : {hexadecimal_preview(payload)}

Die dichte Byteverteilung und das Fehlen längerer zuverlässig lesbarer
Texte sprechen für gepackte beziehungsweise stark binäre Intro-Daten.
Zufällige alphabetische Folgen im Datenstrom sind Tabellen- oder
Grafikmuster und keine belastbaren Bildschirmtexte.


6. Programmrolle
----------------

Der Dateiname "DALEK INTRO  [L]", der BASIC/6510-Hybridstarter, die
Relokation in Zeropage/Stack und die hohe Entropie passen zu einem
eigenständigen Intro-Loader mit gepacktem Inhalt.

Sicher ermittelt sind:

- Benutzerstart über RUN und SYS $0801
- absichtlicher Übergang vom BASIC-Zeilenkopf nach $080B
- Interruptsperre und Änderung des Speicherbank-Ports $01
- 256-Byte-Kopie nach $00FA-$01F9
- anschließender Sprung nach $0100

Ein endgültiger Intro-Einsprung nach der Relokations-/Entpackroutine ist
ohne vollständige 6510-Emulation nicht verifiziert. Er wird deshalb nicht
als feste Adresse behauptet.


7. Prüfergebnis
---------------

Die Datei ist als PRG vollständig lesbar. Gegenüber einer bloßen
Containeranalyse lässt sich ihr tatsächlicher Startweg bis $0100
nachvollziehen. Es handelt sich sehr wahrscheinlich um ein gepacktes,
selbstverlegendes Intro und nicht um ein gewöhnliches BASIC-Programm.
"""


def build_dalek_numbered_report(
    analysis: PrgAnalysis,
    file_data: bytes,
    sequence_number: str,
) -> str:
    """Erzeugt eine ausführliche Gruppenanalyse der Dateien 00 bis 06."""
    payload = file_data[2:]
    statistics = calculate_payload_statistics(payload)
    memory_layout, wraps = prg_memory_layout(
        analysis.load_address,
        analysis.payload_size,
    )
    region_notes = known_memory_region_notes(
        analysis.load_address,
        analysis.payload_size,
    )
    region_text = "\n".join(f"- {note}" for note in region_notes)

    individual_notes = {
        "00": (
            "Der Bereich reicht in den RAM unter dem KERNAL-ROM. Zum Lesen "
            "dieses Anteils muss das Spiel das KERNAL-ROM ausblenden."
        ),
        "01": (
            "Der Bereich reicht in den RAM unter dem BASIC-ROM. Diese Daten "
            "sind erst nach passender Speicherbank-Umschaltung direkt lesbar."
        ),
        "02": (
            "Der Bereich liegt im normalen RAM. Er überlappt fast vollständig "
            "mit Datei 03, weshalb beide sehr wahrscheinlich alternative "
            "Spielabschnitte und keine gleichzeitig residenten Blöcke sind."
        ),
        "03": (
            "Der Bereich liegt im normalen RAM. Er überlappt fast vollständig "
            "mit Datei 02, weshalb beide sehr wahrscheinlich alternative "
            "Spielabschnitte und keine gleichzeitig residenten Blöcke sind."
        ),
        "04": (
            "Die Nutzlast läuft über $FFFF nach $0000 um und berührt dabei "
            "Zeropage, Stack und weitere zentrale Systembereiche. Ein normales "
            "LOAD mit anschließendem RUN wäre dafür ungeeignet; die Datei ist "
            "offensichtlich für einen kontrollierten Spiel-/Entpackloader "
            "vorgesehen."
        ),
        "05": (
            "Der Bereich liegt vollständig im normalen RAM und ist als "
            "austauschbarer Daten- oder Programmblock adressiert."
        ),
        "06": (
            "Der Bereich beginnt im RAM unter dem BASIC-ROM und reicht in den "
            "oberen freien RAM. Das Spiel muss dafür die Speicherbank passend "
            "konfigurieren."
        ),
    }

    wrap_note = (
        "Ja; die lineare Nutzlast überschreitet die 16-Bit-Adressgrenze."
        if wraps
        else "Nein."
    )

    return f"""Programmanalyse: {analysis.filename}
========================================

1. Grunddaten
-------------

Programmdatei     : {analysis.filename}
C64-Dateiname     : {analysis.c64_filename}
Dateigröße        : {german_number(analysis.file_size)} Bytes
PRG-Nutzdaten     : {german_number(analysis.payload_size)} Bytes
Ladebytes         : {file_data[0]:02X} {file_data[1]:02X}
Ladeadresse       : ${analysis.load_address:04X} ({analysis.load_address})
Speicherbelegung  : {memory_layout}
Adressumlauf      : {wrap_note}
BASIC-Programm    : nein
Statischer SYS    : nicht vorhanden
SHA-256           : {analysis.sha256}


2. Speicherbelegung
-------------------

Die Datei belegt beziehungsweise berührt folgende C64-Bereiche:

{region_text}

{individual_notes[sequence_number]}

Die Ladeadresse ist ein Speicherziel, aber kein Programmeinsprung. Eine
PRG-Datei enthält außer den beiden Ladebytes kein allgemeines Startfeld.


3. Gemeinsame Struktur der Dateien 00 bis 06
--------------------------------------------

Diese Datei gehört prüfsummengenau zu der sieben Dateien umfassenden Reihe
"00  DALEK ATTACK" bis "06  DALEK ATTACK" desselben Diskettenabbilds.

Gemeinsame, direkt messbare Merkmale:

- alle sieben Nutzdatenblöcke beginnen mit den Bytes B0 00;
- alle sieben verwenden sämtliche 256 möglichen Bytewerte;
- ihre Shannon-Entropie liegt zwischen 7,782 und 7,860 Bit/Byte;
- zwischen allen sieben Dateien treten zahlreiche identische Datenfolgen
  auf, darunter sieben gemeinsame Folgen mit mindestens 48 Bytes;
- die Dateien besitzen unterschiedliche Zieladressen und teilweise
  überlappende Speicherbereiche.

Diese Übereinstimmungen sind zu stark für unabhängige Zufallsdateien. Die
Blöcke verwenden dasselbe Datenformat und enthalten gemeinsame Tabellen,
Grafikmuster, Routinen oder durch denselben Packer erzeugte Strukturen.


4. Statistische Strukturanalyse dieser Datei
--------------------------------------------

Shannon-Entropie : {statistics.entropy:.3f} von maximal 8,000 Bit/Byte
Bytewerte benutzt: {statistics.unique_byte_values} von 256
Druckbares ASCII : {statistics.printable_ascii_percent:.1f} %
Nullbytes        : {statistics.zero_percent:.1f} %
$FF-Bytes        : {statistics.ff_percent:.1f} %
Längster Gleichlauf: {statistics.longest_equal_byte_run} gleiche Bytes
Nutzdatenanfang  : {hexadecimal_preview(payload)}

Die hohe Entropie bedeutet nicht automatisch Verschlüsselung. Gemeinsam
mit dem identischen B0-00-Anfang und den gruppenweit wiederkehrenden
Binärfolgen spricht sie jedoch deutlich für gepackte beziehungsweise
grafik-, level- oder tabellenreiche Spielmodule.


5. Start- und Ausführungsanalyse
--------------------------------

Am Nutzdatenanfang existiert weder eine gültige BASIC-Zeilenkette noch ein
statisch auswertbarer SYS-Starter. Die Adresse ${analysis.load_address:04X}
ist deshalb nicht als Einsprung zu interpretieren.

Die nummerierte Benennung, das gemeinsame Binärformat und die
Speicherüberlappungen zeigen, dass die Datei sehr wahrscheinlich vom
Hauptprogramm bei Bedarf geladen oder entpackt wird. Sie ist kein
eigenständig mit RUN startbares Programm.

Der exakte Aufrufer, das Entpackformat und die endgültigen Zieladressen
können erst durch Nachverfolgung des bereits entpackten Hauptprogramms
oder durch 6510-Emulation sicher bestimmt werden.


6. Erkannte Inhalte
-------------------

Es wurden keine längeren, zuverlässig als Benutzertext interpretierbaren
ASCII-/PETSCII-Sätze gefunden. Sichtbare alphabetische Reihen und ähnliche
Muster sind mit hoher Wahrscheinlichkeit Grafik-, Zeichen-, Lookup- oder
komprimierte Daten und werden nicht als Textmeldung ausgegeben.

Aus Dateiname und Gruppenstruktur lässt sich als begründete, aber nicht
abschließend bewiesene Rolle ableiten:

- Index beziehungsweise Modulnummer: {sequence_number}
- wahrscheinlich austauschbarer Spielabschnitt, Level- oder Ressourcensatz
- gemeinsames Speicher-/Packformat mit den Modulen 00 bis 06
- Start nur über den Hauptloader des Spiels


7. Prüfergebnis
---------------

Die Datei ist innerhalb ihrer D64-Sektorkette vollständig und besitzt eine
gültige zweibyteige Ladeadresse. Sie enthält deutlich mehr analysierbare
Struktur als nur Größe und Prüfsumme, aber keinen eigenen sicheren
Einsprung. Die belastbarste Einordnung ist ein gepacktes beziehungsweise
binäres DALEK-ATTACK-Spielmodul der nummerierten Reihe 00 bis 06.
"""


def build_generic_prg_report(
    analysis: PrgAnalysis,
    file_data: bytes | None = None,
) -> str:
    """
    Erzeugt einen allgemeinen PRG-Bericht ohne ungesicherte Detailaussagen.

    Ein abschließender Einsprung eines Packers kann im allgemeinen Fall nicht
    allein aus dem PRG-Container bestimmt werden. Der Bericht trennt deshalb
    direkt gespeicherte Daten von heuristischen Ergebnissen.
    """
    raw_file_data = file_data or b""
    payload = raw_file_data[2:] if len(raw_file_data) >= 2 else b""
    statistics = calculate_payload_statistics(payload)
    memory_layout, wraps = prg_memory_layout(
        analysis.load_address,
        analysis.payload_size,
    )
    lines = [
        f"Programmanalyse: {analysis.filename}",
        "=" * 40,
        "",
        "1. Grunddaten",
        "-------------",
        "",
        f"Programmdatei     : {analysis.filename}",
        f"C64-Dateiname     : {analysis.c64_filename}",
        f"Dateigröße        : {german_number(analysis.file_size)} Bytes",
        f"PRG-Nutzdaten     : {german_number(analysis.payload_size)} Bytes",
    ]

    if analysis.load_address is None:
        lines.extend(
            [
                "Ladeadresse       : nicht vorhanden",
                "Geladener Bereich : nicht bestimmbar",
            ]
        )
    else:
        if len(raw_file_data) >= 2:
            lines.append(
                f"Ladebytes         : "
                f"{raw_file_data[0]:02X} {raw_file_data[1]:02X}"
            )
        lines.append(
            f"Ladeadresse       : ${analysis.load_address:04X} "
            f"({analysis.load_address})"
        )
        lines.append(f"Speicherbelegung  : {memory_layout}")
        lines.append(
            "Adressumlauf      : "
            + (
                "ja, über $FFFF nach $0000"
                if wraps
                else "nein"
            )
        )

    if analysis.sys_entry is not None:
        lines.extend(
            [
                f"BASIC-Zeile       : {analysis.sys_entry.line_number} "
                f"SYS {analysis.sys_entry.address}",
                f"SYS-Einsprung     : ${analysis.sys_entry.address:04X} "
                f"({analysis.sys_entry.address})",
            ]
        )
    else:
        lines.extend(
            [
                "BASIC-Zeile       : kein statisch auswertbarer SYS-Befehl",
                "SYS-Einsprung     : nicht bestimmbar",
            ]
        )

    lines.extend(
        [
            f"SHA-256           : {analysis.sha256}",
            "",
            "",
            "2. Startanalyse",
            "----------------",
            "",
        ]
    )

    if analysis.load_address is None:
        lines.extend(
            [
                "Die Datei ist kürzer als zwei Bytes und besitzt daher keine",
                "vollständige PRG-Ladeadresse. Sie ist als C64-PRG strukturell",
                "nicht vollständig.",
            ]
        )
    elif analysis.sys_entry is not None:
        lines.extend(
            [
                "Die ersten beiden Bytes speichern die Ladeadresse in",
                "Little-Endian-Reihenfolge. Im tokenisierten BASIC-Programm",
                "wurde ein direkt auswertbarer SYS-Befehl gefunden.",
                "",
                f"RUN führt BASIC-Zeile {analysis.sys_entry.line_number} aus "
                f"und übergibt die",
                f"Kontrolle mit SYS {analysis.sys_entry.address} an "
                f"${analysis.sys_entry.address:04X}.",
            ]
        )
    elif analysis.load_address == 0x0801:
        lines.extend(
            [
                "Die Datei lädt an die übliche Startadresse eines C64-BASIC-",
                "Programms. Ein direkt auswertbarer SYS-Befehl wurde jedoch",
                "nicht gefunden; der weitere Ablauf ist statisch unbekannt.",
            ]
        )
    else:
        lines.extend(
            [
                "Die Datei besitzt eine gültige PRG-Ladeadresse. Das PRG-Format",
                "speichert jedoch keinen allgemeinen Ausführungseinsprung.",
                "Ohne BASIC-SYS oder programmspezifische Disassemblierung ist",
                "die erste ausgeführte Maschinenroutine nicht sicher bestimmbar.",
            ]
        )

    lines.extend(
        [
            "",
            "",
            "3. Struktur- und Inhaltsanalyse",
            "--------------------------------",
            "",
        ]
    )

    if payload:
        lines.extend(
            [
                f"Shannon-Entropie : {statistics.entropy:.3f} "
                "von maximal 8,000 Bit/Byte",
                f"Bytewerte benutzt: {statistics.unique_byte_values} von 256",
                f"Druckbares ASCII : "
                f"{statistics.printable_ascii_percent:.1f} %",
                f"Nullbytes        : {statistics.zero_percent:.1f} %",
                f"$FF-Bytes        : {statistics.ff_percent:.1f} %",
                f"Längster Gleichlauf: "
                f"{statistics.longest_equal_byte_run} gleiche Bytes",
                f"Nutzdatenanfang  : {hexadecimal_preview(payload)}",
                "",
            ]
        )
        lines.extend(structure_assessment(analysis, raw_file_data))
        lines.extend(
            [
                "",
                "Zufällig druckbare Zeichenfolgen in Binärdaten werden nicht",
                "automatisch als Programmmeldungen gewertet. Verlässliche Texte",
                "erfordern eine passende PETSCII-/Datenformat- oder",
                "Entpackanalyse.",
            ]
        )
    else:
        lines.append("Keine Nutzdaten für eine statistische Analyse vorhanden.")

    region_notes = known_memory_region_notes(
        analysis.load_address,
        analysis.payload_size,
    )
    if region_notes:
        lines.extend(
            [
                "",
                "Berührte Speicherbereiche:",
                *(f"- {note}" for note in region_notes),
            ]
        )

    lines.extend(
        [
            "",
            "",
            "4. Prüfergebnis",
            "---------------",
            "",
            "Die Containerdaten und der statisch erkennbare Programmstart wurden",
            "einschließlich Speicherbelegung und Byteverteilung ausgewertet. Für",
            "diese Prüfsumme ist kein verifiziertes programmspezifisches",
            "Tiefenprofil hinterlegt; mögliche Entpacker-, Selbstmodifikations-",
            "oder endgültige Spieleinsprünge werden daher nicht ungesichert",
            "behauptet.",
            "",
        ]
    )
    return "\n".join(lines)


def build_prg_analysis_report(
    filename: str,
    file_data: bytes,
    *,
    c64_filename: str | None = None,
) -> str:
    """Erzeugt den passenden vollständigen Textbericht für eine PRG-Datei."""
    analysis = inspect_prg_data(
        filename,
        file_data,
        c64_filename=c64_filename,
    )

    if analysis.is_known_dalek_attack_tsm:
        return build_dalek_attack_tsm_report(analysis)
    if analysis.sha256 == DALEK_INTRO_SHA256:
        return build_dalek_intro_report(analysis, file_data)

    sequence_number = DALEK_NUMBERED_PRG_PROFILES.get(analysis.sha256)
    if sequence_number is not None:
        return build_dalek_numbered_report(
            analysis,
            file_data,
            sequence_number,
        )

    return build_generic_prg_report(analysis, file_data)


def build_startup_info_lines(
    image: D64Image,
    entries: list[DirectoryEntry],
) -> list[str]:
    """
    Ermittelt die wahrscheinlich zuerst geladene PRG-Datei und ihren Einsprung.

    Ein D64-Verzeichnis besitzt kein Autostart-Attribut. Als Startkandidat gilt
    deshalb der erste aktive PRG-Eintrag, den auch LOAD"*",8,1 auswählt.
    """
    lines = ["Programmstart (heuristische Analyse)"]

    first_prg = next(
        (
            entry
            for entry in entries
            if entry.type_name == "PRG" and entry.file_type_byte != 0
        ),
        None,
    )

    if first_prg is None:
        lines.append("Startdatei     : kein aktiver PRG-Eintrag gefunden")
        lines.append("Einsprung      : nicht bestimmbar")
        return lines

    lines.append(f"Startdatei     : {first_prg.filename!r}")
    lines.append(
        f"Auswahl        : erster PRG-Eintrag im Verzeichnis; "
        f'LOAD"*",8,1 würde diese Datei laden'
    )
    lines.append(
        f"Startblock     : "
        f"{first_prg.start_track:02d}/{first_prg.start_sector:02d}"
    )

    try:
        file_data = image.read_file_data(first_prg)
    except D64Error as exc:
        lines.append(f"Ladeadresse    : nicht lesbar ({exc})")
        lines.append("Einsprung      : nicht bestimmbar")
        return lines

    if len(file_data) < 2:
        lines.append(
            "Ladeadresse    : nicht vorhanden (PRG ist kürzer als 2 Bytes)"
        )
        lines.append("Einsprung      : nicht bestimmbar")
        return lines

    load_address = int.from_bytes(file_data[:2], "little")
    program_data = file_data[2:]
    lines.append(f"Ladeadresse    : ${load_address:04X} ({load_address})")

    sys_entry = find_basic_sys_entry(program_data, load_address)
    if sys_entry is not None:
        lines.append(
            f"Einsprung      : ${sys_entry.address:04X} "
            f"({sys_entry.address}), erkannt aus "
            f"BASIC-Zeile {sys_entry.line_number}: SYS {sys_entry.address}"
        )
        lines.append(
            "Ausführung     : RUN startet den BASIC-Loader und SYS "
            "übergibt an den Maschinencode"
        )
    elif load_address == 0x0801:
        lines.append(
            "Einsprung      : kein statisch auswertbarer BASIC-SYS gefunden"
        )
        lines.append(
            "Ausführung     : wahrscheinlich über RUN; genauer Start unbekannt"
        )
    else:
        lines.append(
            "Einsprung      : im PRG-Format nicht gespeichert und "
            "nicht sicher bestimmbar"
        )

    lines.append(
        "Hinweis        : Ein D64 enthält kein allgemeines Autostart-Feld; "
        "die Startdatei ist daher eine begründete Annahme."
    )
    return lines


def image_output_directory(image: D64Image) -> Path:
    """Erstellt den gemeinsamen Ausgabeordner mit dem Basisnamen des Images."""
    output_directory = image.path.parent / image.path.stem

    if output_directory.exists() and not output_directory.is_dir():
        raise D64Error(
            f"Ziel für die Ausgabe ist kein Verzeichnis: "
            f"{output_directory}"
        )

    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise D64Error(
            f"Zielverzeichnis kann nicht erstellt werden: "
            f"{output_directory}: {exc}"
        ) from exc

    return output_directory


def print_and_save_startup_info(
    image: D64Image,
    entries: list[DirectoryEntry],
    *,
    verbose: bool = True,
    complete_information: str | None = None,
) -> Path:
    """
    Speichert die gesammelten Informationen im Image-Ausgabeverzeichnis.

    Ohne ``complete_information`` bleibt die Funktion abwärtskompatibel und
    schreibt nur die Startanalyse. Der Hauptablauf übergibt den vollständigen
    Konsolenbericht, damit ``startup_info.txt`` exakt dieselben Informationen
    wie die normale Ausgabe enthält.
    """
    lines = build_startup_info_lines(image, entries)
    output_directory = image_output_directory(image)
    output_path = output_directory / "startup_info.txt"
    information = (
        complete_information
        if complete_information is not None
        else "\n".join(lines) + "\n"
    )

    try:
        output_path.write_text(
            information,
            encoding="utf-8",
        )
    except OSError as exc:
        raise D64Error(
            f"Startinformationen können nicht geschrieben werden: "
            f"{output_path}: {exc}"
        ) from exc

    if verbose:
        if complete_information is not None:
            print(information, end="")
        else:
            print()
            print("\n".join(lines))
            print(f"Informationsdatei: {output_path}")
    return output_path


def save_prg_analysis_report(
    output_path: Path,
    file_data: bytes,
    *,
    c64_filename: str,
) -> Path:
    """
    Speichert die Analyse neben der zugehörigen PRG-Datei.

    Die ursprüngliche Endung bleibt Bestandteil des Namens:
    ``SPIEL.prg`` wird zu ``SPIEL.prg.txt``.
    """
    report_path = output_path.with_name(output_path.name + ".txt")
    information = build_prg_analysis_report(
        output_path.name,
        file_data,
        c64_filename=c64_filename,
    )

    try:
        report_path.write_text(
            information,
            encoding="utf-8",
            newline="",
        )
    except OSError as exc:
        raise D64Error(
            f"PRG-Analyse kann nicht geschrieben werden: "
            f"{report_path}: {exc}"
        ) from exc

    return report_path


def write_prg_analysis_reports(
    image: D64Image,
    entries: list[DirectoryEntry],
    *,
    verbose: bool = True,
) -> tuple[Path, int]:
    """Analysiert alle aktiven PRG-Einträge, ohne sie extrahieren zu müssen."""
    output_directory = image_output_directory(image)
    prg_entries = [
        entry
        for entry in entries
        if entry.type_name == "PRG" and entry.file_type_byte != 0
    ]
    used_names: set[str] = set()
    analysis_count = 0

    if verbose:
        print()
        print("PRG-Programmanalyse")
        print(f"Zielverzeichnis: {output_directory}")

    if not prg_entries:
        if verbose:
            print("Keine aktiven PRG-Dateien gefunden.")
        return output_directory, analysis_count

    for entry in prg_entries:
        output_name = unique_prg_filename(entry.filename, used_names)
        output_path = output_directory / output_name
        file_data = image.read_file_data(entry)
        report_path = save_prg_analysis_report(
            output_path,
            file_data,
            c64_filename=entry.filename,
        )
        analysis_count += 1

        if verbose:
            print(
                f"Analysiert      : {report_path.name} "
                f"({len(file_data)} PRG-Bytes, {entry.filename!r})"
            )

    if verbose:
        print(f"Ergebnis        : {analysis_count} Programmanalysen erstellt")
    return output_directory, analysis_count


def extract_prg_files(
    image: D64Image,
    entries: list[DirectoryEntry],
    *,
    overwrite: bool,
    verbose: bool = True,
) -> tuple[Path, int, int]:
    """
    Extrahiert aktive PRG-Dateien in einen Ordner neben dem D64-Image.

    Der Zielordner trägt den Basisnamen des Images. Die extrahierten Dateien
    enthalten die PRG-Daten unverändert, also einschließlich der ersten beiden
    Bytes mit der C64-Ladeadresse. Zusätzlich entsteht zu jeder PRG-Datei ein
    vollständiger Bericht nach dem Namensschema ``<Programm>.prg.txt``.
    """
    output_directory = image_output_directory(image)

    prg_entries = [
        entry
        for entry in entries
        if entry.type_name == "PRG" and entry.file_type_byte != 0
    ]
    used_names: set[str] = set()
    extracted_count = 0
    skipped_count = 0

    if verbose:
        print()
        print("PRG-Extraktion")
        print(f"Zielverzeichnis: {output_directory}")

    if not prg_entries:
        if verbose:
            print("Keine aktiven PRG-Dateien gefunden.")
        return output_directory, extracted_count, skipped_count

    for entry in prg_entries:
        output_name = unique_prg_filename(entry.filename, used_names)
        output_path = output_directory / output_name
        file_data = image.read_file_data(entry)

        if output_path.exists() and not overwrite:
            if verbose:
                print(
                    f"Übersprungen    : {output_name} "
                    "(bereits vorhanden)"
                )
            skipped_count += 1
        else:
            try:
                output_path.write_bytes(file_data)
            except OSError as exc:
                raise D64Error(
                    f"PRG-Datei kann nicht geschrieben werden: "
                    f"{output_path}: {exc}"
                ) from exc

            if verbose:
                print(
                    f"Extrahiert      : {output_name} "
                    f"({len(file_data)} Bytes, {entry.filename!r})"
                )
            extracted_count += 1

        report_path = save_prg_analysis_report(
            output_path,
            file_data,
            c64_filename=entry.filename,
        )
        if verbose:
            print(
                f"Analyse         : {report_path.name} "
                f"({entry.filename!r})"
            )

    if verbose:
        print(
            f"Ergebnis        : {extracted_count} extrahiert, "
            f"{skipped_count} übersprungen"
        )
    return output_directory, extracted_count, skipped_count


def collect_prg_extraction_information(
    image: D64Image,
    entries: list[DirectoryEntry],
    *,
    overwrite: bool,
) -> str:
    """
    Führt die PRG-Extraktion aus und sammelt ihren vollständigen Bericht.

    Der zurückgegebene Text enthält das Zielverzeichnis, jede extrahierte oder
    übersprungene Datei sowie die Ergebniszusammenfassung. Der Aufrufer kann
    ihn dadurch ausdrücklich an den übrigen Bericht anhängen, ohne von einer
    vorübergehenden Umleitung der Konsolenausgabe abhängig zu sein.
    """
    output = io.StringIO()

    with redirect_stdout(output):
        extract_prg_files(
            image,
            entries,
            overwrite=overwrite,
            verbose=True,
        )

    return output.getvalue()


def collect_prg_analysis_information(
    image: D64Image,
    entries: list[DirectoryEntry],
) -> str:
    """Erzeugt PRG-Berichte und sammelt die zugehörigen Statusmeldungen."""
    output = io.StringIO()

    with redirect_stdout(output):
        write_prg_analysis_reports(
            image,
            entries,
            verbose=True,
        )

    return output.getvalue()


def collect_startup_prg_analysis_information(
    image: D64Image,
    entries: list[DirectoryEntry],
) -> str:
    """Analysiert bei ``--startup`` genau den ersten aktiven PRG-Eintrag."""
    first_prg = next(
        (
            entry
            for entry in entries
            if entry.type_name == "PRG" and entry.file_type_byte != 0
        ),
        None,
    )
    selected_entries = [first_prg] if first_prg is not None else []
    return collect_prg_analysis_information(image, selected_entries)


def disassemble_first_prg(
    image: D64Image,
    entries: list[DirectoryEntry],
    *,
    verbose: bool = True,
) -> tuple[Path, Path | None, Path | None]:
    """
    Extrahiert und disassembliert den ersten aktiven PRG-Verzeichniseintrag.

    Diese Auswahl entspricht der Datei, die LOAD"*",8,1 laden würde.
    """
    output_directory = image_output_directory(image)
    first_prg = next(
        (
            entry
            for entry in entries
            if entry.type_name == "PRG" and entry.file_type_byte != 0
        ),
        None,
    )

    if verbose:
        print()
        print("6510-Disassemblierung")
        print(f"Zielverzeichnis: {output_directory}")

    if first_prg is None:
        if verbose:
            print("Keine aktive PRG-Datei gefunden.")
        return output_directory, None, None

    output_name = unique_prg_filename(first_prg.filename, set())
    prg_path = output_directory / output_name
    listing_path = prg_path.with_name(prg_path.name + ".asm")
    file_data = image.read_file_data(first_prg)

    try:
        prg_path.write_bytes(file_data)
        listing_path.write_text(
            build_prg_disassembly(
                prg_path.name,
                file_data,
                c64_filename=first_prg.filename,
            ),
            encoding="utf-8",
            newline="",
        )
    except OSError as exc:
        raise D64Error(
            f"Disassembly-Dateien können nicht geschrieben werden: {exc}"
        ) from exc

    if verbose:
        print(
            f"Ausgewählte PRG : {first_prg.filename!r} "
            "(erster aktiver PRG-Eintrag)"
        )
        print(
            f"Extrahiert      : {prg_path.name} "
            f"({len(file_data)} Bytes)"
        )
        print(f"Disassembly     : {listing_path.name}")
        print(
            "Hinweis         : Gepackte Daten werden als .byte ausgegeben; "
            "nur statisch erkennbare 6510-Codebereiche werden disassembliert."
        )

    return output_directory, prg_path, listing_path


def collect_disassembly_information(
    image: D64Image,
    entries: list[DirectoryEntry],
) -> str:
    """Führt die Disassemblierung aus und sammelt ihre Statusinformationen."""
    output = io.StringIO()
    with redirect_stdout(output):
        disassemble_first_prg(image, entries, verbose=True)
    return output.getvalue()


def print_image_info(
    image: D64Image,
    *,
    show_bam: bool,
    show_chains: bool,
    show_startup: bool,
    include_deleted: bool,
) -> None:
    geometry = image.geometry
    entries = image.directory_entries(include_deleted=include_deleted)
    bam_tracks = image.bam_tracks()

    print(f"Datei          : {image.path}")
    print(f"Größe          : {len(image.raw):,} Bytes".replace(",", "."))
    print(f"SHA-256        : {image.sha256}")
    print(
        f"Geometrie      : {geometry.tracks} Spuren, "
        f"{geometry.sectors} Sektoren, {SECTOR_SIZE} Bytes/Sektor"
    )
    print(
        "Fehlertabelle  : "
        + (
            f"ja ({len(image.error_table)} Bytes)"
            if geometry.has_error_table
            else "nein"
        )
    )
    print(f"Diskettenname  : {image.disk_name!r}")
    print(f"Disk-ID        : {image.disk_id!r}")
    print(f"DOS-Typ        : {image.dos_type!r}")
    print(f"Header-Zusatz  : {image.header_suffix!r}")
    print(f"DOS-Version    : {image.dos_version!r}")
    print()

    print("Verzeichnis")
    print(
        f"{'Blöcke':>6}  {'Typ':<5}  {'Start':>7}  "
        f"{'Nutzbytes':>10}  Dateiname"
    )
    print(f"{'-' * 6}  {'-' * 5}  {'-' * 7}  {'-' * 10}  {'-' * 16}")

    chains: list[tuple[DirectoryEntry, FileChain]] = []
    for entry in entries:
        chain = image.read_file_chain(entry)
        chains.append((entry, chain))
        data_size = str(chain.data_bytes)
        if chain.error:
            data_size += " !"

        print(
            f"{entry.blocks:6d}  {entry.type_display:<5}  "
            f"{entry.start_track:02d}/{entry.start_sector:02d}  "
            f"{data_size:>10}  {entry.filename!r}"
        )

    if not entries:
        print("(keine Einträge)")

    free_blocks = sum(track.free_count for track in bam_tracks)
    used_directory_blocks = sum(entry.blocks for entry in entries)
    print()
    print(f"Dateien        : {len(entries)}")
    print(f"Dateiblöcke    : {used_directory_blocks}")
    print(f"Freie Blöcke   : {free_blocks} (laut BAM)")

    inconsistent = [track.track for track in bam_tracks if not track.is_consistent]
    if inconsistent:
        tracks = ", ".join(str(track) for track in inconsistent)
        print(f"BAM-Warnung    : Zähler/Bitmap abweichend auf Spur(en) {tracks}")

    chain_warnings = [
        (entry.filename, chain.error)
        for entry, chain in chains
        if chain.error is not None
    ]
    for filename, error in chain_warnings:
        print(f"Kettenwarnung  : {filename!r}: {error}")

    if show_startup:
        print_and_save_startup_info(image, entries)

    if show_chains:
        print()
        print("Dateiketten")
        for entry, chain in chains:
            locations = " -> ".join(
                f"{track}/{sector}" for track, sector in chain.sectors
            )
            if not locations:
                locations = "(leer)"
            print(f"{entry.filename!r}: {locations}")

    if show_bam:
        print()
        print("BAM (1 = Sektor frei)")
        print(
            f"{'Spur':>4}  {'frei':>4}  {'gesamt':>6}  "
            f"{'Bitmap':>6}  freie Sektoren"
        )
        print(f"{'-' * 4}  {'-' * 4}  {'-' * 6}  {'-' * 6}  {'-' * 14}")
        for track in bam_tracks:
            marker = "" if track.is_consistent else " !"
            sector_list = ",".join(str(value) for value in track.free_sectors)
            print(
                f"{track.track:4d}  {track.free_count:4d}  "
                f"{track.total_count:6d}  "
                f"{track.bitmap_free_count:6d}{marker}  {sector_list}"
            )

        if geometry.tracks > 35:
            print()
            print(
                "Hinweis: Die Standard-BAM deckt nur die Spuren 1 bis 35 ab; "
                "erweiterte BAM-Formate sind nicht einheitlich."
            )


def collect_information(
    image: D64Image,
    *,
    show_bam: bool,
    show_chains: bool,
    show_startup: bool,
    include_deleted: bool,
) -> tuple[str, list[DirectoryEntry]]:
    """
    Sammelt den vollständigen Informationsbericht in einem Text.

    Die Ausgabe wird zunächst gepuffert. Dadurch erhalten Konsole und
    ``startup_info.txt`` bei ``--startup`` denselben vollständigen Inhalt.
    """
    entries = image.directory_entries(include_deleted=include_deleted)
    output = io.StringIO()

    with redirect_stdout(output):
        print_image_info(
            image,
            show_bam=show_bam,
            show_chains=show_chains,
            show_startup=False,
            include_deleted=include_deleted,
        )

        if show_startup:
            print()
            print("\n".join(build_startup_info_lines(image, entries)))
            print(
                "Informationsdatei: "
                f"{image.path.parent / image.path.stem / 'startup_info.txt'}"
            )

    return output.getvalue(), entries


def write_complete_startup_report(
    image: D64Image,
    *,
    show_bam: bool,
    show_chains: bool,
    include_deleted: bool,
    extract_prg: bool,
    analyze_prg: bool,
    disassemble: bool,
    overwrite: bool,
    show_console: bool,
) -> Path:
    """
    Schreibt alle normalen Ausgaben eines ``--startup``-Laufs in eine Datei.

    Die Textdatei ist die maßgebliche Ausgabe. Ohne ``--verbose`` wird derselbe
    Datenstrom zusätzlich auf die Konsole gespiegelt. Damit gehören auch die
    Verzeichnisangaben, die heuristische Startanalyse sowie optionale BAM-,
    Ketten- und Extraktionsinformationen garantiert zum gespeicherten Bericht.
    """
    information, entries = collect_information(
        image,
        show_bam=show_bam,
        show_chains=show_chains,
        show_startup=True,
        include_deleted=include_deleted,
    )
    output_directory = image_output_directory(image)
    output_path = output_directory / "startup_info.txt"

    if extract_prg:
        information += collect_prg_extraction_information(
            image,
            entries,
            overwrite=overwrite,
        )
    elif analyze_prg:
        information += collect_prg_analysis_information(
            image,
            entries,
        )
    else:
        information += collect_startup_prg_analysis_information(
            image,
            entries,
        )

    if disassemble:
        information += collect_disassembly_information(image, entries)

    try:
        with output_path.open("w", encoding="utf-8", newline="") as report:
            streams: tuple[TextIO, ...]
            if show_console:
                streams = (report, sys.stdout)
            else:
                streams = (report,)

            with redirect_stdout(TeeTextWriter(*streams)):
                print(information, end="")
    except OSError as exc:
        raise D64Error(
            f"Startinformationen können nicht geschrieben werden: "
            f"{output_path}: {exc}"
        ) from exc

    return output_path


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Zeigt Geometrie, BAM-Kopfdaten und Verzeichnis eines "
            "Commodore-D64-Diskettenabbilds an."
        )
    )
    parser.add_argument("image", type=Path, help="Pfad zur .d64-Datei")
    parser.add_argument(
        "--bam",
        action="store_true",
        help="zusätzlich die Block Allocation Map je Spur anzeigen",
    )
    parser.add_argument(
        "--chains",
        action="store_true",
        help="zusätzlich die Spur-/Sektorketten aller Dateien anzeigen",
    )
    parser.add_argument(
        "--deleted",
        action="store_true",
        help="auch noch vorhandene gelöschte Verzeichniseinträge anzeigen",
    )
    parser.add_argument(
        "--startup",
        "--start",
        "--entry-point",
        dest="show_startup",
        action="store_true",
        help=(
            "wahrscheinliche Startdatei, PRG-Ladeadresse und erkannten "
            "BASIC-SYS-Einsprung anzeigen und den vollständigen "
            "Informationsbericht als startup_info.txt in einem Verzeichnis "
            "mit dem Basisnamen des D64-Images speichern; für die Start-PRG "
            "wird zusätzlich <Programm>.prg.txt erstellt"
        ),
    )
    parser.add_argument(
        "--extract-prg",
        "--extract",
        dest="extract_prg",
        action="store_true",
        help=(
            "alle aktiven PRG-Dateien in ein Verzeichnis mit dem Basisnamen "
            "des D64-Images extrahieren"
        ),
    )
    parser.add_argument(
        "--analyze-prg",
        "--analyse-prg",
        dest="analyze_prg",
        action="store_true",
        help=(
            "für alle aktiven PRG-Dateien vollständige Textberichte nach dem "
            "Namensschema <Programm>.prg.txt erstellen; --extract-prg führt "
            "diese Analyse automatisch mit aus"
        ),
    )
    parser.add_argument(
        "--disassemble",
        action="store_true",
        help=(
            "die erste aktive PRG-Datei (wie bei LOAD\"*\",8,1) extrahieren "
            "und daneben ein adressiertes 6510-Listing <Programm>.prg.asm "
            "erstellen"
        ),
    )
    parser.add_argument(
        "--image-ram",
        action="store_true",
        help=(
            "das D64 mit VICE autostarten, am --ram-breakpoint anhalten und "
            "die vollständige physische 64-KiB-RAM-Bank als "
            "<Image>_ram.bin speichern"
        ),
    )
    parser.add_argument(
        "--disassemble-code",
        action="store_true",
        help=(
            "den vollständigen RAM erfassen und statisch erreichbaren "
            "MOS-6510-Code als <Image>_ram.asm ausgeben; beim bekannten "
            "Dalek-Abbild werden Intro, Raster-IRQ, FIRE-Ausgang und "
            "Spielentpacker getrennt berücksichtigt"
        ),
    )
    parser.add_argument(
        "--ram-input",
        type=Path,
        help=(
            "vorhandenes rohes 65.536-Byte-RAM-Abbild verwenden; damit kann "
            "--disassemble-code ohne gestartetes VICE ausgeführt werden"
        ),
    )
    parser.add_argument(
        "--vice",
        type=Path,
        help=(
            "Pfad zu x64sc.exe beziehungsweise x64sc; ohne Angabe wird "
            "x64sc über PATH gesucht"
        ),
    )
    parser.add_argument(
        "--ram-breakpoint",
        type=parse_address,
        default=0x4100,
        help=(
            "Ausführungsadresse zum Anhalten und als Code-Einsprung "
            "verwenden (Standard: 0x4100)"
        ),
    )
    parser.add_argument(
        "--ram-bank",
        default="ram",
        help=(
            "Name der von VICE gemeldeten Speicherbank "
            "(Standard: ram = physischer RAM)"
        ),
    )
    parser.add_argument(
        "--vice-host",
        default="127.0.0.1",
        help="Adresse des binären VICE-Monitors (Standard: 127.0.0.1)",
    )
    parser.add_argument(
        "--vice-port",
        type=int,
        default=6502,
        help="Port des binären VICE-Monitors (Standard: 6502)",
    )
    parser.add_argument(
        "--vice-file-index",
        type=int,
        default=0,
        help=(
            "Dateiindex im D64 für VICE-Autostart "
            "(Standard: 0 = erste Datei)"
        ),
    )
    parser.add_argument(
        "--vice-connect-timeout",
        type=float,
        default=20.0,
        help="Sekunden zum Verbindungsaufbau mit VICE (Standard: 20)",
    )
    parser.add_argument(
        "--vice-run-timeout",
        type=float,
        default=180.0,
        help="Sekunden bis zum RAM-Haltepunkt (Standard: 180)",
    )
    parser.add_argument(
        "--vice-connect-only",
        action="store_true",
        help=(
            "kein neues x64sc starten, sondern den bereits laufenden "
            "binären VICE-Monitor verwenden"
        ),
    )
    parser.add_argument(
        "--keep-vice",
        action="store_true",
        help="VICE nach dem RAM-Abbild am Haltepunkt geöffnet lassen",
    )
    parser.add_argument(
        "--vice-no-warp",
        action="store_true",
        help="VICE für die RAM-Erfassung nicht im Warp-Modus starten",
    )
    parser.add_argument(
        "--vice-snapshot",
        action="store_true",
        help="zusätzlich einen vollständigen VICE-Snapshot (.vsf) speichern",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "bei --extract-prg bereits vorhandene PRG-Dateien überschreiben"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Informations- und Statusausgaben auf der Konsole unterdrücken; "
            "Fehlermeldungen werden weiterhin ausgegeben"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(sys.argv[1:] if argv is None else argv)

    if args.overwrite and not args.extract_prg:
        print(
            "Fehler: --overwrite kann nur zusammen mit --extract-prg "
            "verwendet werden.",
            file=sys.stderr,
        )
        return 2
    if args.ram_input is not None and args.image_ram:
        print(
            "Fehler: --ram-input und --image-ram können nicht zusammen "
            "verwendet werden.",
            file=sys.stderr,
        )
        return 2
    if args.ram_input is not None and not args.disassemble_code:
        print(
            "Fehler: --ram-input ist für --disassemble-code vorgesehen.",
            file=sys.stderr,
        )
        return 2
    if args.ram_input is not None and not args.ram_input.is_file():
        print(
            f"Fehler: RAM-Eingabedatei nicht gefunden: {args.ram_input}",
            file=sys.stderr,
        )
        return 2
    if not 1 <= args.vice_port <= 65535:
        print(
            "Fehler: --vice-port muss zwischen 1 und 65535 liegen.",
            file=sys.stderr,
        )
        return 2
    if not 0 <= args.vice_file_index <= 65535:
        print(
            "Fehler: --vice-file-index muss zwischen 0 und 65535 liegen.",
            file=sys.stderr,
        )
        return 2

    try:
        image = D64Image(args.image)

        if args.show_startup:
            write_complete_startup_report(
                image,
                show_bam=args.bam,
                show_chains=args.chains,
                include_deleted=args.deleted,
                extract_prg=args.extract_prg,
                analyze_prg=args.analyze_prg,
                disassemble=args.disassemble,
                overwrite=args.overwrite,
                show_console=not args.verbose,
            )
        else:
            information, entries = collect_information(
                image,
                show_bam=args.bam,
                show_chains=args.chains,
                show_startup=False,
                include_deleted=args.deleted,
            )

            if not args.verbose:
                print(information, end="")

            if args.extract_prg:
                extract_prg_files(
                    image,
                    entries,
                    overwrite=args.overwrite,
                    verbose=not args.verbose,
                )
            elif args.analyze_prg:
                write_prg_analysis_reports(
                    image,
                    entries,
                    verbose=not args.verbose,
                )

            if args.disassemble:
                disassemble_first_prg(
                    image,
                    entries,
                    verbose=not args.verbose,
                )

        process_ram_options(
            image,
            image_ram=args.image_ram,
            disassemble_code=args.disassemble_code,
            ram_input=args.ram_input,
            vice_path=args.vice,
            host=args.vice_host,
            port=args.vice_port,
            breakpoint=args.ram_breakpoint,
            bank_name=args.ram_bank,
            file_index=args.vice_file_index,
            connect_timeout=args.vice_connect_timeout,
            run_timeout=args.vice_run_timeout,
            warp=not args.vice_no_warp,
            keep_vice=args.keep_vice,
            connect_only=args.vice_connect_only,
            save_snapshot=args.vice_snapshot,
            verbose=not args.verbose,
        )
    except D64Error as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

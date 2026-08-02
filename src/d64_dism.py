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
#  * Neu/Oeffnen/Speichern/Speichern unter mit sicherer Schliessabfrage
#  * Syntax-Hervorhebung fuer 6502/6510-Assembler und Kommentare
#  * integrierter 6502/6510-Assembler mit C64-PRG- und VICE-Start
#  * ANTLR-basierte C64-Compiler fuer Pascal und C mit 6510-Zwischencode
#  * Operanden-Rechner fuer Dezimal-, Hexadezimal- und Binaerwerte
#  * integrierter CHM-Viewer mit Themen, Keywords und Favoriten
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
import hashlib
import html

from html.parser import HTMLParser

import json
import os
import re
import shutil
import subprocess
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
# Qt5-Anwendung
# ---------------------------------------------------------------------------
def run_gui(initial_directory: Optional[Path] = None) -> int:
    try:
        from PyQt5.QtCore import (
            QDir,
            QFileInfo,
            QObject,
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
            QDialog,
            QDockWidget,
            QFileDialog,
            QFileIconProvider,
            QFileSystemModel,
            QFrame,
            QGridLayout,
            QHBoxLayout,
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
        )
        OPCODE_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:"
            + "|".join(OPCODES)
            + r")(?![A-Za-z0-9_])",
            re.IGNORECASE,
        )
        LABEL_PATTERN = re.compile(
            r"^\s*(?P<label>[A-Za-z_.$][A-Za-z0-9_.$]*)\s*:",
        )
        JUMP_TARGET_PATTERN = re.compile(
            r"^\s*(?:[A-Za-z_.$][A-Za-z0-9_.$]*\s*:\s*)?"
            r"(?:BCC|BCS|BEQ|BMI|BNE|BPL|BVC|BVS|JMP|JSR)\s+"
            r"(?:\(\s*)?"
            r"(?P<target>[A-Za-z_.$][A-Za-z0-9_.$]*)",
            re.IGNORECASE,
        )
        PASCAL_KEYWORD_PATTERN = re.compile(
            r"(?<![A-Za-z0-9_])(?:"
            r"program|const|var|begin|end|if|then|else|while|do|"
            r"repeat|until|for|to|downto|break|continue|integer|"
            r"byte|char|boolean|true|false|div|mod|and|or|xor|not"
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

        def sizeHint(self) -> QSize:
            return QSize(self.editor.line_number_area_width(), 0)

        def paintEvent(self, event) -> None:
            self.editor.line_number_area_paint_event(event)

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

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self._dark_mode = False
            self._completion_enabled = False
            self._completion_context = None
            self._assembler_navigation_enabled = False
            self._assembler_highlighter = None
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
                r"(?P<opcode>[A-Za-z]{3})(?P<spacing>\s+)"
                r"(?P<operand>.*?)\s*$",
                code,
            )
            if (
                match is None
                or match.group("opcode").upper() not in ASSEMBLER_COMMANDS
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

        @staticmethod
        def _completion_candidates(prefix: str):
            wanted = prefix.upper()
            return tuple(
                info
                for mnemonic, info in ASSEMBLER_COMMANDS.items()
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

            word_match = re.search(r"([A-Za-z]{1,3})$", text_before_cursor)
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
            if self.completion_frame.isVisible():
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    self._accept_completion()
                    event.accept()
                    return
                if event.key() == Qt.Key_F1:
                    self._show_completion_help()
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

        def line_number_area_width(self) -> int:
            digits = max(1, len(str(max(1, self.blockCount()))))
            return 10 + self.fontMetrics().horizontalAdvance("9") * digits

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

            painter.setPen(foreground)
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    painter.drawText(
                        0,
                        top,
                        self.line_number_area.width() - 5,
                        self.fontMetrics().height(),
                        Qt.AlignRight,
                        str(block_number + 1),
                    )

                block = block.next()
                top = bottom
                block_number += 1
                if block.isValid():
                    bottom = top + round(self.blockBoundingRect(block).height())

            painter.setPen(separator)
            painter.drawLine(
                self.line_number_area.width() - 1,
                event.rect().top(),
                self.line_number_area.width() - 1,
                event.rect().bottom(),
            )
            
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

        ASSEMBLER_EXTENSIONS = {".asm", ".s", ".a65", ".inc"}
        PASCAL_EXTENSIONS    = {".pas", ".pp"}
        C_EXTENSIONS         = {".c"}
        C_HEADER_EXTENSIONS  = {".h"}
        BINARY_EXTENSIONS    = {".prg", ".ram", ".bin"}

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
            self.untitled_number         = untitled_number
            self.encoding                = encoding
            self.newline                 = newline
            self._syncing_views          = False
            self._data_source            = "text"
            self._last_modified_state    = False
            self.assembled_program       = None
            self.assembled_program_path: Optional[Path] = None
            self.assembled_source_digest = ""

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
            assembler_panel_layout.addWidget(self.assembly_status_label, 1)
            source_layout.addWidget(self.assembler_panel)

            self.raw_editor = SourceTextEdit(self.source_page)
            self.raw_editor.setObjectName("raw_data_editor")
            self.raw_editor.setFont(fixed_font)
            self.raw_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
            self.raw_editor.assembler_help_requested.connect(
                self._show_assembler_help
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
            self.update_syntax_highlighting()

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
            self.hints_editor.setPlaceholderText(
                "Hinweise werden später an dieser Stelle angezeigt."
            )
            self.views.addTab(self.hints_editor, "Hinweise")

            self.raw_editor.textChanged.connect(self._raw_text_changed)
            self.raw_editor.document().modificationChanged.connect(
                self._view_modification_changed
            )

            if (
                self.path is not None
                and self.path.suffix.lower() in self.BINARY_EXTENSIONS
            ):
                self.views.setCurrentWidget(self.hex_editor)

            layout.addWidget(self.views)
            self.set_dark_mode(dark_mode)

        @property
        def display_name(self) -> str:
            if self.path is not None:
                return self.path.name
            return f"Unbenannt {self.untitled_number}"

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

        def _raw_text_changed(self) -> None:
            if self._syncing_views:
                return
            self.invalidate_assembly_result("Quelltext geändert")
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

        def update_syntax_highlighting(self) -> None:
            is_assembler = (
                self.path is not None
                and self.path.suffix.lower() in self.ASSEMBLER_EXTENSIONS
            )
            is_pascal = (
                self.path is not None
                and self.path.suffix.lower() in self.PASCAL_EXTENSIONS
            )
            is_c = (
                self.path is not None
                and self.path.suffix.lower() in self.C_EXTENSIONS
            )
            is_c_header = (
                self.path is not None
                and self.path.suffix.lower() in self.C_HEADER_EXTENSIONS
            )
            self.assembler_panel.setVisible(is_assembler or is_pascal or is_c)
            self.syntax_highlighter.set_enabled(is_assembler)
            self.syntax_highlighter.set_pascal_enabled(is_pascal)
            self.syntax_highlighter.set_c_enabled(is_c or is_c_header)
            self.raw_editor.set_assembler_completion_enabled(is_assembler)
            self.raw_editor.set_assembler_navigation_enabled(is_assembler)
            if is_pascal:
                self.assemble_button.setText("Compile")
                self.assemble_button.setToolTip(
                    "Pascal mit ANTLR in 6510-Assembler und ein C64-PRG übersetzen"
                )
                if self.assembled_program is None:
                    self.assembly_status_label.setText("Noch nicht kompiliert")
            elif is_c:
                self.assemble_button.setText("Compile")
                self.assemble_button.setToolTip(
                    "C mit ANTLR in 6510-Assembler und ein C64-PRG übersetzen"
                )
                if self.assembled_program is None:
                    self.assembly_status_label.setText("Noch nicht kompiliert")
            else:
                self.assemble_button.setText("Assemble")
                self.assemble_button.setToolTip(
                    "Assemblerquelltext in ein C64-PRG übersetzen"
                )
                if is_assembler and self.assembled_program is None:
                    self.assembly_status_label.setText("Noch nicht assembliert")

        @property
        def is_assembler_document(self) -> bool:
            return bool(
                self.path is not None
                and self.path.suffix.lower() in self.ASSEMBLER_EXTENSIONS
            )

        @property
        def is_pascal_document(self) -> bool:
            return bool(
                self.path is not None
                and self.path.suffix.lower() in self.PASCAL_EXTENSIONS
            )

        @property
        def is_c_document(self) -> bool:
            return bool(
                self.path is not None
                and self.path.suffix.lower() in self.C_EXTENSIONS
            )

        @property
        def is_build_document(self) -> bool:
            return (
                self.is_assembler_document
                or self.is_pascal_document
                or self.is_c_document
            )

        def invalidate_assembly_result(self, reason: str = "") -> None:
            had_result = bool(
                self.assembled_program is not None
                or self.assembled_program_path is not None
                or self.assembled_source_digest
            )
            self.assembled_program = None
            self.assembled_program_path = None
            self.assembled_source_digest = ""
            self.start_assembled_button.setEnabled(False)
            if reason and had_result and self.is_build_document:
                self.assembly_status_label.setText(reason)

        def set_assembly_result(
            self,
            program,
            output_path: Path,
            source_digest: str,
        ) -> None:
            self.assembled_program = program
            self.assembled_program_path = Path(output_path).resolve()
            self.assembled_source_digest = str(source_digest)
            self.start_assembled_button.setEnabled(True)
            self.assembly_status_label.setText(
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
            for editor in (self.raw_editor, self.hints_editor):
                editor.setFont(QFont(font))
                editor.update_line_number_area_width(0)
            self.hex_editor.set_c64_font_size(font.pointSize())

        def set_dark_mode(self, enabled: bool) -> None:
            enabled = bool(enabled)
            for editor in (self.raw_editor, self.hints_editor):
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

    class ExplorerWindow(QMainWindow):
        ORGANIZATION = "paule32"
        APPLICATION = "Qt5D64Explorer"
        DEFAULT_EDITOR_FONT_SIZE = 9
        MIN_EDITOR_FONT_SIZE = 9
        MAX_EDITOR_FONT_SIZE = 72
        EDITOR_EXTENSIONS = {
            ".asm", ".s", ".a65", ".inc",
            ".pas", ".pp",
            ".c",
            ".txt", ".text", ".log", ".md",
            ".prg", ".ram", ".bin",
        }
        FILTERS = {
            "D64": {".d64"},
            "RAM": {".ram"},
            "ASM": {".asm", ".s", ".a65", ".inc"},
            "PAS": {".pas", ".pp"},
            "C": {".c"},
            "PRG": {".prg"},
            "TXT": {".txt", ".text", ".log", ".md"},
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
            self.dism_thread = None
            self.dism_worker = None
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
            self.new_file_action = QAction(
                self.style().standardIcon(QStyle.SP_FileIcon),
                "Neu",
                self,
            )
            self.new_file_action.setShortcut(QKeySequence.New)
            self.new_file_action.setStatusTip("Eine neue Textdatei anlegen")
            self.new_file_action.triggered.connect(self.new_document)

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

            self.chm_viewer_action = QAction("CHM-Viewer …", self)
            self.chm_viewer_action.setShortcut(QKeySequence.HelpContents)
            self.chm_viewer_action.setStatusTip(
                "CHM-Hilfedatei mit Themen und Schlüsselwörtern öffnen"
            )
            self.chm_viewer_action.triggered.connect(self.show_chm_viewer)

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

        def _create_menu(self) -> None:
            file_menu = self.menuBar().addMenu("&Datei")
            file_menu.addAction(self.new_file_action)
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
            self.dism_menu = self.menuBar().addMenu("&DISM")
            self.dism_menu.addAction(self.dism_extract_action)
            self.dism_menu.addAction(self.dism_bam_action)
            self.dism_menu.addAction(self.dism_startup_action)
            self.dism_menu.addAction(self.dism_verbose_action)
            self.dism_menu.addAction(self.dism_analyze_action)
            self.dism_menu.addAction(self.dism_disassemble_action)
            self.dism_menu.addAction(self.dism_ram_image_action)
            self.dism_menu.addAction(self.dism_vice_action)
            self.dism_menu.addSeparator()
            
            self.dism_start_menu = QMenu("START", self.dism_menu)
            self.dism_start_menu.setObjectName("dism_start_menu")
            self.dism_start_menu.setIcon(self._toolbar_symbol_icon("play"))
            self.dism_start_menu.addAction(self.dism_start_action)
            self.dism_start_menu.addAction(self.dism_program_action)
            
            self.dism_menu.addMenu(self.dism_start_menu)
            
            help_menu = self.menuBar().addMenu("&Hilfe")
            help_menu.addAction(self.chm_viewer_action)
            help_menu.addSeparator()
            help_menu.addAction(self.about_action)

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

            # Ein dehnbarer Platzhalter richtet die Zoom- und Theme-Symbole
            # dauerhaft an der rechten Kante der (auch verschiebbaren) Toolbar aus.
            toolbar_spacer = QWidget(self.toolbar)
            toolbar_spacer.setObjectName("toolbar_right_spacer")
            toolbar_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            self.toolbar.addWidget(toolbar_spacer)
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

        def new_document(self) -> None:
            self.untitled_counter += 1
            dark_mode = self.application_dark_mode(
                self.dark_mode_enabled
            )
            document = DocumentEditor(
                self.document_tabs,
                untitled_number=self.untitled_counter,
                editor_font=self._make_editor_font(),
                dark_mode=dark_mode,
            )
            self._add_document_tab(document)
            document.focus_preferred_editor()
            self.log(f"Neue Textdatei angelegt: {document.display_name}")

        def open_document_dialog(self) -> None:
            filename, _selected_filter = QFileDialog.getOpenFileName(
                self,
                "Datei öffnen",
                str(self.current_directory),
                (
                    "Unterstützte Dateien "
                    "(*.txt *.text *.log *.md *.asm *.s *.a65 *.inc "
                    "*.pas *.pp *.c *.prg *.ram *.bin);;"
                    "C-Dateien (*.c *.h);;"
                    "Pascaldateien (*.pas *.pp);;"
                    "Assemblerdateien (*.asm *.s *.a65 *.inc);;"
                    "Binärdateien (*.prg *.ram *.bin);;"
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

        def _add_document_tab(self, document: DocumentEditor) -> None:
            index = self.document_tabs.addTab(document, document.display_name)
            self.document_tabs.setTabToolTip(index, self._document_tooltip(document))

            close_button = QToolButton(self.document_tabs.tabBar())
            close_button.setAutoRaise(True)
            close_button.setIcon(
                self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
            )
            close_button.setIconSize(QSize(12, 12))
            close_button.setFixedSize(18, 18)
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
            self.document_tabs.setCurrentWidget(document)
            self._update_document_actions()
            self._update_document_tab(document)
            self._apply_document_theme(document)

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
                return
            self._update_document_tab(document)

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
                initial = str(self.current_directory / f"{document.display_name}.txt")

            filename, _selected_filter = QFileDialog.getSaveFileName(
                self,
                "Datei speichern unter",
                initial,
                (
                    "C-Dateien (*.c);;"
                    "Pascaldateien (*.pas *.pp);;"
                    "Assemblerdateien (*.asm *.s *.a65 *.inc);;"
                    "Textdateien (*.txt);;"
                    "Binärdateien (*.prg *.ram *.bin);;"
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
            document.update_syntax_highlighting()
            self._apply_document_theme(document)
            if previous_path != document.path:
                document.invalidate_assembly_result("Dateipfad geändert")
            document.mark_saved()
            self._update_document_tab(document)
            self.log(f"Datei gespeichert: {document.path}")
            self.statusBar().showMessage(f"Gespeichert: {document.path}")
            if document.path.parent == self.current_directory:
                self.populate_file_list()
            return True

        @staticmethod
        def _assembler_output_path(document: DocumentEditor) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der Quelltext muss vor dem Erzeugen eines C64-PRG "
                    "gespeichert werden."
                )
            return document.path.with_suffix(".prg")

        @staticmethod
        def _pascal_assembly_output_path(document: DocumentEditor) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der Pascal-Quelltext muss zuerst gespeichert werden."
                )
            return document.path.with_name(
                document.path.stem + ".generated.asm"
            )

        @staticmethod
        def _c_assembly_output_path(document: DocumentEditor) -> Path:
            if document.path is None:
                raise AssemblerError(
                    "Der C-Quelltext muss zuerst gespeichert werden."
                )
            return document.path.with_name(
                document.path.stem + ".generated.asm"
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

        def _compile_pascal_document(self, document: DocumentEditor) -> bool:
            """ANTLR-Pascal -> 6510-ASM -> interner Assembler -> C64-PRG."""
            source = document.raw_editor.toPlainText()
            source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
            try:
                from c64pascal import (
                    C64PascalError,
                    compile_pascal_to_assembly,
                )
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

            generated = None
            try:
                output_path = self._assembler_output_path(document)
                assembly_path = self._pascal_assembly_output_path(document)
                generated = compile_pascal_to_assembly(
                    source,
                    filename=document.display_name,
                )
                program = assemble_mos6510_source(
                    generated.assembly,
                    filename=assembly_path.name,
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
            except AssemblerError as exc:
                assembly_line = exc.line or 0
                pascal_line = (
                    generated.pascal_line_for_assembly_line(assembly_line)
                    if generated is not None and assembly_line
                    else 0
                )
                location = (
                    f"ASM-Zeile {assembly_line}, Pascal-Zeile {pascal_line}"
                    if pascal_line
                    else f"ASM-Zeile {assembly_line}"
                    if assembly_line
                    else "erzeugter Assembler"
                )
                message = f"Interner Assemblerfehler ({location}):\n{exc}"
                document.show_assembly_error(
                    message,
                    pascal_line,
                    "Assemblerfehler",
                )
                self.show_error("Fehler im erzeugten Assembler", message)
                self.statusBar().showMessage("Pascal-Kompilierung fehlgeschlagen")
                return False

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
                self._write_assembled_program(output_path, program.prg)
            except OSError as exc:
                message = (
                    "Die Compiler-Ausgabe konnte nicht gespeichert werden:\n"
                    f"ASM: {assembly_path}\n"
                    f"PRG: {output_path}\n\n{exc}"
                )
                document.show_assembly_error(
                    message,
                    status_text="Ausgabefehler",
                )
                self.show_error("Compiler-Ausgabe konnte nicht gespeichert werden", message)
                return False

            if open_assembly is not None:
                open_assembly.raw_editor.setPlainText(generated.assembly)
                open_assembly.mark_saved()
                open_assembly.invalidate_assembly_result("Neu erzeugt")
                self._update_document_tab(open_assembly)

            document.set_assembly_result(program, output_path, source_digest)
            document.hints_editor.setPlainText(
                "C64-Pascal erfolgreich kompiliert\n"
                "\n"
                f"Pascal       : {document.display_name}\n"
                f"Assembler    : {assembly_path}\n"
                f"Programm     : {output_path}\n"
                f"Ladeadresse  : ${program.load_address:04X}\n"
                f"Einsprung    : ${program.entry_address:04X}\n"
                f"Letztes Byte : ${program.end_address:04X}\n"
                f"PRG-Größe    : {len(program.prg)} Bytes\n"
                f"Variablen    : {generated.variable_count}\n"
                f"Strings      : {generated.string_count}\n"
                f"6510-Befehle : {program.instruction_count}\n"
                f"BASIC-Stub   : {'ja' if program.has_basic_stub else 'nein'}\n"
            )
            self.log(
                "PASCAL: "
                f"{document.display_name} -> {assembly_path.name} -> "
                f"{output_path.name}, ${program.load_address:04X}-"
                f"${program.end_address:04X}"
            )
            self.statusBar().showMessage(
                f"Pascal erfolgreich kompiliert: {output_path.name}"
            )
            if output_path.parent == self.current_directory:
                self.populate_file_list()
            return True

        def _compile_c_document(self, document: DocumentEditor) -> bool:
            """ANTLR-C -> 6510-ASM -> interner Assembler -> C64-PRG."""
            source = document.raw_editor.toPlainText()
            source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
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

            generated = None
            try:
                output_path = self._assembler_output_path(document)
                assembly_path = self._c_assembly_output_path(document)
                source_filename = (
                    str(document.path)
                    if document.path is not None
                    else document.display_name
                )
                include_paths = [".", "./include", self.current_directory]
                if document.path is not None:
                    include_paths.insert(0, document.path.parent)
                if self.workspace_root not in include_paths:
                    include_paths.append(self.workspace_root)
                generated = compile_c_to_assembly(
                    source,
                    filename=source_filename,
                    include_paths=include_paths,
                )
                program = assemble_mos6510_source(
                    generated.assembly,
                    filename=assembly_path.name,
                )
            except C64CError as exc:
                message = str(exc)
                error_line = 0
                if exc.line:
                    if document.path is None:
                        if not exc.filename or exc.filename == document.display_name:
                            error_line = exc.line
                    elif exc.filename:
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
            except AssemblerError as exc:
                assembly_line = exc.line or 0
                c_line = (
                    generated.c_line_for_assembly_line(assembly_line)
                    if generated is not None and assembly_line
                    else 0
                )
                location = (
                    f"ASM-Zeile {assembly_line}, C-Zeile {c_line}"
                    if c_line
                    else f"ASM-Zeile {assembly_line}"
                    if assembly_line
                    else "erzeugter Assembler"
                )
                message = f"Interner Assemblerfehler ({location}):\n{exc}"
                document.show_assembly_error(
                    message,
                    c_line,
                    "Assemblerfehler",
                )
                self.show_error("Fehler im erzeugten Assembler", message)
                self.statusBar().showMessage("C-Kompilierung fehlgeschlagen")
                return False

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
                self._write_assembled_program(output_path, program.prg)
            except OSError as exc:
                message = (
                    "Die Compiler-Ausgabe konnte nicht gespeichert werden:\n"
                    f"ASM: {assembly_path}\n"
                    f"PRG: {output_path}\n\n{exc}"
                )
                document.show_assembly_error(
                    message,
                    status_text="Ausgabefehler",
                )
                self.show_error(
                    "Compiler-Ausgabe konnte nicht gespeichert werden",
                    message,
                )
                return False

            if open_assembly is not None:
                open_assembly.raw_editor.setPlainText(generated.assembly)
                open_assembly.mark_saved()
                open_assembly.invalidate_assembly_result("Neu erzeugt")
                self._update_document_tab(open_assembly)

            document.set_assembly_result(program, output_path, source_digest)
            diagnostic_lines = []
            if generated.notes:
                diagnostic_lines.append("Hinweise:")
                diagnostic_lines.extend(f"  {item}" for item in generated.notes)
            if generated.warnings:
                if diagnostic_lines:
                    diagnostic_lines.append("")
                diagnostic_lines.append("Warnungen:")
                diagnostic_lines.extend(f"  {item}" for item in generated.warnings)
            diagnostic_text = (
                "\n\n" + "\n".join(diagnostic_lines)
                if diagnostic_lines
                else ""
            )
            document.hints_editor.setPlainText(
                "C64-C erfolgreich kompiliert\n"
                "\n"
                f"C             : {document.display_name}\n"
                f"Assembler     : {assembly_path}\n"
                f"Programm      : {output_path}\n"
                f"Ladeadresse   : ${program.load_address:04X}\n"
                f"Einsprung     : ${program.entry_address:04X}\n"
                f"Letztes Byte  : ${program.end_address:04X}\n"
                f"PRG-Größe     : {len(program.prg)} Bytes\n"
                f"Variablen     : {generated.variable_count}\n"
                f"Strings       : {generated.string_count}\n"
                f"Includes      : {len(generated.included_files)}\n"
                f"Makros        : {len(generated.macros)}\n"
                f"Typedefs      : {generated.typedef_count}\n"
                f"Strukturen    : {generated.structure_count}\n"
                f"Prototypen    : {generated.prototype_count}\n"
                f"6510-Befehle  : {program.instruction_count}\n"
                f"BASIC-Stub    : {'ja' if program.has_basic_stub else 'nein'}\n"
                f"{diagnostic_text}"
            )
            self.log(
                "C: "
                f"{document.display_name} -> {assembly_path.name} -> "
                f"{output_path.name}, ${program.load_address:04X}-"
                f"${program.end_address:04X}"
            )
            if generated.warnings:
                self.statusBar().showMessage(
                    f"C mit {len(generated.warnings)} Warnung(en) kompiliert: "
                    f"{output_path.name}"
                )
            else:
                self.statusBar().showMessage(
                    f"C erfolgreich kompiliert: {output_path.name}"
                )
            if output_path.parent == self.current_directory:
                self.populate_file_list()
            return True

        def assemble_document(self, document: DocumentEditor) -> bool:
            """Erzeugt aus einem ASM-, Pascal- oder C-Dokument ein C64-PRG."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)
            if document.is_pascal_document:
                return self._compile_pascal_document(document)
            if document.is_c_document:
                return self._compile_c_document(document)
            if not document.is_assembler_document:
                self.show_error(
                    "Kein übersetzbares Dokument",
                    "Compile/Assemble steht für .c, .pas, .pp, .asm, .s, "
                    ".a65 und .inc zur Verfügung.",
                )
                return False

            source = document.raw_editor.toPlainText()
            source_digest = hashlib.sha256(
                source.encode("utf-8")
            ).hexdigest()
            try:
                output_path = self._assembler_output_path(document)
                program = assemble_mos6510_source(
                    source,
                    filename=document.display_name,
                )
                self._write_assembled_program(output_path, program.prg)
            except AssemblerError as exc:
                message = str(exc)
                document.show_assembly_error(message, exc.line or 0)
                self.show_error("Assemblerfehler", message)
                self.statusBar().showMessage("Assemblieren fehlgeschlagen")
                return False
            except OSError as exc:
                message = (
                    "Das C64-Programm konnte nicht gespeichert werden:\n"
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
            document.hints_editor.setPlainText(
                "Assembler erfolgreich beendet\n"
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
                "ASSEMBLE: "
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
                or document.assembled_source_digest != current_digest
                or not output_path.is_file()
            ):
                if not self.assemble_document(document):
                    return False
                output_path = document.assembled_program_path

            if output_path is None:
                return False
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
            self.log(
                "VICE START: "
                + self._display_dism_command(command)
            )
            self.statusBar().showMessage(
                f"In VICE gestartet: {output_path.name}"
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
            self._update_document_actions()
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
            self.directory_tree.setMinimumHeight(220)
            for column in range(1, 4):
                self.directory_tree.hideColumn(column)
            self.directory_tree.clicked.connect(self.directory_tree_clicked)

            filter_widget = QWidget(container)
            filter_layout = QGridLayout(filter_widget)
            filter_layout.setContentsMargins(0, 0, 0, 0)
            filter_layout.setHorizontalSpacing(4)
            filter_layout.setVerticalSpacing(4)
            self.filter_group = QButtonGroup(self)
            self.filter_group.setExclusive(True)
            self.filter_buttons = {}

            for number, filter_name in enumerate(self.FILTERS):
                button = QPushButton(filter_name, filter_widget)
                button.setCheckable(True)
                button.setMinimumWidth(52)
                button.clicked.connect(
                    lambda checked=False, name=filter_name: self.set_filter(name)
                )
                self.filter_group.addButton(button)
                self.filter_buttons[filter_name] = button
                filter_layout.addWidget(button, number // 3, number % 3)

            self.filter_buttons["ALLE"].setChecked(True)

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
            self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
            self.view_menu.addAction(self.left_dock.toggleViewAction())

        def _create_right_dock(self) -> None:
            self.right_dock = QDockWidget("Informationen", self)
            self.right_dock.setObjectName("d64_content_dock")
            self.right_dock.setFeatures(self._dock_features())
            self.right_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            self.right_dock.setMinimumWidth(330)

            container = QWidget(self.right_dock)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(7, 7, 7, 7)
            layout.setSpacing(6)

            self.right_info_tabs = QTabWidget(container)
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
            layout.addWidget(self.right_info_tabs, 1)

            self.right_dock.setWidget(container)
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

            clear_button = QPushButton("Protokoll löschen", container)
            clear_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            clear_button.clicked.connect(self.log_edit.clear)

            layout.addWidget(self.log_edit, 1)
            layout.addWidget(clear_button, 0, Qt.AlignRight)
            self.bottom_dock.setWidget(container)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)
            self.view_menu.addAction(self.bottom_dock.toggleViewAction())

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
            self.filter_buttons[filter_name].setChecked(True)
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

        def show_chm_viewer(self) -> None:
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
        description="D64-DISM"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        help="optionales Arbeitsverzeichnis beim Programmstart",
    )
    return parser.parse_args(argv)

def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_arguments(argv)
    return run_gui(args.directory)

if __name__ == "__main__":
    raise SystemExit(main())

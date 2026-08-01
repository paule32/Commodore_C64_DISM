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
#  * Operanden-Rechner fuer Dezimal-, Hexadezimal- und Binaerwerte
#  * integrierter CHM-Viewer mit Themen, Keywords und Favoriten
#  * Editor-Zoom sowie umschaltbarer Hell-/Dunkelmodus
#
# Installation:
#    py -m pip install PyQt5 PyQtWebEngine
#
# Start:
#    py qt5_d64_explorer.py
#    py qt5_d64_explorer.py "T:/C64/Images"
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
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


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


class ChmSitemapParser(HTMLParser):
    """Toleranter Parser fuer die OBJECT/PARAM-Struktur von HHC und HHK."""

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


def clean_chm_local(value: str) -> Tuple[str, str]:
    """Zerlegt ein HHC/HHK-Local-Feld in relativen Pfad und Sprungmarke."""

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


def resolve_chm_path(root: Path, relative: str) -> Optional[Path]:
    """Loest Windows-typische, nicht case-sensitive CHM-Pfade sicher auf."""

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


class ChmExtractor:
    """Entpackt CHM per 7-Zip oder unter Windows per hh.exe."""

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

    class AssemblerSyntaxHighlighter(QSyntaxHighlighter):
        """Hervorhebung fuer MOS-6502/6510-Assemblerquelltext."""

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

        def __init__(self, document):
            super().__init__(document)
            self.enabled = False
            self.dark_mode = False
            self._jump_target_names = set()
            self._jump_target_refresh_pending = False

            self.opcode_format = QTextCharFormat()
            self.opcode_format.setFontWeight(QFont.Bold)

            self.comment_format = QTextCharFormat()
            self.jump_target_format = QTextCharFormat()
            self.jump_target_format.setFontUnderline(True)
            self._update_theme_formats()
            self.document().contentsChanged.connect(
                self._schedule_jump_target_refresh
            )
            self._refresh_jump_target_names()

        def _update_theme_formats(self) -> None:
            # Im Dunkelmodus sind Mnemonics weiss und Kommentare grau. Im
            # Hellmodus bleiben die Mnemonics schwarz; ein dunkleres Grau
            # sorgt dort fuer ausreichend Kontrast auf hellem Hintergrund.
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

        def set_dark_mode(self, enabled: bool) -> None:
            enabled = bool(enabled)
            self.dark_mode = enabled
            self._update_theme_formats()
            # Auch bei unveraendertem Modus neu hervorheben. Beim Einfuegen
            # eines Editors in eine neue Registerkarte kann Qt die Palette
            # des Dokuments noch einmal vom Eltern-Widget uebernehmen.
            self.rehighlight()

        def set_enabled(self, enabled: bool) -> None:
            enabled = bool(enabled)
            if self.enabled == enabled:
                return
            self.enabled = enabled
            if enabled:
                self._refresh_jump_target_names()
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

        def jump_target_at(self, text: str, position: int):
            """Liefert das klickbare Sprungziel an einer Blockposition."""
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
            # cursorForPosition() kann je nach angeklickter Zeichenhaelfte die
            # Position vor oder hinter dem Zeichen liefern.
            if start <= position < end or start < position <= end:
                return target
            return None

        def label_position(self, target: str):
            """Sucht ein Label ohne Beachtung der Gross-/Kleinschreibung."""
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
            if not self.enabled:
                return

            # Zuerst die Mnemonics markieren. Die Kommentarformatierung folgt
            # zuletzt und ueberdeckt deshalb auch Befehlsnamen im Kommentar.
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

    class LineNumberArea(QWidget):
        """Schmale Zeichenflaeche links neben einem Quelltexteditor."""

        def __init__(self, editor: "SourceTextEdit"):
            super().__init__(editor)
            self.editor = editor
            self.setObjectName("line_number_area")

        def sizeHint(self) -> QSize:
            return QSize(self.editor.line_number_area_width(), 0)

        def paintEvent(self, event) -> None:
            self.editor.line_number_area_paint_event(event)

    @dataclass(frozen=True)
    class AssemblerCommandInfo:
        """Anzeige- und Einfuegedaten fuer einen 6502/6510-Befehl."""

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
    class AssemblerOperandContext:
        """Positionen des per Kontextmenue angeklickten ASM-Operanden."""

        insert_position: int
        replace_start: int
        replace_end: int
        original_value: str

    class NumberCalculatorDialog(QDialog):
        """Button-Rechner und Basisumrechner fuer ASM-Operanden."""

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

    class SourceTextEdit(QPlainTextEdit):
        """Quelltexteditor mit Gutter und intelligenter Assemblerhilfe."""

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

        def _update_current_line_highlight(self) -> None:
            """Hebt die aktuelle Cursorzeile theme-abhaengig hervor."""
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

            # Nur die Opcode-Position vervollstaendigen: am Zeilenanfang oder
            # direkt hinter einer mit Doppelpunkt abgeschlossenen Marke.
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

    class PetsciiCharacterDialog(QDialog):
        """Waehlt eines der 255 PETSCII-Zeichen fuer ein Hex-Editor-Byte."""

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

    class HexEditor(QAbstractScrollArea):
        """Byteorientierter Hex-Editor mit acht Bytes pro Zeile."""

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
            # Vierstelliger 16-Bit-Offset plus drei Zeichen Abstand vor den
            # beiden Hex-Byte-Gruppen.
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

        def _replace_byte(self, index: int, byte_value: int) -> None:
            """Ersetzt genau ein Byte und synchronisiert beide Ansichten."""
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

            # Navigation und Hexziffern sind die einzigen direkten Eingaben.
            # Andere druckbare Zeichen werden bewusst nicht an das Widget
            # weitergereicht, damit der Puffer stets gueltige Bytes enthaelt.
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
        BINARY_EXTENSIONS = {".prg", ".ram", ".bin"}

        def __init__(
            self,
            parent: QWidget,
            *,
            untitled_number: int,
            path: Optional[Path] = None,
            text: str = "",
            encoding: str = "utf-8",
            newline: str = "\n",
            raw_bytes: Optional[bytes] = None,
            editor_font: Optional[QFont] = None,
            dark_mode: bool = False,
        ):
            super().__init__(parent)
            self.path = Path(path).resolve() if path is not None else None
            self.untitled_number = untitled_number
            self.encoding = encoding
            self.newline = newline
            self._syncing_views = False
            self._data_source = "text"
            self._last_modified_state = False
            self.assembled_program = None
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
                "Assemblerquelltext in ein C64-PRG übersetzen"
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
            self.assembler_panel.setVisible(is_assembler)
            self.syntax_highlighter.set_enabled(is_assembler)
            self.raw_editor.set_assembler_completion_enabled(is_assembler)
            self.raw_editor.set_assembler_navigation_enabled(is_assembler)

        @property
        def is_assembler_document(self) -> bool:
            return bool(
                self.path is not None
                and self.path.suffix.lower() in self.ASSEMBLER_EXTENSIONS
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
            if reason and had_result and self.is_assembler_document:
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

        def show_assembly_error(self, message: str, line: int = 0) -> None:
            self.invalidate_assembly_result()
            self.assembly_status_label.setText("Assemblerfehler")
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

        def apply_content_view_theme(self) -> None:
            """Faerbt die Web-Oberflaeche schon vor dem ersten Seitenbild."""
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
                background = "#000000"
                foreground = "#ffffff"
                link = "#66b3ff"
                visited = "#c792ea"
                active = "#ffcc66"
                scheme = "dark"
            else:
                background = "#ffffff"
                foreground = "#000000"
                link = "#0000ee"
                visited = "#551a8b"
                active = "#ee0000"
                scheme = "light"

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

        def apply_content_theme(self) -> None:
            """Wendet das Anwendungstheme auf die aktuelle HTML-Seite an."""
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
            ".txt", ".text", ".log", ".md",
            ".prg", ".ram", ".bin",
        }
        FILTERS = {
            "D64": {".d64"},
            "RAM": {".ram"},
            "ASM": {".asm", ".s", ".a65", ".inc"},
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
            self.open_file_action.setStatusTip("Eine Text- oder Assemblerdatei öffnen")
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

        def _create_scrollbar_arrow_assets(self) -> dict:
            """Erzeugt die gelben Scrollpfeile fuer das dunkle Qt-Theme."""
            if not self.theme_asset_directory.isValid():
                return {}

            asset_directory = Path(self.theme_asset_directory.path())
            directions = {
                "up": ((7.0, 3.0), (3.0, 10.0), (11.0, 10.0)),
                "down": ((3.0, 4.0), (11.0, 4.0), (7.0, 11.0)),
                "left": ((3.0, 7.0), (10.0, 3.0), (10.0, 11.0)),
                "right": ((4.0, 3.0), (11.0, 7.0), (4.0, 11.0)),
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
            stylesheet = """
                QToolTip {
                    color: #ffffff;
                    background-color: #2d3746;
                    border: 1px solid #64748b;
                    padding: 3px;
                }
                QMenuBar, QMenu, QToolBar, QStatusBar {
                    background-color: #202630;
                    color: #ebeef2;
                }
                QMenuBar::item:selected, QMenu::item:selected {
                    background-color: #2a69aa;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background: #536072;
                    margin: 4px 8px;
                }
                QToolBar {
                    border: 1px solid #465164;
                    spacing: 3px;
                }
                QDockWidget::title {
                    background-color: #293241;
                    color: #ebeef2;
                    padding: 5px;
                    text-align: left;
                }
                QTabWidget::pane {
                    border: 1px solid #536072;
                }
                QTabBar::tab {
                    background-color: #293241;
                    color: #dfe4ea;
                    border: 1px solid #536072;
                    padding: 6px 10px;
                }
                QTabBar::tab:selected {
                    background-color: #3a485d;
                    color: #ffffff;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #333e4f;
                }
                QMainWindow::separator, QSplitter::handle {
                    background-color: #536072;
                }

                QPushButton {
                    color: #f0f2f5;
                    background-color: #343e4d;
                    border: 1px solid #596779;
                    border-radius: 3px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #414d5f;
                    border-color: #718198;
                }
                QPushButton:pressed {
                    background-color: #27313e;
                    border-color: #455164;
                }
                QPushButton:checked {
                    background-color: #245b91;
                    border-color: #4f91cf;
                    color: #ffffff;
                }
                QPushButton:disabled {
                    background-color: #292f39;
                    border-color: #3e4653;
                    color: #7d8490;
                }

                QLineEdit, QAbstractSpinBox, QComboBox {
                    color: #ebeef2;
                    background-color: #161b23;
                    selection-background-color: #2a69aa;
                    selection-color: #ffffff;
                    border: 1px solid #536072;
                    border-radius: 2px;
                    padding: 3px 5px;
                }
                QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus {
                    border-color: #4f91cf;
                }
                QLineEdit:disabled, QAbstractSpinBox:disabled,
                QComboBox:disabled {
                    color: #7d8490;
                    background-color: #202630;
                }
                QComboBox QAbstractItemView {
                    color: #ebeef2;
                    background-color: #161b23;
                    selection-background-color: #2a69aa;
                    selection-color: #ffffff;
                }

                QScrollBar:vertical {
                    width: 14px;
                    margin: 14px 0 14px 0;
                    background: #000080;
                    border: 0;
                }
                QScrollBar::handle:vertical {
                    min-height: 24px;
                    background: #244a9b;
                    border: 1px solid #5878ba;
                    border-radius: 2px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #315bb0;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    width: 14px;
                    height: 14px;
                    background: #10185f;
                    border: 1px solid #33458d;
                }
                QScrollBar::sub-line:vertical {
                    subcontrol-position: top;
                    subcontrol-origin: margin;
                }
                QScrollBar::add-line:vertical {
                    subcontrol-position: bottom;
                    subcontrol-origin: margin;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: #000080;
                }

                QScrollBar:horizontal {
                    height: 14px;
                    margin: 0 14px 0 14px;
                    background: #000080;
                    border: 0;
                }
                QScrollBar::handle:horizontal {
                    min-width: 24px;
                    background: #244a9b;
                    border: 1px solid #5878ba;
                    border-radius: 2px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #315bb0;
                }
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    width: 14px;
                    height: 14px;
                    background: #10185f;
                    border: 1px solid #33458d;
                }
                QScrollBar::sub-line:horizontal {
                    subcontrol-position: left;
                    subcontrol-origin: margin;
                }
                QScrollBar::add-line:horizontal {
                    subcontrol-position: right;
                    subcontrol-origin: margin;
                }
                QScrollBar::add-page:horizontal,
                QScrollBar::sub-page:horizontal {
                    background: #000080;
                }
                QScrollBar::corner {
                    background: #000080;
                }
            """

            arrows = self.scrollbar_arrow_assets
            if len(arrows) == 4:
                stylesheet += """
                    QScrollBar::up-arrow:vertical {
                        image: url("%(up)s");
                        width: 14px;
                        height: 14px;
                    }
                    QScrollBar::down-arrow:vertical {
                        image: url("%(down)s");
                        width: 14px;
                        height: 14px;
                    }
                    QScrollBar::left-arrow:horizontal {
                        image: url("%(left)s");
                        width: 14px;
                        height: 14px;
                    }
                    QScrollBar::right-arrow:horizontal {
                        image: url("%(right)s");
                        width: 14px;
                        height: 14px;
                    }
                """ % arrows

            return stylesheet

        def _message_box_palette(self) -> QPalette:
            """Liefert eine explizite Palette fuer modale Meldungsdialoge."""
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

        def _message_box_stylesheet(self) -> str:
            """Erzwingt lesbare Dialogfarben unabhaengig vom Windows-Stil."""
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
                    "*.prg *.ram *.bin);;"
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
                    "Textdateien (*.txt);;Assemblerdateien (*.asm *.s *.a65);;"
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
                    "Der Assemblerquelltext muss zuerst als ASM-Datei "
                    "gespeichert werden."
                )
            return document.path.with_suffix(".prg")

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

        def assemble_document(self, document: DocumentEditor) -> bool:
            """Assemblieren des Quelltexts aus genau einer ASM-Registerkarte."""
            if not isinstance(document, DocumentEditor):
                return False
            self.document_tabs.setCurrentWidget(document)
            if not document.is_assembler_document:
                self.show_error(
                    "Kein ASM-Dokument",
                    "Assemble steht für Dateien mit den Endungen .asm, "
                    ".s, .a65 und .inc zur Verfügung.",
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
# Unveraenderte Programmlogik aus d64info(2).py
# SHA-256: 6ee8bc995af1df0d450d67b47f41a2407cfe5e978766d02dc2fba3f27c5cbcd1
# Der Quelltext wird in einem eigenen Modul-Namensraum ausgefuehrt, damit
# gleichnamige Klassen der vorhandenen GUI nicht ueberschrieben werden.
# ---------------------------------------------------------------------------
_D64INFO_SOURCE = r'''#!/usr/bin/env python3
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
'''

import types as _d64info_types

_D64INFO_MODULE = _d64info_types.ModuleType("_d64info_embedded")
_D64INFO_MODULE.__file__ = str(Path(__file__).with_name("d64info(2).py"))
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

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


class LogoCompilerError(Exception):
    def __init__(
        self,
        message: str,
        line: int = 0,
        column: int = 0,
        filename: str = "<LOGO>",
    ) -> None:
        self.message = str(message)
        self.line = int(line or 0)
        self.column = int(column or 0)
        self.filename = str(filename or "<LOGO>")
        super().__init__(self.message)

    def __str__(self) -> str:
        location = self.filename
        if self.line:
            location += f":{self.line}"
            if self.column:
                location += f":{self.column}"
        return f"{location}: {self.message}"


@dataclass(frozen=True)
class LogoCommand:
    name: str
    value: Optional[float]
    line: int
    source_text: str


@dataclass(frozen=True)
class LogoSegment:
    x1: int
    y1: int
    x2: int
    y2: int
    line: int
    command: str


@dataclass
class LogoCompileResult:
    assembly: str
    source_kind: str = "program"
    notes: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    linked_assembly_files: Tuple[str, ...] = ()
    linked_pe32_modules: Tuple[Tuple[str, str], ...] = ()
    commands: Tuple[LogoCommand, ...] = ()
    segments: Tuple[LogoSegment, ...] = ()
    final_x: int = 160
    final_y: int = 100
    final_heading: float = 0.0


_ALIAS = {
    "right": "right",
    "rechts": "right",
    "left": "left",
    "links": "left",
    "up": "north",
    "hoch": "north",
    "down": "south",
    "runter": "south",
    "go": "go",
    "steps": "go",
    "step": "go",
    "schritte": "go",
    "schritt": "go",
    "west": "west",
    "east": "east",
    "ost": "east",
    "nord": "north",
    "north": "north",
    "south": "south",
    "sued": "south",
    "süd": "south",
}

_DIRECTION_HEADING = {
    "east": 0.0,
    "south": 90.0,
    "west": 180.0,
    "north": 270.0,
}

_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")

_STEP_WORDS = {"steps", "step", "schritte", "schritt"}

# Richtungswörter in einem expliziten Bewegungszusammenhang. Dadurch bleibt
# ``right 90`` klassisches LOGO (90 Grad drehen), während
# ``right steps 20`` eindeutig 20 Pixel nach rechts/Osten bedeutet.
_MOVEMENT_DIRECTION_ALIAS = {
    "right": "east",
    "rechts": "east",
    "left": "west",
    "links": "west",
    "up": "north",
    "hoch": "north",
    "down": "south",
    "runter": "south",
    "west": "west",
    "east": "east",
    "ost": "east",
    "nord": "north",
    "north": "north",
    "south": "south",
    "sued": "south",
    "süd": "south",
}


def _strip_comment(line: str) -> str:
    text = str(line)
    # LOGO-Kommentare: ';', '#', '//' - jeweils ab erster Fundstelle.
    positions = []
    for marker in (";", "#", "//"):
        index = text.find(marker)
        if index >= 0:
            positions.append(index)
    if positions:
        text = text[: min(positions)]
    return text.strip()


def _parse_number(token: str, *, line: int, filename: str) -> float:
    if not _NUMBER.match(token):
        raise LogoCompilerError(
            f"Zahl erwartet, erhalten: {token!r}",
            line=line,
            column=1,
            filename=filename,
        )
    value = float(token)
    if not math.isfinite(value):
        raise LogoCompilerError(
            "Nicht-endliche Zahlen sind in LOGO nicht erlaubt.",
            line=line,
            column=1,
            filename=filename,
        )
    return value


def parse_logo(source: str, *, filename: str = "<LOGO>") -> Tuple[LogoCommand, ...]:
    """Parse the deliberately small bilingual LOGO command language.

    Accepted examples::

        right 90          ; relative turn
        rechts 90
        steps 40          ; forward in current heading
        go 40
        east              ; set absolute heading
        east 40           ; set heading and move
        east steps 40
        right steps 40    ; explicit movement to screen-right/east
        go north 25
        go north steps 25

    One statement occupies one source line.
    """
    commands: List[LogoCommand] = []
    for line_number, raw_line in enumerate(str(source or "").splitlines(), 1):
        text = _strip_comment(raw_line)
        if not text:
            continue
        parts = text.split()
        words = [part.casefold() for part in parts]
        first = words[0]

        def error(message: str) -> None:
            raise LogoCompilerError(
                message, line=line_number, column=1, filename=filename
            )

        # ``go <direction> [steps] <n>`` gives an unambiguous absolute move.
        if first == "go" and len(parts) >= 3:
            direction = _MOVEMENT_DIRECTION_ALIAS.get(words[1])
            if direction is None:
                error(f"Unbekannte Richtung nach 'go': {parts[1]}")
            if len(parts) == 3:
                value_token = parts[2]
            elif len(parts) == 4 and words[2] in _STEP_WORDS:
                value_token = parts[3]
            else:
                error("Erwartet: go <Richtung> [steps] <Zahl>.")
            value = _parse_number(value_token, line=line_number, filename=filename)
            commands.append(LogoCommand(direction, value, line_number, text))
            continue

        # ``<direction> steps <n>``. right/left are movement directions only
        # in this explicit form; ``right 90``/``left 90`` remain rotations.
        if len(parts) == 3 and words[1] in _STEP_WORDS:
            direction = _MOVEMENT_DIRECTION_ALIAS.get(first)
            if direction is None:
                error(f"{parts[0]} kann nicht mit 'steps' verwendet werden.")
            value = _parse_number(parts[2], line=line_number, filename=filename)
            commands.append(LogoCommand(direction, value, line_number, text))
            continue

        name = _ALIAS.get(first)
        if name is None:
            error(f"Unbekanntes LOGO-Kommando: {parts[0]}")
        if len(parts) > 2:
            error(
                f"Zu viele Argumente für {parts[0]!r}. "
                "Erwartet wird eine Zahl oder die Form '<Richtung> steps <Zahl>'."
            )

        value = None
        if len(parts) == 2:
            value = _parse_number(parts[1], line=line_number, filename=filename)
        if name == "go" and value is None:
            error(f"{parts[0]} erwartet eine Schrittzahl, z.B. '{parts[0]} 20'.")
        # Klassisches LOGO: right/left ohne Winkel drehen 90 Grad.
        if name in {"right", "left"} and value is None:
            value = 90.0
        commands.append(LogoCommand(name, value, line_number, text))
    return tuple(commands)


def _heading_text(heading: float) -> str:
    normalized = heading % 360.0
    cardinals = ((0.0, "Ost"), (90.0, "Sued"), (180.0, "West"), (270.0, "Nord"))
    for angle, label in cardinals:
        if abs(normalized - angle) < 1e-9:
            return f"{label} ({normalized:g}°)"
    return f"{normalized:g}°"


def _move(x: int, y: int, heading: float, steps: float) -> Tuple[int, int]:
    radians = math.radians(heading % 360.0)
    new_x = int(round(x + math.cos(radians) * steps))
    new_y = int(round(y + math.sin(radians) * steps))
    return new_x, new_y


def _simulate(
    commands: Sequence[LogoCommand],
) -> Tuple[Tuple[LogoSegment, ...], int, int, float, Tuple[str, ...], Tuple[str, ...]]:
    x = 160
    y = 100
    heading = 0.0  # Ost; positive Winkel drehen im Bildschirmkoordinatensystem nach rechts/clockwise.
    segments: List[LogoSegment] = []
    transcript: List[str] = ["LOGO Start: X=160 Y=100 Richtung=Ost (0°)\r\n"]
    warnings: List[str] = []

    for command in commands:
        if command.name == "right":
            heading = (heading + float(command.value or 0.0)) % 360.0
            transcript.append(
                f"Zeile {command.line}: {command.source_text} -> Richtung={_heading_text(heading)}\r\n"
            )
            continue
        if command.name == "left":
            heading = (heading - float(command.value or 0.0)) % 360.0
            transcript.append(
                f"Zeile {command.line}: {command.source_text} -> Richtung={_heading_text(heading)}\r\n"
            )
            continue
        if command.name in _DIRECTION_HEADING:
            heading = _DIRECTION_HEADING[command.name]
            if command.value is None:
                transcript.append(
                    f"Zeile {command.line}: {command.source_text} -> Richtung={_heading_text(heading)}\r\n"
                )
                continue
            steps = float(command.value)
        elif command.name == "go":
            steps = float(command.value or 0.0)
        else:  # defensive; parser guarantees the set above.
            raise AssertionError(command.name)

        new_x, new_y = _move(x, y, heading, steps)
        segments.append(
            LogoSegment(x, y, new_x, new_y, command.line, command.source_text)
        )
        transcript.append(
            f"Zeile {command.line}: {command.source_text} -> "
            f"X={new_x} Y={new_y} Richtung={_heading_text(heading)}\r\n"
        )
        if not (0 <= new_x < 320 and 0 <= new_y < 200):
            warnings.append(
                f"Zeile {command.line}: Ziel ({new_x},{new_y}) liegt außerhalb der 320x200-Fläche. "
                "Die Grafik-Runtime schneidet außerhalb liegende Pixel ab."
            )
        x, y = new_x, new_y

    transcript.append(f"LOGO Ende: X={x} Y={y} Richtung={_heading_text(heading)}\r\n")
    return tuple(segments), x, y, heading, tuple(transcript), tuple(warnings)


def _db_lines(label: str, data: bytes) -> List[str]:
    payload = bytes(data)
    lines = [f"{label}:"]
    if not payload:
        lines.append("    db 0")
        return lines
    for start in range(0, len(payload), 24):
        chunk = payload[start : start + 24]
        lines.append("    db " + ", ".join(str(value) for value in chunk))
    return lines


def _emit_console_assembly(transcript: str) -> str:
    payload = transcript.encode("latin-1", errors="replace")
    prompt = "\r\nENTER druecken zum Beenden ...\r\n".encode("latin-1", errors="replace")
    lines: List[str] = [
        "bits 32",
        "",
        'import AllocConsole, "kernel32.dll", "AllocConsole"',
        'import GetStdHandle, "kernel32.dll", "GetStdHandle"',
        'import WriteFile, "kernel32.dll", "WriteFile"',
        'import ReadFile, "kernel32.dll", "ReadFile"',
        'import ExitProcess, "kernel32.dll", "ExitProcess"',
        "global _start",
        "entry _start",
        "",
        "section .text",
        "",
        "_start:",
        "    call AllocConsole",
        "    push -11",
        "    call GetStdHandle",
        "    mov dword ptr [__logo_stdout], eax",
        "    push -10",
        "    call GetStdHandle",
        "    mov dword ptr [__logo_stdin], eax",
    ]
    if payload:
        lines.extend([
            "    push 0",
            "    push __logo_written",
            f"    push {len(payload)}",
            "    push __logo_output",
            "    push dword ptr [__logo_stdout]",
            "    call WriteFile",
        ])
    lines.extend([
        "    push 0",
        "    push __logo_written",
        f"    push {len(prompt)}",
        "    push __logo_prompt",
        "    push dword ptr [__logo_stdout]",
        "    call WriteFile",
        "    push 0",
        "    push __logo_read",
        "    push 2",
        "    push __logo_input",
        "    push dword ptr [__logo_stdin]",
        "    call ReadFile",
        "    push 0",
        "    call ExitProcess",
        "",
        "section .data",
        "__logo_stdout:",
        "    dd 0",
        "__logo_stdin:",
        "    dd 0",
        "__logo_written:",
        "    dd 0",
        "__logo_read:",
        "    dd 0",
        "__logo_input:",
        "    db 0, 0, 0, 0",
    ])
    lines.extend(_db_lines("__logo_output", payload))
    lines.extend(_db_lines("__logo_prompt", prompt))
    return "\n".join(lines).rstrip() + "\n"


def _emit_gui_assembly(segments: Sequence[LogoSegment]) -> str:
    lines: List[str] = [
        "bits 32",
        "",
        'import InitGraphics320x200, "d64graphics.dll", "InitGraphics320x200"',
        'import ClearScreen, "d64graphics.dll", "ClearScreen"',
        'import DrawLine, "d64graphics.dll", "DrawLine"',
        'import GraphicsWindowOpen, "d64graphics.dll", "GraphicsWindowOpen"',
        'import DoneGraphics, "d64graphics.dll", "DoneGraphics"',
        'import Sleep, "kernel32.dll", "Sleep"',
        'import ExitProcess, "kernel32.dll", "ExitProcess"',
        "global _start",
        "entry _start",
        "",
        "section .text",
        "",
        "_start:",
        "    call InitGraphics320x200",
        "    call ClearScreen",
        # Startpunkt sichtbar machen.
        "    push 1",
        "    push 100",
        "    push 160",
        "    push 100",
        "    push 160",
        "    call DrawLine",
        "    add esp, 20",
    ]
    for index, segment in enumerate(segments, 1):
        lines.extend([
            f"    ; LOGO {index}: Zeile {segment.line}: {segment.command}",
            "    push 1",
            f"    push {segment.y2}",
            f"    push {segment.x2}",
            f"    push {segment.y1}",
            f"    push {segment.x1}",
            "    call DrawLine",
            "    add esp, 20",
        ])
    lines.extend([
        "",
        "__logo_wait_window:",
        "    call GraphicsWindowOpen",
        "    test eax, eax",
        "    jz __logo_finish",
        "    push 16",
        "    call Sleep",
        "    jmp __logo_wait_window",
        "",
        "__logo_finish:",
        "    push 0",
        "    call DoneGraphics",
        "    add esp, 4",
        "    push 0",
        "    call ExitProcess",
    ])
    return "\n".join(lines).rstrip() + "\n"


def compile_logo_to_assembly(
    source: str,
    *,
    filename: str = "<LOGO>",
    target: str = "pe32",
    windows_application_mode: str = "Console",
) -> LogoCompileResult:
    target_key = str(target or "pe32").strip().casefold()
    if target_key not in {"pe32", "win32", "windows", "windows-pe32"}:
        raise LogoCompilerError(
            "Der LOGO-Compiler unterstützt in diesem ersten Stand ausschließlich Windows PE32.",
            filename=filename,
        )

    mode_key = str(windows_application_mode or "Console").strip().casefold()
    if mode_key in {"console", "konsole"}:
        is_gui = False
        mode_name = "Console"
    elif mode_key in {"gui", "windows", "direct2d", "d2d", "direct3d", "d3d", "d3d9"}:
        is_gui = True
        mode_name = "GUI"
    else:
        raise LogoCompilerError(
            "Unbekannter LOGO-Ausgabemodus. Erlaubt sind Console oder GUI.",
            filename=filename,
        )

    commands = parse_logo(source, filename=filename)
    segments, final_x, final_y, heading, transcript_lines, warnings = _simulate(commands)
    transcript = "".join(transcript_lines)
    assembly = _emit_gui_assembly(segments) if is_gui else _emit_console_assembly(transcript)
    notes = (
        "LOGO-Koordinatensystem: 320x200 Pixel, Startpunkt (160,100).",
        "0° = Ost, right/rechts dreht im Uhrzeigersinn, left/links gegen den Uhrzeigersinn.",
        f"Ausgabemodus: {mode_name}.",
        f"Endposition: ({final_x},{final_y}), Richtung {_heading_text(heading)}.",
    )
    return LogoCompileResult(
        assembly=assembly,
        notes=notes,
        warnings=warnings,
        commands=commands,
        segments=segments,
        final_x=final_x,
        final_y=final_y,
        final_heading=heading,
    )


__all__ = [
    "LogoCompilerError",
    "LogoCommand",
    "LogoSegment",
    "LogoCompileResult",
    "parse_logo",
    "compile_logo_to_assembly",
]

"""Stage 470: shared, file-aware macro preprocessor for the internal PE32/PE64 assemblers.

The output stays ordinary internal Intel syntax (not NASM). No external tools.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Mapping, Iterable

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")
_TOKEN = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z_0-9]*)(?![A-Za-z0-9_])")
_DIRECTIVE = re.compile(r"^\s*%(\w+)\b(.*)$", re.IGNORECASE)
_INC = re.compile(r'^\s*(?:"([^"\r\n]+)"|\x27([^\x27\r\n]+)\x27|<([^>\r\n]+)>)\s*$')
_MAX_INCLUDE_DEPTH = 32
_MAX_LINES = 700000


class WindowsAsmMacroError(Exception):
    def __init__(self, message: str, filename: str, line: int):
        self.filename, self.line, self.message = str(filename), int(line), str(message)
        super().__init__(f"{self.filename}:{self.line}: {self.message}")


@dataclass(frozen=True)
class MacroResult:
    source: str
    # For assembler diagnostics: expanded 1-based line -> (file, original line)
    locations: tuple[tuple[str, int], ...]


def _code_and_comment(text: str) -> tuple[str, str]:
    """Preserve assembler comments; a semicolon inside a string is not a comment."""
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote and char == '\\':
            escaped = True
            continue
        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif char == ';' and quote is None:
            return text[:index], text[index:]
    return text, ""


def _replace_tokens(text: str, mapping: Mapping[str, str], *, nested: bool = True) -> str:
    # Avoid macro substitution inside literals and preserve quotes verbatim.
    def once(value: str) -> str:
        output = []
        start = 0
        quote = None
        escaped = False
        i = 0
        while i < len(value):
            ch = value[i]
            if escaped:
                escaped = False
            elif quote and ch == '\\':
                escaped = True
            elif ch in ('"', "'"):
                if quote is None:
                    if i > start:
                        output.append(_TOKEN.sub(lambda m: mapping.get(m[1], m[1]), value[start:i]))
                    start = i
                    quote = ch
                elif ch == quote:
                    output.append(value[start:i+1]); start = i+1; quote = None
            i += 1
        if start < len(value):
            tail = value[start:]
            output.append(tail if quote else _TOKEN.sub(lambda m: mapping.get(m[1], m[1]), tail))
        return ''.join(output)

    current = text
    for _ in range(24 if nested else 1):
        result = once(current)
        if result == current:
            return result
        current = result
    raise ValueError("Makro-Expansion ist rekursiv oder zu tief (24 Ebenen).")


def _parse_scalar(value: str) -> object:
    value = value.strip()
    try:
        literal = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        literal = None
    if isinstance(literal, (int, float, str, bool)):
        return literal
    if re.fullmatch(r'[+-]?0[xX][0-9a-fA-F]+', value):
        return int(value, 16)
    if re.fullmatch(r'[+-]?[0-9]+', value):
        return int(value, 10)
    if re.fullmatch(r'[+-]?[0-9]+\.[0-9]+', value):
        return float(value)
    if _IDENTIFIER.fullmatch(value):
        # Undefined identifiers in %if evaluate to zero (common ASM convention).
        return 0
    raise ValueError(f"Ungültiger Ausdruck: {value}")


def _evaluate_condition(expr: str, macros: Mapping[str, str]) -> bool:
    expr = expr.strip()
    # Use a single comparison operator, supporting user's => plus normal >=.
    match = re.match(r'^(.*?)\s*(==|<=|>=|=>|!=|<|>)\s*(.*?)$', expr)
    if not match or not match[1].strip() or not match[3].strip():
        raise ValueError("%if/%elif erwartet: WERT ==, !=, <, <=, =>, >= oder > WERT")
    lhs, op, rhs = match.groups()
    left = _parse_scalar(_replace_tokens(lhs, macros))
    right = _parse_scalar(_replace_tokens(rhs, macros))
    if isinstance(left, str) != isinstance(right, str):
        raise ValueError("%if vergleicht inkompatible Typen (String/Zahl).")
    return {
        '==': lambda: left == right, '!=': lambda: left != right,
        '<': lambda: left < right, '<=': lambda: left <= right,
        '>': lambda: left > right, '>=': lambda: left >= right,
        '=>': lambda: left >= right,
    }[op]()


def preprocess_windows_asm(source: str, *, filename: str = '<Assembler>',
                           definitions: Mapping[str, str] | None = None,
                           include_dirs: Iterable[str | Path] = ()) -> MacroResult:
    """Expand includes/defines/conditionals into ordinary PE32/PE64 ASM text.

    `%include "<extern.inc>"` also works (angle brackets are stripped).
    Macro locations are retained so assembly errors can be mapped back to the
    file that owns the offending line.
    """
    stamp = datetime.now()
    values = dict(definitions or {})
    locations: list[tuple[str, int]] = []
    lines: list[str] = []
    current_stack: list[Path] = []
    normalized_file = str(filename)
    # The GUI supplies Compiler -> Eingabe-Verzeichnis in list order.
    # Resolve once so nested includes use the same project roots.
    search_directories: list[Path] = []
    for raw in include_dirs or ():
        if str(raw).strip():
            folder = Path(str(raw)).expanduser().resolve()
            if folder not in search_directories:
                search_directories.append(folder)

    def error(msg: str, file: str, line: int) -> None:
        raise WindowsAsmMacroError(msg, file, line)

    def emit(text: str, file: str, line: int):
        lines.append(text)
        locations.append((file, line))
        if len(lines) > _MAX_LINES:
            error(f"ASM-Vorverarbeitung überschreitet {_MAX_LINES} Zeilen.", file, line)

    def walk(text: str, file: str):
        active = True
        # parent_active, already_chosen, has_else
        conditions: list[list[bool]] = []
        for number, original in enumerate(text.splitlines(), 1):
            head, comment = _code_and_comment(original)
            directive = _DIRECTIVE.match(head)
            if directive is None:
                if active:
                    predefined = {
                        '__LINE__': str(number),
                        '__TIME__': stamp.strftime('"%H:%M:%S"'),
                        '__DATE__': stamp.strftime('"%Y-%m-%d"'),
                        '__FILE__': '"' + Path(file).name.replace('"', '') + '"',
                        '__BREAK__': 'int3',
                    }
                    try:
                        expanded = _replace_tokens(head, {**values, **predefined})
                    except ValueError as exc:
                        error(str(exc), file, number)
                    emit(expanded + comment, file, number)
                else:
                    emit('', file, number)
                continue
            kind, arg = directive[1].lower(), directive[2].strip()
            if kind in ('if', 'ifdef', 'ifndef'):
                parent = active
                try:
                    if kind == 'if':
                        valid = _evaluate_condition(arg, values) if parent else False
                    else:
                        if not _IDENTIFIER.fullmatch(arg):
                            raise ValueError(f"%{kind} erwartet einen einzelnen Makronamen.")
                        valid = (arg in values or arg in {
                            '__LINE__', '__TIME__', '__DATE__', '__FILE__', '__BREAK__'
                        })
                        if kind == 'ifndef':
                            valid = not valid
                    active = bool(parent and valid)
                except ValueError as exc:
                    error(str(exc), file, number)
                conditions.append([parent, active, False])
            elif kind in ('elif', 'else'):
                if not conditions:
                    error(f"%{kind} ohne vorangegangenes %if.", file, number)
                frame = conditions[-1]
                if frame[2]:
                    error(f"%{kind} hinter %else.", file, number)
                if kind == 'else':
                    active = frame[0] and not frame[1]
                    frame[2] = True
                else:
                    try:
                        active = frame[0] and not frame[1] and _evaluate_condition(arg, values)
                    except ValueError as exc:
                        error(str(exc), file, number)
                frame[1] = frame[1] or active
            elif kind == 'endif':
                if not conditions:
                    error('%endif ohne vorangegangenes %if.', file, number)
                if arg:
                    error('%endif erwartet keine Parameter.', file, number)
                active = conditions.pop()[0]
            elif active:
                if kind == 'define':
                    match = re.match(r'^([A-Za-z_][A-Za-z_0-9]*)(?:\s+(.*))?$', arg)
                    if not match:
                        error('%define erwartet MAKRO [WERT].', file, number)
                    key, value = match.group(1), match.group(2)
                    if key in {'__LINE__', '__TIME__', '__DATE__', '__FILE__', '__BREAK__'}:
                        error(f"Vordefiniertes Makro nicht überschreibbar: {key}", file, number)
                    values[key] = '1' if value is None else value
                elif kind == 'undef':
                    if not _IDENTIFIER.fullmatch(arg):
                        error('%undef erwartet einen Makronamen.', file, number)
                    values.pop(arg, None)
                elif kind == 'include':
                    include = _INC.fullmatch(arg)
                    if include is None:
                        error('%include erwartet "datei.inc" oder <datei.inc>.', file, number)
                    name = next(v for v in include.groups() if v is not None)
                    if name.startswith('<') and name.endswith('>'):
                        name = name[1:-1]
                    # Windows backslash paths work on POSIX test environments too.
                    name = name.replace('\\', '/')
                    requested = Path(name)
                    base = Path(file).resolve().parent if not file.startswith('<') else Path.cwd()
                    candidates = (
                        [requested.resolve()] if requested.is_absolute()
                        else [(base / requested).resolve()]
                             + [(directory / requested).resolve() for directory in search_directories]
                    )
                    selected = next((candidate for candidate in candidates if candidate.is_file()), None)
                    if selected is None:
                        checked = "; ".join(str(candidate) for candidate in candidates)
                        error(f"Include-Datei nicht gefunden: {name} (geprüfte Pfade: {checked})", file, number)
                    if len(current_stack) >= _MAX_INCLUDE_DEPTH:
                        error('Maximale Include-Tiefe überschritten.', file, number)
                    if selected in current_stack:
                        error(f"Zyklisches Include: {selected}", file, number)
                    try:
                        included = selected.read_text(encoding='utf-8-sig')
                    except (OSError, UnicodeError) as exc:
                        error(f"Include-Datei nicht lesbar: {selected}: {exc}", file, number)
                    current_stack.append(selected)
                    try:
                        walk(included, str(selected))
                    finally:
                        current_stack.pop()
                else:
                    error(f"Unbekannte ASM-Direktive: %{kind}", file, number)
            emit('', file, number)  # preserve line mapping for directives
        if conditions:
            error('Nicht abgeschlossene Bedingung: %endif fehlt.', file, len(text.splitlines()))

    try:
        root = Path(filename).resolve() if not filename.startswith('<') else None
        if root is not None:
            current_stack.append(root)
        walk(str(source), normalized_file)
    finally:
        if current_stack and current_stack[0] == (Path(filename).resolve() if not filename.startswith('<') else None):
            current_stack.pop(0)
    return MacroResult('\n'.join(lines) + '\n', tuple(locations))


def externalize_windows_imports(assembly: str, assembly_path: str | Path) -> tuple[str, Path | None, str | None]:
    """Write one adjacent, uniquely named .inc file and return compact source.

    Filesystem write is intentionally deferred to callers so the compiler can
    be used purely in memory. We return (new_source, file_path, include_text).
    """
    source_lines = str(assembly).splitlines(keepends=True)
    imports = [line for line in source_lines if re.match(r'^\s*import\s+', line, re.I)]
    if not imports:
        return str(assembly), None, None
    asm_path = Path(assembly_path)
    include_path = asm_path.with_suffix('.extern.inc')
    remaining = [line for line in source_lines if not re.match(r'^\s*import\s+', line, re.I)]
    # Insert import macro near the start; no code addresses are changed.
    name = include_path.name
    line = f'%include "{name}"\n'
    # Do not touch .data/.text ordering: import directives are section-independent.
    remaining.insert(0, line)
    return ''.join(remaining), include_path, ''.join(imports)


def externalize_windows_wfm_payload(
    assembly: str, assembly_path: str | Path
) -> tuple[str, Path | None, str | None]:
    """Move the WFM UI JSON/binary payload db bytes into an adjacent include.

    The payload label and the active .data section remain in the main ASM,
    so references/relocations and alignment are preserved. Only the numeric
    data directives *immediately* following this precise label are extracted.
    The in-memory WFM compiler output stays unchanged until it is saved.
    """
    original = str(assembly)
    source_lines = original.splitlines(keepends=True)
    marker = '__dbase_wfm_external_ui_payload:'
    marker_indices = [i for i, line in enumerate(source_lines)
                      if line.strip() == marker]
    if not marker_indices:
        return original, None, None
    if len(marker_indices) != 1:
        raise ValueError(f"Mehrfaches WFM-Payload-Label: {marker}")
    start = marker_indices[0] + 1
    end = start
    # Only decimal byte lists belong to the serializer's JSON/binary payload.
    # Do not accidentally move the next label, property block or .bss section.
    numeric_db = re.compile(r'^\s+db\s+\d+(?:\s*,\s*\d+)*\s*$', re.I)
    while end < len(source_lines) and numeric_db.fullmatch(source_lines[end].rstrip('\r\n')):
        end += 1
    if end == start:
        raise ValueError(f"Keine numerischen db-Daten hinter {marker}")
    payload_lines = source_lines[start:end]
    include_path = Path(assembly_path).with_suffix('.payload.inc')
    replacement = f'    %include "{include_path.name}"\n'
    return (
        ''.join(source_lines[:start]) + replacement + ''.join(source_lines[end:]),
        include_path,
        ''.join(payload_lines),
    )

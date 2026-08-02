"""Kleiner, deterministischer C-Praeprozessor fuer das C64-Frontend.

Die ANTLR-Grammatik sieht nur bereits aufbereiteten C-Quelltext. Diese Stufe
loest Includes auf, verwaltet Makros und entfernt inaktive bedingte Bereiche,
bevor Lexer und Parser gestartet werden. Jede ausgegebene Zeile behaelt dabei
ihre urspruengliche Datei- und Zeilenposition.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class SourceLocation:
    filename: str
    line: int
    column: int = 1

    def format(self) -> str:
        if self.column > 0:
            return f"{self.filename}:{self.line}:{self.column}"
        return f"{self.filename}:{self.line}"


@dataclass(frozen=True)
class PreprocessorDiagnostic:
    kind: str
    message: str
    location: SourceLocation

    def __str__(self) -> str:
        return f"{self.location.format()}: {self.kind}: {self.message}"


@dataclass(frozen=True)
class Macro:
    name: str
    replacement: str
    parameters: Optional[Tuple[str, ...]] = None
    location: Optional[SourceLocation] = None

    @property
    def function_like(self) -> bool:
        return self.parameters is not None


@dataclass(frozen=True)
class PreprocessResult:
    source: str
    line_map: Tuple[SourceLocation, ...]
    macros: Mapping[str, Macro]
    included_files: Tuple[str, ...]
    notes: Tuple[PreprocessorDiagnostic, ...]
    warnings: Tuple[PreprocessorDiagnostic, ...]

    def location_for_line(self, line: int, column: int = 1) -> SourceLocation:
        index = int(line) - 1
        if 0 <= index < len(self.line_map):
            original = self.line_map[index]
            return SourceLocation(
                original.filename,
                original.line,
                max(1, int(column)),
            )
        return SourceLocation("<C-Editor>", max(1, int(line)), max(1, int(column)))


class C64PreprocessorError(Exception):
    """Fehler einer Praeprozessoranweisung mit Include-Kontext."""

    def __init__(
        self,
        message: str,
        location: SourceLocation,
        include_stack: Sequence[str] = (),
    ) -> None:
        self.message = str(message)
        self.filename = location.filename
        self.line = int(location.line)
        self.column = int(location.column)
        self.include_stack = tuple(str(item) for item in include_stack)
        super().__init__(self.message)

    def __str__(self) -> str:
        text = f"{self.filename}:{self.line}:{self.column}: {self.message}"
        if len(self.include_stack) > 1:
            chain = " -> ".join(self.include_stack)
            text += f"\nInclude-Kette: {chain}"
        return text


@dataclass
class _Conditional:
    parent_active: bool
    condition: bool
    active: bool
    else_seen: bool
    location: SourceLocation


_DIRECTIVE_RE = re.compile(r"^[ \t]*#[ \t]*([A-Za-z_]\w*)\b(.*)$")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_]\w*")
_INCLUDE_RE = re.compile(r'^\s*([<"])(.*?)[>"]\s*(?://.*|/\*.*\*/\s*)?$')


class C64CPreprocessor:
    """Objekt- und funktionsartige Makros mit rekursiven Includes."""

    MAX_INCLUDE_DEPTH = 64
    MAX_MACRO_DEPTH = 100

    def __init__(
        self,
        *,
        include_paths: Iterable[Path | str] = (),
        predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
    ) -> None:
        self.include_paths: List[Path] = []
        for item in include_paths:
            path = Path(item).expanduser().resolve()
            if path not in self.include_paths:
                self.include_paths.append(path)
        builtin = (Path(__file__).resolve().parent / "include").resolve()
        if builtin not in self.include_paths:
            self.include_paths.append(builtin)

        self.macros: Dict[str, Macro] = {}
        for name, value in (predefined_macros or {}).items():
            self._validate_identifier(str(name), SourceLocation("<command line>", 1))
            replacement = "1" if value is True else "0" if value is False else str(value)
            self.macros[str(name)] = Macro(str(name), replacement)

        self.output_lines: List[str] = []
        self.line_map: List[SourceLocation] = []
        self.included_files: List[str] = []
        self.notes: List[PreprocessorDiagnostic] = []
        self.warnings: List[PreprocessorDiagnostic] = []
        self.include_stack: List[str] = []
        self.once_files: Set[Path] = set()
        self.completed_once_files: Set[Path] = set()

    def process(self, source: str, *, filename: str = "<C-Editor>") -> PreprocessResult:
        root_path = self._existing_path(filename)
        display_name = str(root_path) if root_path is not None else str(filename)
        base_directory = root_path.parent if root_path is not None else Path.cwd()
        self._process_text(
            str(source),
            display_name,
            base_directory,
            root_path,
        )
        return PreprocessResult(
            "\n".join(self.output_lines) + ("\n" if self.output_lines else ""),
            tuple(self.line_map),
            dict(self.macros),
            tuple(self.included_files),
            tuple(self.notes),
            tuple(self.warnings),
        )

    @staticmethod
    def _existing_path(filename: str) -> Optional[Path]:
        if not filename or (filename.startswith("<") and filename.endswith(">")):
            return None
        try:
            path = Path(filename).expanduser().resolve()
        except (OSError, RuntimeError):
            return None
        return path if path.is_file() else None

    @staticmethod
    def _validate_identifier(name: str, location: SourceLocation) -> None:
        if not _IDENTIFIER_RE.fullmatch(name):
            raise C64PreprocessorError(
                f"Ungueltiger Makroname: {name!r}.",
                location,
            )

    @staticmethod
    def _logical_lines(source: str) -> List[Tuple[str, int]]:
        physical = source.splitlines()
        result: List[Tuple[str, int]] = []
        index = 0
        while index < len(physical):
            first_line = index + 1
            text = physical[index]
            while text.endswith("\\") and index + 1 < len(physical):
                text = text[:-1] + physical[index + 1]
                index += 1
            result.append((text, first_line))
            index += 1
        return result

    def _process_text(
        self,
        source: str,
        filename: str,
        base_directory: Path,
        canonical_path: Optional[Path],
    ) -> None:
        if len(self.include_stack) >= self.MAX_INCLUDE_DEPTH:
            location = SourceLocation(filename, 1)
            raise C64PreprocessorError(
                f"Maximale Include-Tiefe von {self.MAX_INCLUDE_DEPTH} ueberschritten.",
                location,
                self.include_stack + [filename],
            )
        if canonical_path is not None and canonical_path in self.once_files:
            if (
                canonical_path in self.completed_once_files
                or str(canonical_path) in self.include_stack
            ):
                return

        self.include_stack.append(filename)
        conditionals: List[_Conditional] = []
        in_block_comment = False
        try:
            for raw_line, line_number in self._logical_lines(source):
                location = SourceLocation(filename, line_number, 1)
                directive = None if in_block_comment else _DIRECTIVE_RE.match(raw_line)
                active = conditionals[-1].active if conditionals else True
                if directive is not None:
                    name = directive.group(1).lower()
                    argument = directive.group(2).strip()
                    if name in {"ifdef", "ifndef", "else", "endif"}:
                        self._conditional_directive(
                            name,
                            argument,
                            location,
                            conditionals,
                        )
                        continue
                    if not active:
                        continue
                    self._active_directive(
                        name,
                        argument,
                        location,
                        base_directory,
                    )
                    continue
                if not active:
                    continue
                expanded, in_block_comment = self._expand_line(
                    raw_line,
                    location,
                    in_block_comment,
                )
                self.output_lines.append(expanded)
                self.line_map.append(location)

            if conditionals:
                opening = conditionals[-1].location
                raise C64PreprocessorError(
                    "Fehlendes #endif fuer diese bedingte Anweisung.",
                    opening,
                    self.include_stack,
                )
            if canonical_path is not None and canonical_path in self.once_files:
                self.completed_once_files.add(canonical_path)
        finally:
            self.include_stack.pop()

    def _conditional_directive(
        self,
        name: str,
        argument: str,
        location: SourceLocation,
        stack: List[_Conditional],
    ) -> None:
        if name in {"ifdef", "ifndef"}:
            macro_name = argument.split()[0] if argument else ""
            self._validate_identifier(macro_name, location)
            parent_active = stack[-1].active if stack else True
            condition = macro_name in self.macros
            if name == "ifndef":
                condition = not condition
            stack.append(
                _Conditional(
                    parent_active,
                    condition,
                    parent_active and condition,
                    False,
                    location,
                )
            )
            return

        if not stack:
            raise C64PreprocessorError(
                f"#{name} ohne passendes #ifdef oder #ifndef.",
                location,
                self.include_stack,
            )
        current = stack[-1]
        if name == "else":
            if current.else_seen:
                raise C64PreprocessorError(
                    "Mehrfaches #else im selben bedingten Block.",
                    location,
                    self.include_stack,
                )
            current.else_seen = True
            current.active = current.parent_active and not current.condition
            return
        stack.pop()

    def _active_directive(
        self,
        name: str,
        argument: str,
        location: SourceLocation,
        base_directory: Path,
    ) -> None:
        if name == "include":
            self._include(argument, location, base_directory)
            return
        if name == "define":
            self._define(argument, location)
            return
        if name == "undef":
            macro_name = argument.split()[0] if argument else ""
            self._validate_identifier(macro_name, location)
            self.macros.pop(macro_name, None)
            return
        if name in {"note", "warning", "error"}:
            message = self._expand_text(argument, location).strip()
            if len(message) >= 2 and message[0] == message[-1] == '"':
                message = message[1:-1]
            message = message or f"#{name}"
            if name == "error":
                raise C64PreprocessorError(message, location, self.include_stack)
            diagnostic = PreprocessorDiagnostic(name, message, location)
            (self.notes if name == "note" else self.warnings).append(diagnostic)
            return
        if name == "pragma" and argument.strip().lower() == "once":
            if self.include_stack:
                path = self._existing_path(self.include_stack[-1])
                if path is not None:
                    self.once_files.add(path)
            return
        raise C64PreprocessorError(
            f"Unbekannte Praeprozessoranweisung: #{name}.",
            location,
            self.include_stack,
        )

    def _define(self, argument: str, location: SourceLocation) -> None:
        match = _IDENTIFIER_RE.match(argument)
        if match is None:
            raise C64PreprocessorError(
                "#define erwartet einen Makronamen.",
                location,
                self.include_stack,
            )
        name = match.group(0)
        tail = argument[match.end():]
        parameters: Optional[Tuple[str, ...]] = None
        replacement = tail.lstrip()
        if tail.startswith("("):
            closing = tail.find(")")
            if closing < 0:
                raise C64PreprocessorError(
                    f"Fehlende ')' in der Definition von {name}.",
                    location,
                    self.include_stack,
                )
            raw_parameters = tail[1:closing].strip()
            if raw_parameters:
                parameter_list = tuple(item.strip() for item in raw_parameters.split(","))
                for parameter in parameter_list:
                    self._validate_identifier(parameter, location)
                if len(set(parameter_list)) != len(parameter_list):
                    raise C64PreprocessorError(
                        f"Doppelter Parameter in Makro {name}.",
                        location,
                        self.include_stack,
                    )
                parameters = parameter_list
            else:
                parameters = ()
            replacement = tail[closing + 1:].lstrip()
        if "##" in replacement or re.search(r"(^|\s)#\s*[A-Za-z_]", replacement):
            raise C64PreprocessorError(
                "Die Operatoren # und ## folgen in einer spaeteren Ausbaustufe.",
                location,
                self.include_stack,
            )
        self.macros[name] = Macro(name, replacement, parameters, location)

    def _include(
        self,
        argument: str,
        location: SourceLocation,
        base_directory: Path,
    ) -> None:
        expanded = self._expand_text(argument, location).strip()
        match = _INCLUDE_RE.fullmatch(expanded)
        if match is None:
            raise C64PreprocessorError(
                '#include erwartet "datei.h" oder <datei.h>.',
                location,
                self.include_stack,
            )
        delimiter, include_name = match.groups()
        include_name = include_name.strip()
        candidates: List[Path] = []
        if delimiter == '"':
            candidates.append((base_directory / include_name).resolve())
        candidates.extend((path / include_name).resolve() for path in self.include_paths)
        if delimiter == "<":
            local_candidate = (base_directory / include_name).resolve()
            if local_candidate not in candidates:
                candidates.append(local_candidate)

        include_path = next((path for path in candidates if path.is_file()), None)
        if include_path is None:
            searched = "\n  ".join(str(path) for path in candidates)
            raise C64PreprocessorError(
                f"Include-Datei nicht gefunden: {include_name}\nGesucht in:\n  {searched}",
                location,
                self.include_stack,
            )
        try:
            data = include_path.read_bytes()
            try:
                text = data.decode("utf-8-sig")
            except UnicodeError:
                text = data.decode("cp1252")
        except (OSError, UnicodeError) as exc:
            raise C64PreprocessorError(
                f"Include-Datei kann nicht geoeffnet werden: {include_path}\n{exc}",
                location,
                self.include_stack,
            ) from exc

        canonical = include_path.resolve()
        canonical_text = str(canonical)
        if canonical_text not in self.included_files:
            self.included_files.append(canonical_text)
        self._process_text(text, canonical_text, canonical.parent, canonical)

    def _expand_line(
        self,
        text: str,
        location: SourceLocation,
        in_block_comment: bool,
    ) -> Tuple[str, bool]:
        result: List[str] = []
        index = 0
        while index < len(text):
            if in_block_comment:
                end = text.find("*/", index)
                if end < 0:
                    result.append(text[index:])
                    return "".join(result), True
                result.append(text[index:end + 2])
                index = end + 2
                in_block_comment = False
                continue
            if text.startswith("//", index):
                result.append(text[index:])
                break
            if text.startswith("/*", index):
                result.append("/*")
                index += 2
                in_block_comment = True
                continue
            character = text[index]
            if character in {'"', "'"}:
                end = self._quoted_end(text, index, character)
                result.append(text[index:end])
                index = end
                continue
            match = _IDENTIFIER_RE.match(text, index)
            if match is None:
                result.append(character)
                index += 1
                continue
            name = match.group(0)
            replacement, end = self._expand_identifier(
                text,
                name,
                match.end(),
                location,
                set(),
                0,
            )
            result.append(replacement)
            index = end
        return "".join(result), in_block_comment

    def _expand_text(
        self,
        text: str,
        location: SourceLocation,
        disabled: Optional[Set[str]] = None,
        depth: int = 0,
    ) -> str:
        if depth > self.MAX_MACRO_DEPTH:
            raise C64PreprocessorError(
                "Maximale Makro-Expansionstiefe ueberschritten.",
                location,
                self.include_stack,
            )
        disabled = set(disabled or ())
        result: List[str] = []
        index = 0
        while index < len(text):
            if text.startswith("//", index) or text.startswith("/*", index):
                result.append(text[index:])
                break
            character = text[index]
            if character in {'"', "'"}:
                end = self._quoted_end(text, index, character)
                result.append(text[index:end])
                index = end
                continue
            match = _IDENTIFIER_RE.match(text, index)
            if match is None:
                result.append(character)
                index += 1
                continue
            name = match.group(0)
            replacement, end = self._expand_identifier(
                text,
                name,
                match.end(),
                location,
                disabled,
                depth,
            )
            result.append(replacement)
            index = end
        return "".join(result)

    def _expand_identifier(
        self,
        text: str,
        name: str,
        end: int,
        location: SourceLocation,
        disabled: Set[str],
        depth: int,
    ) -> Tuple[str, int]:
        if name == "__FILE__":
            escaped = location.filename.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"', end
        if name == "__LINE__":
            return str(location.line), end
        macro = self.macros.get(name)
        if macro is None or name in disabled:
            return name, end
        next_disabled = set(disabled)
        next_disabled.add(name)
        if not macro.function_like:
            return (
                self._expand_text(
                    macro.replacement,
                    location,
                    next_disabled,
                    depth + 1,
                ),
                end,
            )

        invocation = end
        while invocation < len(text) and text[invocation] in " \t":
            invocation += 1
        if invocation >= len(text) or text[invocation] != "(":
            return name, end
        arguments, invocation_end = self._macro_arguments(text, invocation, location)
        parameters = macro.parameters or ()
        if len(arguments) != len(parameters):
            raise C64PreprocessorError(
                f"Makro {name} erwartet {len(parameters)} Argument(e), erhalten: {len(arguments)}.",
                location,
                self.include_stack,
            )
        values = {
            parameter: self._expand_text(argument.strip(), location, disabled, depth + 1)
            for parameter, argument in zip(parameters, arguments)
        }
        substituted = self._substitute_parameters(macro.replacement, values)
        return (
            self._expand_text(substituted, location, next_disabled, depth + 1),
            invocation_end,
        )

    def _macro_arguments(
        self,
        text: str,
        opening: int,
        location: SourceLocation,
    ) -> Tuple[List[str], int]:
        arguments: List[str] = []
        current: List[str] = []
        depth = 1
        index = opening + 1
        while index < len(text):
            character = text[index]
            if character in {'"', "'"}:
                end = self._quoted_end(text, index, character)
                current.append(text[index:end])
                index = end
                continue
            if character == "(":
                depth += 1
                current.append(character)
            elif character == ")":
                depth -= 1
                if depth == 0:
                    if current or arguments:
                        arguments.append("".join(current))
                    return arguments, index + 1
                current.append(character)
            elif character == "," and depth == 1:
                arguments.append("".join(current))
                current.clear()
            else:
                current.append(character)
            index += 1
        raise C64PreprocessorError(
            "Fehlende ')' beim Aufruf eines Makros.",
            location,
            self.include_stack,
        )

    def _substitute_parameters(self, text: str, values: Mapping[str, str]) -> str:
        result: List[str] = []
        index = 0
        while index < len(text):
            character = text[index]
            if character in {'"', "'"}:
                end = self._quoted_end(text, index, character)
                result.append(text[index:end])
                index = end
                continue
            match = _IDENTIFIER_RE.match(text, index)
            if match is None:
                result.append(character)
                index += 1
                continue
            name = match.group(0)
            result.append(values.get(name, name))
            index = match.end()
        return "".join(result)

    @staticmethod
    def _quoted_end(text: str, opening: int, quote: str) -> int:
        index = opening + 1
        while index < len(text):
            if text[index] == "\\":
                index += 2
                continue
            if text[index] == quote:
                return index + 1
            index += 1
        return len(text)


def preprocess_c_source(
    source: str,
    *,
    filename: str = "<C-Editor>",
    include_paths: Iterable[Path | str] = (),
    predefined_macros: Optional[Mapping[str, str | int | bool]] = None,
) -> PreprocessResult:
    """Fuehrt die C-Praeprozessorstufe aus und liefert Quellpositionsdaten."""
    return C64CPreprocessor(
        include_paths=include_paths,
        predefined_macros=predefined_macros,
    ).process(source, filename=filename)

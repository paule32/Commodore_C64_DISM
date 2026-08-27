# ---------------------------------------------------------------------------
# File:   makedef.32.py
# Author: (c) 2024, 2025, 2026 Jens Kallup - paule32
# All rights reserved
# ---------------------------------------------------------------------------
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


IMPORTS_FILES = {
    "libruntime_all.dll": [
        "crypto",
        "diskio",
        "arrays",
        "strings",
        "console",
        "runtime",
        "memory",
        "exception",
        "debug",
        "error",
        "kernel32"
    ]
}

# Rückwärtskompatibilität mit bestehendem Code, der den alten Namen nutzt.
imports_files = IMPORTS_FILES

DEFAULT_BASE_DIR      = Path("exports")
DEFAULT_DEF_OUTPUT    = Path("win32/libdbase2many.32.def")
DEFAULT_PYTHON_OUTPUT = Path("../compiler/frontend/dllimports.py")
DEFAULT_COMMONDATA_OUTPUT = Path("../compiler/common/runtime_imports.py")

EXPORT_LINE_RE = re.compile(
    r"^(?P<symbol>[^\s;]+)"
    r"\s+@(?P<ordinal>[0-9]+)"
    r"(?P<suffix>(?:\s+.*)?)$"
)

@dataclass(frozen=True)
class ExportEntry:
    symbol: str
    ordinal: int
    suffix: str = ""

    @property
    def def_line(self) -> str:
        return f"{self.symbol} @{self.ordinal}{self.suffix}"

def parse_export_line(line: str, filename: Path, line_number: int) -> ExportEntry | None:
    text = line.strip()

    if not text:
        return None

    if text.startswith(";"):
        return None

    upper_text = text.upper()

    if upper_text.startswith("LIBRARY"):
        return None

    if upper_text == "EXPORTS":
        return None

    # Kommentar am Zeilenende entfernen.
    declaration = text.split(";", 1)[0].rstrip()
    match = EXPORT_LINE_RE.fullmatch(declaration)

    if match is None:
        raise ValueError(
            f"Ungültige DEF-Zeile in {filename}:{line_number}: "
            f"{line.rstrip()}"
        )

    symbol = match.group("symbol")
    ordinal = int(match.group("ordinal"), 10)
    suffix = match.group("suffix") or ""

    if not 1 <= ordinal <= 0xFFFF:
        raise ValueError(
            f"Ungültige Ordinalnummer in {filename}:{line_number}: "
            f"{ordinal}"
        )

    return ExportEntry(
        symbol=symbol,
        ordinal=ordinal,
        suffix=suffix
    )

def collect_exports(base_dir: str | Path = DEFAULT_BASE_DIR) -> dict[str, list[ExportEntry]]:
    base_path = Path(base_dir)
    result: dict[str, list[ExportEntry]] = {}

    for dll_name, def_names in IMPORTS_FILES.items():
        entries: list[ExportEntry] = []
        symbols: dict[str, ExportEntry] = {}
        ordinals: dict[int, ExportEntry] = {}

        for def_name in def_names:
            def_file = base_path / f"{def_name}.def"

            if not def_file.is_file():
                raise FileNotFoundError(
                    f"DEF-Datei nicht gefunden: {def_file}"
                )

            lines = def_file.read_text(
                encoding="ascii"
            ).splitlines()

            for line_number, line in enumerate(lines, start=1):
                entry = parse_export_line(
                    line,
                    def_file,
                    line_number
                )

                if entry is None:
                    continue

                symbol_key = entry.symbol.lower()
                old_symbol = symbols.get(symbol_key)

                if old_symbol is not None:
                    if old_symbol != entry:
                        raise ValueError(
                            f"Widersprüchliche Definition für "
                            f"{entry.symbol}: {old_symbol.def_line} / "
                            f"{entry.def_line}"
                        )

                    # Identische Wiederholung ist unproblematisch.
                    continue

                old_ordinal = ordinals.get(entry.ordinal)

                if old_ordinal is not None:
                    raise ValueError(
                        f"Ordinal @{entry.ordinal} ist doppelt vergeben: "
                        f"{old_ordinal.symbol} und {entry.symbol}"
                    )

                symbols[symbol_key] = entry
                ordinals[entry.ordinal] = entry
                entries.append(entry)

        result[dll_name] = sorted(
            entries,
            key=lambda item: (item.ordinal, item.symbol.lower())
        )

    return result

def parse_library_name(
    line: str,
    filename: Path,
    line_number: int
) -> str:
    match = re.fullmatch(
        r'LIBRARY\s+(?:"(?P<quoted>[^"]+)"|(?P<plain>\S+))',
        line.strip(),
        re.IGNORECASE
    )

    if match is None:
        raise ValueError(
            f"Ungültige LIBRARY-Zeile in "
            f"{filename}:{line_number}: {line.rstrip()}"
        )

    dll_name = (
        match.group("quoted")
        or match.group("plain")
        or ""
    ).strip()

    if not dll_name:
        raise ValueError(
            f"Leerer DLL-Name in {filename}:{line_number}"
        )

    return dll_name


def collect_exports_from_merged_def(
    def_file: str | Path
) -> dict[str, list[ExportEntry]]:
    """Liest eine bereits gebündelte DEF-Datei."""
    path = Path(def_file)

    if not path.is_file():
        raise FileNotFoundError(
            f"Gebündelte DEF-Datei nicht gefunden: {path}"
        )

    result: dict[str, list[ExportEntry]] = {}
    symbols: dict[str, dict[str, ExportEntry]] = {}
    ordinals: dict[str, dict[int, ExportEntry]] = {}

    current_dll: str | None = None
    exports_seen = False

    lines = path.read_text(
        encoding="ascii"
    ).splitlines()

    for line_number, line in enumerate(lines, start=1):
        text = line.strip()

        if not text or text.startswith(";"):
            continue

        if text.upper().startswith("LIBRARY"):
            current_dll = parse_library_name(
                line,
                path,
                line_number
            )

            if current_dll in result:
                raise ValueError(
                    f"DLL {current_dll} ist in {path}:{line_number} "
                    f"mehrfach definiert"
                )

            result[current_dll] = []
            symbols[current_dll] = {}
            ordinals[current_dll] = {}
            exports_seen = False
            continue

        if text.upper() == "EXPORTS":
            if current_dll is None:
                raise ValueError(
                    f"EXPORTS ohne vorherige LIBRARY-Zeile "
                    f"in {path}:{line_number}"
                )

            exports_seen = True
            continue

        if current_dll is None:
            raise ValueError(
                f"Export ohne vorherige LIBRARY-Zeile "
                f"in {path}:{line_number}: {line.rstrip()}"
            )

        if not exports_seen:
            raise ValueError(
                f"Export vor EXPORTS in "
                f"{path}:{line_number}: {line.rstrip()}"
            )

        entry = parse_export_line(
            line,
            path,
            line_number
        )

        if entry is None:
            continue

        symbol_key = entry.symbol.lower()
        old_symbol = symbols[current_dll].get(
            symbol_key
        )

        if old_symbol is not None:
            if old_symbol != entry:
                raise ValueError(
                    f"Widersprüchliche Definition für "
                    f"{entry.symbol}: {old_symbol.def_line} / "
                    f"{entry.def_line}"
                )

            continue

        old_ordinal = ordinals[current_dll].get(
            entry.ordinal
        )

        if old_ordinal is not None:
            raise ValueError(
                f"Ordinal @{entry.ordinal} ist doppelt vergeben: "
                f"{old_ordinal.symbol} und {entry.symbol}"
            )

        symbols[current_dll][symbol_key] = entry
        ordinals[current_dll][entry.ordinal] = entry
        result[current_dll].append(entry)

    if not result:
        raise ValueError(
            f"Keine LIBRARY-Definition in {path} gefunden"
        )

    for dll_name, entries in result.items():
        if not entries:
            raise ValueError(
                f"Keine Exporte für {dll_name} in {path} gefunden"
            )

        entries.sort(
            key=lambda item: (
                item.ordinal,
                item.symbol.lower()
            )
        )

    return result


def write_commondata_import_module(
    output_file: str | Path,
    exports: dict[str, list[ExportEntry]]
) -> None:
    """
    Schreibt ein importierbares Modul zur Initialisierung von
    CommonData.imports.

    Bereits vorhandene Einträge wie kernel32.dll, user32.dll und mpr.dll
    bleiben erhalten. Ein DLL-Eintrag aus der DEF-Datei ersetzt dagegen
    gezielt einen eventuell veralteten Eintrag derselben DLL.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    lines = [
        "# ---------------------------------------------------------------------------",
        "# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY",
        "# Generated by makedef.32.py --python from the merged DEF file.",
        "# ---------------------------------------------------------------------------",
        "from __future__ import annotations",
        "",
        "",
        "def initialize_commondata_imports(self) -> None:",
        "    \"\"\"Aktualisiert CommonData.imports mit den DEF-Ordinalen.\"\"\"",
        "    self.imports = {",
        "        **getattr(self, 'imports', {}),",
    ]

    for dll_name, entries in exports.items():
        lines.append(f"        {dll_name!r}: [")

        for entry in entries:
            lines.append(
                f"            ({entry.symbol!r}, {entry.ordinal}),"
            )

        lines.append("        ],")

    lines.extend([
        "    }",
        "",
        "",
        "__all__ = [",
        "    'initialize_commondata_imports',",
        "]",
        ""
    ])

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n"
    )


def write_merged_def_file(
    output_file: str | Path,
    base_dir: str | Path = DEFAULT_BASE_DIR,
    exports: dict[str, list[ExportEntry]] | None = None
) -> dict[str, list[ExportEntry]]:
    
    output_path = Path(output_file)

    if exports is None:
        exports = collect_exports(base_dir)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="ascii",
        newline="\n"
    ) as out:
        out.write("; ---------------------------------------------------------------------------\n")
        out.write("; AUTO-GENERATED FILE - DO NOT EDIT MANUALLY\n")
        out.write("; Generated by makedef.32.py from the grouped DEF files.\n")
        out.write("; ---------------------------------------------------------------------------\n")
        for dll_name, entries in exports.items():
            out.write(f'LIBRARY "{dll_name}"\n')
            out.write("EXPORTS\n")

            for entry in entries:
                out.write(f"    {entry.def_line} NONAME\n")

            out.write("\n")

    return exports

def python_constant_name(dll_name: str) -> str:
    stem = Path(dll_name).stem
    normalized = re.sub(
        r"[^A-Za-z0-9]+",
        "",
        stem
    ).upper()

    return normalized + "_IMPORT_ORDINALS"

def write_python_ordinal_module(
    output_file: str | Path,
    exports: dict[str, list[ExportEntry]]
) -> None:
    
    output_path = Path(output_file)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    lines = [
        "# ---------------------------------------------------------------------------",
        "# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY",
        "# Generated by makedef.32.py from the grouped DEF files.",
        "# ---------------------------------------------------------------------------",
        "from __future__ import annotations",
        "",
    ]

    exported_names: list[str] = []

    for dll_name, entries in exports.items():
        constant_name = python_constant_name(dll_name)
        dll_constant = constant_name.removesuffix(
            "_IMPORT_ORDINALS"
        ) + "_DLL_NAME"
        reverse_name = constant_name.removesuffix(
            "_IMPORT_ORDINALS"
        ) + "_ORDINAL_IMPORTS"

        exported_names.extend([
            dll_constant,
            constant_name,
            reverse_name
        ])

        lines.append(f'{dll_constant} = {dll_name!r}')
        lines.append("")
        lines.append(f"{constant_name} = {{")

        for entry in entries:
            lines.append(
                f"    {entry.symbol!r}: {entry.ordinal},"
            )

        lines.append("}")
        lines.append("")
        lines.append(f"{reverse_name} = {{")
        lines.append(
            f"    ordinal: symbol for symbol, ordinal in "
            f"{constant_name}.items()"
        )
        lines.append("}")
        lines.append("")

    exported_names.append("find_import_ordinal")
    exported_names.append("find_import_symbol")

    lines.extend([
        "def find_import_ordinal(",
        "    dll_name: str,",
        "    symbol: str",
        ") -> int | None:",
        "    \"\"\"Liefert die bekannte Ordinalnummer oder None.\"\"\"",
        "    normalized_dll = str(dll_name).strip().lower()",
        "",
    ])

    for dll_name in exports:
        constant_name = python_constant_name(dll_name)
        dll_constant = constant_name.removesuffix(
            "_IMPORT_ORDINALS"
        ) + "_DLL_NAME"
        lines.extend([
            f"    if normalized_dll == {dll_constant}.lower():",
            f"        return {constant_name}.get(str(symbol))",
            "",
        ])

    lines.extend([
        "    return None",
        "",
        "",
        "def find_import_symbol(",
        "    dll_name: str,",
        "    ordinal: int",
        ") -> str | None:",
        "    \"\"\"Liefert den bekannten Symbolnamen oder None.\"\"\"",
        "    normalized_dll = str(dll_name).strip().lower()",
        "",
    ])

    for dll_name in exports:
        constant_name = python_constant_name(dll_name)
        dll_constant = constant_name.removesuffix(
            "_IMPORT_ORDINALS"
        ) + "_DLL_NAME"
        reverse_name = constant_name.removesuffix(
            "_IMPORT_ORDINALS"
        ) + "_ORDINAL_IMPORTS"
        lines.extend([
            f"    if normalized_dll == {dll_constant}.lower():",
            f"        return {reverse_name}.get(int(ordinal))",
            "",
        ])

    lines.extend([
        "    return None",
        "",
        "",
        "__all__ = [",
    ])

    for name in exported_names:
        lines.append(f"    {name!r},")

    lines.extend([
        "]",
        ""
    ])

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n"
    )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bündelt gruppierte DEF-Dateien und erzeugt ein "
            "importierbares Python-Modul mit den Ordinaltabellen."
        )
    )

    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Verzeichnis mit den gruppierten DEF-Dateien"
    )

    parser.add_argument(
        "--def-output",
        default=str(DEFAULT_DEF_OUTPUT),
        help="Zieldatei der gebündelten DEF-Datei"
    )

    parser.add_argument(
        "--python-output",
        default=str(DEFAULT_PYTHON_OUTPUT),
        help="Zieldatei des erzeugten Ordinal-Moduls"
    )

    parser.add_argument(
        "--ignore",
        action="store_true",
        help=(
            "Gruppierte DEF-Dateien ignorieren und die vorhandene "
            "Datei aus --def-output lesen. Ohne --python wird daraus "
            "nur das Ordinal-Modul aus --python-output erzeugt."
        )
    )

    parser.add_argument(
        "--python",
        nargs="?",
        const=str(DEFAULT_COMMONDATA_OUTPUT),
        metavar="OUTPUT",
        help=(
            "Aus der vorhandenen Datei aus --def-output ein "
            "importierbares CommonData.imports-Modul schreiben. "
            "Optional kann direkt der Ausgabepfad angegeben werden. "
            "Dieser Schalter impliziert das Lesen der vorhandenen DEF-Datei."
        )
    )

    return parser.parse_args()

def main() -> int:
    args = parse_arguments()

    read_existing_def = (
        args.ignore
        or args.python is not None
    )

    if read_existing_def:
        exports = collect_exports_from_merged_def(
            args.def_output
        )

        print(
            f"Vorhandene DEF-Datei gelesen: "
            f"{Path(args.def_output)}"
        )

        if args.ignore:
            write_python_ordinal_module(
                args.python_output,
                exports
            )

            print(
                f"Ordinal-Modul geschrieben: "
                f"{Path(args.python_output)}"
            )

        if args.python is not None:
            write_commondata_import_module(
                args.python,
                exports
            )

            print(
                f"CommonData-Importmodul geschrieben: "
                f"{Path(args.python)}"
            )

        export_count = sum(
            len(entries)
            for entries in exports.values()
        )

        print(
            f"Importierte Symbole: {export_count}"
        )

        return 0

    exports = collect_exports(
        args.base_dir
    )

    write_merged_def_file(
        args.def_output,
        base_dir=args.base_dir,
        exports=exports
    )

    write_python_ordinal_module(
        args.python_output,
        exports
    )

    export_count = sum(
        len(entries)
        for entries in exports.values()
    )

    print(
        f"DEF-Datei geschrieben: "
        f"{Path(args.def_output)}"
    )

    print(
        f"Ordinal-Modul geschrieben: "
        f"{Path(args.python_output)}"
    )

    print(
        f"Exportierte Symbole: {export_count}"
    )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

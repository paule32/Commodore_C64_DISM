#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# File:   make_thunks_mini.py
# Author: generated for paule32
# Target: Python 3.10+, NASM win32/COFF32, GNU ar
# ---------------------------------------------------------------------------
"""
Erzeugt aus dem EXPORTS-Abschnitt einer DEF-Datei kleine i386-Import-Thunks.

Für jedes Funktionssymbol wird eine eigene NASM-Datei und daraus ein eigenes
COFF32-Objekt erzeugt. Anschließend werden alle Objekte in das indexierte
Archiv ``libthunks_mini.a`` geschrieben.

Standardmäßig wird die 32-Bit-MinGW-Schreibweise verwendet:

    DEF-Symbol:       LoadLibraryA@4
    Thunk-Symbol:     _LoadLibraryA@4
    IAT-Referenz:     __imp__LoadLibraryA@4

Der generierte Thunk besteht sinngemäß aus:

    _LoadLibraryA@4:
        jmp dword [__imp__LoadLibraryA@4]

Wichtig: Das Archiv enthält absichtlich nur die kleinen Code-Thunks. Die
jeweiligen __imp_-IAT-Symbole müssen vom PE-Linker beziehungsweise von einer
separaten Import-Library bereitgestellt werden.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_ARCHIVE = "libthunks_mini.a"
DEFAULT_OBJ_DIR = "obj"

# NASM unterstützt für externe COFF-Symbole unter anderem die Zeichen, die
# in stdcall- und Microsoft-C++-Dekorationen vorkommen.
NASM_IDENTIFIER_RE = re.compile(
    r"^[A-Za-z_?.@#$~][A-Za-z0-9_?.@#$~]*$"
)

TOP_LEVEL_KEYWORDS = {
    "CODE",
    "DATA",
    "DESCRIPTION",
    "EXPORTS",
    "HEAPSIZE",
    "IMPORTS",
    "LIBRARY",
    "NAME",
    "SECTIONS",
    "STACKSIZE",
    "VERSION",
}


class BuildError(RuntimeError):
    """Fehler, der ohne Python-Traceback ausgegeben werden soll."""


@dataclass(frozen=True)
class DefExport:
    export_name: str
    internal_name: str | None
    ordinal: int | None
    noname: bool
    is_data: bool
    is_constant: bool
    is_private: bool
    line_number: int


@dataclass(frozen=True)
class DefFile:
    filename: Path
    library_name: str | None
    exports: tuple[DefExport, ...]


@dataclass(frozen=True)
class ThunkJob:
    source: DefExport
    public_symbol: str
    iat_symbol: str
    asm_path: Path
    object_path: Path


def remove_def_comment(line: str) -> str:
    """Entfernt ein DEF-Semikolon-Kommentar außerhalb von Anführungszeichen."""

    quote: str | None = None

    for index, char in enumerate(line):
        if quote is not None:
            if char == quote:
                quote = None
            continue

        if char in ("'", '"'):
            quote = char
        elif char == ";":
            return line[:index]

    return line


def read_text_file(filename: Path) -> str:
    """Liest typische UTF-8- oder Windows-DEF-Dateien."""

    raw = filename.read_bytes()

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass

    raise BuildError(
        f"DEF-Datei kann weder als UTF-8 noch als CP1252 gelesen werden: "
        f"{filename}"
    )


def read_def_atom(text: str, position: int) -> tuple[str, int]:
    """Liest einen möglicherweise in Anführungszeichen stehenden DEF-Namen."""

    length = len(text)

    while position < length and text[position].isspace():
        position += 1

    if position >= length:
        return "", position

    quote = text[position] if text[position] in ("'", '"') else None

    if quote is not None:
        position += 1
        start = position

        while position < length and text[position] != quote:
            position += 1

        if position >= length:
            raise ValueError("fehlendes schließendes Anführungszeichen")

        value = text[start:position]
        return value, position + 1

    start = position

    while (
        position < length
        and not text[position].isspace()
        and text[position] != "="
    ):
        position += 1

    return text[start:position], position


def split_def_tokens(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def parse_export_line(
    text: str,
    filename: Path,
    line_number: int,
) -> DefExport:
    try:
        export_name, position = read_def_atom(text, 0)

        if not export_name:
            raise ValueError("Exportname fehlt")

        while position < len(text) and text[position].isspace():
            position += 1

        internal_name: str | None = None

        if position < len(text) and text[position] == "=":
            internal_name, position = read_def_atom(text, position + 1)

            if not internal_name:
                raise ValueError("interner Name hinter '=' fehlt")

        remaining = text[position:].strip()
        tokens = split_def_tokens(remaining) if remaining else []
    except ValueError as error:
        raise BuildError(
            f"{filename}:{line_number}: ungültiger EXPORTS-Eintrag: {error}"
        ) from error

    ordinal: int | None = None
    flags: set[str] = set()

    for token in tokens:
        upper = token.upper()

        if re.fullmatch(r"@[0-9]+", token):
            if ordinal is not None:
                raise BuildError(
                    f"{filename}:{line_number}: Ordinal doppelt angegeben"
                )
            ordinal = int(token[1:], 10)
            continue

        if upper not in {"NONAME", "DATA", "CONSTANT", "PRIVATE"}:
            raise BuildError(
                f"{filename}:{line_number}: unbekanntes Export-Attribut: "
                f"{token}"
            )

        flags.add(upper)

    return DefExport(
        export_name=export_name,
        internal_name=internal_name,
        ordinal=ordinal,
        noname="NONAME" in flags,
        is_data="DATA" in flags,
        is_constant="CONSTANT" in flags,
        is_private="PRIVATE" in flags,
        line_number=line_number,
    )


def parse_library_line(text: str) -> str | None:
    tokens = split_def_tokens(text)

    if len(tokens) < 2:
        return None

    # Ein eventuell folgendes BASE=... gehört nicht zum DLL-Namen.
    return tokens[1]


def parse_def_file(filename: Path) -> DefFile:
    if not filename.is_file():
        raise BuildError(f"DEF-Datei nicht gefunden: {filename}")

    text = read_text_file(filename)
    library_name: str | None = None
    exports: list[DefExport] = []
    in_exports = False
    found_exports_section = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = remove_def_comment(raw_line).strip()

        if not line:
            continue

        first_word = line.split(None, 1)[0].upper()

        if first_word == "LIBRARY":
            library_name = parse_library_line(line)
            in_exports = False
            continue

        if first_word == "EXPORTS":
            in_exports = True
            found_exports_section = True

            # Auch "EXPORTS Foo" wird akzeptiert.
            rest = line[len(line.split(None, 1)[0]):].strip()
            if rest:
                exports.append(
                    parse_export_line(rest, filename, line_number)
                )
            continue

        if in_exports and first_word in TOP_LEVEL_KEYWORDS:
            in_exports = False

        if in_exports:
            exports.append(
                parse_export_line(line, filename, line_number)
            )

    if not found_exports_section:
        raise BuildError(
            f"DEF-Datei enthält keinen EXPORTS-Abschnitt: {filename}"
        )

    if not exports:
        raise BuildError(
            f"DEF-Datei enthält keine Exporte: {filename}"
        )

    return DefFile(
        filename=filename,
        library_name=library_name,
        exports=tuple(exports),
    )


def decorate_public_symbol(symbol: str, symbol_style: str) -> str:
    if symbol_style == "mingw":
        return "_" + symbol

    if symbol_style == "raw":
        return symbol

    raise AssertionError(f"unbekannter Symbolstil: {symbol_style}")


def nasm_identifier(symbol: str, source: DefExport) -> str:
    if not NASM_IDENTIFIER_RE.fullmatch(symbol):
        raise BuildError(
            f"DEF-Zeile {source.line_number}: Symbol kann von NASM nicht "
            f"direkt dargestellt werden: {symbol!r}. Verwende in der "
            f"DEF-Datei einen gültigen Alias."
        )

    # Das $ zwingt NASM, auch Namen wie WAIT als Identifier statt als
    # reserviertes Wort auszuwerten. Das $ gehört nicht zum COFF-Symbol.
    return "$" + symbol


def filename_fragment(symbol: str) -> str:
    fragment = re.sub(r"[^A-Za-z0-9]+", "_", symbol).strip("_")

    if not fragment:
        fragment = "symbol"

    return fragment[:48]


def make_jobs(
    def_file: DefFile,
    obj_dir: Path,
    symbol_style: str,
    iat_prefix: str,
    include_private: bool,
) -> tuple[list[ThunkJob], list[DefExport]]:
    jobs: list[ThunkJob] = []
    skipped: list[DefExport] = []
    seen_public: dict[str, DefExport] = {}
    seen_iat: dict[str, DefExport] = {}

    for export in def_file.exports:
        if export.is_data or export.is_constant:
            skipped.append(export)
            continue

        if export.is_private and not include_private:
            skipped.append(export)
            continue

        public_symbol = decorate_public_symbol(
            export.export_name,
            symbol_style,
        )
        iat_symbol = iat_prefix + public_symbol

        nasm_identifier(public_symbol, export)
        nasm_identifier(iat_symbol, export)

        if public_symbol in seen_public:
            previous = seen_public[public_symbol]
            raise BuildError(
                f"doppeltes Thunk-Symbol {public_symbol!r} in DEF-Zeile "
                f"{previous.line_number} und {export.line_number}"
            )

        if iat_symbol in seen_iat:
            previous = seen_iat[iat_symbol]
            raise BuildError(
                f"doppelte IAT-Referenz {iat_symbol!r} in DEF-Zeile "
                f"{previous.line_number} und {export.line_number}"
            )

        seen_public[public_symbol] = export
        seen_iat[iat_symbol] = export

        digest = hashlib.sha1(
            public_symbol.encode("utf-8")
        ).hexdigest()[:10]
        base_name = (
            f"thunk_{len(jobs) + 1:04d}_"
            f"{filename_fragment(public_symbol)}_{digest}"
        )

        jobs.append(
            ThunkJob(
                source=export,
                public_symbol=public_symbol,
                iat_symbol=iat_symbol,
                asm_path=obj_dir / f"{base_name}.asm",
                object_path=obj_dir / f"{base_name}.o",
            )
        )

    if not jobs:
        raise BuildError(
            "Nach dem Überspringen von DATA-, CONSTANT- und PRIVATE-Einträgen "
            "sind keine Funktionssymbole übrig."
        )

    return jobs, skipped


def render_assembly(job: ThunkJob, def_file: DefFile) -> str:
    public = nasm_identifier(job.public_symbol, job.source)
    iat = nasm_identifier(job.iat_symbol, job.source)
    dll_name = def_file.library_name or "(in DEF nicht angegeben)"

    source_suffix = ""
    if job.source.internal_name is not None:
        source_suffix = f" = {job.source.internal_name}"

    ordinal_suffix = ""
    if job.source.ordinal is not None:
        ordinal_suffix = f" @{job.source.ordinal}"

    noname_suffix = " NONAME" if job.source.noname else ""

    return (
        "; Automatisch erzeugt durch make_thunks_mini.py\n"
        f"; DLL:        {dll_name}\n"
        f"; DEF-Export: {job.source.export_name}"
        f"{source_suffix}{ordinal_suffix}{noname_suffix}\n"
        f"; COFF:       {job.public_symbol} -> [{job.iat_symbol}]\n"
        "\n"
        "BITS 32\n"
        "\n"
        "SECTION .text align=16\n"
        f"GLOBAL {public}\n"
        f"EXTERN {iat}\n"
        "\n"
        f"{public}:\n"
        f"    jmp dword [{iat}]\n"
    )


def write_assembly_files(
    jobs: Sequence[ThunkJob],
    def_file: DefFile,
) -> None:
    for job in jobs:
        job.asm_path.write_text(
            render_assembly(job, def_file),
            encoding="utf-8",
            newline="\n",
        )


def resolve_tool(
    explicit_name: str | None,
    candidates: Sequence[str],
    description: str,
) -> str:
    names = [explicit_name] if explicit_name else list(candidates)

    for name in names:
        if not name:
            continue

        # shutil.which() unterstützt sowohl einfache Programmnamen als auch
        # explizite Pfade.
        resolved = shutil.which(name)

        if resolved:
            return resolved

        path = Path(name)
        if path.is_file():
            return str(path.resolve())

    searched = ", ".join(repr(item) for item in names if item)
    raise BuildError(
        f"{description} nicht gefunden. Gesucht wurde nach: {searched}"
    )


def command_text(command: Sequence[str]) -> str:
    return subprocess.list2cmdline([str(item) for item in command])


def run_checked(
    command: Sequence[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [str(item) for item in command],
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise BuildError(
            f"Kommando konnte nicht gestartet werden:\n"
            f"  {command_text(command)}\n"
            f"  {error}"
        ) from error

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        if details:
            details = "\n" + details

        raise BuildError(
            f"Kommando ist mit Exitcode {result.returncode} fehlgeschlagen:\n"
            f"  {command_text(command)}{details}"
        )

    return result


def assemble_job(
    job: ThunkJob,
    nasm: str,
    nasm_args: Sequence[str],
) -> tuple[ThunkJob, str]:
    command = [
        nasm,
        "-f",
        "win32",
        "-Ox",
        *nasm_args,
        "-o",
        str(job.object_path),
        str(job.asm_path),
    ]
    result = run_checked(command)
    return job, result.stderr.strip()


def assemble_all(
    jobs: Sequence[ThunkJob],
    nasm: str,
    nasm_args: Sequence[str],
    jobs_count: int,
    verbose: bool,
) -> None:
    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=jobs_count) as executor:
        futures = {
            executor.submit(
                assemble_job,
                job,
                nasm,
                nasm_args,
            ): job
            for job in jobs
        }

        for future in as_completed(futures):
            job = futures[future]

            try:
                _, warning_text = future.result()
                if verbose:
                    print(f"COFF32: {job.object_path}")
                if warning_text:
                    print(warning_text, file=sys.stderr)
            except BuildError as error:
                failures.append(str(error))

    if failures:
        raise BuildError(
            f"{len(failures)} NASM-Kompilierung(en) fehlgeschlagen:\n\n"
            + "\n\n".join(failures)
        )


def chunks(
    values: Sequence[Path],
    chunk_size: int,
) -> Iterable[Sequence[Path]]:
    for start in range(0, len(values), chunk_size):
        yield values[start:start + chunk_size]


def create_indexed_archive(
    object_files: Sequence[Path],
    archive: Path,
    ar: str,
    batch_size: int,
    verbose: bool,
) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_name(
        f".{archive.name}.{os.getpid()}.tmp"
    )

    if temporary.exists():
        temporary.unlink()

    try:
        for batch_number, batch in enumerate(
            chunks(object_files, batch_size)
        ):
            operation = "rcs" if batch_number == 0 else "r"
            command = [
                ar,
                operation,
                str(temporary),
                *(str(filename) for filename in batch),
            ]
            run_checked(command)

        # Ein abschließendes "ar s" erzwingt ausdrücklich den Symbolindex.
        run_checked([ar, "s", str(temporary)])

        listing = run_checked([ar, "t", str(temporary)]).stdout.splitlines()
        actual_members = [item.strip().rstrip("/") for item in listing if item]
        expected_members = [item.name for item in object_files]

        if actual_members != expected_members:
            raise BuildError(
                "Archivprüfung fehlgeschlagen: Mitgliederliste stimmt nicht "
                "mit der Objektliste überein."
            )

        os.replace(temporary, archive)
    finally:
        if temporary.exists():
            temporary.unlink()

    if verbose:
        print(f"ARCHIV: {archive}")


def positive_integer(value: str) -> int:
    try:
        number = int(value, 10)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"positive Ganzzahl erwartet: {value!r}"
        ) from error

    if number < 1:
        raise argparse.ArgumentTypeError(
            f"Wert muss größer als 0 sein: {number}"
        )

    return number


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Erzeugt je DEF-Funktionssymbol einen NASM-Import-Thunk, "
            "kompiliert ihn als win32/COFF32 und erstellt ein indexiertes "
            "Archiv."
        )
    )
    parser.add_argument(
        "def_file",
        type=Path,
        help="Eingabe-DEF-Datei",
    )
    parser.add_argument(
        "--obj-dir",
        type=Path,
        default=Path(DEFAULT_OBJ_DIR),
        help=f"Verzeichnis für .asm und .o (Standard: {DEFAULT_OBJ_DIR})",
    )
    parser.add_argument(
        "-o",
        "--archive",
        type=Path,
        default=Path(DEFAULT_ARCHIVE),
        help=f"Zielarchiv (Standard: {DEFAULT_ARCHIVE})",
    )
    parser.add_argument(
        "--symbol-style",
        choices=("mingw", "raw"),
        default="mingw",
        help=(
            "mingw: führenden Unterstrich ergänzen; "
            "raw: DEF-Namen unverändert verwenden (Standard: mingw)"
        ),
    )
    parser.add_argument(
        "--iat-prefix",
        default="__imp_",
        help="Präfix des externen IAT-Symbols (Standard: __imp_)",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Auch mit PRIVATE markierte DEF-Exporte aufnehmen",
    )
    parser.add_argument(
        "--nasm",
        help="NASM-Programm oder vollständiger Pfad",
    )
    parser.add_argument(
        "--ar",
        help="GNU-ar-/llvm-ar-Programm oder vollständiger Pfad",
    )
    parser.add_argument(
        "--nasm-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="Zusätzliches NASM-Argument; mehrfach verwendbar",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=positive_integer,
        default=max(1, min(8, os.cpu_count() or 1)),
        help="Anzahl paralleler NASM-Prozesse (Standard: bis zu 8)",
    )
    parser.add_argument(
        "--ar-batch-size",
        type=positive_integer,
        default=100,
        help=(
            "Objekte pro ar-Aufruf; vermeidet zu lange Windows-"
            "Kommandozeilen (Standard: 100)"
        ),
    )
    parser.add_argument(
        "--emit-only",
        action="store_true",
        help="Nur NASM-Dateien erzeugen; nicht kompilieren/archivieren",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Jede erzeugte Objektdatei anzeigen",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        def_filename = args.def_file.resolve()
        obj_dir = args.obj_dir.resolve()
        archive = args.archive.resolve()

        def_file = parse_def_file(def_filename)
        obj_dir.mkdir(parents=True, exist_ok=True)

        thunk_jobs, skipped = make_jobs(
            def_file=def_file,
            obj_dir=obj_dir,
            symbol_style=args.symbol_style,
            iat_prefix=args.iat_prefix,
            include_private=args.include_private,
        )
        write_assembly_files(thunk_jobs, def_file)

        print(f"DEF:      {def_file.filename}")
        if def_file.library_name:
            print(f"LIBRARY:  {def_file.library_name}")
        print(f"THUNKS:   {len(thunk_jobs)}")
        print(f"OBJ-DIR:  {obj_dir}")

        if skipped:
            print(
                f"ÜBERSPRUNGEN: {len(skipped)} "
                f"(DATA/CONSTANT/PRIVATE)"
            )

        noname_count = sum(
            1 for job in thunk_jobs if job.source.noname
        )
        if noname_count:
            print(
                f"HINWEIS: {noname_count} NONAME-Export(e); "
                f"die Ordinalzuordnung wird von diesen reinen Code-Thunks "
                f"nicht gespeichert.",
                file=sys.stderr,
            )

        if args.emit_only:
            print("Nur NASM-Dateien erzeugt (--emit-only).")
            return 0

        nasm = resolve_tool(
            args.nasm,
            ("nasm", "nasm.exe"),
            "NASM",
        )
        ar = resolve_tool(
            args.ar,
            (
                "i686-w64-mingw32-ar",
                "i686-w64-mingw32-ar.exe",
                "ar",
                "ar.exe",
                "llvm-ar",
                "llvm-ar.exe",
            ),
            "Archivprogramm",
        )

        assemble_all(
            jobs=thunk_jobs,
            nasm=nasm,
            nasm_args=args.nasm_arg,
            jobs_count=min(args.jobs, len(thunk_jobs)),
            verbose=args.verbose,
        )
        create_indexed_archive(
            object_files=[job.object_path for job in thunk_jobs],
            archive=archive,
            ar=ar,
            batch_size=args.ar_batch_size,
            verbose=args.verbose,
        )

        print(f"ERSTELLT: {archive}")
        return 0

    except (BuildError, OSError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

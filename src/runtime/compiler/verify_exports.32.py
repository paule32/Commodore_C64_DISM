#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# File:   verify_exports.32.py
#
# Prüft eine PE32-DLL gegen die von makedef.32.py erzeugte Ordinaltabelle.
#
# Unterstützte Manifestformate:
#   - Python-Modul: libdbase2many32_ordinals.py
#   - JSON-Manifest mit einem "libraries"-Objekt
#
# Auch NONAME-Exporte werden geprüft. In diesem Fall kann aus der DLL nur
# verifiziert werden, dass der erwartete Ordinalslot existiert und eine
# gültige Export-RVA besitzt.
# ---------------------------------------------------------------------------
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


PYTHON_DLL_NAME = "LIBDBASE2MANY32_DLL_NAME"
PYTHON_ORDINAL_TABLE = "LIBDBASE2MANY32_IMPORT_ORDINALS"


EXPORT_ADDRESS_RE = re.compile(
    r"^\s*\[\s*(?P<index>[0-9]+)\]\s+"
    r"\+base\[\s*(?P<ordinal>[0-9]+)\]\s+"
    r"(?P<rva>[0-9A-Fa-f]+)\s+"
    r"Export RVA\s*$"
)

EXPORT_NAME_RE = re.compile(
    r"^\s*\[\s*(?P<index>[0-9]+)\]\s+"
    r"\+base\[\s*(?P<ordinal>[0-9]+)\]\s+"
    r"[0-9A-Fa-f]+\s+"
    r"(?P<name>\S+)\s*$"
)


@dataclass(frozen=True)
class ExportTable:
    ordinal_to_rva: dict[int, int]
    ordinal_to_name: dict[int, str]
    name_to_ordinal: dict[str, int]


@dataclass(frozen=True)
class ExpectedExports:
    dll_name: str
    symbol_to_ordinal: dict[str, int]


def normalize_dll_name(value: str) -> str:
    return Path(str(value).strip()).name.lower()


def load_python_module(path: Path) -> ModuleType:
    module_name = (
        "_dBase2Many_generated_ordinals_"
        + str(abs(hash(path.resolve())))
    )

    spec = importlib.util.spec_from_file_location(
        module_name,
        path
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            f"Python-Modul kann nicht geladen werden: {path}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def validate_expected_table(
    dll_name: str,
    table: object,
    source: Path
) -> ExpectedExports:
    if not isinstance(table, dict):
        raise TypeError(
            f"Ordinaltabelle in {source} ist kein Dictionary"
        )

    result: dict[str, int] = {}
    used_ordinals: dict[int, str] = {}

    for raw_symbol, raw_ordinal in table.items():
        symbol = str(raw_symbol).strip()

        if not symbol:
            raise ValueError(
                f"Leerer Symbolname in {source}"
            )

        if isinstance(raw_ordinal, bool):
            raise TypeError(
                f"Ungültige Ordinalnummer für {symbol}: "
                f"{raw_ordinal!r}"
            )

        try:
            ordinal = int(raw_ordinal)
        except (TypeError, ValueError):
            raise TypeError(
                f"Ungültige Ordinalnummer für {symbol}: "
                f"{raw_ordinal!r}"
            ) from None

        if not 1 <= ordinal <= 0xFFFF:
            raise ValueError(
                f"Ordinal @{ordinal} für {symbol} "
                f"liegt außerhalb 1..65535"
            )

        old_symbol = used_ordinals.get(
            ordinal
        )

        if old_symbol is not None:
            raise ValueError(
                f"Ordinal @{ordinal} ist im Manifest "
                f"doppelt vergeben: {old_symbol} und {symbol}"
            )

        used_ordinals[ordinal] = symbol
        result[symbol] = ordinal

    if not result:
        raise RuntimeError(
            f"Keine Exporte in {source} gefunden"
        )

    return ExpectedExports(
        dll_name=Path(dll_name).name,
        symbol_to_ordinal=result
    )


def load_python_manifest(
    path: Path
) -> ExpectedExports:
    module = load_python_module(
        path
    )

    dll_name = getattr(
        module,
        PYTHON_DLL_NAME,
        None
    )

    table = getattr(
        module,
        PYTHON_ORDINAL_TABLE,
        None
    )

    if not isinstance(dll_name, str) or not dll_name.strip():
        raise RuntimeError(
            f"{PYTHON_DLL_NAME} fehlt in {path}"
        )

    if table is None:
        raise RuntimeError(
            f"{PYTHON_ORDINAL_TABLE} fehlt in {path}"
        )

    return validate_expected_table(
        dll_name,
        table,
        path
    )


def load_json_manifest(
    path: Path,
    dll_file: Path
) -> ExpectedExports:
    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    libraries = data.get(
        "libraries"
    )

    if not isinstance(libraries, dict):
        raise RuntimeError(
            f"JSON-Manifest {path} enthält kein "
            f"'libraries'-Objekt"
        )

    wanted_name = normalize_dll_name(
        dll_file.name
    )

    selected_name = None
    selected_table = None

    for raw_name, raw_table in libraries.items():
        if normalize_dll_name(raw_name) == wanted_name:
            selected_name = str(raw_name)
            selected_table = raw_table
            break

    if selected_name is None:
        raise RuntimeError(
            f"Kein Manifest-Eintrag für {dll_file.name} "
            f"in {path}"
        )

    return validate_expected_table(
        selected_name,
        selected_table,
        path
    )


def load_expected_exports(
    path: Path,
    dll_file: Path
) -> ExpectedExports:
    suffix = path.suffix.lower()

    if suffix == ".py":
        return load_python_manifest(
            path
        )

    if suffix == ".json":
        return load_json_manifest(
            path,
            dll_file
        )

    raise ValueError(
        f"Nicht unterstütztes Manifestformat: {path.suffix}; "
        f"erwartet .py oder .json"
    )


def run_objdump(
    dll_file: Path,
    objdump: str
) -> str:
    executable = shutil.which(
        objdump
    )

    if executable is None:
        raise FileNotFoundError(
            f"objdump nicht gefunden: {objdump}"
        )

    process = subprocess.run(
        [
            executable,
            "-p",
            str(dll_file)
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if process.returncode != 0:
        message = (
            process.stderr.strip()
            or process.stdout.strip()
            or f"{objdump} konnte {dll_file} nicht lesen"
        )

        raise RuntimeError(
            message
        )

    return process.stdout


def parse_objdump_exports(
    output: str
) -> ExportTable:
    ordinal_to_rva: dict[int, int] = {}
    ordinal_to_name: dict[int, str] = {}
    name_to_ordinal: dict[str, int] = {}

    section = None

    for raw_line in output.splitlines():
        line = raw_line.rstrip()

        if line.startswith(
            "Export Address Table --"
        ):
            section = "addresses"
            continue

        if line.startswith(
            "[Ordinal/Name Pointer] Table --"
        ):
            section = "names"
            continue

        if line.startswith(
            "PE File Base Relocations"
        ):
            section = None
            break

        if section == "addresses":
            match = EXPORT_ADDRESS_RE.match(
                line
            )

            if match is None:
                continue

            ordinal = int(
                match.group("ordinal"),
                10
            )

            rva = int(
                match.group("rva"),
                16
            )

            ordinal_to_rva[ordinal] = rva
            continue

        if section == "names":
            match = EXPORT_NAME_RE.match(
                line
            )

            if match is None:
                continue

            ordinal = int(
                match.group("ordinal"),
                10
            )

            name = match.group(
                "name"
            )

            old_name = ordinal_to_name.get(
                ordinal
            )

            if old_name is not None and old_name != name:
                raise RuntimeError(
                    f"DLL enthält mehrere Namen für Ordinal "
                    f"@{ordinal}: {old_name} und {name}"
                )

            old_ordinal = name_to_ordinal.get(
                name
            )

            if (
                old_ordinal is not None
                and old_ordinal != ordinal
            ):
                raise RuntimeError(
                    f"DLL exportiert {name} unter mehreren "
                    f"Ordinalen: @{old_ordinal} und @{ordinal}"
                )

            ordinal_to_name[ordinal] = name
            name_to_ordinal[name] = ordinal

    if not ordinal_to_rva:
        raise RuntimeError(
            "Keine Export Address Table in der DLL gefunden"
        )

    return ExportTable(
        ordinal_to_rva=ordinal_to_rva,
        ordinal_to_name=ordinal_to_name,
        name_to_ordinal=name_to_ordinal
    )


def verify_exports(
    dll_file: Path,
    expected: ExpectedExports,
    actual: ExportTable,
    strict_extra: bool
) -> int:
    failed = False
    named_count = 0
    noname_count = 0

    expected_by_ordinal = {
        ordinal: symbol
        for symbol, ordinal
        in expected.symbol_to_ordinal.items()
    }

    for symbol, ordinal in sorted(
        expected.symbol_to_ordinal.items(),
        key=lambda item: (
            item[1],
            item[0].lower()
        )
    ):
        rva = actual.ordinal_to_rva.get(
            ordinal
        )

        if rva is None:
            failed = True
            print(
                f"FEHLT: {symbol} @{ordinal} "
                f"besitzt keinen Exportslot"
            )
            continue

        if rva == 0:
            failed = True
            print(
                f"FEHLT: {symbol} @{ordinal} "
                f"besitzt eine RVA von 0"
            )
            continue

        actual_name = actual.ordinal_to_name.get(
            ordinal
        )

        actual_symbol_ordinal = actual.name_to_ordinal.get(
            symbol
        )

        if (
            actual_symbol_ordinal is not None
            and actual_symbol_ordinal != ordinal
        ):
            failed = True
            print(
                f"FALSCH: {symbol} liegt in der DLL bei "
                f"@{actual_symbol_ordinal}, erwartet @{ordinal}"
            )
            continue

        if actual_name is None:
            noname_count += 1
            continue

        named_count += 1

        if actual_name != symbol:
            # Ein fremder Name auf demselben Slot ist ein eindeutiger
            # ABI-Fehler. Bei NONAME gäbe es hier keinen Namenseintrag.
            failed = True
            print(
                f"FALSCH: Ordinal @{ordinal} heißt in der DLL "
                f"{actual_name}, erwartet {symbol}"
            )

    # Benannte _jit_-Exporte, die nicht in der erwarteten Tabelle stehen,
    # sind fast immer ein versehentlich neu veröffentlichtes ABI-Symbol.
    for name, ordinal in sorted(
        actual.name_to_ordinal.items(),
        key=lambda item: (
            item[1],
            item[0].lower()
        )
    ):
        if name in expected.symbol_to_ordinal:
            continue

        if name.startswith("_jit_"):
            failed = True
            print(
                f"NICHT IM MANIFEST: {name} @{ordinal}"
            )
            continue

        message = (
            f"zusätzlicher benannter Export: "
            f"{name} @{ordinal}"
        )

        if strict_extra:
            failed = True
            print(
                f"FEHLER: {message}"
            )
        else:
            print(
                f"WARNUNG: {message}"
            )

    # Nicht im Manifest enthaltene NONAME-Slots können keinem Symbolnamen
    # zugeordnet werden. Sie werden deshalb über die Ordinalnummer gemeldet.
    unexpected_noname = []

    for ordinal, rva in sorted(
        actual.ordinal_to_rva.items()
    ):
        if ordinal in expected_by_ordinal:
            continue

        if ordinal in actual.ordinal_to_name:
            continue

        if rva == 0:
            continue

        unexpected_noname.append(
            ordinal
        )

    for ordinal in unexpected_noname:
        message = (
            f"zusätzlicher NONAME-Export @{ordinal}"
        )

        if strict_extra:
            failed = True
            print(
                f"FEHLER: {message}"
            )
        else:
            print(
                f"WARNUNG: {message}"
            )

    if failed:
        print(
            "Exportprüfung fehlgeschlagen."
        )
        return 1

    print(
        "Exportprüfung erfolgreich:"
    )
    print(
        f"  DLL              : {dll_file}"
    )
    print(
        f"  erwartete Symbole: "
        f"{len(expected.symbol_to_ordinal)}"
    )
    print(
        f"  benannte Exporte : {named_count}"
    )
    print(
        f"  NONAME-Exporte   : {noname_count}"
    )

    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prüft die Exporte und Ordinalnummern einer "
            "PE32-DLL gegen eine erzeugte Ordinaltabelle."
        )
    )

    parser.add_argument(
        "dll",
        type=Path,
        help="Zu prüfende DLL"
    )

    parser.add_argument(
        "manifest",
        type=Path,
        help=(
            "Erzeugtes Python-Modul "
            "libdbase2many32_ordinals.py "
            "oder JSON-Manifest"
        )
    )

    parser.add_argument(
        "--objdump",
        default="objdump",
        help="Pfad oder Name des GNU-objdump-Programms"
    )

    parser.add_argument(
        "--strict-extra",
        action="store_true",
        help=(
            "Auch zusätzliche Nicht-_jit_- und "
            "NONAME-Exporte als Fehler behandeln"
        )
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    dll_file = args.dll.resolve()
    manifest_file = args.manifest.resolve()

    try:
        if not dll_file.is_file():
            raise FileNotFoundError(
                f"DLL nicht gefunden: {dll_file}"
            )

        if not manifest_file.is_file():
            raise FileNotFoundError(
                f"Ordinaltabelle nicht gefunden: "
                f"{manifest_file}"
            )

        expected = load_expected_exports(
            manifest_file,
            dll_file
        )

        if (
            normalize_dll_name(expected.dll_name)
            != normalize_dll_name(dll_file.name)
        ):
            raise RuntimeError(
                f"Die Ordinaltabelle gehört zu "
                f"{expected.dll_name}, geprüft wird aber "
                f"{dll_file.name}"
            )

        output = run_objdump(
            dll_file,
            args.objdump
        )

        actual = parse_objdump_exports(
            output
        )

        return verify_exports(
            dll_file,
            expected,
            actual,
            args.strict_extra
        )

    except Exception as exc:
        print(
            f"Fehler: {exc}",
            file=sys.stderr
        )

        return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

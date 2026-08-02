"""Erzeugt die Python-Zieldateien aus den beiden ANTLR-Grammatiken."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "antlr_jar",
        type=Path,
        help="Pfad zu antlr-4.13.2-complete.jar",
    )
    args = parser.parse_args()

    package = Path(__file__).resolve().parent
    grammar = package / "grammar"
    generated = package / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    common = [
        "java",
        "-jar",
        str(args.antlr_jar.resolve()),
        "-Dlanguage=Python3",
        "-Xexact-output-dir",
    ]
    subprocess.run(
        common
        + [
            "-o",
            str(generated),
            str(grammar / "C64PascalLexer.g4"),
        ],
        check=True,
    )
    subprocess.run(
        common
        + [
            "-visitor",
            "-no-listener",
            "-lib",
            str(generated),
            "-o",
            str(generated),
            str(grammar / "C64PascalParser.g4"),
        ],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


from __future__ import annotations

import argparse
from pathlib import Path

from .compiler import LogoCompilerError, compile_logo_to_assembly


def main() -> int:
    parser = argparse.ArgumentParser(description="dBase2Many LOGO -> Windows PE32 Assembler")
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--mode", choices=("console", "gui"), default="console")
    args = parser.parse_args()

    try:
        text = args.source.read_text(encoding="utf-8")
        generated = compile_logo_to_assembly(
            text,
            filename=str(args.source),
            target="pe32",
            windows_application_mode=args.mode,
        )
    except (OSError, UnicodeError, LogoCompilerError) as exc:
        print(exc)
        return 1

    output = args.output or args.source.with_name(args.source.stem + ".generated.pe32.asm")
    output.write_text(generated.assembly, encoding="utf-8", newline="\n")
    for note in generated.notes:
        print("Hinweis:", note)
    for warning in generated.warnings:
        print("Warnung:", warning)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

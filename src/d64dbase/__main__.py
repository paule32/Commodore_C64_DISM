from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import (
    DBaseCompilerError,
    compile_dbase_to_assembly,
    preprocess_dbase_file,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="dBase-Compiler: Variablen, ?/??, SET DEBUG ON/OFF, eingebettete stdout/stderr-Ausgabe / Windows PE32 + PE32+"
    )
    parser.add_argument("source", help="dBase-Quelldatei")
    parser.add_argument(
        "--target",
        default="pe32",
        choices=("pe32", "pe64"),
        help="Ziel: pe32 oder pe64 (= Windows PE32+/AMD64)",
    )
    parser.add_argument(
        "--list-comments",
        action="store_true",
        help="erkannte Kommentare mit Position ausgeben",
    )
    parser.add_argument(
        "--emit-asm",
        action="store_true",
        help="nativen PE32/PE32+-Assembler fuer das dBase-Programm ausgeben",
    )
    args = parser.parse_args(argv)

    try:
        source_path = Path(args.source)
        result = preprocess_dbase_file(source_path, target=args.target)
        if args.emit_asm:
            generated = compile_dbase_to_assembly(
                result.source,
                filename=str(source_path),
                target=args.target,
            )
            sys.stdout.write(generated.assembly)
        elif args.list_comments:
            for comment in result.comments:
                print(
                    f"{comment.kind:5} {comment.marker:2} "
                    f"{comment.start_line}:{comment.start_column}-"
                    f"{comment.end_line}:{comment.end_column}"
                )
        else:
            sys.stdout.write(result.comment_free_source)
    except (OSError, UnicodeError, DBaseCompilerError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path

try:
    from .compiler import compile_pascal_to_assembly
except ImportError:
    from compiler import compile_pascal_to_assembly


def main() -> int:
    root = Path(__file__).resolve().parent
    source_path = root / "units" / "System" / "SysUtils.pas"
    source = source_path.read_text(encoding="utf-8")

    generated = compile_pascal_to_assembly(
        source,
        filename=str(source_path),
        include_paths=(root / "units", root / "units" / "System"),
        target="pe32",
    )

    asm = generated.assembly
    assert generated.source_kind == "unit", generated.source_kind
    assert generated.unit_name == "System.SysUtils", generated.unit_name
    assert "global __pas_method_exception_create" in asm
    assert "call __pas_method_tobject_create" in asm
    assert "call __pas_method_exception_create" not in "\n".join(
        line for line in asm.splitlines()
        if "call __pas_method_tobject_create" in line
    )
    print("System.SysUtils PE32: OK")
    print("inherited TObject.Create: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

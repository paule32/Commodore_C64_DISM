from pathlib import Path

try:
    from .compiler import compile_pascal_to_assembly
except ImportError:
    from compiler import compile_pascal_to_assembly


def main() -> int:
    root = Path(__file__).resolve().parent
    source_path = root / "units" / "System" / "Strings.pas"
    source = source_path.read_text(encoding="utf-8")

    generated = compile_pascal_to_assembly(
        source,
        filename=str(source_path),
        include_paths=(root / "units", root / "units" / "System"),
        target="pe32",
    )

    asm = generated.assembly
    assert generated.source_kind == "unit"
    assert generated.unit_name == "System.Strings"
    assert "global __pas_System_Strings_IntToStr" in asm
    assert "global __pas_System_Strings_StrToInt" in asm
    assert "call __IntToStr" in asm
    assert "call __StrToInt" in asm
    assert 'import _jit_dynstring_from_cstr, "libruntime_mini.dll", "jit_dynstring_from_cstr"' in asm
    assert tuple(Path(x).name for x in generated.linked_object_files) == (
        "inttostr.o",
        "strtoint.o",
    )
    print("System.Strings PE32: OK")
    print("{$L}: inttostr.o + strtoint.o: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

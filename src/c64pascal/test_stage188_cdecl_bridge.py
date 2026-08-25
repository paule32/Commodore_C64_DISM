from pathlib import Path
import re

try:
    from .compiler import (
        PascalPreprocessor,
        _legacy_pascal_extension_bridge,
        _pui_routine_information,
        _unit_program_source,
    )
except ImportError:
    from compiler import (
        PascalPreprocessor,
        _legacy_pascal_extension_bridge,
        _pui_routine_information,
        _unit_program_source,
    )


def main() -> int:
    interface = (
        "function Foo(A: Integer): Integer; cdecl;\n"
        "procedure Ext(S: String); cdecl; external;\n"
        "function Later: Integer; forward;\n"
    )
    parser_source, routines = _pui_routine_information("Test.Unit", interface)
    assert re.search(r"(?i)\\bcdecl\\b", parser_source) is None
    assert re.search(r"(?i)\\bexternal\\b", parser_source) is None
    assert re.search(r"(?i)\\bforward\\b", parser_source) is None
    assert [item["name"] for item in routines] == ["Foo", "Ext", "Later"]
    assert routines[0]["calling_convention"] == "cdecl"

    source = (
        "program P;\n"
        "function Local(A: Integer): Integer;\n"
        "begin\n"
        " result := A;\n"
        "end;\n"
        "function Ext(A: Integer): Integer; cdecl; external;\n"
        "begin\n"
        "end.\n"
    )
    bridged, _types, externals, _props, _inherited, globals_ = (
        _legacy_pascal_extension_bridge(source)
    )
    assert re.search(r"(?i)\\bcdecl\\b", bridged) is None
    assert re.search(r"(?i)\\bexternal\\b", bridged) is None
    assert [(item.name, item.symbol) for item in externals] == [("Ext", "_Ext")]
    assert globals_ == (("function", "Local", 2),)

    root = Path(__file__).resolve().parent
    strings_path = root / "units" / "System" / "Strings.pas"
    strings_source = strings_path.read_text(encoding="utf-8")
    processed = PascalPreprocessor().process(
        strings_source,
        filename=str(strings_path),
    )
    transformed, _unit_name, *_rest = _unit_program_source(
        processed.source,
        filename=str(strings_path),
    )
    bridged, _types, externals, _props, _inherited, globals_ = (
        _legacy_pascal_extension_bridge(transformed)
    )
    assert re.search(r"(?i)\\bcdecl\\b", bridged) is None
    assert [item.name for item in externals] == [
        "jit_dynstring_from_cstr",
        "_IntToStr",
        "_StrToInt",
    ]
    assert [item[1] for item in globals_] == ["IntToStr", "StrToInt"]
    print("Stage188 cdecl/PUI/legacy bridge: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

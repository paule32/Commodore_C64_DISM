from __future__ import annotations

import json
import tempfile
from pathlib import Path

try:
    from .compiler import write_pascal_unit_interface
except ImportError:
    from compiler import write_pascal_unit_interface


FORBIDDEN_KEYS = {
    "source",
    "interface_source",
    "declaration_source",
    "parser_source",
    "source_text",
}


def assert_no_source_payload(value) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key).casefold() not in FORBIDDEN_KEYS, key
            assert_no_source_payload(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_source_payload(child)


def main() -> int:
    root = Path(__file__).resolve().parent
    source = root / "units" / "System" / "Objects.pas"
    with tempfile.TemporaryDirectory(prefix="d64-pui-stage186-") as directory:
        destination = Path(directory) / "System.Objects.pui"
        write_pascal_unit_interface(
            source,
            destination,
            target="pe32",
            include_paths=(root / "units", root / "units" / "System"),
        )
        document = json.loads(destination.read_text(encoding="utf-8"))
        assert document["format"] == "dBase2Many Pascal Unit Interface"
        assert document["version"] == 1
        assert document["unit"]["name"] == "System.Objects"
        assert document["target"]["object_format"] == "coff32"
        assert document["object"]["file"] == "System.Objects.coff32.o"
        assert_no_source_payload(document)
        serialized = destination.read_text(encoding="utf-8")
        assert "unit System.Objects" not in serialized
        assert "constructor Create;" not in serialized
        classes = document["symbols"]["classes"]
        assert any(item.get("name") == "TObject" for item in classes)
        tobject = next(item for item in classes if item.get("name") == "TObject")
        assert any(method.get("name") == "Create" for method in tobject["methods"])
        assert document["macros"] == {}
    print("Stage186 metadata-only PUI: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

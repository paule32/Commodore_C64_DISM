"""Stage-177 regression test for System.Types/System.Objects.

Run after regenerating the ANTLR files with 4.13.2, from the package parent:
    py -m c64pascal.test_stage177_system_units
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from .compiler import compile_pascal_to_assembly


def _compile(source: Path, target: str = "pe32"):
    with tempfile.TemporaryDirectory(prefix="d64pas_stage177_") as temp_name:
        temp = Path(temp_name)
        local = temp / source.name
        local.write_bytes(source.read_bytes())
        result = compile_pascal_to_assembly(
            local.read_text(encoding="utf-8-sig"),
            filename=str(local),
            target=target,
        )
        pui = Path(result.pui_path) if result.pui_path else None
        pui_exists = bool(pui and pui.is_file())
        return result, pui_exists


def main() -> int:
    package = Path(__file__).resolve().parent
    types_source = package / "units" / "System" / "Types.pas"
    objects_source = package / "units" / "System" / "Objects.pas"

    types_result, types_pui = _compile(types_source)
    assert types_result.source_kind == "unit"
    assert types_result.unit_name == "System.Types"
    assert types_pui
    assert "bits 32" in types_result.assembly
    assert "global __unit_System_Types" in types_result.assembly
    assert "global _start" not in types_result.assembly

    objects_result, objects_pui = _compile(objects_source)
    assert objects_result.source_kind == "unit"
    assert objects_result.unit_name == "System.Objects"
    assert objects_pui
    assert "bits 32" in objects_result.assembly
    assert "global __unit_System_Objects" in objects_result.assembly
    assert "global _start" not in objects_result.assembly

    for symbol in (
        "_jit_object_instance_new",
        "_jit_object_instance_free",
        "_jit_object_free",
        "_jit_object_class_type",
        "_jit_class_parent",
        "_jit_class_name",
        "_jit_class_instance_size",
        "_jit_inherits_from_class",
        "_jit_inherits_from_object",
        "_jit_dynstring_from_cstr",
    ):
        assert f"extern {symbol}" in objects_result.assembly, symbol

    for method in (
        "create", "destroy", "free", "freeinstance", "classtype",
        "classparent", "classnameaddress", "classname", "instancesize",
        "inheritsfrom",
    ):
        assert f"global __pas_method_tobject_{method}" in objects_result.assembly

    print("Stage177 System.Types PE32 UNIT: OK")
    print("Stage177 System.Objects PE32 UNIT: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import unittest
from pathlib import Path

from c64pascal import C64PascalError, compile_pascal_to_assembly


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "c64pascal" / "oop_records_sets_arrays_classes.pas"


class PascalOOPTypeTests(unittest.TestCase):
    def _source(self) -> str:
        return EXAMPLE.read_text(encoding="utf-8")

    def test_oop_example_compiles_for_c64(self) -> None:
        generated = compile_pascal_to_assembly(self._source(), filename=EXAMPLE.name)
        self.assertIn("__pas_vmt_tshape:", generated.assembly)
        self.assertIn("__pas_vmt_tmovingshape:", generated.assembly)
        self.assertIn(".word __pas_method_tmovingshape_show", generated.assembly)
        self.assertIn("__pas_virtual_call:", generated.assembly)

    def test_oop_example_compiles_for_pe32(self) -> None:
        generated = compile_pascal_to_assembly(
            self._source(),
            filename=EXAMPLE.name,
            target="pe32",
            windows_application_mode="Console",
        )
        self.assertIn("__pas_vmt_tshape:", generated.assembly)
        self.assertIn("__pas_vmt_tmovingshape:", generated.assembly)
        self.assertIn("dd __pas_method_tmovingshape_show", generated.assembly)
        self.assertIn("call dword ptr [ecx+", generated.assembly)

    def test_oop_example_compiles_for_amiga(self) -> None:
        generated = compile_pascal_to_assembly(
            self._source(),
            filename=EXAMPLE.name,
            target="amiga",
        )
        self.assertIn("__pas_vmt_tshape:", generated.assembly)
        self.assertIn("__pas_vmt_tmovingshape:", generated.assembly)
        self.assertIn("dc.l __pas_method_tmovingshape_show", generated.assembly)
        self.assertIn("jsr (a0)", generated.assembly)

    def test_private_field_is_not_visible_outside_class(self) -> None:
        source = """program PrivateAccess;
type
  TBase = class
  private
    FValue: Integer;
  public
    procedure Run;
  end;
var Obj: TBase;
procedure TBase.Run;
begin
  FValue := 1;
end;
begin
  Obj.FValue := 2;
end.
"""
        with self.assertRaisesRegex(C64PascalError, "PRIVATE-Member"):
            compile_pascal_to_assembly(source)

    def test_protected_field_is_visible_in_descendant(self) -> None:
        source = """program ProtectedAccess;
type
  TBase = class
  protected
    FValue: Integer;
  public
    procedure Run;
  end;
  TChild = class(TBase)
  public
    procedure RunChild;
  end;
var Obj: TChild;
procedure TBase.Run;
begin
  FValue := 1;
end;
procedure TChild.RunChild;
begin
  FValue := FValue + 1;
end;
begin
  Obj.RunChild;
end.
"""
        generated = compile_pascal_to_assembly(source)
        self.assertIn("__pas_method_tchild_runchild:", generated.assembly)

    def test_override_requires_virtual_base_method(self) -> None:
        source = """program BadOverride;
type
  TBase = class
  public
    procedure Show;
  end;
  TChild = class(TBase)
  public
    procedure Show; override;
  end;
var Obj: TChild;
procedure TBase.Show;
begin
end;
procedure TChild.Show;
begin
end;
begin
end.
"""
        with self.assertRaisesRegex(C64PascalError, "OVERRIDE"):
            compile_pascal_to_assembly(source)


if __name__ == "__main__":
    unittest.main()

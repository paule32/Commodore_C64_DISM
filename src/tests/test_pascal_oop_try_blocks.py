from __future__ import annotations

import unittest

from c64pascal import C64PascalError, compile_pascal_to_assembly


SOURCE = r"""program Unbenannt;

type
    TObject = class
    public
        constructor Create;
        destructor Destroy;
    end;

constructor TObject.Create;
begin
    WriteLn('TObject: Create');
end;

destructor TObject.Destroy;
begin
    WriteLn('TObject: Destroy');
end;

var
    obj: TObject;

begin
    WriteLn('Test Application');
    obj := TObject.Create;
    try
        WriteLn('in finally');
    finally
        obj.Free;
    end;
    ReadLn;
end.
"""


class PascalOOPTryTests(unittest.TestCase):
    def test_exact_program_compiles_for_pe32(self) -> None:
        generated = compile_pascal_to_assembly(
            SOURCE,
            target="pe32",
            windows_application_mode="Console",
        )
        asm = generated.assembly.lower()
        self.assertIn("call __pas_new_object", asm)
        self.assertIn("call heapalloc", asm)
        self.assertIn("call __pas_method_tobject_create", asm)
        self.assertIn("call __pas_method_tobject_destroy", asm)
        self.assertIn("call __pas_free_object", asm)
        self.assertIn("call heapfree", asm)
        self.assertIn("call __pas_readln", asm)
        self.assertLess(
            asm.index("call __pas_method_tobject_create"),
            asm.index("call __pas_method_tobject_destroy"),
        )
        self.assertLess(
            asm.index("call __pas_method_tobject_destroy"),
            asm.index("call __pas_readln"),
        )

    def test_late_global_var_after_method_implementations_is_supported(self) -> None:
        generated = compile_pascal_to_assembly(
            SOURCE,
            target="pe32",
            windows_application_mode="Console",
        )
        self.assertIn("__pas_var_obj_", generated.assembly.lower())

    def test_try_except_syntax_is_supported(self) -> None:
        source = r"""program TryExceptDemo;
begin
    try
        WriteLn('try');
    except
        WriteLn('except');
    end;
    ReadLn;
end.
"""
        generated = compile_pascal_to_assembly(
            source,
            target="pe32",
            windows_application_mode="Console",
        )
        asm = generated.assembly.lower()
        self.assertIn("try_except_handler", asm)
        self.assertIn("try_except_end", asm)

    def test_derived_constructor_can_be_assigned_to_base_reference(self) -> None:
        source = r"""program PolymorphicCtor;
type
  TBase = class
  public
    constructor Create;
    procedure Show; virtual;
  end;
  TChild = class(TBase)
  public
    procedure Show; override;
  end;
constructor TBase.Create;
begin
end;
procedure TBase.Show;
begin
end;
procedure TChild.Show;
begin
end;
var Obj: TBase;
begin
  Obj := TChild.Create;
  Obj.Show;
  Obj.Free;
end.
"""
        generated = compile_pascal_to_assembly(
            source,
            target="pe32",
            windows_application_mode="Console",
        )
        asm = generated.assembly.lower()
        self.assertIn("mov edx, __pas_vmt_tchild", asm)
        self.assertIn("call __pas_new_object", asm)
        self.assertIn("call dword ptr [ecx+", asm)

    def test_base_constructor_cannot_be_assigned_to_child_reference(self) -> None:
        source = r"""program BadCtorTarget;
type
  TBase = class
  public
    constructor Create;
  end;
  TChild = class(TBase)
  end;
constructor TBase.Create;
begin
end;
var Obj: TChild;
begin
  Obj := TBase.Create;
end.
"""
        with self.assertRaisesRegex(C64PascalError, "kann nicht an"):
            compile_pascal_to_assembly(
                source,
                target="pe32",
                windows_application_mode="Console",
            )


if __name__ == "__main__":
    unittest.main()

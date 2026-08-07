from __future__ import annotations

import unittest

from c64pascal import compile_pascal_to_assembly


class PascalHeapExceptionTests(unittest.TestCase):
    def compile(self, source: str):
        return compile_pascal_to_assembly(
            source,
            target="pe32",
            windows_application_mode="Console",
        )

    def test_class_variable_is_heap_reference_and_free_sets_nil(self) -> None:
        source = r"""program HeapObject;
type
  TObject = class
  public
    constructor Create;
    destructor Destroy;
  end;
constructor TObject.Create;
begin
end;
destructor TObject.Destroy;
begin
end;
var Obj: TObject;
begin
  Obj := TObject.Create;
  Obj.Free;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("class reference (nil)", asm)
        self.assertIn("call __pas_new_object", asm)
        self.assertIn("call heapalloc", asm)
        self.assertIn("call __pas_method_tobject_destroy", asm)
        self.assertIn("call __pas_free_object", asm)
        self.assertIn("call heapfree", asm)

    def test_nil_assignment_and_free_nil_are_supported(self) -> None:
        source = r"""program NilReference;
type
  TObject = class
  end;
var Obj: TObject;
begin
  Obj := nil;
  Obj.Free;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("xor eax, eax", asm)
        self.assertIn("free_done", asm)

    def test_nested_raise_runs_finally_then_outer_except(self) -> None:
        source = r"""program NestedException;
begin
  try
    try
      WriteLn('before');
      raise Exception.Create('boom');
    finally
      WriteLn('cleanup');
    end;
  except
    WriteLn(ExceptionMessage());
  end;
  ReadLn;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("call __pas_raise", asm)
        self.assertIn("try_finally_unwind", asm)
        self.assertIn("jmp __pas_reraise", asm)
        self.assertIn("try_except_handler", asm)
        self.assertIn("__pas_exception_unwind", asm)
        self.assertIn("__pas_exception_message", asm)

    def test_raise_from_method_unwinds_to_caller_except(self) -> None:
        source = r"""program MethodException;
type
  TWorker = class
  public
    constructor Create;
    procedure Fail;
  end;
constructor TWorker.Create;
begin
end;
procedure TWorker.Fail;
begin
  raise Exception.Create('worker failed');
end;
var Worker: TWorker;
begin
  Worker := TWorker.Create;
  try
    Worker.Fail;
  except
    WriteLn(ExceptionMessage());
  end;
  Worker.Free;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("__pas_method_tworker_fail", asm)
        self.assertIn("call __pas_raise", asm)
        self.assertIn("mov ebp, dword ptr [ecx+8]", asm)
        self.assertIn("lea esp, [ecx+24]", asm)
        self.assertIn("jmp edx", asm)

    def test_reraise_is_supported(self) -> None:
        source = r"""program ReraiseDemo;
begin
  try
    try
      raise 'first';
    except
      raise;
    end;
  except
    WriteLn(ExceptionMessage());
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("jmp __pas_reraise", asm)
        self.assertGreaterEqual(asm.count("try_except_handler"), 2)

    def test_break_leaving_try_has_frame_cleanup_trampoline(self) -> None:
        source = r"""program BreakTry;
var I: Integer;
begin
  I := 0;
  while I < 10 do
  begin
    try
      break;
    finally
      WriteLn('finally');
    end;
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("try_break_cleanup", asm)
        self.assertIn("add esp, 24", asm)


if __name__ == "__main__":
    unittest.main()

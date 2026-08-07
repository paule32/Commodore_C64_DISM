from __future__ import annotations

import unittest

from c64pascal import compile_pascal_to_assembly


class PascalExceptionClassTests(unittest.TestCase):
    def compile(self, source: str):
        return compile_pascal_to_assembly(
            source,
            target="pe32",
            windows_application_mode="Console",
        )

    def test_custom_exception_handler_binds_object_and_reads_message(self) -> None:
        source = r"""program TypedExcept;
type
  EMyException = class(Exception)
  end;
begin
  try
    raise EMyException.Create('boom');
  except
    on E: EMyException do
    begin
      WriteLn(E.Message);
    end;
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("__pas_exception_object", asm)
        self.assertIn("__pas_exception_is_a", asm)
        self.assertIn("__pas_vmt_emyexception__parent: dd __pas_vmt_exception", asm)
        self.assertIn("call __pas_raise_object", asm)
        self.assertIn("call __pas_exception_release", asm)

    def test_base_exception_handler_catches_derived_exception(self) -> None:
        source = r"""program BaseHandler;
type
  EBase = class(Exception)
  end;
  EChild = class(EBase)
  end;
begin
  try
    raise EChild.Create('child');
  except
    on E: Exception do
      WriteLn(E.Message);
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("__pas_vmt_echild__parent: dd __pas_vmt_ebase", asm)
        self.assertIn("__pas_vmt_ebase__parent: dd __pas_vmt_exception", asm)
        self.assertIn("mov ecx, dword ptr [ecx-4]", asm)

    def test_multiple_on_handlers_are_emitted_in_order(self) -> None:
        source = r"""program MultiHandler;
type
  EOne = class(Exception)
  end;
  ETwo = class(Exception)
  end;
begin
  try
    raise ETwo.Create('two');
  except
    on E: EOne do WriteLn('one');
    on E: ETwo do WriteLn(E.Message);
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertGreaterEqual(asm.count("except_next"), 2)
        self.assertIn("mov edx, __pas_vmt_eone", asm)
        self.assertIn("mov edx, __pas_vmt_etwo", asm)

    def test_unmatched_typed_handler_reraises(self) -> None:
        source = r"""program ReRaiseNoMatch;
type
  EOne = class(Exception)
  end;
  ETwo = class(Exception)
  end;
begin
  try
    try
      raise ETwo.Create('two');
    except
      on E: EOne do WriteLn('wrong');
    end;
  except
    on E: Exception do WriteLn(E.Message);
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("jmp __pas_reraise", asm)

    def test_raise_semicolon_preserves_same_exception_object(self) -> None:
        source = r"""program TypedReraise;
type
  EMyException = class(Exception)
  end;
begin
  try
    try
      raise EMyException.Create('boom');
    except
      on E: EMyException do
      begin
        WriteLn(E.Message);
        raise;
      end;
    end;
  except
    on E: Exception do WriteLn(E.Message);
  end;
end.
"""
        asm = self.compile(source).assembly.lower()
        self.assertIn("call __pas_reraise", asm)
        self.assertIn("__pas_exception_object", asm)


if __name__ == "__main__":
    unittest.main()

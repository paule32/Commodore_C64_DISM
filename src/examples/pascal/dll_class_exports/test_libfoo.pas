program test_libfoo;

{$L libfoo}
uses System, UFoo;

var
  Foo: TFoo;
begin
  Foo := TFoo.Create(42);
  try
    WriteLn(Foo.Value);
    Foo.Value := 100;
    WriteLn(Foo.GetValue);
  finally
    Foo.Free;
  end;
end.

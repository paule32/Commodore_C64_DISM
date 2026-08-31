// ---------------------------------------------------------------------------
// File:   test_raise.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
program test_raise;

{$L inttostr.o}
{$L strtoint.o}

uses System, Windows;

type
    TFaz = class(TObject)
    public
        constructor Create;
        destructor Destroy; override;
        
        procedure Show; virtual;
    end;
type
    TFoo = class(TFaz)
    private
        FValue: Integer;
        FString: String;
        FDouble: Double;
        FName: String;
    public
        constructor Create(AValue: Integer);
        destructor Destroy; override;
        
        procedure Show; override;
    published
        property OnTest: String read FString write FString;
        property OnTest2: Double read FDouble write FDouble;
        property OnTest3: String read FName write FName;
    end;

constructor TFaz.Create;
begin
    inherited Create;
    WriteLn('TFaz Create');
end;
procedure TFaz.Show;
begin
    WriteLn('TFaz Show', '');
    WriteLn('  Runtime class: ', ClassName);
    WriteLn('  Method  owner: ', OwnerClassName);
    WriteLn('  Size         : ', IntToStr(InstanceSize));
end;
destructor TFaz.Destroy;
begin
    WriteLn('TFaz Destroy','');
    inherited Destroy;
end;

constructor TFoo.Create(AValue: Integer);
begin
    inherited Create;
    FValue := AValue;

    FString := 'Hello';
    FDouble := 3.21;

    FName   := 'World !';
end;

destructor TFoo.Destroy;
begin
    WriteLn('TFoo Destroy','');
    inherited Destroy;
end;

procedure TFoo.Show;
begin
    WriteLn('TFoo Show','');
    WriteLn('  Runtime class: ', ClassName);
    WriteLn('  Method  owner: ', OwnerClassName );
    WriteLn('  Size         : ', IntToStr(self.InstanceSize));
    inherited Show;
end;

var
    Foo: TFoo;
    Application: TApplication;
begin
    Foo := TFoo.Create(42);
    try
        Foo.Show;
    finally
        Foo.Free;
    end;
    
    Application := TApplication.Create;
    Application.Free;
    
    ExitProcess(0)
end.

(*
begin
writeln('start');
    try
        WriteLn('before raise');
        raise Exception.Create('fuzz');
        WriteLn('unreachable');
    except
        WriteLn('exception caught');
    end;

    WriteLn('after except');
    ReadLn;
    ExitProcess(0);
end.
*)

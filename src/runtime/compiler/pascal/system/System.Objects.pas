// ---------------------------------------------------------------------------
// File:   System.Objects.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit System.Objects;

interface

type
    TClass  = Pointer;

    TObject = class
    public
        constructor Create;
        destructor Destroy; virtual;

        procedure Free;
        procedure FreeInstance;

        function ClassType: TClass;
        function ClassParent: TClass;
        function ClassNameAddress: Pointer;
        function ClassName: String;
        
        function InstanceSize: Integer;
        function InheritsFrom(AClass: TClass): Boolean;
    end;

implementation

function  jit_object_instance_new (AVmt:    Pointer): Pointer; cdecl; external;
procedure jit_object_instance_free(AObject: Pointer);          cdecl; external;
procedure jit_object_free         (AObject: Pointer);          cdecl; external;
function  jit_object_class_type   (AObject: Pointer): Pointer; cdecl; external;

function  jit_class_parent        (AVmt:    Pointer): Pointer; cdecl; external;
function  jit_class_name          (AVmt:    Pointer): Pointer; cdecl; external;
function  jit_class_instance_size (AVmt:    Pointer): Integer; cdecl; external;

function  jit_inherits_from_class (ACurrentClass: Pointer; AExpectedClass: Pointer): Integer; cdecl; external;
function  jit_inherits_from_object(AObject:       Pointer; AExpectedClass: Pointer): Boolean; cdecl; external;

function  jit_dynstring_from_cstr(AText: Pointer): String; cdecl; external;

constructor TObject.Create;
begin
end;

destructor TObject.Destroy;
begin
end;

procedure TObject.Free;
begin
    if Self <> nil then
        jit_object_free(Pointer(Self));
end;

procedure TObject.FreeInstance;
begin
    if Self <> nil then
        jit_object_instance_free(Pointer(Self));
end;

function TObject.ClassType: TClass;
begin
    Result := jit_object_class_type(Pointer(Self));
end;

function TObject.ClassParent: TClass;
begin
    Result := jit_class_parent(
        jit_object_class_type(Pointer(Self))
    );
end;

function TObject.ClassNameAddress: Pointer;
begin
    Result := jit_class_name(
        jit_object_class_type(Pointer(Self))
    );
end;

function TObject.ClassName: String;
begin
    result := jit_dynstring_from_cstr(ClassNameAddress);
end;

function TObject.InstanceSize: Integer;
begin
    Result := jit_class_instance_size(
        jit_object_class_type(Pointer(Self))
    );
end;

function TObject.InheritsFrom(
    AClass: TClass
): Boolean;
begin
    Result := (jit_inherits_from_object(Pointer(Self), AClass ) <> 0);
end;

end.

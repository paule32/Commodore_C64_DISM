// ---------------------------------------------------------------------------
// File: System.Objects.prg
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved.
// Stage 602: method bodies are real dBASE; native calls are declared below.
// ---------------------------------------------------------------------------
#ifndef RUNTIME_DLL
#define RUNTIME_DLL "libd64_qt5.dll"
#else
#undef RUNTIME_DLL
#define RUNTIME_DLL "libd64_qt5.dll"
#endif

extern PVOID jit_object_instance_new (PVOID); cdecl; RUNTIME_DLL; from "jit_object_instance_new"
extern       jit_object_instance_free(PVOID); cdecl; RUNTIME_DLL; from "jit_object_instance_free"
extern       jit_object_free         (PVOID); cdecl; RUNTIME_DLL; from "jit_object_free"
extern PVOID jit_object_class_type   (PVOID); cdecl; RUNTIME_DLL; from "jit_object_class_type"
extern PVOID jit_class_parent        (PVOID); cdecl; RUNTIME_DLL; from "jit_class_parent"
extern PVOID jit_class_name          (PVOID); cdecl; RUNTIME_DLL; from "jit_class_name"
extern CINT  jit_class_instance_size (PVOID); cdecl; RUNTIME_DLL; from "jit_class_instance_size"
extern CINT  jit_inherits_from_class (PVOID, PVOID); cdecl; RUNTIME_DLL; from "jit_inherits_from_class"
extern CBOOL jit_inherits_from_object(PVOID, PVOID); cdecl; RUNTIME_DLL; from "jit_inherits_from_object"
// Note: jit_dynstring_from_cstr returns a PASCAL dynstring, not a dBASE string.
// ClassName returns the native const char*; the dBASE call site makes a copy.

CLASS TObject OF CUSTOM

    procedure __ini__
        return

    procedure __del__
        return

    procedure Free
        if Self <> NULL
            jit_object_free(Self)
        endif
        return

    procedure FreeInstance
        if Self <> NULL
            jit_object_instance_free(Self)
        endif
        return

    function ClassType
        return jit_object_class_type(Self)

    function ClassParent
        return jit_class_parent(jit_object_class_type(Self))

    function ClassNameAddress
        return jit_class_name(jit_object_class_type(Self))

    function ClassName
        return ClassNameAddress()

    function InstanceSize
        return jit_class_instance_size(jit_object_class_type(Self))

    function InheritsFrom(TClass)
        return jit_inherits_from_object(Self, TClass) <> 0

ENDCLASS

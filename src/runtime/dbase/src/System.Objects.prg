// ---------------------------------------------------------------------------
// File:   System.Objects.prg
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
#ifndef SYSTEM_OBJECTS_PRG
#define SYSTEM_OBJECTS_PRG

#ifndef RUNTIME_DLL
#define RUNTIME_DLL "libd64_runtime.dll"
#else
#undef  RUNTIME_DLL
#define RUNTIME_DLL "libd64_runtime.dll"
#endif

extern PVOID   jit_object_instance_new (PVOID); cdecl; RUNTIME_DLL; from "jit_object_instance_new"
extern         jit_object_instance_free(PVOID); cdecl; RUNTIME_DLL; from "jit_object_instance_free"
extern         jit_object_free         (PVOID); cdecl; RUNTIME_DLL; from "jit_object_free"
extern PVOID   jit_object_class_type   (PVOID); cdecl; RUNTIME_DLL; from "jit_object_class_type"

extern PVOID   jit_class_parent        (PVOID); cdecl; RUNTIME_DLL; from "jit_class_parent"
extern PVOID   jit_class_name          (PVOID); cdecl; RUNTIME_DLL; from "jit_class_name"
extern CINT    jit_class_instance_size (PVOID); cdecl; RUNTIME_DLL; from "jit_class_instance_size"

extern CINT    jit_inherits_from_class (PVOID, PVOID); cdecl; RUNTIME_DLL; from "jit_inherits_from_class"
extern CBOOL   jit_inherits_from_object(PVOID, PVOID); cdecl; RUNTIME_DLL; from "jit_inherits_from_object"

extern LPCSTR  jit_dynstring_from_cstr (PVOID); cdecl; RUNTIME_DLL; from "jit_dynstring_from_cstr"

CLASS TObject of CUSTOM
    procedure __ini__
    return

    procedure __del__
    return

    procedure Free
        if self <> NULL
            jit_object_free(self)
        endif
    return

    procedure FreeInstance
        if self <> NULL
            jit_object_instance_free(self)
        endif
    return

    function ClassType
    return jit_object_class_type(self)

    function ClassParent
    return jit_class_parent(jit_object_class_type(self))

    function ClassNameAddress
    return jit_class_name(jit_object_class_type(self))

    function ClassName
    return ClassNameAddress()
        
    function InstanceSize
    return jit_class_instance_size(jit_object_class_type(self))

    function InheritsFrom(TClass)
    return jit_inherits_from_object(self, TClass) <> 0

ENDCLASS

#endif    // SYSTEM_OBJECTS_PRG

// ---------------------------------------------------------------------------
// File: System.Objects.prg
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved.
// ---------------------------------------------------------------------------
#ifndef SYSTEM_OBJECTS_PRG
#define SYSTEM_OBJECTS_PRG

#include "RuntimeDB"

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
#endif // SYSTEM_OBJECTS_PRG

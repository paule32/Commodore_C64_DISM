; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: System.Objects
bits 32
global __unit_System_Objects
import _jit_object_instance_new, "libruntime_mini.dll", "jit_object_instance_new"
import _jit_object_instance_free, "libruntime_mini.dll", "jit_object_instance_free"
import _jit_object_free, "libruntime_mini.dll", "jit_object_free"
import _jit_object_class_type, "libruntime_mini.dll", "jit_object_class_type"
import _jit_class_parent, "libruntime_mini.dll", "jit_class_parent"
import _jit_class_name, "libruntime_mini.dll", "jit_class_name"
import _jit_class_instance_size, "libruntime_mini.dll", "jit_class_instance_size"
import _jit_inherits_from_class, "libruntime_mini.dll", "jit_inherits_from_class"
import _jit_inherits_from_object, "libruntime_mini.dll", "jit_inherits_from_object"
import _jit_dynstring_from_cstr, "libruntime_mini.dll", "jit_dynstring_from_cstr"
__unit_System_Objects:
    ret

; constructor TObject.Create
global __pas_method_tobject_create
__pas_method_tobject_create:
    push ebp
    mov ebp, esp
    mov esp, ebp
    pop ebp
    ret

; destructor TObject.Destroy
global __pas_method_tobject_destroy
__pas_method_tobject_destroy:
    push ebp
    mov ebp, esp
    mov esp, ebp
    pop ebp
    ret

; procedure TObject.Free
global __pas_method_tobject_free
__pas_method_tobject_free:
    push ebp
    mov ebp, esp
    mov eax, esi
    push eax
    xor eax, eax
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_System_Objects_if_else_1
    mov eax, esi
    push eax
    call _jit_object_free
    add esp, 4
    jmp __pas_unit_System_Objects_if_end_2
__pas_unit_System_Objects_if_else_1:
__pas_unit_System_Objects_if_end_2:
    mov esp, ebp
    pop ebp
    ret

; procedure TObject.FreeInstance
global __pas_method_tobject_freeinstance
__pas_method_tobject_freeinstance:
    push ebp
    mov ebp, esp
    mov eax, esi
    push eax
    xor eax, eax
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_System_Objects_if_else_3
    mov eax, esi
    push eax
    call _jit_object_instance_free
    add esp, 4
    jmp __pas_unit_System_Objects_if_end_4
__pas_unit_System_Objects_if_else_3:
__pas_unit_System_Objects_if_end_4:
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassType
global __pas_method_tobject_classtype
__pas_method_tobject_classtype:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classtype_result_0
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classtype_result_0
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classtype_result_0
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassParent
global __pas_method_tobject_classparent
__pas_method_tobject_classparent:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classparent_result_1
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_parent
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classparent_result_1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classparent_result_1
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassNameAddress
global __pas_method_tobject_classnameaddress
__pas_method_tobject_classnameaddress:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classnameaddress_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_name
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classnameaddress_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classnameaddress_result_2
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassName
global __pas_method_tobject_classname
__pas_method_tobject_classname:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classname_result_3
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tobject_classnameaddress
    pop esi
    push eax
    call _jit_dynstring_from_cstr
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classname_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classname_result_3
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.InstanceSize
global __pas_method_tobject_instancesize
__pas_method_tobject_instancesize:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_instancesize_result_4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_instance_size
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_instancesize_result_4
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_instancesize_result_4
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.InheritsFrom
global __pas_method_tobject_inheritsfrom
__pas_method_tobject_inheritsfrom:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_inheritsfrom_result_6
    pop eax
    mov byte ptr [ecx], al
    mov ecx, __pas_param_tobject_inheritsfrom_aclass_5
    mov eax, dword ptr [ecx]
    push eax
    mov eax, esi
    push eax
    call _jit_inherits_from_object
    add esp, 8
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    push eax
    mov ecx, __pas_result_tobject_inheritsfrom_result_6
    pop eax
    mov byte ptr [ecx], al
    mov ecx, __pas_result_tobject_inheritsfrom_result_6
    movzx eax, byte ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

align 4
__pas_unit_System_Objects_fmt_s: db 37, 115, 0
__pas_unit_System_Objects_fmt_d: db 37, 100, 0
__pas_unit_System_Objects_fmt_c: db 37, 99, 0
__pas_unit_System_Objects_newline: db 13, 10, 0
__pas_unit_System_Objects_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_System_Objects_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_result_tobject_classtype_result_0: dd 0 ; intern: pointer
__pas_result_tobject_classparent_result_1: dd 0 ; intern: pointer
__pas_result_tobject_classnameaddress_result_2: dd 0 ; intern: pointer
__pas_result_tobject_classname_result_3: dd 0 ; intern: string
__pas_result_tobject_instancesize_result_4: dd 0 ; intern: integer
__pas_param_tobject_inheritsfrom_aclass_5: dd 0 ; intern: pointer
__pas_result_tobject_inheritsfrom_result_6: db 0 ; intern: boolean

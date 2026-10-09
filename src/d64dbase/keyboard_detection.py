"""Native Win32/Win64 code for the dBase ``iskeyboard()`` built-in.

GetRawInputDeviceList enumerates devices visible to Windows Raw Input.
RIM_TYPEKEYBOARD=1; RAWINPUTDEVICELIST is 8 bytes on Win32 and 16 on Win64.
No C/Qt bridge or external build tools are involved.
"""
from __future__ import annotations


def emit_keyboard_probe(*, is64: bool, label_prefix: str,
                        has_shadow_space: bool = False) -> list[str]:
    """Return native assembly leaving 0/1 in EAX, balancing the stack.

    On x64 ``has_shadow_space=True`` means the calling WFM callback already
    has a correctly aligned Win64 shadow area. Normal dBase expressions have
    no such area and must align and allocate a separate one.
    """
    stem = str(label_prefix)
    done = f"{stem}_done"
    release = f"{stem}_release"
    scan = f"{stem}_scan"
    present = f"{stem}_present"

    if is64:
        # The caller's rsp is 16-byte aligned in WFM callbacks. Standalone
        # dBase expressions have rsp%16 == 8, as in existing API calls.
        frame = 64 if has_shadow_space else 72
        count = 32 if has_shadow_space else 40
        pointer = count + 8
        result = count + 16
        return [
            f"    sub rsp, {frame}",
            f"    mov dword ptr [rsp+{count}], 0",
            f"    mov qword ptr [rsp+{pointer}], 0",
            f"    mov dword ptr [rsp+{result}], 0",
            "    xor ecx, ecx",  # pRawInputDeviceList = NULL
            f"    lea rdx, [rsp+{count}]",  # puiNumDevices
            "    mov r8d, 16",  # cbSize = sizeof(RAWINPUTDEVICELIST)
            "    call GetRawInputDeviceList",
            "    cmp eax, 4294967295",  # UINT(-1) indicates failure
            f"    je {done}",
            f"    mov edx, dword ptr [rsp+{count}]",
            "    test edx, edx",
            f"    jz {done}",
            "    cmp edx, 268435455",  # count*16 must not overflow 32-bit
            f"    ja {done}",
            "    shl rdx, 4",  # allocation size
            "    xor ecx, ecx",  # lpAddress = NULL
            "    mov r8d, 12288",  # MEM_COMMIT | MEM_RESERVE
            "    mov r9d, 4",  # PAGE_READWRITE
            "    call VirtualAlloc",
            "    test rax, rax",
            f"    jz {done}",
            f"    mov qword ptr [rsp+{pointer}], rax",
            "    mov rcx, rax",
            f"    lea rdx, [rsp+{count}]",
            "    mov r8d, 16",
            "    call GetRawInputDeviceList",
            "    cmp eax, 4294967295",
            f"    je {release}",
            "    test eax, eax",
            f"    jz {release}",
            "    mov r10d, eax",  # number actually enumerated
            f"    mov r11, qword ptr [rsp+{pointer}]",
            f"{scan}:",
            "    cmp dword ptr [r11+8], 1",  # RIM_TYPEKEYBOARD
            f"    je {present}",
            "    add r11, 16",
            "    dec r10d",
            f"    jnz {scan}",
            f"    jmp {release}",
            f"{present}:",
            f"    mov dword ptr [rsp+{result}], 1",
            f"{release}:",
            f"    mov rcx, qword ptr [rsp+{pointer}]",
            "    xor edx, edx",  # dwSize=0
            "    mov r8d, 32768",  # MEM_RELEASE
            "    call VirtualFree",
            f"{done}:",
            f"    mov eax, dword ptr [rsp+{result}]",
            f"    add rsp, {frame}",
        ]

    # Win32 stdcall; all API callees remove their stack arguments.
    return [
        "    sub esp, 12",  # DWORD count, pointer, result
        "    mov dword ptr [esp], 0",
        "    mov dword ptr [esp+4], 0",
        "    mov dword ptr [esp+8], 0",
        "    lea eax, [esp]",
        "    push 8",  # sizeof(RAWINPUTDEVICELIST)
        "    push eax",  # puiNumDevices
        "    push 0",  # pRawInputDeviceList = NULL
        "    call GetRawInputDeviceList",
        "    cmp eax, 4294967295",
        f"    je {done}",
        "    mov edx, dword ptr [esp]",
        "    test edx, edx",
        f"    jz {done}",
        "    cmp edx, 536870911",  # count*8 must not overflow 32-bit
        f"    ja {done}",
        "    shl edx, 3",
        "    push 4",  # PAGE_READWRITE
        "    push 12288",  # MEM_COMMIT | MEM_RESERVE
        "    push edx",  # dwSize
        "    push 0",  # lpAddress = NULL
        "    call VirtualAlloc",
        "    test eax, eax",
        f"    jz {done}",
        "    mov dword ptr [esp+4], eax",
        "    lea edx, [esp]",
        "    push 8",
        "    push edx",
        "    push eax",
        "    call GetRawInputDeviceList",
        "    cmp eax, 4294967295",
        f"    je {release}",
        "    test eax, eax",
        f"    jz {release}",
        "    mov ecx, eax",
        "    mov edx, dword ptr [esp+4]",
        f"{scan}:",
        "    cmp dword ptr [edx+4], 1",  # RIM_TYPEKEYBOARD
        f"    je {present}",
        "    add edx, 8",
        "    dec ecx",
        f"    jnz {scan}",
        f"    jmp {release}",
        f"{present}:",
        "    mov dword ptr [esp+8], 1",
        f"{release}:",
        "    mov eax, dword ptr [esp+4]",
        "    push 32768",  # MEM_RELEASE
        "    push 0",  # dwSize=0
        "    push eax",  # lpAddress
        "    call VirtualFree",
        f"{done}:",
        "    mov eax, dword ptr [esp+8]",
        "    add esp, 12",
    ]

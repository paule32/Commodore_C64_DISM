# -*- coding: utf-8 -*-
"""Stage 449: shared, Qt-independent WFM variant formatting for the dBASE DLL.

ABI (PE32 cdecl / Windows x64):
 DBaseStringLengthN(char *text, uint32_t maximum) -> uint32_t
 DBaseWfmClassifyType(uint32_t type) -> uint32_t (0=NULL,1=STRING,2=OBJECT,3=NUMBER)
 DBaseWfmFormatValue(const ValueSlot *slot, char *number_scratch,
                     FormatResult *result) -> void

WFM ValueSlot is packed as [uint32 type, double number, uintptr ptr, uint32 len].
FormatResult is [uintptr ptr, uint32 len].  Both live in the caller's memory;
returned pointers refer to the source, the caller-owned buffer, or DLL literals.
No Qt5 call is made from this DLL. Caller handles the newline/GUI output.
"""

EXPORTS = ('DBaseStringLengthN', 'DBaseWfmClassifyType', 'DBaseWfmFormatValue')


def classify_type(value: int) -> int:
    """Reference semantics corresponding to the optimized inline comparisons."""
    return 1 if value in (3, 6) else 2 if value == 4 else 3 if value in (1, 2, 5) else 0


def string_length_n(value: bytes | None, maximum: int) -> int:
    """Bounded byte length; used for tests of the runtime's byte-level contract."""
    if not value or maximum <= 0:
        return 0
    limit = min(len(value), maximum)
    pos = value.find(b'\0', 0, limit)
    return limit if pos == -1 else pos


def emit_runtime(*, is64: bool) -> list[str]:
    """Emit three DLL leaf/helper procedures without WFM-specific globals."""
    code = []
    # Length always counts bytes (never UTF-8 codepoints); protects _gcvt's
    # 96-byte WFM output buffer against unbounded reads.
    length_name = 'DBaseStringLengthN'
    code += ['', f'{length_name}:']
    if is64:
        code += [
            '    xor eax, eax', '    test rcx, rcx', '    je __dbase_strlen_n_done',
            '    test edx, edx', '    je __dbase_strlen_n_done',
            '__dbase_strlen_n_loop:',
            '    movzx r8d, byte ptr [rcx]', '    test r8d, r8d',
            '    je __dbase_strlen_n_done',
            '    inc rcx', '    inc eax', '    dec edx',
            '    jne __dbase_strlen_n_loop',
            '__dbase_strlen_n_done:', '    ret',
        ]
    else:
        code += [
            '    push esi', '    mov esi, dword ptr [esp+8]',
            '    mov ecx, dword ptr [esp+12]',
            '    xor eax, eax', '    test esi, esi',
            '    je __dbase_strlen_n_done', '    test ecx, ecx',
            '    je __dbase_strlen_n_done',
            '__dbase_strlen_n_loop:',
            '    movzx edx, byte ptr [esi]', '    test edx, edx',
            '    je __dbase_strlen_n_done',
            '    inc esi', '    inc eax', '    dec ecx',
            '    jne __dbase_strlen_n_loop',
            '__dbase_strlen_n_done:', '    pop esi', '    ret',
        ]
    # Three conditional comparisons rather than five: type=1/2 -> number.
    code += ['', 'DBaseWfmClassifyType:']
    code.append('    mov eax, ecx' if is64 else '    mov eax, dword ptr [esp+4]')
    code += [
        '    cmp eax, 3', '    je __dbase_wfm_class_string',
        '    cmp eax, 6', '    je __dbase_wfm_class_string',
        '    cmp eax, 4', '    je __dbase_wfm_class_object',
        '    cmp eax, 5', '    je __dbase_wfm_class_number',
        '    sub eax, 1', '    cmp eax, 1',
        '    jbe __dbase_wfm_class_number',
        '    xor eax, eax', '    ret',
        '__dbase_wfm_class_string:', '    mov eax, 1', '    ret',
        '__dbase_wfm_class_object:', '    mov eax, 2', '    ret',
        '__dbase_wfm_class_number:', '    mov eax, 3', '    ret',
    ]
    # One exported formatter replaces each per-print 5-way switch,
    # _gcvt conversion, strlen loop and constant labeling. Preserve all
    # nonvolatile registers for both ABIs. DLL owns only NULL/object literals.
    pointer = 'qword' if is64 else 'dword'
    ptr_offset = 12
    len_offset = 20 if is64 else 16
    result_len_offset = 8 if is64 else 4
    code += ['', 'DBaseWfmFormatValue:']
    if is64:
        code += ['    push rbx', '    push rsi', '    push rdi',
                 '    mov rbx, rcx', '    mov rsi, rdx', '    mov rdi, r8']
        b, s, o, ax = 'rbx', 'rsi', 'rdi', 'rax'
    else:
        code += ['    push ebx', '    push esi', '    push edi',
                 '    mov ebx, dword ptr [esp+16]',
                 '    mov esi, dword ptr [esp+20]',
                 '    mov edi, dword ptr [esp+24]']
        b, s, o, ax = 'ebx', 'esi', 'edi', 'eax'
    code += [
        f'    test {o}, {o}', '    je __dbase_wfm_fmt_done',
        f'    test {b}, {b}', '    je __dbase_wfm_fmt_null',
        f'    mov eax, dword ptr [{b}]',
        '    cmp eax, 3', '    je __dbase_wfm_fmt_string',
        '    cmp eax, 4', '    je __dbase_wfm_fmt_object',
        '    cmp eax, 5', '    je __dbase_wfm_fmt_logical',
        '    cmp eax, 6', '    je __dbase_wfm_fmt_string',
        '    sub eax, 1', '    cmp eax, 1',
        '    jbe __dbase_wfm_fmt_number',
        '    jmp __dbase_wfm_fmt_null',
        '__dbase_wfm_fmt_string:',
        f'    mov {ax}, {pointer} ptr [{b}+{ptr_offset}]',
        f'    test {ax}, {ax}', '    je __dbase_wfm_fmt_null',
        f'    mov {pointer} ptr [{o}], {ax}',
        f'    mov eax, dword ptr [{b}+{len_offset}]',
        f'    mov dword ptr [{o}+{result_len_offset}], eax',
        '    jmp __dbase_wfm_fmt_done',
        '__dbase_wfm_fmt_object:',
        f'    mov {ax}, {pointer} ptr [{b}+{ptr_offset}]',
        f'    test {ax}, {ax}', '    je __dbase_wfm_fmt_null',
        f'    mov {ax}, __dbase_wfm_object_text',
        f'    mov {pointer} ptr [{o}], {ax}',
        f'    mov dword ptr [{o}+{result_len_offset}], 8',
        '    jmp __dbase_wfm_fmt_done',
        '__dbase_wfm_fmt_logical:',
        f'    mov eax, dword ptr [{b}+4]',
        f'    mov edx, dword ptr [{b}+8]',
        '    or eax, edx',
        '    je __dbase_wfm_fmt_false',
        f'    mov {ax}, __dbase_wfm_true_text',
        f'    mov {pointer} ptr [{o}], {ax}',
        f'    mov dword ptr [{o}+{result_len_offset}], 3',
        '    jmp __dbase_wfm_fmt_done',
        '__dbase_wfm_fmt_false:',
        f'    mov {ax}, __dbase_wfm_false_text',
        f'    mov {pointer} ptr [{o}], {ax}',
        f'    mov dword ptr [{o}+{result_len_offset}], 3',
        '    jmp __dbase_wfm_fmt_done',
        '__dbase_wfm_fmt_number:',
        f'    test {s}, {s}', '    je __dbase_wfm_fmt_null',
    ]
    if is64:
        code += [
            f'    movsd xmm0, qword ptr [{b}+4]',
            '    mov edx, 15', '    mov r8, rsi',
            '    sub rsp, 32', '    call __dbase_runtime_gcvt', '    add rsp, 32',
            '    mov rcx, rsi', '    mov edx, 96',
            '    sub rsp, 32', '    call DBaseStringLengthN', '    add rsp, 32',
            '    mov qword ptr [rdi], rsi',
            '    mov dword ptr [rdi+8], eax',
        ]
    else:
        code += [
            '    push esi', '    push 15',
            '    push dword ptr [ebx+8]', '    push dword ptr [ebx+4]',
            '    call __dbase_runtime_gcvt', '    add esp, 16',
            '    push 96', '    push esi',
            '    call DBaseStringLengthN', '    add esp, 8',
            '    mov dword ptr [edi], esi',
            '    mov dword ptr [edi+4], eax',
        ]
    code += [
        '    jmp __dbase_wfm_fmt_done',
        '__dbase_wfm_fmt_null:',
        f'    mov {ax}, __dbase_wfm_null_text',
        f'    mov {pointer} ptr [{o}], {ax}',
        f'    mov dword ptr [{o}+{result_len_offset}], 6',
        '__dbase_wfm_fmt_done:',
    ]
    if is64:
        code += ['    pop rdi', '    pop rsi', '    pop rbx', '    ret']
    else:
        code += ['    pop edi', '    pop esi', '    pop ebx', '    ret']
    return code


def emit_data() -> list[str]:
    return ['', '__dbase_wfm_null_text:', '    db "<null>", 0',
            '__dbase_wfm_object_text:', '    db "<object>", 0',
            '__dbase_wfm_true_text:', '    db ".T.", 0',
            '__dbase_wfm_false_text:', '    db ".F.", 0']

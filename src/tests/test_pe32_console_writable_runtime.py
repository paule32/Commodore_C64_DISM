import struct
import d64_dism as d64


def _first_section_characteristics(pe: bytes) -> int:
    pe_offset = struct.unpack_from('<I', pe, 0x3C)[0]
    optional_size = struct.unpack_from('<H', pe, pe_offset + 4 + 16)[0]
    section_offset = pe_offset + 4 + 20 + optional_size
    return struct.unpack_from('<I', pe, section_offset + 0x24)[0]


def test_internal_coff_mixed_text_is_writable():
    obj = d64.assemble_pe32_coff_object(
        '''bits 32
        global _start
        entry _start
        extern ExitProcess
        _start:
            mov eax, 1
            mov dword ptr [runtime_state], eax
            push 0
            call ExitProcess
        align 4
        runtime_state: dd 0
        ''',
        filename='runtime-write.asm',
    )
    chars = struct.unpack_from('<I', obj, 20 + 0x24)[0]
    assert chars & 0x80000000, hex(chars)


def test_final_pe32_mixed_text_is_writable():
    obj = d64.assemble_pe32_coff_object(
        '''bits 32
        global _start
        entry _start
        extern ExitProcess
        _start:
            mov eax, 1
            mov dword ptr [runtime_state], eax
            push 0
            call ExitProcess
        align 4
        runtime_state: dd 0
        ''',
        filename='runtime-write.asm',
    )
    program = d64.link_coff32_objects([obj])
    chars = _first_section_characteristics(program.executable)
    assert chars & 0x80000000, hex(chars)

"""Stage 648: compact, ABI-preserving CATCH/THROW slot copies."""
from pathlib import Path
import re

import pytest

from d64dbase.compiler import compile_dbase_to_assembly
from test_stage605_link import _load_pe_linker

SOURCE = '''TRY
    THROW NEW DbException("Fehler")
CATCH (DbException e)
    ? e.Message
ENDTRY
'''
RETHROW = '''TRY
    TRY
        THROW NEW DbException("Fehler")
    CATCH (DbException e)
        THROW e
    ENDTRY
CATCH (Exception outer)
    ? outer.Message
ENDTRY
'''

@pytest.mark.parametrize('target,reg,count', [('pe32','e',10),('pe64','r',12)])
def test_exception_catch_block_copy_and_nonvolatile_regs(target,reg,count):
    asm = compile_dbase_to_assembly(SOURCE, target=target, filename='stage648.prg').assembly
    handler = re.search(r'(?m)^__dbase_catch_handler_\d+:\n(.*?)(?=^__dbase_)',
                        asm, flags=re.S | re.M)
    assert handler
    body = handler.group(1)
    assert f'    push {reg}si\n    push {reg}di\n' in body
    assert '    lea '+reg+'si, [__dbase_exception_message_type]\n' in body
    assert '    lea '+reg+'di, [__dbase_caught_' in body
    assert f'    mov ecx, {count}\n    rep movsd\n' in body
    assert f'    pop {reg}di\n    pop {reg}si\n' in body
    assert '    fild dword ptr [__dbase_exception_code]' in body
    assert '    fstp qword ptr [' in body
    assert '    mov dword ptr [__dbase_exception_object_ptr], 0' in body if target == 'pe32' else '    mov qword ptr [__dbase_exception_object_ptr], 0' in body
    assert 'mov eax, dword ptr [__dbase_exception_message_type]' not in body

    # Byte-level slot adjacency is a deliberate invariant of the block copy.
    raw = asm.split('__dbase_exception_message_type:\n',1)[1]
    assert re.match(r'    resd 1\n__dbase_exception_message_num:\n    resq 1\n'
                    r'__dbase_exception_message_ptr:\n    res[qd] 1\n'
                    r'__dbase_exception_message_len:\n    resd 1\n'
                    r'__dbase_exception_class_type:\n', raw)

@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_compact_rethrow_direction_and_link(target):
    asm = compile_dbase_to_assembly(RETHROW,target=target,filename='stage648.prg').assembly
    assert asm.count('    rep movsd\n') >= 3
    assert '    lea '+('rsi' if target=='pe64' else 'esi')+', [__dbase_caught_' in asm
    linker = _load_pe_linker()
    object_program = linker[f'assemble_{target}_object_source'](asm)
    assert object_program.code.count(b'\xF3\xA5') >= 3
    blob = linker['write_coff32_object' if target == 'pe32' else 'write_coff64_object'](object_program)
    image = linker['link_coff32_objects' if target=='pe32' else 'link_coff64_objects'](
        (blob,), entry_symbol='_start')
    assert image.executable[:2] == b'MZ'

@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_internal_assembler_rep_movsd_opcode(target):
    linker = _load_pe_linker()
    asm = 'section .text\nentry _start\n_start:\n    rep movsd\n    ret\n'
    obj = linker[f'assemble_{target}_object_source'](asm)
    assert obj.code == b'\xF3\xA5\xC3'

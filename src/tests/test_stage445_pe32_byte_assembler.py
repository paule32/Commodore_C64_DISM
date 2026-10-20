# -*- coding: utf-8 -*-
"""Stage 445 – Echte PE32-COFF-Assemblertests fuer die dBASE-TRIM-Laufzeit."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import re
import struct
from typing import Dict, List, Optional, Tuple

import pytest

from d64dbase import compile_dbase_to_assembly
from d64dbase.string_length_trim import emit_trim_operation
from test_stage443_wfm_len_event import WFM, _compile_wfm_for_test

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def _assemble():
    """Qt-unabhaengigen Originalassembler laden, nicht einen Mock benutzen."""
    text = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
    start = text.index('IMAGE_FILE_MACHINE_I386 =')
    stop = text.index('def _pe32_apply_single_object_relocations(', start)
    ns = dict(globals())
    exec(compile(text[start:stop], 'stage445_real_pe32_assembler', 'exec'), ns)
    return ns['assemble_pe32_object_source']


def test_byte_mov_cmp_and_byte_immediate_have_correct_machine_code_and_offsets():
    source = '''section .text
entry _start
_start:
  mov esi, text
  mov al, byte ptr [esi]
  cmp al, 32
  mov bl, byte ptr [esi+1]
  cmp bl, 9
  mov byte ptr [esi+2], 0
  mov byte ptr [esi+1], al
  ret
section .data
text: db 32,9,0
'''
    obj = _assemble()(source)
    assert obj.code.hex() == 'be000000008a063c208a5e0180fb09c6460200884601c3'
    assert obj.data == b' \t\0'
    assert obj.symbols['_start'] == 0
    assert len(obj.relocations) == 1


def test_byte_memory_immediate_and_relocation_sizes():
    source = '''section .text
_start:
  mov byte ptr [flag], 255
next:
  mov al, byte ptr [flag]
  cmp al, 0
  ret
section .data
flag: db 0
'''
    obj = _assemble()(source)
    assert obj.symbols['next'] == 7  # C6 05 + disp32 + imm8
    assert obj.code[0:2] == bytes.fromhex('c6 05')
    assert obj.code[6] == 255
    assert obj.code[7:9] == bytes.fromhex('8a 05')
    assert obj.code[-3:] == bytes.fromhex('3c 00 c3')
    assert len(obj.relocations) == 2


@pytest.mark.parametrize('kind', ('ltrim', 'rtrim', 'trim'))
def test_complete_dbase_trim_generator_assembles_into_real_pe32_coff(kind):
    instructions = emit_trim_operation('src', 'dest', kind=kind,
             is64=False, prefix='test_' + kind, string_type=2)
    text = '\n'.join(['section .text', 'entry _start', '_start:'] + instructions + [
        'ret', 'section .data',
        'src_ptr: dd input_text', 'src_len: dd 8', 'src_type: dd 2',
        'dest_ptr: dd 0', 'dest_len: dd 0', 'dest_type: dd 0',
        'input_text: db 32,32,72,97,108,108,111,32,0',
    ])
    obj = _assemble()(text)
    assert len(obj.code) > 100
    assert 'test_' + kind + '_copy_done' in obj.symbols
    assert 'test_' + kind + '_allocated' in obj.symbols
    assert b'\xc6' in obj.code  # terminator: mov byte ptr [...], 0
    assert obj.externals  # malloc + ExitProcess


def test_complete_wfm_pe32_event_with_trim_assembles():
    src = WFM.replace('        ? RTRIM(" xyz  ")',
                      '        ? LTRIM(" xyz  ")\n        ? RTRIM(" xyz  ")')
    asm = _compile_wfm_for_test(src, target='pe32').assembly
    obj = _assemble()(asm)
    assert len(obj.code) > 1000
    assert any(name.startswith('__dbase_wfm_flow_') for name in obj.symbols)


def test_complete_dbase_prg_pe32_compiles_and_assembles():
    prg = '''FUNCTION valueText()
RETURN "  Beispiel   "
? LTRIM(valueText())
? RTRIM(valueText())
? TRIM(valueText())
? LEN(TRIM(valueText()))
'''
    result = compile_dbase_to_assembly(prg, target='pe32')
    obj = _assemble()(result.assembly)
    assert len(obj.code) > 100
    assert len(obj.relocations) > 10


def test_invalid_byte_size_rejected():
    assemble = _assemble()
    for statement in ('mov al, dword ptr [esi]', 'mov byte ptr [esi], 256', 'cmp al, 256'):
        with pytest.raises(Exception):
            assemble('_start:\n' + statement + '\nret\n')

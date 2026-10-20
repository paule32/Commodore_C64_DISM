# -*- coding: utf-8 -*-
"""Stage 446: true internal PE32/PE32+/COFF link integration (no mocked assembler)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Sequence, Optional, Tuple, List, Set, Union, Mapping, Iterable
import re
import os
import struct
import json
import math
import zlib
import sys
import ast
import io
import hashlib
import collections
import functools

from d64dbase import compile_dbase_to_assembly
from d64dbase.console_runtime import build_dll, DLL_NAME
from test_stage445_pe32_byte_assembler import _assemble
from test_stage443_wfm_len_event import WFM, _compile_wfm_for_test

ROOT = Path(__file__).parent


@lru_cache(maxsize=1)
def linkers():
    """Load only the non-Qt internal COFF/PE linker code from actual project."""
    funcs = _assemble().__globals__.copy()
    funcs.update({
        **globals(), "__name__": __name__,
    })
    source = (ROOT / 'd64_dism.py').read_text('utf-8')
    start = source.index('def _pe32_apply_single_object_relocations(')
    stop = source.index('class AmigaAssemblerError(', start)
    exec(compile(source[start:stop], 'stage446_internal_linker', 'exec'), funcs)
    return funcs


def test_internal_linker_generates_both_prepackaged_dlls_byte_identically(tmp_path):
    ns = linkers()
    for target in ('pe32', 'pe64'):
        destination = tmp_path / target / DLL_NAME
        build_dll(target, destination,
                  assemble32=ns['assemble_pe32_object_source'],
                  coff32=ns['write_coff32_object'], link32=ns['link_coff32_objects'],
                  assemble64=ns['assemble_pe64_object_source'],
                  coff64=ns['write_coff64_object'], link64=ns['link_coff64_objects'])
        assert destination.read_bytes() == (ROOT / 'd64dbase' / 'bin' / target / DLL_NAME).read_bytes()


def test_full_dbase_program_links_for_pe32_and_pe64(tmp_path):
    ns = linkers()
    program = '''SET FORMAT TO CONSOLE
STORE "  Hallo " TO Text
? LEN(Text)
? TRIM(Text)
? "Fertig"
'''
    for target in ('pe32','pe64'):
        asm = compile_dbase_to_assembly(program, target=target).assembly
        if target=='pe32':
            obj = ns['write_coff32_object'](ns['assemble_pe32_object_source'](asm))
            result = ns['link_coff32_objects']((obj,), entry_symbol='_start', gui=True)
        else:
            obj = ns['write_coff64_object'](ns['assemble_pe64_object_source'](asm))
            result = ns['link_coff64_objects']((obj,), entry_symbol='_start', gui=True)
        binary = result.executable
        assert binary.startswith(b'MZ')
        assert b'c64_dbase_runtime.dll' in binary
        assert b'DBaseConsoleWrite' in binary
        assert len(binary)>1500
        (tmp_path/f'{target}.exe').write_bytes(binary)


def test_wfm_real_coff_link_includes_console_dll_and_qt_bridge(tmp_path):
    ns = linkers()
    for target in ('pe32','pe64'):
        asm = _compile_wfm_for_test(WFM, target=target).assembly
        if target=='pe32':
            obj = ns['write_coff32_object'](ns['assemble_pe32_object_source'](asm))
            result = ns['link_coff32_objects']((obj,), entry_symbol='__d64_wfm_entry', gui=True)
        else:
            obj = ns['write_coff64_object'](ns['assemble_pe64_object_source'](asm))
            result = ns['link_coff64_objects']((obj,), entry_symbol='__d64_wfm_entry', gui=True)
        assert b'DBaseQtConsoleWrite' in result.executable
        assert b'c64_dbase_runtime.dll' in result.executable
        (tmp_path / f'wfm_{target}.exe').write_bytes(result.executable)


def test_x64_mov_byte_and_cmp_byte_mnemonics_are_real_machine_code():
    ns=linkers()
    asm='''section .text
entry _start
_start:
 mov al, byte ptr [rsi]
 cmp al, 32
 mov bl, byte ptr [rdi+1]
 cmp bl, 9
 mov byte ptr [rdi], 0
 ret
'''
    obj=ns['assemble_pe64_object_source'](asm)
    assert obj.code.startswith(bytes.fromhex('8a 06 3c 20 8a 5f 01 80 fb 09 c6 07 00 c3'))


def test_runtime_can_rebuild_from_internal_linker_if_packaged_binary_missing(tmp_path):
    from d64dbase.console_runtime import deploy_runtime
    from test_stage446_console_dll import pe_info, get_exports
    ns = linkers()
    fake_package = tmp_path / 'empty_package'
    for target in ('pe32','pe64'):
        output = tmp_path / target / 'myprogram.exe'
        path = deploy_runtime(output, target, package_root=fake_package,
                              get_exports=get_exports,
                              assemble32=ns['assemble_pe32_object_source'],
                              coff32=ns['write_coff32_object'],
                              link32=ns['link_coff32_objects'],
                              assemble64=ns['assemble_pe64_object_source'],
                              coff64=ns['write_coff64_object'],
                              link64=ns['link_coff64_objects'])
        assert path.is_file()
        assert pe_info(path)[0] == (0x14c if target=='pe32' else 0x8664)

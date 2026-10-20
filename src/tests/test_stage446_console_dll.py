# -*- coding: utf-8 -*-
"""Stage 446: genuine PE32/PE32+ console DLLs, real EXE imports & deployment."""
from __future__ import annotations

from pathlib import Path
import re
import struct

import pytest

from d64dbase import compile_dbase_to_assembly
from d64dbase.console_runtime import DLL_NAME, EXPORTS, assembly_source, deploy_runtime

ROOT = Path(__file__).parent
PRG = '''SET FORMAT TO CONSOLE
STORE "  console " TO Text
? LEN(Text)
? TRIM(Text)
?? "done"
'''


def pe_info(path: Path):
    """Read actual PE machine and exported names, no PyQt or external tooling."""
    d = Path(path).read_bytes()
    assert d[:2] == b'MZ'
    off = struct.unpack_from('<I', d, 0x3c)[0]
    assert d[off:off+4] == b'PE\x00\x00'
    machine, nsecs = struct.unpack_from('<HH', d, off+4)
    assert struct.unpack_from('<H', d, off+22)[0] & 0x2000
    opt = off + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    assert magic in (0x10b, 0x20b)
    export_rva = struct.unpack_from('<I', d, opt + (0x60 if magic == 0x10b else 0x70))[0]
    section_start = opt + struct.unpack_from('<H', d, off+20)[0]
    sections = []
    for i in range(nsecs):
        so = section_start + i*40
        va, rawsz, raw = (struct.unpack_from('<I', d, so+12)[0],
                          struct.unpack_from('<I', d, so+16)[0],
                          struct.unpack_from('<I', d, so+20)[0])
        sections.append((va, rawsz, raw))
    def file_offset(rva):
        for va, length, raw in sections:
            if va <= rva < va + max(length, 1):
                return raw + rva-va
        raise ValueError('unmapped RVA ' + hex(rva))
    names = set()
    if export_rva:
        eo = file_offset(export_rva)
        n = struct.unpack_from('<I', d, eo+24)[0]
        array_rva = struct.unpack_from('<I', d, eo+32)[0]
        for i in range(n):
            name_rva = struct.unpack_from('<I', d, file_offset(array_rva)+i*4)[0]
            no = file_offset(name_rva)
            names.add(d[no:d.index(b'\0', no)].decode('ascii'))
    return machine, names


def get_exports(path, machine):
    if not Path(path).is_file():
        return {}
    found_machine, names = pe_info(path)
    return {name: i for i, name in enumerate(sorted(names), 1)} if found_machine == machine else {}


@pytest.mark.parametrize('target,machine', [('pe32', 0x14c), ('pe64', 0x8664)])
def test_packaged_runtime_is_real_dll_with_all_four_exports(target, machine):
    p = ROOT / 'd64dbase' / 'bin' / target / DLL_NAME
    found_machine, names = pe_info(p)
    assert found_machine == machine
    assert set(EXPORTS).issubset(names)
    data = p.read_bytes()
    assert b'CONOUT$' in data
    assert b'kernel32.dll' in data.lower()
    assert b'user32.dll' in data.lower()


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_compiler_uses_dll_without_old_embedded_console(target):
    result = compile_dbase_to_assembly(PRG, target=target)
    asm = result.assembly
    for exported in EXPORTS:
        assert f'import {exported}, "{DLL_NAME}", "{exported}"' in asm
    assert 'call DBaseConsoleWrite' in asm
    assert 'call DBaseConsoleShutdown' in asm
    assert '__dbase_console_write:' not in asm
    assert '__dbase_console_ensure:' not in asm
    assert '__dbase_console_ready:' not in asm
    assert '__dbase_console_handle:' not in asm
    # numeric output buffer length is *not* the console lifecycle state
    assert '__dbase_console_number_len:' in asm
    assert '__dbase_workstation_lazy_console_marker:' in asm
    assert 'import AllocConsole,' not in asm
    if target == 'pe64':
        assert 'sub rsp, 40\n    call DBaseConsoleWrite\n    add rsp, 40' in asm
        assert 'sub rsp, 40\n    call DBaseConsoleShutdown\n    add rsp, 40' in asm


def test_dll_assembly_is_shared_with_original_console_implementation():
    s32 = assembly_source('pe32')
    s64 = assembly_source('pe64')
    for src in (s32, s64):
        assert 'AllocConsole' in src and 'CONOUT$' in src
        assert 'SetConsoleScreenBufferSize' in src
        assert 'SetForegroundWindow' in src
        assert 'SetConsoleOutputCP' in src and '1252' in src
        assert 'DBaseConsoleSetTitle' in src
        assert '__dbase_console_title_selected' in src
        assert '__dbase_console_shutdown:' in src
    assert '__dbase_console_dll_entry:\n    mov eax, 1\n    ret 12' in s32
    assert '__dbase_console_dll_entry:\n    mov eax, 1\n    ret\n' in s64


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_deploy_copies_correct_architecture_and_repairs_incompatible_file(tmp_path, target):
    output = tmp_path / 'test.exe'
    dest = deploy_runtime(output, target, get_exports=get_exports)
    machine, exports = pe_info(dest)
    assert machine == (0x14c if target=='pe32' else 0x8664)
    assert set(EXPORTS).issubset(exports)
    assert dest.read_bytes() == (ROOT/'d64dbase'/'bin'/target/DLL_NAME).read_bytes()
    dest.write_bytes(b'bad binary')
    assert deploy_runtime(output, target, get_exports=get_exports) == dest
    assert set(EXPORTS).issubset(pe_info(dest)[1])


def test_runtime_deployment_fails_if_no_binary_or_linker(tmp_path):
    missing = tmp_path / 'not-packed'
    with pytest.raises(FileNotFoundError):
        deploy_runtime(tmp_path / 'program.exe', 'pe32', get_exports=get_exports,
                       package_root=missing)


def test_wfm_output_still_uses_qt_bridge():
    from test_stage443_wfm_len_event import _compile_wfm_for_test, WFM
    assembly = _compile_wfm_for_test(WFM, target='pe32').assembly
    assert 'DBaseQtConsoleWrite' in assembly
    # The WFM bootstrap may include ordinary dBASE console output as well.
    # WFM events themselves still use the Qt5 bridge.
    assert DLL_NAME in assembly
    assert 'call DBaseQtConsoleWrite' in assembly


def test_gui_build_and_start_deploy_the_console_dll():
    source = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
    assert 'def _prepare_dbase_console_runtime(' in source
    assert 'assemble32=assemble_pe32_object_source' in source
    assert 'assemble64=assemble_pe64_object_source' in source
    assert 'self._prepare_dbase_console_runtime(output_path, document.build_target)' in source
    assert 'b"c64_dbase_runtime.dll" in output_path.read_bytes().lower()' in source
    assert 'from d64dbase.console_runtime import deploy_runtime' in source


def test_architecture_mismatch_is_corrected_even_with_same_exports(tmp_path):
    from shutil import copy2
    path = tmp_path / DLL_NAME
    copy2(ROOT / 'd64dbase' / 'bin' / 'pe64' / DLL_NAME, path)
    assert pe_info(path)[0] == 0x8664
    deploy_runtime(tmp_path / 'test.exe', 'pe32', get_exports=get_exports)
    assert pe_info(path)[0] == 0x014c

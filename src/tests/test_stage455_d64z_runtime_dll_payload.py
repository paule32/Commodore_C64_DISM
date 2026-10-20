# -*- coding: utf-8 -*-
"""Stage 455: DLL-specific D64Z payload and loader for both COFF targets."""
import ctypes
import os
import struct
import sys
import zlib
from pathlib import Path

import pytest

from test_stage446_real_pe_link import linkers
from d64dbase.console_runtime import DLL_NAME, EXPORTS, build_dll, deploy_runtime, assembly_source
from d64dbase.runtime_builder import create_runtime_dll
from d64dbase.pe_dll_payload import (D64Z, DLL_LOADER_IMPORTS, is_payload_packed,
                                      import_iats, parse_pe, rva_offset,
                                      text_relocations, pack_pe_dll)


def _kwargs():
    ns = linkers()
    return dict(assemble32=ns['assemble_pe32_object_source'],
                coff32=ns['write_coff32_object'], link32=ns['link_coff32_objects'],
                assemble64=ns['assemble_pe64_object_source'],
                coff64=ns['write_coff64_object'], link64=ns['link_coff64_objects'])


def _get_exports(path, machine):
    """Read actual exported names, no synthetic export set."""
    pe = parse_pe(Path(path).read_bytes())
    if pe['machine'] != machine:
        raise ValueError('architecture mismatch')
    b = pe['blob']
    export_rva, size = struct.unpack_from('<II', b, pe['dd'])
    assert export_rva and size
    off = rva_offset(pe, export_rva)
    count = struct.unpack_from('<I', b, off+24)[0]
    names_rva = struct.unpack_from('<I', b, off+32)[0]
    return {
        b[rva_offset(pe, struct.unpack_from('<I', b, rva_offset(pe, names_rva+i*4))[0]):].split(b'\0', 1)[0].decode()
        for i in range(count)
    }


@pytest.mark.parametrize('target,machine', [('pe32',0x14c),('pe64',0x8664)])
def test_real_linker_payload_roundtrips_text_and_relocations(tmp_path, target, machine):
    kwargs = _kwargs()
    plain=tmp_path/f'{target}-plain.dll'
    packed=tmp_path/target/DLL_NAME
    # Baseline uses the same import-containing *pre-packing* image as the
    # payload packer; its five keepalive calls are not in the plain runtime.
    source=assembly_source(target, payload_loader=True)
    if target == 'pe32':
        obj=kwargs['coff32'](kwargs['assemble32'](source))
        baseline=kwargs['link32']((obj,), entry_symbol='__dbase_console_dll_entry',
                                  dll=True, dll_name=DLL_NAME).executable
    else:
        obj=kwargs['coff64'](kwargs['assemble64'](source))
        baseline=kwargs['link64']((obj,), entry_symbol='__dbase_console_dll_entry',
                                  dll=True, dll_name=DLL_NAME).executable
    plain.write_bytes(baseline)
    # Non-Windows unit-test compressor models the byte container; production
    # passes None and uses Cabinet/MSZIP (same as the existing EXE packer).
    build_dll(target, packed, pack_dll=True, compressor=zlib.compress, **kwargs)
    orig=parse_pe(plain.read_bytes())
    result=parse_pe(packed.read_bytes())
    assert orig['machine'] == result['machine'] == machine
    assert result['entry'] != orig['entry']
    assert is_payload_packed(packed)
    assert len(_get_exports(packed, machine)) == len(EXPORTS)
    assert set(EXPORTS) == _get_exports(plain, machine) == _get_exports(packed, machine)
    for name in ('.loader', '.ztext'):
        sec=next(s for s in result['secs'] if s['name']==name.encode())
        assert sec['rsize'] and sec['rptr']
    assert next(s for s in result['secs'] if s['name']==b'.text')['rsize'] == 0
    loader=next(s for s in result['secs'] if s['name']==b'.loader')
    assert loader['chars'] & 0x80000000   # initialization guard is writable
    assert loader['chars'] & 0x20000000   # and executed from Windows loader
    ztext=next(s for s in result['secs'] if s['name']==b'.ztext')
    hdr=D64Z.unpack_from(ztext['data'])
    assert hdr[:4] == (b'D64Z', 1, 2, 1)
    oldtext=next(s for s in orig['secs'] if s['name']==b'.text')
    assert hdr[4] == oldtext['rva'] and hdr[5] == oldtext['vsize']
    packed_raw=ztext['data'][D64Z.size:D64Z.size+hdr[6]]
    assert zlib.decompress(packed_raw) == oldtext['data'][:oldtext['vsize']]
    assert hdr[7] == orig['entry']
    assert hdr[8] == zlib.crc32(oldtext['data'][:oldtext['vsize']])
    relocs=text_relocations(result, next(s for s in result['secs'] if s['name']==b'.text'))
    assert relocs
    relocation_bytes=ztext['data'][D64Z.size+hdr[6]:D64Z.size+hdr[6]+4*len(relocs)]
    assert tuple(struct.unpack('<'+'I'*len(relocs), relocation_bytes)) == tuple(relocs)
    assert text_relocations(orig, oldtext) == relocs[:len(text_relocations(orig,oldtext))]
    iats=import_iats(result)
    for dll, function in DLL_LOADER_IMPORTS.values():
        assert (dll,function) in iats
    # Critical PE directories remain byte-for-byte identical RVAs & sizes.
    for index in (0,1,5):
        assert struct.unpack_from('<II',orig['blob'],orig['dd']+8*index) == struct.unpack_from('<II',result['blob'],result['dd']+8*index)


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_manual_create_packs_without_ntfs(tmp_path, target):
    dest=create_runtime_dll(target, tmp_path/target, get_exports=_get_exports,
                            pack_dll=True, compressor=zlib.compress, **_kwargs())
    assert dest.is_file() and is_payload_packed(dest)


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_deploy_packed_dll_and_preserve_it(tmp_path, monkeypatch, target):
    import d64dbase.pe_dll_payload as packer
    monkeypatch.setattr(packer, 'mszip_compress', zlib.compress)
    root = tmp_path/'bin'
    executable = tmp_path/target/'program.exe'
    result=deploy_runtime(executable, target, get_exports=_get_exports,
                          package_root=root, pack_dll=True, **_kwargs())
    assert result.name == DLL_NAME and is_payload_packed(result)
    before = result.read_bytes()
    again=deploy_runtime(executable, target, get_exports=_get_exports,
                         package_root=root, pack_dll=True, **_kwargs())
    assert again.read_bytes() == before


def test_user_facing_gui_reports_payload_not_ntfs():
    src=Path(__file__).with_name('d64_dism.py').read_text('utf-8')
    start=src.index('        def create_dbase_runtime_dll(')
    end=src.index('        def set_project_windows_output_directory(',start)
    assert 'D64Z/MSZIP-Payload' in src[start:end]
    assert 'NTFS' in src[start:end]  # explicitly mentions NTFS is not needed
    assert 'compression_report' not in src[start:end]


@pytest.mark.skipif(os.name!='nt', reason='Windows LoadLibrary + Cabinet/MSZIP integration')
def test_native_windows_real_loader_export(tmp_path):
    target='pe64' if struct.calcsize('P')==8 else 'pe32'
    path=tmp_path/target/DLL_NAME
    build_dll(target,path, pack_dll=True, **_kwargs())
    lib=ctypes.CDLL(str(path))  # actual Windows LoadLibrary/PROCESS_ATTACH
    pred=lib.DBaseCharIsLowerCP1252
    pred.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    pred.restype=ctypes.c_int
    sample=ctypes.create_string_buffer(b'a')
    assert pred(ctypes.addressof(sample),1)==1

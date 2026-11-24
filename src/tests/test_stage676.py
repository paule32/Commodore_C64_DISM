# -*- coding: utf-8 -*-
"""Stage 676 regression: merged native dBASE runtime and import routing."""
from __future__ import annotations
import ctypes
from pathlib import Path
import re
import shutil
import struct
import subprocess
import pytest
from d64dbase import compile_dbase_to_assembly
from dbase_size_optimizer import optimize_dbase_size_assembly
from d64dbase.native_runtime_deploy import (
    DLL_NAME, REQUIRED_EXPORTS, DBASE_EXPORTS, deploy_runtime,
)
from d64dbase.char_case import _cp1252_is_case

ROOT=Path(__file__).resolve().parent


def test_runtime_exports_build_and_qt_bridge_source():
    src=(ROOT/'runtime/dbase_runtime_merged.cc').read_text()
    defs=(ROOT/'d64qt5/d64qt5_bridge.def').read_text()
    qt=(ROOT/'d64qt5/d64qt5_bridge.cpp').read_text()
    build=(ROOT/'runtime/build.qt5_embedded.win32.sh').read_text()
    assert 'dbase_runtime_merged' in build and 'libd64_qt5_native.a' in build
    assert '-lmsvcrt' in (ROOT/'d64qt5/d64qt5_bridge.pro').read_text()
    for name in DBASE_EXPORTS:
        assert re.search(r'\b'+name+r'\s*\(',src)
        assert re.search(r'^\s*'+name+r'\s+@\d+',defs,re.M)
    assert 'DBaseConsoleWrite(text, length);' in qt
    assert 'LoadLibraryA("libd64_runtime.dll")' not in qt
    assert 'GetModuleHandleA("libd64_runtime.dll")' not in qt
    assert 'GetModuleHandleA("c64_dbase_runtime.dll")' not in qt
    assert 'from d64dbase.native_runtime_deploy import deploy_runtime' in (ROOT/'d64_dism.py').read_text()


@pytest.mark.parametrize('target', ('pe32','pe64'))
@pytest.mark.parametrize('level', ('O0','O1','O2'))
def test_real_dbase_generated_imports_and_coff_link(target,level,tmp_path):
    from test_stage605_link import _load_pe_linker
    from pascal_console_dependencies import inspect_pe
    native=_load_pe_linker()
    asm=compile_dbase_to_assembly('? "Hallo"\n? "Welt"\n',target=target).assembly
    asm=optimize_dbase_size_assembly(asm,level=level).assembly
    assert '"c64_dbase_runtime.dll"' not in asm
    assert '"libd64_runtime.dll"' not in asm
    assert 'import DBaseWfmFormatValue, "libd64_qt5.dll", "DBaseWfmFormatValue"' in asm
    obj=native['assemble_pe32_object_source' if target=='pe32' else 'assemble_pe64_object_source'](asm)
    machine=0x14c if target=='pe32' else 0x8664
    linked=native['link_coff32_objects' if target=='pe32' else 'link_coff64_objects'](
        (native['write_coff32_object' if target=='pe32' else 'write_coff64_object'](obj),),
        entry_symbol='_start',gui=True)
    binary=tmp_path/'App.exe';binary.write_bytes(linked.executable)
    pe_machine, imports, _=inspect_pe(binary)
    assert pe_machine==machine
    assert 'c64_dbase_runtime.dll' not in imports
    assert 'libd64_runtime.dll' not in imports
    assert 'DBaseConsoleWrite' in imports['libd64_qt5.dll']


@pytest.mark.skipif(not shutil.which('g++'),reason='g++ missing')
def test_native_functions_actual_abi(tmp_path):
    so=tmp_path/'native.so'
    subprocess.run(['g++','-std=c++20','-shared','-fPIC','-O1',
                    '-o',str(so),str(ROOT/'runtime/dbase_runtime_merged.cc')],check=True)
    dll=ctypes.CDLL(str(so))
    for upper in (False,True):
        for encoding in ('CP1252','Utf8'):
            fn=getattr(dll,'DBaseCharIs'+('Upper' if upper else 'Lower')+encoding)
            fn.argtypes=[ctypes.c_char_p,ctypes.c_uint]
            fn.restype=ctypes.c_int
            for v in range(256):
                try: ch=bytes([v]).decode('cp1252')
                except UnicodeDecodeError: continue
                raw=ch.encode('utf8' if encoding=='Utf8' else 'cp1252')
                expected= int(_cp1252_is_case(v,upper))
                # The original UTF-8 predicate supports only 1/2-byte
                # codepoints. Three-byte punctuation is explicitly excluded.
                if encoding=='Utf8' and len(raw)>2: expected=0
                assert fn(raw,len(raw))==expected,(upper,encoding,v)
            assert fn(b'A',2)==0
    strlen=dll.DBaseStringLengthN
    strlen.argtypes=[ctypes.c_char_p,ctypes.c_uint];strlen.restype=ctypes.c_uint
    assert strlen(b'ab\0xyz',8)==2
    assert strlen(b'ab\0xyz',1)==1
    assert strlen(None,15)==0
    classify=dll.DBaseWfmClassifyType
    classify.argtypes=[ctypes.c_uint];classify.restype=ctypes.c_uint
    assert [classify(i) for i in range(8)]==[0,3,3,1,2,3,1,0]
    fmt=dll.DBaseWfmFormatValue
    fmt.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
    fmt.restype=None
    ptrfmt='<Q' if ctypes.sizeof(ctypes.c_void_p)==8 else '<I'
    def formatted(kind, numeric=0., payload=None):
        buf=ctypes.create_string_buffer(payload) if payload is not None else None
        addr=ctypes.addressof(buf) if buf is not None else 0
        slot=ctypes.create_string_buffer(struct.pack('<Id',kind,numeric)
            +struct.pack(ptrfmt,addr)+struct.pack('<I',len(payload) if payload else 0))
        scratch=ctypes.create_string_buffer(96)
        raw=(ctypes.c_ubyte*20)(*([0xaa]*20))
        fmt(slot,scratch,raw)
        offset=ctypes.sizeof(ctypes.c_void_p)
        ptr=struct.unpack_from(ptrfmt,bytes(raw),0)[0]
        size=struct.unpack_from('<I',bytes(raw),offset)[0]
        assert bytes(raw)[offset+4:]==b'\xaa'*(20-offset-4), 'format wrote C++ padding beyond ABI structure'
        return ctypes.string_at(ptr,size)
    assert formatted(3,payload=b'hello')==b'hello'
    assert formatted(4,payload=b'object')==b'<object>'
    assert formatted(3)==b'<null>'
    assert formatted(5,numeric=1.)==b'.T.'
    assert formatted(5,numeric=0.)==b'.F.'
    assert formatted(1,numeric=12.5)==b'12.5'
    assert formatted(2,numeric=-7.0)==b'-7'
    dll.DBaseConsoleSetTitle.argtypes=[ctypes.c_char_p]
    dll.DBaseConsoleSetTitle(b'Test')
    dll.DBaseConsoleEnsure()
    dll.DBaseConsoleWrite.argtypes=[ctypes.c_char_p,ctypes.c_int]
    dll.DBaseConsoleWrite(b'hello',5)
    dll.DBaseConsoleShutdown()


def test_native_deployment_checks_merged_exports_and_machine(tmp_path):
    pkg=tmp_path/'project';dest=tmp_path/'out'
    source=pkg/'d64qt5/release'/DLL_NAME; source.parent.mkdir(parents=True)
    source.write_bytes(b'PE32 NEW RUNTIME')
    def parser(path,expected_machine):
        data=Path(path).read_bytes()
        return {name:i for i,name in enumerate(REQUIRED_EXPORTS)} if (
            expected_machine==0x14c and data==b'PE32 NEW RUNTIME') else {}
    out=deploy_runtime(dest/'App.exe','pe32',get_exports=parser,package_root=pkg)
    assert out.read_bytes()==source.read_bytes()
    # Ensure an obsolete 11-export-only binary does not replace the native.
    source.write_bytes(b'OLD CONSOLE')
    assert deploy_runtime(dest/'App.exe','pe32',get_exports=parser,package_root=pkg)==out
    out.unlink()
    with pytest.raises(FileNotFoundError,match='libd64_qt5.dll'):
        deploy_runtime(dest/'App.exe','pe32',get_exports=parser,package_root=pkg)
    with pytest.raises(FileNotFoundError):
        deploy_runtime(dest/'App.exe','pe64',get_exports=parser,package_root=pkg)

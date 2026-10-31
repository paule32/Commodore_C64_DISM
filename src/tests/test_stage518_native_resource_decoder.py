# -*- coding: utf-8 -*-
"""Stage 518: native C-ABI decoder against the actual Stage-517 packer."""
import ctypes
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

import pytest
from test_stage504_resource_hex_codepage import SCOPE

HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native' / 'd64resource'


class NativeInfo(ctypes.Structure):
    _fields_ = [
        ('struct_size', ctypes.c_uint32),
        ('original_type', ctypes.c_uint16),
        ('original_id', ctypes.c_uint16),
        ('language', ctypes.c_uint16),
        ('reserved', ctypes.c_uint16),
        ('codepage', ctypes.c_uint32),
        ('size', ctypes.c_uint32),
        ('crc32', ctypes.c_uint32),
    ]


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    if os.name == 'nt' or shutil.which('cc') is None:
        pytest.skip('Native Test benötigt GCC/Clang unter Linux')
    folder = tmp_path_factory.mktemp('native_lib')
    out = folder / 'libd64resource.so'
    subprocess.run(['cc', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-shared', '-fPIC', str(NATIVE / 'd64resource.c'),
                    '-o', str(out), '-lz'], check=True, timeout=40)
    lib = ctypes.CDLL(str(out))
    ptr = ctypes.c_void_p
    lib.D64ResourceInspect.argtypes = [ptr, ctypes.c_uint32, ctypes.POINTER(NativeInfo)]
    lib.D64ResourceInspect.restype = ctypes.c_int
    lib.D64ResourceDecode.argtypes = [ptr, ctypes.c_uint32, ptr, ctypes.c_uint32,
                                      ctypes.POINTER(NativeInfo)]
    lib.D64ResourceDecode.restype = ctypes.c_int
    return lib


def make_record(page=65001, original=None):
    original = original if original is not None else ('Öffnen'.encode('utf-8') * 1000)
    entry = SCOPE['ResourceEntry'](10, 200, original, 0x0407, codepage=page)
    packed = SCOPE['pack_resource_dll_entries']([entry])[0]
    assert packed.type_id == 0xF117
    return bytes(packed.data), original


def call_decode(native, raw, capacity=None):
    source = ctypes.create_string_buffer(bytes(raw))
    info = NativeInfo()
    info.struct_size = ctypes.sizeof(info)
    code = native.D64ResourceInspect(source, len(raw), ctypes.byref(info))
    if code:
        return code, info, None
    if capacity is None:
        capacity = info.size
    output = ctypes.create_string_buffer(max(capacity, 1))
    code = native.D64ResourceDecode(source, len(raw), output, capacity, ctypes.byref(info))
    return code, info, output.raw[:info.size] if code == 0 else None


@pytest.mark.parametrize('page', [20127, 65001, 1200])
@pytest.mark.parametrize('content', [b'A' * 4096, b'ABCDE' * 900, bytes(range(32)) * 250])
def test_native_matches_python_unpack(native, page, content):
    payload, source = make_record(page, content)
    code, info, output = call_decode(native, payload)
    assert code == 0 and output == content
    assert (info.original_type, info.original_id, info.language, info.codepage) == (
        10, 200, 0x0407, page)
    assert info.crc32 == zlib.crc32(content)
    assert info.size == len(content)
    assert SCOPE['unpack_resource_dll_record'](payload)[4] == output


def test_query_without_output_and_with_undersized_buffer(native):
    payload, content = make_record()
    record = ctypes.create_string_buffer(payload)
    info = NativeInfo()
    info.struct_size = ctypes.sizeof(info)
    assert native.D64ResourceDecode(record, len(payload), None, 0, ctypes.byref(info)) == 1
    assert info.size == len(content)
    too_small = ctypes.create_string_buffer(8)
    assert native.D64ResourceDecode(record, len(payload), too_small, 8, ctypes.byref(info)) == 1
    assert native.D64ResourceDecode(record, len(payload), None, 0, None) == -1


@pytest.mark.parametrize('mutation,expected', [
    ('bad_magic', -2), ('empty', -2), ('huge_size', -3),
    ('crc', -5), ('length', -4), ('zlib', -4), ('trailing', -4),
])
def test_native_rejects_damaged_record(native, mutation, expected):
    payload, _ = make_record()
    raw = bytearray(payload)
    if mutation == 'bad_magic':
        raw[0] = 0x00
    elif mutation == 'empty':
        raw = raw[:24]
    elif mutation == 'huge_size':
        struct.pack_into('<I', raw, 18, 128 * 1024 * 1024 + 1)
    elif mutation == 'crc':
        struct.pack_into('<I', raw, 22, 0)
    elif mutation == 'length':
        struct.pack_into('<I', raw, 18, 12001)
    elif mutation == 'zlib':
        raw[26] ^= 0xFF
    elif mutation == 'trailing':
        raw += b'EXTRA'
    if mutation in ('bad_magic', 'empty', 'huge_size'):
        info = NativeInfo(); info.struct_size = ctypes.sizeof(info)
        buf = ctypes.create_string_buffer(bytes(raw))
        assert native.D64ResourceInspect(buf, len(raw), ctypes.byref(info)) == expected
    else:
        result, _, _ = call_decode(native, raw)
        assert result == expected


def test_native_artifacts_and_windows_loader_exports():
    header = (NATIVE / 'd64resource.h').read_text(encoding='utf-8')
    code = (NATIVE / 'd64resource.c').read_text(encoding='utf-8')
    script = (NATIVE / 'build_windows.sh').read_text(encoding='utf-8')
    demo = (NATIVE / 'demo_win.c').read_text(encoding='utf-8')
    assert 'D64ResourceDecode' in header and 'D64ResourceReadModuleW' in header
    assert 'D64RES_CALL __cdecl' in header
    assert 'EnumResourceNamesW' in code and 'EnumResourceLanguagesW' in code
    assert 'D64RES_PACKED_TYPE' in code and 'D64RES_PACKED_TYPE 0xF117u' in header
    assert 'LOAD_LIBRARY_AS_DATAFILE' in demo and 'GetProcAddress' in demo
    assert 'demo_standalone.exe' in script and 'demo_external_dll.exe' in script
    assert 'i686-w64-mingw32' in script and 'x86_64-w64-mingw32' in script

@pytest.fixture(scope='module')
def winmock(tmp_path_factory):
    """Compile/run the Win32 lookup branch against a minimal API shim."""
    if os.name == 'nt' or shutil.which('cc') is None:
        pytest.skip('Windows-Mock-Kompilierung nur unter Linux')
    build = tmp_path_factory.mktemp('winmock')
    libpath = build / 'libd64winmock.so'
    mock = NATIVE / 'tests' / 'fakewin'
    subprocess.run(['cc', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-shared', '-fPIC', '-D_WIN32', '-DD64RESOURCE_STATIC',
                    '-I', str(mock), str(NATIVE / 'd64resource.c'),
                    str(mock / 'mock_winapi.c'), '-o', str(libpath), '-lz'],
                   check=True, timeout=40)
    lib = ctypes.CDLL(str(libpath))
    ptr = ctypes.c_void_p
    lib.TestReset.argtypes = []
    lib.TestAdd.argtypes = [ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16,
                            ptr, ctypes.c_uint32]
    lib.TestAdd.restype = ctypes.c_int
    lib.D64ResourceReadModuleW.argtypes = [ptr, ctypes.c_uint16, ctypes.c_uint16,
                                           ctypes.c_uint16, ptr, ctypes.c_uint32,
                                           ctypes.POINTER(NativeInfo)]
    lib.D64ResourceReadModuleW.restype = ctypes.c_int
    return lib


def test_windows_abi_lookup_original_id_and_language(winmock):
    winmock.TestReset()
    bytes_utf8 = b'Byte payload!' * 400
    packed, _ = make_record(65001, bytes_utf8)
    saved_packed = ctypes.create_string_buffer(packed)
    saved_plain = ctypes.create_string_buffer(b'plain data')
    # Packer generates packed ID 1. Standalone asks original ID 200.
    assert winmock.TestAdd(0xF117, 1, 0x0407, saved_packed, len(packed)) == 0
    assert winmock.TestAdd(10, 201, 0x0407, saved_plain, 10) == 0
    info = NativeInfo(); info.struct_size = ctypes.sizeof(info)
    module = ctypes.c_void_p(1)
    read = winmock.D64ResourceReadModuleW
    assert read(module, 10, 200, 0x0407, None, 0, ctypes.byref(info)) == 1
    assert info.size == len(bytes_utf8) and info.codepage == 65001
    output = ctypes.create_string_buffer(info.size)
    assert read(module, 10, 200, 0x0407, output, len(output), ctypes.byref(info)) == 0
    assert output.raw == bytes_utf8
    assert read(module, 10, 200, 0x0409, output, len(output), ctypes.byref(info)) == -6
    info.struct_size = ctypes.sizeof(info)
    assert read(module, 10, 201, 0, None, 0, ctypes.byref(info)) == 1
    assert info.size == 10 and info.codepage == 0
    plain_out = ctypes.create_string_buffer(10)
    assert read(module, 10, 201, 0, plain_out, 10, ctypes.byref(info)) == 0
    assert plain_out.raw == b'plain data'


def test_windows_abi_handles_multiple_internal_ids(winmock):
    winmock.TestReset()
    packed1, _ = make_record(65001, b'Z' * 1000)
    # Edit header's original ID from 200 to 500 and update original language.
    one = ctypes.create_string_buffer(packed1)
    two = bytearray(packed1)
    struct.pack_into('<H', two, 10, 500)
    two = bytes(two)
    two_buf = ctypes.create_string_buffer(two)
    winmock.TestAdd(0xF117, 1, 0x0407, one, len(packed1))
    winmock.TestAdd(0xF117, 7, 0x0407, two_buf, len(two))
    info = NativeInfo(); info.struct_size = ctypes.sizeof(info)
    assert winmock.D64ResourceReadModuleW(ctypes.c_void_p(1), 10, 500, 0,
                                          None, 0, ctypes.byref(info)) == 1
    out = ctypes.create_string_buffer(info.size)
    assert winmock.D64ResourceReadModuleW(ctypes.c_void_p(1), 10, 500, 0,
                                          out, len(out), ctypes.byref(info)) == 0
    assert out.raw == b'Z' * 1000

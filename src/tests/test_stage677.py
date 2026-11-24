# -*- coding: utf-8 -*-
"""Stage 677: Resolve Win32 dynamic exports without cast-function-type warnings."""
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parent


def test_pascal_console_uses_native_allocator_inside_qt5():
    source = (ROOT / 'd64qt5/d64_pascal_console.cpp').read_text()
    assert '_jit_malloc(1024)' in source
    assert 'GetProcAddress(runtime, "_jit_malloc")' not in source
    assert '_jit_malloc' in (ROOT / 'd64qt5/d64qt5_bridge.h').read_text()


def test_qt_console_writer_is_a_direct_cdecl_function():
    source = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text()
    assert 'DBaseConsoleWrite(text, length);' in source
    assert 'GetProcAddress(module, "DBaseConsoleWrite")' not in source
    assert 'DBaseConsoleWrite' in (ROOT / 'd64qt5/d64qt5_bridge.def').read_text()


@pytest.mark.skipif(not shutil.which('g++'), reason='GCC unavailable')
def test_generic_function_pointer_abi_transfer_compiles_and_runs_without_warning(tmp_path):
    """Native stand-in; Windows/MinGW full build requires the target toolchain."""
    source = tmp_path / 'function_pointer_conversion.cpp'
    source.write_text(r'''
#include <cstring>
#include <cstddef>
#include <cstdio>
// Deliberately different function signatures, as with Win32 FARPROC.
using FARPROC = int (*)();
using Alloc = void* (*)(unsigned);
using ConsoleWriter = void (*)(const char*, int);
static unsigned char buffer[32];
static int called = 0;
void* runtime_malloc(unsigned count) { return count == 32 ? buffer : nullptr; }
void runtime_write(const char* s, int len) { if (s && len == 3 && s[0] == 'a') called += len; }
template <typename Function>
FARPROC as_farproc(Function original) {
    static_assert(sizeof(Function) == sizeof(FARPROC), "same ABI pointer width");
    FARPROC result = nullptr;
    std::memcpy(&result, &original, sizeof(result));
    return result;
}
int main() {
    FARPROC symbol = as_farproc(&runtime_malloc);
    static_assert(sizeof(Alloc) == sizeof(FARPROC), "same ABI pointer width");
    Alloc alloc = nullptr;
    std::memcpy(&alloc, &symbol, sizeof(alloc));
    if (alloc(32) != buffer) return 1;
    symbol = as_farproc(&runtime_write);
    static_assert(sizeof(ConsoleWriter) == sizeof(FARPROC), "same ABI pointer width");
    ConsoleWriter writer = nullptr;
    std::memcpy(&writer, &symbol, sizeof(writer));
    writer("abc", 3);
    return called == 3 ? 0 : 2;
}
''', encoding='utf-8')
    exe = tmp_path / 'pointer_test'
    subprocess.run(['g++', '-std=c++11', '-O2', '-Wall', '-Wextra',
                    '-Wcast-function-type', '-Werror=cast-function-type',
                    str(source), '-o', str(exe)], check=True, capture_output=True, text=True)
    subprocess.run([str(exe)], check=True, capture_output=True, text=True)

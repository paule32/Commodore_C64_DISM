"""Stage486: Linux ELF32/ELF64 backend and build-target menu regressions."""
import ast
import os
from pathlib import Path
import platform
import struct
import subprocess

import pytest

from linux_elf import LinuxELFError, assemble_linux_elf, link_elf_objects, write_elf_object
from test_stage446_real_pe_link import linkers


@pytest.fixture(scope='module')
def asm():
    return linkers()


@pytest.mark.parametrize('bits', (32, 64))
def test_elf_object_header_and_executable(asm, bits):
    if bits == 32:
        source = 'section .text\nentry _start\n_start:\nmov eax,1\nmov ebx,42\nint 0x80\n'
    else:
        source = 'section .text\nentry _start\n_start:\nmov rax,60\nmov rdi,42\nsyscall\n'
    obj, binary = assemble_linux_elf(
        source, bits=bits, filename='main.asm',
        assembler32=asm['assemble_pe32_object_source'],
        assembler64=asm['assemble_pe64_object_source'],
    )
    elf_class = 1 if bits == 32 else 2
    machine = 3 if bits == 32 else 62
    assert obj[:6] == binary[:6] == b'\x7fELF' + bytes((elf_class, 1))
    assert struct.unpack_from('<H', obj, 16)[0] == 1  # ET_REL
    assert struct.unpack_from('<H', binary, 16)[0] == 2  # ET_EXEC
    assert struct.unpack_from('<H', binary, 18)[0] == machine
    assert b'_start\0' in obj
    assert len(binary) > 4100


def test_real_linux_amd64_execution(asm, tmp_path):
    if not platform.system().lower() == 'linux' or platform.machine() not in ('x86_64', 'amd64'):
        pytest.skip('native Linux x86-64 execution only')
    source = ('section .text\nentry _start\n_start:\n'
              'mov rax,60\nmov rdi,42\nsyscall\n')
    _, exe = assemble_linux_elf(source, bits=64, filename='test.asm',
                                assembler32=asm['assemble_pe32_object_source'],
                                assembler64=asm['assemble_pe64_object_source'])
    output = tmp_path / 'return42.elf64'
    output.write_bytes(exe)
    output.chmod(0o755)
    assert subprocess.run([str(output)], check=False, timeout=3).returncode == 42


@pytest.mark.parametrize('bits', (32, 64))
def test_link_undefined_symbols_two_objects(asm, bits):
    assemble = asm[f'assemble_pe{bits}_object_source']
    entry = 'section .text\nentry _start\n_start:\ncall helper\nret\n'
    helper = 'section .text\nhelper:\nret\n'
    primary = write_elf_object(assemble(entry), bits=bits)
    secondary = write_elf_object(assemble(helper), bits=bits)
    with pytest.raises(LinuxELFError, match='Ungeloestes'):
        link_elf_objects((primary,), bits=bits)
    program = link_elf_objects((primary, secondary), bits=bits)
    assert program[:4] == b'\x7fELF'


@pytest.mark.parametrize('bits', (32, 64))
def test_data_relocations_and_phdr(asm, bits):
    if bits == 32:
        source = ('section .text\nentry _start\n_start:\n'
                  'mov eax,4\nmov ebx,1\nmov ecx,msg\nmov edx,3\nint 0x80\n'
                  'mov eax,1\nmov ebx,0\nint 0x80\n'
                  'section .data\nmsg:\ndb 72,105,10\n')
    else:
        source = ('section .text\nentry _start\n_start:\n'
                  'mov rax,1\nmov rdi,1\nmov rsi,msg\nmov rdx,3\nsyscall\n'
                  'mov rax,60\nmov rdi,0\nsyscall\n'
                  'section .data\nmsg:\ndb 72,105,10\n')
    obj, exe = assemble_linux_elf(source, bits=bits, filename='print.asm',
                                  assembler32=asm['assemble_pe32_object_source'],
                                  assembler64=asm['assemble_pe64_object_source'])
    assert b'Hi\n' in exe
    assert (b'.rela.text' if bits == 64 else b'.rel.text') in obj
    assert struct.unpack_from('<H', exe, 44 if bits == 32 else 56)[0] == 2
    if bits == 64 and platform.system() == 'Linux' and platform.machine() == 'x86_64':
        out = Path('/tmp/d64_stage486_exec_test.elf64')
        try:
            out.write_bytes(exe); out.chmod(0o700)
            assert subprocess.check_output([str(out)], timeout=3) == b'Hi\n'
        finally:
            out.unlink(missing_ok=True)


def test_macro_include_nested_linux_elf64(asm, tmp_path):
    (tmp_path / 'syscalls.inc').write_text('%define EXIT_NR 60\n', encoding='utf-8')
    src = '%include "syscalls.inc"\nsection .text\nentry _start\n_start:\nmov rax,EXIT_NR\nmov rdi,0\nsyscall\n'
    obj, exe = assemble_linux_elf(src, bits=64, filename=str(tmp_path / 'main.asm'),
                                  assembler32=asm['assemble_pe32_object_source'],
                                  assembler64=asm['assemble_pe64_object_source'], include_dirs=(tmp_path,))
    assert b'\xb8' in obj and exe[:4] == b'\x7fELF'


def test_import_directive_not_silently_linked(asm):
    source = 'section .text\nentry _start\nimport Win32Call,"kernel32.dll","ExitProcess"\n_start:\nret\n'
    with pytest.raises(LinuxELFError, match='Windows-IMPORT'):
        assemble_linux_elf(source, bits=32, filename='bad.asm',
                           assembler32=asm['assemble_pe32_object_source'],
                           assembler64=asm['assemble_pe64_object_source'])


def test_new_menu_targets_and_build_order():
    source = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
    left = source.index('self.build_menu = self.main_menu_bar.addMenu("&Erstellen")')
    end = source.index('self.build_menu.aboutToShow.connect', left)
    menu = source[left:end]
    assert menu.index('"Kompilieren + Linken"') < menu.index('QAction("Kompilieren",')
    assert menu.index('"linux32", "Linux Ubuntu 22.04  32-Bit"') < menu.index('"linux64", "Linux Ubuntu 22.04  64-Bit"')
    assert menu.index('"linux64", "Linux Ubuntu 22.04  64-Bit"') < menu.index('"c64", "Commodore C= 64"')
    assert menu.index('"AMIGA 500"') < menu.index('QAction("Starten",')
    assert source.count('Linux Ubuntu 22.04 32-Bit') >= 2
    assert 'elif document.build_target in {"linux32", "linux64"}' in source


def test_byte_encoder_syscall():
    source = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf8')
    assert 'if mnemonic == "syscall" and not ops: return b"\\x0f\\x05"' in source

"""Stage479 checks independent of the unavailable Windows/PyQt UI runtime."""
from pathlib import Path
from types import SimpleNamespace
import ast
import os

import pytest

from windows_asm_att import att_to_intel, contains_att_syntax
from windows_asm_macros import preprocess_windows_asm
from test_stage446_real_pe_link import linkers


def _output_path_function():
    main = Path(__file__).with_name('d64_dism.py')
    tree = ast.parse(main.read_text(encoding='utf-8'))
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == '_project_document_output_path')
    source = ast.get_source_segment(main.read_text(encoding='utf-8'), node)
    ns = {'Path': Path, 'os': os, 'AssemblerError': ValueError}
    exec(source, ns)
    return ns['_project_document_output_path']


def test_split_output_with_relative_source_root(tmp_path):
    root = tmp_path / 'project'; source_dir=root / 'src'; source_dir.mkdir(parents=True)
    project_path=root / 'main.pro'
    owner=SimpleNamespace(
        project_windows_assembler_cache={'pe32':str(root/'tmp'/'asm')},
        project_windows_output_directories={'pe32':str(root/'bin')},
        project_windows_relative_paths={'pe32': {'output': True}},
        _project_windows_base_directory=lambda:root,
    )
    document=SimpleNamespace(path=source_dir/'Form1.wfm', build_target='pe32', window=lambda:owner)
    fn=_output_path_function()
    assert fn(document,'Form1.generated.pe32.asm') == (source_dir/'tmp'/'asm'/'Form1.generated.pe32.asm').resolve()
    assert fn(document,'Form1.exe') == (source_dir/'bin'/'Form1.exe').resolve()
    assert fn(document,'Form1.o') == (source_dir/'bin'/'Form1.o').resolve()


def test_absolute_output_modes_and_legacy_default(tmp_path):
    owner=SimpleNamespace(project_windows_assembler_cache={'pe64':str(tmp_path/'asm')},
                          project_windows_output_directories={'pe64':str(tmp_path/'bin')},
                          project_windows_relative_paths={'pe64':{'output': False}},
                          _project_windows_base_directory=lambda:tmp_path/'project')
    document=SimpleNamespace(path=tmp_path/'folder'/'file.prg',build_target='pe64',window=lambda:owner)
    fn=_output_path_function()
    assert fn(document,'file.generated.pe64.asm') == (tmp_path/'asm'/'file.generated.pe64.asm').resolve()
    assert fn(document,'file.exe') == (tmp_path/'bin'/'file.exe').resolve()
    owner.project_windows_assembler_cache['pe64']=''
    owner.project_windows_output_directories['pe64']=''
    assert fn(document,'file.generated.pe64.asm') == (tmp_path/'folder'/'file.generated.pe64.asm')


def test_att_translation_instruction_memory_and_immediate():
    text='.att_syntax\n.text\n_start:\n movl $42, %eax\n addl $3, %eax\n movl -4(%ebp), %ecx\n ret\n'
    translated=att_to_intel(text)
    assert 'section .text' in translated
    assert 'mov eax, 42' in translated
    assert 'mov ecx, dword ptr [ebp-4]' in translated
    assert contains_att_syntax(text)
    assert not contains_att_syntax(translated)


@pytest.mark.parametrize('target', ['pe32','pe64'])
def test_att_assembler_and_linker(target, tmp_path):
    asm=att_to_intel('.att_syntax\n.section .text\nentry _start\n_start:\n movl $42, %eax\n ret\n')
    ns=linkers()
    obj=ns[f'assemble_{target}_object_source'](asm,filename=str(tmp_path/'app.asm'))
    assert obj.code.startswith(b'\xb8\x2a\x00\x00\x00')
    coff=ns[f'write_coff{64 if target=="pe64" else 32}_object'](obj)
    exe=ns[f'link_coff{64 if target=="pe64" else 32}_objects']((coff,),entry_symbol='_start',gui=True)
    assert exe.executable.startswith(b'MZ')


def test_att_include_and_macros_preserved(tmp_path):
    file=tmp_path/'main.asm'
    (tmp_path/'custom.inc').write_text('%define VAL 7\nmovl $VAL, %eax\n',encoding='utf8')
    text='%include "custom.inc"\n.att_syntax\nsection .text\nentry _start\n_start:\nret\n'
    expanded=preprocess_windows_asm(text,filename=str(file)).source
    translated=att_to_intel(expanded)
    assert 'mov eax, 7' in translated
    assert '%include' not in translated

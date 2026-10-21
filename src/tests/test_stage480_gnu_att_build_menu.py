"""Stage 480: GNU AT&T output/input, safe metadata, and Build menu wiring."""
from pathlib import Path
import ast
import pytest

from windows_asm_att import att_to_intel, intel_to_att, contains_att_syntax
from test_stage446_real_pe_link import linkers


def test_generated_att_roundtrip_keeps_compiler_machine_code():
    intel = ('section .text\nentry _start\n_start:\n'
             '  push ebp\n  mov ebp, esp\n  mov eax, 42\n  pop ebp\n  ret\n'
             'section .data\nmessage:\n  db 65, 66, 0\n')
    gnu = intel_to_att(intel, target='pe32')
    assert '.att_syntax' in gnu
    assert 'movl $42, %eax' in gnu
    assert '.byte 65, 66, 0' in gnu
    assert '.d64_entry _start' in gnu
    assert att_to_intel(gnu).count('entry _start') == 1
    ns = linkers()
    fn = ns['assemble_pe32_object_source']
    old_obj = fn(intel)
    new_obj = fn(att_to_intel(gnu))
    assert old_obj.code == new_obj.code
    assert old_obj.data == new_obj.data


@pytest.mark.parametrize('arch', ['pe32', 'pe64'])
def test_gnu_zero_fill_and_bss_have_real_coff_bytes(arch):
    gnu = ('.att_syntax\n.data\ntext:\n.byte 41\n.zero 3\n.fill 2, 2, 0x1234\n'
           '.bss\nreserve:\n.zero 12\n.text\nentry _start\n_start:\n'
           'movl $42, %eax\nretq\n')
    converted = att_to_intel(gnu)
    assert 'db 0, 0, 0' in converted
    assert 'dw 4660, 4660' in converted
    assert 'resb 12' in converted
    ns=linkers()
    obj=ns[f'assemble_{arch}_object_source'](converted)
    assert b'\x29\x00\x00\x00\x34\x12\x34\x12' in obj.data
    assert obj.code.startswith(b'\xb8\x2a\x00\x00\x00')
    coff=ns[f'write_coff{64 if arch=="pe64" else 32}_object'](obj)
    exe=ns[f'link_coff{64 if arch=="pe64" else 32}_objects']((coff,),entry_symbol='_start',gui=True)
    assert exe.executable.startswith(b'MZ')


def test_gnu_mnemonics_and_intel_blocks():
    source = ('.att_syntax\ncallq target\nmovabsq $42, %rax\n'
              '.intel_syntax noprefix\nmov eax, 1\n'
              '.att_syntax prefix\nretq\n')
    text=att_to_intel(source)
    assert 'call target' in text
    assert 'mov rax, 42' in text
    assert 'mov eax, 1' in text
    assert 'ret' in text
    assert 'mov eax, 1' in text


def test_gnu_unsupported_constructions_raise_clear_errors():
    for text in ('.att_syntax\n.p2align 50', '.att_syntax\n.fill 2,3,1',
                 '.att_syntax\n.impossible 3', '.att_syntax\nimull $2, %eax, %ecx'):
        with pytest.raises(ValueError):
            att_to_intel(text)


def test_windows_assembly_mode_detection_does_not_confuse_native_intel_sections():
    assert not contains_att_syntax('section .data\n.section .text\nmov eax, 1\n')
    assert contains_att_syntax('.att_syntax\nmovl $12, %eax')
    assert contains_att_syntax('movl $12, %eax')


def _stage_methods():
    source=Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    app=next(n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=='D64DismMainWindow') if any(isinstance(n,ast.ClassDef) and n.name=='D64DismMainWindow' for n in ast.walk(tree)) else None
    return tree,source


def test_build_menu_actions_and_callbacks_available():
    tree,source = _stage_methods()
    assert 'self.main_menu_bar.addMenu("&Projekt")' in source
    assert 'self.main_menu_bar.addMenu("&Erstellen")' in source
    assert source.index('addMenu("&Projekt")') < source.index('addMenu("&Erstellen")') < source.index('addMenu("&Server")')
    for text in ('Kompilieren + Linken','Kompilieren','Windows PE 32-Bit','Windows PE 64-Bit','Commodore C= 64','AMIGA 500'):
        assert text in source
    for method in ('_build_menu_compile','_build_menu_select_target','_build_menu_sync_target','_build_menu_target_supported'):
        assert any(isinstance(n,ast.FunctionDef) and n.name==method for n in ast.walk(tree))
    assert 'self._launch_assembled_document(document)' not in ast.get_source_segment(source, next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_build_menu_compile'))


def test_build_target_compatibility_is_explicit():
    tree,source=_stage_methods()
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_build_menu_target_supported')
    # pure staticmethod -> can execute it without PyQt
    namespace={}
    exec(ast.get_source_segment(source,node).replace('DocumentEditor','object'),namespace)
    fn=namespace[node.name]
    class Doc:
        is_basic_document=False
        is_dbase_document=False
        is_prolog_document=False
        is_lisp_document=False
        is_logo_document=False
    d=Doc();d.is_dbase_document=True
    assert fn(d,'pe32') and fn(d,'pe64') and not fn(d,'amiga') and not fn(d,'c64')
    d.is_dbase_document=False;d.is_basic_document=True
    assert fn(d,'c64') and not fn(d,'pe32')


def test_gnu_include_recurses_through_project_search_path(tmp_path):
    from windows_asm_macros import preprocess_windows_asm
    project=tmp_path/'source';project.mkdir()
    inputs=tmp_path/'inc';inputs.mkdir()
    (inputs/'inner.inc').write_text('movl $42, %eax\n',encoding='utf8')
    (inputs/'outer.inc').write_text('.include "inner.inc"\n',encoding='utf8')
    main=project/'hello.s'
    main.write_text('.att_syntax\n.include "outer.inc"\nretq\n',encoding='utf8')
    result=preprocess_windows_asm(main.read_text(),filename=str(main),include_dirs=[inputs])
    assert len(result.locations) >= 3
    assert 'movl $42, %eax' in result.source
    assert any(loc[0].endswith('inner.inc') for loc in result.locations)
    assert 'mov eax, 42' in att_to_intel(result.source)

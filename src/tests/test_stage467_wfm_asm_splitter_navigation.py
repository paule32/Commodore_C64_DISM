"""Stage 467: WFM vertical source/assembler split + source line links."""
import ast
import re
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage466_wfm_top_level_program import USER_SOURCE
from test_stage446_real_pe_link import linkers

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_source_line_comments_from_header_and_methods(target):
    asm = compile_slot_optimized(target, False, True, USER_SOURCE)
    preamble = asm.split('__dbase_wfm_proc___dbase_top_level__:', 1)[1].split(
        '; END WFM PROCEDURE/FUNCTION: __dbase_top_level__', 1)[0]
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 1\s*$', preamble)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 3\s*$', preamble)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 6\s*$', preamble)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 7\s*$', preamble)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 8\s*$', preamble)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 10\s*$', preamble)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 15\s*$', preamble)
    method = asm.split('__dbase_wfm_proc_Button1_onClick:', 1)[1].split(
        '; END WFM PROCEDURE/FUNCTION: Button1_onClick', 1)[0]
    original_lines = USER_SOURCE.splitlines()
    print_line = original_lines.index('        ? VARTYPE(xyz)') + 1
    return_line = original_lines.index('        RETURN') + 1
    assert f'; Quellcode Zeile: {print_line}' in method
    assert f'; Quellcode Zeile: {return_line}' in method
    assert '; Quellcode Zeile: 0' not in asm
    # Comments must remain accepted by the actual internal assembler/linker.
    lk = linkers()
    obj = lk[f'assemble_{target}_object_source'](asm)
    coff = lk[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = lk[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert exe.executable.startswith(b'MZ')


def test_comments_keep_original_line_numbers_after_quotes_and_multiline_comments():
    source = '''STORE "x && y" TO Text
/* block comment
   IF fake
*/
? Text && actual comment
CLASS Form1 OF FORM
    PROCEDURE OnClick()
        STORE 9 TO x
        /* method block
        multiline */
        ? x
        RETURN
ENDCLASS
'''
    asm = compile_slot_optimized('pe32', False, True, source)
    before = asm.split('__dbase_wfm_proc___dbase_top_level__:', 1)[1].split(
        '; END WFM PROCEDURE/FUNCTION: __dbase_top_level__', 1)[0]
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 1\s*$', before)
    assert re.search(r'(?m)^\s*; Quellcode Zeile: 5\s*$', before)
    assert 'Quellcode Zeile: 3' not in before
    method = asm.split('__dbase_wfm_proc_OnClick:', 1)[1].split(
        '; END WFM PROCEDURE/FUNCTION: OnClick', 1)[0]
    assert '; Quellcode Zeile: 8' in method
    assert '; Quellcode Zeile: 11' in method
    assert '; Quellcode Zeile: 12' in method
    assert 'Quellcode Zeile: 9' not in method


def test_wfm_designer_contains_nested_vertical_splitter_but_no_assembler_tab():
    start = SOURCE.index('        def _ensure_dbase_form_designer(self) -> None:')
    end = SOURCE.index('        def _apply_dbase_form_source_outline_theme(', start)
    method = SOURCE[start:end]
    assert 'source_assembly_splitter = QSplitter(Qt.Vertical, source_page)' in method
    assert 'source_assembly_splitter.addWidget(source_splitter)' in method
    assert 'source_assembly_splitter.addWidget(assembly_host)' in method
    assert 'source_assembly_splitter.setChildrenCollapsible(False)' in method
    assert 'source_assembly_splitter.setSizes([620, 300])' in method
    assert 'source_layout.addWidget(source_assembly_splitter, 1)' in method
    assert 'form_tabs.addTab(source_page, "Quellcode")' in method
    assert 'form_tabs.addTab(assembly_page' not in method
    assert 'generated_assembly_editor.viewport().installEventFilter' in method
    assert 'self.dbase_form_source_assembly_splitter = source_assembly_splitter' in method
    # Compile must not send the user to the old assembler tab.
    compile_method = SOURCE[SOURCE.index('        def compile_dbase_form(self) -> bool:'):
                            SOURCE.index('        def assemble_dbase_form(self) -> bool:')]
    assert 'setCurrentWidget(self.dbase_form_source_page)' in compile_method
    assert 'setCurrentWidget(self.dbase_form_assembly_page)' not in compile_method


def test_asm_marker_hit_detection_only_on_matching_comment_line():
    start = SOURCE.index('        def _dbase_form_asm_source_line_at(self, position) -> int:')
    end = SOURCE.index('        @staticmethod\n        def _dbase_form_timer_default_procedure', start)
    code = textwrap.dedent(SOURCE[start:end])
    namespace = {'re': re}
    exec(compile(code, '<stage467-asm-hit>', 'exec'), namespace)
    match = namespace['_dbase_form_asm_source_line_at']

    class Editor:
        def __init__(self, line):
            self.line = line
        def cursorForPosition(self, position):
            assert position == 'point'
            return SimpleNamespace(block=lambda: SimpleNamespace(text=lambda: self.line))
    stub = SimpleNamespace(dbase_form_build_document=SimpleNamespace(
        generated_assembly_editor=Editor('    ; Quellcode Zeile: 152')))
    assert match(stub, 'point') == 152
    stub.dbase_form_build_document.generated_assembly_editor.line = '    mov eax, 152'
    assert match(stub, 'point') == 0
    stub.dbase_form_build_document.generated_assembly_editor.line = '    ; Other comment'
    assert match(stub, 'point') == 0
    stub.dbase_form_build_document.generated_assembly_editor.line = '    ; Quellcode Zeile: 0'
    assert match(stub, 'point') == 0

"""Stage 481: WFM GNU section regression and form-aware Build/Start menu."""
from __future__ import annotations

import ast
from pathlib import Path
from types import MethodType, SimpleNamespace

from windows_asm_att import intel_to_att, att_to_intel


def test_real_wfm_dot_section_roundtrip():
    # WFM generator intentionally uses '.section .text', not 'section .text'.
    intel = (
        '.section .text\n'
        'entry __d64_wfm_entry\n'
        '__d64_wfm_entry:\n'
        '  mov eax, 42\n'
        '  ret\n'
        '.section .data\n'
        'number:\n'
        '  dd 123\n'
        '.section .bss\n'
        'temporary:\n'
        '  resb 4\n'
    )
    att = intel_to_att(intel, target='pe32')
    assert '$.text' not in att and '$.data' not in att
    assert '\n.text\n' in att and '\n.data\n' in att and '\n.bss\n' in att
    restored = att_to_intel(att)
    assert 'section .text' in restored and 'section .data' in restored
    assert 'section .bss' in restored
    assert 'mov eax, 42' in restored


def test_old_stage480_bad_section_is_supported_without_misassembling():
    assert att_to_intel('.att_syntax\n.section $.text\nmovl $2, %eax\n') == (
        '; AT&T syntax\nsection .text\nmov eax, 2\n'
    )


def test_wfm_section_roundtrip_produces_real_coff(tmp_path):
    from test_stage446_real_pe_link import linkers
    ns = linkers()
    for target in ('pe32', 'pe64'):
        intel = (
            '.section .text\nentry _start\n_start:\nmov eax, 42\nret\n'
            '.section .data\nmessage:\ndb 65, 0\n'
        )
        source = att_to_intel(intel_to_att(intel, target=target))
        obj = ns[f'assemble_{target}_object_source'](source)
        writer = ns['write_coff64_object' if target == 'pe64' else 'write_coff32_object']
        linker = ns['link_coff64_objects' if target == 'pe64' else 'link_coff32_objects']
        result = linker((writer(obj),), entry_symbol='_start', gui=True)
        assert result.executable.startswith(b'MZ')


def _methods():
    source = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    names = {
        '_build_menu_active_document', '_build_menu_can_start',
        '_build_menu_sync_target', '_build_menu_compile', '_build_menu_start',
    }
    nodes = {node.name: node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name in names}
    assert nodes.keys() == names
    ns = {'Path': Path}
    for name in names:
        exec(compile(ast.Module(body=[nodes[name]], type_ignores=[]), '<stage481>', 'exec'), ns)
    return ns, source


class _Action:
    def __init__(self):
        self.enabled = None
        self.checked = False

    def setEnabled(self, value):
        self.enabled = bool(value)

    def isEnabled(self):
        return bool(self.enabled)

    def blockSignals(self, state):
        return False

    def setChecked(self, value):
        self.checked = bool(value)


class _Doc:
    def __init__(self):
        self.build_target = 'pe32'
        self.is_build_document = True
        self.display_name = 'Form1.wfm'
        self.assembled_program_path = None
        self.is_dbase_document = True
        self.is_basic_document = False
        self.is_prolog_document = False
        self.is_lisp_document = False
        self.is_logo_document = False
        self.is_modified = False


def test_form_designer_menu_compiles_links_and_starts_only_ready_artifact(tmp_path):
    ns, source = _methods()
    # Real menu has a separator after AMIGA 500, followed by Starten.
    creation = source[source.index('self.build_menu = self.main_menu_bar.addMenu("&Erstellen")'):]
    assert creation.index('"Kompilieren + Linken"') < creation.index('"Kompilieren"')
    assert creation.index('"AMIGA 500"') < creation.index('self.build_menu.addSeparator()', creation.index('"AMIGA 500"')) < creation.index('QAction("Starten"')

    form = _Doc()
    foreign = _Doc()
    foreign.display_name = 'Other.prg'
    start_action = _Action()
    form_start = _Action()
    form_start.setEnabled(False)
    target_actions = {'pe32': _Action(), 'pe64': _Action()}
    status = SimpleNamespace(showMessage=lambda *a: None)
    ctx = SimpleNamespace(
        document_tabs=object(),
        dbase_form_build_document=form,
        dbase_form_current_path=tmp_path/'Form1.wfm',
        dbase_form_start_button=form_start,
        dbase_form_target_combo=SimpleNamespace(currentData=lambda: 'pe32'),
        build_target_actions=target_actions,
        build_compile_action=_Action(), build_compile_link_action=_Action(),
        build_start_action=start_action,
        _build_menu_form_ready_source=None,
        _build_menu_form_ready_path=None,
        _build_menu_form_ready_target=None,
        _build_menu_ready_document=None,
        _build_menu_ready_path=None,
        _build_menu_ready_target=None,
        statusBar=lambda: status,
        current_document=lambda: foreign,
        _dbase_form_is_active=lambda: True,
        _serialize_dbase_form_wfm=lambda: 'CLASS Form1 OF FORM\nENDCLASS\n',
        log=lambda *a: None,
        show_error=lambda *a: (_ for _ in ()).throw(AssertionError('Unexpected error')),
        start_dbase_form=lambda: True,
        _build_menu_target_supported=lambda d, t: t in ('pe32', 'pe64'),
    )
    for name in ('_build_menu_active_document','_build_menu_can_start',
                 '_build_menu_sync_target','_build_menu_compile','_build_menu_start'):
        setattr(ctx, name, MethodType(ns[name], ctx))

    def compile_form():
        form_start.setEnabled(False)
        return True

    def assemble_form():
        output = tmp_path/'Form1.exe'
        output.write_bytes(b'MZbinary')
        form.assembled_program_path = output
        form_start.setEnabled(True)
        ctx._build_menu_form_ready_source = ctx._serialize_dbase_form_wfm()
        ctx._build_menu_form_ready_path = ctx.dbase_form_current_path.resolve()
        ctx._build_menu_form_ready_target = form.build_target
        return True

    ctx.compile_dbase_form = compile_form
    ctx.assemble_dbase_form = assemble_form
    ctx._build_menu_sync_target()
    assert ctx.build_compile_action.enabled and ctx.build_compile_link_action.enabled
    assert not start_action.enabled
    assert ctx._build_menu_compile(link=False)
    assert not start_action.enabled
    assert ctx._build_menu_compile(link=True)
    assert start_action.enabled
    assert ctx._build_menu_start()
    ctx._serialize_dbase_form_wfm = lambda: 'CLASS Form1 OF FORM\n? "Changed"\nENDCLASS\n'
    ctx._build_menu_sync_target()
    assert not start_action.enabled


def test_document_menu_and_form_paths_are_separated():
    ns, source = _methods()
    assert 'self.compile_dbase_form()' in source
    assert 'self.assemble_dbase_form()' in source
    assert 'self._launch_assembled_document(document)' in source
    assert 'self.start_dbase_form()' in source
    assert 'self._build_menu_sync_target()' in source[source.index('def _update_document_actions'):source.index('def renumber_c64_basic_document')]

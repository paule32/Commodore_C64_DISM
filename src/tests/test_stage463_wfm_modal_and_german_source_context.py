"""Stage 463: WFM modal parameter/constructor and German context-menu invariants."""
from __future__ import annotations
import ast
import re
from pathlib import Path
import pytest
from test_stage446_real_pe_link import linkers
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized

ROOT = Path(__file__).parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf8')
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf8')
DEFS = (ROOT / 'd64qt5/d64qt5_bridge.def').read_text(encoding='utf8')

class FakeAction:
    def __init__(self, text, shortcut=None, separator=False):
        self._text, self._shortcut, self._separator = text, shortcut, separator
        self.callback = object()
        self.enabled = True
    def text(self): return self._text
    def setText(self, text): self._text = text
    def shortcut(self): return self._shortcut
    def isSeparator(self): return self._separator

class FakeMenu:
    def __init__(self, actions): self._actions = actions
    def actions(self): return self._actions


def _translate_source_menu_function():
    module = ast.parse(SOURCE)
    mapping = next(n for n in module.body if isinstance(n, ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id == '_SOURCE_EDITOR_CONTEXT_TRANSLATIONS' for t in n.targets))
    fn = next(n for n in module.body if isinstance(n,ast.FunctionDef)
              and n.name == '_translate_source_editor_context_menu')
    env={}
    exec(compile(ast.Module(body=[mapping,fn],type_ignores=[]),'<stage463 context menu>','exec'),env)
    return env['_translate_source_editor_context_menu']


def test_german_menu_text_and_shortcuts_keep_original_actions_and_separators():
    labels = ['Undo\tCtrl+Z','Redo\tCtrl+Y','', 'Cut\tCtrl+X',
              'Copy\tCtrl+C','Paste\tCtrl+V','Delete','', 'Select All\tCtrl+A']
    keys = ['CTRL+Z','CTRL+Y',None,'CTRL+X','CTRL+C','CTRL+V',None,None,'CTRL+A']
    a=[FakeAction(label,key,label=='') for label,key in zip(labels,keys)]
    menu = FakeMenu(a)
    _translate_source_menu_function()(menu)
    assert [x.text() for x in a] == [
        'Rückgängig\tSTRG + Z','Wiederherstellen\tSTRG + Y','',
        'Ausschneiden\tSTRG + X','Kopieren\tSTRG + C','Einfügen\tSTRG + V',
        'Löschen','', 'Alles auswählen\tSTRG + A'
    ]
    assert [x.shortcut() for x in a] == keys
    assert menu.actions() is a
    assert [x.isSeparator() for x in a] == [False,False,True,False,False,False,False,True,False]


def test_special_source_context_menu_and_other_source_editors_use_translator():
    for name in ('ResourceCodeEditor','ApacheConfigTextEdit','DoxyCodeEditor','LocalizeCodeEditor'):
        assert f'class {name}(GermanSourceEditorContextMenuMixin, QPlainTextEdit):' in SOURCE
    assert 'standard_menu = self.createStandardContextMenu()\n            _translate_source_editor_context_menu(standard_menu)' in SOURCE
    assert 'menu.addSeparator()' in SOURCE
    assert '_execute_german_source_editor_context_menu(' in SOURCE


FORM = '''** END HEADER -- do not remove this line
// Generated on 19.10.2026
//
PARAMETER bmodal
LOCAL B
B = NEW Form1(51,4)
if bmodal = .T.
   B.ReadModal()
else
   B.Open()
endif
CLASS Form1 OF FORM
    PROCEDURE __init__(p1,p2)
        RETURN
    PROCEDURE __main__()
        RETURN
ENDCLASS
'''


@pytest.mark.parametrize('target',['pe32','pe64'])
def test_modal_runtime_call_is_linkable_in_wfm(target):
    asm = compile_slot_optimized(target,False,False,FORM)
    assert '    call DBaseQtWfmModalParameter' in asm
    assert '    call DBaseQtFormRun' in asm
    assert '    call DBaseQtFormOpen' in asm
    # The legacy console shell remains present but is not the PE entrypoint.
    entry = asm.split('__d64_wfm_entry:', 1)[1].split('; Stage 133:', 1)[0]
    assert '    call DBaseQtExec\n' not in entry
    assert '    call __dbase_wfm_' in asm
    funcs=linkers()
    obj=funcs[f'assemble_{target}_object_source'](asm)
    bits=32 if target=='pe32' else 64
    coff=funcs[f'write_coff{bits}_object'](obj)
    result=funcs[f'link_coff{bits}_objects']((coff,),entry_symbol='__d64_wfm_entry',gui=True)
    assert result.executable[:2] == b'MZ'
    assert b'DBaseQtFormRun' in result.executable
    assert b'DBaseQtWfmModalParameter' in result.executable


@pytest.mark.parametrize('target',['pe32','pe64'])
def test_constructor_arg_mismatch_is_reported(target):
    source = FORM.replace('__init__(p1,p2)','__init__(p1)')
    with pytest.raises(Exception,match=r'__init__.*erwartet 1.*liefert aber 2'):
        compile_slot_optimized(target,False,False,source)
    source = FORM.replace('__init__(p1,p2)','__init__()')
    with pytest.raises(Exception,match=r'__init__.*erwartet 0.*2 Argumente'):
        compile_slot_optimized(target,False,False,source)


def test_runtime_modes_exported_without_changing_core_ordinals():
    assert 'DBaseQtWfmModalParameter @1013' in DEFS
    assert 'DBaseQtFormRun @1014' in DEFS
    assert 'CommandLineToArgvW' in BRIDGE
    assert 'g_workstation_mode_enabled' in BRIDGE
    assert 'D64_WFM_IDE_LAUNCH' in BRIDGE
    assert 'Qt::ApplicationModal' in BRIDGE

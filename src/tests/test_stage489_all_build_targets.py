"""Stage 489: every build-menu target can be selected without silent PE32 fallback."""
from __future__ import annotations

import ast
from pathlib import Path
from types import MethodType, SimpleNamespace

SOURCE = Path(__file__).with_name('d64_dism.py').read_text('utf-8')


def methods():
    tree=ast.parse(SOURCE)
    wanted={'_build_menu_sync_target','_build_menu_select_target',
            '_build_menu_target_supported','_build_menu_compile'}
    funcs={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in wanted}
    assert set(funcs)==wanted
    ns={'Path':Path}
    for name,node in funcs.items():
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<stage489>','exec'),ns)
    return ns


class Action:
    def __init__(self,name):
        self.label=name;self.checked=False;self.enabled=False;self.props={}
    def blockSignals(self,blocked):return False
    def setChecked(self,val):self.checked=bool(val)
    def setEnabled(self,val):self.enabled=bool(val)
    def setText(self,text):self.label=text
    def text(self):return self.label
    def setProperty(self,k,v):self.props[k]=v


class Doc:
    is_build_document=True
    is_basic_document=False
    is_dbase_document=True
    is_assembler_document=False
    is_lisp_document=False
    is_prolog_document=False
    is_logo_document=False
    display_name='Form1.wfm'
    build_target='pe32'
    def set_build_target(self,target): self.build_target=target


class Combo:
    values=('pe32','pe64','linux32','linux64','c64','amiga')
    def __init__(self,doc):self.doc=doc;self.index=0
    def findData(self,key):return self.values.index(key) if key in self.values else -1
    def currentData(self):return self.values[self.index]
    def setCurrentIndex(self,index):
        self.index=index
        self.doc.build_target=self.currentData()
        self.doc.build_menu_requested_target=self.currentData()


def context(*,form=False,doc=True):
    ns=methods()
    target_names={'pe32':'Windows PE 32-Bit', 'pe64':'Windows PE 64-Bit',
                  'linux32':'Linux Ubuntu 22.04  32-Bit','linux64':'Linux Ubuntu 22.04  64-Bit',
                  'c64':'Commodore C= 64','amiga':'AMIGA 500'}
    d=Doc() if doc else None
    actions={key:Action(label) for key,label in target_names.items()}
    logs=[]; errors=[]
    ctx=SimpleNamespace(
        _build_menu_selected_target='pe32',build_target_actions=actions,
        build_target_action_labels=target_names,build_compile_action=Action('Compile'),
        build_compile_link_action=Action('Link'),build_start_action=Action('Start'),
        _build_menu_ready_document=None,_build_menu_ready_path=None,
        _build_menu_ready_target=None,_build_menu_form_ready_source=None,
        _build_menu_form_ready_path=None,_build_menu_form_ready_target=None,
        dbase_form_target_combo=Combo(d) if d else None,
        _dbase_form_is_active=lambda:form,
        _build_menu_active_document=lambda:d,
        _build_menu_can_start=lambda d:False,
        _build_menu_target_supported=lambda d,t:ns['_build_menu_target_supported'](d,t),
        statusBar=lambda:SimpleNamespace(showMessage=lambda *args:logs.append(args)),
        show_error=lambda *args:errors.append(args),
    )
    for key in ('_build_menu_select_target','_build_menu_sync_target','_build_menu_compile'):
        setattr(ctx,key,MethodType(ns[key],ctx))
    return ctx,d,actions,logs,errors


def check_one(actions,selected):
    assert {k for k,a in actions.items() if a.checked}=={selected}
    assert {k for k,a in actions.items() if a.props.get('compiler_target_selected')}=={selected}
    assert actions[selected].text().startswith('✓ ')
    assert all(not a.text().startswith('✓ ') for k,a in actions.items() if k != selected)


def test_menu_contains_exactly_six_exclusive_checkable_targets():
    menu=SOURCE[SOURCE.index('self.build_menu = self.main_menu_bar.addMenu("&Erstellen")'):]
    assert 'self.build_target_action_group.setExclusive(True)' in menu
    assert menu.count('action.setCheckable(True)',0,menu.index('# Stage 481: Start'))==3
    assert menu.count('self.build_target_action_group.addAction(action)',0,menu.index('# Stage 481: Start'))==3
    assert menu.index('"Kompilieren + Linken"') < menu.index('QAction("Kompilieren",')
    for target in ('pe32','pe64','linux32','linux64','c64','amiga'):
        assert '"'+target+'", ' in menu


def test_user_can_select_all_six_with_open_prg():
    ctx,doc,actions,logs,errors=context(form=False)
    doc.display_name='Test.prg'
    ctx._build_menu_sync_target()
    check_one(actions,'pe32')
    for key in ('pe64','linux32','linux64','amiga','c64','pe32'):
        ctx._build_menu_select_target(key)
        assert doc.build_target==key
        assert doc.build_menu_requested_target==key
        check_one(actions,key)
    assert not errors


def test_all_six_targets_available_with_wfm_form_designer():
    ctx,doc,actions,logs,errors=context(form=True)
    for key in ('pe64','linux32','linux64','amiga','c64','pe32'):
        ctx._build_menu_select_target(key)
        assert ctx.dbase_form_target_combo.currentData()==key
        assert doc.build_target==key
        check_one(actions,key)
    assert not errors
    assert 'target_combo.addItem("AMIGA 500", "amiga")' in SOURCE
    assert 'target_combo.addItem("Commodore C= 64", "c64")' in SOURCE


def test_no_document_target_can_be_preselected_without_error():
    ctx,doc,actions,logs,errors=context(doc=False)
    for key in ('pe64','linux64','amiga','c64','linux32','pe32'):
        ctx._build_menu_select_target(key)
        check_one(actions,key)
    assert not errors
    assert not ctx.build_compile_action.enabled


def test_unsupported_target_keeps_marker_but_refuses_build():
    for target in ('amiga','c64'):
        ctx,doc,actions,logs,errors=context(form=False)
        ctx._build_menu_select_target(target)
        assert not ctx._build_menu_compile(link=True)
        check_one(actions,target)
        assert errors and 'nicht implementiert' in errors[-1][1]
        assert doc.build_target==target


def test_dbase_compiler_no_longer_silently_reverts_to_pe32():
    block=SOURCE[SOURCE.index('def _compile_dbase_document('):SOURCE.index('def _compile_logo_document(')]
    assert 'document.set_build_target("pe32")' not in block
    assert 'noch nicht implementiert' in block
    assert 'if target not in {"pe32", "pe64", "linux32", "linux64"}' in SOURCE


def test_switching_between_documents_restores_individual_target_markers():
    ctx,first,actions,logs,errors=context(form=False)
    first.display_name='Main.prg'
    second=Doc()
    second.display_name='Second.prg'
    active=[first]
    ctx._build_menu_active_document=lambda:active[0]
    ctx._build_menu_select_target('linux64')
    active[0]=second
    ctx._build_menu_sync_target()
    check_one(actions,'pe32')
    ctx._build_menu_select_target('amiga')
    active[0]=first
    ctx._build_menu_sync_target()
    check_one(actions,'linux64')
    active[0]=second
    ctx._build_menu_sync_target()
    check_one(actions,'amiga')
    assert not errors

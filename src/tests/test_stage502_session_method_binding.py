"""Stage 502: SESSION method double-click binds the object and its wrapper."""

from pathlib import Path
import re
import textwrap

import pytest

from d64dbase.session_designer import (
    SESSION_METHODS, bind_session_method, session_method_assignments,
    session_method_binding, session_method_source,
)
from d64dbase.wfm import parse_dbase_wfm


def test_all_methods_get_object_binding_and_matching_function():
    for method in SESSION_METHODS:
        assert session_method_binding('Session1', method) == (
            method, f'CLASS::SESSION1_{method.upper()}'
        )
        lines = session_method_source('Session1', method)
        assert lines[0] == f'    function SESSION1_{method}(param)'
        assert lines[1] == f'        return SESSION::{method}(param)'


def test_bind_is_idempotent_replaces_other_case_and_applies_only_one_session():
    one = {'beforeRelease': 'CLASS::S1_beforeRelease', 'DELETEALIAS': 'CLASS::OLD'}
    two = {}
    assert bind_session_method(one, 'Session1', 'deleteAlias')
    assert one == {
        'beforeRelease': 'CLASS::S1_beforeRelease',
        'deleteAlias': 'CLASS::SESSION1_DELETEALIAS',
    }
    assert not bind_session_method(one, 'Session1', 'deleteAlias')
    assert bind_session_method(two, 'Session2', 'deleteAlias')
    assert two['deleteAlias'] == 'CLASS::SESSION2_DELETEALIAS'
    assert list(one).count('deleteAlias') == 1
    assert session_method_assignments(one) == [
        ('deleteAlias', 'CLASS::SESSION1_DELETEALIAS')
    ]


def test_invalid_name_cannot_inject_source_or_create_binding():
    one = {}
    with pytest.raises(ValueError):
        bind_session_method(one, 'S1)\nENDWITH', 'deleteAlias')
    with pytest.raises(ValueError):
        bind_session_method(one, 'Session1', 'runAnything')
    assert one == {}


def test_method_bindings_parse_as_events_without_changing_other_properties():
    source = '''CLASS ParentForm OF FORM
    THIS.SESSION1 = NEW SESSION(THIS)
    WITH (THIS.SESSION1)
        deleteAlias = CLASS::SESSION1_DELETEALIAS
        addAlias = CLASS::SESSION1_ADDALIAS
        left = 80
        top = 80
        lockRetryCount = 7
        lockRetryInterval = 250
        beforeRelease = CLASS::SESSION1_beforeRelease
    ENDWITH
    function SESSION1_deleteAlias(param)
        return SESSION::deleteAlias(param)
    function SESSION1_addAlias(param)
        return SESSION::addAlias(param)
ENDCLASS
'''
    model = parse_dbase_wfm(source)
    assert len(model.controls) == 1
    control = model.controls[0]
    assert control.events == {
        'deleteAlias': 'CLASS::SESSION1_DELETEALIAS',
        'addAlias': 'CLASS::SESSION1_ADDALIAS',
        'beforeRelease': 'CLASS::SESSION1_beforeRelease',
    }
    assert control.properties['left'] == 80
    assert control.properties['top'] == 80
    assert control.properties['lockRetryCount'] == 7
    assert control.properties['lockRetryInterval'] == 250
    assert 'deleteAlias' not in control.properties
    assert set(m.name for m in model.methods) == {
        'SESSION1_deleteAlias', 'SESSION1_addAlias'
    }


def test_parser_does_not_turn_unbound_session_properties_into_events():
    source = '''CLASS P OF FORM
THIS.S = NEW SESSION(THIS)
WITH (THIS.S)
    deleteAlias = "some string"
ENDWITH
ENDCLASS
'''
    model = parse_dbase_wfm(source)
    assert model.controls[0].events == {}
    assert model.controls[0].properties['deleteAlias'] == 'some string'


def test_actual_fixed_component_serializer_emits_binding_before_geometry_once():
    """Exercise the real emit_item body (no PyQt GUI required)."""
    code = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
    anchor = '            def emit_item(item, parent_path="THIS"):'
    start = code.index(anchor, code.index('        def _serialize_dbase_form_wfm(self) -> str:'))
    end = code.index('            for item in children_of(None):', start)
    body = textwrap.dedent(code[start:end])

    class Item:
        component_type = 'Session'
        component_name = 'SESSION1'
        wfm_class_name = 'SESSION'
        component_active = False
        session_lock_retry_count = 3
        session_lock_retry_interval = 1000
        wfm_events = {}

        def geometry_values(self):
            return (80, 80, 42, 42)

    class Host:
        @staticmethod
        def _wfm_class_for_component(kind):
            return kind.upper()

        @staticmethod
        def _wfm_quote(s):
            return '"' + s + '"'

        @staticmethod
        def _wfm_bool(b):
            return '.T.' if b else '.F.'

    item = Item()
    bind_session_method(item.wfm_events, item.component_name, 'deleteAlias')
    bind_session_method(item.wfm_events, item.component_name, 'addAlias')
    namespace = {
        'lines': [], 'self': Host(), 'DBASE_FORM_FIXED_42_COMPONENTS': {'Session'},
        'canonical_event_reference': lambda value: value,
    }
    exec(body, namespace)
    namespace['emit_item'](item)
    output = '\n'.join(namespace['lines'])
    assert output.count('deleteAlias = CLASS::SESSION1_DELETEALIAS') == 1
    assert output.count('addAlias = CLASS::SESSION1_ADDALIAS') == 1
    assert output.index('deleteAlias =') < output.index('Left = 80')
    assert output.index('addAlias =') < output.index('Top = 80')
    assert '    THIS.SESSION1 = NEW SESSION(THIS)' in output
    assert '    WITH (THIS.SESSION1)' in output
    assert '        Left = 80' in output and '        Top = 80' in output
    source = ('CLASS ParentForm OF FORM\n' + output + '\n'
              + '\n'.join(session_method_source('SESSION1', 'deleteAlias')) + '\n'
              + '\n'.join(session_method_source('SESSION1', 'addAlias')) + '\nENDCLASS\n')
    parsed = parse_dbase_wfm(source)
    assert parsed.controls[0].events == item.wfm_events
    assert parsed.controls[0].properties['Left'] == 80
    assert parsed.controls[0].properties['Top'] == 80


def test_gui_entrypoint_syncs_existing_source_then_binds_exact_item():
    code = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
    start = code.index('        def _open_dbase_form_session_method(')
    end = code.index('        def _open_dbase_form_event_procedure(', start)
    body = code[start:end]
    assert '_merge_dbase_form_source_methods_events(strict=False)' in body
    assert 'bind_session_method(item.wfm_events, item.component_name, method_name)' in body
    assert body.index('bind_session_method(') < body.index('source = self._sync_dbase_form_source()')
    assert body.count('methods.append(') == 1
    assert 'find_event_procedure_offset' in body

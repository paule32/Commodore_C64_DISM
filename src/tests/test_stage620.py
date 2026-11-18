# -*- coding: utf-8 -*-
"""Stage 620: Ein Splash vor dem expliziten Oeffnen von Docking-Fenstern."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dock_opening_prelude import (
    DOCK_OPENING_TITLES,
    EXISTING_PRELUDE_METHODS,
    install_dock_opening_preludes,
)


class FakeMain:
    def __init__(self):
        self._dock_prelude_ready = True
        self._dock_prelude_dispatching = False
        self._operation_prelude = None
        self.events = []
        self.pending = None

    def run_with_operation_prelude(self, title, message, operation):
        self.events.append(('splash', title, message))
        self.pending = operation
        return True

    def show_agent_0003_dock(self, who=None, *, source=None):
        self.events.append(('agent', who, source))

    def show_settings_dock(self, _checked=False):
        self.events.append(('settings', _checked))

    def show_project_settings_dock(self, _checked=False):
        self.events.append(('existing-prelude', _checked))

    def open_project_wfm_with_prelude(self, path):
        self.events.append(('wfm-prelude', path))

    def show_dbase_form_designer(self):
        # Workspace ruft bei Bedarf weitere Oeffnungsaktionen auf.
        self.events.append(('form',))
        self.show_settings_dock()

    def localize_dialog(self):
        self.events.append(('localize',))


def new_main():
    # Pro Test eine neue Klasse, damit keine Klassenmodifikation leckt.
    cls = type('TestMain', (FakeMain,), {})
    for name, method in vars(FakeMain).items():
        if name in DOCK_OPENING_TITLES or name in EXISTING_PRELUDE_METHODS:
            setattr(cls, name, method)
    return cls, cls()


def test_before_dock_open_and_preserves_arguments():
    cls, main = new_main()
    names = install_dock_opening_preludes(cls)
    assert 'show_agent_0003_dock' in names
    assert main.show_agent_0003_dock('test', source='image.png') is True
    assert main.events == [
        ('splash', 'Agent 0003 – Bild-Erkennung', 'Agent 0003 – Bild-Erkennung wird geladen …')
    ]
    assert main.pending() is True
    assert main.events[-1] == ('agent', 'test', 'image.png')


def test_qaction_triggered_bool_is_not_forwarded_to_zero_argument_slot():
    cls, main = new_main()
    install_dock_opening_preludes(cls)
    # Agent-/Localize-Menueaktionen liefern ein checked=False-Signal.
    assert main.localize_dialog(False) is True
    assert main.pending() is True
    assert main.events[-1] == ('localize',)


def test_qaction_checked_argument_is_preserved_for_matching_slot():
    cls, main = new_main()
    install_dock_opening_preludes(cls)
    assert main.show_settings_dock(True) is True
    main.pending()
    assert ('settings', True) in main.events


def test_pre_existing_and_startup_are_synchronous():
    cls, main = new_main()
    install_dock_opening_preludes(cls)
    main._dock_prelude_ready = False
    assert main.show_settings_dock(True) is None
    assert main.events == [('settings', True)]
    main.events.clear()
    main.show_project_settings_dock()
    main.open_project_wfm_with_prelude('test.wfm')
    assert main.events == [('existing-prelude', False), ('wfm-prelude', 'test.wfm')]


def test_nested_dock_opening_does_not_open_second_splash():
    cls, main = new_main()
    install_dock_opening_preludes(cls)
    main.show_dbase_form_designer()
    assert main.events == [('splash', 'dBASE Formular-Designer', 'dBASE Formular-Designer wird geladen …')]
    assert main.pending() is True
    assert main.events[1:] == [('form',), ('settings', False)]
    assert not main._dock_prelude_dispatching


def test_existing_prelude_does_not_start_second_independent_operation():
    cls, main = new_main()
    install_dock_opening_preludes(cls)
    main._operation_prelude = object()
    assert main.localize_dialog() is False
    assert main.events == []


def test_existing_prelude_runs_nested_operation_immediately():
    cls, main = new_main()
    install_dock_opening_preludes(cls)
    main._operation_prelude = object()
    main._operation_prelude_executing = True
    assert main.localize_dialog() is None
    assert main.events == [('localize',)]


def test_idempotent_install_and_public_signature():
    cls, main = new_main()
    first = install_dock_opening_preludes(cls)
    assert first
    assert install_dock_opening_preludes(cls) == ()
    assert cls.show_agent_0003_dock.__name__ == 'show_agent_0003_dock'
    main.localize_dialog()
    assert main.events == [('splash', 'Localize PO/MO', 'Localize PO/MO wird geladen …')]


def test_exception_resets_guard():
    cls, main = new_main()
    def boom(self):
        raise ValueError('fehler')
    cls.show_agent_0003_dock = boom
    install_dock_opening_preludes(cls)
    main.show_agent_0003_dock()
    with pytest.raises(ValueError, match='fehler'):
        main.pending()
    assert not main._dock_prelude_dispatching


def test_main_window_integration_and_startup_guard():
    source = (Path(__file__).resolve().parent / 'd64_dism.py').read_text(encoding='utf-8')
    assert 'install_dock_opening_preludes(ExplorerWindow)' in source
    assert source.index('install_dock_opening_preludes(ExplorerWindow)') < source.index('window = ExplorerWindow(initial_directory)')
    assert source.index('window = ExplorerWindow(initial_directory)') < source.index('window._dock_prelude_ready = True')
    assert 'self.run_with_operation_prelude(' in source
    assert 'D64OperationPreludeDialog(' in source


def test_default_dock_opening_names_are_actually_present():
    source = (Path(__file__).resolve().parent / 'd64_dism.py').read_text(encoding='utf-8')
    for method in DOCK_OPENING_TITLES:
        assert f'def {method}(' in source, method


def test_original_lazy_imports_are_retained():
    source = (Path(__file__).resolve().parent / 'd64_dism.py').read_text(encoding='utf-8')
    assert 'lazy from app_lang.deu import APP_LANGUAGE as LANG_DEU' in source
    assert 'lazy from app_lang.enu import APP_LANGUAGE as LANG_ENU' in source


def test_new_module_compiles():
    source = (Path(__file__).resolve().parent / 'dock_opening_prelude.py').read_text(encoding='utf-8')
    ast.parse(source)

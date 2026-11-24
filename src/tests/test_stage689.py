# -*- coding: utf-8 -*-
"""Stage 689: Turbo Help message boxes respect the MainWindow theme.

The real PyQt5 widget cannot be launched in the CI container. These tests run
actual methods from TurboHelpEditor against minimal Qt-compatible stand-ins.
"""
from pathlib import Path
from types import SimpleNamespace
import ast
import textwrap

SOURCE = (Path(__file__).resolve().parent / 'turbo_help_gui.py').read_text('utf-8')
MODULE = ast.parse(SOURCE)
CLASS = next(x for x in MODULE.body if isinstance(x, ast.ClassDef) and x.name == 'TurboHelpEditor')


def method(name, namespace):
    node = next(x for x in CLASS.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == name)
    return ns_exec(node, namespace)[name]


def ns_exec(node, namespace):
    # Compiling only this method avoids PyQt imports and preserves its real body.
    tree = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(tree)
    exec(compile(tree, 'turbo_help_gui.py', 'exec'), namespace)
    return namespace


class MockBox:
    def __init__(self, owner):
        self.owner = owner
        self.attrs = {}
        self.executed = False

    def __getattr__(self, key):
        if key.startswith('set'):
            def setter(*args):
                self.attrs[key] = args
            return setter
        raise AttributeError(key)

    def exec_(self):
        self.executed = True
        return 123


class MockQMessageBox:
    Ok, Warning, Critical = 1, 2, 3
    instances = []

    def __new__(cls, owner):
        result = MockBox(owner)
        cls.instances.append(result)
        return result


class FakePalette:
    def __init__(self, lightness):
        self.lightness_value = lightness

    def color(self, role):
        return SimpleNamespace(lightness=lambda: self.lightness_value)


class FakeApp:
    palette_obj = FakePalette(40)

    @classmethod
    def instance(cls):
        return SimpleNamespace(palette=lambda: cls.palette_obj)


def namespace():
    return {
        'QMessageBox': MockQMessageBox,
        'QApplication': FakeApp,
        'QPalette': SimpleNamespace(Window=1),
        'Qt': SimpleNamespace(PlainText=0, WA_StyledBackground=99),
    }


class DummyWidget:
    def __init__(self, parent=None):
        self.parent = parent

    def parentWidget(self):
        return self.parent

    def palette(self):
        return FakePalette(40)


def test_parent_chain_finds_main_window_factory_even_through_dock():
    ns = namespace()
    fn = method('_help_message_box', ns)
    box = MockBox(None)

    class MainWindow(DummyWidget):
        def __init__(self):
            super().__init__()
            self.args = []

        def _create_message_box(self, icon, title, message):
            self.args.append((icon, title, message))
            return box

    main_window = MainWindow()
    dock = DummyWidget(main_window)
    editor = DummyWidget(dock)
    result = fn(editor, MockQMessageBox.Warning, 'Turbo Hilfe', 'Haupt-Eintrag fehlt')
    assert result is box
    assert main_window.args == [(MockQMessageBox.Warning, 'Turbo Hilfe', 'Haupt-Eintrag fehlt')]
    assert not MockQMessageBox.instances, 'MainWindow factory must be reused, not bypassed'


def test_fallback_standalone_message_is_readable_in_dark_and_light():
    ns = namespace()
    fn = method('_help_message_box', ns)
    for brightness, foreground, surface in ((40, '#ffffff', '#202630'),
                                            (230, '#000000', '#f0f0f0')):
        FakeApp.palette_obj = FakePalette(brightness)
        editor = DummyWidget()
        box = fn(editor, MockQMessageBox.Critical, 'Hilfecompiler', 'Fehler')
        css = box.attrs['setStyleSheet'][0]
        assert surface in css and foreground in css
        assert 'QMessageBox QLabel' in css and 'QMessageBox QPushButton' in css
        assert box.attrs['setPalette'][0] is FakeApp.palette_obj
        assert box.attrs['setAttribute'] == (99, True)
        assert box.attrs['setText'] == ('Fehler',)


def test_compile_warning_when_no_main_entry_uses_styled_dialog():
    ns = namespace()
    compile_help = method('compile_help', ns)

    class FailingEditor:
        _busy = False
        use_project_list = True
        def __init__(self):
            self.status = []
            self.messages = []
            self.status_label = SimpleNamespace(setText=self.status.append)
            self.resolve_project_help_inputs = self.missing_main
        def missing_main(self):
            raise ValueError('Kein Haupt-Eintrag ausgewählt')
        def _show_help_message(self, *args):
            self.messages.append(args)
    editor = FailingEditor()
    assert compile_help(editor) is False
    assert editor.status == ['Fehler: Kein Haupt-Eintrag ausgewählt']
    assert editor.messages == [(MockQMessageBox.Warning, 'Turbo Hilfe',
                                 'Kein Haupt-Eintrag ausgewählt')]


def test_all_help_editor_alerts_use_the_same_style_path():
    assert 'QMessageBox.warning(self,' not in SOURCE
    assert 'QMessageBox.critical(self,' not in SOURCE
    assert "getattr(self.parent(), 'dark_mode_enabled'" not in SOURCE
    assert SOURCE.count('self._show_help_message(') >= 6
    for method_name in ('load_document', '_save_edit', 'compile_help'):
        node = next(x for x in CLASS.body if isinstance(x, ast.FunctionDef) and x.name == method_name)
        assert any(isinstance(n, ast.Attribute) and n.attr == '_show_help_message'
                   for n in ast.walk(node)), method_name


def test_show_help_message_executes_box_from_factory():
    fn = method('_show_help_message', namespace())
    box = MockBox(None)
    editor = SimpleNamespace(_help_message_box=lambda *a: box)
    assert fn(editor, MockQMessageBox.Warning, 'x', 'y') == 123
    assert box.executed

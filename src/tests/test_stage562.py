"""Stage 562: Hintergrundfenster-Konfiguration und explizites Dock-Schließen."""
from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from installer_background_settings import (
    BACKGROUND_SECTION, BACKGROUND_DEFAULTS, parse_background_settings,
    encode_background_settings,
)
from software_installer_model import InstallerProject

ROOT = Path(__file__).resolve().parent
DIALOGS = (ROOT / "software_installer_dialogs.py").read_text(encoding="utf-8")
WORKBENCH = (ROOT / "software_installer.py").read_text(encoding="utf-8")
MAIN = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
HELP = ROOT / "help" / "software_installer"


class Stage562ModelTests(unittest.TestCase):
    def test_defaults(self):
        defaults = parse_background_settings("")
        self.assertEqual(defaults, BACKGROUND_DEFAULTS)
        self.assertEqual(defaults["title_text"], "%ProductName%")
        self.assertEqual(defaults["version_text"], "%ProductVersion%")
        self.assertEqual(defaults["footer_text"], "%Copyright% Alle Rechte vorbehalten.")

    def test_json_roundtrip_all_styles_and_project(self):
        for mode in ("standard", "framed", "kiosk"):
            for appearance in ("static", "gradient", "image"):
                settings = dict(BACKGROUND_DEFAULTS)
                settings.update({
                    "enabled": True, "mode": mode, "appearance": appearance,
                    "static_color": "#AABBCC", "gradient_start": "#0088ff",
                    "gradient_end": "#ffeeaa", "image_path": r"C:\Setup\background.png",
                    "title_text": "%ProductName% Setup", "title_font": "Arial,10,-1,5,50,0,0,0,0,0",
                    "title_color": "#123456", "title_align": "right",
                    "version_text": "%ProductVersion%", "version_align": "left",
                    "version_color": "#987654", "footer_text": "© %Copyright%",
                })
                encoded = encode_background_settings(settings)
                project = InstallerProject(sections={BACKGROUND_SECTION: encoded})
                with tempfile.TemporaryDirectory() as temp:
                    target = Path(temp) / "test.installer.json"
                    project.save(str(target))
                    loaded = InstallerProject.load(str(target))
                    parsed = parse_background_settings(loaded.sections[BACKGROUND_SECTION])
                    self.assertEqual(parsed["mode"], mode)
                    self.assertEqual(parsed["appearance"], appearance)
                    self.assertEqual(parsed["title_align"], "right")
                    self.assertEqual(parsed["static_color"], "#aabbcc")

    def test_reject_invalid_project_options(self):
        invalid = (
            {"mode": "unknown"}, {"enabled": "false"},
            {"appearance": "rainbow"}, {"title_color": "red"},
            {"version_align": "bottom"}, {"image_path": None},
            {"not_a_setting": "x"},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    encode_background_settings(changes)
        with self.assertRaises(ValueError):
            parse_background_settings(json.dumps({"version": 9, "settings": {}}))
        with self.assertRaises(json.JSONDecodeError):
            parse_background_settings("{ broken json")

    def test_missing_keys_are_defaulted(self):
        parsed = parse_background_settings(json.dumps(
            {"version": 1, "settings": {"enabled": True, "mode": "kiosk"}}))
        self.assertTrue(parsed["enabled"])
        self.assertEqual(parsed["mode"], "kiosk")
        self.assertEqual(parsed["gradient_end"], "#ffffff")


class Stage562StructureTests(unittest.TestCase):
    def test_syntax(self):
        ast.parse(DIALOGS)
        ast.parse(WORKBENCH)
        # d64_dism.py verwendet bereits Python-3.15-Lazy-Imports, die
        # Python 3.13 hier nicht direkt parsen kann. Die beiden geänderten
        # Methoden werden separat geprüft.
        for start, end in (
            ('        def _ensure_installer_workspace_after_restore(',
             '        def _restore_exclusive_tool_workspace('),
            ('        def show_software_installer_dock(',
             '        def show_software_installer_help('),
        ):
            snippet = MAIN[MAIN.index(start):MAIN.index(end, MAIN.index(start))]
            import textwrap
            ast.parse(textwrap.dedent(snippet))

    def test_ui_geometry_components_and_actions(self):
        needles = (
            'class InstallerBackgroundWindowDialog(InstallerThemedDialog):',
            '"Hintergrund Fenster anzeigen"',
            '"Hintergrund Fenster"',
            'self.setFixedSize(WIZARD_SIZE[0] - 140, WIZARD_SIZE[1] - 40)',
            '"Standard"', '"Eingerahmt"', '"Kiosk"',
            '"Statische Farbe"', '"Verlauf"', '"Bild"',
            '"Durchsuchen"', '"Text"', '"Titel-Zeile"',
            '"Version-Zeile"', '"Fuß-Zeile"', '"Links"', '"Mitte"',
            '"Rechts"', 'InstallerColorComboBox(', 'QFontDialog.getFont(',
            'self.image_edit.setEnabled(self.image_radio.isChecked())',
            'self.image_browse.setEnabled(self.image_radio.isChecked())',
            '("OK", "Abbrechen", "Hilfe")',
            'self.help_callback("Hintergrund Fenster")',
        )
        for needle in needles:
            with self.subTest(needle=needle):
                self.assertIn(needle, DIALOGS)

    def test_project_save_and_cancel_paths(self):
        fragment = WORKBENCH[WORKBENCH.index('def edit_background_window('):
                             WORKBENCH.index('def handle_panel_action(', WORKBENCH.index('def edit_background_window('))]
        for needle in ('InstallerBackgroundWindowDialog(', 'dialog.exec_() != QDialog.Accepted',
                       'self.project.sections[BACKGROUND_SECTION] = serialized',
                       'self._mark_dirty()', 'self.save_configuration()'):
            self.assertIn(needle, fragment)
        self.assertIn('"Hintergrund Fenster": self.edit_background_window', WORKBENCH)

    def test_explicit_dock_close_not_visibility_restore(self):
        self.assertIn('class InstallerWorkspaceDock(QDockWidget):', WORKBENCH)
        self.assertIn('explicitCloseRequested = pyqtSignal()', WORKBENCH)
        self.assertIn('def closeEvent(self, event):', WORKBENCH)
        self.assertIn('dock.explicitCloseRequested.connect(', MAIN)
        self.assertIn('self._ensure_installer_workspace_after_restore', MAIN)
        self.assertIn('if not visible:\n                    return', MAIN)

    def test_minimize_visibility_does_not_restore_workspace(self):
        """Echte Callback-Implementierung mit Qt-freien Ersatzobjekten testen."""
        import textwrap
        start = MAIN.index('        def _exclusive_tool_workspace_visibility_changed(')
        end = MAIN.index('        def _restore_exclusive_tool_workspace(', start)
        method = textwrap.dedent(MAIN[start:end])
        namespace = {'QDockWidget': object}
        class Timer:
            @staticmethod
            def singleShot(_delay, callback):
                callback()
        namespace['QTimer'] = Timer
        exec(compile(method, '<qt-dock-visibility>', 'exec'), namespace)
        callback = namespace['_exclusive_tool_workspace_visibility_changed']
        class Host:
            _exclusive_tool_workspace_transitioning = False
            def __init__(self):
                self.software_installer_dock = object()
                self._exclusive_tool_workspace = {'owner': self.software_installer_dock}
                self.minimized = False
                self.visible = True
                self.restores = []
                self.expansions = []
            def isMinimized(self):
                return self.minimized
            def isVisible(self):
                return self.visible
            def _restore_exclusive_tool_workspace(self, dock):
                self.restores.append(dock)
            def _expand_exclusive_tool_workspace(self, dock):
                self.expansions.append(dock)
        host = Host()
        host.minimized = True
        host.visible = False
        callback(host, False, host.software_installer_dock)
        self.assertEqual(host.restores, [])
        # Auch im normalen Zustand darf false keinen Restore ausloesen,
        # denn nur der explizite Close-Handler darf das.
        host.minimized = False
        host.visible = True
        callback(host, False, host.software_installer_dock)
        self.assertEqual(host.restores, [])
        callback(host, True, host.software_installer_dock)
        self.assertEqual(host.expansions, [host.software_installer_dock])

    def test_restore_reactivates_only_active_installer(self):
        import textwrap
        start = MAIN.index('        def _ensure_installer_workspace_after_restore(')
        end = MAIN.index('        def _exclusive_tool_workspace_visibility_changed(', start)
        namespace = {}
        exec(compile(textwrap.dedent(MAIN[start:end]), '<qt-dock-restore>', 'exec'), namespace)
        callback = namespace['_ensure_installer_workspace_after_restore']
        class Dock:
            def __init__(self):
                self.visible = False
                self.shows = 0
            def isVisible(self):
                return self.visible
            def show(self):
                self.visible = True
                self.shows += 1
        class Host:
            _exclusive_tool_workspace_transitioning = False
            def __init__(self):
                self.software_installer_dock = Dock()
                self._exclusive_tool_workspace = {'owner': self.software_installer_dock}
                self.minimized = True
                self.expansions = []
            def isMinimized(self):
                return self.minimized
            def isVisible(self):
                return not self.minimized
            def _expand_exclusive_tool_workspace(self, dock):
                self.expansions.append(dock)
        host = Host()
        callback(host)
        self.assertEqual(host.software_installer_dock.shows, 0)
        host.minimized = False
        callback(host)
        self.assertEqual(host.software_installer_dock.shows, 1)
        self.assertEqual(host.expansions, [host.software_installer_dock])
        callback(host)
        self.assertEqual(host.software_installer_dock.shows, 1)
        host._exclusive_tool_workspace = None
        host.software_installer_dock.visible = False
        callback(host)
        self.assertEqual(host.software_installer_dock.shows, 1)

    def test_help_index(self):
        self.assertTrue((HELP / 'hintergrund_fenster.html').is_file())
        for filename in ('index.html', 'installer.hhc', 'installer.hhk', 'installer.hhp'):
            self.assertIn('hintergrund_fenster.html', (HELP / filename).read_text('utf-8'))


if __name__ == '__main__':
    unittest.main()

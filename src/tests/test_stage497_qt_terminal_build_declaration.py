"""Stage 497 regression adapted to Stage 498 platform-specific terminal.

Eliminating the redundant Windows dialog also eliminates the missing-prototype
failure of Stage 495: no call or declaration must remain in the Windows C++.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class Stage497QtTerminalTests(unittest.TestCase):
    def test_obsolete_windows_dialog_is_not_created(self):
        source = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
        self.assertNotIn('append_dbase_qt_terminal', source)
        self.assertNotIn('dbaseTerminalDialog', source)
        self.assertNotIn('g_dbase_qt_terminal_editor', source)

    def test_windows_output_uses_existing_dialog_and_runner(self):
        source = (ROOT / 'd64qt5' / 'd64qt5_bridge.cpp').read_text(encoding='utf-8')
        body = source.split('extern "C" D64QT5_API void DBaseQtAppendConsole(', 1)[1].split('extern "C" D64QT5_API void DBaseQtAppendDebug(', 1)[0]
        self.assertIn('append_wfm_output(', body)
        self.assertIn('send_wfm_output_to_workstation(', body)
        self.assertIn('append_text(g_console, text, length)', body)

if __name__ == '__main__':
    unittest.main()

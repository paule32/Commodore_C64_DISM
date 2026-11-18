"""Stage 625: SET BACKGROUND targets the main 80x25 console, not Turbo Vision.

Static bridge integration checks plus live compiler assembly checks. GUI paint remains
for Windows/Qt5 runtime validation.
"""
from pathlib import Path
import unittest

from d64dbase.compiler import compile_dbase_to_assembly

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')
TURBO = (ROOT / 'd64qt5/d64_turbo_output.hpp').read_text(encoding='utf-8')


def body_of(symbol: str) -> str:
    begin = BRIDGE.index(symbol)
    open_brace = BRIDGE.index('{', begin)
    depth = 0
    for i in range(open_brace, len(BRIDGE)):
        if BRIDGE[i] == '{':
            depth += 1
        elif BRIDGE[i] == '}':
            depth -= 1
            if depth == 0:
                return BRIDGE[open_brace + 1:i]
    raise ValueError(f'No end for {symbol}')


class Stage625MainBackgroundTests(unittest.TestCase):
    def test_qplaintextedit_is_the_main_console(self):
        self.assertIn('g_console = new QPlainTextEdit(g_console_frame)', BRIDGE)
        self.assertIn('new D64TurboOutputWidget(g_console->viewport())', BRIDGE)
        self.assertIn('g_console->setObjectName(QStringLiteral("dbaseConsole"))', BRIDGE)

    def test_fill_targets_console_not_turbo(self):
        fill = body_of('extern "C" D64QT5_API int DBaseQtFillBackground(')
        self.assertIn('render_console_character_pattern(code, foreground, background)', fill)
        self.assertNotIn('g_turbo_output->fillBackground(', fill)
        self.assertNotIn('g_turbo_output->show()', fill)
        self.assertNotIn('g_turbo_output->hide()', fill)
        self.assertIn('g_turbo_output->isVisible()', fill)
        self.assertIn('g_turbo_output->raise()', fill)

    def test_console_cp437_cell_filling(self):
        render = body_of('bool render_console_character_pattern(')
        self.assertIn('D64TurboOutputWidget::dosCharacter(byteCode)', render)
        self.assertIn('const QString row(DBASE_TEXT_COLUMNS, glyph)', render)
        self.assertIn('y < DBASE_TEXT_ROWS', render)
        self.assertIn('g_console->clear()', render)
        self.assertIn('cursor.insertText(pattern, format)', render)
        self.assertIn('format.setForeground(foreground)', render)
        self.assertIn('format.setBackground(background)', render)

    def test_new_background_keeps_last_colors_for_short_form(self):
        fill = body_of('extern "C" D64QT5_API int DBaseQtFillBackground(')
        self.assertIn('bg >= 0', fill)
        self.assertIn('fg >= 0', fill)
        self.assertIn('g_console_clear_char_background : g_console_background', fill)
        self.assertIn('g_console_clear_char_foreground : g_output_foreground', fill)
        self.assertIn('g_console_clear_char_code = code', fill)
        self.assertIn('g_console_clear_char_background = background', fill)
        self.assertIn('g_console_clear_char_foreground = foreground', fill)

    def test_zoom_preserves_background_pattern(self):
        self.assertIn('restore_console_clear_pattern_after_grid_change();', BRIDGE)
        restore = body_of('void restore_console_clear_pattern_after_grid_change()')
        self.assertIn('ConsoleClearMode::CharacterPattern', restore)
        self.assertIn('g_console_clear_char_code', restore)
        self.assertIn('g_console_clear_char_foreground', restore)
        self.assertIn('g_console_clear_char_background', restore)

    def test_turbo_debug_print_remains_separate(self):
        self.assertIn('g_turbo_output->appendOutput(QString::fromLocal8Bit(text, length))', BRIDGE)
        self.assertIn('class D64TurboOutputWidget final : public QWidget', TURBO)
        self.assertIn('toggleMaximized()', TURBO)

    def test_invalid_parameters(self):
        fill = body_of('extern "C" D64QT5_API int DBaseQtFillBackground(')
        self.assertIn('code < 0 || code > 255', fill)
        self.assertIn('bg < -1 || bg > 15', fill)
        self.assertIn('fg < -1 || fg > 15', fill)

    def test_compiler_short_long_forms_pe32_pe64(self):
        for code in ('SET BACKGROUND TO 176', 'SET BACKGROUND TO 1, 14, 178'):
            for target in ('pe32', 'pe64'):
                with self.subTest(code=code, target=target):
                    asm = compile_dbase_to_assembly(code, target=target).assembly
                    self.assertIn('call DBaseQtFillBackground', asm)


if __name__ == '__main__':
    unittest.main()

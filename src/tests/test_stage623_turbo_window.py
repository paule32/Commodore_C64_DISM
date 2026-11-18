"""Stage 623: statische Integrations- und Zeichenraster-Regressionstests.

Die GUI selbst benoetigt Qt5/MinGW32 und wird unter Windows getestet.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "d64qt5" / "d64_turbo_output.hpp").read_text(encoding="utf-8")
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


def round_to_cell(delta: int, cell: int) -> int:
    cell = max(1, cell)
    return ((delta + cell//2) // cell * cell) if delta >= 0 else -(((-delta + cell//2)//cell)*cell)


def move_clamped(x: int, y: int, width: int, height: int, area_width: int, area_height: int):
    return (max(0, min(x, max(0, area_width-width))),
            max(0, min(y, max(0, area_height-height))))


def maximized_grid(vw: int, vh: int, cw: int, ch: int, chrome_w: int = 27, shadow: int = 7):
    # titleHeight=ch+14; footerHeight=ch+9; chromeHeight=2*ch+31
    return (max(1, (vw-chrome_w-shadow)//cw),
            max(1, (vh-(2*ch+31)-shadow)//ch))


class Stage623SourceTests(unittest.TestCase):
    def test_uses_existing_widget_and_no_moc(self):
        self.assertIn('class D64TurboOutputWidget final : public QWidget', HEADER)
        self.assertNotIn('Q_OBJECT', HEADER.split('class D64TurboOutputWidget', 1)[1])
        self.assertIn('D64TurboOutputWidget * g_turbo_output', BRIDGE)

    def test_title_drag_mouse_events(self):
        for symbol in ('mousePressEvent(', 'mouseMoveEvent(', 'mouseReleaseEvent(',
                       'isTitleBarPoint(', 'moveWithinViewport(',
                       'moveStartGlobal_', 'roundToCell(delta.x(), cellWidth_)',
                       'roundToCell(delta.y(), cellHeight_)'):
            self.assertIn(symbol, HEADER)

    def test_max_button_and_double_click(self):
        for symbol in ('QToolButton *maximizeButton_', 'QToolButton::clicked',
                       'toggleMaximized()', 'mouseDoubleClickEvent(',
                       'restoreOriginX_', 'restoreOriginY_',
                       'restoreColumns_', 'restoreRows_'):
            self.assertIn(symbol, HEADER)
        self.assertIn('maximizeButton_->setToolTip(QStringLiteral("Ausgabefenster maximieren"))', HEADER)
        self.assertIn('maximizeButton_->setToolTip(QStringLiteral("Ausgabefenster wiederherstellen"))', HEADER)

    def test_zoom_viewport_resize(self):
        self.assertIn('if (maximized_)\n            fitMaximizedToViewport();', HEADER)
        self.assertIn('watched == parentWidget() && event->type() == QEvent::Resize', HEADER)
        self.assertIn('const QFontMetrics fm(font)', HEADER)

    def test_resize_grip_visibility(self):
        self.assertIn('grip_->hide();', HEADER)
        self.assertIn('grip_->show();', HEADER)
        self.assertIn('if (maximized_) return QWidget::eventFilter(watched, event);', HEADER)

    def test_dbase_print_routing_kept(self):
        self.assertIn('g_turbo_output->appendOutput(QString::fromLocal8Bit(text, length))', BRIDGE)

    def test_block_rounding(self):
        self.assertEqual([round_to_cell(n, 8) for n in (0,3,4,5,8,11,12,15,16)],
                         [0,0,8,8,8,8,16,16,16])
        self.assertEqual([round_to_cell(n, 8) for n in (-3,-4,-5,-8,-11,-12,-16)],
                         [0,-8,-8,-8,-8,-16,-16])
        self.assertEqual(round_to_cell(13, 12), 12)

    def test_move_restricted_to_viewport(self):
        self.assertEqual(move_clamped(999,-8,470,260,800,600), (330,0))
        self.assertEqual(move_clamped(100,200,470,260,300,100), (0,0))

    def test_restore_geometry_semantics(self):
        origin = (48, 32)
        grid = (44, 14)
        full = maximized_grid(1000,720,8,16)
        self.assertGreater(full[0],grid[0])
        self.assertGreater(full[1],grid[1])
        after_restore = (move_clamped(*origin, grid[0]*8+34, grid[1]*16+63,1000,720),grid)
        self.assertEqual(after_restore, (origin, grid))
        self.assertEqual(move_clamped(*origin, grid[0]*8+34,grid[1]*16+63,300,150), (0,0))

    def test_maximized_char_count_updates_with_zoom(self):
        before = maximized_grid(800,500,8,16)
        after = maximized_grid(800,500,12,24)
        self.assertGreater(before[0],after[0])
        self.assertGreater(before[1],after[1])


if __name__ == '__main__':
    unittest.main()

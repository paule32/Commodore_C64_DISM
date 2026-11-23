# -*- coding: utf-8 -*-
"""Stage 657: Das Hilfe-Fenster wird beim Drag nur zellenweise verschoben."""
from pathlib import Path
import shutil
import subprocess
import textwrap
import pytest

ROOT = Path(__file__).resolve().parent
HELP = (ROOT / 'd64qt5/d64_turbo_help_window.hpp').read_text(encoding='utf-8')
BRIDGE = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text(encoding='utf-8')


def test_help_title_drag_moves_by_cells_in_both_axes():
    assert 'const QPoint delta = mouse->globalPos() - dragGlobal_;' in HELP
    assert 'd64TurboRoundCells(delta.x(), gridCellWidth_) * gridCellWidth_' in HELP
    assert 'd64TurboRoundCells(delta.y(), gridCellHeight_) * gridCellHeight_' in HELP
    assert 'moveOnGrid(position);' in HELP
    assert 'const QPoint position = dragPosition_ + mouse->globalPos() - dragGlobal_;' not in HELP


def test_grid_cell_size_matches_the_real_console_metrics_and_zoom():
    assert 'g_turbo_help_window->setGridCellSize(current_console_cell_size());' in BRIDGE
    assert BRIDGE.count('g_turbo_help_window->setGridCellSize(current_console_cell_size());') == 2
    assert 'QFontMetrics fm = console_font_metrics(font);' in BRIDGE
    assert "fm.horizontalAdvance(QLatin1Char('M'))" in BRIDGE
    assert 'qMax(1, fm.lineSpacing())' in BRIDGE


def test_grid_limits_resize_restore_and_parent_bounds():
    assert 'moveOnGrid(pos());' in HELP
    assert 'd64TurboClampGridCoordinate(' in HELP
    assert 'parentWidget()->width() - 72' in HELP
    assert 'parentWidget()->height() - title_->height()' in HELP
    assert 'restore_.moveTopLeft(' in HELP
    assert 'if (maximized_) {' in HELP
    assert 'moveOnGrid(QPoint(gridCellWidth_, gridCellHeight_));' in HELP


def test_scrollbars_and_no_host_are_unchanged():
    assert 'new D64TurboArrowScrollBar(Qt::Horizontal, browser_)' in HELP
    assert 'new D64TurboArrowScrollBar(Qt::Vertical, browser_)' in HELP
    assert 'browser_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in HELP
    assert 'browser_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in HELP
    assert 'g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);' in BRIDGE
    assert 'g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);' in BRIDGE
    assert not (ROOT / 'd64qt5/turbo_help_host.cpp').exists()


def test_cpp_move_snaps_and_clamps_to_cell_edges(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ nicht installiert')
    cpp = tmp_path / 'test_grid.cpp'
    exe = tmp_path / 'test_grid'
    cpp.write_text(textwrap.dedent(r'''
        #include "d64_turbo_grid_motion.hpp"
        #include <cassert>
        int main() {
          // Positive und negative Mausbewegung runden auf volle Zellen.
          assert(d64TurboRoundCells(0, 8) == 0);
          assert(d64TurboRoundCells(3, 8) == 0);
          assert(d64TurboRoundCells(4, 8) == 1);
          assert(d64TurboRoundCells(12, 8) == 2);
          assert(d64TurboRoundCells(-3, 8) == 0);
          assert(d64TurboRoundCells(-4, 8) == -1);
          assert(d64TurboRoundCells(-12, 8) == -2);
          // Y-Raster 16, z.B. DOS 8x16.
          assert(d64TurboClampGridCoordinate(23, 16, 200) == 16);
          assert(d64TurboClampGridCoordinate(24, 16, 200) == 32);
          // Der letzte erlaubte Zellursprung endet VOR dem Pixel-Maximum.
          assert(d64TurboClampGridCoordinate(9999, 9, 100) == 99);
          assert(d64TurboClampGridCoordinate(-99, 9, 100) == 0);
          assert(d64TurboClampGridCoordinate(9999, 16, 15) == 0);
          assert(d64TurboClampGridCoordinate(9999, 16, -5) == 0);
          // Test verschiedener Zellgroessen und Grenzen gegen Pixel-Drift.
          for (int w : {6, 8, 9, 12, 17})
          for (int h : {12, 16, 20, 25})
          for (int x=-100; x<=300; x+=3)
          for (int y=-100; y<=300; y+=13) {
            const int sx=d64TurboClampGridCoordinate(x,w,235);
            const int sy=d64TurboClampGridCoordinate(y,h,169);
            assert(sx%w==0 && sy%h==0);
            assert(sx>=0 && sx<=235 && sy>=0 && sy<=169);
            assert(d64TurboClampGridCoordinate(sx,w,235)==sx);
            assert(d64TurboClampGridCoordinate(sy,h,169)==sy);
          }
        }
    '''), encoding='utf-8')
    subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    '-I', str(ROOT / 'd64qt5'), str(cpp), '-o', str(exe)],
                   check=True, capture_output=True, text=True, timeout=25)
    subprocess.run([str(exe)], check=True, capture_output=True, text=True, timeout=20)

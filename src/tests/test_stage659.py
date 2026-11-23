# -*- coding: utf-8 -*-
"""Stage 659: Hilfe-Fensterbreite/-hoehe in ganzen DOS-Zellen aendern."""
from pathlib import Path
import shutil
import subprocess
import textwrap
import pytest

ROOT = Path(__file__).resolve().parent
HELP = (ROOT / 'd64qt5/d64_turbo_help_window.hpp').read_text(encoding='utf-8')
GRID = (ROOT / 'd64qt5/d64_turbo_grid_motion.hpp').read_text(encoding='utf-8')


def test_resize_grip_uses_cell_size_on_both_axes():
    assert 'd64TurboGridDragExtent(resizeStart_.width(), change.x(),' in HELP
    assert 'd64TurboGridDragExtent(resizeStart_.height(), change.y(),' in HELP
    assert 'gridCellWidth_, minimumWidth(), maxW)' in HELP
    assert 'gridCellHeight_, minimumHeight(), maxH)' in HELP
    assert 'resizeStart_.width() + change.x()' not in HELP
    assert 'resizeStart_.height() + change.y()' not in HELP


def test_all_nonmaximized_resizes_snap_to_cells():
    assert 'void resizeOnGrid(const QSize &desired)' in HELP
    assert 'resizeOnGrid(QSize(qMax(320,' in HELP
    assert 'resizeOnGrid(QSize(columns * gridCellWidth_, rows * gridCellHeight_));' in HELP
    assert 'resizeOnGrid(size());' in HELP  # parent resize and maximize restore
    assert 'const int columns = d64TurboRoundCells(width(), oldWidth);' in HELP
    assert 'const int rows = d64TurboRoundCells(height(), oldHeight);' in HELP
    assert 'restore_.setSize(QSize(' in HELP
    assert 'd64TurboClampGridExtent(restoreColumns * gridCellWidth_,' in HELP
    assert 'd64TurboClampGridExtent(restoreRows * gridCellHeight_,' in HELP


def test_existing_behaviour_untouched():
    assert 'moveOnGrid(position);' in HELP
    assert 'g_console' not in HELP  # parent is passed in, not made a new console
    assert 'browser_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in HELP
    assert 'browser_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);' in HELP
    assert 'if (maximized_) setGeometry(parentWidget()->rect());' in HELP
    assert 'raise();' in HELP
    assert 'D64TurboArrowScrollBar' in HELP


def test_cpp_drag_grid_step_rounding_bounds_and_font_change(tmp_path):
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ nicht installiert')
    cpp = tmp_path / 'stage659_grid.cpp'
    exe = tmp_path / 'stage659_grid'
    cpp.write_text(textwrap.dedent(r'''
       #include "d64_turbo_grid_motion.hpp"
       #include <cassert>
       #include <algorithm>
       int main() {
           // DOS 8x16: nur ganze Zeichenspalten und -zeilen.
           assert(d64TurboGridDragExtent(400, 3, 8, 320, 700) == 400);
           assert(d64TurboGridDragExtent(400, 4, 8, 320, 700) == 408);
           assert(d64TurboGridDragExtent(400, -4, 8, 320, 700) == 392);
           assert(d64TurboGridDragExtent(400, 31, 8, 320, 700) == 432);
           assert(d64TurboGridDragExtent(320, -9999, 8, 320, 700) == 320);
           assert(d64TurboGridDragExtent(400, 9999, 8, 320, 699) == 696);
           // Mindesthoehe 200 -> 13 Textzeilen (208 Pixel).
           assert(d64TurboGridDragExtent(240, 0, 16, 200, 580) == 240);
           assert(d64TurboGridDragExtent(240, 7, 16, 200, 580) == 240);
           assert(d64TurboGridDragExtent(240, 8, 16, 200, 580) == 256);
           assert(d64TurboGridDragExtent(240, -8, 16, 200, 580) == 224);
           assert(d64TurboGridDragExtent(240, -9999, 16, 200, 580) == 208);
           assert(d64TurboGridDragExtent(240, 9999, 16, 200, 570) == 560);
           // Viewport zu klein fuer Minimum: Qt-Mindestgroesse gewinnt.
           assert(d64TurboClampGridExtent(200, 16, 200, 160) == 208);
           // Bei Fontwechsel Rasterzellzahl erhalten.
           assert(d64TurboClampGridExtent(50*9, 9, 320, 1000) == 450);
           assert(d64TurboClampGridExtent(20*19, 19, 200, 800) == 380);
           // Bei jedem Drag stets ganze Rasterzellen, begrenztes Maximum.
           for (int cw : {6, 8, 9, 11, 17})
           for (int ch : {12, 16, 19, 25}) {
               for (int drag=-300; drag<=300; ++drag) {
                   int w = d64TurboGridDragExtent(43*cw, drag, cw, 320, 700);
                   int h = d64TurboGridDragExtent(19*ch, drag, ch, 200, 580);
                   assert(w % cw == 0 && h % ch == 0);
                   assert(w >= 320 && h >= 200);
                   assert(w <= std::max(700, ((320+cw-1)/cw)*cw));
                   assert(h <= std::max(580, ((200+ch-1)/ch)*ch));
                   assert(d64TurboGridDragExtent(w, 0, cw, 320, 700) == w);
                   assert(d64TurboGridDragExtent(h, 0, ch, 200, 580) == h);
               }
           }
       }
    '''), encoding='utf-8')
    subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    '-I', str(ROOT / 'd64qt5'), str(cpp), '-o', str(exe)],
                   check=True, capture_output=True, text=True, timeout=25)
    subprocess.run([str(exe)], check=True, capture_output=True, text=True, timeout=20)

"""Stage 650: Turbo-Vision-Hilfe -> Ueber ..."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
BRIDGE = (ROOT / "d64qt5/d64qt5_bridge.cpp").read_text(encoding="utf-8")
DIALOG = (ROOT / "d64qt5/d64_turbo_messagebox.hpp").read_text(encoding="utf-8")


def _about_block():
    start = BRIDGE.index('QAction *aboutAction = helpMenu->addAction(QStringLiteral("Über ..."));')
    end = BRIDGE.index('g_menu_bar->addMenu(helpMenu);', start)
    return BRIDGE[start:end]


def test_exact_about_text_and_newlines():
    block = _about_block()
    match = re.search(r'D64TurboMessageBox::information\(.*?QStringLiteral\(("(?:[^"\\]|\\.)*"(?:\s*"(?:[^"\\]|\\.)*")*)\)', block, re.DOTALL)
    assert match is not None
    literals = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))
    import ast
    actual = ''.join(ast.literal_eval('"' + fragment + '"') for fragment in literals)
    expected = (
        'Turbo Vision  -  dBASE\n'
        'Copyright (c) 2026 Jens Kallup - paule32\n'
        'Alle Rechte vorbehalten.\n\n'
        'Built with: Python and Qt5 Framework,'
    )
    assert actual == expected


def test_only_about_uses_centered_alignment():
    assert 'QStringLiteral("Information"), Qt::AlignCenter);' in _about_block()
    assert 'content->setAlignment(textAlignment);' in DIALOG
    assert 'Qt::Alignment textAlignment = Qt::AlignLeft | Qt::AlignVCenter' in DIALOG
    assert 'D64TurboMessageBox box(&layer, title, message, buttons, textAlignment);' in DIALOG
    assert 'showMessage(parent, title, message, {{QStringLiteral("OK"), Ok}}, textAlignment);' in DIALOG


def test_unchanged_modal_and_button_structure():
    assert 'D64TurboMessageBox::information(g_console ? g_console->viewport() : g_window,' in _about_block()
    assert 'D64TurboModalLayer layer(desktop);' in DIALOG
    assert 'QObject::connect(button, &QPushButton::clicked, this,' in DIALOG

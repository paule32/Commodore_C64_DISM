# -*- coding: utf-8 -*-
"""Stage 666 regression: real Qt document frame margin, not ignored body CSS."""
from pathlib import Path
import re

HEADER = (Path(__file__).parent / 'd64qt5/d64_turbo_help_window.hpp').read_text(encoding='utf-8')


def test_help_html_uses_qtextdocument_root_frame_with_one_character_gap():
    assert '#include <QTextFrame>' in HEADER
    assert '#include <QTextFormat>' in HEADER
    helper = HEADER[HEADER.index('    void setHelpHtml('):HEADER.index('    // Only <b>', HEADER.index('    void setHelpHtml('))]
    assert 'browser_->setHtml(renderMarkup(source));' in helper
    assert 'QTextFrame *root = browser_->document()->rootFrame();' in helper
    assert 'QTextFrameFormat format = root->frameFormat();' in helper
    assert 'format.setLeftMargin(qreal(qMax(1, gridCellWidth_)));' in helper
    assert 'root->setFrameFormat(format);' in helper
    assert helper.index('browser_->setHtml') < helper.index('root->setFrameFormat')
    assert 'format.setTopMargin(0.0);' in helper
    assert 'format.setRightMargin(0.0);' in helper
    assert 'format.setBottomMargin(0.0);' in helper


def test_every_topic_render_uses_margin_helper_including_missing_topic():
    assert 'setHelpHtml(topics_.value(resolvedTopic));' in HEADER
    assert 'setHelpHtml(topics_.value(currentTopic_));' in HEADER
    assert 'setHelpHtml(QStringLiteral("<b>Hilfethema nicht gefunden: </b>") + topic);' in HEADER
    # There must not be a bypass that resets the frame and loses its inset.
    assert HEADER.count('browser_->setHtml(') == 1
    assert 'browser_->clear(); // Replace the previous topic' in HEADER
    assert 'root->setFrameFormat(format);' in HEADER


def test_document_styles_do_not_double_indent_after_root_margin():
    assert '"margin:0;padding:0;font-family:Consolas' in HEADER
    assert 'padding:0 0 0 %1px' not in HEADER
    assert 'textInsetPixels()' not in HEADER
    assert 'static QString renderMarkup(const QString &text)' in HEADER
    assert '.arg(qMax(0, leftInset))' not in HEADER


def test_existing_window_chrome_and_grid_behaviour_unaffected():
    for snippet in (
        'border:2px solid #ffe600',
        'shadow->setOffset(5.0, 5.0);',
        'QStringLiteral("Hilfe:  ") + resolvedTopic',
        'd64TurboGridDragExtent(',
        'd64TurboRoundCells(delta.x(), gridCellWidth_)',
        'bool showTopicByNumber(quint32 number',
        'browser_->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOn);',
        'browser_->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOn);',
    ):
        assert snippet in HEADER


def test_helper_is_called_after_resizing_character_grid():
    method = HEADER[HEADER.index('    void setGridCellSize('):HEADER.index('    bool openMo(')]
    assert 'gridCellWidth_ = qMax(1, cellSize.width());' in method
    assert 'setHelpHtml(topics_.value(currentTopic_));' in method
    assert method.index('gridCellWidth_ = qMax') < method.index('setHelpHtml(')

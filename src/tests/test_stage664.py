# -*- coding: utf-8 -*-
"""Stage 664: numeric Turbo Help topics and native console help window style."""
import gettext
import io
from pathlib import Path

import pytest

from turbo_help_compiler import (
    HELP_NUMBER_CONTEXT, HelpCompiler, HelpCompileError,
    HelpTopicCatalog, read_po, write_mo, write_po,
)
from turbo_help_sidecar import compile_help_sources, install_help_catalog

ROOT = Path(__file__).resolve().parent
HELP = (ROOT / 'd64qt5/d64_turbo_help_window.hpp').read_text('utf-8')
CPP = (ROOT / 'd64qt5/d64qt5_bridge.cpp').read_text('utf-8')
H = (ROOT / 'd64qt5/d64qt5_bridge.h').read_text('utf-8')
DEF = (ROOT / 'd64qt5/d64qt5_bridge.def').read_text('utf-8')


def make_source(tmp_path, body):
    source = tmp_path / 'help.thlp'
    source.write_text(body, encoding='utf-8')
    return source


def compile_as_gettext(source):
    topics = HelpCompiler(source).compile()
    po = write_po(topics)
    entries = read_po(po)
    catalog = gettext.GNUTranslations(io.BytesIO(write_mo(entries)))
    return topics, po, entries, catalog


def test_numeric_topic_generates_two_standard_gettext_entries(tmp_path):
    source = make_source(tmp_path, '%topic "index"\nHallo\n%topic "test" 1234\n<b>Hilfeinhalt</b>\n')
    topics, po, entries, catalog = compile_as_gettext(source)
    assert topics.topic_numbers == {1234: 'test'}
    assert 'msgid "test"\nmsgstr "<b>Hilfeinhalt</b>"' in po
    assert 'msgctxt "turbo-help-id"\nmsgid "1234"\nmsgstr "test"' in po
    assert entries['test'] == '<b>Hilfeinhalt</b>'
    assert entries['turbo-help-id\x041234'] == 'test'
    assert catalog.gettext('test') == '<b>Hilfeinhalt</b>'
    assert catalog.pgettext(HELP_NUMBER_CONTEXT, '1234') == 'test'
    assert catalog.gettext(catalog.pgettext(HELP_NUMBER_CONTEXT, '1234')) == '<b>Hilfeinhalt</b>'


def test_numeric_link_and_anchor_refs(tmp_path):
    source = make_source(tmp_path, '''%topic "index" 10
%link 1234
%ref 1234 #abschnitt
%topic 'test' 1234
%anchor #abschnitt
Zeile
''')
    topics, _, _, catalog = compile_as_gettext(source)
    assert topics.topic_numbers == {10: 'index', 1234: 'test'}
    assert "<link>'1234'</link>" in topics['index']
    assert "<ref>'1234' #abschnitt</ref>" in topics['index']
    assert '<anchor id="abschnitt"></anchor>' in topics['test']
    assert catalog.pgettext(HELP_NUMBER_CONTEXT, '10') == 'index'


def test_include_and_multiple_project_sources_preserve_numeric_map(tmp_path):
    main = make_source(tmp_path, '%topic "index" 1\nStart\n%include "chapter.thlp"\n')
    ext = tmp_path / 'chapter.thlp'
    ext.write_text('%topic "Kapitel" 77\nInhalt\n', encoding='utf-8')
    another = tmp_path / 'extra.thlp'
    another.write_text('%topic "Letzte Seite" 88\nEnde\n', encoding='utf-8')
    topics = HelpCompiler.compile_files([main, another])
    assert topics.topic_numbers == {1: 'index', 77: 'Kapitel', 88: 'Letzte Seite'}
    translated = gettext.GNUTranslations(io.BytesIO(write_mo(read_po(write_po(topics)))))
    assert translated.pgettext(HELP_NUMBER_CONTEXT, '88') == 'Letzte Seite'


@pytest.mark.parametrize('number', ['4294967296', '999999999999999999999999999', '-1', '12.5'])
def test_out_of_range_or_malformed_numeric_topic_rejected(tmp_path, number):
    source = make_source(tmp_path, f'%topic "index"\nHello\n%topic "test" {number}\nContent\n')
    with pytest.raises(HelpCompileError, match='Hilfenummer|Präprozessoranweisung'):
        HelpCompiler(source).compile()


def test_duplicate_numeric_help_numbers_rejected_across_sources(tmp_path):
    a = make_source(tmp_path, '%topic "index" 001234\nStart\n')
    b = tmp_path / 'second.thlp'
    b.write_text('%topic "test" 1234\nContent\n', encoding='utf-8')
    with pytest.raises(HelpCompileError, match='Hilfenummer 1234 schon'):
        HelpCompiler.compile_files([a, b])


def test_legacy_topics_keep_identical_gettext_lookup(tmp_path):
    source = make_source(tmp_path, '%topic "index"\nHallo\n%topic "test"\nTest\n')
    topics, po, entries, catalog = compile_as_gettext(source)
    assert topics.topic_numbers == {}
    assert 'msgctxt' not in po
    assert set(entries) == {'', 'index', 'test'}
    assert catalog.gettext('test') == 'Test'


def test_pofile_context_round_trip_and_unresolved_id_rejected():
    entries = read_po('''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "index"
msgstr "Start"

msgctxt "turbo-help-id"
msgid "1"
msgstr "index"
''')
    assert entries['turbo-help-id\x041'] == 'index'
    with pytest.raises(HelpCompileError, match='unbekanntes Thema'):
        read_po('''msgid ""
msgstr ""

msgid "index"
msgstr "Start"

msgctxt "turbo-help-id"
msgid "1"
msgstr "missing"
''')


def test_project_build_named_hlp_contains_numeric_topic_alias(tmp_path):
    src = make_source(tmp_path, '%topic "index" 101\nHome\n%topic "test" 1234\nContent\n')
    exe = tmp_path / 'bin' / 'AppDB.exe'
    topics, po, hlp = compile_help_sources([src], exe)
    assert hlp == exe.with_suffix('.hlp')
    assert po == src.parent / 'AppDB.po'
    assert topics['test'] == 'Content'
    catalog = gettext.GNUTranslations(io.BytesIO(hlp.read_bytes()))
    assert catalog.pgettext(HELP_NUMBER_CONTEXT, '1234') == 'test'
    exe.write_bytes(b'MZ')
    assert install_help_catalog(exe, hlp) == hlp


def test_bridge_numeric_lookup_export_and_native_rendering():
    assert 'QHash<quint32, QString> helpNumbers_' in HELP
    assert 'QStringLiteral("turbo-help-id\\x04")' in HELP
    assert 'bool showTopicByNumber(quint32 number' in HELP
    assert 'if (ok && helpNumbers_.contains(number))' in HELP
    assert 'DBaseQtHelpShowTopicId(unsigned int helpNumber)' in H
    assert 'DBaseQtHelpShowTopicId @1018' in DEF
    assert 'extern "C" D64QT5_API int DBaseQtHelpShowTopicId(unsigned int helpNumber)' in CPP
    assert 'g_turbo_help_window->showTopicByNumber(helpNumber)' in CPP


def test_yellow_border_5_pixel_shadow_and_root_frame_character_gap():
    assert 'border:2px solid #ffe600' in HELP
    assert 'shadow->setOffset(5.0, 5.0);' in HELP
    assert 'shadow->setBlurRadius(0.0);' in HELP
    assert 'browser_->document()->setDocumentMargin(0.0);' in HELP
    assert 'format.setLeftMargin(qreal(qMax(1, gridCellWidth_)));' in HELP
    assert 'root->setFrameFormat(format);' in HELP
    assert 'margin:0;padding:0;font-family:Consolas' in HELP
    assert 'Hilfe:  ' in HELP

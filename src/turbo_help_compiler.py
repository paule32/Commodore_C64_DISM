#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turbo Vision Help compiler: %topic [number]/%include/%ref/%link -> GNU PO and MO.

Usage: python turbo_help_compiler.py source.thlp [--output-dir DIRECTORY]
The default topic is ``index``. No external dependencies / msgfmt needed.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import OrderedDict
from pathlib import Path


class HelpCompileError(ValueError):
    pass


_QUOTED = r'(?P<quote>[\'\"])(?P<name>.*?)(?P=quote)'
_TOPIC = re.compile(r'^\s*%topic\s+' + _QUOTED + r'(?:\s+(?P<number>[0-9]+))?\s*$', re.I)
_INCLUDE = re.compile(r'^\s*%include\s+(?:"([^"]+)"|\'([^\']+)\'|<([^>]+)>)\s*$', re.I)
_ANCHOR = re.compile(r'^\s*%anchor\s+#?([\w.-]+)\s*$', re.I)
_REF = re.compile(r'%(ref)\s+(?:"([^"]+)"|\'([^\']+)\'|([0-9]+))\s+#([\w.-]+)', re.I)
_LINK = re.compile(r'%(link)\s+(?:"([^"]+)"|\'([^\']+)\'|([0-9]+))', re.I)


# The GNU gettext context is serialized in .mo as "turbo-help-id\x04<number>".
# Each numeric entry points to the *name*, not a second copy of the help text.
HELP_NUMBER_CONTEXT = 'turbo-help-id'
MAX_HELP_NUMBER = 0xFFFFFFFF


class HelpTopicCatalog(OrderedDict):
    """Ordinary name->content mapping, with optional unique 32-bit help IDs."""

    def __init__(self, *args, topic_numbers=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.topic_numbers = dict(topic_numbers or {})  # number -> name


class HelpCompiler:
    def __init__(self, source: Path):
        self.source = source.expanduser().resolve(strict=True)
        self.root = self.source.parent
        self.topics: OrderedDict[str, list[str]] = OrderedDict()
        self.active: str | None = None
        self.stack: list[Path] = []
        self._visited_files: set[Path] = set()
        self.where: dict[str, str] = {}
        self.topic_numbers: dict[int, str] = {}
        self.number_where: dict[int, str] = {}

    def compile(self) -> OrderedDict[str, str]:
        self._visit(self.source)
        if 'index' not in self.topics:
            raise HelpCompileError('Das Standardthema %topic "index" fehlt.')
        return HelpTopicCatalog(((topic, '\n'.join(lines).rstrip('\n'))
                                 for topic, lines in self.topics.items()),
                                topic_numbers=self.topic_numbers)

    @classmethod
    def compile_files(cls, sources, *, root=None, include_paths=()):
        """Compile all registered .thlp project files into a shared topic catalog.

        Each source is parsed once; %include may pull additional topics.
        Duplicate topic definitions remain errors, including across files.
        """
        import os
        files = [Path(path).expanduser().resolve(strict=True) for path in sources]
        if not files:
            raise HelpCompileError('Keine Hilfedateien zum Kompilieren')
        instance = cls(files[0])
        instance.root = (Path(root).resolve() if root is not None else
                         Path(os.path.commonpath([str(p.parent) for p in files])))
        instance._project_files = tuple(files)
        instance._include_roots = tuple(dict.fromkeys(
            [instance.root, *(Path(p).resolve() for p in include_paths)]))
        for path in files:
            instance.active = None  # Each top-level source starts independently.
            instance._visit(path)
        if 'index' not in instance.topics:
            raise HelpCompileError('Das Standardthema %topic "index" fehlt.')
        return HelpTopicCatalog(((key, '\n'.join(lines).rstrip('\n'))
                                 for key, lines in instance.topics.items()),
                                topic_numbers=instance.topic_numbers)

    def _visit(self, path: Path) -> None:
        path = path.resolve(strict=True)
        registered = set(getattr(self, '_project_files', ()))
        allowed_roots = getattr(self, '_include_roots', (self.root,))
        if (path not in registered and
                not any(path.is_relative_to(root) for root in allowed_roots)):
            raise HelpCompileError(f'Include außerhalb des Hilfe-Verzeichnisses: {path}')
        if path in self.stack:
            raise HelpCompileError('Zyklisches %include: ' + ' -> '.join(map(str, self.stack + [path])))
        if path in self._visited_files:
            return
        if len(self.stack) >= 32:
            raise HelpCompileError('Maximale Include-Tiefe (32) überschritten.')
        self.stack.append(path)
        try:
            try:
                source = path.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeError) as exc:
                raise HelpCompileError(f'{path}: {exc}') from exc
            for number, line in enumerate(source.splitlines(), 1):
                location = f'{path.name}:{number}'
                include = _INCLUDE.fullmatch(line)
                if include:
                    name = next(x for x in include.groups() if x is not None)
                    if not name or Path(name).is_absolute():
                        raise HelpCompileError(f'{location}: ungültiger Include-Pfad')
                    try:
                        if hasattr(self, '_project_files'):
                            from turbo_help_project_tree import resolve_include
                            include_path = resolve_include(
                                name, path, self._project_files, self._include_roots)
                        else:
                            include_path = path.parent / name
                        # An include may define other topics; do not let its
                        # last topic steal subsequent lines of this source.
                        previous_topic = self.active
                        try:
                            self._visit(include_path)
                        finally:
                            self.active = previous_topic
                    except (OSError, ValueError) as exc:
                        raise HelpCompileError(f'{location}: %include {name}: {exc}') from exc
                    continue
                topic = _TOPIC.fullmatch(line)
                if topic:
                    name = topic.group('name').strip()
                    if not name:
                        raise HelpCompileError(f'{location}: leere Topic-ID')
                    if name in self.topics:
                        raise HelpCompileError(f'{location}: %topic {name!r} schon in {self.where[name]} definiert')
                    number_text = topic.group('number')
                    if number_text is not None:
                        # Canonical decimal form: 000123 and 123 refer to the same ID.
                        if len(number_text) > 10 or int(number_text) > MAX_HELP_NUMBER:
                            raise HelpCompileError(f'{location}: Hilfenummer außerhalb 0..{MAX_HELP_NUMBER}')
                        number = int(number_text)
                        if number in self.topic_numbers:
                            raise HelpCompileError(
                                f'{location}: Hilfenummer {number} schon für '
                                f'{self.topic_numbers[number]!r} in {self.number_where[number]} vergeben')
                        self.topic_numbers[number] = name
                        self.number_where[number] = location
                    self.topics[name] = []
                    self.where[name] = location
                    self.active = name
                    continue
                if line.lstrip().startswith(('%include', '%topic')):
                    raise HelpCompileError(f'{location}: fehlerhafte Präprozessoranweisung: {line.strip()}')
                if self.active is None:
                    if line.strip() and not line.lstrip().startswith('//'):
                        raise HelpCompileError(f'{location}: Text vor dem ersten %topic')
                    continue
                anchor = _ANCHOR.fullmatch(line)
                if anchor:
                    line = f'<anchor id="{anchor.group(1)}"></anchor>'
                elif line.lstrip().startswith('%anchor'):
                    raise HelpCompileError(f'{location}: ungültiger %anchor')
                line = _REF.sub(lambda m: f"<ref>'{m.group(2) or m.group(3) or m.group(4)}' #{m.group(5)}</ref>", line)
                line = _LINK.sub(lambda m: f"<link>'{m.group(2) or m.group(3) or m.group(4)}'</link>", line)
                self.topics[self.active].append(line)
        finally:
            self.stack.pop()
        self._visited_files.add(path)


def po_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_po(topics: dict[str, str], metadata=None) -> str:
    # Stage 688: optional project-specific Localize-compatible PO header.
    # Preserve the historic minimal header when called without metadata.
    if metadata is not None:
        from turbo_help_po_metadata import HEADER_FIELDS, normalize_po_settings
        values = normalize_po_settings({'headers': metadata})['headers']
        header = ('msgid ""\nmsgstr ""\n' + ''.join(
            po_quote(f'{key}: {values.get(key, "")}\n') + '\n'
            for key in HEADER_FIELDS) + '\n')
    else:
        header = (
        'msgid ""\nmsgstr ""\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '\n'
    )
    parts = [header]
    by_name: dict[str, int] = {}
    for raw_number, topic in getattr(topics, 'topic_numbers', {}).items():
        number = int(raw_number)
        if number < 0 or number > MAX_HELP_NUMBER or topic not in topics:
            raise HelpCompileError(f'Ungültige Hilfenummer/Ziel: {raw_number!r} -> {topic!r}')
        if topic in by_name:
            raise HelpCompileError(f'Thema {topic!r} besitzt mehrere Hilfenummern')
        by_name[topic] = number
    for name, content in topics.items():
        parts.append(f'msgid {po_quote(name)}\n')
        if '\n' in content:
            parts.append('msgstr ""\n')
            for chunk in content.splitlines(keepends=True):
                parts.append(po_quote(chunk) + '\n')
        else:
            parts.append(f'msgstr {po_quote(content)}\n')
        parts.append('\n')
        if name in by_name:
            # Standard GNU gettext msgctxt: the MO key is
            # "turbo-help-id\x04<number>"; msgstr stores the symbolic topic name.
            # The original msgid=name / msgstr=content is unchanged.
            parts.append(f'msgctxt {po_quote(HELP_NUMBER_CONTEXT)}\n')
            parts.append(f'msgid {po_quote(str(by_name[name]))}\n')
            parts.append(f'msgstr {po_quote(name)}\n\n')
    return ''.join(parts)


def read_po(source: str) -> dict[str, str]:
    """Read our GNU PO subset (msgctxt/msgid/msgstr with string continuations).

    For contextual entries, GNU .mo uses the standard key ``context\x04msgid``.
    Thus old text-based lookups and new numeric aliases coexist without changing
    the existing topics. The .po remains the source of truth for .mo generation.
    """
    entries: dict[str, str] = {}
    current_context: str | None = None
    current_id: str | None = None
    current_value = ''
    mode = ''

    def flush():
        nonlocal current_context, current_id, current_value, mode
        if current_context is not None and current_id is None:
            raise HelpCompileError('PO-Eintrag mit msgctxt ohne msgid')
        if current_id is not None:
            key = (current_context + '\x04' if current_context is not None else '') + current_id
            if key in entries:
                raise HelpCompileError(f'Doppelte msgid/msgctxt in PO: {key!r}')
            entries[key] = current_value
        current_context = None
        current_id = None
        current_value = ''
        mode = ''

    for line_number, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            if not line:
                flush()
            continue
        if line.startswith('msgctxt '):
            if current_id is not None:
                flush()
            elif current_context is not None:
                raise HelpCompileError(f'PO Zeile {line_number}: doppeltes msgctxt')
            try:
                current_context = json.loads(line[8:])
            except (ValueError, TypeError) as exc:
                raise HelpCompileError(f'PO Zeile {line_number}: ungültige msgctxt') from exc
            mode = 'ctxt'
        elif line.startswith('msgid '):
            if current_id is not None:
                flush()
            try:
                current_id = json.loads(line[6:])
            except (ValueError, TypeError) as exc:
                raise HelpCompileError(f'PO Zeile {line_number}: ungültige msgid') from exc
            mode = 'id'
        elif line.startswith('msgstr '):
            if current_id is None:
                raise HelpCompileError(f'PO Zeile {line_number}: msgstr ohne msgid')
            try:
                current_value = json.loads(line[7:])
            except (ValueError, TypeError) as exc:
                raise HelpCompileError(f'PO Zeile {line_number}: ungültige msgstr') from exc
            mode = 'str'
        elif line.startswith('"'):
            try:
                addition = json.loads(line)
            except (ValueError, TypeError) as exc:
                raise HelpCompileError(f'PO Zeile {line_number}: ungültige Fortsetzung') from exc
            if mode == 'ctxt' and current_context is not None:
                current_context += addition
            elif mode == 'id' and current_id is not None:
                current_id += addition
            elif mode == 'str':
                current_value += addition
            else:
                raise HelpCompileError(f'PO Zeile {line_number}: Fortsetzung ohne msgctxt/msgid/msgstr')
        else:
            raise HelpCompileError(f'PO Zeile {line_number}: nicht unterstützte Anweisung')
    flush()
    if '' not in entries:
        raise HelpCompileError('PO-Kopf mit Zeichensatzangabe fehlt')
    if 'index' not in entries:
        raise HelpCompileError('PO-Standardthema index fehlt')
    # Numeric associations must target existing topics, never arbitrary content.
    seen_targets = set()
    prefix = HELP_NUMBER_CONTEXT + '\x04'
    for key, topic in entries.items():
        if key.startswith(prefix):
            digits = key[len(prefix):]
            if not digits.isdecimal() or int(digits) > MAX_HELP_NUMBER:
                raise HelpCompileError(f'Ungültige Hilfenummer in msgctxt: {digits!r}')
            if topic not in entries:
                raise HelpCompileError(f'Hilfenummer {digits} verweist auf unbekanntes Thema {topic!r}')
            if topic in seen_targets:
                raise HelpCompileError(f'Doppelte Hilfenummernzuordnung für {topic!r}')
            seen_targets.add(topic)
    return entries


def write_mo(messages: dict[str, str]) -> bytes:
    """GNU gettext .mo revision 0, little-endian, UTF-8, no external msgfmt."""
    header = messages.get('') or 'Content-Type: text/plain; charset=UTF-8\nMIME-Version: 1.0\n'
    # Unlike Stage 687, keep the parsed PO metadata in the MO header.
    entries = sorted({**messages, '': header}.items(), key=lambda kv: kv[0].encode('utf-8'))
    ids = [key.encode('utf-8') for key, _ in entries]
    strs = [value.encode('utf-8') for _, value in entries]
    count = len(entries)
    source_table = 28
    translation_table = source_table + 8 * count
    strings_offset = translation_table + 8 * count
    blob = bytearray()
    source_records: list[tuple[int, int]] = []
    translation_records: list[tuple[int, int]] = []
    for item in ids:
        source_records.append((len(item), strings_offset + len(blob)))
        blob.extend(item + b'\0')
    for item in strs:
        translation_records.append((len(item), strings_offset + len(blob)))
        blob.extend(item + b'\0')
    out = bytearray(struct.pack('<7I', 0x950412DE, 0, count, source_table,
                                translation_table, 0, 0))
    for record in source_records + translation_records:
        out.extend(struct.pack('<2I', *record))
    out.extend(blob)
    return bytes(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output-dir', type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        topics = HelpCompiler(args.source).compile()
        directory = args.output_dir or args.source.resolve().parent
        directory.mkdir(parents=True, exist_ok=True)
        basename = args.source.stem
        po = directory / f'{basename}.po'
        hlp = directory / f'{basename}.hlp'
        po.write_text(write_po(topics), encoding='utf-8', newline='\n')
        hlp.write_bytes(write_mo(read_po(po.read_text(encoding='utf-8'))))
        print(f'Help Compiler: {len(topics)} Themen; PO: {po}; HLP: {hlp}')
        return 0
    except (HelpCompileError, OSError) as exc:
        print(f'Help Compiler Fehler: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

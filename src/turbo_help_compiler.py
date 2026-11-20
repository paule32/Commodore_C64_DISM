#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turbo Vision Help compiler: %topic/%include/%ref/%link -> GNU PO and MO.

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
_TOPIC = re.compile(r'^\s*%topic\s+' + _QUOTED + r'\s*$', re.I)
_INCLUDE = re.compile(r'^\s*%include\s+(?:"([^"]+)"|\'([^\']+)\'|<([^>]+)>)\s*$', re.I)
_ANCHOR = re.compile(r'^\s*%anchor\s+#?([\w.-]+)\s*$', re.I)
_REF = re.compile(r'%(ref)\s+(?:"([^"]+)"|\'([^\']+)\')\s+#([\w.-]+)', re.I)
_LINK = re.compile(r'%(link)\s+(?:"([^"]+)"|\'([^\']+)\')', re.I)


class HelpCompiler:
    def __init__(self, source: Path):
        self.source = source.expanduser().resolve(strict=True)
        self.root = self.source.parent
        self.topics: OrderedDict[str, list[str]] = OrderedDict()
        self.active: str | None = None
        self.stack: list[Path] = []
        self._visited_files: set[Path] = set()
        self.where: dict[str, str] = {}

    def compile(self) -> OrderedDict[str, str]:
        self._visit(self.source)
        if 'index' not in self.topics:
            raise HelpCompileError('Das Standardthema %topic "index" fehlt.')
        return OrderedDict((topic, '\n'.join(lines).rstrip('\n'))
                           for topic, lines in self.topics.items())

    @classmethod
    def compile_files(cls, sources):
        """Compile all registered .thlp project files into a shared topic catalog.

        Each source is parsed once; %include may pull additional topics.
        Duplicate topic definitions remain errors, including across files.
        """
        import os
        files = [Path(path).expanduser().resolve(strict=True) for path in sources]
        if not files:
            raise HelpCompileError('Keine Hilfedateien zum Kompilieren')
        instance = cls(files[0])
        instance.root = Path(os.path.commonpath([str(p.parent) for p in files]))
        for path in files:
            instance._visit(path)
        if 'index' not in instance.topics:
            raise HelpCompileError('Das Standardthema %topic "index" fehlt.')
        return OrderedDict((key, '\n'.join(lines).rstrip('\n'))
                           for key, lines in instance.topics.items())

    def _visit(self, path: Path) -> None:
        path = path.resolve(strict=True)
        if not path.is_relative_to(self.root):
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
                        self._visit(path.parent / name)
                    except OSError as exc:
                        raise HelpCompileError(f'{location}: %include {name}: {exc}') from exc
                    continue
                topic = _TOPIC.fullmatch(line)
                if topic:
                    name = topic.group('name').strip()
                    if not name:
                        raise HelpCompileError(f'{location}: leere Topic-ID')
                    if name in self.topics:
                        raise HelpCompileError(f'{location}: %topic {name!r} schon in {self.where[name]} definiert')
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
                line = _REF.sub(lambda m: f"<ref>'{m.group(2) or m.group(3)}' #{m.group(4)}</ref>", line)
                line = _LINK.sub(lambda m: f"<link>'{m.group(2) or m.group(3)}'</link>", line)
                self.topics[self.active].append(line)
        finally:
            self.stack.pop()
        self._visited_files.add(path)


def po_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_po(topics: dict[str, str]) -> str:
    header = (
        'msgid ""\nmsgstr ""\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '\n'
    )
    parts = [header]
    for name, content in topics.items():
        parts.append(f'msgid {po_quote(name)}\n')
        if '\n' in content:
            parts.append('msgstr ""\n')
            for chunk in content.splitlines(keepends=True):
                parts.append(po_quote(chunk) + '\n')
        else:
            parts.append(f'msgstr {po_quote(content)}\n')
        parts.append('\n')
    return ''.join(parts)


def read_po(source: str) -> dict[str, str]:
    """Read the msgid/msgstr subset generated by write_po().

    This makes PO the canonical intermediate representation: .mo is built
    from the actual .po data, not independently from the source topic map.
    """
    entries: dict[str, str] = {}
    current_id: str | None = None
    current_value = ''
    mode = ''

    def flush():
        nonlocal current_id, current_value, mode
        if current_id is not None:
            if current_id in entries:
                raise HelpCompileError(f'Doppelte msgid in PO: {current_id!r}')
            entries[current_id] = current_value
        current_id = None
        current_value = ''
        mode = ''

    for line_number, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            if not line:
                flush()
            continue
        if line.startswith('msgid '):
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
            if mode == 'id' and current_id is not None:
                current_id += addition
            elif mode == 'str':
                current_value += addition
            else:
                raise HelpCompileError(f'PO Zeile {line_number}: Fortsetzung ohne msgid/msgstr')
        else:
            raise HelpCompileError(f'PO Zeile {line_number}: nicht unterstützte Anweisung')
    flush()
    if '' not in entries:
        raise HelpCompileError('PO-Kopf mit Zeichensatzangabe fehlt')
    if 'index' not in entries:
        raise HelpCompileError('PO-Standardthema index fehlt')
    return entries


def write_mo(messages: dict[str, str]) -> bytes:
    """GNU gettext .mo revision 0, little-endian, UTF-8, no external msgfmt."""
    header = 'Content-Type: text/plain; charset=UTF-8\nMIME-Version: 1.0\n'
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
        mo = directory / f'{basename}.hlp'
        po.write_text(write_po(topics), encoding='utf-8', newline='\n')
        mo.write_bytes(write_mo(read_po(po.read_text(encoding='utf-8'))))
        print(f'Help Compiler: {len(topics)} Themen; PO: {po}; MO: {mo}')
        return 0
    except (HelpCompileError, OSError) as exc:
        print(f'Help Compiler Fehler: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

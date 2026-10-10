"""Zentrale Custom-Brush-Bibliothek (brush.json) im Anwendungsverzeichnis."""
import json
import os
import re
import tempfile
from pathlib import Path

FORMAT = 'd64-brush-library-v1'


def library_path():
    return Path(__file__).resolve().parent / 'brush.json'


def slug(text):
    result = re.sub(r'[^a-z0-9_-]+', '-', str(text).strip().lower()).strip('-')
    return result or 'muster'


def load_catalog(path=None):
    from d64_custom_brush import validated_pattern
    target = Path(path) if path is not None else library_path()
    if not target.exists():
        return []
    raw = json.loads(target.read_text(encoding='utf-8'))
    if not isinstance(raw, dict) or raw.get('format') != FORMAT or not isinstance(raw.get('patterns'), list):
        raise ValueError('Ungueltiges brush.json-Bibliotheksformat')
    entries, used = [], set()
    for source in raw['patterns']:
        if not isinstance(source, dict):
            continue
        try:
            pattern = validated_pattern(source)
        except (ValueError, TypeError, KeyError):
            continue
        identifier = str(source.get('id', '')).strip()
        if not identifier or identifier in used:
            continue
        used.add(identifier)
        entries.append(dict(id=identifier, name=str(source.get('name') or identifier), **pattern))
    return entries


def store_catalog(entries, path=None):
    target = Path(path) if path is not None else library_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {'format': FORMAT, 'patterns': entries}
    fd, temp_path = tempfile.mkstemp(prefix='.brush-', suffix='.json', dir=str(target.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temp_path, target)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def register_pattern(name, data, *, identifier=None, path=None):
    from d64_custom_brush import validated_pattern
    pattern = validated_pattern(data)
    entries = load_catalog(path)
    ident = identifier or slug(name)
    same = next((i for i, e in enumerate(entries) if e['id'] == ident), None)
    if same is None:
        base = ident
        counter = 2
        while any(e['id'] == ident for e in entries):
            ident = f'{base}-{counter}'
            counter += 1
    record = dict(id=ident, name=str(name), **pattern)
    if same is None:
        entries.append(record)
    else:
        entries[same] = record
    store_catalog(entries, path)
    return record

"""Stage 688: project-local gettext headers and paths for Turbo Vision help.

Independent from Qt so project persistence and PO/HLP generation can be tested
without running the IDE. Empty input/output overrides mean derive from the
marked main THLP. The compiled GNU gettext catalog uses the .hlp extension;
no separate .mo file is generated.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

def parse_po_header_datetime(value):
    """Parse existing gettext dates for the date/time editor (legacy-safe)."""
    text = str(value or '').strip()
    if not text:
        return None
    for pattern in ('%Y-%m-%d %H:%M%z', '%Y-%m-%d %H:%M:%S%z',
                    '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def format_po_header_datetime(year, month, day, hour, minute):
    """Serialize a selected local wall-clock time using gettext's UTC offset."""
    selected = datetime(int(year), int(month), int(day), int(hour), int(minute))
    return selected.astimezone().strftime('%Y-%m-%d %H:%M%z')


HEADER_FIELDS = (
    'Project-Id-Version', 'Report-Msgid-Bugs-To', 'POT-Creation-Date',
    'PO-Revision-Date', 'Last-Translator', 'Language-Team', 'Language',
    'MIME-Version', 'Content-Type', 'Content-Transfer-Encoding',
)


def default_po_headers(settings=None):
    now = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M%z')
    def saved(name, fallback=''):
        if settings is None:
            return fallback
        try:
            return str(settings.value('localize/header/' + name, fallback) or fallback).strip()
        except (AttributeError, RuntimeError, TypeError):
            return fallback

    language = saved('Language')
    if not language:
        try:
            src = str(settings.value('localize/source_lang', 'ENU') or 'ENU')
            dst = str(settings.value('localize/dest_lang', 'DEU') or 'DEU')
        except (AttributeError, RuntimeError, TypeError):
            src, dst = 'ENU', 'DEU'
        language = src + ':' + dst
    defaults = {
        'Project-Id-Version': '1.0', 'Report-Msgid-Bugs-To': '',
        'POT-Creation-Date': now, 'PO-Revision-Date': now,
        'Last-Translator': '', 'Language-Team': '', 'Language': language,
        'MIME-Version': '1.0', 'Content-Type': 'text/plain; charset=UTF-8',
        'Content-Transfer-Encoding': '8bit',
    }
    return {name: saved(name, defaults[name]) for name in HEADER_FIELDS}


def default_po_settings(settings=None):
    return {'input_file': '', 'output_file': '',
            'headers': default_po_headers(settings)}


def normalize_po_settings(value, *, defaults=None):
    result = default_po_settings() if defaults is None else {
        'input_file': str(defaults.get('input_file') or ''),
        'output_file': str(defaults.get('output_file') or ''),
        'headers': {name: str(defaults.get('headers', {}).get(name, ''))
                    for name in HEADER_FIELDS},
    }
    if not isinstance(value, dict):
        return result
    for field in ('input_file', 'output_file'):
        if field in value:
            result[field] = str(value.get(field) or '').strip()
    headers = value.get('headers')
    if isinstance(headers, dict):
        for name in HEADER_FIELDS:
            if name in headers:
                result['headers'][name] = str(headers[name] or '')
    return result


def default_catalog_paths(main_file, project_dir=None):
    """Recommend .po/.hlp next to the selected main entry (or project root)."""
    if main_file:
        main = Path(main_file).expanduser()
        return main.with_suffix('.po'), main.with_suffix('.hlp')
    base = Path(project_dir).expanduser() if project_dir else Path.cwd()
    return base / 'System.Help.po', base / 'System.Help.hlp'


def resolve_catalog_paths(settings, *, main_file=None, project_dir=None):
    state = normalize_po_settings(settings)
    suggested_po, suggested_hlp = default_catalog_paths(main_file, project_dir)
    base = Path(project_dir).resolve() if project_dir else suggested_po.parent.resolve()
    def resolve(raw, suggested, suffix):
        path = Path(raw).expanduser() if raw else suggested
        if not path.is_absolute():
            path = base / path
        if path.suffix.casefold() != suffix:
            raise ValueError(f'Der Dateiname muss auf {suffix} enden: {path}')
        return path.resolve()
    po = resolve(state['input_file'], suggested_po, '.po')
    hlp = resolve(state['output_file'], suggested_hlp, '.hlp')
    if po == hlp:
        raise ValueError('PO und HLP dürfen nicht denselben Dateinamen haben')
    return po, hlp

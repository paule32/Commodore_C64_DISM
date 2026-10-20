"""Small, GUI-independent helpers for Stage 472 WFM assembly include tabs."""
from pathlib import Path
import re

_INCLUDE = re.compile(r'(?i)(?<![\w])%include\s+(["\'])([^"\'\r\n]+)\1')


def include_at_position(line: str, column: int):
    """Return quoted include name only if the mouse hits the quoted path."""
    body = str(line).split(';', 1)[0]
    for match in _INCLUDE.finditer(body):
        if match.start(2) <= column <= match.end(2):
            return match.group(2)
    return None


def resolve_wfm_include(name, working_directory, input_directories=()):
    """Resolve cwd first, then project input dirs. Return (file, searched, failure)."""
    value = str(name or '').strip()
    if not value or '\0' in value:
        return None, (), 'Ungueltiger Include-Dateiname'
    target = Path(value).expanduser()
    bases = [Path(working_directory).expanduser(), *(Path(p).expanduser() for p in input_directories)]
    paths = [target] if target.is_absolute() else [base / target for base in bases]
    checked = []
    errors = []
    for path in paths:
        try:
            resolved = path.resolve(strict=False)
            if resolved in checked:
                continue
            checked.append(resolved)
            if resolved.is_file():
                # The caller performs the actual read and handles permissions.
                return resolved, tuple(checked), None
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(f'{path}: {exc}')
    return None, tuple(checked), '\n'.join(errors) if errors else 'Datei nicht gefunden'

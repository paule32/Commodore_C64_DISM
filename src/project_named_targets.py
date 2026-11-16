"""Stage 596: language-specific named projects and robust .pro metadata.

The language identifier is the persistent identity.  Users may rename the
project without breaking source assignments.  A project may be compiled as an
executable or a library; the selected kind is intentionally separate from the
source's intrinsic PROGRAM/LIBRARY declaration.
"""
from __future__ import annotations

import json
from typing import Mapping

LANGUAGES = (
    ("basic", "BASIC"),
    ("pascal", "Pascal"),
    ("prolog", "Prolog"),
    ("assembler", "Assembler"),
    ("lisp", "Lisp"),
    ("dbase", "dBASE"),
)
LANGUAGE_IDS = frozenset(language for language, _ in LANGUAGES)
# Stage 597: program and library use distinct names in Pascal and dBASE.
# The legacy ``pascal`` / ``dbase`` keys remain accepted for old .pro files.
PROFILE_FIELDS = (
    ("basic", "BASIC"),
    ("pascal_program", "Pascal EXE"),
    ("pascal_library", "Pascal DLL"),
    ("dbase_program", "dBASE EXE"),
    ("dbase_library", "dBASE DLL"),
    ("prolog", "Prolog"),
    ("assembler", "Assembler"),
    ("lisp", "Lisp"),
)


def profile_key(language: str, kind: str) -> str:
    language, kind = str(language).casefold(), str(kind).casefold()
    if language in {"pascal", "dbase"} and kind in {"program", "library"}:
        return f"{language}_{kind}"
    return language


def profile_name(names: Mapping | None, language: str, kind: str) -> str:
    source = names if isinstance(names, Mapping) else {}
    key = profile_key(language, kind)
    if key in source:
        return str(source.get(key, "") or "").strip()
    return str(source.get(language, "") or "").strip()


def assignment_matches(assignment: str, language: str, kind: str) -> bool:
    """Legacy language-only assignments belong to either kind until edited."""
    assignment = str(assignment or "").casefold()
    return assignment == str(language).casefold() or assignment == f"{language}|{kind}".casefold()


def assignment_is_valid(value: str) -> bool:
    value = str(value or "").casefold()
    if value in LANGUAGE_IDS:
        return True
    language, kind = normalize_selection(value)
    return bool(language and kind)
KINDS = frozenset(("program", "library"))

NAMES_KEY = "__named_project_names__"
SELECTED_KEY = "__named_project_selected__"
ASSIGNMENTS_KEY = "__named_project_assignments__"
NAMES_SECTION = "Project.NamedTargets"
ASSIGNMENTS_SECTION = "Project.NamedTargetFiles"


def normalize_names(names: Mapping | None) -> dict[str, str]:
    source = names if isinstance(names, Mapping) else {}
    result = {language: str(source.get(language, "") or "").strip()
              for language, _ in LANGUAGES}
    for key, _title in PROFILE_FIELDS:
        if key not in result:
            language = key.rsplit("_", 1)[0] if key.endswith(("_program", "_library")) else key
            # Only migrate absent keys; deliberately empty new fields stay empty.
            result[key] = str(source.get(key, source.get(language, "")) or "").strip()
    return result


def normalize_selection(selection) -> tuple[str, str]:
    if isinstance(selection, str) and "|" in selection:
        language, kind = selection.split("|", 1)
    elif isinstance(selection, (tuple, list)) and len(selection) == 2:
        language, kind = selection
    elif isinstance(selection, Mapping):
        language, kind = selection.get("language"), selection.get("kind")
    else:
        return "", ""
    language, kind = str(language or "").casefold(), str(kind or "").casefold()
    return (language, kind) if language in LANGUAGE_IDS and kind in KINDS else ("", "")



def legacy_pascal_ancestry(ancestry) -> list[str]:
    """Preserve saved Stage-596/597 Pascal assignment keys after Stage 601.

    Only presentation changes: Pascal-Programme -> Windows PE32 Module
    replaces Pascal-Programme -> Windows PE32 -> Module. The old project
    file identity is still used so existing .pro associations survive.
    """
    parts = [str(part) for part in ancestry]
    if not parts or parts[0].strip().casefold() not in {
            "pascal-programme", "pascal programme", "pascal-programs"}:
        return parts
    prefixes = (("Windows PE32+", "Windows PE32+"),
                ("Windows PE32", "Windows PE32"))
    roles = (("Ressourcen", "Resourcen"), ("Resourcen", "Resourcen"),
             ("Tabellen", "Tabellen"), ("Modules", "Module"),
             ("Module", "Module"), ("Units", "Unit"), ("Unit", "Unit"))
    for i in range(1, len(parts)):
        label = parts[i].strip()
        for prefix, old_prefix in prefixes:
            if not label.casefold().startswith((prefix + " ").casefold()):
                continue
            suffix = label[len(prefix):].strip()
            for role, old_role in roles:
                if suffix.casefold() == role.casefold():
                    return parts[:i] + [old_prefix, old_role] + parts[i+1:]
    return parts


def leaf_key(path: str, node_kind: str, ancestry) -> str:
    """Stable per-branch key, even if a file belongs to multiple target nodes."""
    # Stage 601: presentation-only Pascal tree flattening must not change
    # project file assignment identities stored in existing .pro files.
    parts = [str(part).strip().casefold()
             for part in legacy_pascal_ancestry(ancestry)]
    normalized_path = str(path or "").strip().replace("\\", "/").casefold()
    return json.dumps([normalized_path, str(node_kind or "").casefold(), parts],
                      ensure_ascii=False, separators=(",", ":"))


def rebase_leaf_key(key: str, project_path, *, to_storage: bool, path_converter) -> str:
    """Convert the path inside a saved assignment key for portable .pro files.

    Other key components (node kind / branch identity) are kept byte-for-byte.
    The caller supplies the existing project path storage/restore function.
    Unknown legacy key shapes remain unchanged rather than being destroyed.
    """
    try:
        parts = json.loads(key)
        if not (isinstance(parts, list) and len(parts) == 3
                and isinstance(parts[0], str) and isinstance(parts[2], list)):
            return key
        new_path = path_converter(parts[0], project_path)
        parts[0] = str(new_path).replace("\\", "/").casefold()
        return json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    except (ValueError, TypeError, OSError, RuntimeError):
        return key


def encode_names(parser, names: Mapping, selection, assignments: Mapping) -> None:
    clean_names = normalize_names(names)
    language, kind = normalize_selection(selection)
    parser[NAMES_SECTION] = {
        "Version": "1",
        "Names": json.dumps(clean_names, ensure_ascii=False, sort_keys=True),
        "Selection": json.dumps({"language": language, "kind": kind}),
    }
    parser[ASSIGNMENTS_SECTION] = {"Version": "1"}
    for index, (key, assigned_language) in enumerate(sorted(assignments.items()), 1):
        if not assignment_is_valid(assigned_language) or not key:
            continue
        parser[ASSIGNMENTS_SECTION][f"Item{index:04d}"] = json.dumps(
            {"key": str(key), "language": assigned_language},
            ensure_ascii=False, separators=(",", ":"))


def decode_names(parser) -> tuple[dict[str, str], tuple[str, str], dict[str, str]]:
    names, selection, assignments = normalize_names(None), ("", ""), {}
    if parser.has_section(NAMES_SECTION):
        try:
            names = normalize_names(json.loads(parser.get(NAMES_SECTION, "Names", fallback="{}")))
        except (TypeError, ValueError):
            pass
        try:
            selection = normalize_selection(json.loads(
                parser.get(NAMES_SECTION, "Selection", fallback="{}")))
        except (TypeError, ValueError):
            pass
    if parser.has_section(ASSIGNMENTS_SECTION):
        for option, raw in parser.items(ASSIGNMENTS_SECTION):
            if not option.casefold().startswith("item"):
                continue
            try:
                entry = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(entry, dict):
                continue
            language = str(entry.get("language", "")).casefold()
            key = str(entry.get("key", ""))
            if assignment_is_valid(language) and key:
                assignments[key] = language
    return names, selection, assignments

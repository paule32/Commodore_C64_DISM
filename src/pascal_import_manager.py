"""Stage 541: deterministic Pascal import manifest, linker hints and on-disk cache.

The cache stores only declarations and symbol usage, NEVER addresses or loaded
Windows-module handles. Each entry is immutable and written atomically so two
parallel Pascal workers can safely produce the same cache key.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
import hashlib
import json
import os
import re
import tempfile

SCHEMA_VERSION = 1
IMPORT_MANAGER_VERSION = "541.1"
_TARGETS = {"pe32", "pe64"}
_DECL = re.compile(r'^\s*(import|extern)\s+([^,\s;]+)\s*(?:,\s*"([^"\r\n]+)"\s*,\s*"([^"\r\n]+)")?\s*(?:;.*)?$', re.I)
_TOKEN_BOUNDARY = r"[A-Za-z0-9_.$?@]"


def normalize_target(target: str) -> str:
    key = str(target).strip().lower()
    if key in {"pe32", "win32", "windows", "windows-pe32"}:
        return "pe32"
    if key in {"pe64", "win64", "windows64", "windows-pe64", "windows-pe32+"}:
        return "pe64"
    raise ValueError("Import-Cache unterstützt nur Windows PE32/PE32+: " + str(target))


def cache_root(output_directory=None, filename=None, explicit=None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    if output_directory:
        return Path(output_directory).expanduser().resolve() / ".d64cache" / "imports"
    if filename and not str(filename).startswith("<"):
        return Path(filename).expanduser().resolve().parent / ".d64cache" / "imports"
    return Path.cwd().resolve() / ".d64cache" / "imports"


def _sha(text: bytes) -> str:
    return hashlib.sha256(text).hexdigest()


def _strip_asm_comment(raw: str) -> str:
    quote = None
    for pos, char in enumerate(raw):
        if quote is not None:
            if char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == ";":
            return raw[:pos]
    return raw


def _code_lines(source: str) -> list[str]:
    """Exclude import/extern metadata and comments, not data or relocations.

    Unknown preprocessors/macros are explicitly handled as conservative usage.
    """
    rows = []
    for raw in source.splitlines():
        if _DECL.fullmatch(raw.strip()):
            continue
        # This internal assembler uses ';' as its comment delimiter.
        rows.append(_strip_asm_comment(raw))
    return rows


def _referenced(code: str, symbol: str) -> bool:
    return re.search(
        rf"(?<!{_TOKEN_BOUNDARY}){re.escape(symbol)}(?!{_TOKEN_BOUNDARY})",
        code, flags=re.IGNORECASE,
    ) is not None


def analyze_assembly(source: str, target: str, *,
                     conservative: bool = False) -> dict:
    target = normalize_target(target)
    seen: dict[str, dict] = {}
    declared: list[dict] = []
    for number, line in enumerate(source.splitlines(), 1):
        match = _DECL.fullmatch(line.strip())
        if not match:
            continue
        directive, symbol, dll, member = match.groups()
        is_import = directive.casefold() == "import"
        if is_import and (not dll or not member):
            # Do not silently mutate declarations we cannot round-trip.
            conservative = True
        item = {"kind": directive.casefold(), "symbol": symbol,
                "dll": dll if is_import else None,
                "member": member if is_import else None,
                "line": number}
        key = symbol.casefold()
        old = seen.get(key)
        if old is not None:
            # Duplicate identical declarations are harmless; conflicting DLL or
            # external symbol declarations must not be silently reconciled.
            if ((old["kind"], old["dll"], old["member"]) !=
                    (item["kind"], item["dll"], item["member"])):
                raise ValueError(f"Widersprüchliche Import-Deklaration für {symbol}: Zeile {number}")
            item["duplicate"] = True
        else:
            seen[key] = item
        declared.append(item)
    body = "\n".join(_code_lines(source))
    # The assembler's preprocessor can introduce references later. In that case
    # an unused-import decision based solely on the raw ASM is unsafe.
    if re.search(r"^\s*(?:%include|%define|%macro|\.include)\b", body, re.I | re.M):
        conservative = True
    for item in declared:
        item["used"] = bool(conservative or _referenced(body, item["symbol"]))
    return {
        "schema": SCHEMA_VERSION,
        "version": IMPORT_MANAGER_VERSION,
        "target": target,
        "conservative": bool(conservative),
        "imports": [item for item in declared if item["kind"] == "import"],
        "externals": [item for item in declared if item["kind"] == "extern"],
        "declared": len(declared),
        "used": sum(bool(x["used"]) for x in declared),
        "unused": sum(not x["used"] for x in declared),
    }


def prune_assembly(source: str, manifest: dict, *,
                   keep_line_numbers: bool = True) -> str:
    """Remove only proven-unused declaration lines, never code/data labels.

    The actual COFF linker performs cross-module liveness and import merging.
    Line-preserving comments avoid invalidating the Pascal source map.
    """
    candidates = {
        item["line"] for item in manifest.get("imports", []) + manifest.get("externals", [])
        if not item.get("used") or item.get("duplicate")
    }
    if not candidates:
        return source
    rows = source.splitlines(keepends=True)
    for number in candidates:
        i = number - 1
        if i >= len(rows):
            continue
        if keep_line_numbers:
            suffix = "\r\n" if rows[i].endswith("\r\n") else "\n" if rows[i].endswith("\n") else ""
            rows[i] = "; Stage 541: unbenutzte/duplizierte Import-Deklaration" + suffix
        else:
            rows[i] = ""
    return "".join(rows)


def _runtime_fingerprints(source: str, output_directory, filename) -> dict:
    """Invalidate cached import metadata when a local runtime DLL changes."""
    candidates = []
    if output_directory:
        candidates.append(Path(output_directory).expanduser())
    if filename and not str(filename).startswith("<"):
        candidates.append(Path(filename).expanduser().resolve().parent)
    candidates.append(Path.cwd())
    imports = {str(m.group(3)).casefold() for raw in source.splitlines()
               if (m := _DECL.fullmatch(raw.strip())) and m.group(1).casefold() == "import"
               and m.group(3) and m.group(3).casefold().startswith("libd64_")}
    result = {}
    for dll in sorted(imports):
        for directory in candidates:
            path = directory / dll
            if not path.is_file():
                continue
            try:
                with path.open("rb") as stream:
                    result[dll] = hashlib.file_digest(stream, "sha256").hexdigest()
                break
            except OSError:
                continue
    return result


def _atomic_json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".d64imp-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def process_assembly(source: str, target: str, *,
                     source_text: Optional[str] = None,
                     filename: Optional[str] = None,
                     output_directory=None,
                     explicit_cache_root=None,
                     runtime_version: str = "libd64_runtime",
                     configuration: Optional[dict] = None,
                     cache_enabled: bool = True,
                     prune_unused: bool = True,
                     conservative: bool = False) -> tuple[str, dict]:
    """Return optimized ASM and a manifest; cache reuse is content-addressed.

    `conservative=True` for UNITs, mixed-language inputs or uninspected COFF
    objects: the final linker, not a single source file, owns import liveness.
    """
    target = normalize_target(target)
    config = configuration or {}
    source_digest = _sha((source_text or "").encode("utf-8"))
    asm_digest = _sha(source.encode("utf-8"))
    key_document = {
        "schema": SCHEMA_VERSION, "version": IMPORT_MANAGER_VERSION,
        "target": target, "source_hash": source_digest,
        "assembly_hash": asm_digest, "config": config,
        "runtime_version": str(runtime_version),
        "runtime_dll_hashes": _runtime_fingerprints(source, output_directory, filename),
        "conservative": bool(conservative),
    }
    cache_key = _sha(json.dumps(key_document, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    root = cache_root(output_directory, filename, explicit_cache_root)
    cache_file = root / target / (cache_key + ".json")
    hit = False
    manifest = None
    if cache_enabled:
        try:
            existing = json.loads(cache_file.read_text(encoding="utf-8"))
            if existing.get("key") == key_document and isinstance(existing.get("manifest"), dict):
                manifest = existing["manifest"]
                hit = True
        except (OSError, ValueError, TypeError, UnicodeError):
            pass
    if manifest is None:
        manifest = analyze_assembly(source, target, conservative=conservative)
        if cache_enabled:
            try:
                _atomic_json_write(cache_file, {"key": key_document, "manifest": manifest})
            except OSError:
                # Cache is an optimization, not a required compilation input.
                pass
    manifest = dict(manifest)
    manifest["source_hash"] = source_digest
    manifest["assembly_hash"] = asm_digest
    manifest["cache_key"] = cache_key
    manifest["cache_hit"] = hit
    manifest["cache_file"] = str(cache_file) if cache_enabled else None
    manifest["pruned"] = bool(prune_unused and not manifest["conservative"])
    result = prune_assembly(source, manifest) if manifest["pruned"] else source
    return result, manifest


def write_manifest(path, manifest: dict) -> Path:
    path = Path(path)
    _atomic_json_write(path, manifest)
    return path


def clear_cache(root, target: Optional[str] = None) -> int:
    """Delete only hashed Stage-541 import cache entries, never output files."""
    root = Path(root).expanduser().resolve()
    targets = (normalize_target(target),) if target else ("pe32", "pe64")
    count = 0
    for arch in targets:
        directory = root / arch
        if not directory.is_dir():
            continue
        for entry in directory.glob("*.json"):
            if re.fullmatch(r"[0-9a-f]{64}\.json", entry.name):
                entry.unlink()
                count += 1
    return count


def _import_spec_pair(spec) -> tuple[str, str]:
    if isinstance(spec, dict):
        member = spec.get("ordinal")
        if member is not None:
            member = "#" + str(member)
        else:
            member = spec.get("member", spec.get("name", ""))
        return str(spec.get("dll", "")), str(member)
    return str(spec[0]), str(spec[1])


def link_manifest_from_parsed_objects(parsed_objects: Iterable, target: str,
                                      used_imports: dict,
                                      *, output_file: Optional[str] = None) -> dict:
    """Link-wide manifest from COFF metadata and actual relocation-selected IAT.

    Excludes dead imports and records the DLL-name/export mapping of the exact
    set of imported symbols actually needed by the entire link (all units).
    """
    target = normalize_target(target)
    declared: dict[str, tuple[str, str]] = {}
    for obj in parsed_objects:
        for symbol, spec in getattr(obj, "imports", {}).items():
            name = symbol.casefold()
            pair = _import_spec_pair(spec)
            if name in declared and (declared[name][0].casefold(), declared[name][1]) != (pair[0].casefold(), pair[1]):
                raise ValueError(f"Widersprüchliche Importziele bei {symbol}")
            declared[name] = pair
    entries = []
    for symbol, spec in sorted(used_imports.items()):
        dll, member = _import_spec_pair(spec)
        entries.append({"symbol": str(symbol), "dll": dll, "member": member})
    return {"schema": SCHEMA_VERSION, "version": IMPORT_MANAGER_VERSION,
            "target": target, "output": output_file,
            "imports": entries, "used": len(entries),
            "unused_declared": sorted(set(declared) - set(used_imports))}


def externalize_declarations(source: str, assembly_path, *,
                             use_preprocessor_lines: bool = False):
    """Move assembler IMPORT/EXTERN lines to a sibling `.imports.inc` file.

    The internal Windows ASM preprocessor expands `%include` before COFF
    parsing.  By default declaration lines are replaced by empty placeholders
    (legacy Stage-541 behavior).  In compact mode, contiguous declaration and
    removed-import-placeholder blocks become one `%include` plus `%line N`.
    N is the logical line number of the *next* retained original ASM line.
    """
    rows = source.splitlines(keepends=True)
    declaration_lines = []
    declaration_indices = []
    for index, raw in enumerate(rows):
        if _DECL.fullmatch(raw.strip()):
            declaration_indices.append(index)
            declaration_lines.append(raw.rstrip("\r\n"))
    if not declaration_indices:
        return source, None, None
    path = Path(str(assembly_path) + ".imports.inc")
    include = '%include "' + path.name + '"'
    if use_preprocessor_lines:
        # Stage 550: the Stage-541 import pruning pass can leave placeholder
        # comments in the header.  They are removed together with the import
        # declarations, without discarding actual comments or code lines.
        # Non-contiguous declaration blocks are handled independently.
        obsolete = re.compile(
            r"^\s*;\s*Stage 541:\s*unbenutzte/duplizierte "
            r"Import-Deklaration\s*$")

        def removable(index: int) -> bool:
            row = rows[index].strip()
            return bool(not row or _DECL.fullmatch(row) or obsolete.fullmatch(row))

        newline = "\r\n" if "\r\n" in source else "\n"
        out = []
        cursor = 0
        used_include = False
        while cursor < len(rows):
            # A pruned import may precede the first retained declaration.
            # Include that marker in the collapsed import block too.
            if not (_DECL.fullmatch(rows[cursor].strip()) or
                    obsolete.fullmatch(rows[cursor].strip())):
                out.append(rows[cursor])
                cursor += 1
                continue
            end = cursor + 1
            while end < len(rows) and removable(end):
                end += 1
            # For the usual contiguous import header there is precisely one
            # include and one line directive.  The next *original* line is
            # 1-based end+1; NASM applies %line to the line after the marker.
            has_declarations = any(
                _DECL.fullmatch(rows[i].strip()) for i in range(cursor, end))
            if has_declarations and not used_include:
                out.append(include + newline)
                used_include = True
            out.append(f"%line {end + 1}" + newline)
            cursor = end
        return "".join(out), path, "\n".join(declaration_lines) + "\n"

    for index in declaration_indices:
        ending = "\r\n" if rows[index].endswith("\r\n") else "\n" if rows[index].endswith("\n") else ""
        rows[index] = (include if index == declaration_indices[0] else
                       "") + ending
    return "".join(rows), path, "\n".join(declaration_lines) + "\n"

"""Stage 524: verlustarmes DBF-PACK mit externen dBASE-III NDX Indizes.

MDX wird von einer echten dBASE-IV-MDX-Engine erstellt (Windows ODBC oder
konfigurierter MDX-Writer). Kein proprietaerer Pseudo-MDX-Container.
Diese Operation fasst nur physisch als geloescht markierte DBF-Records an.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence
import datetime
import os
import shutil
import stat
import struct
import subprocess
import tempfile
import math


@dataclass(frozen=True)
class PackResult:
    removed: int
    remaining: int
    ndx_files: tuple[Path, ...]
    mdx_file: Optional[Path]


@dataclass(frozen=True)
class _Field:
    name: str
    type: str
    offset: int
    length: int


def _parse_dbf(blob: bytes):
    if len(blob) < 33:
        raise ValueError('DBF-Datei ist unvollstaendig.')
    version = blob[0]
    # DBase III/IV/V, keine FoxPro/CDX-Datenbank oder verschluesselte DBF.
    if version not in (0x03, 0x04, 0x05, 0x83, 0x8B):
        raise ValueError(f'Nicht unterstuetzte DBF-Version: 0x{version:02X}.')
    if blob[15]:
        raise ValueError('Verschluesselte DBF-Dateien werden nicht gepackt.')
    count = struct.unpack_from('<I', blob, 4)[0]
    header_len, record_len = struct.unpack_from('<HH', blob, 8)
    if header_len < 33 or header_len > len(blob) or record_len < 1:
        raise ValueError('Ungueltiger DBF-Header.')
    if count > (len(blob) - header_len) // record_len:
        raise ValueError('DBF-Datensatzbereich ist abgeschnitten; Pack abgebrochen.')
    fields = []
    offset = 1
    ptr = 32
    while ptr + 32 <= header_len and blob[ptr] != 0x0D:
        desc = blob[ptr:ptr + 32]
        try:
            name = desc[:11].split(b'\0', 1)[0].decode('ascii')
        except UnicodeDecodeError as exc:
            raise ValueError('Ungueltiger DBF-Feldname.') from exc
        if not name or not desc[16]:
            raise ValueError('Leeres DBF-Feld / Feldbreite.')
        fields.append(_Field(name, chr(desc[11]), offset, desc[16]))
        offset += desc[16]
        ptr += 32
    if not fields or offset != record_len or ptr >= header_len or blob[ptr] != 0x0D:
        raise ValueError('DBF-Felddefinitionen passen nicht zur Datensatzbreite.')
    records = []
    deleted = 0
    for i in range(count):
        rec = blob[header_len + i * record_len:header_len + (i + 1) * record_len]
        if rec[0] == 0x2A:
            deleted += 1
        elif rec[0] == 0x20:
            records.append(rec)
        else:
            raise ValueError(f'Unbekannte DBF-Loeschmarkierung in Datensatz {i + 1}.')
    return fields, header_len, record_len, records, deleted


def _ndx_key(field: _Field, rec: bytes) -> bytes:
    raw = rec[field.offset:field.offset + field.length]
    if field.type in ('N', 'F'):
        try:
            val = float(raw.strip().decode('ascii') or '0')
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError(f'Nicht-numerischer Indexwert in {field.name}.') from exc
        if not math.isfinite(val):
            raise ValueError(f'Ungueltiger numerischer Indexwert in {field.name}.')
        return struct.pack('<d', val)
    if field.type == 'D':
        if raw.strip() and (len(raw) != 8 or not raw.isdigit()):
            raise ValueError(f'Ungueltiges DBF-Datum in {field.name}.')
        return raw.ljust(8, b' ')
    if field.type == 'L':
        return raw[:1].upper()
    if field.type == 'C':
        return raw
    raise ValueError(f'Nicht unterstuetzter Indextyp {field.type} in {field.name}.')


def build_ndx_bytes(field: _Field, records: Sequence[bytes]) -> bytes:
    """dBASE-III-NDX mit 512-Byte-B-Baumseiten und physischen 1-basierten RecNos."""
    if field.type == 'M':
        raise ValueError('Memo-Felder koennen nicht indiziert werden.')
    key_len = 8 if field.type in ('N', 'F', 'D') else field.length
    if key_len < 1 or key_len >= 100:
        raise ValueError(f'NDX-Schluessel {field.name} muss 1..99 Bytes lang sein.')
    recsize = 8 + ((key_len + 3) // 4) * 4
    maxkeys = (512 - 8) // recsize
    if maxkeys < 2:
        raise ValueError('NDX-Indexschluessel zu lang.')
    all_entries = []
    for i, rec in enumerate(records, 1):
        key = _ndx_key(field, rec)
        # NDX numeric comparison uses IEEE754 values, never lexical byte sorting.
        key_order = struct.unpack('<d', key)[0] if field.type in ('N', 'F') else key
        all_entries.append((key_order, i, key))
    all_entries.sort(key=lambda x: (x[0], x[1]))

    # Voller B-Baum: Schluessel stehen EXAKT einmal im Baum, auch wenn
    # Innenseiten nach dem Split selbst Recordreferenzen enthalten.
    from bisect import bisect_right

    class Node:
        def __init__(self, keys=None, children=None):
            self.keys = list(keys or [])
            self.children = list(children or [])

    root_node = Node()

    def insert(node, entry):
        if node.children:
            child_index = bisect_right([(e[0], e[1]) for e in node.keys],
                                       (entry[0], entry[1]))
            split = insert(node.children[child_index], entry)
            if split is not None:
                middle, right = split
                node.keys.insert(child_index, middle)
                node.children.insert(child_index + 1, right)
        else:
            pos = bisect_right([(e[0], e[1]) for e in node.keys],
                               (entry[0], entry[1]))
            node.keys.insert(pos, entry)
        if len(node.keys) <= maxkeys:
            return None
        mid = len(node.keys) // 2
        middle = node.keys[mid]
        right = Node(node.keys[mid + 1:],
                     node.children[mid + 1:] if node.children else [])
        node.keys = node.keys[:mid]
        if node.children:
            node.children = node.children[:mid + 1]
        return middle, right

    for entry in all_entries:
        split = insert(root_node, entry)
        if split is not None:
            separator, right = split
            root_node = Node([separator], [root_node, right])

    pages: list[bytes] = []

    def emit_page(node):
        child_pages = [emit_page(child) for child in node.children]
        data = bytearray(512)
        struct.pack_into('<I', data, 0, len(node.keys))
        for i, (_sort, recno, key) in enumerate(node.keys):
            pos = 4 + i * recsize
            child = child_pages[i] if child_pages else 0
            struct.pack_into('<II', data, pos, child, recno)
            data[pos + 8:pos + 8 + len(key)] = key
        struct.pack_into('<I', data, 4 + len(node.keys) * recsize,
                         child_pages[-1] if child_pages else 0)
        pages.append(bytes(data))
        return len(pages)

    root = emit_page(root_node)

    header = bytearray(512)
    struct.pack_into('<IIIHHHI', header, 0, root, 1 + len(pages), len(all_entries) + 1,
                     key_len, maxkeys, int(field.type in ('N', 'F')), recsize)
    expr_text = f'DTOS({field.name})' if field.type == 'D' else field.name
    expr = expr_text.encode('ascii')[:100]
    header[24:24 + len(expr)] = expr
    return bytes(header) + b''.join(pages)


def _write_mdx_odbc(dbf_path: Path, names: Sequence[str]):
    """Optionaler echter dBASE-IV/5 MDX-Writer via installiertem Windows-ODBC."""
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError('MDX benötigt den Windows-dBASE-ODBC-Treiber und pyodbc oder '
                           'einen externen MDX-Writer (D64_DBASE_MDX_WRITER).') from exc
    available = [name for name in pyodbc.drivers() if 'dBASE' in name]
    if not available:
        raise RuntimeError('Kein dBASE-ODBC-Treiber gefunden: MDX kann nicht sicher erzeugt werden.')
    driver = available[-1]
    connection = pyodbc.connect(f'DRIVER={{{driver}}};DBQ={dbf_path.parent};', autocommit=True)
    try:
        with connection.cursor() as cur:
            for name in names:
                # Felder aus validiertem DBF-Header, keine freien SQL-Ausdruecke.
                cur.execute(f'CREATE INDEX [{name}] ON [{dbf_path.name}] ([{name}])')
    finally:
        connection.close()


def _build_mdx(dbf_path: Path, names: Sequence[str], mdx_writer=None):
    if not names:
        return None
    if mdx_writer is not None:
        mdx_writer(dbf_path, tuple(names))
    elif os.environ.get('D64_DBASE_MDX_WRITER'):
        executable = Path(os.environ['D64_DBASE_MDX_WRITER'])
        if not executable.is_file():
            raise FileNotFoundError(f'Konfigurierter MDX-Writer fehlt: {executable}')
        completed = subprocess.run([str(executable), str(dbf_path), *names],
                                   capture_output=True, text=True, timeout=120)
        if completed.returncode:
            raise RuntimeError(f'MDX-Writer fehlgeschlagen: {completed.stderr or completed.stdout}')
    else:
        _write_mdx_odbc(dbf_path, names)
    mdx = dbf_path.with_suffix('.mdx')
    if not mdx.is_file() or mdx.stat().st_size < 1024:
        raise RuntimeError('MDX-Writer hat keine gültige externe MDX-Datei erzeugt.')
    return mdx


def pack_dbf_with_indexes(path: Path, indexed_fields: Sequence[str], *, mdx_writer=None,
                          build_mdx=True) -> PackResult:
    """PACK + echte NDX/MDX. Staging vor jeder Ersetzung, Rollback bei OS-Fehlern.

    mdx_writer: Integration eines externen echten MDX-Treiber-Backends, nimmt
    (temp_dbf_path, feldnamen) an. Das Programm validiert die Ausgabedatei.
    """
    path = Path(path).expanduser().absolute()
    if not path.is_file():
        raise FileNotFoundError(f'DBF nicht gefunden: {path}')
    if not os.access(path, os.W_OK) or not os.access(path.parent, os.W_OK) or not(path.stat().st_mode & 0o222):
        raise PermissionError(f'Keine Schreibrechte: {path}')
    source = path.read_bytes()
    fields, header_len, record_len, records, deleted = _parse_dbf(source)
    by_name = {f.name.casefold(): f for f in fields}
    index_fields = []
    for name in indexed_fields:
        field = by_name.get(str(name).casefold())
        if field is None:
            raise ValueError(f'Indexfeld fehlt in DBF: {name}')
        if field not in index_fields:
            index_fields.append(field)
    if len(index_fields) > 47 and build_mdx:
        raise ValueError('Eine MDX-Datei kann maximal 47 Index-Tags enthalten.')
    # Verwaiste/benutzerdefinierte Sidecars nicht stillschweigend ueberschreiben.
    target_ndx = [path.with_name(f'{path.stem}_{f.name}.ndx') for f in index_fields]
    target_mdx = path.with_suffix('.mdx') if build_mdx and index_fields else None
    if (source[28] or path.with_suffix('.mdx').exists()) and not target_mdx:
        raise ValueError('Bestehende MDX-Indexdatei ohne Indexdefinition: PACK verweigert.')

    for target in [path, *target_ndx, *([target_mdx] if target_mdx else [])]:
        if target.exists() and (not target.is_file() or not os.access(target, os.W_OK)):
            raise PermissionError(f'Indexdatei nicht schreibbar: {target}')

    # Kein anderes NDX des Namensschemas darf mit veralteten Record-IDs uebrigbleiben.
    expected = {p.name.casefold() for p in target_ndx}
    for other in path.parent.iterdir():
        if (other.suffix.casefold() == '.ndx' and
            other.name.casefold().startswith(path.stem.casefold() + '_') and
            other.name.casefold() not in expected):
            raise ValueError(f'Nicht zugeordnetes NDX {other.name}: Index erst zuordnen.')

    header = bytearray(source[:header_len])
    now = datetime.date.today()
    header[1:4] = bytes(((now.year - 1900) & 0xff, now.month, now.day))
    struct.pack_into('<I', header, 4, len(records))
    # Produktions-MDX-Flag erst setzen, wenn die echte MDX erzeugt wurde.
    header[28] = 0  # Das MDX-Backend darf keine fehlende Produktionsdatei sehen.
    compacted = bytes(header) + b''.join(records) + b'\x1a'

    # Keine weiteren DBF-Schreiboperationen waehrend temporaerer Indexerzeugung.
    with tempfile.TemporaryDirectory(prefix='.d64pack_', dir=path.parent) as staging:
        temp_path = Path(staging) / path.name
        temp_path.write_bytes(compacted)
        new_files = [(temp_path, path)]
        for field, dst in zip(index_fields, target_ndx):
            temp_ndx = temp_path.with_name(dst.name)
            temp_ndx.write_bytes(build_ndx_bytes(field, records))
            new_files.append((temp_ndx, dst))
        if target_mdx:
            mdx = _build_mdx(temp_path, [f.name for f in index_fields], mdx_writer)
            new_files.append((mdx, target_mdx))
            # Fremd-Writer darf Markierung nicht loeschen, Datenformat veraendern
            # oder beim Bau einen Datensatz entfernen.
            generated = temp_path.read_bytes()
            _gfields, _gh, _gr, generated_recs, _gd = _parse_dbf(generated)
            if generated_recs != records:
                raise RuntimeError('MDX-Backend hat DBF-Datensaetze veraendert.')
            if not generated[28]:
                marked = bytearray(generated)
                marked[28] = 1
                temp_path.write_bytes(marked)
        backups = []
        installed = []
        try:
            for _tmp, dst in new_files:
                if dst.exists():
                    backup = Path(staging) / (dst.name + '.backup')
                    os.replace(dst, backup)
                    backups.append((dst, backup))
            for tmp, dst in new_files:
                os.replace(tmp, dst)
                installed.append(dst)
        except OSError:
            for dst in reversed(installed):
                try: dst.unlink()
                except OSError: pass
            for dst, backup in reversed(backups):
                try: os.replace(backup, dst)
                except OSError: pass
            raise
    return PackResult(deleted, len(records), tuple(target_ndx), target_mdx)

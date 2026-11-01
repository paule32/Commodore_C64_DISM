"""Stage 524: Verlustarme DBF-PACK-Operation und projektinterner Index.

Pack ist byteorientiert: erhaelt Feld-Header, Codepage-Marker, Datenbytes
und DBT-Memoverweise, entfernt ausschliesslich Datensaetze mit '*'.
Externe NDX/MDX/CDX werden NICHT geschrieben; solche Tabellen werden zum
Schutz vor ungueltigen physischen Satznummern zurueckgewiesen.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import struct
import tempfile
import time
from typing import Sequence


class DBasePackError(ValueError):
    """Ungeeignete/beschaedigte DBF oder nicht unterstuetzte Fremdindizes."""


def _check_write_permissions(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"DBF-Datei nicht gefunden: {path}")
    if not path.parent.is_dir():
        raise NotADirectoryError(str(path.parent))
    if (not os.access(path, os.W_OK)
            or not (path.stat().st_mode & stat.S_IWUSR)
            or not os.access(path.parent, os.W_OK)
            or not (path.parent.stat().st_mode & 0o222)):
        raise PermissionError(f"Keine Schreibrechte fuer die Tabelle: {path}")


def _external_index_files(path: Path) -> list[Path]:
    # Gleichnamige NDX, CDX und MDX; auch anders benannte NDX koennen eine
    # DBF referenzieren. Sie lassen sich ohne NDX-Parser nicht sicher erkennen.
    # Daher alle NDX-Dateien des Verzeichnisses sicherheitshalber sperren.
    bad = []
    for child in path.parent.iterdir():
        if child.suffix.casefold() == '.ndx' or (
            child.suffix.casefold() in {'.mdx', '.cdx'}
            and child.stem.casefold() == path.stem.casefold()
        ):
            bad.append(child)
    return bad


def _dbf_layout(blob: bytes):
    if len(blob) < 33:
        raise DBasePackError('DBF-Header ist unvollstaendig.')
    count = struct.unpack_from('<I', blob, 4)[0]
    header_length = struct.unpack_from('<H', blob, 8)[0]
    record_length = struct.unpack_from('<H', blob, 10)[0]
    if header_length < 33 or header_length > len(blob) or blob[header_length - 1] != 0x0D:
        raise DBasePackError('Ungueltiger DBF-Feldheader (0x0D fehlt).')
    if record_length < 1 or count > (len(blob)-header_length)//record_length:
        raise DBasePackError('DBF-Datensatzanzahl/-laenge ist inkonsistent.')
    if count > 0xFFFFFFFF:
        raise DBasePackError('Zu viele Datensaetze.')
    return count, header_length, record_length


def _packed_bytes(blob: bytes):
    count, offset, length = _dbf_layout(blob)
    retained = []
    removed = 0
    for i in range(count):
        record = blob[offset+i*length:offset+(i+1)*length]
        if record[0] == ord('*'):
            removed += 1
        elif record[0] == ord(' '):
            retained.append(record)
        else:
            raise DBasePackError(f'Ungueltige DBF-Loeschmarkierung in Satz {i+1}: {record[0]:02X}')
    header = bytearray(blob[:offset])
    struct.pack_into('<I', header, 4, len(retained))
    now = time.localtime()
    header[1:4] = bytes((max(0, min(255, now.tm_year - 1900)), now.tm_mon, now.tm_mday))
    # Die dBase-EOF-Marke bleibt erhalten, ein ggf. anhaengendes Fremd-Payload
    # wird nicht stillschweigend verworfen: solche DBFs werden zurueckgewiesen.
    tail = blob[offset+count*length:]
    if tail not in (b'', b'\x1a'):
        raise DBasePackError('DBF enthaelt nicht erkannte Daten hinter den Datensaetzen.')
    return bytes(header) + b''.join(retained) + (b'\x1a' if tail else b''), removed


def _index_bytes(fields: Sequence, records: Sequence) -> bytes | None:
    """Projektinternes Indexformat; KEIN xBase-kompatibles NDX/MDX/CDX."""
    indexed = [f for f in fields if bool(getattr(f, 'indexed', False))]
    if not indexed:
        return None
    index = {}
    for f in indexed:
        name = f.name
        rows = [(str(vals.get(name, '')).strip(), number)
                for number, (deleted, vals) in enumerate(records, 1) if not deleted]
        rows.sort(key=lambda item: (item[0].casefold(), item[1]))
        index[name] = [{'key': value, 'record': number} for value, number in rows]
    result = {'format': 'dBase2Many-field-index-v1',
              'note': 'Projektintern; nicht kompatibel mit NDX/MDX/CDX',
              'record_count': len(records), 'fields': index}
    return (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def refresh_dbase_managed_index(path: Path, fields: Sequence, records: Sequence) -> None:
    """Aktualisiert einen existierenden oder definierten Projektindex nach DBF-Save."""
    path = Path(path)
    content = _index_bytes(fields, records)
    idx = path.with_suffix(path.suffix + '.d64idx.json')
    if content is None:
        if idx.exists():
            idx.unlink()  # ehemalige Indexmarkierungen entfernt
        return
    with tempfile.NamedTemporaryFile(mode='wb', prefix=idx.name+'.',
                                     suffix='.tmp', dir=str(idx.parent),
                                     delete=False) as f:
        candidate = Path(f.name)
        try:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            candidate.unlink(missing_ok=True)
            raise
    try:
        os.replace(candidate, idx)
    finally:
        candidate.unlink(missing_ok=True)


def pack_dbase_dbf(path: Path) -> dict:
    """Entfernt physisch geloeschte Saetze, regeneriert Projektindex.

    Original-DBF bleibt bei gescheiterten Vorpruefungen unveraendert.
    Bei einem Fehler nach Austausch erfolgt Rollback per Sicherheitskopie.
    """
    path = Path(path).expanduser().absolute()
    _check_write_permissions(path)
    foreign = _external_index_files(path)
    if foreign:
        raise DBasePackError(
            'Externe NDX/MDX/CDX-Indizes gefunden; ein kompatibler Index-Writer '
            'ist nicht vorhanden. PACK wurde zum Schutz der Indizes verweigert: '
            + ', '.join(p.name for p in foreign))

    old_blob = path.read_bytes()
    packed, deleted_count = _packed_bytes(old_blob)
    # Der vorhandene DBF-Reader liest die Index-Feldmarkierungen aus den
    # Projektmetadaten und die unveraenderten Werte (auch Memo-Zeiger).
    from_loader = None
    try:
        # Import erst zur Laufzeit: d64_dism.py reicht die vorhandene
        # Reader-Funktion explizit via set_dbase_pack_reader() herein.
        from_loader = _DBF_READER
    except NameError:
        pass
    if from_loader is None:
        raise RuntimeError('DBF-Reader fuer PACK nicht registriert.')
    table = from_loader(path)
    active = [(False, values) for deleted, values in table.records if not deleted]
    if len(active) != struct.unpack_from('<I', packed, 4)[0]:
        raise DBasePackError('DBF-Datensaetze konnten nicht konsistent gelesen werden.')
    index_content = _index_bytes(table.fields, active)
    idx = path.with_suffix(path.suffix + '.d64idx.json')
    if idx.exists() and (not os.access(idx, os.W_OK) or not idx.stat().st_mode & stat.S_IWUSR):
        raise PermissionError(f'Indexdatei ist schreibgeschuetzt: {idx}')
    # Physische DBF-Änderung nur bei mindestens einem '*' erforderlich.
    if not deleted_count:
        refresh_dbase_managed_index(path, table.fields, active)
        return {'deleted': 0, 'remaining': len(active), 'indexed_fields':
                sum(1 for f in table.fields if f.indexed)}

    candidates = []
    original_backup = None
    modified_idx = False
    old_index = idx.read_bytes() if idx.is_file() else None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', prefix=path.name+'.pack.',
                                         suffix='.tmp', dir=str(path.parent),
                                         delete=False) as stream:
            output_file = Path(stream.name)
            candidates.append(output_file)
            stream.write(packed)
            stream.flush()
            os.fsync(stream.fileno())
        # Vor DBF-Austausch pruefen, ob der Source zwischenzeitlich veraendert wurde.
        if path.read_bytes() != old_blob:
            raise DBasePackError('DBF wurde gleichzeitig geaendert; PACK abgebrochen.')
        with tempfile.NamedTemporaryFile(mode='wb', prefix=path.name+'.backup.',
                                         suffix='.tmp', dir=str(path.parent),
                                         delete=False) as stream:
            original_backup = Path(stream.name)
            candidates.append(original_backup)
            stream.write(old_blob)
            stream.flush()
            os.fsync(stream.fileno())
        # Index zuerst austauschen, damit ein Indexfehler keine DBF aendert.
        # Bei nachfolgendem DBF-Fehler wird der alte Index zurueckgestellt.
        if index_content is not None or idx.exists():
            if index_content is not None:
                with tempfile.NamedTemporaryFile(mode='wb', prefix=idx.name+'.pack.',
                                                 suffix='.tmp', dir=str(idx.parent),
                                                 delete=False) as stream:
                    idx_candidate = Path(stream.name)
                    candidates.append(idx_candidate)
                    stream.write(index_content)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(idx_candidate, idx)
            else:
                idx.unlink()
            modified_idx = True
        try:
            os.replace(output_file, path)
        except OSError:
            if modified_idx:
                _restore_index(idx, old_index)
            raise
    except Exception:
        raise
    finally:
        for candidate in candidates:
            candidate.unlink(missing_ok=True)
    return {'deleted': deleted_count, 'remaining': len(active), 'indexed_fields':
            sum(1 for f in table.fields if f.indexed)}


def _restore_index(path: Path, old_content: bytes | None) -> None:
    if old_content is None:
        path.unlink(missing_ok=True)
    else:
        with tempfile.NamedTemporaryFile(mode='wb', prefix=path.name+'.rollback.',
                                         suffix='.tmp', dir=str(path.parent),
                                         delete=False) as stream:
            candidate = Path(stream.name)
            stream.write(old_content)
        try:
            os.replace(candidate, path)
        finally:
            candidate.unlink(missing_ok=True)


_DBF_READER = None


def set_dbase_pack_reader(callback):
    global _DBF_READER
    _DBF_READER = callback

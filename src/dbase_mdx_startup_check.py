"""Stage 525: temporärer PACK/NDX/MDX-Selbsttest bei jedem GUI-Start.

Es werden ausschließlich Dateien in einem neu angelegten Temp-Verzeichnis
angelegt. Anwender-DBF, bestehende Indexdateien und Projekte bleiben unberührt.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import struct
import tempfile


@dataclass(frozen=True)
class MdxStartupCheck:
    executed: bool
    success: bool
    message: str


def _create_temporary_dbf(path: Path) -> None:
    """Minimale DBF-III-Tabelle mit zwei Feldern und einem Löschmarker."""
    rows = (
        (False, 'ALPHA', '10'),
        (True, 'DELETE', '20'),
        (False, 'BETA', '30'),
    )
    header = bytearray(32)
    header[0] = 0x03
    struct.pack_into('<IHH', header, 4, len(rows), 97, 16)
    name = bytearray(32)
    name[:4] = b'NAME'
    name[11] = ord('C')
    name[16] = 10
    age = bytearray(32)
    age[:3] = b'AGE'
    age[11] = ord('N')
    age[16] = 5
    with path.open('wb') as stream:
        stream.write(header + name + age + b'\x0d')
        for deleted, value, age_value in rows:
            stream.write(
                (b'*' if deleted else b' ')
                + value.encode('ascii').ljust(10, b' ')
                + age_value.encode('ascii').rjust(5, b' ')
            )
        stream.write(b'\x1a')


def check_mdx_at_startup(*, platform: str | None = None, pack_function=None) -> MdxStartupCheck:
    """Testet das echte PACK-Backend einschließlich .ndx und .mdx.

    Ein echtes ODBC/MDX-Backend wird nur unter Windows automatisch aufgerufen.
    pack_function erlaubt isolierte Tests mit einem simulierten Backend; sie
    belegen nicht die Interoperabilität der realen Windows-MDX-Datei.
    """
    if (os.name if platform is None else platform) != 'nt' and pack_function is None:
        return MdxStartupCheck(False, False, 'Übersprungen: MDX-/ODBC-Test benötigt Windows.')

    try:
        from dbase_pack_index import _parse_dbf, pack_dbf_with_indexes
        pack = pack_function if pack_function is not None else pack_dbf_with_indexes
        # Ein eigener temporärer Ordner pro Start; kein Zugriff auf Projekte.
        with tempfile.TemporaryDirectory(prefix='d64_mdx_start_') as directory:
            dbf = Path(directory) / 'mdxcheck.dbf'
            _create_temporary_dbf(dbf)
            result = pack(dbf, ['NAME', 'AGE'])
            if result.removed != 1 or result.remaining != 2:
                raise RuntimeError('PACK hat nicht genau den erwarteten Datensatz entfernt.')
            _fields, _header, _size, active, deleted = _parse_dbf(dbf.read_bytes())
            if deleted != 0 or len(active) != 2 or not dbf.read_bytes()[28]:
                raise RuntimeError('DBF-Inhalt oder MDX-Headerkennung nach PACK ungültig.')
            if active[0][1:11].strip() != b'ALPHA' or active[1][1:11].strip() != b'BETA':
                raise RuntimeError('PACK hat aktive Datensätze verändert.')
            expected_ndx = {
                dbf.with_name('mdxcheck_NAME.ndx'),
                dbf.with_name('mdxcheck_AGE.ndx'),
            }
            if set(result.ndx_files) != expected_ndx:
                raise RuntimeError('Die erwarteten externen NDX-Indizes fehlen.')
            for ndx in expected_ndx:
                if not ndx.is_file() or ndx.stat().st_size < 1024:
                    raise RuntimeError(f'NDX-Index fehlt oder ist zu klein: {ndx.name}')
            mdx = dbf.with_suffix('.mdx')
            if result.mdx_file != mdx or not mdx.is_file() or mdx.stat().st_size < 1024:
                raise RuntimeError('Externer MDX-Index wurde nicht erzeugt.')
        return MdxStartupCheck(
            True, True, 'OK: temporäre DBF gepackt (1 gelöscht, 2 erhalten); '
                        '2 NDX-Indizes und MDX-Datei erzeugt.',
        )
    except Exception as exc:
        return MdxStartupCheck(
            True, False, f'{type(exc).__name__}: {exc}',
        )

"""Fallback descriptions for a small, stable set of Win32 GetLastError codes.

The *native* compiler always uses FormatMessageA(FROM_SYSTEM, IGNORE_INSERTS)
under Windows, so the user's Windows locale supplies the full message table.
These German fallbacks are only used by the portable Python preview and tests.
They are never used to classify an SEH/NTSTATUS exception.
"""
from __future__ import annotations

WIN32_ERRORS_DE: dict[int, str] = {
    1: 'Unzulässige Funktion.',
    2: 'Das System kann die angegebene Datei nicht finden.',
    3: 'Das System kann den angegebenen Pfad nicht finden.',
    4: 'Das System kann die Datei nicht öffnen.',
    5: 'Zugriff verweigert.',
    6: 'Ungültiges Handle.',
    8: 'Nicht genügend Speicherressourcen verfügbar.',
    15: 'Das angegebene Laufwerk wurde nicht gefunden.',
    19: 'Das Medium ist schreibgeschützt.',
    32: 'Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird.',
    33: 'Der Prozess kann nicht auf die Datei zugreifen, da ein anderer Prozess einen Teil gesperrt hat.',
    80: 'Die Datei ist bereits vorhanden.',
    87: 'Der Parameter ist falsch.',
    112: 'Auf dem Datenträger ist nicht genügend Speicherplatz verfügbar.',
    123: 'Der Dateiname, Verzeichnisname oder die Datenträgerbezeichnung ist falsch.',
    183: 'Die Datei kann nicht erstellt werden, da sie bereits vorhanden ist.',
    206: 'Der Dateiname oder die Erweiterung ist zu lang.',
    267: 'Der Verzeichnisname ist ungültig.',
    995: 'Der E/A-Vorgang wurde wegen eines Threadendes oder einer Anwendungsanforderung abgebrochen.',
}


def win32_message(code: int) -> str:
    """Portable preview of a system error without touching the host's errno."""
    unsigned = int(code) & 0xFFFFFFFF
    return WIN32_ERRORS_DE.get(unsigned, f'Windows-Systemfehler {unsigned}.')

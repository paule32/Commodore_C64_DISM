# PE32 Console writable runtime section fix

## Ursache

Der interne PE32-Assembler speichert aktuell Maschinencode und Runtime-/Pascal-Daten gemeinsam in `.text`.
Der PE32-Writer kennzeichnete `.text` nur mit `IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ | IMAGE_SCN_CNT_CODE`.

Nach `AllocConsole` schreibt die Console-Runtime jedoch sofort Werte nach:

- `stdin_handle`
- `stdout_handle`
- `console_mode`
- `written`
- `read_count`
- `input_buffer`
- Pascal-Variablen

Da diese Labels ebenfalls in `.text` liegen, führte der erste Schreibzugriff zu einer Windows Access Violation.
Das sichtbare Symptom war: Console öffnet kurz, kein Text erscheint, `ReadLn` wird scheinbar übersprungen, Prozess beendet sich sofort.

## Korrektur

Solange Code und Daten noch gemeinsam in einer Sektion liegen, setzt der interne Writer zusätzlich `IMAGE_SCN_MEM_WRITE`.

Finales PE32 `.text`:

- CODE
- EXECUTE
- READ
- WRITE

Interne COFF32 `.text` erhält dasselbe Write-Recht einschließlich der bisherigen Alignment-Flags.

## Langfristig

Eine spätere saubere Trennung in `.text` (RX) und `.data` (RW) ist weiterhin sinnvoll. Für den aktuellen internen Assembler ist die gemischte RWX-Sektion jedoch erforderlich, damit die vorhandenen Runtime- und Pascal-Daten funktionieren.

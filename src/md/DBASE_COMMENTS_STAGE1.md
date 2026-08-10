# dBase-Compiler – Ausbaustufe 1: Kommentare

Der neue dBase-Compiler ist als Windows-Frontend in `d64_dism.py` integriert.
Die Backend-Ziele sind von Anfang an fest auf die vorhandene interne Windows-
Toolchain ausgerichtet:

- `pe32` – IA-32 / Windows PE32
- `pe64` – AMD64 / Windows PE32+ (intern weiterhin `pe64` genannt)

C64 und Amiga sind für dBase keine gültigen Ziele.

## Kommentarformen

Die Kommentarstufe erkennt vier Formen:

```text
// Kommentar bis zum Zeilenende
** Kommentar bis zum Zeilenende
&& Kommentar bis zum Zeilenende
/* Blockkommentar */
```

`/* ... */` darf mitten in einer Quellzeile beginnen und endet unmittelbar am
ersten folgenden `*/`. Danach wird auf derselben Zeile normal weitergelesen.
Der Blockkommentar darf beliebig viele Zeilen umfassen und ist nicht
verschachtelt.

Beispiel:

```text
? 2 /** text */ + 2 /*
text
*/ * 3 && Kommentar
** Kommentar
```

Die Kommentarbereiche werden in der Compiler-Vorstufe nicht einfach aus dem
String gelöscht, sondern durch Leerzeichen ersetzt. CR, LF und CRLF bleiben
unverändert. Dadurch bleiben Offsets, Zeilennummern und Spalten des folgenden
Quellcodes exakt identisch zum Original.

Kommentarzeichen innerhalb einfacher oder doppelter Strings starten keinen
Kommentar:

```text
? "// Text"
? '/* Text */'
```

Ein nicht abgeschlossenes `/*` erzeugt einen `DBaseCompilerError` an der
Originalposition des Kommentarstarts.

## Phase-1-Verhalten

Diese Ausbaustufe implementiert absichtlich nur die Kommentar-Lexik. Echte
dBase-Anweisungen und Ausdrücke werden noch nicht stillschweigend ignoriert,
sondern als noch nicht implementiert gemeldet. Ein leerer bzw. ausschließlich
aus Kommentaren bestehender Quelltext kann bereits zu einem echten PE32- oder
PE32+-Grundprogramm gebaut werden. Damit sind Zielauswahl, interner Assembler,
COFF-Writer und PE-Linker schon jetzt end-to-end geprüft.

## Kommandozeile

Kommentarvorstufe anzeigen:

```text
py -m d64dbase beispiel.dbase --target pe32
py -m d64dbase beispiel.dbase --target pe64
```

Kommentare mit Position auflisten:

```text
py -m d64dbase beispiel.dbase --target pe64 --list-comments
```

Ein reines Kommentarprogramm über `d64_dism` bauen:

```text
py d64_dism.py --write-pe32 comments_only.dbase
py d64_dism.py --write-pe64 comments_only.dbase
```

`--write-pe64` erzeugt ein Windows-PE32+-Image für AMD64.

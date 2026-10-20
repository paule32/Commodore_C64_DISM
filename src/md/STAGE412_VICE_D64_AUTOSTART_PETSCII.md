# Stage 412 – VICE-Autostart aus D64 ohne Host-Dateinamen-Konvertierung

Verbindliche Grundlage: `d64_dism_asm_411.zip`.

## Auslöser

Auf dem vom Benutzer übermittelten VICE-Screenshot wird nach dem Start eine BASIC-Direktzeile `LOAD"<Grafikzeichen>",8,1` angezeigt, unmittelbar gefolgt von `?FILE NOT FOUND ERROR` sowie `RUN` / `READY.`. Das weist auf den fehlgeschlagenen **VICE-Autostart des kompilierten PRG** hin; der im BASIC-Programm stehende `LOAD "sprites.spr",8,1` wurde noch gar nicht ausgeführt.

Stage 411 startete mit `-autostart <image>.d64:SPRITE_A`. VICE konvertiert diesen ASCII-Kommandonamen in PETSCII. Durch die Inkonsistenz mit den unverändert aus dem D64-Verzeichnis übernommenen PETSCII-Dateinamen erscheint eine fehlerhafte Grafikzeichenfolge.

## Korrektur

* `d64_dism.py`: Programmstart jetzt über `c64_vice_d64_autostart_options(sprite_disk)` aus `c64_d64_disk.py`.
* VICE-Kommando: `x64sc ... -8 <absolute-image>.d64 -autostart <absolute-image>.d64`. **Kein** `:SPRITE_A`-Suffix mehr.
* Der D64-Schreiber legt das ausführbare PRG schon seit Stage 409 in den ersten Verzeichniseintrag, gefolgt von `SPRITES.SPR`. Der dokumentierte VICE-Autostart ohne Suffix startet diese erste PRG-Datei.
* Generierte PRG-Aliasnamen werden im Dateisystem-Diskettenimage PETSCII-freundlich kodiert: Windows-Underscore `_` wird in `-` umgewandelt, denn PETSCII `$5F` steht für den Linkspfeil.
* Der Debug/BASIC-Direkttransfer bleibt unverändert: hier wird das D64 über `-8` eingehängt und BASIC-Zeilen werden separat an den Binary Monitor übergeben.
* Die Sprite-Datei und der `SETNAM`-Zeiger aus Stages 410/411 werden nicht verändert.

## Kontrolle

Neu erzeugtes D64: `Sprite_A_412.d64` mit PRG `SPRITE-A` an erster Stelle und `SPRITES.SPR` an zweiter Stelle. Die Dateiinhalte sind bytegenau mit dem Stage-411-PRG und der vorbereiteten Sprite-Datei identisch.

In VICE manuell: neues Image auf Laufwerk 8 einlegen; `LOAD "*",8,1` gefolgt von `RUN` sollte die erste PRG-Datei laden. Dabei sollte keine Grafikzeichenfolge als Dateiname auftauchen. VICE-Direktausführung unter Windows konnte in dieser Umgebung nicht getestet werden.

## Technischer Hinweis

Die Änderung zielt genau auf die Grafikzeichen im **Autostart-LOAD**, nicht auf eine erneute, unbewiesene Fehlersuche beim `LOAD "sprites.spr"` im kompilierten Programm.

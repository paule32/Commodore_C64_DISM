# Stage 108c - WFM Speichern/Speichern unter

Beim Speichern einer geöffneten WFM-Datei stürzte `_serialize_dbase_form_wfm()`
mit `UnboundLocalError: lines` ab.

Ursache: Innerhalb der verschachtelten Funktion `emit_item()` wurden drei
`lines += [...]`-Anweisungen verwendet. Augmented Assignment macht `lines` in
Python zu einer lokalen Variable von `emit_item()`. Der vorherige Aufruf
`lines.append(...)` griff deshalb auf eine noch nicht initialisierte lokale
Variable zu.

Korrektur: Die drei Anweisungen verwenden jetzt `lines.extend([...])`. Dadurch
bleibt `lines` eine Closure-Variable der äußeren Serializer-Funktion.

Getestet wurde ein Save/Parse-Roundtrip mit einem Root-PushButton, einem
Container und einem darin enthaltenen PushButton.

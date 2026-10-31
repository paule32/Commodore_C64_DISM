# Stage 509 – Ressourcen-TreeList: Kontextmenü und Menu-Vorlage

**Verbindliche Basis:** `d64_dism_asm_508.zip`.

## Kontextmenü im linken Ressourcenbaum

Per Rechtsklick auf eine Ressource oder eine freie Stelle des linken `resource_tree` wird das Kontextmenü geöffnet:

1. `Neu:  Dialog`
2. `Neu:  Menü`
3. `Neu:  Text`
4. `Neu:  Icon`
5. `Neu:  Bitmap`
6. `Neu:  Cursor`
7. `Neu:  RCDATA`
8. Trennlinie
9. `Alles auswählen`
10. `Kopieren`
11. `Einfügen`
12. `Löschen`

Die vier Textoperationen beziehen sich auf den Text im **RC-Quelltexteditor**: Alles auswählen (`selectAll`), selektierten Text kopieren (`copy`), Clipboard-Text einfügen (`paste`) und selektierten Text entfernen (`QTextCursor.removeSelectedText`). Das Kontextmenü im Editor selbst bleibt bestehen.

Die **Neu**-Aktionen fügen die jeweilige RC-Quelltextdeklaration am Ende des Quelltexts ein, damit eine existierende Ressource nicht durch eine aktuelle Markierung überschrieben wird. Jede Vorlage ist eindeutig benannt. Ein binäres `.res`-Dokument ist weiterhin schreibgeschützt; dort sind Änderungen im Kontextmenü deaktiviert.

### Live-Ressourcenliste

Nach dem Erstellen wird sofort (ohne zusätzliches Klicken auf "Aktualisieren") die vorhandene RC-Vorschaukompilierung gestartet. Die kompilierten Einträge erscheinen mit Typ/ID/Sprache/Größe in der TreeList. Bei unvollständigen Vorlagen – besonders bei `Icon`, `Bitmap` und `Cursor`, wenn die referenzierte Bilddatei noch nicht vorliegt – bleiben die letzten gültigen Binärdaten erhalten und die erzeugten Quelltextdeklarationen erscheinen in der Gruppe `RC-Vorlagen (nicht kompiliert)`.

**Wichtig:** Diese Markierungen sind ausdrücklich **kein** kompiliertes Binärformat und werden nicht als gefälschte `ResourceEntry` in RES/COFF ausgegeben. Für vollständige Ressourcen müssen die Dateien am referenzierten Pfad liegen oder die RC-Dateipfade entsprechend angepasst werden. Bei Auswahl eines unkompilierten Elements wird im Hex-Tab statt alter Ressourcendaten eine Erklärung eingeblendet.

## Zusätzlicher Button `Menu`

In der unteren Vorlagen-Toolbar steht `Menu` direkt rechts neben `Dialog` und vor `Text`. Die Vorlage wird durch `resource_rc_templates.rc_template("Menu")` erzeugt:

```rc
IDM_MENU_1 MENU
BEGIN
    POPUP "Datei"
    BEGIN
        MENUITEM "Öffnen", 3011
        MENUITEM SEPARATOR
        MENUITEM "Beenden", 3012
    END
    POPUP "Hilfe"
    BEGIN
        MENUITEM "Über ...", 3013
    END
END
```

Bei wiederholter Einfügung wird `IDM_MENU_2` mit anderen numerischen Menü-IDs verwendet. Die Vorlage wird vom vorhandenen internen Microsoft-RC-Compiler zu einer echten RT_MENU-Ressource kompiliert.

## Geänderte/ergänzte Dateien

- `d64_dism.py`: Tree-Kontextmenü, Menüaktionen, Vorschau-/TreeList-Aktualisierung, read-only-Schutz und klar gekennzeichnete nicht kompilierte Vorlagen
- `resource_rc_templates.py`: `Menu`-Vorlage und Erkennung erzeugter RC-Deklarationen als Source-Outline
- `test_stage509_resource_tree_context_menu.py`: neue Regressionstests

## Testergebnisse

- `python -m py_compile d64_dism.py resource_rc_templates.py test_stage509_resource_tree_context_menu.py`: erfolgreich
- `python -m pytest -q test_stage509_resource_tree_context_menu.py`: **13 bestanden**
- Gezielter gemeinsamer Testlauf mit Stage-457-, Stage-501–508-Tests: **122 bestanden**
- Gesamtumfang aller 123 Testmodule: Ein Komplettlauf wurde gestartet, überschritt jedoch das Testzeitlimit. Er wird **nicht** als erfolgreicher Gesamt-Testlauf ausgewiesen.
- Native Windows-PyQt5-Darstellung wurde hier nicht getestet (PyQt5 ist in der Testumgebung nicht installiert).

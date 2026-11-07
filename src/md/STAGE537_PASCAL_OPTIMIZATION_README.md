# Stage 537 – Pascal-Codeoptimierung und Systeminformationen

**Basis:** `d64_dism_stage536.zip` (vollständiger Projektstand).
**Ziel:** Bestehenden PE32-/PE32+-Pascal-Compiler optimierbar machen, ohne O0-Builds unnötig zu verändern.

## GUI und Projektdatei

In den **Projekt-Einstellungen** existiert nun für beide Windows-Ziele der TreeList-Pfad
`Compiler > Pascal > Optimierung`. Die Ansicht zeigt die GroupBox `Optimierung-Stufen: ` mit
vier exklusiven RadioButtons:

- `O0  -  Bisheriger Code, keine Optimierung`
- `O1  -  Redundante MOV/PUSH/POP, Konstantenfaltung, unerreichbarer Code`
- `O2  -  Direkte bedingte Sprünge, Registeroptimierung, unnötige Initialisierungen entfernen`
- `O3  -  Zusätzlich selektives Inlining und erweiterte Kontrollfluss-/Datenflussanalyse`

Die Auswahl wird unabhängig gespeichert:

```ini
[Settings.Windows.32Bit.Compiler.Pascal.Optimierung]
Level = O0

[Settings.Windows.64Bit.Compiler.Pascal.Optimierung]
Level = O0
```

Fehlende/ältere Einstellungen erhalten O0. Die Auswahl geht sowohl an die normale
Pascal-Codeerzeugung als auch an die Stage-536-Worker für parallele UNIT-Builds.

## Codegenerator und Optimierungsumfang

- **Unabhängig von der Stufe:** PE32-Funktionsprologe sichern EBX, ESI und EDI einschließlich aller
  normalen Rücksprünge und `Exit`; damit bleibt die Windows-Callback-Aufrufkonvention erhalten.
  Konsoleninitialisierung verwendet den tatsächlichen `STD_OUTPUT_HANDLE` für
  `SetConsoleWindowInfo`; eine notwendige Konsolen-Restaurierung liegt vor einem expliziten
  `ExitProcess`-Aufruf. `WM_NCDESTROY` gibt die `TForm`-Instanz nicht zusätzlich frei;
  `TApplication.Destroy` bleibt ihr Eigentümer. Die korrigierte VCL-UNIT muss im Projekt
  neu kompiliert werden.
- **O0:** keine Peephole-Optimierung oder Konstantenfaltung. ABI- und Laufzeitkorrekturen gelten
  trotzdem. Bestehende statische Routine-/Methodenparameter bleiben hier zur Kompatibilität.
- **O1:** schmale, kontrollierte Peephole-Muster für redundante PUSH/MOV/POP-Sequenzen,
  `MOV reg,reg`, direkt unerreichbare JMP hinter RET; Faltung sicher berechenbarer
  32-Bit-Literalausdrücke. Der Quellzeilen-Bezug wird beim Entfernen angepasst.
- **O2:** direkte bedingte Sprünge aus integer-/pointerartigen Vergleichen, Reduktion einzelner
  redundanter Registerbewegungen, Weglassen von Nullinitialisierungen, wenn unmittelbar eine
  literale Initialisierung folgt. Routine-**Lokale** und **Result**-Variablen erhalten
  pro Aufruf EBP-/RBP-relative Stack-Slots. Bei globalen CDECL-/STDCALL-PE32-Routinen
  werden Stackparameter direkt über `[EBP+...]` angesprochen; bei globalen PE64-Routinen
  verwendet der Compiler die Windows-x64-Home-Slots (`[RBP+16]` usw.). Dadurch entfallen
  deren statische Parameter-Zwischenspeicher.
- **O3:** konservative, lokale Kontrollflussoptimierung: Verkettete Sprünge reduzieren,
  Sprung zum unmittelbar nächsten Label entfernen, zur Compile-Zeit sichere konstante
  IF-Zweige auswählen und triviale leere, nichtvirtuelle, parameterlose Prozeduren inline
  auslassen. Keine aggressive globale Alias- oder SSA-Optimierung.

**Sicherheitsgrenze:** Ein Peephole-Durchlauf verändert keine Cookie-Checks,
Runtime-Imports, Speicherzugriffe über unbewiesene Aliase oder externen Aufrufkonventionen.

## Nicht vollständig umgesetzt / bekannte Grenzen

- **Keine allgemeine SSA-/Register-Allokation oder Alias-Analyse.** O3 enthält vorsichtige
  Kontrollfluss- und Konstantenoptimierungen, keine vollständige interprozedurale Datenflussanalyse.
- Methodenparameter, temporäre Aufruf-/Konstruktor-Slots und einige Windows-/Runtime-Puffer
  werden zum Teil weiterhin statisch gespeichert. Die Umstellung auf vollständig reentrant
  aufrufbare Klassenmethoden benötigt zusätzliche ABI- und Lebensdauerarbeit.
- Rekursive/gleichzeitige Programme mit dynamischen Strings/Exceptions müssen unter realem
  Windows mit aktivierten Optimierungsstufen separat auf Speicher- und Besitzkorrektheit
  geprüft werden. Stack-Cookie, Exception-Runtime und Parallel-Compiler sind keine
  vollständige Laufzeitverifikation.
- Native PE32-/PE32+-EXE-, DLL-, GUI- und WindowProc-Laufzeittests waren in dieser
  Linux-basierten Umgebung nicht möglich. Für einen echten Pascal-Frontend-End-to-End-Test
  wird die zum generierten Parser passende ANTLR-4.13.2-Runtime benötigt; hier lag 4.9.3 vor.
- Das Ausgangsprojekt besitzt Python-3.15-`lazy from`-Imports; dieser bestehende Syntaxstand
  wurde unverändert übernommen und verhindert ein direktes Importieren des gesamten
  `d64_dism.py` unter älteren Python-Versionen.

## System-Informationen: Windows-Titelleiste

Der vorhandene Dialog `Hilfe > System-Informationen` übernimmt beim Anzeigen die aktive
Dark-/Light-Auswahl über `DwmSetWindowAttribute` mit DWMWA_USE_IMMERSIVE_DARK_MODE (Attribut
20, Fallback 19). Auf anderen Systemen oder älteren Builds erfolgt ein sicherer No-Op.

## Prüfungen

```bash
python -m unittest test_stage537 test_stage531 test_stage532 test_stage533 test_stage534 test_stage535 test_stage536 -q
```

28 Tests bestanden in der Entwicklungsumgebung; sie prüfen insbesondere O0/O1/O2/O3,
PE32/PE64-Codegenerierung mit Cookie, Stack-Slots, `.pro`-Trennung, Worker-/GUI-Anbindung,
VCL-Besitzregel und bestehende Regressionen. **Kein nativer Windows-Laufzeittest.**

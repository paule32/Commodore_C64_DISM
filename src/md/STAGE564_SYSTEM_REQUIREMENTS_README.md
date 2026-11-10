# Stage 564 – Installer-Systemanforderungen

Basis: d64_dism_stage563.zip (verbindliche Vorlage).

- Der Button unter Einstellungen heißt jetzt `Systemanforderungen` statt `Benötigte Resourcen`.
- 620 × 550 Pixel Dialog, gradientenbasierte Titelleiste schwarz → weiß im Dark Mode.
- Links TreeWidget für die bekannten Windows-Desktop- und Windows-Server-Versionen des Wizards; anklickbare Checkboxen für jeden Knoten und jedes Blatt mit tri-state-Elternanzeige.
- Rechts GroupBoxen `System-Prüfungen` und `Benutzer benachrichtigen` mit jeweils einer Hälfte der Spaltenhöhe.
- Mindestwerte: RAM (MB), Bildschirmweite/-höhe (Pixel), Farbtiefe (BPP); 0 deaktiviert die jeweilige Mindestanforderung.
- Administratorrechte und zwei gegenseitig ausschließende Benachrichtigungs-Checkboxen.
- OK serialisiert in `InstallerProject.sections["Systemanforderungen"]`, speichert wie der bestehende Hintergrund-Dialog; Abbrechen verwirft Änderungen vor dem OK. Hilfe ruft den vorhandenen CHM-Viewer mit Thema `Systemanforderungen` auf.
- Der Projektname-belegt-Warnhinweis erhält den Dark-Mode-Stil und die native dunkle Windows-Titelleiste.
- Neue CHM-Quell-Hilfeseite und Verlinkung in HHC/HHK/HHP und Index. Die kompilierte CHM muss bei Verwendung einer solchen separat neu erstellt werden.
- Die tatsächliche Prüfung der Werte in einem generierten Setup ist **nicht** Teil dieser Stage; sie werden für spätere Setup-Generierung gespeichert.
- Statische und Model-Regressionstests: 49 erfolgreich (`test_stage559` bis `test_stage564`). Native GUI-Laufzeitprüfung nicht möglich, PyQt5 in dieser Umgebung nicht installiert.

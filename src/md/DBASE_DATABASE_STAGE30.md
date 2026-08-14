# dBase DATABASE Stage 30

Stage 30 fuehrt die eingebaute Klasse `DATABASE` ein und baut auf SESSION/Login und dem zentralen Shutdown aus Stage 29 auf.

## Syntax

```dbase
local db as Database
db = new Database()
```

`local db as Database` deklariert `db` als Objektalias fuer die eingebaute DATABASE-Klasse. `new Database()` erzeugt die native Runtime-Instanz. Ein nicht qualifiziertes DATABASE-Objekt hat `_app` als Parent.

## Eigenschaften

```dbase
db.path = "C:\\Daten"
db.databaseName = "Kunden"
db.userName = "user"
db.password = "pass"
db.alias = "MY_DSN"
db.session = _app.security
db.active = true
```

- `path`: Wurzelverzeichnis fuer lokale DBF/MDX/NDX/DBT-Dateien.
- `databaseName`: logischer Datenbankname; wenn bei lokaler Verwendung ein gleichnamiges Unterverzeichnis existiert, wird dieses als Tabellenwurzel verwendet.
- `userName`, `password`: SQL-/ODBC-Anmeldedaten.
- `alias`: Alias/DSN-Eigenschaft. Stage 30 verbindet native ODBC-DSNs. Die Eigenschaft bleibt bewusst transportneutral, damit ein nativer BDE-Adapter spaeter ohne Syntaxaenderung angeschlossen werden kann.
- `session`: Referenz auf ein zuvor erzeugtes SESSION-Objekt.
- `active = true`: entspricht `open()`.
- `active = false`: entspricht `close()`.

String-Eigenschaften akzeptieren wie die bisherige Ausdrucksschicht Stringliterale, Makros, Variablen und FUNCTION-Rueckgaben.

## Methoden

```dbase
db.open()
db.commit()
db.close()
```

`open()` prueft zuerst, ob `session` gesetzt ist und diese SESSION erfolgreich authentifiziert wurde. Ohne Alias wird der lokale Verzeichnis-Kontext geoeffnet. Mit Alias wird unter Windows eine ODBC-Verbindung ohne Benutzerprompt aufgebaut. ODBC-Autocommit wird ausgeschaltet, damit `commit()` die Transaktion explizit dauerhaft bestaetigt.

`close()` schliesst zuerst alle an die DATABASE gebundenen Tabellen (Stage-30-Hook, TABLE folgt spaeter), rollt eine noch nicht bestaetigte ODBC-Transaktion zurueck, trennt die Verbindung und setzt `active = false`.

`commit()` bestaetigt eine ODBC-Transaktion. Fuer lokale DBF-Daten ist der Hook fuer das spaetere gemeinsame Flushen der TABLE-Schicht vorbereitet.

## Sicherheitsbindung

Eine DATABASE kann nur geoeffnet werden, wenn ihre `session` existiert und authentifiziert ist. Wird der Loginstatus dieser Session ungueltig, wird eine aktive DATABASE geschlossen.

## Warnbox

Scheitert `open()` oder `commit()`, wird kein Standard-QMessageBox verwendet. Stage 30 besitzt einen eigenen rastergebundenen Warndialog:

- Titel `Warnung`
- modal
- 52 x 8 Zeichenzellen innerhalb des 80 x 25 Konsolenrasters
- roter Hintergrund
- weisser CP437/Terminal-Rahmen
- schwarzer Warntext
- `OK`-Button
- Consolas, Fallback Courier New / Fixed Font
- wird beim globalen Shutdown automatisch beendet

## Cleanup

Der zentrale `DBaseQtShutdown()` ruft vor dem Abbau von SESSION und GUI `close_runtime_data_files()` auf. Dieser schliesst alle DATABASE-Objekte. Danach werden Passwoerter vor dem Freigeben der DATABASE-Objekte ueberschrieben.

## Neue C-ABI

- `DBaseQtDatabaseCreate`
- `DBaseQtDatabaseSetPath`
- `DBaseQtDatabaseSetDatabaseName`
- `DBaseQtDatabaseSetUserName`
- `DBaseQtDatabaseSetPassword`
- `DBaseQtDatabaseSetAlias`
- `DBaseQtDatabaseSetSession`
- `DBaseQtDatabaseSetActive`
- `DBaseQtDatabaseOpen`
- `DBaseQtDatabaseClose`
- `DBaseQtDatabaseCommit`

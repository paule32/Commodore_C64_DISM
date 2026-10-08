D64 ODBC helper - Stage ASM 18 (new branch based on ASM 17)
==============================================================

Python dependency:
    py -m pip install pyodbc

List installed Windows ODBC drivers:
    print(odbc_available_drivers())

One-shot query, result as list:

    rows = execute_odbc_sql(
        "DSN=MeineDB;UID=user;PWD=secret",
        "SELECT ID, NAME FROM CUSTOMER WHERE ID > ?",
        [10],
        result_type="list",
        include_columns=True,
    )

Result example:
    [
        ["ID", "NAME"],
        [11, "Meyer"],
        [12, "Schmidt"],
    ]

One-shot query, result as string:

    text = execute_odbc_sql(
        "DSN=MeineDB;UID=user;PWD=secret",
        "SELECT ID, NAME FROM CUSTOMER",
        result_type="string",
        include_columns=True,
    )

Result example:
    ID<TAB>NAME
    11<TAB>Meyer
    12<TAB>Schmidt

Persistent connection:

    with D64ODBCConnection(
        "DSN=MeineDB;UID=user;PWD=secret"
    ) as db:
        rows1 = db.execute("SELECT * FROM CUSTOMER")
        rows2 = db.execute("SELECT * FROM ORDERS")

SQL Server connection-string example:

    DRIVER={ODBC Driver 18 for SQL Server};
    SERVER=localhost;
    DATABASE=TestDB;
    UID=user;
    PWD=secret;
    TrustServerCertificate=yes;

Microsoft Access example:

    DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};
    DBQ=T:\\Data\\Database.accdb;

For INSERT/UPDATE/DELETE/DDL:
    - successful commands are committed when autocommit=False
    - list mode returns [[rowcount]]
    - string mode returns the rowcount as text

Parameterized SQL should use ? placeholders. Do not concatenate user input into SQL.

Stage ASM 19 - SQL Builder GUI integration
==========================================

The SQL Builder now lists the installed ODBC drivers below the SQL editor.
The ODBC... button opens a login dialog with:
    Benutzer-Name
    Passwort
    Verbinden
    Testen
    Abbrechen

For DBF/dBase drivers the current SQL-Builder directory is added as DBQ.
Credentials are never written to the .d64sql project. Only the selected
ODBC driver name is persisted.

The View tab contains a record navigator:
    Anfang | Zurück | Vorwärts | Ende | Aktualisieren

Aktualisieren executes the current SELECT/WITH statement through the active
ODBC connection and displays the returned rows in the query grid. The four
navigation buttons select and scroll to the current result row.

Stage ASM 20 - ODBC data sources (DSN) instead of drivers
==========================================================

The SQL Builder ComboBox now lists configured ODBC data sources (DSNs),
not merely installed drivers. Each entry is shown as:

    DSN name  —  driver name

Sources are collected from pyodbc.dataSources() and, on Windows, supplemented
from User/System DSNs in both 32-bit and 64-bit ODBC registry views. This is
useful when a legacy 32-bit dBASE DSN exists on a 64-bit development machine.

Connections are now created with:

    DSN={MyDataSource};UID={user};PWD={password};

The .d64sql project stores the selected DSN and its driver name. Stage-19
projects containing only an odbc_driver value remain loadable; the first DSN
using that driver is selected when possible.

# dBase Stage 21 – SESSION / Windows Login

Stage 21 fuehrt die eingebaute Klasse `SESSION` als ersten Baustein fuer den
spaeteren DBF/MDX/NDX/DBT-Datenzugriff ein.

## Syntax

```dbase
foo = new Session()
result = foo.Login("user", "pass", "Users")
```

Auch als `_app`-Property:

```dbase
_app.security = new Session()
result = _app.security.Login("DOMAIN\\user", "pass", "DOMAIN\\Group")
```

Der Rueckgabewert ist numerisch `1` fuer erfolgreich authentifiziert und in der
angegebenen Windows-Gruppe, sonst `0`.

## Parent-Regel

- `foo = new Session()` -> Parent ist `_app`.
- `_app.foo = new Session()` -> Parent ist `_app`.
- `form1.foo = new Session()` -> Parentpfad ist `form1`.

`FORM` selbst ist in dieser Stufe noch nicht implementiert; die Parent-Ableitung
ist aber bereits so angelegt, dass ein spaeteres natives FORM-Handle direkt an
`DBaseQtSessionCreate(parent)` uebergeben werden kann.

## Windows-Authentifizierung

Die Runtime verwendet `LogonUserW` mit `LOGON32_LOGON_NETWORK`. Der zurueck-
gelieferte Impersonation-Token wird mit `CheckTokenMembership` gegen die per
`LookupAccountNameW` aufgeloeste Gruppen-SID geprueft.

Unterstuetzte Benutzernamen:

- `user` -> lokale Kontodatenbank (`.`)
- `DOMAIN\\user` -> explizite Windows-Domain
- `user@domain.example` -> UPN, Domainparameter fuer LogonUserW ist NULL

Die Session speichert kein Passwort. Die temporaere breite Passwortkopie wird
mit `SecureZeroMemory` geloescht; das Token wird in allen Pfaden geschlossen.

Hinweis: Ein als Stringliteral im dBase-Quelltext hinterlegtes Passwort liegt
naturgemaess im erzeugten Programmimage. Fuer produktive Logins sollte das
Passwort spaeter ueber eine Eingabekomponente oder einen sicheren Credential-
Provider bereitgestellt werden.

## Native C-ABI

```cpp
void *DBaseQtSessionCreate(void *parent);

int DBaseQtSessionLogin(
    void *handle,
    const char *username, int usernameLength,
    const char *password, int passwordLength,
    const char *group, int groupLength
);
```

PE32 verwendet cdecl. PE32+ verwendet die Windows-x64-ABI; wegen der sieben
Argumente werden neben RCX/RDX/R8/R9 drei weitere Argumente im Stackbereich
hinter dem Shadow Space uebergeben.

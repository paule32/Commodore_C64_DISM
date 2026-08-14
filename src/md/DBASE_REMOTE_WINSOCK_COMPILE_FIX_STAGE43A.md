# Stage 43A – Winsock/Qt connect compile fix

Stage 43A ist eine reine Build-Korrektur auf Basis von Stage 43.

## Ursache

`ServerDialog` erbt indirekt von `QObject`. Der unqualifizierte Aufruf

```cpp
connect(socketValue, ...)
```

wurde deshalb bei der C++-Namenssuche als Kandidat fuer `QObject::connect()`
behandelt. MinGW meldete daraufhin, dass keine der Qt-Overloads zu
`SOCKET, sockaddr *, unsigned int` passt.

## Korrektur

Der Winsock-Aufruf wird explizit im globalen Namespace aufgerufen:

```cpp
const int result = ::connect(
    socketValue,
    reinterpret_cast<const sockaddr *>(&address),
    static_cast<int>(sizeof(address))
);
```

Zur Vermeidung weiterer Qt/Win32-Namenskollisionen sind die nativen
Winsock-Aufrufe des Stage-43-Remote-Moduls ebenfalls explizit mit `::`
qualifiziert (`::socket`, `::bind`, `::listen`, `::accept`, `::send`,
`::recv`, `::shutdown`, `::closesocket` usw.). Qt-Signalverbindungen bleiben
unveraendert `QObject::connect(...)`.

## Build

```text
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

Das qmake-Projekt bindet weiterhin `-lws2_32` ein.

Der alte, derzeit unbenutzte `show_btx_dialog()`-Helper kann weiterhin eine
`-Wunused-function`-Warnung erzeugen. Diese Warnung ist kein Buildfehler und
wurde in Stage 43A bewusst nicht funktional veraendert.

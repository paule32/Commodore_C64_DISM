#define _UNICODE
#define UNICODE
#include <windows.h>

static const wchar_t *kMutexName = L"Global\\d64_dism.start.launcher.v1";

int WINAPI wWinMain(HINSTANCE, HINSTANCE, LPWSTR, int) {
    HANDLE mutex = CreateMutexW(nullptr, FALSE, kMutexName);
    if (!mutex) {
        MessageBoxW(nullptr, L"Globaler Launcher-Mutex konnte nicht erzeugt werden.",
                    L"start.exe", MB_OK | MB_ICONERROR | MB_TOPMOST);
        return 10;
    }

    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        MessageBoxW(nullptr, L"start.exe läuft bereits.",
                    L"start.exe", MB_OK | MB_ICONINFORMATION | MB_TOPMOST);
        CloseHandle(mutex);
        return 11;
    }

    // Hier d64_dism.exe per CreateProcessW starten und auf den Prozess warten.
    // Der Mutex muss bis zum Ende des Launchers offen bleiben.

    MessageBoxW(nullptr, L"Mutex erfolgreich belegt.",
                L"start.exe", MB_OK | MB_ICONINFORMATION);

    CloseHandle(mutex);
    return 0;
}

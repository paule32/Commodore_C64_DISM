#include "d64_workstation.h"

#ifdef _WIN32
#include <windows.h>

static const wchar_t kWindowClass[] = L"D64WorkstationSmokeTest";

static LRESULT CALLBACK WindowProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    switch (msg) {
    case WM_CLOSE:
        D64WorkstationBeginLeave();
        DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(hwnd, msg, wp, lp);
    }
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show)
{
    /*
     * Prepare bindet diesen GUI-Thread an den neuen Desktop, schaltet ihn aber
     * noch nicht sichtbar. Deshalb bleibt Windows bei jedem Fehler erreichbar.
     */
    if (!D64WorkstationPrepare()) {
        MessageBoxW(
            nullptr,
            L"Der Test-Desktop konnte nicht vorbereitet werden.",
            L"D64 Workstation Test",
            MB_OK | MB_ICONERROR
        );
        return 1;
    }

    WNDCLASSW wc{};
    wc.lpfnWndProc = WindowProc;
    wc.hInstance = instance;
    wc.lpszClassName = kWindowClass;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);

    if (!RegisterClassW(&wc)) {
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 2;
    }

    HWND hwnd = CreateWindowExW(
        0,
        kWindowClass,
        L"D64 Workstation Smoke Test - EXIT doppelklicken oder Alt+F4",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        800, 500,
        nullptr,
        nullptr,
        instance,
        nullptr
    );

    if (!hwnd) {
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 3;
    }

    /* Fenster zuerst auf dem unsichtbaren Workstation-Desktop bereitstellen. */
    ShowWindow(hwnd, show);
    UpdateWindow(hwnd);

    /* Erst mit einem sichtbaren HWND wird die Workstation aktiviert. */
    if (!D64WorkstationActivate(hwnd)) {
        DestroyWindow(hwnd);
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 4;
    }

    // Stage 36: Die Workstation darf nur aktiv sein, wenn das EXIT-Icon
    // oben links tatsaechlich als eigenes Win32-Fenster sichtbar ist.
    if (!D64WorkstationExitIconVisible()) {
        PostMessageW(hwnd, WM_CLOSE, 0, 0);
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 5;
    }

    D64WorkstationInstallKeyboardGuard(hwnd);

    MSG msg{};
    while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    D64WorkstationBeginLeave();
    D64WorkstationFinalizeLeave();
    return static_cast<int>(msg.wParam);
}

#else
int main() { return 0; }
#endif

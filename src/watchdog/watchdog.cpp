// Commodore_C64_DISM native crash watchdog, adapted from PythonBDE's design.
// Independent Win32 process. Does not import/load Qt or Python.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0601
#endif
#include <windows.h>
#include <shellapi.h>
#include <algorithm>
#include <cwchar>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <initializer_list>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {
constexpr int ID_TRACE = 1001, ID_COPY = 1002, ID_CLOSE = 1003;
constexpr DWORD MAX_LOG_BYTES = 48 * 1024;

struct Options {
    DWORD pid = 0;
    std::wstring role = L"Commodore C64 DISM";
    std::wstring fatalLog, errorLog, readyEvent;
};
struct DialogState {
    std::wstring title, details;
    HWND editor = nullptr, copy = nullptr, close = nullptr;
};

std::wstring to_wide(const char* data, int length) {
    if (!data || length <= 0) return L"";
    int count = MultiByteToWideChar(CP_UTF8, 0, data, length, nullptr, 0);
    if (count <= 0) return L"";
    std::wstring text(static_cast<size_t>(count), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, data, length, &text[0], count);
    return text;
}

std::wstring windows_lines(const std::wstring& text) {
    std::wstring value;
    value.reserve(text.size() + text.size()/10);
    for (size_t i = 0; i < text.size(); ++i) {
        if (text[i] == L'\n' && (i == 0 || text[i - 1] != L'\r')) value += L'\r';
        value += text[i];
    }
    return value;
}

std::wstring read_tail(const std::wstring& path) {
    if (path.empty()) return L"";
    HANDLE handle = CreateFileW(path.c_str(), GENERIC_READ,
                                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (handle == INVALID_HANDLE_VALUE) return L"";
    LARGE_INTEGER length{};
    if (!GetFileSizeEx(handle, &length) || length.QuadPart < 1) {
        CloseHandle(handle);
        return L"";
    }
    DWORD size = static_cast<DWORD>(std::min<LONGLONG>(length.QuadPart, MAX_LOG_BYTES));
    LARGE_INTEGER pos{};
    pos.QuadPart = length.QuadPart - size;
    if (!SetFilePointerEx(handle, pos, nullptr, FILE_BEGIN)) {
        CloseHandle(handle);
        return L"";
    }
    std::vector<char> bytes(size);
    DWORD got = 0;
    BOOL success = ReadFile(handle, bytes.data(), size, &got, nullptr);
    CloseHandle(handle);
    return success ? windows_lines(to_wide(bytes.data(), static_cast<int>(got))) : L"";
}

std::wstring hex_code(DWORD code) {
    std::wostringstream stream;
    stream << L"0x" << std::uppercase << std::hex << std::setfill(L'0') << std::setw(8) << code;
    return stream.str();
}

bool parse_args(Options& opt) {
    int argc = 0;
    LPWSTR* args = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!args) return false;
    bool valid = argc >= 3 && argc % 2 == 1;
    for (int i = 1; valid && i+1 < argc; i += 2) {
        std::wstring key = args[i];
        std::wstring value = args[i+1];
        if (key == L"--pid") {
            wchar_t* end = nullptr;
            unsigned long number = wcstoul(value.c_str(), &end, 10);
            if (!end || *end || !number) valid = false;
            else opt.pid = static_cast<DWORD>(number);
        } else if (key == L"--role") opt.role = value;
        else if (key == L"--fatal-log") opt.fatalLog = value;
        else if (key == L"--error-log") opt.errorLog = value;
        else if (key == L"--ready-event") opt.readyEvent = value;
        else valid = false;
    }
    LocalFree(args);
    return valid && opt.pid;
}

void notify_ready(const std::wstring& event_name) {
    if (event_name.empty()) return;
    HANDLE event = OpenEventW(EVENT_MODIFY_STATE, FALSE, event_name.c_str());
    if (event) {
        SetEvent(event);
        CloseHandle(event);
    }
}

void clipboard_copy(HWND hwnd, const std::wstring& text) {
    if (!OpenClipboard(hwnd)) return;
    if (EmptyClipboard()) {
        SIZE_T size = (text.size() + 1) * sizeof(wchar_t);
        HGLOBAL global = GlobalAlloc(GMEM_MOVEABLE, size);
        if (global) {
            void* memory = GlobalLock(global);
            if (memory) {
                memcpy(memory, text.c_str(), size);
                GlobalUnlock(global);
                if (SetClipboardData(CF_UNICODETEXT, global)) global = nullptr;
            }
            if (global) GlobalFree(global);
        }
    }
    CloseClipboard();
}

void layout(HWND window, DialogState* state) {
    if (!state) return;
    RECT client{};
    GetClientRect(window, &client);
    // Explicit casts: RECT::right/left are LONG, std::max uses int.
    const int w = std::max(100, static_cast<int>(client.right-client.left));
    const int h = std::max(100, static_cast<int>(client.bottom-client.top));
    if (state->editor) MoveWindow(state->editor, 12, 12, w-24, std::max(30, h-68), TRUE);
    if (state->copy) MoveWindow(state->copy, std::max(12, w-266), h-44, 140, 30, TRUE);
    if (state->close) MoveWindow(state->close, std::max(155, w-116), h-44, 104, 30, TRUE);
}

LRESULT CALLBACK window_proc(HWND window, UINT message, WPARAM wp, LPARAM lp) {
    DialogState* state = reinterpret_cast<DialogState*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    switch (message) {
    case WM_NCCREATE: {
        CREATESTRUCTW* created = reinterpret_cast<CREATESTRUCTW*>(lp);
        SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(created->lpCreateParams));
        return TRUE;
    }
    case WM_CREATE: {
        state = reinterpret_cast<DialogState*>(GetWindowLongPtrW(window, GWLP_USERDATA));
        if (!state) return -1;
        state->editor = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", state->details.c_str(),
                    WS_CHILD | WS_VISIBLE | WS_VSCROLL | WS_HSCROLL | ES_MULTILINE |
                    ES_READONLY | ES_AUTOVSCROLL | ES_AUTOHSCROLL,
                    0, 0, 100, 100, window, reinterpret_cast<HMENU>(static_cast<INT_PTR>(ID_TRACE)),
                    GetModuleHandleW(nullptr), nullptr);
        state->copy = CreateWindowExW(0, L"BUTTON", L"Copy Traceback",
                    WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, 0, 0, 120, 30, window,
                    reinterpret_cast<HMENU>(static_cast<INT_PTR>(ID_COPY)), GetModuleHandleW(nullptr), nullptr);
        state->close = CreateWindowExW(0, L"BUTTON", L"Close",
                    WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 0, 0, 100, 30, window,
                    reinterpret_cast<HMENU>(static_cast<INT_PTR>(ID_CLOSE)), GetModuleHandleW(nullptr), nullptr);
        if (!state->editor || !state->copy || !state->close) return -1;
        SendMessageW(state->editor, EM_LIMITTEXT, 600000, 0);
        HFONT font = static_cast<HFONT>(GetStockObject(DEFAULT_GUI_FONT));
        for (HWND child : {state->editor, state->copy, state->close})
            SendMessageW(child, WM_SETFONT, reinterpret_cast<WPARAM>(font), TRUE);
        layout(window, state);
        return 0;
    }
    case WM_SIZE:
        layout(window, state);
        return 0;
    case WM_COMMAND:
        if (LOWORD(wp) == ID_COPY && state) {
            clipboard_copy(window, state->details);
            return 0;
        }
        if (LOWORD(wp) == ID_CLOSE) {
            DestroyWindow(window);
            return 0;
        }
        break;
    case WM_CLOSE:
        DestroyWindow(window);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(window, message, wp, lp);
}

void show_crash(DialogState& state) {
    HINSTANCE instance = GetModuleHandleW(nullptr);
    WNDCLASSEXW klass{};
    klass.cbSize = sizeof(klass);
    klass.hInstance = instance;
    klass.lpfnWndProc = window_proc;
    klass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    klass.hIcon = LoadIconW(nullptr, IDI_ERROR);
    klass.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_BTNFACE + 1);
    klass.lpszClassName = L"CommodoreC64DismCrashWatchdogWindow";
    RegisterClassExW(&klass);
    HWND window = CreateWindowExW(WS_EX_APPWINDOW, klass.lpszClassName, state.title.c_str(),
                    WS_OVERLAPPEDWINDOW | WS_VISIBLE, CW_USEDEFAULT, CW_USEDEFAULT, 900, 600,
                    nullptr, nullptr, instance, &state);
    if (!window) {
        MessageBoxW(nullptr, state.details.substr(0, 2800).c_str(), state.title.c_str(),
                    MB_ICONERROR | MB_OK | MB_SYSTEMMODAL);
        return;
    }
    ShowWindow(window, SW_SHOW);
    UpdateWindow(window);
    MSG message{};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
}

}  // namespace

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    Options opts;
    if (!parse_args(opts)) return 2;
    // PID mutex avoids multiple watcher dialogs on repeated Python imports.
    std::wstring mutex_name = L"Local\\CommodoreC64Dism_Watchdog_" + std::to_wstring(opts.pid);
    HANDLE mutex = CreateMutexW(nullptr, TRUE, mutex_name.c_str());
    if (!mutex) return 3;
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        notify_ready(opts.readyEvent);
        CloseHandle(mutex);
        return 0;
    }
    HANDLE process = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, opts.pid);
    if (!process) {
        ReleaseMutex(mutex);
        CloseHandle(mutex);
        return 4;
    }
    notify_ready(opts.readyEvent);
    DWORD wait = WaitForSingleObject(process, INFINITE);
    DWORD status = 0;
    bool valid = (wait == WAIT_OBJECT_0 && GetExitCodeProcess(process, &status));
    CloseHandle(process);
    ReleaseMutex(mutex);
    CloseHandle(mutex);
    if (!valid || !status) return valid ? 0 : 5;

    const std::wstring fatal = read_tail(opts.fatalLog);
    // Match PythonBDE: expected startup exits (1/2) don't count as crashes
    // unless the native faulthandler captured an actual failure.
    if ((status == 1 || status == 2) && fatal.empty()) return 0;

    std::wstring details = L"The monitored Commodore C64 DISM process ended unexpectedly.\r\n";
    details += L"Application: " + opts.role + L"\r\n";
    details += L"Process ID: " + std::to_wstring(opts.pid) + L"\r\n";
    details += L"Exit code: " + hex_code(status) + L" (" + std::to_wstring(status) + L")\r\n\r\n";
    if (!fatal.empty()) details += L"=== Native / faulthandler traceback ===\r\n" + fatal + L"\r\n\r\n";
    std::wstring errors = read_tail(opts.errorLog);
    if (!errors.empty()) details += L"=== Recent Python error log ===\r\n" + errors + L"\r\n";
    if (fatal.empty() && errors.empty())
        details += L"No traceback available. Check Windows Event Viewer / WER dumps.\r\n";
    DialogState dialog;
    dialog.title = opts.role + L" - Crash Watchdog";
    dialog.details = std::move(details);
    show_crash(dialog);
    return 0;
}

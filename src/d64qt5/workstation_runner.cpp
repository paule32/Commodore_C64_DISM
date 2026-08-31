// ---------------------------------------------------------------------------
// File:   workstation_runner.cpp
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
// Generic Workstation host/launcher for PE32/PE32+ programs which do not
// initialize d64qt5 themselves.  The authoritative Workstation lifecycle stays
// in the existing d64_workstation.cpp (OWNER/JOINED/Desktop/Panel/EXIT).
// ---------------------------------------------------------------------------
#include "d64_workstation.h"

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#endif

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cwchar>
#include <cwctype>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace {

constexpr wchar_t RUNNER_WINDOW_CLASS[] = L"D64WorkstationRunnerWindow";
constexpr wchar_t RUNNER_WINDOW_TITLE[] = L"D64 Workstation Runner";
constexpr wchar_t RUNNER_PIPE_NAME[] = L"\\\\.\\pipe\\dBase2Many.D64Workstation.Runner.v1";
constexpr std::uint32_t RUNNER_PIPE_MAGIC = 0x31525744u; // "DWR1"
constexpr UINT WM_RUNNER_LAUNCH = WM_APP + 0x321;
constexpr UINT WM_RUNNER_EXIT   = WM_APP + 0x322;
constexpr UINT_PTR RUNNER_TIMER = 0xD641;

constexpr wchar_t D64_APP_WINDOW_PREFIX[] = L"dBase2Many.D64ApplicationWindow.";
constexpr wchar_t WORKSTATION_PANEL_CLASS[] = L"D64WorkstationPanel";
constexpr wchar_t WORKSTATION_BOTTOM_PANEL_CLASS[] = L"D64WorkstationBottomPanel";

constexpr int WORKSTATION_PANEL_WIDTH = 76;
constexpr int WORKSTATION_DB_CLICK_TOP = 176;
constexpr int WORKSTATION_ITEM_HEIGHT = 86;

struct PipeHeader {
    std::uint32_t magic;
    std::uint32_t flags;
    std::uint32_t pathBytes;
    std::uint32_t cwdBytes;
};

struct LaunchRequest {
    std::wstring application;
    std::wstring workingDirectory;
    bool consoleMode = false;
};

struct ChildProcess {
    std::wstring canonicalPath;
    HANDLE process = nullptr;
    DWORD pid = 0;
};

HWND g_host_window = nullptr;
HHOOK g_mouse_hook = nullptr;
HHOOK g_keyboard_hook = nullptr;
HWND g_close_candidate = nullptr;
std::vector<HWND> g_hidden_windows;
std::vector<ChildProcess> g_children;
std::thread g_pipe_thread;
std::atomic<bool> g_pipe_stop{false};
bool g_leave_started = false;

// Der DB-Button repraesentiert das zuletzt an den Runner uebergebene
// Hauptprogramm. Dadurch kann das Programm nach einem normalen Schliessen
// (Hide) wieder angezeigt oder nach einem echten Prozessende neu gestartet
// werden.
LaunchRequest g_db_launch_request;
bool g_has_db_launch_request = false;

UINT workstation_global_shutdown_message()
{
    static const UINT message = RegisterWindowMessageW(
        L"dBase2Many.D64Workstation.GlobalShutdown"
    );
    return message;
}

std::wstring normalize_path(const std::wstring &path)
{
    if (path.empty())
        return std::wstring();

    wchar_t fullPath[32768] = {0};
    const DWORD length = GetFullPathNameW(
        path.c_str(),
        static_cast<DWORD>(sizeof(fullPath) / sizeof(fullPath[0])),
        fullPath,
        nullptr
    );

    std::wstring result =
        (length > 0 && length < (sizeof(fullPath) / sizeof(fullPath[0])))
            ? std::wstring(fullPath, length)
            : path;

    for (wchar_t &ch : result) {
        if (ch == L'/')
            ch = L'\\';
        ch = static_cast<wchar_t>(std::towlower(ch));
    }
    return result;
}


std::vector<std::wstring> split_runner_command_line(const wchar_t *text)
{
    std::vector<std::wstring> args;
    if (!text)
        return args;

    const wchar_t *cursor = text;
    while (*cursor) {
        while (*cursor && std::iswspace(*cursor))
            ++cursor;
        if (!*cursor)
            break;

        std::wstring value;
        bool quoted = false;
        while (*cursor) {
            if (*cursor == L'"') {
                quoted = !quoted;
                ++cursor;
                continue;
            }
            if (!quoted && std::iswspace(*cursor))
                break;
            value.push_back(*cursor++);
        }
        args.push_back(value);
        while (*cursor && std::iswspace(*cursor))
            ++cursor;
    }
    return args;
}

std::wstring absolute_path(const std::wstring &path)
{
    if (path.empty())
        return std::wstring();

    wchar_t fullPath[32768] = {0};
    const DWORD length = GetFullPathNameW(
        path.c_str(),
        static_cast<DWORD>(sizeof(fullPath) / sizeof(fullPath[0])),
        fullPath,
        nullptr
    );
    if (length > 0 && length < (sizeof(fullPath) / sizeof(fullPath[0])))
        return std::wstring(fullPath, length);
    return path;
}

std::wstring parent_directory(const std::wstring &path)
{
    const std::wstring full = absolute_path(path);
    const std::wstring::size_type slash = full.find_last_of(L"\\/");
    if (slash == std::wstring::npos)
        return std::wstring();
    if (slash == 2 && full.size() >= 3 && full[1] == L':')
        return full.substr(0, 3);
    return full.substr(0, slash);
}

bool regular_file_exists(const std::wstring &path)
{
    const DWORD attributes = GetFileAttributesW(path.c_str());
    return attributes != INVALID_FILE_ATTRIBUTES &&
        (attributes & FILE_ATTRIBUTE_DIRECTORY) == 0;
}

bool pe_uses_console_subsystem(const std::wstring &path)
{
    HANDLE file = CreateFileW(
        path.c_str(),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        nullptr
    );
    if (file == INVALID_HANDLE_VALUE)
        return false;

    bool console = false;
    IMAGE_DOS_HEADER dos{};
    DWORD got = 0;
    if (!ReadFile(file, &dos, sizeof(dos), &got, nullptr) ||
        got != sizeof(dos) || dos.e_magic != IMAGE_DOS_SIGNATURE) {
        CloseHandle(file);
        return false;
    }

    LARGE_INTEGER position{};
    position.QuadPart = dos.e_lfanew;
    if (!SetFilePointerEx(file, position, nullptr, FILE_BEGIN)) {
        CloseHandle(file);
        return false;
    }

    DWORD signature = 0;
    IMAGE_FILE_HEADER fileHeader{};
    WORD optionalMagic = 0;
    if (!ReadFile(file, &signature, sizeof(signature), &got, nullptr) ||
        got != sizeof(signature) || signature != IMAGE_NT_SIGNATURE ||
        !ReadFile(file, &fileHeader, sizeof(fileHeader), &got, nullptr) ||
        got != sizeof(fileHeader) ||
        !ReadFile(file, &optionalMagic, sizeof(optionalMagic), &got, nullptr) ||
        got != sizeof(optionalMagic)) {
        CloseHandle(file);
        return false;
    }

    position.QuadPart = dos.e_lfanew + sizeof(DWORD) + sizeof(IMAGE_FILE_HEADER);
    if (!SetFilePointerEx(file, position, nullptr, FILE_BEGIN)) {
        CloseHandle(file);
        return false;
    }

    if (optionalMagic == IMAGE_NT_OPTIONAL_HDR32_MAGIC) {
        IMAGE_OPTIONAL_HEADER32 optional{};
        if (ReadFile(file, &optional, sizeof(optional), &got, nullptr) &&
            got == sizeof(optional)) {
            console = optional.Subsystem == IMAGE_SUBSYSTEM_WINDOWS_CUI;
        }
    } else if (optionalMagic == IMAGE_NT_OPTIONAL_HDR64_MAGIC) {
        IMAGE_OPTIONAL_HEADER64 optional{};
        if (ReadFile(file, &optional, sizeof(optional), &got, nullptr) &&
            got == sizeof(optional)) {
            console = optional.Subsystem == IMAGE_SUBSYSTEM_WINDOWS_CUI;
        }
    }

    CloseHandle(file);
    return console;
}

void show_runner_usage()
{
    MessageBoxW(
        nullptr,
        L"Direkter Start:\n\n"
        L"  d64_workstation_runner.exe <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --console <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --gui <Anwendung.exe>\n"
        L"  d64_workstation_runner.exe --cwd <Verzeichnis> <Anwendung.exe>\n\n"
        L"Ohne --console/--gui wird das PE-Subsystem automatisch erkannt.\n"
        L"Ohne Anwendung bleibt der Runner als kompatibler Pipe-Host aktiv.",
        L"D64 Workstation Runner",
        MB_OK | MB_ICONINFORMATION | MB_SETFOREGROUND
    );
}

bool parse_runner_command_line(
    const wchar_t *commandLine,
    LaunchRequest &request,
    bool &hasRequest,
    bool &showHelp
)
{
    hasRequest = false;
    showHelp = false;
    request = LaunchRequest();

    const std::vector<std::wstring> args = split_runner_command_line(commandLine);
    if (args.empty())
        return true;

    bool modeSpecified = false;
    std::wstring application;
    std::wstring workingDirectory;

    for (std::size_t i = 0; i < args.size(); ++i) {
        const std::wstring &arg = args[i];
        if (_wcsicmp(arg.c_str(), L"--help") == 0 ||
            _wcsicmp(arg.c_str(), L"-h") == 0 ||
            _wcsicmp(arg.c_str(), L"/?") == 0) {
            showHelp = true;
            return true;
        }
        if (_wcsicmp(arg.c_str(), L"--console") == 0) {
            request.consoleMode = true;
            modeSpecified = true;
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--gui") == 0) {
            request.consoleMode = false;
            modeSpecified = true;
            continue;
        }
        if (_wcsicmp(arg.c_str(), L"--cwd") == 0) {
            if (i + 1 >= args.size())
                return false;
            workingDirectory = args[++i];
            continue;
        }
        if (arg.size() >= 2 && arg[0] == L'-')
            return false;
        if (!application.empty())
            return false;
        application = arg;
    }

    if (application.empty())
        return false;

    application = absolute_path(application);
    if (!regular_file_exists(application))
        return false;

    if (workingDirectory.empty())
        workingDirectory = parent_directory(application);
    else
        workingDirectory = absolute_path(workingDirectory);

    request.application = application;
    request.workingDirectory = workingDirectory;
    if (!modeSpecified)
        request.consoleMode = pe_uses_console_subsystem(application);
    hasRequest = true;
    return true;
}

bool class_name_equals(HWND hwnd, const wchar_t *expected)
{
    if (!hwnd || !expected)
        return false;
    wchar_t className[256] = {0};
    if (!GetClassNameW(hwnd, className, 255))
        return false;
    return _wcsicmp(className, expected) == 0;
}

struct PropertyScanContext {
    bool found = false;
};

int CALLBACK scan_window_property(
    HWND,
    LPWSTR string,
    HANDLE,
    ULONG_PTR parameter
)
{
    PropertyScanContext *context =
        reinterpret_cast<PropertyScanContext *>(parameter);
    if (!context || context->found || !string)
        return FALSE;

    wchar_t atomName[256] = {0};
    const wchar_t *name = string;
    if (IS_INTRESOURCE(string)) {
        const ATOM atom = static_cast<ATOM>(reinterpret_cast<ULONG_PTR>(string));
        if (!GlobalGetAtomNameW(atom, atomName, 255))
            return TRUE;
        name = atomName;
    }

    constexpr std::size_t prefixLength =
        (sizeof(D64_APP_WINDOW_PREFIX) / sizeof(D64_APP_WINDOW_PREFIX[0])) - 1;
    if (_wcsnicmp(name, D64_APP_WINDOW_PREFIX, prefixLength) == 0) {
        context->found = true;
        return FALSE;
    }
    return TRUE;
}

bool has_d64_application_marker(HWND hwnd)
{
    if (!hwnd || !IsWindow(hwnd))
        return false;
    PropertyScanContext context;
    EnumPropsExW(hwnd, &scan_window_property, reinterpret_cast<LPARAM>(&context));
    return context.found;
}

bool is_workstation_panel(HWND hwnd)
{
    if (!hwnd)
        return false;
    return class_name_equals(hwnd, WORKSTATION_PANEL_CLASS) ||
           class_name_equals(hwnd, WORKSTATION_BOTTOM_PANEL_CLASS);
}

bool is_db_panel_click(const POINT &screenPoint)
{
    HWND hwnd = WindowFromPoint(screenPoint);
    if (!hwnd)
        return false;
    hwnd = GetAncestor(hwnd, GA_ROOT);
    if (!class_name_equals(hwnd, WORKSTATION_PANEL_CLASS))
        return false;

    POINT point = screenPoint;
    if (!ScreenToClient(hwnd, &point))
        return false;
    return point.x >= 0 && point.x < WORKSTATION_PANEL_WIDTH &&
           point.y >= WORKSTATION_DB_CLICK_TOP &&
           point.y < WORKSTATION_DB_CLICK_TOP + WORKSTATION_ITEM_HEIGHT;
}

bool is_candidate_application_window(HWND hwnd)
{
    if (!hwnd || !IsWindow(hwnd) || hwnd == g_host_window)
        return false;
    if (is_workstation_panel(hwnd))
        return false;
    if (!IsWindowVisible(hwnd))
        return false;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    const LONG_PTR exStyle = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    if ((style & WS_CHILD) != 0 || (exStyle & WS_EX_TOOLWINDOW) != 0)
        return false;

    // Dialoge/Popups duerfen ihr normales Close-Verhalten behalten. Fuer die
    // Workstation-Semantik wird nur das Hauptfenster einer Anwendung versteckt.
    if (GetWindow(hwnd, GW_OWNER) != nullptr)
        return false;

    // d64qt5-Fenster besitzen bereits Stage-128-closeEvent()/Dialog-Restore.
    // Diese bestehende Logik darf der generische Runner nicht uebergehen.
    if (has_d64_application_marker(hwnd))
        return false;

    return true;
}

bool point_hits_close_button(HWND hwnd, const POINT &point)
{
    if (!is_candidate_application_window(hwnd))
        return false;

    DWORD_PTR hit = HTNOWHERE;
    const LPARAM packed = MAKELPARAM(
        static_cast<SHORT>(point.x),
        static_cast<SHORT>(point.y)
    );
    if (!SendMessageTimeoutW(
            hwnd,
            WM_NCHITTEST,
            0,
            packed,
            SMTO_ABORTIFHUNG | SMTO_BLOCK,
            100,
            &hit)) {
        return false;
    }
    return static_cast<LRESULT>(hit) == HTCLOSE;
}

void remember_hidden_window(HWND hwnd)
{
    if (!hwnd || !IsWindow(hwnd))
        return;
    if (std::find(g_hidden_windows.begin(), g_hidden_windows.end(), hwnd)
        == g_hidden_windows.end()) {
        g_hidden_windows.push_back(hwnd);
    }
}

void hide_application_window(HWND hwnd)
{
    if (!is_candidate_application_window(hwnd))
        return;
    remember_hidden_window(hwnd);
    ShowWindowAsync(hwnd, SW_HIDE);
}

struct RestoreMarkedContext {
    HWND host = nullptr;
    std::vector<HWND> restored;
};

BOOL CALLBACK restore_marked_window(HWND hwnd, LPARAM parameter)
{
    RestoreMarkedContext *context =
        reinterpret_cast<RestoreMarkedContext *>(parameter);
    if (!context || !hwnd || !IsWindow(hwnd) || hwnd == context->host)
        return TRUE;
    if (IsWindowVisible(hwnd))
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    const LONG_PTR exStyle = GetWindowLongPtrW(hwnd, GWL_EXSTYLE);
    if ((style & WS_CHILD) != 0 || (exStyle & WS_EX_TOOLWINDOW) != 0)
        return TRUE;
    if (!has_d64_application_marker(hwnd))
        return TRUE;

    ShowWindowAsync(hwnd, SW_RESTORE);
    ShowWindowAsync(hwnd, SW_SHOW);
    context->restored.push_back(hwnd);
    return TRUE;
}

void restore_hidden_windows()
{
    HWND last = nullptr;
    for (auto it = g_hidden_windows.begin(); it != g_hidden_windows.end();) {
        HWND hwnd = *it;
        if (!hwnd || !IsWindow(hwnd)) {
            it = g_hidden_windows.erase(it);
            continue;
        }
        ShowWindowAsync(hwnd, SW_RESTORE);
        ShowWindowAsync(hwnd, SW_SHOW);
        last = hwnd;
        ++it;
    }

    // Wenn der Runner OWNER ist und spaeter eine d64qt5-Anwendung JOINED,
    // liegt deren DB-Callback in einem anderen Prozess. Deshalb wird ihr
    // markiertes Hauptfenster zusaetzlich direkt wieder sichtbar gemacht.
    const wchar_t *desktopName = D64WorkstationDesktopName();
    if (desktopName && *desktopName) {
        HDESK desktop = OpenDesktopW(
            desktopName,
            0,
            FALSE,
            DESKTOP_ENUMERATE | DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS
        );
        if (desktop) {
            RestoreMarkedContext context;
            context.host = g_host_window;
            EnumDesktopWindows(
                desktop,
                &restore_marked_window,
                reinterpret_cast<LPARAM>(&context)
            );
            if (!context.restored.empty())
                last = context.restored.back();
            CloseDesktop(desktop);
        }
    }

    if (last && IsWindow(last)) {
        DWORD pid = 0;
        GetWindowThreadProcessId(last, &pid);
        if (pid)
            AllowSetForegroundWindow(pid);
        SetWindowPos(
            last, HWND_TOP, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
        );
        BringWindowToTop(last);
        SetForegroundWindow(last);
    }
}

LRESULT CALLBACK runner_mouse_proc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode < 0)
        return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);

    const MSLLHOOKSTRUCT *mouse =
        reinterpret_cast<const MSLLHOOKSTRUCT *>(lParam);
    if (!mouse)
        return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);

    if (wParam == WM_LBUTTONUP && is_db_panel_click(mouse->pt)) {
        restore_hidden_windows();
        return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);
    }

    if (wParam == WM_LBUTTONDOWN) {
        HWND hwnd = WindowFromPoint(mouse->pt);
        if (hwnd)
            hwnd = GetAncestor(hwnd, GA_ROOT);
        if (point_hits_close_button(hwnd, mouse->pt)) {
            g_close_candidate = hwnd;
            return 1;
        }
        g_close_candidate = nullptr;
    } else if (wParam == WM_LBUTTONUP && g_close_candidate) {
        HWND candidate = g_close_candidate;
        g_close_candidate = nullptr;
        hide_application_window(candidate);
        return 1;
    }

    return CallNextHookEx(g_mouse_hook, nCode, wParam, lParam);
}

bool install_mouse_guard()
{
    if (g_mouse_hook)
        return true;
    g_mouse_hook = SetWindowsHookExW(
        WH_MOUSE_LL,
        &runner_mouse_proc,
        GetModuleHandleW(nullptr),
        0
    );
    return g_mouse_hook != nullptr;
}

void remove_mouse_guard()
{
    if (!g_mouse_hook)
        return;
    UnhookWindowsHookEx(g_mouse_hook);
    g_mouse_hook = nullptr;
}

LRESULT CALLBACK runner_keyboard_proc(int nCode, WPARAM wParam, LPARAM lParam)
{
    if (nCode < 0)
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);

    if (wParam != WM_KEYDOWN && wParam != WM_SYSKEYDOWN)
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);

    const KBDLLHOOKSTRUCT *kbd =
        reinterpret_cast<const KBDLLHOOKSTRUCT *>(lParam);
    if (!kbd)
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);

    const bool alt =
        ((kbd->flags & LLKHF_ALTDOWN) != 0) ||
        ((GetAsyncKeyState(VK_MENU) & 0x8000) != 0);

    if (alt && kbd->vkCode == VK_F4) {
        HWND focused = GetForegroundWindow();
        if (focused)
            focused = GetAncestor(focused, GA_ROOTOWNER);
        if (!focused)
            focused = GetForegroundWindow();

        if (is_candidate_application_window(focused)) {
            hide_application_window(focused);
            return 1;
        }
    }

    return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);
}

bool install_keyboard_guard()
{
    if (g_keyboard_hook)
        return true;
    g_keyboard_hook = SetWindowsHookExW(
        WH_KEYBOARD_LL,
        &runner_keyboard_proc,
        GetModuleHandleW(nullptr),
        0
    );
    return g_keyboard_hook != nullptr;
}

void remove_keyboard_guard()
{
    if (!g_keyboard_hook)
        return;
    UnhookWindowsHookEx(g_keyboard_hook);
    g_keyboard_hook = nullptr;
}

void cleanup_finished_children()
{
    for (auto it = g_children.begin(); it != g_children.end();) {
        if (!it->process) {
            it = g_children.erase(it);
            continue;
        }
        if (WaitForSingleObject(it->process, 0) == WAIT_OBJECT_0) {
            CloseHandle(it->process);
            it = g_children.erase(it);
            continue;
        }
        ++it;
    }
}

ChildProcess *find_running_child(const std::wstring &canonicalPath)
{
    cleanup_finished_children();
    for (ChildProcess &child : g_children) {
        if (_wcsicmp(child.canonicalPath.c_str(), canonicalPath.c_str()) == 0)
            return &child;
    }
    return nullptr;
}

struct ActivateChildWindowContext
{
    DWORD pid;
    HWND target;
};

BOOL CALLBACK activate_child_window_enum_proc(HWND hwnd, LPARAM value)
{
    ActivateChildWindowContext *ctx =
        reinterpret_cast<ActivateChildWindowContext *>(value);
    if (!ctx)
        return FALSE;

    DWORD windowPid = 0;
    GetWindowThreadProcessId(hwnd, &windowPid);
    if (windowPid != ctx->pid)
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    if ((style & WS_CHILD) != 0)
        return TRUE;

    ctx->target = hwnd;
    return FALSE;
}

bool switch_to_workstation_desktop()
{
    const wchar_t *desktopName = D64WorkstationDesktopName();
    if (!desktopName || !*desktopName)
        desktopName = L"D64Workstation";

    HDESK desktop = OpenDesktopW(
        desktopName,
        0,
        FALSE,
        DESKTOP_SWITCHDESKTOP |
        DESKTOP_ENUMERATE |
        DESKTOP_READOBJECTS |
        DESKTOP_WRITEOBJECTS
    );
    if (!desktop)
        return false;

    const BOOL ok = SwitchDesktop(desktop);
    CloseDesktop(desktop);
    return ok != FALSE;
}

bool activate_child_windows(DWORD pid)
{
    ActivateChildWindowContext context = {};
    context.pid = pid;
    context.target = nullptr;

    /*
     * Der Runner-GUI-Thread wurde durch D64WorkstationPrepare() bereits an
     * D64Workstation gebunden. EnumWindows() sieht deshalb genau die Fenster
     * dieses Desktops.
     */
    EnumWindows(
        &activate_child_window_enum_proc,
        reinterpret_cast<LPARAM>(&context)
    );

    if (!context.target)
        return false;

    /*
     * Stage 254:
     * Eine generische, vom Runner gestartete PE-GUI besitzt keine eigene
     * d64qt5-Workstation-Runtime. Deshalb kann sie D64WorkstationActivate()
     * nicht selbst aufrufen. Der Runner macht das Sichtbarmachen hier
     * stellvertretend.
     */
    switch_to_workstation_desktop();

    ShowWindowAsync(context.target, SW_RESTORE);
    ShowWindowAsync(context.target, SW_SHOW);

    SetWindowPos(
        context.target,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE |
        SWP_NOSIZE |
        SWP_SHOWWINDOW
    );

    AllowSetForegroundWindow(pid);
    BringWindowToTop(context.target);
    SetForegroundWindow(context.target);
    return true;
}

bool launch_program(const LaunchRequest &request)
{
    if (request.application.empty())
        return false;

    // Der zuletzt uebergebene Startauftrag wird zum Ziel des DB-Icons.
    // Auch Pipe-/CLI-Starts aktualisieren damit konsistent dieselbe Anwendung.
    g_db_launch_request = request;
    g_has_db_launch_request = true;

    const std::wstring canonical = normalize_path(request.application);
    if (canonical.empty())
        return false;

    if (ChildProcess *existing = find_running_child(canonical)) {
        switch_to_workstation_desktop();
        activate_child_windows(existing->pid);
        restore_hidden_windows();
        return true;
    }

    std::wstring desktopSpec = L"WinSta0\\";
    const wchar_t *desktopName = D64WorkstationDesktopName();
    desktopSpec += (desktopName && *desktopName) ? desktopName : L"D64Workstation";

    std::wstring commandLine = L"\"";
    commandLine += request.application;
    commandLine += L"\"";
    std::vector<wchar_t> command(commandLine.begin(), commandLine.end());
    command.push_back(L'\0');

    STARTUPINFOW startup;
    ZeroMemory(&startup, sizeof(startup));
    startup.cb = sizeof(startup);
    startup.lpDesktop = const_cast<LPWSTR>(desktopSpec.c_str());

    PROCESS_INFORMATION processInfo;
    ZeroMemory(&processInfo, sizeof(processInfo));

    DWORD creationFlags = CREATE_UNICODE_ENVIRONMENT | CREATE_NEW_PROCESS_GROUP;
    if (request.consoleMode)
        creationFlags |= CREATE_NEW_CONSOLE;

    const BOOL ok = CreateProcessW(
        request.application.c_str(),
        command.data(),
        nullptr,
        nullptr,
        FALSE,
        creationFlags,
        nullptr,
        request.workingDirectory.empty()
            ? nullptr
            : request.workingDirectory.c_str(),
        &startup,
        &processInfo
    );
    if (!ok)
        return false;

    CloseHandle(processInfo.hThread);

    ChildProcess child;
    child.canonicalPath = canonical;
    child.process = processInfo.hProcess;
    child.pid = processInfo.dwProcessId;
    g_children.push_back(child);

    /*
     * Stage 254:
     * CreateProcessW() allein garantiert bei einem generischen GUI-Target
     * nicht, dass das erste Top-Level-HWND schon existiert bzw. sichtbar ist.
     * Bei --gui warten wir auf die GUI-Initialisierung und suchen danach das
     * Fenster des neuen Prozesses auf D64Workstation. Sobald es existiert,
     * wird es restauriert, sichtbar gemacht und aktiviert.
     *
     * Kein Compiler/Make-Aufruf und keine Runtime-Injektion in die Ziel-EXE.
     */
    if (!request.consoleMode) {
        switch_to_workstation_desktop();

        /*
         * WaitForInputIdle() kehrt bei normalen Win32-/Qt-GUI-Programmen
         * zurueck, sobald deren Message Queue initialisiert wurde. Ein Fehler
         * ist nicht fatal; danach wird trotzdem per HWND-Polling gesucht.
         */
        WaitForInputIdle(processInfo.hProcess, 1500);

        const DWORD deadline = GetTickCount() + 3000;
        for (;;) {
            if (WaitForSingleObject(processInfo.hProcess, 0) == WAIT_OBJECT_0)
                break;

            if (activate_child_windows(processInfo.dwProcessId))
                break;

            if (static_cast<LONG>(GetTickCount() - deadline) >= 0)
                break;

            Sleep(25);
        }
    } else {
        /*
         * Auch eine neu gestartete Console-Anwendung muss auf der sichtbaren
         * Workstation landen, wenn zuvor ein anderer Desktop aktiv war.
         */
        switch_to_workstation_desktop();
    }

    return true;
}

struct CloseChildWindowContext
{
    DWORD pid;
};

BOOL CALLBACK close_child_window_enum_proc(HWND hwnd, LPARAM value)
{
    CloseChildWindowContext *ctx =
        reinterpret_cast<CloseChildWindowContext *>(value);
    if (!ctx)
        return FALSE;

    DWORD windowPid = 0;
    GetWindowThreadProcessId(hwnd, &windowPid);
    if (windowPid != ctx->pid)
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    if ((style & WS_CHILD) != 0)
        return TRUE;

    PostMessageW(hwnd, WM_CLOSE, 0, 0);
    return TRUE;
}

void request_child_window_close(DWORD pid)
{
    CloseChildWindowContext context = {};
    context.pid = pid;

    const wchar_t *desktopName = D64WorkstationDesktopName();
    if (!desktopName || !*desktopName)
        return;

    HDESK desktop = OpenDesktopW(
        desktopName,
        0,
        FALSE,
        DESKTOP_ENUMERATE | DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS
    );
    if (!desktop)
        return;

    EnumDesktopWindows(
        desktop,
        &close_child_window_enum_proc,
        reinterpret_cast<LPARAM>(&context)
    );
    CloseDesktop(desktop);
}

void terminate_children()
{
    cleanup_finished_children();

    // Red Workstation EXIT authorizes a real application shutdown. Give GUI
    // programs a chance to process WM_CLOSE and release files/sessions first.
    for (ChildProcess &child : g_children) {
        if (!child.process ||
            WaitForSingleObject(child.process, 0) == WAIT_OBJECT_0)
            continue;
        request_child_window_close(child.pid);
    }

    const DWORD deadline = GetTickCount() + 2000;
    for (;;) {
        bool anyRunning = false;
        for (ChildProcess &child : g_children) {
            if (child.process &&
                WaitForSingleObject(child.process, 0) != WAIT_OBJECT_0) {
                anyRunning = true;
                break;
            }
        }
        if (!anyRunning || static_cast<LONG>(GetTickCount() - deadline) >= 0)
            break;
        Sleep(25);
    }

    // Console applications without a closeable top-level window, or hung
    // programs, must not keep the Workstation session alive after EXIT.
    for (ChildProcess &child : g_children) {
        if (!child.process)
            continue;
        if (WaitForSingleObject(child.process, 0) != WAIT_OBJECT_0) {
            TerminateProcess(child.process, 0);
            WaitForSingleObject(child.process, 1000);
        }
        CloseHandle(child.process);
        child.process = nullptr;
    }
    g_children.clear();
}


bool write_exact(HANDLE pipe, const void *buffer, DWORD bytes)
{
    const BYTE *source = static_cast<const BYTE *>(buffer);
    DWORD total = 0;
    while (total < bytes) {
        DWORD written = 0;
        if (!WriteFile(
                pipe,
                source + total,
                bytes - total,
                &written,
                nullptr) || written == 0) {
            return false;
        }
        total += written;
    }
    return true;
}

bool send_request_to_existing_runner(
    const LaunchRequest &request,
    DWORD timeoutMs
)
{
    if (request.application.empty())
        return false;

    const DWORD started = GetTickCount();
    HANDLE pipe = INVALID_HANDLE_VALUE;

    for (;;) {
        if (WaitNamedPipeW(RUNNER_PIPE_NAME, 200)) {
            pipe = CreateFileW(
                RUNNER_PIPE_NAME,
                GENERIC_WRITE,
                0,
                nullptr,
                OPEN_EXISTING,
                0,
                nullptr
            );
            if (pipe != INVALID_HANDLE_VALUE)
                break;
        }

        if (static_cast<DWORD>(GetTickCount() - started) >= timeoutMs)
            return false;
        Sleep(50);
    }

    const std::uint64_t pathBytes64 =
        static_cast<std::uint64_t>(request.application.size()) * sizeof(wchar_t);
    const std::uint64_t cwdBytes64 =
        static_cast<std::uint64_t>(request.workingDirectory.size()) * sizeof(wchar_t);
    if (pathBytes64 == 0 || pathBytes64 > 60u * 1024u ||
        cwdBytes64 > 60u * 1024u) {
        CloseHandle(pipe);
        return false;
    }

    PipeHeader header{};
    header.magic = RUNNER_PIPE_MAGIC;
    header.flags = request.consoleMode ? 1u : 0u;
    header.pathBytes = static_cast<std::uint32_t>(pathBytes64);
    header.cwdBytes = static_cast<std::uint32_t>(cwdBytes64);

    bool ok = write_exact(pipe, &header, sizeof(header));
    if (ok) {
        ok = write_exact(
            pipe,
            request.application.data(),
            header.pathBytes
        );
    }
    if (ok && header.cwdBytes) {
        ok = write_exact(
            pipe,
            request.workingDirectory.data(),
            header.cwdBytes
        );
    }

    FlushFileBuffers(pipe);
    CloseHandle(pipe);
    return ok;
}

bool read_exact(HANDLE pipe, void *buffer, DWORD bytes)
{
    BYTE *target = static_cast<BYTE *>(buffer);
    DWORD total = 0;
    while (total < bytes) {
        DWORD got = 0;
        if (!ReadFile(pipe, target + total, bytes - total, &got, nullptr) || got == 0)
            return false;
        total += got;
    }
    return true;
}

void pipe_server_loop()
{
    while (!g_pipe_stop.load()) {
        HANDLE pipe = CreateNamedPipeW(
            RUNNER_PIPE_NAME,
            PIPE_ACCESS_INBOUND,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
            1,
            64 * 1024,
            64 * 1024,
            0,
            nullptr
        );
        if (pipe == INVALID_HANDLE_VALUE)
            return;

        const BOOL connected = ConnectNamedPipe(pipe, nullptr)
            ? TRUE
            : (GetLastError() == ERROR_PIPE_CONNECTED);

        if (!connected) {
            CloseHandle(pipe);
            if (g_pipe_stop.load())
                break;
            continue;
        }

        if (g_pipe_stop.load()) {
            DisconnectNamedPipe(pipe);
            CloseHandle(pipe);
            break;
        }

        PipeHeader header{};
        if (read_exact(pipe, &header, sizeof(header)) &&
            header.magic == RUNNER_PIPE_MAGIC &&
            header.pathBytes > 0 &&
            header.pathBytes <= 60 * 1024 &&
            header.cwdBytes <= 60 * 1024 &&
            (header.pathBytes % sizeof(wchar_t)) == 0 &&
            (header.cwdBytes % sizeof(wchar_t)) == 0) {

            std::vector<BYTE> pathBytes(header.pathBytes);
            std::vector<BYTE> cwdBytes(header.cwdBytes);
            const bool pathOk = read_exact(pipe, pathBytes.data(), header.pathBytes);
            const bool cwdOk = header.cwdBytes == 0 ||
                read_exact(pipe, cwdBytes.data(), header.cwdBytes);

            if (pathOk && cwdOk && g_host_window) {
                std::unique_ptr<LaunchRequest> request(new LaunchRequest());
                request->application.assign(
                    reinterpret_cast<const wchar_t *>(pathBytes.data()),
                    header.pathBytes / sizeof(wchar_t)
                );
                if (header.cwdBytes) {
                    request->workingDirectory.assign(
                        reinterpret_cast<const wchar_t *>(cwdBytes.data()),
                        header.cwdBytes / sizeof(wchar_t)
                    );
                }
                request->consoleMode = (header.flags & 1u) != 0;
                PostMessageW(
                    g_host_window,
                    WM_RUNNER_LAUNCH,
                    0,
                    reinterpret_cast<LPARAM>(request.release())
                );
            }
        }

        FlushFileBuffers(pipe);
        DisconnectNamedPipe(pipe);
        CloseHandle(pipe);
    }
}

void wake_pipe_server()
{
    HANDLE pipe = CreateFileW(
        RUNNER_PIPE_NAME,
        GENERIC_WRITE,
        0,
        nullptr,
        OPEN_EXISTING,
        0,
        nullptr
    );
    if (pipe != INVALID_HANDLE_VALUE)
        CloseHandle(pipe);
}

void stop_pipe_server()
{
    g_pipe_stop.store(true);
    wake_pipe_server();
    if (g_pipe_thread.joinable())
        g_pipe_thread.join();
}

void begin_leave_once()
{
    if (g_leave_started)
        return;
    g_leave_started = true;
    stop_pipe_server();
    remove_keyboard_guard();
    remove_mouse_guard();
    terminate_children();
    D64WorkstationBeginLeave();
}

void workstation_exit_requested()
{
    const int answer = MessageBoxW(
        nullptr,
        L"Moechten Sie die Workstation wirklich beenden?",
        L"Workstation beenden",
        MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON2 | MB_SETFOREGROUND
    );
    if (answer == IDYES && g_host_window)
        PostMessageW(g_host_window, WM_RUNNER_EXIT, 0, 0);
}

void workstation_db_requested()
{
    // Zuerst alle vom Runner versteckten Fenster wieder sichtbar machen.
    restore_hidden_windows();

    if (!g_has_db_launch_request)
        return;

    const std::wstring canonical =
        normalize_path(g_db_launch_request.application);
    if (canonical.empty())
        return;

    // Laeuft die Anwendung noch, wird keine zweite Instanz erzeugt.
    // Stattdessen das vorhandene Hauptfenster wiederherstellen/aktivieren.
    if (ChildProcess *existing = find_running_child(canonical)) {
        activate_child_windows(existing->pid);
        restore_hidden_windows();
        return;
    }

    // Der Prozess wurde wirklich beendet: derselbe gespeicherte Startauftrag
    // (EXE, Arbeitsverzeichnis, Console/GUI) wird erneut ausgefuehrt.
    if (!launch_program(g_db_launch_request)) {
        MessageBoxW(
            nullptr,
            L"Die DB-Anwendung konnte nicht erneut gestartet werden.",
            L"Workstation Mode",
            MB_OK | MB_ICONERROR | MB_SETFOREGROUND
        );
    }
}

LRESULT CALLBACK runner_window_proc(
    HWND hwnd,
    UINT message,
    WPARAM wParam,
    LPARAM lParam
)
{
    if (message == workstation_global_shutdown_message()) {
        PostMessageW(hwnd, WM_RUNNER_EXIT, 0, 0);
        return 0;
    }

    switch (message) {
    case WM_RUNNER_LAUNCH: {
        std::unique_ptr<LaunchRequest> request(
            reinterpret_cast<LaunchRequest *>(lParam)
        );
        if (request && !launch_program(*request)) {
            MessageBoxW(
                nullptr,
                L"Die Anwendung konnte nicht auf der Workstation gestartet werden.",
                L"Workstation Mode",
                MB_OK | MB_ICONERROR | MB_SETFOREGROUND
            );
        }
        return 0;
    }

    case WM_RUNNER_EXIT:
        begin_leave_once();
        PostQuitMessage(0);
        return 0;

    case WM_TIMER:
        if (wParam == RUNNER_TIMER)
            cleanup_finished_children();
        return 0;

    case WM_CLOSE:
        // Das Runner-Fenster selbst darf die Session nicht beenden. Es bleibt
        // unsichtbare Infrastruktur bis zum roten Workstation-EXIT.
        ShowWindow(hwnd, SW_HIDE);
        return 0;

    case WM_DESTROY:
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

bool register_runner_class(HINSTANCE instance)
{
    WNDCLASSEXW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = &runner_window_proc;
    wc.hInstance = instance;
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);
    wc.lpszClassName = RUNNER_WINDOW_CLASS;
    if (RegisterClassExW(&wc))
        return true;
    return GetLastError() == ERROR_CLASS_ALREADY_EXISTS;
}

HWND create_runner_window(HINSTANCE instance)
{
    return CreateWindowExW(
        WS_EX_TOOLWINDOW,
        RUNNER_WINDOW_CLASS,
        RUNNER_WINDOW_TITLE,
        WS_OVERLAPPEDWINDOW,
        120,
        120,
        360,
        180,
        nullptr,
        nullptr,
        instance,
        nullptr
    );
}

} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, LPWSTR commandLine, int)
{
    LaunchRequest startupRequest;
    bool hasStartupRequest = false;
    bool showHelp = false;
    if (!parse_runner_command_line(
            commandLine,
            startupRequest,
            hasStartupRequest,
            showHelp)) {
        show_runner_usage();
        return 20;
    }
    if (showHelp) {
        show_runner_usage();
        return 0;
    }

    if (!D64WorkstationPrepare()) {
        const DWORD error = GetLastError();
        // A resident Runner already owns its per-application mutex.  For the
        // new direct CLI syntax the short-lived second process forwards the
        // application to that Runner and exits immediately.
        if (error == ERROR_ALREADY_EXISTS && hasStartupRequest) {
            return send_request_to_existing_runner(startupRequest, 5000)
                ? 0
                : 11;
        }
        return error == ERROR_ALREADY_EXISTS ? 10 : 2;
    }

    if (!register_runner_class(instance)) {
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 3;
    }

    g_host_window = create_runner_window(instance);
    if (!g_host_window) {
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 4;
    }

    D64WorkstationSetExitCallback(&workstation_exit_requested);
    D64WorkstationSetDbCallback(&workstation_db_requested);

    // Activate() requires a visible HWND. OWNER creates/switches the desktop
    // and panels here; JOINED attaches this Runner to the existing Workstation.
    ShowWindow(g_host_window, SW_SHOWNORMAL);
    UpdateWindow(g_host_window);
    if (!D64WorkstationActivate(g_host_window)) {
        DestroyWindow(g_host_window);
        g_host_window = nullptr;
        D64WorkstationBeginLeave();
        D64WorkstationFinalizeLeave();
        return 5;
    }

    // The existing core guard keeps Win/Alt-Tab/etc. inside the Workstation.
    // Install our generic-app guard afterwards so Alt+F4 on a normal PE child
    // means "hide", matching the old d64qt5 Stage-128 semantics.
    if (!D64WorkstationInstallKeyboardGuard(g_host_window) ||
        !install_mouse_guard() ||
        !install_keyboard_guard()) {
        begin_leave_once();
        DestroyWindow(g_host_window);
        g_host_window = nullptr;
        D64WorkstationFinalizeLeave();
        return 6;
    }

    // The host window is infrastructure only. The Workstation panels remain
    // visible. Requests may now arrive either from the CLI or the legacy pipe.
    ShowWindow(g_host_window, SW_HIDE);
    SetTimer(g_host_window, RUNNER_TIMER, 500, nullptr);

    g_pipe_stop.store(false);
    g_pipe_thread = std::thread(&pipe_server_loop);

    int resultCode = 0;
    if (hasStartupRequest && !launch_program(startupRequest)) {
        MessageBoxW(
            nullptr,
            L"Die angegebene Anwendung konnte nicht auf der Workstation gestartet werden.",
            L"Workstation Mode",
            MB_OK | MB_ICONERROR | MB_SETFOREGROUND
        );
        resultCode = 7;
        PostMessageW(g_host_window, WM_RUNNER_EXIT, 0, 0);
    }

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    begin_leave_once();
    if (g_host_window && IsWindow(g_host_window)) {
        KillTimer(g_host_window, RUNNER_TIMER);
        DestroyWindow(g_host_window);
    }
    g_host_window = nullptr;
    D64WorkstationFinalizeLeave();
    return resultCode;
}

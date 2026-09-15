#define _UNICODE
#include <windows.h>
#include <shellapi.h>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <cwctype>
#include <cstdint>
#include <cwchar>

namespace {

const DWORD kPollMs = 500;
const ULONGLONG kStartupGraceMs = 30000;
const ULONGLONG kHeartbeatStaleMs = 15000;
const DWORD kUserTerminateCode = 0xE0000001u;
const wchar_t *kLauncherMutexName = L"Global\\d64_dism.start.launcher.v1";
const DWORD kLaunchGuardVersion = 0x00010001u;

class ScopedHandle {
public:
    ScopedHandle() : handle_(nullptr) {}
    explicit ScopedHandle(HANDLE handle) : handle_(handle) {}
    ~ScopedHandle() { reset(); }
    ScopedHandle(const ScopedHandle &) = delete;
    ScopedHandle &operator=(const ScopedHandle &) = delete;
    HANDLE get() const { return handle_; }
    HANDLE release() { HANDLE h = handle_; handle_ = nullptr; return h; }
    void reset(HANDLE handle = nullptr) {
        if (handle_ && handle_ != INVALID_HANDLE_VALUE) CloseHandle(handle_);
        handle_ = handle;
    }
    explicit operator bool() const { return handle_ && handle_ != INVALID_HANDLE_VALUE; }
private:
    HANDLE handle_;
};

struct LaunchGuardBlock {
    DWORD version;
    DWORD launcherPid;
    wchar_t token[128];
};

std::wstring module_path() {
    std::vector<wchar_t> buffer(32768, L'\0');
    DWORD n = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!n || n >= buffer.size()) return L"";
    return std::wstring(buffer.data(), n);
}

std::wstring dirname_of(const std::wstring &path) {
    std::wstring::size_type pos = path.find_last_of(L"\\/");
    if (pos == std::wstring::npos) return L".";
    return path.substr(0, pos);
}

std::wstring join_path(const std::wstring &a, const std::wstring &b) {
    if (a.empty()) return b;
    wchar_t tail = a.back();
    if (tail == L'\\' || tail == L'/') return a + b;
    return a + L"\\" + b;
}

bool file_exists(const std::wstring &path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY);
}

bool dir_exists(const std::wstring &path) {
    DWORD attr = GetFileAttributesW(path.c_str());
    return attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY);
}

std::wstring quote_arg(const std::wstring &arg) {
    if (arg.empty()) return L"\"\"";
    if (arg.find_first_of(L" \t\n\v\"") == std::wstring::npos) return arg;
    std::wstring out = L"\"";
    unsigned backslashes = 0;
    for (wchar_t ch : arg) {
        if (ch == L'\\') {
            ++backslashes;
            continue;
        }
        if (ch == L'\"') {
            out.append(backslashes * 2 + 1, L'\\');
            out.push_back(L'\"');
            backslashes = 0;
            continue;
        }
        out.append(backslashes, L'\\');
        backslashes = 0;
        out.push_back(ch);
    }
    out.append(backslashes * 2, L'\\');
    out.push_back(L'\"');
    return out;
}

std::wstring get_env(const wchar_t *name) {
    DWORD needed = GetEnvironmentVariableW(name, nullptr, 0);
    if (!needed) return L"";
    std::vector<wchar_t> buf(needed + 1, L'\0');
    DWORD got = GetEnvironmentVariableW(name, buf.data(), static_cast<DWORD>(buf.size()));
    if (!got) return L"";
    return std::wstring(buf.data(), got);
}

std::wstring find_python() {
    std::wstring configured = get_env(L"D64_PYTHON");
    if (!configured.empty()) return configured;
    std::vector<wchar_t> buffer(32768, L'\0');
    DWORD n = SearchPathW(nullptr, L"python.exe", nullptr,
                          static_cast<DWORD>(buffer.size()), buffer.data(), nullptr);
    if (n && n < buffer.size()) return std::wstring(buffer.data(), n);
    n = SearchPathW(nullptr, L"py.exe", nullptr,
                    static_cast<DWORD>(buffer.size()), buffer.data(), nullptr);
    if (n && n < buffer.size()) return std::wstring(buffer.data(), n);
    return L"python.exe";
}

std::wstring hex_code(DWORD value) {
    std::wostringstream out;
    out << L"0x" << std::uppercase << std::hex << std::setw(8) << std::setfill(L'0') << value;
    return out.str();
}

std::wstring classify_exit_code(DWORD code) {
    switch (code) {
        case 0xC0000005u: return L"Access Violation (ungueltiger Speicherzugriff)";
        case 0xC00000FDu: return L"Stack Overflow";
        case 0xC000001Du: return L"Illegal Instruction";
        case 0xC0000094u: return L"Integer Division durch Null";
        case 0xC0000409u: return L"Stack Buffer Overrun / Fast Fail";
        case 0xC0000374u: return L"Heap Corruption";
        case 0xC0000135u: return L"Abhaengige DLL nicht gefunden";
        case 0x40000015u: return L"Fatal Application Exit";
        case kUserTerminateCode: return L"Vom Benutzer nach Watchdog-Warnung beendet";
        default:
            if ((code & 0xC0000000u) == 0xC0000000u)
                return L"Unbehandelte native Windows-Exception";
            return L"Unerwarteter Prozessabbruch";
    }
}

bool read_file_text(const std::wstring &path, std::wstring &out) {
    HANDLE h = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                           nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (h == INVALID_HANDLE_VALUE) return false;
    LARGE_INTEGER size{};
    if (!GetFileSizeEx(h, &size) || size.QuadPart < 0 || size.QuadPart > 1024 * 1024) {
        CloseHandle(h);
        return false;
    }
    std::vector<char> bytes(static_cast<size_t>(size.QuadPart) + 1, '\0');
    DWORD got = 0;
    BOOL ok = ReadFile(h, bytes.data(), static_cast<DWORD>(size.QuadPart), &got, nullptr);
    CloseHandle(h);
    if (!ok) return false;
    int count = MultiByteToWideChar(CP_UTF8, 0, bytes.data(), static_cast<int>(got), nullptr, 0);
    if (count <= 0) return false;
    std::vector<wchar_t> wide(static_cast<size_t>(count) + 1, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, bytes.data(), static_cast<int>(got), wide.data(), count);
    out.assign(wide.data(), count);
    return true;
}

bool heartbeat_age_ms(const std::wstring &path, ULONGLONG &ageMs) {
    WIN32_FILE_ATTRIBUTE_DATA fad{};
    if (!GetFileAttributesExW(path.c_str(), GetFileExInfoStandard, &fad)) return false;
    ULARGE_INTEGER modified{};
    modified.LowPart = fad.ftLastWriteTime.dwLowDateTime;
    modified.HighPart = fad.ftLastWriteTime.dwHighDateTime;
    FILETIME nowFt{};
    GetSystemTimeAsFileTime(&nowFt);
    ULARGE_INTEGER now{};
    now.LowPart = nowFt.dwLowDateTime;
    now.HighPart = nowFt.dwHighDateTime;
    if (now.QuadPart < modified.QuadPart) {
        ageMs = 0;
        return true;
    }
    ageMs = (now.QuadPart - modified.QuadPart) / 10000ull;
    return true;
}

std::wstring make_watchdog_dir() {
    std::vector<wchar_t> temp(MAX_PATH + 2, L'\0');
    DWORD n = GetTempPathW(static_cast<DWORD>(temp.size()), temp.data());
    std::wstring base = (n && n < temp.size()) ? std::wstring(temp.data(), n) : L".\\";
    std::wostringstream name;
    name << L"d64_dism_watchdog_" << GetCurrentProcessId() << L"_" << GetTickCount64();
    std::wstring path = join_path(base, name.str());
    CreateDirectoryW(path.c_str(), nullptr);
    return path;
}

void cleanup_watchdog_dir(const std::wstring &dir) {
    const wchar_t *names[] = {L"heartbeat.txt", L"status.txt", L"app.pid", L"exception.txt"};
    for (const wchar_t *name : names) DeleteFileW(join_path(dir, name).c_str());
    RemoveDirectoryW(dir.c_str());
}

std::wstring make_token() {
    LARGE_INTEGER counter{};
    QueryPerformanceCounter(&counter);
    std::wostringstream out;
    out << GetCurrentProcessId() << L"-" << GetTickCount64() << L"-" << counter.QuadPart;
    return out.str();
}

bool create_launch_guard(const std::wstring &token, ScopedHandle &mapping, std::wstring &error) {
    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    HANDLE raw = CreateFileMappingW(
        INVALID_HANDLE_VALUE, &sa, PAGE_READWRITE, 0,
        static_cast<DWORD>(sizeof(LaunchGuardBlock)), nullptr
    );
    if (!raw) {
        error = L"Der Launcher-Startschutz konnte nicht angelegt werden. Win32-Fehler: "
              + std::to_wstring(GetLastError());
        return false;
    }
    mapping.reset(raw);

    auto *view = static_cast<LaunchGuardBlock *>(MapViewOfFile(
        mapping.get(), FILE_MAP_WRITE, 0, 0, sizeof(LaunchGuardBlock)
    ));
    if (!view) {
        error = L"Der Launcher-Startschutz konnte nicht beschrieben werden. Win32-Fehler: "
              + std::to_wstring(GetLastError());
        mapping.reset();
        return false;
    }
    ZeroMemory(view, sizeof(*view));
    view->version = kLaunchGuardVersion;
    view->launcherPid = GetCurrentProcessId();
    wcsncpy(view->token, token.c_str(), (sizeof(view->token) / sizeof(view->token[0])) - 1);
    view->token[(sizeof(view->token) / sizeof(view->token[0])) - 1] = L'\0';
    UnmapViewOfFile(view);
    return true;
}

std::wstring handle_as_decimal(HANDLE handle) {
    std::wostringstream out;
    out << static_cast<unsigned long long>(reinterpret_cast<uintptr_t>(handle));
    return out.str();
}

struct Target {
    std::wstring executable;
    std::vector<std::wstring> prefixArgs;
    std::wstring appDir;
    std::wstring description;
};

struct LaunchOptions {
    bool console = false;
    std::wstring explicitApp;
    std::vector<std::wstring> passThrough;
};

bool env_truthy(const wchar_t *name) {
    std::wstring value = get_env(name);
    std::transform(value.begin(), value.end(), value.begin(),
                   [](wchar_t ch) { return static_cast<wchar_t>(towlower(ch)); });
    return value == L"1" || value == L"true" || value == L"yes" || value == L"on";
}

bool parse_options(int argc, wchar_t **argv, LaunchOptions &options, std::wstring &error) {
    options.console = env_truthy(L"D64_LAUNCHER_CONSOLE");
    bool passthroughOnly = false;
    for (int i = 1; i < argc; ++i) {
        std::wstring arg = argv[i];
        if (passthroughOnly) {
            options.passThrough.push_back(arg);
            continue;
        }
        if (arg == L"--") {
            passthroughOnly = true;
        } else if (arg == L"--console") {
            options.console = true;
        } else if (arg == L"--no-console") {
            options.console = false;
        } else if (arg == L"--app") {
            if (i + 1 >= argc) {
                error = L"Nach --app fehlt der Anwendungspfad.";
                return false;
            }
            options.explicitApp = argv[++i];
        } else {
            options.passThrough.push_back(arg);
        }
    }
    return true;
}

bool enable_console_if_requested(bool requested) {
    if (!requested) return false;
    if (!AttachConsole(ATTACH_PARENT_PROCESS)) {
        DWORD error = GetLastError();
        if (error != ERROR_ACCESS_DENIED && !AllocConsole()) return false;
    }
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    return true;
}

struct ChildIoHandles {
    HANDLE input = INVALID_HANDLE_VALUE;
    HANDLE output = INVALID_HANDLE_VALUE;
};

void close_child_io(ChildIoHandles &io) {
    if (io.input != INVALID_HANDLE_VALUE && io.input != nullptr) CloseHandle(io.input);
    if (io.output != INVALID_HANDLE_VALUE && io.output != nullptr) CloseHandle(io.output);
    io.input = INVALID_HANDLE_VALUE;
    io.output = INVALID_HANDLE_VALUE;
}

bool prepare_hidden_child_io(const std::wstring &appDir, STARTUPINFOW &si, ChildIoHandles &io) {
    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    io.input = CreateFileW(L"NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
                           &sa, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);

    std::wstring logPath = join_path(appDir, L"d64_dism_console.log");
    io.output = CreateFileW(logPath.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                            &sa, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (io.output == INVALID_HANDLE_VALUE) {
        io.output = CreateFileW(L"NUL", GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                                &sa, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    }

    if (io.input == INVALID_HANDLE_VALUE || io.output == INVALID_HANDLE_VALUE) {
        close_child_io(io);
        return false;
    }

    si.dwFlags |= STARTF_USESTDHANDLES;
    si.hStdInput = io.input;
    si.hStdOutput = io.output;
    si.hStdError = io.output;
    return true;
}

bool resolve_target(const LaunchOptions &options, Target &target, std::wstring &error) {
    std::wstring launcherDir = dirname_of(module_path());
    if (!options.explicitApp.empty()) {
        std::wstring requested = options.explicitApp;
        if (!file_exists(requested)) {
            error = L"Die mit --app angegebene Anwendung wurde nicht gefunden:\n" + requested;
            return false;
        }
        target.appDir = dirname_of(requested);
        if (requested.size() >= 3 && requested.substr(requested.size() - 3) == L".py") {
            target.executable = find_python();
            target.prefixArgs.push_back(requested);
            target.description = requested;
        } else {
            target.executable = requested;
            target.description = requested;
        }
        return true;
    }

    std::wstring exe = join_path(launcherDir, L"d64_dism.exe");
    if (file_exists(exe)) {
        target.executable = exe;
        target.appDir = launcherDir;
        target.description = exe;
        return true;
    }
    std::wstring script = join_path(launcherDir, L"d64_dism.py");
    if (file_exists(script)) {
        target.executable = find_python();
        target.prefixArgs.push_back(script);
        target.appDir = launcherDir;
        target.description = script;
        return true;
    }
    error = L"Weder d64_dism.exe noch d64_dism.py wurden neben dem Launcher gefunden.\n\n"
            L"Alternativ: d64_dism_launcher.exe --app <Pfad> [--console] [--] [Argumente]";
    return false;
}

std::wstring build_command_line(const Target &target, const LaunchOptions &options) {
    std::wstring cmd = quote_arg(target.executable);
    for (const auto &arg : target.prefixArgs) {
        cmd += L" ";
        cmd += quote_arg(arg);
    }
    for (const auto &arg : options.passThrough) {
        cmd += L" ";
        cmd += quote_arg(arg);
    }
    return cmd;
}

void show_start_error(const std::wstring &text) {
    MessageBoxW(nullptr, text.c_str(), L"d64_dism Launcher", MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND);
}

void show_crash_dialog(DWORD exitCode, const std::wstring &status,
                       const std::wstring &watchdogDir, const std::wstring &appDir) {
    std::wostringstream text;
    text << L"d64_dism wurde unerwartet beendet.\n\n"
         << classify_exit_code(exitCode) << L"\n"
         << L"Exit-/Exception-Code: " << hex_code(exitCode) << L"\n\n";
    if (!status.empty()) text << L"Letzter Watchdog-Status:\n" << status << L"\n";
    text << L"Crash-Log:\n" << join_path(appDir, L"d64_dism_crash.log") << L"\n\n"
         << L"Watchdog-Daten:\n" << watchdogDir << L"\n\n"
         << L"Die Anwendung kann nicht sicher fortgesetzt werden.";
    MessageBoxW(nullptr, text.str().c_str(), L"d64_dism - Schwerer Fehler",
                MB_OK | MB_ICONERROR | MB_TOPMOST | MB_SETFOREGROUND);
}

} // namespace

int WINAPI wWinMain(HINSTANCE, HINSTANCE, LPWSTR, int) {
    // Stage 155: genau eine start.exe-Instanz auf dem gesamten Windows-System.
    // Der Global\-Namespace gilt auch über Terminal-Services-Sessions hinweg.
    SECURITY_ATTRIBUTES mutexSa{};
    mutexSa.nLength = sizeof(mutexSa);
    mutexSa.bInheritHandle = TRUE;
    ScopedHandle launcherMutex(CreateMutexW(&mutexSa, FALSE, kLauncherMutexName));
    if (!launcherMutex) {
        std::wostringstream msg;
        msg << L"Der globale Launcher-Mutex konnte nicht erzeugt werden.\n\nWin32-Fehler: "
            << GetLastError();
        show_start_error(msg.str());
        return 10;
    }
    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        MessageBoxW(
            nullptr,
            L"d64_dism wurde bereits über start.exe gestartet.\n"
            L"Eine zweite Launcher-Instanz ist nicht zulässig.",
            L"d64_dism Launcher",
            MB_OK | MB_ICONINFORMATION | MB_TOPMOST | MB_SETFOREGROUND
        );
        return 11;
    }

    int argc = 0;
    LPWSTR *argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (!argv) {
        show_start_error(L"CommandLineToArgvW ist fehlgeschlagen.");
        return 2;
    }

    LaunchOptions options;
    Target target;
    std::wstring error;
    if (!parse_options(argc, argv, options, error) || !resolve_target(options, target, error)) {
        show_start_error(error);
        LocalFree(argv);
        return 2;
    }

    const bool consoleAttached = enable_console_if_requested(options.console);
    if (options.console && !consoleAttached) {
        MessageBoxW(nullptr,
                    L"Die angeforderte Diagnosekonsole konnte nicht bereitgestellt werden.\n"
                    L"Die Anwendung wird dennoch gestartet.",
                    L"d64_dism Launcher", MB_OK | MB_ICONWARNING | MB_TOPMOST);
    }

    std::wstring watchdogDir = make_watchdog_dir();
    std::wstring token = make_token();
    std::wstring parentPid = std::to_wstring(GetCurrentProcessId());
    ScopedHandle launchGuard;
    if (!create_launch_guard(token, launchGuard, error)) {
        show_start_error(error);
        LocalFree(argv);
        cleanup_watchdog_dir(watchdogDir);
        return 12;
    }
    std::wstring guardHandle = handle_as_decimal(launchGuard.get());
    SetEnvironmentVariableW(L"D64_WATCHDOG_DIR", watchdogDir.c_str());
    SetEnvironmentVariableW(L"D64_WATCHDOG_TOKEN", token.c_str());
    SetEnvironmentVariableW(L"D64_LAUNCHER_PID", parentPid.c_str());
    SetEnvironmentVariableW(L"D64_LAUNCHED_BY_WATCHDOG", L"1");
    SetEnvironmentVariableW(L"D64_LAUNCH_GUARD_HANDLE", guardHandle.c_str());
    SetEnvironmentVariableW(L"D64_LAUNCH_GUARD_TOKEN", token.c_str());

    std::wstring commandLine = build_command_line(target, options);
    LocalFree(argv);
    std::vector<wchar_t> mutableCommand(commandLine.begin(), commandLine.end());
    mutableCommand.push_back(L'\0');

    STARTUPINFOW si{};
    si.cb = sizeof(si);
    PROCESS_INFORMATION pi{};
    DWORD creationFlags = CREATE_UNICODE_ENVIRONMENT;
    // Stage 155: der anonyme Launch-Guard-Handle muss an d64_dism.exe vererbt werden.
    BOOL inheritHandles = TRUE;
    ChildIoHandles childIo;

    // Stage 140: Der Launcher und ein eventuell gestartetes python.exe bleiben
    // standardmaessig ohne sichtbare Konsole. Nur --console bzw.
    // D64_LAUNCHER_CONSOLE=1 hebt dieses Verhalten fuer Diagnoseausgaben auf.
    // Im versteckten Modus gehen stdout/stderr nicht verloren, sondern nach
    // d64_dism_console.log neben der Anwendung.
    if (!options.console) {
        creationFlags |= CREATE_NO_WINDOW;
        if (prepare_hidden_child_io(target.appDir, si, childIo)) inheritHandles = TRUE;
    }

    BOOL started = CreateProcessW(
        nullptr,
        mutableCommand.data(),
        nullptr,
        nullptr,
        inheritHandles,
        creationFlags,
        nullptr,
        target.appDir.c_str(),
        &si,
        &pi
    );
    DWORD createError = started ? ERROR_SUCCESS : GetLastError();
    close_child_io(childIo);
    if (!started) {
        DWORD err = createError;
        std::wostringstream msg;
        msg << L"Die Anwendung konnte nicht gestartet werden.\n\n"
            << target.description << L"\n\nWin32-Fehler: " << err;
        show_start_error(msg.str());
        cleanup_watchdog_dir(watchdogDir);
        return 3;
    }

    CloseHandle(pi.hThread);
    const ULONGLONG startTick = GetTickCount64();
    std::wstring heartbeatPath = join_path(watchdogDir, L"heartbeat.txt");
    std::wstring statusPath = join_path(watchdogDir, L"status.txt");
    bool heartbeatSeen = false;
    bool stallWarned = false;
    bool stallIgnored = false;
    bool userTerminated = false;

    for (;;) {
        DWORD wait = WaitForSingleObject(pi.hProcess, kPollMs);
        if (wait == WAIT_OBJECT_0) break;
        if (wait == WAIT_FAILED) break;

        ULONGLONG age = 0;
        if (heartbeat_age_ms(heartbeatPath, age)) {
            heartbeatSeen = true;
            if (age < 3000) {
                stallWarned = false;
                stallIgnored = false;
            }
            if (age > kHeartbeatStaleMs && !stallWarned && !stallIgnored) {
                stallWarned = true;
                std::wostringstream message;
                message << L"d64_dism reagiert seit etwa " << (age / 1000) << L" Sekunden nicht mehr.\n\n"
                        << L"Der externe Watchdog laeuft weiterhin.\n\n"
                        << L"Abbrechen = Anwendung hart beenden\n"
                        << L"Wiederholen = weiter warten und spaeter erneut warnen\n"
                        << L"Ignorieren = bis zur naechsten Erholung nicht mehr warnen";
                int choice = MessageBoxW(nullptr, message.str().c_str(),
                                         L"d64_dism - Watchdog",
                                         MB_ABORTRETRYIGNORE | MB_ICONWARNING | MB_TOPMOST | MB_SETFOREGROUND);
                if (choice == IDABORT) {
                    userTerminated = true;
                    TerminateProcess(pi.hProcess, kUserTerminateCode);
                    WaitForSingleObject(pi.hProcess, 5000);
                    break;
                }
                if (choice == IDIGNORE) {
                    stallIgnored = true;
                } else {
                    stallWarned = false;
                }
            }
        } else if (!heartbeatSeen && (GetTickCount64() - startTick) > kStartupGraceMs) {
            // Kein Heartbeat nach der Startphase: einmalig warnen. Das deckt auch
            // Fehler vor der QApplication-/Hauptfenster-Initialisierung ab.
            if (!stallWarned && !stallIgnored) {
                stallWarned = true;
                int choice = MessageBoxW(nullptr,
                    L"d64_dism hat innerhalb von 30 Sekunden keinen Watchdog-Heartbeat erzeugt.\n\n"
                    L"Abbrechen = Anwendung beenden\nWiederholen = weiter warten\nIgnorieren = nicht erneut warnen",
                    L"d64_dism - Watchdog",
                    MB_ABORTRETRYIGNORE | MB_ICONWARNING | MB_TOPMOST | MB_SETFOREGROUND);
                if (choice == IDABORT) {
                    userTerminated = true;
                    TerminateProcess(pi.hProcess, kUserTerminateCode);
                    WaitForSingleObject(pi.hProcess, 5000);
                    break;
                }
                if (choice == IDIGNORE) stallIgnored = true;
                else stallWarned = false;
            }
        }
    }

    DWORD exitCode = 0;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    CloseHandle(pi.hProcess);

    std::wstring status;
    read_file_text(statusPath, status);
    // Exitcode 0 gilt immer als sauber. Das vermeidet Fehlalarme fuer CLI-Aufrufe
    // oder sehr fruehe, aber regulaere Beendigungen noch vor dem ersten Heartbeat.
    const bool clean = (exitCode == 0);

    if (clean) {
        cleanup_watchdog_dir(watchdogDir);
        return 0;
    }
    if (!userTerminated) {
        show_crash_dialog(exitCode, status, watchdogDir, target.appDir);
    }
    return static_cast<int>(exitCode ? exitCode : 1);
}

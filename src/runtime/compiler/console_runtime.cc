// Stage 551 - one process-wide console service for generated Pascal PE32/PE32+.
// The DLL has its own state; generated modules do not own console buffers.
// Build with MSYS2 MinGW32/MinGW64 (normal Windows headers and CRT).
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cstdint>

namespace {
struct ConsoleState {
    HANDLE output = INVALID_HANDLE_VALUE;
    HANDLE input  = INVALID_HANDLE_VALUE;
    CONSOLE_SCREEN_BUFFER_INFO original = {};
    DWORD original_mode = 0;
    bool have_original = false;
    bool have_mode = false;
    bool created_console = false;
};

ConsoleState state;
volatile LONG init_state = 0;   // 0: not initialized; 1: initializing; 2: ready

bool valid(HANDLE h) { return h && h != INVALID_HANDLE_VALUE; }

bool borrow_output() {
    if (!valid(state.output)) state.output = GetStdHandle(STD_OUTPUT_HANDLE);
    if (!valid(state.input))  state.input = GetStdHandle(STD_INPUT_HANDLE);
    return valid(state.output);
}

void write_bytes(const char* text, DWORD length) {
    if (!text || !length) return;
    if (!borrow_output()) return;  // DLLs must not allocate a console implicitly.
    while (length) {
        DWORD written = 0;
        if (!WriteFile(state.output, text, length, &written, nullptr) || !written) break;
        text += written;
        length -= written;
    }
}

// Read and discard the remainder of an overlong line, never write beyond size.
DWORD read_line(char* output, DWORD size) {
    if (!output || !size) return 0;
    output[0] = '\0';
    if (!valid(state.input)) state.input = GetStdHandle(STD_INPUT_HANDLE);
    if (!valid(state.input)) return 0;
    DWORD n = 0;
    for (;;) {
        char ch = 0;
        DWORD got = 0;
        if (!ReadFile(state.input, &ch, 1, &got, nullptr) || !got) break;
        if (ch == '\n') break;
        if (ch == '\r') continue;
        if (n + 1 < size) output[n++] = ch;
    }
    output[n] = '\0';
    return n;
}
}

extern "C" {

__declspec(dllexport) int __cdecl d64_console_init() {
    LONG was = InterlockedCompareExchange(&init_state, 1, 0);
    if (was == 2) return borrow_output() ? 1 : 0;
    if (was == 1) {
        while (InterlockedCompareExchange(&init_state, 2, 2) == 1) Sleep(0);
        return borrow_output() ? 1 : 0;
    }
    // Do not change a host-provided console's size or ownership.
    if (!GetConsoleWindow()) {
        if (AllocConsole()) state.created_console = true;
    }
    borrow_output();
    if (valid(state.output)) {
        state.have_original = GetConsoleScreenBufferInfo(state.output, &state.original) != 0;
        state.have_mode = GetConsoleMode(state.output, &state.original_mode) != 0;
        if (state.have_mode) {
            SetConsoleMode(state.output, state.original_mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
        }
        if (state.created_console) {
            SMALL_RECT rect = {0, 0, 79, 24};
            SetConsoleWindowInfo(state.output, TRUE, &rect);
            COORD buffer_size = {80, 25};
            SetConsoleScreenBufferSize(state.output, buffer_size);
        }
    }
    InterlockedExchange(&init_state, 2);
    return valid(state.output) ? 1 : 0;
}

__declspec(dllexport) void __cdecl d64_console_restore() {
    if (InterlockedCompareExchange(&init_state, 1, 2) != 2) return;
    if (valid(state.output)) {
        if (state.have_mode) SetConsoleMode(state.output, state.original_mode);
        if (state.have_original && !state.created_console) {
            // Existing console was not resized, so only mode needs restoring.
        }
    }
    if (state.created_console) FreeConsole();
    state = ConsoleState{};
    InterlockedExchange(&init_state, 0);
}

__declspec(dllexport) void __cdecl d64_console_write_text(const char* text) {
    if (text) write_bytes(text, static_cast<DWORD>(std::strlen(text)));
}
__declspec(dllexport) void __cdecl d64_console_write_int(int value) {
    char text[32];
    const int n = std::snprintf(text, sizeof(text), "%d", value);
    if (n > 0) write_bytes(text, static_cast<DWORD>(n < 32 ? n : 31));
}
__declspec(dllexport) void __cdecl d64_console_write_double(double value) {
    char text[96];
    const int n = std::snprintf(text, sizeof(text), "%.15g", value);
    if (n > 0) write_bytes(text, static_cast<DWORD>(n < 96 ? n : 95));
}
__declspec(dllexport) void __cdecl d64_console_write_char(int value) {
    const char c = static_cast<char>(value);
    write_bytes(&c, 1); // Handles NUL without strlen truncation.
}
__declspec(dllexport) void __cdecl d64_console_newline() {
    write_bytes("\r\n", 2);
}
__declspec(dllexport) void __cdecl d64_console_clear() {
    write_bytes("\033[2J\033[H", 7);
}
__declspec(dllexport) unsigned __cdecl d64_console_read_line(char* text, unsigned capacity) {
    return read_line(text, capacity);
}
__declspec(dllexport) int __cdecl d64_console_read_int() {
    char text[128];
    read_line(text, sizeof(text));
    const char* p = text;
    while (*p == ' ' || *p == '\t') ++p;
    bool negative = false;
    if (*p == '-' || *p == '+') { negative = (*p == '-'); ++p; }
    const unsigned limit = negative ? 2147483648u : 2147483647u;
    unsigned result = 0;
    while (*p >= '0' && *p <= '9') {
        const unsigned digit = static_cast<unsigned>(*p - '0');
        if (result > (limit - digit) / 10u) {
            result = limit;  // Defined saturation for out-of-range input.
            break;
        }
        result = result * 10u + digit;
        ++p;
    }
    if (negative && result == 2147483648u) return (-2147483647 - 1);
    return negative ? -static_cast<int>(result) : static_cast<int>(result);
}
// Allocate through the existing libd64_runtime allocator; callers must free
// with _jit_free (and can transfer ownership to a Pascal String variable).
__declspec(dllexport) char* __cdecl d64_console_read_string() {
    using Alloc = void* (__cdecl*)(unsigned);
    HMODULE runtime = GetModuleHandleA("libd64_runtime.dll");
    if (!runtime) return nullptr;
    auto alloc = reinterpret_cast<Alloc>(GetProcAddress(runtime, "_jit_malloc"));
    if (!alloc) return nullptr;
    char* value = static_cast<char*>(alloc(1024));
    if (!value) return nullptr;
    read_line(value, 1024);
    return value;
}
}

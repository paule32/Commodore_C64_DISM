// ---------------------------------------------------------------------------
// File:   d64_workstation.cpp
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
#include "d64_workstation.h"

#ifdef _WIN32

#include <windows.h>
#include <cwchar>
#include <cwctype>
#include <cstdint>
#include <string>
#include <vector>

namespace {

HDESK g_original_thread_desktop  = nullptr;
HDESK g_original_input_desktop   = nullptr;
HDESK g_work_desktop             = nullptr;

HHOOK g_keyboard_hook            = nullptr;

HWND g_main_window               = nullptr;
HWND g_exit_window               = nullptr;
HWND g_bottom_panel_window       = nullptr;

ATOM g_exit_window_class         = 0;
ATOM g_bottom_panel_window_class = 0;

enum class PanelHotItem {
    None,
    Exit,
    Btx,
    Db
};
PanelHotItem g_panel_hover = PanelHotItem::None;

D64WorkstationCallback g_exit_callback = nullptr;
D64WorkstationBtxCallback g_btx_callback = nullptr;
D64WorkstationCallback g_db_callback = nullptr;
D64WorkstationCallback g_server_callback = nullptr;
D64WorkstationServerClientCallback g_server_client_callback = nullptr;

int g_server_client_count = 0;
int g_bottom_hover_client = -2; // -2 none, -1 server, >=0 SRV-PC n

std::vector<DWORD> g_workstation_child_pids;

bool g_workstation_active = false;   // GUI-Thread ist an der Workstation gebunden
bool g_workstation_visible = false;  // Workstation ist fuer diesen Prozess aktiv/sichtbar
bool g_leave_started = false;
bool g_workstation_owner = false;    // nur die erste Instanz besitzt Panel/Switch/Hook
bool g_workstation_joined = false;   // weitere Prozesse benutzen denselben Desktop

HANDLE g_workstation_mutex       = nullptr;
HANDLE g_workstation_ready_event = nullptr;
HANDLE g_application_mutex       = nullptr;

std::wstring g_application_path;
std::wstring g_application_mutex_name;
std::wstring g_application_window_property_name;

wchar_t g_desktop_name[128] = {0};
wchar_t g_original_input_name[128] = {0};

constexpr wchar_t WORKSTATION_MUTEX_NAME          [] = L"Global\\dBase2Many.D64Workstation.Singleton";
constexpr wchar_t WORKSTATION_READY_EVENT_NAME    [] = L"Global\\dBase2Many.D64Workstation.Ready";
constexpr wchar_t WORKSTATION_DESKTOP_NAME        [] = L"D64Workstation";
constexpr wchar_t APPLICATION_MUTEX_PREFIX        [] = L"Global\\dBase2Many.D64Application.";
constexpr wchar_t WORKSTATION_TOOL_WINDOW_PROPERTY[] = L"D64Workstation.ToolWindow";

ACCESS_MASK workstation_desktop_access()
{
    return
        DESKTOP_CREATEWINDOW  |
        DESKTOP_CREATEMENU    |
        DESKTOP_ENUMERATE     |
        DESKTOP_HOOKCONTROL   |
        DESKTOP_READOBJECTS   |
        DESKTOP_SWITCHDESKTOP |
        DESKTOP_WRITEOBJECTS;
}

void debug_last_error(const wchar_t *where);

UINT workstation_global_shutdown_message()
{
    static const UINT message = RegisterWindowMessageW(
        L"dBase2Many.D64Workstation.GlobalShutdown"
    );
    return message;
}

bool pid_in_list(const std::vector<DWORD> &pids, DWORD pid)
{
    for (DWORD value : pids) {
        if (value == pid)
            return true;
    }
    return false;
}

void append_unique_pid(std::vector<DWORD> &pids, DWORD pid)
{
    if (!pid || pid == GetCurrentProcessId() || pid_in_list(pids, pid))
        return;
    pids.push_back(pid);
}

std::wstring normalize_application_path(const wchar_t *path)
{
    if (!path || !*path)
        return std::wstring();

    wchar_t fullPath[32768] = {0};
    const DWORD length = GetFullPathNameW(
        path,
        static_cast<DWORD>(sizeof(fullPath) / sizeof(fullPath[0])),
        fullPath,
        nullptr
    );

    std::wstring result =
        (length > 0 && length < (sizeof(fullPath) / sizeof(fullPath[0])))
            ? std::wstring(fullPath, length)
            : std::wstring(path);

    for (wchar_t &ch : result) {
        if (ch == L'/')
            ch = L'\\';
        ch = static_cast<wchar_t>(std::towlower(ch));
    }
    return result;
}

std::wstring current_application_path()
{
    wchar_t buffer[32768] = {0};
    const DWORD length = GetModuleFileNameW(
        nullptr,
        buffer,
        static_cast<DWORD>(sizeof(buffer) / sizeof(buffer[0]))
    );
    if (!length || length >= (sizeof(buffer) / sizeof(buffer[0])))
        return std::wstring();
    return normalize_application_path(buffer);
}

std::uint64_t application_path_hash(const std::wstring &path)
{
    // 64-bit FNV-1a over the canonical lower-case UTF-16 path. The full path
    // intentionally distinguishes equally named applications in other dirs.
    std::uint64_t hash = 1469598103934665603ULL;
    for (wchar_t ch : path) {
        hash ^= static_cast<std::uint16_t>(ch);
        hash *= 1099511628211ULL;
    }
    return hash;
}

std::wstring application_object_name(
    const std::wstring &applicationPath,
    const wchar_t *suffix
)
{
    wchar_t hashText[32] = {0};
    std::swprintf(
        hashText,
        sizeof(hashText) / sizeof(hashText[0]),
        L"%016llX",
        static_cast<unsigned long long>(application_path_hash(applicationPath))
    );

    std::wstring name(APPLICATION_MUTEX_PREFIX);
    name += hashText;
    if (suffix && *suffix)
        name += suffix;
    return name;
}

std::wstring application_window_property_name(const std::wstring &applicationPath)
{
    wchar_t hashText[32] = {0};
    std::swprintf(
        hashText,
        sizeof(hashText) / sizeof(hashText[0]),
        L"%016llX",
        static_cast<unsigned long long>(application_path_hash(applicationPath))
    );
    std::wstring name = L"dBase2Many.D64ApplicationWindow.";
    name += hashText;
    return name;
}

struct ExistingApplicationWindowContext {
    const std::wstring *propertyName = nullptr;
    HWND visibleMain = nullptr;
    HWND hiddenMain = nullptr;
    DWORD processId = 0;
};

BOOL CALLBACK find_existing_application_window(HWND hwnd, LPARAM lParam)
{
    ExistingApplicationWindowContext *context =
        reinterpret_cast<ExistingApplicationWindowContext *>(lParam);
    if (!context || !context->propertyName || !IsWindow(hwnd))
        return TRUE;

    // Nur das von D64WorkstationActivate() markierte Hauptfenster zaehlt.
    // Login-/Warning-/Qt-Hilfsfenster besitzen diese Property bewusst nicht.
    if (!GetPropW(hwnd, context->propertyName->c_str()))
        return TRUE;

    DWORD processId = 0;
    GetWindowThreadProcessId(hwnd, &processId);
    context->processId = processId;

    if (IsWindowVisible(hwnd)) {
        context->visibleMain = hwnd;
        return FALSE;
    }
    if (!context->hiddenMain)
        context->hiddenMain = hwnd;
    return TRUE;
}

bool activate_existing_application_by_path(const std::wstring &applicationPath)
{
    if (applicationPath.empty())
        return false;

    const std::wstring propertyName =
        application_window_property_name(applicationPath);

    HDESK desktop = g_work_desktop;
    bool closeDesktop = false;
    if (!desktop) {
        desktop = OpenDesktopW(
            WORKSTATION_DESKTOP_NAME,
            0,
            FALSE,
            DESKTOP_ENUMERATE | DESKTOP_READOBJECTS | DESKTOP_WRITEOBJECTS
        );
        closeDesktop = desktop != nullptr;
    }
    if (!desktop)
        return false;

    ExistingApplicationWindowContext context;
    context.propertyName = &propertyName;
    EnumDesktopWindows(
        desktop,
        &find_existing_application_window,
        reinterpret_cast<LPARAM>(&context)
    );

    if (closeDesktop)
        CloseDesktop(desktop);

    HWND mainWindow = context.visibleMain ? context.visibleMain : context.hiddenMain;
    if (!mainWindow)
        return false;

    HWND target = GetLastActivePopup(mainWindow);
    if (!target || !IsWindow(target))
        target = mainWindow;

    if (context.processId)
        AllowSetForegroundWindow(context.processId);

    ShowWindowAsync(mainWindow, SW_RESTORE);
    ShowWindowAsync(mainWindow, SW_SHOW);
    if (target != mainWindow) {
        ShowWindowAsync(target, SW_RESTORE);
        ShowWindowAsync(target, SW_SHOW);
    }
    SetWindowPos(
        target,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    );
    BringWindowToTop(target);
    SetForegroundWindow(target);
    return true;
}

void mark_application_main_window(HWND mainWindow)
{
    if (!mainWindow || g_application_window_property_name.empty())
        return;
    SetPropW(
        mainWindow,
        g_application_window_property_name.c_str(),
        reinterpret_cast<HANDLE>(static_cast<ULONG_PTR>(1))
    );
}

void unmark_application_main_window()
{
    if (g_main_window && IsWindow(g_main_window) &&
        !g_application_window_property_name.empty()) {
        RemovePropW(g_main_window, g_application_window_property_name.c_str());
    }
}

void signal_application_ready()
{
    if (g_application_path.empty())
        return;
    const std::wstring eventName = application_object_name(
        g_application_path,
        L".InstanceReady"
    );
    HANDLE eventHandle = CreateEventW(nullptr, TRUE, FALSE, eventName.c_str());
    if (!eventHandle)
        return;
    SetEvent(eventHandle);
    CloseHandle(eventHandle);
}

bool acquire_application_instance()
{
    g_application_path = current_application_path();
    if (g_application_path.empty())
        return true;

    g_application_mutex_name = application_object_name(g_application_path, L"");
    g_application_window_property_name =
        application_window_property_name(g_application_path);
    g_application_mutex = CreateMutexW(
        nullptr,
        FALSE,
        g_application_mutex_name.c_str()
    );
    if (!g_application_mutex) {
        debug_last_error(L"CreateMutexW(application instance)");
        return false;
    }

    if (GetLastError() == ERROR_ALREADY_EXISTS) {
        CloseHandle(g_application_mutex);
        g_application_mutex = nullptr;
        activate_existing_application_by_path(g_application_path);
        SetLastError(ERROR_ALREADY_EXISTS);
        return false;
    }
    return true;
}

void release_application_instance()
{
    if (g_application_mutex) {
        CloseHandle(g_application_mutex);
        g_application_mutex = nullptr;
    }
    g_application_path.clear();
    g_application_mutex_name.clear();
    g_application_window_property_name.clear();
}

void close_kernel_handle(HANDLE &handle)
{
    if (!handle)
        return;
    CloseHandle(handle);
    handle = nullptr;
}

void release_singleton_state()
{
    if (g_workstation_owner && g_workstation_mutex) {
        ReleaseMutex(g_workstation_mutex);
    }
    close_kernel_handle(g_workstation_ready_event);
    close_kernel_handle(g_workstation_mutex);
    g_workstation_owner = false;
    g_workstation_joined = false;
}

bool acquire_singleton_role()
{
    g_workstation_mutex = CreateMutexW(
        nullptr,
        TRUE,
        WORKSTATION_MUTEX_NAME
    );
    if (!g_workstation_mutex) {
        debug_last_error(L"CreateMutexW(workstation singleton)");
        return false;
    }

    const DWORD createError = GetLastError();
    if (createError != ERROR_ALREADY_EXISTS) {
        g_workstation_owner = true;
        g_workstation_joined = false;
        return true;
    }

    // Initial ownership is ignored when CreateMutexW opens an existing mutex.
    // WAIT_TIMEOUT means another process still owns the Workstation lifetime.
    const DWORD wait = WaitForSingleObject(g_workstation_mutex, 0);
    if (wait == WAIT_TIMEOUT) {
        g_workstation_owner = false;
        g_workstation_joined = true;
        return true;
    }

    if (wait == WAIT_OBJECT_0 || wait == WAIT_ABANDONED) {
        // The previous owner ended between CreateMutexW and this test. We now
        // own the mutex and may safely become the new Workstation owner.
        g_workstation_owner = true;
        g_workstation_joined = false;
        return true;
    }

    debug_last_error(L"WaitForSingleObject(workstation singleton)");
    close_kernel_handle(g_workstation_mutex);
    return false;
}

bool prepare_ready_event()
{
    g_workstation_ready_event = CreateEventW(
        nullptr,
        TRUE,
        FALSE,
        WORKSTATION_READY_EVENT_NAME
    );
    if (!g_workstation_ready_event) {
        debug_last_error(L"CreateEventW(workstation ready)");
        return false;
    }

    if (g_workstation_owner) {
        ResetEvent(g_workstation_ready_event);
        return true;
    }

    const DWORD wait = WaitForSingleObject(g_workstation_ready_event, 10000);
    if (wait == WAIT_OBJECT_0)
        return true;

    // If the owner died while we were waiting, try to take over the mutex.
    const DWORD ownerWait = WaitForSingleObject(g_workstation_mutex, 0);
    if (ownerWait == WAIT_OBJECT_0 || ownerWait == WAIT_ABANDONED) {
        g_workstation_owner = true;
        g_workstation_joined = false;
        ResetEvent(g_workstation_ready_event);
        return true;
    }

    if (wait == WAIT_TIMEOUT)
        SetLastError(ERROR_TIMEOUT);
    debug_last_error(L"WaitForSingleObject(workstation ready)");
    return false;
}

bool key_is_down(int vk)
{
    return (GetAsyncKeyState(vk) & 0x8000) != 0;
}

void debug_last_error(const wchar_t *where)
{
    const DWORD error = GetLastError();
    wchar_t buffer[256] = {0};
    std::swprintf(
        buffer,
        sizeof(buffer) / sizeof(buffer[0]),
        L"d64qt5 workstation: %ls failed, GetLastError=%lu\n",
        where ? where : L"Win32 call",
        static_cast<unsigned long>(error)
    );
    OutputDebugStringW(buffer);
}

bool get_desktop_name(HDESK desktop, wchar_t *buffer, DWORD chars)
{
    if (!desktop || !buffer || chars == 0)
        return false;

    buffer[0] = L'\0';
    DWORD needed = 0;
    if (!GetUserObjectInformationW(
            desktop,
            UOI_NAME,
            buffer,
            chars * sizeof(wchar_t),
            &needed
        )) {
        buffer[0] = L'\0';
        return false;
    }
    return buffer[0] != L'\0';
}

bool current_thread_is_on_work_desktop()
{
    if (!g_work_desktop)
        return false;

    HDESK current = GetThreadDesktop(GetCurrentThreadId());
    if (!current)
        return false;

    wchar_t current_name[128] = {0};
    wchar_t work_name[128] = {0};

    if (!get_desktop_name(current, current_name, 128) ||
        !get_desktop_name(g_work_desktop, work_name, 128)) {
        // GetThreadDesktop liefert in der Regel denselben Desktop-Handle,
        // nachdem SetThreadDesktop erfolgreich war. Name-Vergleich ist aber
        // robuster, wenn Windows verschiedene Handles auf dasselbe Objekt gibt.
        return current == g_work_desktop;
    }

    return _wcsicmp(current_name, work_name) == 0;
}


const wchar_t *workstation_exit_class_name()
{
    return L"D64WorkstationPanel";
}

constexpr int WORKSTATION_PANEL_WIDTH =  76;
constexpr int WORKSTATION_EXIT_TOP    =   6;
constexpr int WORKSTATION_BTX_TOP     =  94;
constexpr int WORKSTATION_DB_TOP      = 182;
constexpr int WORKSTATION_ICON_LEFT   =  12;
constexpr int WORKSTATION_ICON_SIZE   =  52;
constexpr int WORKSTATION_BOTTOM_PANEL_HEIGHT = WORKSTATION_ICON_SIZE;
constexpr int WORKSTATION_PANEL_GAP   =   4;
constexpr int WORKSTATION_ITEM_HEIGHT =  86;

RECT panel_item_rect(int top)
{
    RECT rc = { 0, top, WORKSTATION_PANEL_WIDTH, top + WORKSTATION_ITEM_HEIGHT };
    return rc;
}

bool point_in_rect(const RECT &rc, LONG x, LONG y)
{
    return x >= rc.left && x < rc.right && y >= rc.top && y < rc.bottom;
}

PanelHotItem panel_item_at(LPARAM lParam)
{
    const LONG x = static_cast<SHORT>(LOWORD(lParam));
    const LONG y = static_cast<SHORT>(HIWORD(lParam));
    if (point_in_rect(panel_item_rect(0), x, y))
        return PanelHotItem::Exit;
    if (point_in_rect(panel_item_rect(WORKSTATION_BTX_TOP - WORKSTATION_EXIT_TOP), x, y))
        return PanelHotItem::Btx;
    if (point_in_rect(panel_item_rect(WORKSTATION_DB_TOP - WORKSTATION_EXIT_TOP), x, y))
        return PanelHotItem::Db;
    return PanelHotItem::None;
}

void draw_exit_symbol(HDC dc, const RECT &iconRect)
{
    HPEN xPen = CreatePen(PS_SOLID, 5, RGB(255, 255, 255));
    HGDIOBJ oldPen = SelectObject(dc, xPen);
    
    MoveToEx    (dc, iconRect.left + 14, iconRect.top + 14, nullptr);
    LineTo      (dc, iconRect.right - 14, iconRect.bottom - 14);
    MoveToEx    (dc, iconRect.right - 14, iconRect.top + 14, nullptr);
    LineTo      (dc, iconRect.left + 14, iconRect.bottom - 14);
    
    SelectObject(dc, oldPen);
    DeleteObject(xPen);
}

void draw_database_symbol(HDC dc, const RECT &iconRect)
{
    const int left   = iconRect.left   + 10;
    const int right  = iconRect.right  - 10;
    
    const int top    = iconRect.top    +  9;
    const int bottom = iconRect.bottom -  9;
    
    const int ellipseHeight = 12;

    HBRUSH bodyBrush = CreateSolidBrush(RGB(0, 128, 82));
    HPEN outlinePen  = CreatePen(PS_SOLID, 2, RGB(255, 255, 255));
    
    HGDIOBJ oldBrush = SelectObject(dc, bodyBrush);
    HGDIOBJ oldPen   = SelectObject(dc, outlinePen);

    Rectangle(dc, left, top + ellipseHeight / 2, right, bottom - ellipseHeight / 2);
    
    Ellipse(dc, left, top, right, top + ellipseHeight);
    Ellipse(dc, left, bottom - ellipseHeight, right, bottom);

    const int line1 = top + (bottom - top) / 2;
    const int line2 = top + (bottom - top) * 3 / 4;
    
    MoveToEx(dc, left  + 2, line1, nullptr);
    LineTo  (dc, right - 2, line1);
    MoveToEx(dc, left  + 2, line2, nullptr);
    LineTo  (dc, right - 2, line2);

    SelectObject(dc, oldPen);
    SelectObject(dc, oldBrush);
    
    DeleteObject(outlinePen);
    DeleteObject(bodyBrush);
}

HFONT create_panel_font(int pixelHeight, int weight)
{
    return CreateFontW(
        -pixelHeight,
        0, 0, 0,
        weight,
        FALSE, FALSE, FALSE,
        DEFAULT_CHARSET,
        OUT_DEFAULT_PRECIS,
        CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY,
        FIXED_PITCH | FF_MODERN,
        L"Consolas"
    );
}

void draw_panel_item(
    HDC dc,
    int top,
    PanelHotItem item,
    const wchar_t *text,
    COLORREF baseColor,
    COLORREF hoverColor,
    bool drawExit,
    bool drawDatabase)
{
    const bool hover = g_panel_hover == item;
    RECT iconRect = {
        WORKSTATION_ICON_LEFT,
        top,
        WORKSTATION_ICON_LEFT + WORKSTATION_ICON_SIZE,
        top + WORKSTATION_ICON_SIZE
    };

    HBRUSH iconBrush = CreateSolidBrush(hover ? hoverColor : baseColor);
    HPEN borderPen = CreatePen(PS_SOLID, 2, RGB(255, 255, 255));
    HGDIOBJ oldBrush = SelectObject(dc, iconBrush);
    HGDIOBJ oldPen = SelectObject(dc, borderPen);
    RoundRect(
        dc,
        iconRect.left,
        iconRect.top,
        iconRect.right,
        iconRect.bottom,
        10,
        10
    );

    if (drawExit) {
        draw_exit_symbol(dc, iconRect);
    } else if (drawDatabase) {
        draw_database_symbol(dc, iconRect);
    } else {
        SetTextColor(dc, RGB(255, 255, 255));
        SetBkMode(dc, TRANSPARENT);
        HFONT font = create_panel_font(16, FW_BOLD);
        HGDIOBJ oldFont = SelectObject(dc, font);
        DrawTextW(
            dc,
            text,
            -1,
            &iconRect,
            DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX
        );
        SelectObject(dc, oldFont);
        DeleteObject(font);
    }

    SelectObject(dc, oldPen);
    SelectObject(dc, oldBrush);
    DeleteObject(borderPen);
    DeleteObject(iconBrush);

    if (drawExit || drawDatabase) {
        RECT labelRect = {
            0,
            iconRect.bottom + 4,
            WORKSTATION_PANEL_WIDTH,
            iconRect.bottom + 25
        };
        SetTextColor(dc, RGB(255, 255, 255));
        SetBkMode(dc, TRANSPARENT);
        HFONT font = create_panel_font(14, FW_BOLD);
        HGDIOBJ oldFont = SelectObject(dc, font);
        DrawTextW(
            dc,
            drawExit ? L"EXIT" : L"DB",
            -1,
            &labelRect,
            DT_CENTER | DT_TOP | DT_SINGLELINE | DT_NOPREFIX
        );
        SelectObject(dc, oldFont);
        DeleteObject(font);
    }
}


const wchar_t *workstation_bottom_panel_class_name()
{
    return L"D64WorkstationBottomPanel";
}

int bottom_client_slot_width()
{
    return 112;
}

int bottom_item_at(LPARAM lParam)
{
    const LONG x = static_cast<SHORT>(LOWORD(lParam));
    const LONG y = static_cast<SHORT>(HIWORD(lParam));
    if (y < 0 || y >= WORKSTATION_BOTTOM_PANEL_HEIGHT)
        return -2;
    if (x >= 0 && x < WORKSTATION_PANEL_WIDTH)
        return -1; // SERVER

    const int start = WORKSTATION_PANEL_WIDTH + 4;
    if (x < start)
        return -2;
    const int index = (x - start) / bottom_client_slot_width();
    return (index >= 0 && index < g_server_client_count) ? index : -2;
}

void draw_bottom_button(HDC dc, const RECT &rc, const wchar_t *text, bool hover, COLORREF base)
{
    HBRUSH brush = CreateSolidBrush(hover ? RGB(65, 95, 155) : base);
    HPEN pen = CreatePen(PS_SOLID, 1, RGB(205, 205, 205));
    HGDIOBJ oldBrush = SelectObject(dc, brush);
    HGDIOBJ oldPen = SelectObject(dc, pen);
    RoundRect(dc, rc.left + 3, rc.top + 3, rc.right - 3, rc.bottom - 3, 8, 8);
    
    SelectObject(dc, oldPen);
    SelectObject(dc, oldBrush);
    
    DeleteObject(pen);
    DeleteObject(brush);

    SetTextColor(dc, RGB(255, 255, 255));
    SetBkMode(dc, TRANSPARENT);
    HFONT font = create_panel_font(13, FW_BOLD);
    HGDIOBJ oldFont = SelectObject(dc, font);
    RECT textRect = rc;
    DrawTextW(dc, text, -1, &textRect, DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX);
    
    SelectObject(dc, oldFont);
    DeleteObject(font);
}

LRESULT CALLBACK workstation_bottom_panel_proc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message) {
    case WM_NCHITTEST:
        return HTCLIENT;
    case WM_SETCURSOR:
        SetCursor(LoadCursorW(nullptr, IDC_HAND));
        return TRUE;
    case WM_MOUSEMOVE: {
        const int item = bottom_item_at(lParam);
        if (item != g_bottom_hover_client) {
            g_bottom_hover_client = item;
            InvalidateRect(hwnd, nullptr, FALSE);
        }
        TRACKMOUSEEVENT track;
        ZeroMemory(&track, sizeof(track));
        track.cbSize = sizeof(track);
        track.dwFlags = TME_LEAVE;
        track.hwndTrack = hwnd;
        TrackMouseEvent(&track);
        return 0;
    }
    case WM_MOUSELEAVE:
        g_bottom_hover_client = -2;
        InvalidateRect(hwnd, nullptr, FALSE);
        return 0;
    case WM_LBUTTONUP: {
        const int item = bottom_item_at(lParam);
        if (item == -1) {
            if (g_server_callback)
                g_server_callback();
        } else if (item >= 0 && g_server_client_callback) {
            g_server_client_callback(item);
        }
        return 0;
    }
    case WM_ERASEBKGND:
        return 1;
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC dc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);
        HBRUSH panelBrush = CreateSolidBrush(RGB(36, 36, 36));
        FillRect(dc, &rc, panelBrush);
        DeleteObject(panelBrush);

        RECT serverRect = {0, 0, WORKSTATION_PANEL_WIDTH, WORKSTATION_BOTTOM_PANEL_HEIGHT};
        draw_bottom_button(dc, serverRect, L"SERVER", g_bottom_hover_client == -1, RGB(95, 45, 120));

        const int start = WORKSTATION_PANEL_WIDTH + 4;
        for (int i = 0; i < g_server_client_count; ++i) {
            RECT itemRect = {
                start + i * bottom_client_slot_width(),
                0,
                start + (i + 1) * bottom_client_slot_width(),
                WORKSTATION_BOTTOM_PANEL_HEIGHT
            };
            wchar_t label[64] = {0};
            _snwprintf(label, 63, L"SRV-PC %d", i + 1);
            draw_bottom_button(dc, itemRect, label, g_bottom_hover_client == i, RGB(40, 75, 115));
        }
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_DESTROY:
        if (g_bottom_panel_window == hwnd)
            g_bottom_panel_window = nullptr;
        g_bottom_hover_client = -2;
        return 0;
    }
    return DefWindowProcW(hwnd, message, wParam, lParam);
}

bool register_bottom_panel_window_class()
{
    if (g_bottom_panel_window_class)
        return true;
    WNDCLASSEXW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.style = CS_DBLCLKS;
    wc.lpfnWndProc = workstation_bottom_panel_proc;
    wc.hInstance = GetModuleHandleW(nullptr);
    wc.hCursor = LoadCursorW(nullptr, IDC_HAND);
    wc.hbrBackground = nullptr;
    wc.lpszClassName = workstation_bottom_panel_class_name();
    g_bottom_panel_window_class = RegisterClassExW(&wc);
    if (!g_bottom_panel_window_class) {
        const DWORD error = GetLastError();
        if (error == ERROR_CLASS_ALREADY_EXISTS)
            return true;
        debug_last_error(L"RegisterClassExW(workstation bottom panel)");
        return false;
    }
    return true;
}

bool create_bottom_panel_window()
{
    if (g_bottom_panel_window && IsWindow(g_bottom_panel_window))
        return true;
    if (!register_bottom_panel_window_class())
        return false;
    const int width = GetSystemMetrics(SM_CXSCREEN);
    const int height = GetSystemMetrics(SM_CYSCREEN);
    g_bottom_panel_window = CreateWindowExW(
        WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
        workstation_bottom_panel_class_name(),
        L"D64 Workstation Server Panel",
        WS_POPUP,
        0,
        height - WORKSTATION_BOTTOM_PANEL_HEIGHT,
        width,
        WORKSTATION_BOTTOM_PANEL_HEIGHT,
        nullptr, nullptr, GetModuleHandleW(nullptr), nullptr
    );
    if (!g_bottom_panel_window) {
        debug_last_error(L"CreateWindowExW(workstation bottom panel)");
        return false;
    }
    ShowWindow(g_bottom_panel_window, SW_SHOWNOACTIVATE);
    UpdateWindow(g_bottom_panel_window);
    SetWindowPos(
        g_bottom_panel_window,
        HWND_TOPMOST,
        0,
        height - WORKSTATION_BOTTOM_PANEL_HEIGHT,
        width,
        WORKSTATION_BOTTOM_PANEL_HEIGHT,
        SWP_NOACTIVATE | SWP_SHOWWINDOW
    );
    return true;
}

void destroy_bottom_panel_window()
{
    if (g_bottom_panel_window && IsWindow(g_bottom_panel_window))
        DestroyWindow(g_bottom_panel_window);
    g_bottom_panel_window = nullptr;
    g_bottom_hover_client = -2;
    g_server_client_count = 0;
}

LRESULT CALLBACK workstation_exit_proc(
    HWND hwnd,
    UINT message,
    WPARAM wParam,
    LPARAM lParam
)
{
    switch (message) {
    case WM_NCHITTEST:
        return HTCLIENT;

    case WM_SETCURSOR:
        SetCursor(LoadCursorW(nullptr, IDC_HAND));
        return TRUE;

    case WM_MOUSEMOVE: {
        const PanelHotItem item = panel_item_at(lParam);
        if (item != g_panel_hover) {
            g_panel_hover = item;
            InvalidateRect(hwnd, nullptr, TRUE);
        }
        TRACKMOUSEEVENT track;
        ZeroMemory(&track, sizeof(track));
        track.cbSize = sizeof(track);
        track.dwFlags = TME_LEAVE;
        track.hwndTrack = hwnd;
        TrackMouseEvent(&track);
        return 0;
    }

    case WM_MOUSELEAVE:
        g_panel_hover = PanelHotItem::None;
        InvalidateRect(hwnd, nullptr, TRUE);
        return 0;

    case WM_LBUTTONUP: {
        const PanelHotItem item = panel_item_at(lParam);
        if (item == PanelHotItem::Exit && g_exit_callback) {
            // EXIT zeigt zuerst die JA/NEIN-Abfrage im Qt-Thread.
            g_exit_callback();
        } else if (item == PanelHotItem::Btx && g_btx_callback) {
            // BTX.exe wird im Qt-Thread gestartet, nicht direkt im WndProc.
            g_btx_callback();
        } else if (item == PanelHotItem::Db && g_db_callback) {
            // Das verborgene Hauptfenster wieder anzeigen.
            g_db_callback();
        }
        return 0;
    }

    case WM_LBUTTONDBLCLK:
        // Keine zweite Exit-Semantik. Ein einfacher Klick auf EXIT reicht und
        // ist durch die JA/NEIN-Abfrage gegen versehentliches Beenden geschuetzt.
        return 0;

    case WM_ERASEBKGND:
        return 1;

    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC dc = BeginPaint(hwnd, &ps);
        RECT rc;
        GetClientRect(hwnd, &rc);

        HBRUSH panelBrush = CreateSolidBrush(RGB(36, 36, 36));
        FillRect(dc, &rc, panelBrush);
        DeleteObject(panelBrush);
        SetBkMode(dc, TRANSPARENT);

        draw_panel_item(
            dc,
            WORKSTATION_EXIT_TOP,
            PanelHotItem::Exit,
            L"EXIT",
            RGB(180, 0, 0),
            RGB(220, 40, 40),
            true,
            false
        );
        draw_panel_item(
            dc,
            WORKSTATION_BTX_TOP,
            PanelHotItem::Btx,
            L"BTX",
            RGB(0, 70, 145),
            RGB(0, 105, 205),
            false,
            false
        );
        draw_panel_item(
            dc,
            WORKSTATION_DB_TOP,
            PanelHotItem::Db,
            L"DB",
            RGB(0, 105, 70),
            RGB(0, 155, 105),
            false,
            true
        );

        EndPaint(hwnd, &ps);
        return 0;
    }

    case WM_DESTROY:
        if (g_exit_window == hwnd)
            g_exit_window = nullptr;
        g_panel_hover = PanelHotItem::None;
        return 0;
    }

    return DefWindowProcW(hwnd, message, wParam, lParam);
}

bool register_exit_window_class()
{
    if (g_exit_window_class)
        return true;

    HINSTANCE instance = GetModuleHandleW(nullptr);

    WNDCLASSEXW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.style = CS_DBLCLKS;
    wc.lpfnWndProc = workstation_exit_proc;
    wc.hInstance = instance;
    wc.hCursor = LoadCursorW(nullptr, IDC_HAND);
    wc.hbrBackground = nullptr;
    wc.lpszClassName = workstation_exit_class_name();

    g_exit_window_class = RegisterClassExW(&wc);
    if (!g_exit_window_class) {
        const DWORD error = GetLastError();
        if (error == ERROR_CLASS_ALREADY_EXISTS)
            return true;
        debug_last_error(L"RegisterClassExW(workstation panel)");
        return false;
    }
    return true;
}

bool create_exit_window()
{
    if (g_exit_window && IsWindow(g_exit_window))
        return true;

    if (!register_exit_window_class())
        return false;

    const int screenHeight = GetSystemMetrics(SM_CYSCREEN);
    const int usableHeight = screenHeight - WORKSTATION_BOTTOM_PANEL_HEIGHT;
    const int panelHeight = usableHeight > 180 ? usableHeight : 180;

    g_exit_window = CreateWindowExW(
        WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE,
        workstation_exit_class_name(),
        L"D64 Workstation Panel",
        WS_POPUP,
        0,
        0,
        WORKSTATION_PANEL_WIDTH,
        panelHeight,
        nullptr,
        nullptr,
        GetModuleHandleW(nullptr),
        nullptr
    );

    if (!g_exit_window) {
        debug_last_error(L"CreateWindowExW(workstation panel)");
        return false;
    }

    ShowWindow(g_exit_window, SW_SHOWNOACTIVATE);
    UpdateWindow(g_exit_window);
    SetWindowPos(
        g_exit_window,
        HWND_TOPMOST,
        0,
        0,
        WORKSTATION_PANEL_WIDTH,
        panelHeight,
        SWP_NOACTIVATE | SWP_SHOWWINDOW
    );
    signal_application_ready();
    return true;
}

void destroy_exit_window()
{
    if (g_exit_window && IsWindow(g_exit_window))
        DestroyWindow(g_exit_window);
    g_exit_window = nullptr;
    g_panel_hover = PanelHotItem::None;
}

LRESULT CALLBACK workstation_keyboard_proc(
    int nCode,
    WPARAM wParam,
    LPARAM lParam
)
{
    if (nCode < 0) {
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);
    }

    if (wParam != WM_KEYDOWN && wParam != WM_SYSKEYDOWN) {
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);
    }

    const KBDLLHOOKSTRUCT *kbd =
        reinterpret_cast<const KBDLLHOOKSTRUCT *>(lParam);

    if (!kbd) {
        return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);
    }

    const DWORD vk = kbd->vkCode;
    const bool alt =
        ((kbd->flags & LLKHF_ALTDOWN) != 0) || key_is_down(VK_MENU);
    const bool ctrl = key_is_down(VK_CONTROL);
    const bool shift = key_is_down(VK_SHIFT);

    /*
     * Ctrl+Alt+Shift+F12 sendet nur WM_CLOSE an das Hauptfenster. Seit Stage
     * 128 versteckt ein normales WM_CLOSE das Hauptfenster lediglich; einen
     * echten Runtime-Shutdown darf nur der globale Workstation-EXIT ausloesen.
     */
    if (ctrl && alt && shift && vk == VK_F12) {
        if (g_main_window) {
            PostMessageW(g_main_window, WM_CLOSE, 0, 0);
        }
        return 1;
    }

    /* Windows-Tasten: blockiert u.a. Win+R, Win+D, Win+E, Win+X, Win+L. */
    if (vk == VK_LWIN || vk == VK_RWIN) {
        return 1;
    }

    if (alt && vk == VK_TAB) {
        return 1;
    }
    if (alt && vk == VK_ESCAPE) {
        return 1;
    }
    if (ctrl && !shift && vk == VK_ESCAPE) {
        return 1;
    }
    if (ctrl && shift && vk == VK_ESCAPE) {
        return 1;
    }

    /*
     * Stage 41: Alt+F4 ist keine Workstation-Aktion und darf insbesondere
     * keinen fokussierten Unterdialog isoliert schliessen. Der globale Guard
     * bestimmt deshalb das Root-Owner-Fenster der aktuell fokussierten
     * Anwendung und sendet WM_CLOSE ausschliesslich an dieses Hauptfenster.
     *
     * Beispiel:
     *   Fokus = QLineEdit im Login-Dialog
     *   GetForegroundWindow() = Login-Dialog
     *   GetAncestor(..., GA_ROOTOWNER) = dBase/BTX-Hauptfenster
     *   Alt+F4 -> WM_CLOSE an Hauptfenster
     *
     * Das Workstation-Panel selbst wird niemals per Alt+F4 geschlossen.
     */
    if (alt && vk == VK_F4) {
        HWND focusedWindow = GetForegroundWindow();
        if (!focusedWindow || !IsWindow(focusedWindow))
            return 1;

        HWND mainApplicationWindow =
            GetAncestor(focusedWindow, GA_ROOTOWNER);
        if (!mainApplicationWindow)
            mainApplicationWindow = focusedWindow;

        if (
            !IsWindow(mainApplicationWindow) ||
            mainApplicationWindow == g_exit_window ||
            mainApplicationWindow == g_bottom_panel_window ||
            GetPropW(mainApplicationWindow, WORKSTATION_TOOL_WINDOW_PROPERTY) != nullptr
        ) {
            return 1;
        }

        const LONG_PTR style =
            GetWindowLongPtrW(mainApplicationWindow, GWL_STYLE);
        if ((style & WS_CHILD) != 0)
            return 1;

        PostMessageW(mainApplicationWindow, WM_CLOSE, 0, 0);
        return 1;
    }

    return CallNextHookEx(g_keyboard_hook, nCode, wParam, lParam);
}

HMODULE module_from_hook_address()
{
    MEMORY_BASIC_INFORMATION mbi;
    ZeroMemory(&mbi, sizeof(mbi));

    if (VirtualQuery(
            reinterpret_cast<LPCVOID>(&workstation_keyboard_proc),
            &mbi,
            sizeof(mbi)
        ) == 0) {
        return nullptr;
    }

    return reinterpret_cast<HMODULE>(mbi.AllocationBase);
}

struct WorkstationShutdownCollectContext {
    std::vector<DWORD> *pids = nullptr;
};

BOOL CALLBACK collect_workstation_application_pid(HWND hwnd, LPARAM param)
{
    WorkstationShutdownCollectContext *context =
        reinterpret_cast<WorkstationShutdownCollectContext *>(param);
    if (!context || !context->pids || !hwnd || !IsWindow(hwnd))
        return TRUE;

    if (hwnd == g_exit_window || hwnd == g_bottom_panel_window)
        return TRUE;

    if (GetPropW(hwnd, WORKSTATION_TOOL_WINDOW_PROPERTY) != nullptr)
        return TRUE;

    const LONG_PTR style = GetWindowLongPtrW(hwnd, GWL_STYLE);
    if ((style & WS_CHILD) != 0)
        return TRUE;

    DWORD processId = 0;
    GetWindowThreadProcessId(hwnd, &processId);
    append_unique_pid(*context->pids, processId);
    return TRUE;
}

struct WorkstationShutdownSignalContext {
    const std::vector<DWORD> *pids = nullptr;
    UINT message = 0;
};

BOOL CALLBACK signal_workstation_application_shutdown(HWND hwnd, LPARAM param)
{
    WorkstationShutdownSignalContext *context =
        reinterpret_cast<WorkstationShutdownSignalContext *>(param);
    if (!context || !context->pids || !hwnd || !IsWindow(hwnd))
        return TRUE;

    DWORD processId = 0;
    GetWindowThreadProcessId(hwnd, &processId);
    if (!pid_in_list(*context->pids, processId))
        return TRUE;

    PostMessageW(hwnd, context->message, 0, 0);
    return TRUE;
}

void shutdown_workstation_child_processes()
{
    if (!g_workstation_owner)
        return;

    // Stage 128:
    // Neben den explizit via D64WorkstationLaunchProgram() gestarteten
    // Prozessen werden auch bereits gejointe Anwendungen auf dem dedizierten
    // Workstation-Desktop erfasst.
    std::vector<DWORD> childPids;
    for (DWORD pid : g_workstation_child_pids)
        append_unique_pid(childPids, pid);

    if (g_work_desktop) {
        WorkstationShutdownCollectContext collect;
        collect.pids = &childPids;
        EnumDesktopWindows(
            g_work_desktop,
            &collect_workstation_application_pid,
            reinterpret_cast<LPARAM>(&collect)
        );
    }

    if (childPids.empty()) {
        g_workstation_child_pids.clear();
        return;
    }

    // Erst geordneten Runtime-Cleanup anfordern. Ein normales WM_CLOSE wird
    // absichtlich NICHT benutzt, weil Fenster-X seit Stage 128 nur versteckt.
    if (g_work_desktop) {
        WorkstationShutdownSignalContext signal;
        signal.pids = &childPids;
        signal.message = workstation_global_shutdown_message();
        EnumDesktopWindows(
            g_work_desktop,
            &signal_workstation_application_shutdown,
            reinterpret_cast<LPARAM>(&signal)
        );
    }

    struct ProcessWait {
        DWORD pid = 0;
        HANDLE handle = nullptr;
    };
    std::vector<ProcessWait> waits;
    waits.reserve(childPids.size());

    for (DWORD pid : childPids) {
        HANDLE process = OpenProcess(
            SYNCHRONIZE | PROCESS_TERMINATE | PROCESS_QUERY_LIMITED_INFORMATION,
            FALSE,
            pid
        );
        if (process) {
            ProcessWait item;
            item.pid = pid;
            item.handle = process;
            waits.push_back(item);
        }
    }

    // Maximal ca. 3 Sekunden fuer sauberen Qt/DB/Session-Cleanup aller
    // Child-Prozesse zusammen. Danach werden verbliebene Prozesse beendet;
    // TerminateProcess beendet dabei saemtliche Threads des Prozesses.
    const DWORD started = GetTickCount();
    constexpr DWORD gracefulTimeoutMs = 3000;

    for (ProcessWait &item : waits) {
        const DWORD elapsed = GetTickCount() - started;
        const DWORD remaining =
            elapsed < gracefulTimeoutMs
                ? gracefulTimeoutMs - elapsed
                : 0;

        if (WaitForSingleObject(item.handle, remaining) == WAIT_OBJECT_0)
            continue;

        TerminateProcess(item.handle, 0);
        WaitForSingleObject(item.handle, 1000);
    }

    for (ProcessWait &item : waits) {
        if (item.handle)
            CloseHandle(item.handle);
    }

    g_workstation_child_pids.clear();
}

void close_desktop_handle(HDESK &desktop)
{
    if (!desktop)
        return;
    CloseDesktop(desktop);
    desktop = nullptr;
}

bool switch_to_original_input_desktop()
{
    if (g_original_input_desktop && SwitchDesktop(g_original_input_desktop)) {
        return true;
    }

    if (g_original_input_desktop)
        debug_last_error(L"SwitchDesktop(original input)");

    /*
     * Fallback fuer einen normalen interaktiven WinSta0-Prozess: falls der
     * urspruengliche Handle wider Erwarten nicht mehr schaltbar ist, versuchen
     * wir zuerst den gespeicherten Namen und danach "Default". Das ist nur ein
     * Rueckweg; wir ersetzen den urspruenglichen Desktop nicht prophylaktisch.
     */
    const wchar_t *fallback_name =
        g_original_input_name[0] ? g_original_input_name : L"Default";

    HDESK fallback = OpenDesktopW(
        fallback_name,
        0,
        FALSE,
        DESKTOP_SWITCHDESKTOP |
        DESKTOP_READOBJECTS |
        DESKTOP_WRITEOBJECTS
    );

    if (!fallback && _wcsicmp(fallback_name, L"Default") != 0) {
        fallback = OpenDesktopW(
            L"Default",
            0,
            FALSE,
            DESKTOP_SWITCHDESKTOP |
            DESKTOP_READOBJECTS |
            DESKTOP_WRITEOBJECTS
        );
    }

    if (!fallback) {
        debug_last_error(L"OpenDesktopW(original/Default)");
        return false;
    }

    const BOOL ok = SwitchDesktop(fallback);
    if (!ok)
        debug_last_error(L"SwitchDesktop(fallback)");
    CloseDesktop(fallback);
    return ok != FALSE;
}

} // namespace

void D64WorkstationSetExitCallback(D64WorkstationCallback callback)
{
    g_exit_callback = callback;
}

void D64WorkstationSetBtxCallback(D64WorkstationBtxCallback callback)
{
    g_btx_callback = callback;
}

void D64WorkstationSetDbCallback(D64WorkstationCallback callback)
{
    g_db_callback = callback;
}

void D64WorkstationSetServerCallback(D64WorkstationCallback callback)
{
    g_server_callback = callback;
}

void D64WorkstationSetServerClientCallback(D64WorkstationServerClientCallback callback)
{
    g_server_client_callback = callback;
}

void D64WorkstationSetServerClientCount(int count)
{
    if (count < 0)
        count = 0;
    if (count > 32)
        count = 32;
    g_server_client_count = count;
    if (g_bottom_panel_window && IsWindow(g_bottom_panel_window))
        InvalidateRect(g_bottom_panel_window, nullptr, FALSE);
}

bool D64WorkstationPrepare()
{
    if (g_workstation_active)
        return true;

    g_leave_started = false;
    g_workstation_visible = false;
    g_main_window = nullptr;
    g_original_input_name[0] = L'\0';
    g_desktop_name[0] = L'\0';

    // Stage 42: Jede Hauptanwendung besitzt zusaetzlich zur globalen
    // Workstation einen eigenen, aus ihrem kanonischen EXE-Pfad abgeleiteten
    // Windows-Mutex. Eine zweite Instanz derselben Anwendung beendet die
    // Initialisierung und aktiviert stattdessen das bereits vorhandene Fenster.
    if (!acquire_application_instance())
        return false;

    if (!acquire_singleton_role()) {
        release_application_instance();
        return false;
    }

    if (!prepare_ready_event()) {
        release_singleton_state();
        release_application_instance();
        return false;
    }

    /*
     * Der GUI-Thread ist zu diesem Zeitpunkt noch fenster-/hookfrei. Das ist
     * zwingend, weil SetThreadDesktop vor QApplication/QWidget erfolgen muss.
     */
    g_original_thread_desktop = GetThreadDesktop(GetCurrentThreadId());
    if (!g_original_thread_desktop) {
        debug_last_error(L"GetThreadDesktop");
        release_singleton_state();
        release_application_instance();
        return false;
    }

    /*
     * Der sichtbare Eingabedesktop bleibt nur fuer den OWNER der Rueckweg.
     * JOINED-Prozesse duerfen beim eigenen Ende die globale Workstation nicht
     * vom Benutzer wegschalten.
     */
    if (g_workstation_owner) {
        g_original_input_desktop = OpenInputDesktop(
            0,
            FALSE,
            DESKTOP_SWITCHDESKTOP |
            DESKTOP_READOBJECTS |
            DESKTOP_WRITEOBJECTS
        );

        if (!g_original_input_desktop) {
            debug_last_error(L"OpenInputDesktop");
            g_original_thread_desktop = nullptr;
            release_singleton_state();
            release_application_instance();
            return false;
        }
        get_desktop_name(g_original_input_desktop, g_original_input_name, 128);
    }

    std::wcsncpy(
        g_desktop_name,
        WORKSTATION_DESKTOP_NAME,
        (sizeof(g_desktop_name) / sizeof(g_desktop_name[0])) - 1
    );
    g_desktop_name[(sizeof(g_desktop_name) / sizeof(g_desktop_name[0])) - 1] = L'\0';

    if (g_workstation_owner) {
        /*
         * CreateDesktopW liefert bei bereits vorhandenem Namen einen Handle
         * auf denselben Desktop. Das ist auch nach einem Owner-Crash korrekt,
         * solange ein JOINED-Prozess den Desktop noch offen haelt.
         */
        g_work_desktop = CreateDesktopW(
            g_desktop_name,
            nullptr,
            nullptr,
            0,
            workstation_desktop_access(),
            nullptr
        );
    } else {
        g_work_desktop = OpenDesktopW(
            g_desktop_name,
            0,
            FALSE,
            workstation_desktop_access()
        );
    }

    if (!g_work_desktop) {
        debug_last_error(
            g_workstation_owner
                ? L"CreateDesktopW"
                : L"OpenDesktopW(existing Workstation)"
        );
        close_desktop_handle(g_original_input_desktop);
        g_original_thread_desktop = nullptr;
        g_desktop_name[0] = L'\0';
        release_singleton_state();
        release_application_instance();
        return false;
    }

    /*
     * Ein via STARTUPINFO.lpDesktop gestartetes BTX.exe kann bereits auf dem
     * Workstation-Desktop liegen. Andernfalls wird der noch fensterfreie GUI-
     * Thread jetzt an den vorhandenen Desktop gebunden.
     */
    if (!current_thread_is_on_work_desktop()) {
        if (!SetThreadDesktop(g_work_desktop)) {
            debug_last_error(L"SetThreadDesktop(work)");
            close_desktop_handle(g_work_desktop);
            close_desktop_handle(g_original_input_desktop);
            g_original_thread_desktop = nullptr;
            g_desktop_name[0] = L'\0';
            release_singleton_state();
            release_application_instance();
            return false;
        }
    }

    if (!current_thread_is_on_work_desktop()) {
        if (g_original_thread_desktop)
            SetThreadDesktop(g_original_thread_desktop);
        close_desktop_handle(g_work_desktop);
        close_desktop_handle(g_original_input_desktop);
        g_original_thread_desktop = nullptr;
        g_desktop_name[0] = L'\0';
        release_singleton_state();
        release_application_instance();
        return false;
    }

    g_workstation_active = true;

    if (g_workstation_owner) {
        // Erst ab hier duerfen weitere Prozesse den gemeinsamen Desktop oeffnen.
        SetEvent(g_workstation_ready_event);
    }

    return true;
}

bool D64WorkstationActivate(HWND mainWindow)
{
    if (!g_workstation_active || !g_work_desktop || !mainWindow)
        return false;

    if (!current_thread_is_on_work_desktop())
        return false;

    if (!IsWindow(mainWindow) || !IsWindowVisible(mainWindow))
        return false;

    g_main_window = mainWindow;
    mark_application_main_window(mainWindow);

    // Auch die erste sichtbare Position liegt immer im freien Workstation-
    // Bereich rechts vom linken und oberhalb des unteren Panels.
    RECT constrainedRect;
    if (GetWindowRect(mainWindow, &constrainedRect)) {
        const int oldX = constrainedRect.left;
        const int oldY = constrainedRect.top;
        D64WorkstationConstrainMovingRect(&constrainedRect);
        if (constrainedRect.left != oldX || constrainedRect.top != oldY) {
            SetWindowPos(
                mainWindow, nullptr,
                constrainedRect.left, constrainedRect.top,
                0, 0,
                SWP_NOACTIVATE | SWP_NOZORDER | SWP_NOSIZE
            );
        }
    }

    /*
     * JOINED: Die globale Workstation existiert bereits. Nur das neue
     * Programmfenster wird auf diesem Desktop aktiviert. Kein zweites Panel,
     * kein zweites SwitchDesktop und spaeter kein zweiter Keyboard-Hook.
     */
    if (!g_workstation_owner) {
        g_workstation_visible = true;
        SetForegroundWindow(mainWindow);
        BringWindowToTop(mainWindow);
        SetActiveWindow(mainWindow);
        signal_application_ready();
        return true;
    }

    if (g_workstation_visible)
        return true;

    /* OWNER: Panel erzeugen, erst danach die Workstation sichtbar schalten. */
    if (!create_exit_window()) {
        g_main_window = nullptr;
        return false;
    }
    if (!create_bottom_panel_window()) {
        destroy_bottom_panel_window();
        destroy_exit_window();
        g_main_window = nullptr;
        return false;
    }

    if (!SwitchDesktop(g_work_desktop)) {
        debug_last_error(L"SwitchDesktop(work)");
        destroy_bottom_panel_window();
        destroy_exit_window();
        g_main_window = nullptr;
        return false;
    }

    g_workstation_visible = true;

    SetForegroundWindow(mainWindow);
    BringWindowToTop(mainWindow);
    SetActiveWindow(mainWindow);
    const int screenHeight = GetSystemMetrics(SM_CYSCREEN);
    const int usableHeight = screenHeight - WORKSTATION_BOTTOM_PANEL_HEIGHT;
    const int panelHeight = usableHeight > 180 ? usableHeight : 180;
    SetWindowPos(
        g_exit_window,
        HWND_TOPMOST,
        0,
        0,
        WORKSTATION_PANEL_WIDTH,
        panelHeight,
        SWP_NOACTIVATE | SWP_SHOWWINDOW
    );
    const int screenWidth = GetSystemMetrics(SM_CXSCREEN);
    SetWindowPos(
        g_bottom_panel_window,
        HWND_TOPMOST,
        0,
        screenHeight - WORKSTATION_BOTTOM_PANEL_HEIGHT,
        screenWidth,
        WORKSTATION_BOTTOM_PANEL_HEIGHT,
        SWP_NOACTIVATE | SWP_SHOWWINDOW
    );
    signal_application_ready();
    return true;
}

bool D64WorkstationInstallKeyboardGuard(HWND mainWindow)
{
    if (!g_workstation_active || !g_workstation_visible || !mainWindow)
        return false;

    g_main_window = mainWindow;

    // Nur der OWNER installiert den globalen Low-Level-Keyboard-Hook.
    if (!g_workstation_owner)
        return true;

    if (g_keyboard_hook)
        return true;

    HMODULE module = module_from_hook_address();
    if (!module)
        return false;

    g_keyboard_hook = SetWindowsHookExW(
        WH_KEYBOARD_LL,
        workstation_keyboard_proc,
        module,
        0
    );

    if (!g_keyboard_hook) {
        debug_last_error(L"SetWindowsHookExW");
        return false;
    }

    return true;
}

void D64WorkstationBeginLeave()
{
    if (!g_workstation_active || g_leave_started)
        return;

    g_leave_started = true;
    unmark_application_main_window();

    /*
     * JOINED beendet nur seine eigene Runtime. Die globale Workstation, das
     * Panel und der Input-Desktop gehoeren ausschliesslich dem OWNER.
     */
    if (!g_workstation_owner) {
        g_main_window = nullptr;
        g_workstation_visible = false;
        return;
    }

    if (g_keyboard_hook) {
        UnhookWindowsHookEx(g_keyboard_hook);
        g_keyboard_hook = nullptr;
    }

    // Stage 128:
    // Zuerst alle Console-/GUI-Child-Prozesse beenden. Panel, Desktop und
    // Workstation-Mutex bleiben bis D64WorkstationFinalizeLeave() erhalten,
    // damit die Workstation wirklich als letzte Ressource verschwindet.
    shutdown_workstation_child_processes();
    g_main_window = nullptr;
}

void D64WorkstationFinalizeLeave()
{
    if (!g_workstation_active) {
        release_singleton_state();
        release_application_instance();
        return;
    }

    if (g_workstation_owner && g_keyboard_hook) {
        UnhookWindowsHookEx(g_keyboard_hook);
        g_keyboard_hook = nullptr;
    }

    if (g_workstation_owner) {
        destroy_bottom_panel_window();
        destroy_exit_window();
    }

    if (g_workstation_owner && g_workstation_visible) {
        switch_to_original_input_desktop();
        g_workstation_visible = false;
    }

    /*
     * Erst nachdem alle Qt-Fenster dieses Prozesses zerlegt wurden, darf der
     * GUI-Thread auf seinen Startdesktop zurueck. Beim via lpDesktop gestarteten
     * JOINED-Prozess ist das bereits derselbe Workstation-Desktop.
     */
    if (g_original_thread_desktop &&
        !current_thread_is_on_work_desktop()) {
        // already on another/original desktop; nothing to do
    } else if (g_original_thread_desktop) {
        if (!SetThreadDesktop(g_original_thread_desktop)) {
            debug_last_error(L"SetThreadDesktop(original)");
        }
    }

    close_desktop_handle(g_work_desktop);
    close_desktop_handle(g_original_input_desktop);

    g_original_thread_desktop = nullptr;
    g_original_input_name[0] = L'\0';
    g_desktop_name[0] = L'\0';
    
    g_main_window   = nullptr;
    g_exit_callback = nullptr;
    g_btx_callback  = nullptr;
    g_db_callback   = nullptr;
    
    g_workstation_child_pids.clear();
    g_workstation_active  = false;
    g_workstation_visible = false;
    
    g_leave_started = false;

    // OWNER gibt den Workstation-Lifetime-Mutex als allerletzten Schritt frei.
    // Der Anwendungs-Mutex lebt exakt so lange wie diese Hauptanwendung.
    release_singleton_state();
    release_application_instance();
}

bool D64WorkstationIsActive()
{
    return g_workstation_active;
}

bool D64WorkstationIsVisible()
{
    return g_workstation_visible;
}

bool D64WorkstationOwnsDesktop()
{
    return g_workstation_owner;
}

bool D64WorkstationJoinedExisting()
{
    return g_workstation_joined;
}

bool D64WorkstationExitIconVisible()
{
    return g_exit_window && IsWindow(g_exit_window) && IsWindowVisible(g_exit_window);
}

bool D64WorkstationPanelVisible()
{
    return D64WorkstationExitIconVisible() &&
        g_bottom_panel_window && IsWindow(g_bottom_panel_window) && IsWindowVisible(g_bottom_panel_window);
}

namespace {

struct ApplicationWindowCloseContext {
    DWORD processId = 0;
    HWND mainWindow = nullptr;
};

BOOL CALLBACK close_current_application_window(HWND hwnd, LPARAM param)
{
    ApplicationWindowCloseContext *context =
        reinterpret_cast<ApplicationWindowCloseContext *>(param);
    if (!context || !hwnd || !IsWindow(hwnd))
        return TRUE;

    DWORD processId = 0;
    GetWindowThreadProcessId(hwnd, &processId);
    if (processId != context->processId)
        return TRUE;

    // Das Hauptfenster befindet sich bereits in seinem Qt-closeEvent().
    // Das Workstation-Panel gehoert dem OWNER und darf von einem normalen
    // Application-Close ebenfalls nicht getroffen werden.
    if (hwnd == context->mainWindow || hwnd == g_exit_window || hwnd == g_bottom_panel_window)
        return TRUE;

    ShowWindow(hwnd, SW_HIDE);
    PostMessageW(hwnd, WM_CLOSE, 0, 0);
    return TRUE;
}

} // namespace

void D64WorkstationCloseApplicationWindows(HWND mainWindow)
{
    if (!g_work_desktop)
        return;

    ApplicationWindowCloseContext context;
    context.processId = GetCurrentProcessId();
    context.mainWindow = mainWindow;

    EnumDesktopWindows(
        g_work_desktop,
        &close_current_application_window,
        reinterpret_cast<LPARAM>(&context)
    );
}


int D64WorkstationLeftPanelWidth()
{
    return WORKSTATION_PANEL_WIDTH;
}

int D64WorkstationBottomPanelHeight()
{
    return WORKSTATION_BOTTOM_PANEL_HEIGHT;
}

void D64WorkstationConstrainMovingRect(RECT *rect)
{
    if (!rect)
        return;
    const int screenWidth = GetSystemMetrics(SM_CXSCREEN);
    const int screenHeight = GetSystemMetrics(SM_CYSCREEN);
    const int left = WORKSTATION_PANEL_WIDTH + WORKSTATION_PANEL_GAP;
    const int top = WORKSTATION_PANEL_GAP;
    const int right = screenWidth - WORKSTATION_PANEL_GAP;
    const int bottom = screenHeight - WORKSTATION_BOTTOM_PANEL_HEIGHT - WORKSTATION_PANEL_GAP;
    const int width = rect->right - rect->left;
    const int height = rect->bottom - rect->top;

    int x = rect->left;
    int y = rect->top;
    if (x < left) x = left;
    if (y < top) y = top;
    if (x + width > right) x = right - width;
    if (y + height > bottom) y = bottom - height;
    if (x < left) x = left;
    if (y < top) y = top;
    rect->left = x;
    rect->top = y;
    rect->right = x + width;
    rect->bottom = y + height;
}

void D64WorkstationConstrainMaximizeInfo(void *minMaxInfo)
{
    if (!minMaxInfo)
        return;

    MINMAXINFO *info = reinterpret_cast<MINMAXINFO *>(minMaxInfo);

    const int screenWidth = GetSystemMetrics(SM_CXSCREEN);
    const int screenHeight = GetSystemMetrics(SM_CYSCREEN);

    const int left = WORKSTATION_PANEL_WIDTH + WORKSTATION_PANEL_GAP;
    const int top = WORKSTATION_PANEL_GAP;
    const int right = screenWidth - WORKSTATION_PANEL_GAP;
    const int bottom =
        screenHeight -
        WORKSTATION_BOTTOM_PANEL_HEIGHT -
        WORKSTATION_PANEL_GAP;

    const int width = right > left ? right - left : 1;
    const int height = bottom > top ? bottom - top : 1;

    // WM_GETMINMAXINFO steuert die aeussere maximierte Fenstergeometrie.
    // Dadurch bleiben linkes Panel, Bottom-Panel und der 4px-Rand frei.
    info->ptMaxPosition.x = left;
    info->ptMaxPosition.y = top;
    info->ptMaxSize.x = width;
    info->ptMaxSize.y = height;

    // Auch das Track-Limit darf den freien Workstation-Bereich nicht
    // ueberschreiten; zusammen mit D64WorkstationConstrainMovingRect()
    // kann ein Child-Fenster dadurch nicht ueber die Panels wachsen.
    info->ptMaxTrackSize.x = width;
    info->ptMaxTrackSize.y = height;
}

void D64WorkstationPositionMinimizedWindow(HWND mainWindow)
{
    if (!mainWindow || !IsWindow(mainWindow))
        return;

    // Windows besitzt fuer minimierte Top-Level-Fenster eine eigene gespeicherte
    // Position. SetWindowPos() auf das normale Fensterrechteck ist dafuer nicht
    // verlaesslich (u. a. -32000/-32000 bei minimierten Fenstern).
    WINDOWPLACEMENT placement;
    ZeroMemory(&placement, sizeof(placement));
    placement.length = sizeof(placement);
    if (!GetWindowPlacement(mainWindow, &placement))
        return;

    const int minimizedHeight = (GetSystemMetrics(SM_CYMINIMIZED) > 0 ? GetSystemMetrics(SM_CYMINIMIZED) : 1);
    placement.flags |= WPF_SETMINPOSITION;
    placement.ptMinPosition.x = WORKSTATION_PANEL_WIDTH + WORKSTATION_PANEL_GAP;
    placement.ptMinPosition.y = GetSystemMetrics(SM_CYSCREEN)
        - WORKSTATION_BOTTOM_PANEL_HEIGHT
        - WORKSTATION_PANEL_GAP
        - minimizedHeight;
    SetWindowPlacement(mainWindow, &placement);
}

bool D64WorkstationLaunchProgram(
    const wchar_t *applicationPath,
    const wchar_t *workingDirectory
)
{
    if (!g_workstation_active || !applicationPath || !*applicationPath)
        return false;

    const std::wstring canonicalPath = normalize_application_path(applicationPath);
    if (canonicalPath.empty())
        return false;

    /*
     * Stage 42: Pro Hauptanwendung gibt es zwei Kernelobjekte:
     *   - D64Application.<hash>             = Lebensdauer-/Instance-Mutex
     *   - D64Application.<hash>.LaunchGate = serialisiert schnelle Doppelklicks
     *
     * Der LaunchGate bleibt gehalten, bis die neue Anwendung in
     * D64WorkstationActivate() ihr InstanceReady-Event setzt. Dadurch kann auch
     * ein sehr schneller zweiter BTX-Klick nie zwischen CreateProcessW() und
     * der Mutex-Erzeugung der Kindanwendung eine zweite Instanz starten.
     */
    const std::wstring instanceName = application_object_name(canonicalPath, L"");
    const std::wstring gateName = application_object_name(canonicalPath, L".LaunchGate");
    const std::wstring readyName = application_object_name(canonicalPath, L".InstanceReady");

    HANDLE gate = CreateMutexW(nullptr, FALSE, gateName.c_str());
    if (!gate) {
        debug_last_error(L"CreateMutexW(application launch gate)");
        return false;
    }

    const DWORD gateWait = WaitForSingleObject(gate, 5000);
    if (gateWait != WAIT_OBJECT_0 && gateWait != WAIT_ABANDONED) {
        CloseHandle(gate);
        SetLastError(gateWait == WAIT_TIMEOUT ? ERROR_TIMEOUT : GetLastError());
        return false;
    }

    HANDLE existing = OpenMutexW(SYNCHRONIZE, FALSE, instanceName.c_str());
    if (existing) {
        CloseHandle(existing);
        activate_existing_application_by_path(canonicalPath);
        ReleaseMutex(gate);
        CloseHandle(gate);
        return true;
    }

    HANDLE readyEvent = CreateEventW(nullptr, TRUE, FALSE, readyName.c_str());
    if (readyEvent)
        ResetEvent(readyEvent);

    std::wstring desktopSpec = L"WinSta0\\";
    desktopSpec += g_desktop_name;

    std::wstring commandLine = L"\"";
    commandLine += applicationPath;
    commandLine += L"\"";
    std::vector<wchar_t> mutableCommand(commandLine.begin(), commandLine.end());
    mutableCommand.push_back(L'\0');

    STARTUPINFOW startup;
    ZeroMemory(&startup, sizeof(startup));
    startup.cb = sizeof(startup);
    startup.lpDesktop = const_cast<LPWSTR>(desktopSpec.c_str());

    PROCESS_INFORMATION processInfo;
    ZeroMemory(&processInfo, sizeof(processInfo));

    const BOOL ok = CreateProcessW(
        applicationPath,
        mutableCommand.data(),
        nullptr,
        nullptr,
        FALSE,
        CREATE_UNICODE_ENVIRONMENT,
        nullptr,
        (workingDirectory && *workingDirectory) ? workingDirectory : nullptr,
        &startup,
        &processInfo
    );

    if (!ok) {
        debug_last_error(L"CreateProcessW(workstation program)");
        if (readyEvent)
            CloseHandle(readyEvent);
        ReleaseMutex(gate);
        CloseHandle(gate);
        return false;
    }

    g_workstation_child_pids.push_back(processInfo.dwProcessId);
    CloseHandle(processInfo.hThread);

    // Normalerweise wird dieses Event schon waehrend D64WorkstationPrepare/
    // Activate der Kindanwendung gesetzt. Das kurze Warten verhindert die
    // Start-Race bei Doppelklicks, ohne einen Desktop-Wechsel auszufuehren.
    if (readyEvent) {
        HANDLE waits[2] = { readyEvent, processInfo.hProcess };
        WaitForMultipleObjects(2, waits, FALSE, 2000);
        CloseHandle(readyEvent);
    }

    CloseHandle(processInfo.hProcess);
    ReleaseMutex(gate);
    CloseHandle(gate);
    return true;
}

bool D64WorkstationApplicationInstanceOwned()
{
    return g_application_mutex != nullptr;
}

const wchar_t *D64WorkstationApplicationMutexName()
{
    return g_application_mutex_name.c_str();
}

const wchar_t *D64WorkstationDesktopName()
{
    return g_desktop_name;
}

#else

void D64WorkstationSetExitCallback(D64WorkstationCallback) {}
void D64WorkstationSetBtxCallback(D64WorkstationBtxCallback) {}
void D64WorkstationSetDbCallback(D64WorkstationCallback) {}
void D64WorkstationSetServerCallback(D64WorkstationCallback) {}
void D64WorkstationSetServerClientCallback(D64WorkstationServerClientCallback) {}
void D64WorkstationSetServerClientCount(int) {}

bool D64WorkstationPrepare() { return true; }
bool D64WorkstationActivate(HWND) { return true; }
bool D64WorkstationInstallKeyboardGuard(HWND) { return true; }

void D64WorkstationBeginLeave() {}
void D64WorkstationFinalizeLeave() {}

bool D64WorkstationIsActive() { return false; }
bool D64WorkstationIsVisible() { return false; }
bool D64WorkstationOwnsDesktop() { return false; }
bool D64WorkstationJoinedExisting() { return false; }
bool D64WorkstationExitIconVisible() { return false; }
bool D64WorkstationPanelVisible() { return false; }

int  D64WorkstationLeftPanelWidth() { return 0; }
int  D64WorkstationBottomPanelHeight() { return 0; }

void D64WorkstationConstrainMovingRect(RECT *) {}
void D64WorkstationConstrainMaximizeInfo(void *) {}
void D64WorkstationPositionMinimizedWindow(HWND) {}
void D64WorkstationCloseApplicationWindows(HWND) {}

bool D64WorkstationLaunchProgram(const wchar_t *, const wchar_t *) { return false; }
bool D64WorkstationApplicationInstanceOwned() { return false; }

const wchar_t *D64WorkstationApplicationMutexName() { return L""; }
const wchar_t *D64WorkstationDesktopName() { return L""; }

#endif

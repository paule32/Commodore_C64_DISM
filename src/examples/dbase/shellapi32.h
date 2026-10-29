// ---------------------------------------------------------------------------
// File:   shellapi32.h
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
#ifndef DBASE_WINAPI_SHELL32_H
#define DBASE_WINAPI_SHELL32_H

# define shell32 "shell32.dll"

// ---------------------------------------------------------------------------
// Programm oder Datei starten
// ---------------------------------------------------------------------------
extern HINSTANCE ShellExecute     (HWND, LPCSTR , LPCSTR , LPCSTR , LPCSTR , CINT) shell32 from "ShellExecuteA"
extern HINSTANCE ShellExecuteA    (HWND, LPCSTR , LPCSTR , LPCSTR , LPCSTR , CINT) shell32 from "ShellExecuteA"
extern HINSTANCE ShellExecuteW    (HWND, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, CINT) shell32 from "ShellExecuteW"

// ---------------------------------------------------------------------------
// Windows-Shell-Info anzeigen
// ---------------------------------------------------------------------------
extern CINT ShellAboutW           (HWND, LPCWSTR, LPCWSTR, HICON) shell32 from "ShellAboutW"

// ---------------------------------------------------------------------------
// Papierkorb leeren
// ---------------------------------------------------------------------------
extern HRESULT SHEmptyRecycleBinW (HWND, LPCWSTR, DWORD) shell32 from "SHEmptyRecycleBinW"

// ---------------------------------------------------------------------------
// Symbol aus einer Datei extrahieren
// ---------------------------------------------------------------------------
extern HICON ExtractIconW (HINSTANCE, LPCWSTR, UINT) shell32 from "ExtractIconW"

#endif


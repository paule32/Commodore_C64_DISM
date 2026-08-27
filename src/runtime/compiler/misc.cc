// ---------------------------------------------------------------------------
// \file misc.cc
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "dbase2many.hpp"

static bool
starts_with(
    const std::string& s,
    const std::string& prefix) {
    
    return s.rfind(prefix, 0) == 0;
}

static std::string
trim(
    const std::string& s) {
    const char* ws = " \t\r\n";

    size_t first = s.find_first_not_of(ws);
    if (first == std::string::npos)
        return "";

    size_t last = s.find_last_not_of(ws);

    return s.substr(first, last - first + 1);
}

std::string
format_asm_line(
    const std::string& line)
{
    std::string s = line;

    if (s.empty())
        return "";

    size_t pos = s.find_first_not_of(" \t\r\n");
    if (pos == std::string::npos)
        return "";

    s = s.substr(pos);

    if (!s.empty() && s[0] == ';')
        return s;

    size_t colon = s.find(':');
    size_t space = s.find_first_of(" \t");

    if (colon != std::string::npos &&
        (space == std::string::npos || colon < space))
        return s;

    size_t mnemonic_end = s.find_first_of(" \t");
    if (mnemonic_end == std::string::npos)
        return "    " + s;

    std::string mnemonic = s.substr(0, mnemonic_end);

    size_t operand_start = s.find_first_not_of(" \t", mnemonic_end);
    if (operand_start == std::string::npos)
        return "    " + mnemonic;

    std::string operands = s.substr(operand_start);

    const size_t operand_column = 16;
    std::string out = "    " + mnemonic;

    if (out.length() < operand_column)
        out += std::string(operand_column - out.length(), ' ');
    else
        out += "    ";

    out += operands;
    return out;
}

static std::string
format_asm_line_cpp(
    const std::string& line)
{
    std::string t = trim(line);
    if (t.empty())
        return "";

    // Labels links lassen
    if (t.back() == ':')
        return t;

    // NASM-Direktiven nicht einrücken
    if (
        starts_with(t, "struc ")   ||
        starts_with(t, "endstruc") ||
        starts_with(t, "extern ")  ||
        starts_with(t, "global ")  ||
        starts_with(t, "section ") ||
        starts_with(t, "equ ")     ||
        t.find(" equ ") != std::string::npos  ||
        t.find(" db ")  != std::string::npos  ||
        t.find(" resq ") != std::string::npos ||
        t.find(" resd ") != std::string::npos) {
        return t;
    }

    std::string s = line;

    if (s.empty())
        return "";

    size_t pos = s.find_first_not_of(" \t\r\n");
    if (pos == std::string::npos)
        return "";

    s = s.substr(pos);

    if (!s.empty() && s[0] == ';')
        return s;

    size_t colon = s.find(':');
    size_t space = s.find_first_of(" \t");

    if (colon != std::string::npos &&
        (space == std::string::npos || colon < space))
        return s;

    size_t mnemonic_end = s.find_first_of(" \t");
    if (mnemonic_end == std::string::npos)
        return "    " + s;

    std::string mnemonic = s.substr(0, mnemonic_end);

    size_t operand_start = s.find_first_not_of(" \t", mnemonic_end);
    if (operand_start == std::string::npos)
        return "    " + mnemonic;

    std::string operands = s.substr(operand_start);

    const size_t operand_column = 16;

    std::string out = "    " + mnemonic;

    if (out.length() < operand_column)
        out += std::string(operand_column - out.length(), ' ');
    else
        out += "    ";

    out += operands;
    return out;
}

DLL_API bool
write_formatted_asm_file(
    const char* asm_text,
    const char* file_name)
{
    try {
        if (!asm_text || !file_name)
            return false;

        std::ofstream asm_out(file_name);
        if (!asm_out.is_open())
            return false;

        std::istringstream iss(asm_text);
        std::string line;

        while (std::getline(iss, line)) {
            asm_out << format_asm_line_cpp(line) << '\n';
        }

        return true;
    }
    catch (...) {
        return false;
    }
}

DLL_API int32_t _jit_read_int() {
    int32_t v;
    std::cin >> v;
    return v;
}

DLL_API char* _jit_read_string() {
    std::string s;
    std::getline(std::cin, s);

    char* mem = (char*)malloc(s.size() + 1);
    memcpy(mem, s.c_str(), s.size() + 1);
    return mem;
}

DLL_API void _jit_debug_break() {
    std::cout << "[BREAK] Press ENTER..." << std::endl;
    std::cin.get();
}

DLL_API bool
replace_all_str_c(
    const char* asm_text,
    const char* file_name)
{
    try {
        if (!asm_text || !file_name)
            return false;

        std::ofstream asm_out(file_name);
        if (!asm_out.is_open())
            return false;

        std::istringstream iss(asm_text);
        std::string line;

        while (std::getline(iss, line)) {
            asm_out << format_asm_line(line) << '\n';
        }

        return true;
    }
    catch (...) {
        return false;
    }
}

DLL_API void
replace_all_str(
    std::string&   asm_text,
    std::ofstream& asm_out) {
    
    std::istringstream iss(asm_text);
    std::string line;
    
    while (std::getline(iss, line)) {
        asm_out << format_asm_line(line) << std::endl;
    }
}

DLL_API uint64_t
_double_to_bits(double value) {
    uint64_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

DLL_API void
replace_all(
    std::string& s,
    const std::string& from,
    const std::string& to) {
    
    if (from.empty())
        return;

    size_t pos = 0;

    while ((pos = s.find(from, pos)) != std::string::npos) {
        s.replace(pos, from.length(), to);
        pos += std::max<size_t>(to.length(), 1);
    }
}

DLL_API std::string&
replace_all_ptr(std::string& asm_text)
{
    replace_all(asm_text, "byte ptr ",    "byte ");
    replace_all(asm_text, "word ptr ",    "word ");
    replace_all(asm_text, "dword ptr ",   "dword ");
    replace_all(asm_text, "qword ptr ",   "qword ");
    replace_all(asm_text, "xmmword ptr ", "xmmword ");
    
    return asm_text;
}

DLL_API std::string&
replace_all_fun(std::string& asm_text)
{
    replace_all(asm_text, std::to_string((uint64_t)&_jit_print_text),    "_jit_print_text");
    replace_all(asm_text, std::to_string((uint64_t)&_jit_print_int),     "_jit_print_int");
    replace_all(asm_text, std::to_string((uint64_t)&_jit_print_double),  "_jit_print_double");
    replace_all(asm_text, std::to_string((uint64_t)&_jit_print_newline), "_jit_print_newline");
    
    return asm_text;
}

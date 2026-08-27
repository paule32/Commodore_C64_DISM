// ---------------------------------------------------------------------------
// File: iostream.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"

namespace std {
ostream cout;

ostream::ostream() { }
ostream& ostream::operator<<(int value) {
    _jit_print_int(value);
    return *this;
}

ostream& ostream::operator<<(uint32_t value) {
    _jit_print_int(value);
    return *this;
}

ostream& ostream::operator<<(double value) {
    _jit_print_double(value);
    return *this;
}

ostream& ostream::operator<<(char value) {
    _jit_print_char(value);
    return *this;
}

ostream& ostream::operator<<(const char* text) {
    _jit_print_text(text);
    return *this;
}

ostream& ostream::operator<<(ostream_manipulator fn) {
    return fn(*this);
}

ostream& endl(ostream& os) {
    _jit_print_newline();
    return os;
}

}   // namespace: std

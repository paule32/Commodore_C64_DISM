#pragma once
// Stage 631: unabhängiger, deterministischer Ausdrucksparser für den
// Turbo-Vision-Taschenrechner. Keine dynamische Ausführung von Code.
// Grammatik: expr := term ((+|-) term)*;
// term := factor ((*|/) factor)*; factor := (+|-) factor | '(' expr ')' | number.
#include <cmath>
#include <cctype>
#include <string>

struct D64CalculatorResult {
    bool ok = false;
    double value = 0.0;
    std::string error;
};

class D64CalculatorExpression final {
public:
    static D64CalculatorResult evaluate(const std::string &expression)
    {
        D64CalculatorExpression parser(expression);
        const double value = parser.parseExpression();
        parser.skipSpaces();
        if (parser.error_.empty() && parser.pos_ != expression.size())
            parser.error_ = "Unerwartetes Zeichen";
        if (parser.error_.empty() && !std::isfinite(value))
            parser.error_ = "Ergebnis ausserhalb des Zahlenbereichs";
        if (!parser.error_.empty()) return {false, 0.0, parser.error_};
        return {true, value, {}};
    }
private:
    explicit D64CalculatorExpression(const std::string &source) : source_(source) {}
    void skipSpaces()
    {
        while (pos_ < source_.size() && std::isspace(static_cast<unsigned char>(source_[pos_]))) ++pos_;
    }
    bool accept(char c)
    {
        skipSpaces();
        if (pos_ >= source_.size() || source_[pos_] != c) return false;
        ++pos_;
        return true;
    }
    double parseExpression()
    {
        double lhs = parseTerm();
        while (error_.empty()) {
            if (accept('+')) lhs += parseTerm();
            else if (accept('-')) lhs -= parseTerm();
            else break;
            if (!std::isfinite(lhs)) error_ = "Zahlenueberlauf";
        }
        return lhs;
    }
    double parseTerm()
    {
        double lhs = parseFactor();
        while (error_.empty()) {
            if (accept('*')) lhs *= parseFactor();
            else if (accept('/')) {
                const double rhs = parseFactor();
                if (!error_.empty()) break;
                if (rhs == 0.0) { error_ = "Division durch Null"; break; }
                lhs /= rhs;
            } else break;
            if (!std::isfinite(lhs)) error_ = "Zahlenueberlauf";
        }
        return lhs;
    }
    double parseFactor()
    {
        if (!error_.empty()) return 0.0;
        if (accept('+')) return parseFactor();
        if (accept('-')) return -parseFactor();
        if (accept('(')) {
            const double value = parseExpression();
            if (!accept(')') && error_.empty()) error_ = "Schliessende Klammer fehlt";
            return value;
        }
        skipSpaces();
        double whole = 0.0;
        bool digits = false;
        while (pos_ < source_.size() && source_[pos_] >= '0' && source_[pos_] <= '9') {
            whole = whole * 10.0 + (source_[pos_++] - '0');
            digits = true;
        }
        if (accept('.')) {
            double divisor = 10.0;
            while (pos_ < source_.size() && source_[pos_] >= '0' && source_[pos_] <= '9') {
                whole += (source_[pos_++] - '0') / divisor;
                divisor *= 10.0;
                digits = true;
            }
        }
        if (!digits && error_.empty()) error_ = "Zahl erwartet";
        return whole;
    }
    const std::string &source_;
    std::size_t pos_ = 0;
    std::string error_;
};

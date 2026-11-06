"""Agent -> 0001: deutscher Grammatikparser für d64_dism."""
from .grammar import Diagnostic, ParseResult, Token, parse_sentence, tokenize

# GUI erst bei Bedarf laden: reine Grammatiktests benötigen kein PyQt5.
def __getattr__(name):
    if name == "GermanGrammarWidget":
        from .gui import GermanGrammarWidget
        return GermanGrammarWidget
    raise AttributeError(name)

__all__ = ["Diagnostic", "ParseResult", "Token", "parse_sentence", "tokenize", "GermanGrammarWidget"]

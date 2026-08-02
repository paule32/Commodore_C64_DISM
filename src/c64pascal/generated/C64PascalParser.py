# Generated from /workspace/scratch/bfdb5d095aea/library_work/dBase Lexer + Parser/c64pascal/grammar/C64PascalParser.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,55,256,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,2,19,7,19,2,20,
        7,20,2,21,7,21,2,22,7,22,2,23,7,23,2,24,7,24,2,25,7,25,2,26,7,26,
        2,27,7,27,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,3,1,66,8,1,1,1,1,1,
        1,1,1,1,1,2,3,2,73,8,2,1,2,3,2,76,8,2,1,2,1,2,1,3,1,3,4,3,82,8,3,
        11,3,12,3,83,1,4,1,4,1,4,1,4,1,4,1,5,1,5,4,5,93,8,5,11,5,12,5,94,
        1,6,1,6,1,6,1,6,1,6,3,6,102,8,6,1,6,1,6,1,7,1,7,1,7,5,7,109,8,7,
        10,7,12,7,112,9,7,1,8,1,8,1,9,1,9,3,9,118,8,9,1,9,1,9,1,10,1,10,
        1,10,5,10,125,8,10,10,10,12,10,128,9,10,1,10,3,10,131,8,10,1,11,
        1,11,1,11,1,11,1,11,1,11,1,11,1,11,1,11,3,11,142,8,11,1,12,1,12,
        1,12,1,12,1,13,1,13,1,13,3,13,151,8,13,1,13,3,13,154,8,13,1,14,1,
        14,1,14,1,14,1,14,1,14,3,14,162,8,14,1,15,1,15,1,15,1,15,1,15,1,
        16,1,16,3,16,171,8,16,1,16,1,16,1,16,1,17,1,17,1,17,1,17,1,17,1,
        17,1,17,1,17,1,17,1,18,1,18,1,18,5,18,188,8,18,10,18,12,18,191,9,
        18,1,19,1,19,1,20,1,20,1,20,5,20,198,8,20,10,20,12,20,201,9,20,1,
        21,1,21,1,21,5,21,206,8,21,10,21,12,21,209,9,21,1,22,1,22,1,22,3,
        22,214,8,22,1,23,1,23,1,23,5,23,219,8,23,10,23,12,23,222,9,23,1,
        24,1,24,1,24,5,24,227,8,24,10,24,12,24,230,9,24,1,25,1,25,1,25,3,
        25,235,8,25,1,26,1,26,1,26,1,26,1,26,1,26,1,26,3,26,244,8,26,1,26,
        1,26,1,26,1,26,1,26,1,26,3,26,252,8,26,1,27,1,27,1,27,0,0,28,0,2,
        4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,
        50,52,54,0,8,1,0,18,21,1,0,14,15,1,0,27,28,1,0,31,36,1,0,37,38,2,
        0,24,25,39,40,2,0,29,29,37,38,1,0,47,49,263,0,56,1,0,0,0,2,59,1,
        0,0,0,4,72,1,0,0,0,6,79,1,0,0,0,8,85,1,0,0,0,10,90,1,0,0,0,12,96,
        1,0,0,0,14,105,1,0,0,0,16,113,1,0,0,0,18,115,1,0,0,0,20,121,1,0,
        0,0,22,141,1,0,0,0,24,143,1,0,0,0,26,147,1,0,0,0,28,155,1,0,0,0,
        30,163,1,0,0,0,32,168,1,0,0,0,34,175,1,0,0,0,36,184,1,0,0,0,38,192,
        1,0,0,0,40,194,1,0,0,0,42,202,1,0,0,0,44,210,1,0,0,0,46,215,1,0,
        0,0,48,223,1,0,0,0,50,234,1,0,0,0,52,251,1,0,0,0,54,253,1,0,0,0,
        56,57,3,2,1,0,57,58,5,0,0,1,58,1,1,0,0,0,59,60,5,1,0,0,60,65,5,51,
        0,0,61,62,5,41,0,0,62,63,3,14,7,0,63,64,5,42,0,0,64,66,1,0,0,0,65,
        61,1,0,0,0,65,66,1,0,0,0,66,67,1,0,0,0,67,68,5,45,0,0,68,69,3,4,
        2,0,69,70,5,46,0,0,70,3,1,0,0,0,71,73,3,6,3,0,72,71,1,0,0,0,72,73,
        1,0,0,0,73,75,1,0,0,0,74,76,3,10,5,0,75,74,1,0,0,0,75,76,1,0,0,0,
        76,77,1,0,0,0,77,78,3,18,9,0,78,5,1,0,0,0,79,81,5,2,0,0,80,82,3,
        8,4,0,81,80,1,0,0,0,82,83,1,0,0,0,83,81,1,0,0,0,83,84,1,0,0,0,84,
        7,1,0,0,0,85,86,5,51,0,0,86,87,5,34,0,0,87,88,3,38,19,0,88,89,5,
        45,0,0,89,9,1,0,0,0,90,92,5,3,0,0,91,93,3,12,6,0,92,91,1,0,0,0,93,
        94,1,0,0,0,94,92,1,0,0,0,94,95,1,0,0,0,95,11,1,0,0,0,96,97,3,14,
        7,0,97,98,5,44,0,0,98,101,3,16,8,0,99,100,5,30,0,0,100,102,3,38,
        19,0,101,99,1,0,0,0,101,102,1,0,0,0,102,103,1,0,0,0,103,104,5,45,
        0,0,104,13,1,0,0,0,105,110,5,51,0,0,106,107,5,43,0,0,107,109,5,51,
        0,0,108,106,1,0,0,0,109,112,1,0,0,0,110,108,1,0,0,0,110,111,1,0,
        0,0,111,15,1,0,0,0,112,110,1,0,0,0,113,114,7,0,0,0,114,17,1,0,0,
        0,115,117,5,4,0,0,116,118,3,20,10,0,117,116,1,0,0,0,117,118,1,0,
        0,0,118,119,1,0,0,0,119,120,5,5,0,0,120,19,1,0,0,0,121,126,3,22,
        11,0,122,123,5,45,0,0,123,125,3,22,11,0,124,122,1,0,0,0,125,128,
        1,0,0,0,126,124,1,0,0,0,126,127,1,0,0,0,127,130,1,0,0,0,128,126,
        1,0,0,0,129,131,5,45,0,0,130,129,1,0,0,0,130,131,1,0,0,0,131,21,
        1,0,0,0,132,142,3,18,9,0,133,142,3,24,12,0,134,142,3,26,13,0,135,
        142,3,28,14,0,136,142,3,30,15,0,137,142,3,32,16,0,138,142,3,34,17,
        0,139,142,5,16,0,0,140,142,5,17,0,0,141,132,1,0,0,0,141,133,1,0,
        0,0,141,134,1,0,0,0,141,135,1,0,0,0,141,136,1,0,0,0,141,137,1,0,
        0,0,141,138,1,0,0,0,141,139,1,0,0,0,141,140,1,0,0,0,142,23,1,0,0,
        0,143,144,5,51,0,0,144,145,5,30,0,0,145,146,3,38,19,0,146,25,1,0,
        0,0,147,153,5,51,0,0,148,150,5,41,0,0,149,151,3,36,18,0,150,149,
        1,0,0,0,150,151,1,0,0,0,151,152,1,0,0,0,152,154,5,42,0,0,153,148,
        1,0,0,0,153,154,1,0,0,0,154,27,1,0,0,0,155,156,5,6,0,0,156,157,3,
        38,19,0,157,158,5,7,0,0,158,161,3,22,11,0,159,160,5,8,0,0,160,162,
        3,22,11,0,161,159,1,0,0,0,161,162,1,0,0,0,162,29,1,0,0,0,163,164,
        5,9,0,0,164,165,3,38,19,0,165,166,5,10,0,0,166,167,3,22,11,0,167,
        31,1,0,0,0,168,170,5,11,0,0,169,171,3,20,10,0,170,169,1,0,0,0,170,
        171,1,0,0,0,171,172,1,0,0,0,172,173,5,12,0,0,173,174,3,38,19,0,174,
        33,1,0,0,0,175,176,5,13,0,0,176,177,5,51,0,0,177,178,5,30,0,0,178,
        179,3,38,19,0,179,180,7,1,0,0,180,181,3,38,19,0,181,182,5,10,0,0,
        182,183,3,22,11,0,183,35,1,0,0,0,184,189,3,38,19,0,185,186,5,43,
        0,0,186,188,3,38,19,0,187,185,1,0,0,0,188,191,1,0,0,0,189,187,1,
        0,0,0,189,190,1,0,0,0,190,37,1,0,0,0,191,189,1,0,0,0,192,193,3,40,
        20,0,193,39,1,0,0,0,194,199,3,42,21,0,195,196,7,2,0,0,196,198,3,
        42,21,0,197,195,1,0,0,0,198,201,1,0,0,0,199,197,1,0,0,0,199,200,
        1,0,0,0,200,41,1,0,0,0,201,199,1,0,0,0,202,207,3,44,22,0,203,204,
        5,26,0,0,204,206,3,44,22,0,205,203,1,0,0,0,206,209,1,0,0,0,207,205,
        1,0,0,0,207,208,1,0,0,0,208,43,1,0,0,0,209,207,1,0,0,0,210,213,3,
        46,23,0,211,212,7,3,0,0,212,214,3,46,23,0,213,211,1,0,0,0,213,214,
        1,0,0,0,214,45,1,0,0,0,215,220,3,48,24,0,216,217,7,4,0,0,217,219,
        3,48,24,0,218,216,1,0,0,0,219,222,1,0,0,0,220,218,1,0,0,0,220,221,
        1,0,0,0,221,47,1,0,0,0,222,220,1,0,0,0,223,228,3,50,25,0,224,225,
        7,5,0,0,225,227,3,50,25,0,226,224,1,0,0,0,227,230,1,0,0,0,228,226,
        1,0,0,0,228,229,1,0,0,0,229,49,1,0,0,0,230,228,1,0,0,0,231,232,7,
        6,0,0,232,235,3,50,25,0,233,235,3,52,26,0,234,231,1,0,0,0,234,233,
        1,0,0,0,235,51,1,0,0,0,236,252,3,54,27,0,237,252,5,50,0,0,238,252,
        5,22,0,0,239,252,5,23,0,0,240,241,5,51,0,0,241,243,5,41,0,0,242,
        244,3,36,18,0,243,242,1,0,0,0,243,244,1,0,0,0,244,245,1,0,0,0,245,
        252,5,42,0,0,246,252,5,51,0,0,247,248,5,41,0,0,248,249,3,38,19,0,
        249,250,5,42,0,0,250,252,1,0,0,0,251,236,1,0,0,0,251,237,1,0,0,0,
        251,238,1,0,0,0,251,239,1,0,0,0,251,240,1,0,0,0,251,246,1,0,0,0,
        251,247,1,0,0,0,252,53,1,0,0,0,253,254,7,7,0,0,254,55,1,0,0,0,24,
        65,72,75,83,94,101,110,117,126,130,141,150,153,161,170,189,199,207,
        213,220,228,234,243,251
    ]

class C64PascalParser ( Parser ):

    grammarFileName = "C64PascalParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'PROGRAM'", "'CONST'", "'VAR'", "'BEGIN'", 
                     "'END'", "'IF'", "'THEN'", "'ELSE'", "'WHILE'", "'DO'", 
                     "'REPEAT'", "'UNTIL'", "'FOR'", "'TO'", "'DOWNTO'", 
                     "'BREAK'", "'CONTINUE'", "'INTEGER'", "'BYTE'", "'CHAR'", 
                     "'BOOLEAN'", "'TRUE'", "'FALSE'", "'DIV'", "'MOD'", 
                     "'AND'", "'OR'", "'XOR'", "'NOT'", "':='", "'<='", 
                     "'>='", "'<>'", "'='", "'<'", "'>'", "'+'", "'-'", 
                     "'*'", "'/'", "'('", "')'", "','", "':'", "';'", "'.'" ]

    symbolicNames = [ "<INVALID>", "PROGRAM", "CONST", "VAR", "BEGIN", "END", 
                      "IF", "THEN", "ELSE", "WHILE", "DO", "REPEAT", "UNTIL", 
                      "FOR", "TO", "DOWNTO", "BREAK", "CONTINUE", "INTEGER_TYPE", 
                      "BYTE_TYPE", "CHAR_TYPE", "BOOLEAN_TYPE", "TRUE", 
                      "FALSE", "DIV", "MOD", "AND", "OR", "XOR", "NOT", 
                      "ASSIGN", "LE", "GE", "NE", "EQ", "LT", "GT", "PLUS", 
                      "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "COMMA", 
                      "COLON", "SEMI", "DOT", "HEX_INTEGER", "BINARY_INTEGER", 
                      "DECIMAL_INTEGER", "STRING_LITERAL", "IDENTIFIER", 
                      "BRACE_COMMENT", "PAREN_COMMENT", "LINE_COMMENT", 
                      "WS" ]

    RULE_compilationUnit = 0
    RULE_programUnit = 1
    RULE_block = 2
    RULE_constSection = 3
    RULE_constDefinition = 4
    RULE_varSection = 5
    RULE_varDeclaration = 6
    RULE_identifierList = 7
    RULE_typeIdentifier = 8
    RULE_compoundStatement = 9
    RULE_statementSequence = 10
    RULE_statement = 11
    RULE_assignmentStatement = 12
    RULE_callStatement = 13
    RULE_ifStatement = 14
    RULE_whileStatement = 15
    RULE_repeatStatement = 16
    RULE_forStatement = 17
    RULE_argumentList = 18
    RULE_expression = 19
    RULE_orExpression = 20
    RULE_andExpression = 21
    RULE_comparisonExpression = 22
    RULE_additiveExpression = 23
    RULE_multiplicativeExpression = 24
    RULE_unaryExpression = 25
    RULE_primaryExpression = 26
    RULE_integerLiteral = 27

    ruleNames =  [ "compilationUnit", "programUnit", "block", "constSection", 
                   "constDefinition", "varSection", "varDeclaration", "identifierList", 
                   "typeIdentifier", "compoundStatement", "statementSequence", 
                   "statement", "assignmentStatement", "callStatement", 
                   "ifStatement", "whileStatement", "repeatStatement", "forStatement", 
                   "argumentList", "expression", "orExpression", "andExpression", 
                   "comparisonExpression", "additiveExpression", "multiplicativeExpression", 
                   "unaryExpression", "primaryExpression", "integerLiteral" ]

    EOF = Token.EOF
    PROGRAM=1
    CONST=2
    VAR=3
    BEGIN=4
    END=5
    IF=6
    THEN=7
    ELSE=8
    WHILE=9
    DO=10
    REPEAT=11
    UNTIL=12
    FOR=13
    TO=14
    DOWNTO=15
    BREAK=16
    CONTINUE=17
    INTEGER_TYPE=18
    BYTE_TYPE=19
    CHAR_TYPE=20
    BOOLEAN_TYPE=21
    TRUE=22
    FALSE=23
    DIV=24
    MOD=25
    AND=26
    OR=27
    XOR=28
    NOT=29
    ASSIGN=30
    LE=31
    GE=32
    NE=33
    EQ=34
    LT=35
    GT=36
    PLUS=37
    MINUS=38
    STAR=39
    SLASH=40
    LPAREN=41
    RPAREN=42
    COMMA=43
    COLON=44
    SEMI=45
    DOT=46
    HEX_INTEGER=47
    BINARY_INTEGER=48
    DECIMAL_INTEGER=49
    STRING_LITERAL=50
    IDENTIFIER=51
    BRACE_COMMENT=52
    PAREN_COMMENT=53
    LINE_COMMENT=54
    WS=55

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class CompilationUnitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def programUnit(self):
            return self.getTypedRuleContext(C64PascalParser.ProgramUnitContext,0)


        def EOF(self):
            return self.getToken(C64PascalParser.EOF, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_compilationUnit

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompilationUnit" ):
                return visitor.visitCompilationUnit(self)
            else:
                return visitor.visitChildren(self)




    def compilationUnit(self):

        localctx = C64PascalParser.CompilationUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_compilationUnit)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 56
            self.programUnit()
            self.state = 57
            self.match(C64PascalParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ProgramUnitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PROGRAM(self):
            return self.getToken(C64PascalParser.PROGRAM, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def block(self):
            return self.getTypedRuleContext(C64PascalParser.BlockContext,0)


        def DOT(self):
            return self.getToken(C64PascalParser.DOT, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_programUnit

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitProgramUnit" ):
                return visitor.visitProgramUnit(self)
            else:
                return visitor.visitChildren(self)




    def programUnit(self):

        localctx = C64PascalParser.ProgramUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_programUnit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 59
            self.match(C64PascalParser.PROGRAM)
            self.state = 60
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 65
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==41:
                self.state = 61
                self.match(C64PascalParser.LPAREN)
                self.state = 62
                self.identifierList()
                self.state = 63
                self.match(C64PascalParser.RPAREN)


            self.state = 67
            self.match(C64PascalParser.SEMI)
            self.state = 68
            self.block()
            self.state = 69
            self.match(C64PascalParser.DOT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BlockContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def constSection(self):
            return self.getTypedRuleContext(C64PascalParser.ConstSectionContext,0)


        def varSection(self):
            return self.getTypedRuleContext(C64PascalParser.VarSectionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_block

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlock" ):
                return visitor.visitBlock(self)
            else:
                return visitor.visitChildren(self)




    def block(self):

        localctx = C64PascalParser.BlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_block)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 72
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==2:
                self.state = 71
                self.constSection()


            self.state = 75
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==3:
                self.state = 74
                self.varSection()


            self.state = 77
            self.compoundStatement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CONST(self):
            return self.getToken(C64PascalParser.CONST, 0)

        def constDefinition(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ConstDefinitionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ConstDefinitionContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_constSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstSection" ):
                return visitor.visitConstSection(self)
            else:
                return visitor.visitChildren(self)




    def constSection(self):

        localctx = C64PascalParser.ConstSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_constSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 79
            self.match(C64PascalParser.CONST)
            self.state = 81 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 80
                self.constDefinition()
                self.state = 83 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==51):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstDefinitionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def EQ(self):
            return self.getToken(C64PascalParser.EQ, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_constDefinition

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstDefinition" ):
                return visitor.visitConstDefinition(self)
            else:
                return visitor.visitChildren(self)




    def constDefinition(self):

        localctx = C64PascalParser.ConstDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_constDefinition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 85
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 86
            self.match(C64PascalParser.EQ)
            self.state = 87
            self.expression()
            self.state = 88
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VarSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VAR(self):
            return self.getToken(C64PascalParser.VAR, 0)

        def varDeclaration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.VarDeclarationContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.VarDeclarationContext,i)


        def getRuleIndex(self):
            return C64PascalParser.RULE_varSection

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarSection" ):
                return visitor.visitVarSection(self)
            else:
                return visitor.visitChildren(self)




    def varSection(self):

        localctx = C64PascalParser.VarSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_varSection)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 90
            self.match(C64PascalParser.VAR)
            self.state = 92 
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 91
                self.varDeclaration()
                self.state = 94 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la==51):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VarDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def identifierList(self):
            return self.getTypedRuleContext(C64PascalParser.IdentifierListContext,0)


        def COLON(self):
            return self.getToken(C64PascalParser.COLON, 0)

        def typeIdentifier(self):
            return self.getTypedRuleContext(C64PascalParser.TypeIdentifierContext,0)


        def SEMI(self):
            return self.getToken(C64PascalParser.SEMI, 0)

        def ASSIGN(self):
            return self.getToken(C64PascalParser.ASSIGN, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_varDeclaration

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVarDeclaration" ):
                return visitor.visitVarDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def varDeclaration(self):

        localctx = C64PascalParser.VarDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_varDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 96
            self.identifierList()
            self.state = 97
            self.match(C64PascalParser.COLON)
            self.state = 98
            self.typeIdentifier()
            self.state = 101
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==30:
                self.state = 99
                self.match(C64PascalParser.ASSIGN)
                self.state = 100
                self.expression()


            self.state = 103
            self.match(C64PascalParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IdentifierListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.IDENTIFIER)
            else:
                return self.getToken(C64PascalParser.IDENTIFIER, i)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.COMMA)
            else:
                return self.getToken(C64PascalParser.COMMA, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_identifierList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifierList" ):
                return visitor.visitIdentifierList(self)
            else:
                return visitor.visitChildren(self)




    def identifierList(self):

        localctx = C64PascalParser.IdentifierListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_identifierList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 105
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 110
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==43:
                self.state = 106
                self.match(C64PascalParser.COMMA)
                self.state = 107
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 112
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeIdentifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INTEGER_TYPE(self):
            return self.getToken(C64PascalParser.INTEGER_TYPE, 0)

        def BYTE_TYPE(self):
            return self.getToken(C64PascalParser.BYTE_TYPE, 0)

        def CHAR_TYPE(self):
            return self.getToken(C64PascalParser.CHAR_TYPE, 0)

        def BOOLEAN_TYPE(self):
            return self.getToken(C64PascalParser.BOOLEAN_TYPE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_typeIdentifier

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeIdentifier" ):
                return visitor.visitTypeIdentifier(self)
            else:
                return visitor.visitChildren(self)




    def typeIdentifier(self):

        localctx = C64PascalParser.TypeIdentifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_typeIdentifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 113
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 3932160) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CompoundStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def BEGIN(self):
            return self.getToken(C64PascalParser.BEGIN, 0)

        def END(self):
            return self.getToken(C64PascalParser.END, 0)

        def statementSequence(self):
            return self.getTypedRuleContext(C64PascalParser.StatementSequenceContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_compoundStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompoundStatement" ):
                return visitor.visitCompoundStatement(self)
            else:
                return visitor.visitChildren(self)




    def compoundStatement(self):

        localctx = C64PascalParser.CompoundStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_compoundStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 115
            self.match(C64PascalParser.BEGIN)
            self.state = 117
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 2251799813892688) != 0):
                self.state = 116
                self.statementSequence()


            self.state = 119
            self.match(C64PascalParser.END)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementSequenceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.StatementContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.StatementContext,i)


        def SEMI(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SEMI)
            else:
                return self.getToken(C64PascalParser.SEMI, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_statementSequence

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStatementSequence" ):
                return visitor.visitStatementSequence(self)
            else:
                return visitor.visitChildren(self)




    def statementSequence(self):

        localctx = C64PascalParser.StatementSequenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_statementSequence)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 121
            self.statement()
            self.state = 126
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,8,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 122
                    self.match(C64PascalParser.SEMI)
                    self.state = 123
                    self.statement() 
                self.state = 128
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,8,self._ctx)

            self.state = 130
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==45:
                self.state = 129
                self.match(C64PascalParser.SEMI)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return C64PascalParser.RULE_statement

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class CallStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def callStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CallStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallStatementNode" ):
                return visitor.visitCallStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class WhileStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def whileStatement(self):
            return self.getTypedRuleContext(C64PascalParser.WhileStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatementNode" ):
                return visitor.visitWhileStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class AssignmentStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def assignmentStatement(self):
            return self.getTypedRuleContext(C64PascalParser.AssignmentStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentStatementNode" ):
                return visitor.visitAssignmentStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class ForStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def forStatement(self):
            return self.getTypedRuleContext(C64PascalParser.ForStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStatementNode" ):
                return visitor.visitForStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class BreakStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def BREAK(self):
            return self.getToken(C64PascalParser.BREAK, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBreakStatementNode" ):
                return visitor.visitBreakStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class ContinueStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def CONTINUE(self):
            return self.getToken(C64PascalParser.CONTINUE, 0)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContinueStatementNode" ):
                return visitor.visitContinueStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class IfStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ifStatement(self):
            return self.getTypedRuleContext(C64PascalParser.IfStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatementNode" ):
                return visitor.visitIfStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class CompoundStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def compoundStatement(self):
            return self.getTypedRuleContext(C64PascalParser.CompoundStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompoundStatementNode" ):
                return visitor.visitCompoundStatementNode(self)
            else:
                return visitor.visitChildren(self)


    class RepeatStatementNodeContext(StatementContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a C64PascalParser.StatementContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def repeatStatement(self):
            return self.getTypedRuleContext(C64PascalParser.RepeatStatementContext,0)


        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatStatementNode" ):
                return visitor.visitRepeatStatementNode(self)
            else:
                return visitor.visitChildren(self)



    def statement(self):

        localctx = C64PascalParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_statement)
        try:
            self.state = 141
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,10,self._ctx)
            if la_ == 1:
                localctx = C64PascalParser.CompoundStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 132
                self.compoundStatement()
                pass

            elif la_ == 2:
                localctx = C64PascalParser.AssignmentStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 133
                self.assignmentStatement()
                pass

            elif la_ == 3:
                localctx = C64PascalParser.CallStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 134
                self.callStatement()
                pass

            elif la_ == 4:
                localctx = C64PascalParser.IfStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 135
                self.ifStatement()
                pass

            elif la_ == 5:
                localctx = C64PascalParser.WhileStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 136
                self.whileStatement()
                pass

            elif la_ == 6:
                localctx = C64PascalParser.RepeatStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 6)
                self.state = 137
                self.repeatStatement()
                pass

            elif la_ == 7:
                localctx = C64PascalParser.ForStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 7)
                self.state = 138
                self.forStatement()
                pass

            elif la_ == 8:
                localctx = C64PascalParser.BreakStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 8)
                self.state = 139
                self.match(C64PascalParser.BREAK)
                pass

            elif la_ == 9:
                localctx = C64PascalParser.ContinueStatementNodeContext(self, localctx)
                self.enterOuterAlt(localctx, 9)
                self.state = 140
                self.match(C64PascalParser.CONTINUE)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AssignmentStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def ASSIGN(self):
            return self.getToken(C64PascalParser.ASSIGN, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_assignmentStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentStatement" ):
                return visitor.visitAssignmentStatement(self)
            else:
                return visitor.visitChildren(self)




    def assignmentStatement(self):

        localctx = C64PascalParser.AssignmentStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_assignmentStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 143
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 144
            self.match(C64PascalParser.ASSIGN)
            self.state = 145
            self.expression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CallStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(C64PascalParser.ArgumentListContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_callStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCallStatement" ):
                return visitor.visitCallStatement(self)
            else:
                return visitor.visitChildren(self)




    def callStatement(self):

        localctx = C64PascalParser.CallStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_callStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 147
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 153
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==41:
                self.state = 148
                self.match(C64PascalParser.LPAREN)
                self.state = 150
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 4365474028584960) != 0):
                    self.state = 149
                    self.argumentList()


                self.state = 152
                self.match(C64PascalParser.RPAREN)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IfStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IF(self):
            return self.getToken(C64PascalParser.IF, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def THEN(self):
            return self.getToken(C64PascalParser.THEN, 0)

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.StatementContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.StatementContext,i)


        def ELSE(self):
            return self.getToken(C64PascalParser.ELSE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_ifStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatement" ):
                return visitor.visitIfStatement(self)
            else:
                return visitor.visitChildren(self)




    def ifStatement(self):

        localctx = C64PascalParser.IfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_ifStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 155
            self.match(C64PascalParser.IF)
            self.state = 156
            self.expression()
            self.state = 157
            self.match(C64PascalParser.THEN)
            self.state = 158
            self.statement()
            self.state = 161
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,13,self._ctx)
            if la_ == 1:
                self.state = 159
                self.match(C64PascalParser.ELSE)
                self.state = 160
                self.statement()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WhileStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def WHILE(self):
            return self.getToken(C64PascalParser.WHILE, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def DO(self):
            return self.getToken(C64PascalParser.DO, 0)

        def statement(self):
            return self.getTypedRuleContext(C64PascalParser.StatementContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_whileStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatement" ):
                return visitor.visitWhileStatement(self)
            else:
                return visitor.visitChildren(self)




    def whileStatement(self):

        localctx = C64PascalParser.WhileStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_whileStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 163
            self.match(C64PascalParser.WHILE)
            self.state = 164
            self.expression()
            self.state = 165
            self.match(C64PascalParser.DO)
            self.state = 166
            self.statement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RepeatStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def REPEAT(self):
            return self.getToken(C64PascalParser.REPEAT, 0)

        def UNTIL(self):
            return self.getToken(C64PascalParser.UNTIL, 0)

        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def statementSequence(self):
            return self.getTypedRuleContext(C64PascalParser.StatementSequenceContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_repeatStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitRepeatStatement" ):
                return visitor.visitRepeatStatement(self)
            else:
                return visitor.visitChildren(self)




    def repeatStatement(self):

        localctx = C64PascalParser.RepeatStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_repeatStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 168
            self.match(C64PascalParser.REPEAT)
            self.state = 170
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 2251799813892688) != 0):
                self.state = 169
                self.statementSequence()


            self.state = 172
            self.match(C64PascalParser.UNTIL)
            self.state = 173
            self.expression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ForStatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FOR(self):
            return self.getToken(C64PascalParser.FOR, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def ASSIGN(self):
            return self.getToken(C64PascalParser.ASSIGN, 0)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ExpressionContext,i)


        def DO(self):
            return self.getToken(C64PascalParser.DO, 0)

        def statement(self):
            return self.getTypedRuleContext(C64PascalParser.StatementContext,0)


        def TO(self):
            return self.getToken(C64PascalParser.TO, 0)

        def DOWNTO(self):
            return self.getToken(C64PascalParser.DOWNTO, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_forStatement

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitForStatement" ):
                return visitor.visitForStatement(self)
            else:
                return visitor.visitChildren(self)




    def forStatement(self):

        localctx = C64PascalParser.ForStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_forStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 175
            self.match(C64PascalParser.FOR)
            self.state = 176
            self.match(C64PascalParser.IDENTIFIER)
            self.state = 177
            self.match(C64PascalParser.ASSIGN)
            self.state = 178
            self.expression()
            self.state = 179
            _la = self._input.LA(1)
            if not(_la==14 or _la==15):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
            self.state = 180
            self.expression()
            self.state = 181
            self.match(C64PascalParser.DO)
            self.state = 182
            self.statement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArgumentListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ExpressionContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.COMMA)
            else:
                return self.getToken(C64PascalParser.COMMA, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_argumentList

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitArgumentList" ):
                return visitor.visitArgumentList(self)
            else:
                return visitor.visitChildren(self)




    def argumentList(self):

        localctx = C64PascalParser.ArgumentListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_argumentList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 184
            self.expression()
            self.state = 189
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==43:
                self.state = 185
                self.match(C64PascalParser.COMMA)
                self.state = 186
                self.expression()
                self.state = 191
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def orExpression(self):
            return self.getTypedRuleContext(C64PascalParser.OrExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_expression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpression" ):
                return visitor.visitExpression(self)
            else:
                return visitor.visitChildren(self)




    def expression(self):

        localctx = C64PascalParser.ExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_expression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 192
            self.orExpression()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OrExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def andExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.AndExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.AndExpressionContext,i)


        def OR(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.OR)
            else:
                return self.getToken(C64PascalParser.OR, i)

        def XOR(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.XOR)
            else:
                return self.getToken(C64PascalParser.XOR, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_orExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrExpression" ):
                return visitor.visitOrExpression(self)
            else:
                return visitor.visitChildren(self)




    def orExpression(self):

        localctx = C64PascalParser.OrExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_orExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 194
            self.andExpression()
            self.state = 199
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==27 or _la==28:
                self.state = 195
                _la = self._input.LA(1)
                if not(_la==27 or _la==28):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 196
                self.andExpression()
                self.state = 201
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AndExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def comparisonExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.ComparisonExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.ComparisonExpressionContext,i)


        def AND(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.AND)
            else:
                return self.getToken(C64PascalParser.AND, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_andExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAndExpression" ):
                return visitor.visitAndExpression(self)
            else:
                return visitor.visitChildren(self)




    def andExpression(self):

        localctx = C64PascalParser.AndExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_andExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 202
            self.comparisonExpression()
            self.state = 207
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==26:
                self.state = 203
                self.match(C64PascalParser.AND)
                self.state = 204
                self.comparisonExpression()
                self.state = 209
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ComparisonExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def additiveExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.AdditiveExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.AdditiveExpressionContext,i)


        def EQ(self):
            return self.getToken(C64PascalParser.EQ, 0)

        def NE(self):
            return self.getToken(C64PascalParser.NE, 0)

        def LT(self):
            return self.getToken(C64PascalParser.LT, 0)

        def LE(self):
            return self.getToken(C64PascalParser.LE, 0)

        def GT(self):
            return self.getToken(C64PascalParser.GT, 0)

        def GE(self):
            return self.getToken(C64PascalParser.GE, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_comparisonExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitComparisonExpression" ):
                return visitor.visitComparisonExpression(self)
            else:
                return visitor.visitChildren(self)




    def comparisonExpression(self):

        localctx = C64PascalParser.ComparisonExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_comparisonExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 210
            self.additiveExpression()
            self.state = 213
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 135291469824) != 0):
                self.state = 211
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 135291469824) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 212
                self.additiveExpression()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AdditiveExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def multiplicativeExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.MultiplicativeExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.MultiplicativeExpressionContext,i)


        def PLUS(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.PLUS)
            else:
                return self.getToken(C64PascalParser.PLUS, i)

        def MINUS(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.MINUS)
            else:
                return self.getToken(C64PascalParser.MINUS, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_additiveExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAdditiveExpression" ):
                return visitor.visitAdditiveExpression(self)
            else:
                return visitor.visitChildren(self)




    def additiveExpression(self):

        localctx = C64PascalParser.AdditiveExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_additiveExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 215
            self.multiplicativeExpression()
            self.state = 220
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==37 or _la==38:
                self.state = 216
                _la = self._input.LA(1)
                if not(_la==37 or _la==38):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 217
                self.multiplicativeExpression()
                self.state = 222
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MultiplicativeExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def unaryExpression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(C64PascalParser.UnaryExpressionContext)
            else:
                return self.getTypedRuleContext(C64PascalParser.UnaryExpressionContext,i)


        def STAR(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.STAR)
            else:
                return self.getToken(C64PascalParser.STAR, i)

        def SLASH(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.SLASH)
            else:
                return self.getToken(C64PascalParser.SLASH, i)

        def DIV(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.DIV)
            else:
                return self.getToken(C64PascalParser.DIV, i)

        def MOD(self, i:int=None):
            if i is None:
                return self.getTokens(C64PascalParser.MOD)
            else:
                return self.getToken(C64PascalParser.MOD, i)

        def getRuleIndex(self):
            return C64PascalParser.RULE_multiplicativeExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMultiplicativeExpression" ):
                return visitor.visitMultiplicativeExpression(self)
            else:
                return visitor.visitChildren(self)




    def multiplicativeExpression(self):

        localctx = C64PascalParser.MultiplicativeExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_multiplicativeExpression)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 223
            self.unaryExpression()
            self.state = 228
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 1649317773312) != 0):
                self.state = 224
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 1649317773312) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 225
                self.unaryExpression()
                self.state = 230
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class UnaryExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def unaryExpression(self):
            return self.getTypedRuleContext(C64PascalParser.UnaryExpressionContext,0)


        def PLUS(self):
            return self.getToken(C64PascalParser.PLUS, 0)

        def MINUS(self):
            return self.getToken(C64PascalParser.MINUS, 0)

        def NOT(self):
            return self.getToken(C64PascalParser.NOT, 0)

        def primaryExpression(self):
            return self.getTypedRuleContext(C64PascalParser.PrimaryExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_unaryExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitUnaryExpression" ):
                return visitor.visitUnaryExpression(self)
            else:
                return visitor.visitChildren(self)




    def unaryExpression(self):

        localctx = C64PascalParser.UnaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_unaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 234
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [29, 37, 38]:
                self.enterOuterAlt(localctx, 1)
                self.state = 231
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 412853731328) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 232
                self.unaryExpression()
                pass
            elif token in [22, 23, 41, 47, 48, 49, 50, 51]:
                self.enterOuterAlt(localctx, 2)
                self.state = 233
                self.primaryExpression()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PrimaryExpressionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def integerLiteral(self):
            return self.getTypedRuleContext(C64PascalParser.IntegerLiteralContext,0)


        def STRING_LITERAL(self):
            return self.getToken(C64PascalParser.STRING_LITERAL, 0)

        def TRUE(self):
            return self.getToken(C64PascalParser.TRUE, 0)

        def FALSE(self):
            return self.getToken(C64PascalParser.FALSE, 0)

        def IDENTIFIER(self):
            return self.getToken(C64PascalParser.IDENTIFIER, 0)

        def LPAREN(self):
            return self.getToken(C64PascalParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(C64PascalParser.RPAREN, 0)

        def argumentList(self):
            return self.getTypedRuleContext(C64PascalParser.ArgumentListContext,0)


        def expression(self):
            return self.getTypedRuleContext(C64PascalParser.ExpressionContext,0)


        def getRuleIndex(self):
            return C64PascalParser.RULE_primaryExpression

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPrimaryExpression" ):
                return visitor.visitPrimaryExpression(self)
            else:
                return visitor.visitChildren(self)




    def primaryExpression(self):

        localctx = C64PascalParser.PrimaryExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_primaryExpression)
        self._la = 0 # Token type
        try:
            self.state = 251
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,23,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 236
                self.integerLiteral()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 237
                self.match(C64PascalParser.STRING_LITERAL)
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 238
                self.match(C64PascalParser.TRUE)
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 239
                self.match(C64PascalParser.FALSE)
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 240
                self.match(C64PascalParser.IDENTIFIER)
                self.state = 241
                self.match(C64PascalParser.LPAREN)
                self.state = 243
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 4365474028584960) != 0):
                    self.state = 242
                    self.argumentList()


                self.state = 245
                self.match(C64PascalParser.RPAREN)
                pass

            elif la_ == 6:
                self.enterOuterAlt(localctx, 6)
                self.state = 246
                self.match(C64PascalParser.IDENTIFIER)
                pass

            elif la_ == 7:
                self.enterOuterAlt(localctx, 7)
                self.state = 247
                self.match(C64PascalParser.LPAREN)
                self.state = 248
                self.expression()
                self.state = 249
                self.match(C64PascalParser.RPAREN)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IntegerLiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def HEX_INTEGER(self):
            return self.getToken(C64PascalParser.HEX_INTEGER, 0)

        def BINARY_INTEGER(self):
            return self.getToken(C64PascalParser.BINARY_INTEGER, 0)

        def DECIMAL_INTEGER(self):
            return self.getToken(C64PascalParser.DECIMAL_INTEGER, 0)

        def getRuleIndex(self):
            return C64PascalParser.RULE_integerLiteral

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIntegerLiteral" ):
                return visitor.visitIntegerLiteral(self)
            else:
                return visitor.visitChildren(self)




    def integerLiteral(self):

        localctx = C64PascalParser.IntegerLiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_integerLiteral)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 253
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 985162418487296) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx






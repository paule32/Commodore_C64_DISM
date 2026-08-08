# Generated from gramm/cc/CppDocParser.g4 by ANTLR 4.13.2
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
        4,1,27,163,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,2,13,7,13,
        2,14,7,14,2,15,7,15,2,16,7,16,2,17,7,17,2,18,7,18,1,0,5,0,40,8,0,
        10,0,12,0,43,9,0,1,0,1,0,1,1,1,1,3,1,49,8,1,1,2,1,2,1,2,3,2,54,8,
        2,1,2,1,2,1,2,1,2,3,2,60,8,2,1,3,1,3,1,4,1,4,1,4,1,4,5,4,68,8,4,
        10,4,12,4,71,9,4,1,5,3,5,74,8,5,1,5,1,5,1,6,5,6,79,8,6,10,6,12,6,
        82,9,6,1,7,1,7,1,7,1,7,1,7,3,7,89,8,7,1,8,1,8,1,8,1,9,1,9,1,10,5,
        10,97,8,10,10,10,12,10,100,9,10,1,10,3,10,103,8,10,1,10,1,10,1,10,
        3,10,108,8,10,1,10,1,10,3,10,112,8,10,1,10,1,10,1,11,1,11,1,11,1,
        11,1,12,1,12,1,12,5,12,123,8,12,10,12,12,12,126,9,12,1,13,1,13,3,
        13,130,8,13,1,14,1,14,1,15,1,15,1,15,3,15,137,8,15,1,16,1,16,5,16,
        141,8,16,10,16,12,16,144,9,16,1,17,1,17,1,17,1,17,1,17,1,17,5,17,
        152,8,17,10,17,12,17,155,9,17,1,17,1,17,3,17,159,8,17,1,18,1,18,
        1,18,0,0,19,0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,
        0,4,1,0,1,2,1,0,3,5,2,0,6,7,9,9,2,0,10,10,14,27,165,0,41,1,0,0,0,
        2,48,1,0,0,0,4,50,1,0,0,0,6,61,1,0,0,0,8,63,1,0,0,0,10,73,1,0,0,
        0,12,80,1,0,0,0,14,88,1,0,0,0,16,90,1,0,0,0,18,93,1,0,0,0,20,98,
        1,0,0,0,22,115,1,0,0,0,24,119,1,0,0,0,26,127,1,0,0,0,28,131,1,0,
        0,0,30,136,1,0,0,0,32,138,1,0,0,0,34,158,1,0,0,0,36,160,1,0,0,0,
        38,40,3,2,1,0,39,38,1,0,0,0,40,43,1,0,0,0,41,39,1,0,0,0,41,42,1,
        0,0,0,42,44,1,0,0,0,43,41,1,0,0,0,44,45,5,0,0,1,45,1,1,0,0,0,46,
        49,3,4,2,0,47,49,3,36,18,0,48,46,1,0,0,0,48,47,1,0,0,0,49,3,1,0,
        0,0,50,51,3,6,3,0,51,53,5,10,0,0,52,54,3,8,4,0,53,52,1,0,0,0,53,
        54,1,0,0,0,54,55,1,0,0,0,55,56,5,14,0,0,56,57,3,12,6,0,57,59,5,15,
        0,0,58,60,5,18,0,0,59,58,1,0,0,0,59,60,1,0,0,0,60,5,1,0,0,0,61,62,
        7,0,0,0,62,7,1,0,0,0,63,64,5,19,0,0,64,69,3,10,5,0,65,66,5,20,0,
        0,66,68,3,10,5,0,67,65,1,0,0,0,68,71,1,0,0,0,69,67,1,0,0,0,69,70,
        1,0,0,0,70,9,1,0,0,0,71,69,1,0,0,0,72,74,3,18,9,0,73,72,1,0,0,0,
        73,74,1,0,0,0,74,75,1,0,0,0,75,76,3,32,16,0,76,11,1,0,0,0,77,79,
        3,14,7,0,78,77,1,0,0,0,79,82,1,0,0,0,80,78,1,0,0,0,80,81,1,0,0,0,
        81,13,1,0,0,0,82,80,1,0,0,0,83,89,3,16,8,0,84,89,3,20,10,0,85,89,
        3,22,11,0,86,89,3,4,2,0,87,89,3,36,18,0,88,83,1,0,0,0,88,84,1,0,
        0,0,88,85,1,0,0,0,88,86,1,0,0,0,88,87,1,0,0,0,89,15,1,0,0,0,90,91,
        3,18,9,0,91,92,5,19,0,0,92,17,1,0,0,0,93,94,7,1,0,0,94,19,1,0,0,
        0,95,97,3,28,14,0,96,95,1,0,0,0,97,100,1,0,0,0,98,96,1,0,0,0,98,
        99,1,0,0,0,99,102,1,0,0,0,100,98,1,0,0,0,101,103,3,32,16,0,102,101,
        1,0,0,0,102,103,1,0,0,0,103,104,1,0,0,0,104,105,3,30,15,0,105,107,
        5,16,0,0,106,108,3,24,12,0,107,106,1,0,0,0,107,108,1,0,0,0,108,109,
        1,0,0,0,109,111,5,17,0,0,110,112,5,8,0,0,111,110,1,0,0,0,111,112,
        1,0,0,0,112,113,1,0,0,0,113,114,5,18,0,0,114,21,1,0,0,0,115,116,
        3,32,16,0,116,117,5,10,0,0,117,118,5,18,0,0,118,23,1,0,0,0,119,124,
        3,26,13,0,120,121,5,20,0,0,121,123,3,26,13,0,122,120,1,0,0,0,123,
        126,1,0,0,0,124,122,1,0,0,0,124,125,1,0,0,0,125,25,1,0,0,0,126,124,
        1,0,0,0,127,129,3,32,16,0,128,130,5,10,0,0,129,128,1,0,0,0,129,130,
        1,0,0,0,130,27,1,0,0,0,131,132,7,2,0,0,132,29,1,0,0,0,133,137,5,
        10,0,0,134,135,5,26,0,0,135,137,5,10,0,0,136,133,1,0,0,0,136,134,
        1,0,0,0,137,31,1,0,0,0,138,142,5,10,0,0,139,141,3,34,17,0,140,139,
        1,0,0,0,141,144,1,0,0,0,142,140,1,0,0,0,142,143,1,0,0,0,143,33,1,
        0,0,0,144,142,1,0,0,0,145,159,5,21,0,0,146,159,5,22,0,0,147,148,
        5,23,0,0,148,153,3,32,16,0,149,150,5,20,0,0,150,152,3,32,16,0,151,
        149,1,0,0,0,152,155,1,0,0,0,153,151,1,0,0,0,153,154,1,0,0,0,154,
        156,1,0,0,0,155,153,1,0,0,0,156,157,5,24,0,0,157,159,1,0,0,0,158,
        145,1,0,0,0,158,146,1,0,0,0,158,147,1,0,0,0,159,35,1,0,0,0,160,161,
        7,3,0,0,161,37,1,0,0,0,18,41,48,53,59,69,73,80,88,98,102,107,111,
        124,129,136,142,153,158
    ]

class CppDocParser ( Parser ):

    grammarFileName = "CppDocParser.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'class'", "'struct'", "'public'", "'private'", 
                     "'protected'", "'virtual'", "'static'", "'const'", 
                     "'inline'", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "'{'", "'}'", "'('", "')'", "';'", "':'", 
                     "','", "'*'", "'&'", "'<'", "'>'", "'='", "'~'" ]

    symbolicNames = [ "<INVALID>", "CLASS", "STRUCT", "PUBLIC", "PRIVATE", 
                      "PROTECTED", "VIRTUAL", "STATIC", "CONST", "INLINE", 
                      "IDENT", "LINE_COMMENT", "BLOCK_COMMENT", "WS", "LBRACE", 
                      "RBRACE", "LPAREN", "RPAREN", "SEMI", "COLON", "COMMA", 
                      "STAR", "AMP", "LT", "GT", "EQ", "TILDE", "OTHER" ]

    RULE_translationUnit = 0
    RULE_declaration = 1
    RULE_classDeclaration = 2
    RULE_classKind = 3
    RULE_inheritance = 4
    RULE_inheritanceItem = 5
    RULE_classBody = 6
    RULE_classMember = 7
    RULE_accessSection = 8
    RULE_accessSpecifier = 9
    RULE_methodDeclaration = 10
    RULE_fieldDeclaration = 11
    RULE_parameterList = 12
    RULE_parameter = 13
    RULE_modifier = 14
    RULE_destructorOrName = 15
    RULE_typeName = 16
    RULE_typeSuffix = 17
    RULE_otherToken = 18

    ruleNames =  [ "translationUnit", "declaration", "classDeclaration", 
                   "classKind", "inheritance", "inheritanceItem", "classBody", 
                   "classMember", "accessSection", "accessSpecifier", "methodDeclaration", 
                   "fieldDeclaration", "parameterList", "parameter", "modifier", 
                   "destructorOrName", "typeName", "typeSuffix", "otherToken" ]

    EOF = Token.EOF
    CLASS=1
    STRUCT=2
    PUBLIC=3
    PRIVATE=4
    PROTECTED=5
    VIRTUAL=6
    STATIC=7
    CONST=8
    INLINE=9
    IDENT=10
    LINE_COMMENT=11
    BLOCK_COMMENT=12
    WS=13
    LBRACE=14
    RBRACE=15
    LPAREN=16
    RPAREN=17
    SEMI=18
    COLON=19
    COMMA=20
    STAR=21
    AMP=22
    LT=23
    GT=24
    EQ=25
    TILDE=26
    OTHER=27

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class TranslationUnitContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(CppDocParser.EOF, 0)

        def declaration(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.DeclarationContext)
            else:
                return self.getTypedRuleContext(CppDocParser.DeclarationContext,i)


        def getRuleIndex(self):
            return CppDocParser.RULE_translationUnit

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTranslationUnit" ):
                listener.enterTranslationUnit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTranslationUnit" ):
                listener.exitTranslationUnit(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTranslationUnit" ):
                return visitor.visitTranslationUnit(self)
            else:
                return visitor.visitChildren(self)




    def translationUnit(self):

        localctx = CppDocParser.TranslationUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_translationUnit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 41
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 268420102) != 0):
                self.state = 38
                self.declaration()
                self.state = 43
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 44
            self.match(CppDocParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def classDeclaration(self):
            return self.getTypedRuleContext(CppDocParser.ClassDeclarationContext,0)


        def otherToken(self):
            return self.getTypedRuleContext(CppDocParser.OtherTokenContext,0)


        def getRuleIndex(self):
            return CppDocParser.RULE_declaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDeclaration" ):
                listener.enterDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDeclaration" ):
                listener.exitDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDeclaration" ):
                return visitor.visitDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def declaration(self):

        localctx = CppDocParser.DeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_declaration)
        try:
            self.state = 48
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [1, 2]:
                self.enterOuterAlt(localctx, 1)
                self.state = 46
                self.classDeclaration()
                pass
            elif token in [10, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]:
                self.enterOuterAlt(localctx, 2)
                self.state = 47
                self.otherToken()
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


    class ClassDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def classKind(self):
            return self.getTypedRuleContext(CppDocParser.ClassKindContext,0)


        def IDENT(self):
            return self.getToken(CppDocParser.IDENT, 0)

        def LBRACE(self):
            return self.getToken(CppDocParser.LBRACE, 0)

        def classBody(self):
            return self.getTypedRuleContext(CppDocParser.ClassBodyContext,0)


        def RBRACE(self):
            return self.getToken(CppDocParser.RBRACE, 0)

        def inheritance(self):
            return self.getTypedRuleContext(CppDocParser.InheritanceContext,0)


        def SEMI(self):
            return self.getToken(CppDocParser.SEMI, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_classDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterClassDeclaration" ):
                listener.enterClassDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitClassDeclaration" ):
                listener.exitClassDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassDeclaration" ):
                return visitor.visitClassDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def classDeclaration(self):

        localctx = CppDocParser.ClassDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_classDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 50
            self.classKind()
            self.state = 51
            self.match(CppDocParser.IDENT)
            self.state = 53
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==19:
                self.state = 52
                self.inheritance()


            self.state = 55
            self.match(CppDocParser.LBRACE)
            self.state = 56
            self.classBody()
            self.state = 57
            self.match(CppDocParser.RBRACE)
            self.state = 59
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,3,self._ctx)
            if la_ == 1:
                self.state = 58
                self.match(CppDocParser.SEMI)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClassKindContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CLASS(self):
            return self.getToken(CppDocParser.CLASS, 0)

        def STRUCT(self):
            return self.getToken(CppDocParser.STRUCT, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_classKind

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterClassKind" ):
                listener.enterClassKind(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitClassKind" ):
                listener.exitClassKind(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassKind" ):
                return visitor.visitClassKind(self)
            else:
                return visitor.visitChildren(self)




    def classKind(self):

        localctx = CppDocParser.ClassKindContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_classKind)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 61
            _la = self._input.LA(1)
            if not(_la==1 or _la==2):
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


    class InheritanceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def COLON(self):
            return self.getToken(CppDocParser.COLON, 0)

        def inheritanceItem(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.InheritanceItemContext)
            else:
                return self.getTypedRuleContext(CppDocParser.InheritanceItemContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(CppDocParser.COMMA)
            else:
                return self.getToken(CppDocParser.COMMA, i)

        def getRuleIndex(self):
            return CppDocParser.RULE_inheritance

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInheritance" ):
                listener.enterInheritance(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInheritance" ):
                listener.exitInheritance(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInheritance" ):
                return visitor.visitInheritance(self)
            else:
                return visitor.visitChildren(self)




    def inheritance(self):

        localctx = CppDocParser.InheritanceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_inheritance)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 63
            self.match(CppDocParser.COLON)
            self.state = 64
            self.inheritanceItem()
            self.state = 69
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==20:
                self.state = 65
                self.match(CppDocParser.COMMA)
                self.state = 66
                self.inheritanceItem()
                self.state = 71
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class InheritanceItemContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def typeName(self):
            return self.getTypedRuleContext(CppDocParser.TypeNameContext,0)


        def accessSpecifier(self):
            return self.getTypedRuleContext(CppDocParser.AccessSpecifierContext,0)


        def getRuleIndex(self):
            return CppDocParser.RULE_inheritanceItem

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterInheritanceItem" ):
                listener.enterInheritanceItem(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitInheritanceItem" ):
                listener.exitInheritanceItem(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitInheritanceItem" ):
                return visitor.visitInheritanceItem(self)
            else:
                return visitor.visitChildren(self)




    def inheritanceItem(self):

        localctx = CppDocParser.InheritanceItemContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_inheritanceItem)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 73
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 56) != 0):
                self.state = 72
                self.accessSpecifier()


            self.state = 75
            self.typeName()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClassBodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def classMember(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.ClassMemberContext)
            else:
                return self.getTypedRuleContext(CppDocParser.ClassMemberContext,i)


        def getRuleIndex(self):
            return CppDocParser.RULE_classBody

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterClassBody" ):
                listener.enterClassBody(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitClassBody" ):
                listener.exitClassBody(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassBody" ):
                return visitor.visitClassBody(self)
            else:
                return visitor.visitChildren(self)




    def classBody(self):

        localctx = CppDocParser.ClassBodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_classBody)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 80
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,6,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 77
                    self.classMember() 
                self.state = 82
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,6,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClassMemberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def accessSection(self):
            return self.getTypedRuleContext(CppDocParser.AccessSectionContext,0)


        def methodDeclaration(self):
            return self.getTypedRuleContext(CppDocParser.MethodDeclarationContext,0)


        def fieldDeclaration(self):
            return self.getTypedRuleContext(CppDocParser.FieldDeclarationContext,0)


        def classDeclaration(self):
            return self.getTypedRuleContext(CppDocParser.ClassDeclarationContext,0)


        def otherToken(self):
            return self.getTypedRuleContext(CppDocParser.OtherTokenContext,0)


        def getRuleIndex(self):
            return CppDocParser.RULE_classMember

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterClassMember" ):
                listener.enterClassMember(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitClassMember" ):
                listener.exitClassMember(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitClassMember" ):
                return visitor.visitClassMember(self)
            else:
                return visitor.visitChildren(self)




    def classMember(self):

        localctx = CppDocParser.ClassMemberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_classMember)
        try:
            self.state = 88
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,7,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 83
                self.accessSection()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 84
                self.methodDeclaration()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 85
                self.fieldDeclaration()
                pass

            elif la_ == 4:
                self.enterOuterAlt(localctx, 4)
                self.state = 86
                self.classDeclaration()
                pass

            elif la_ == 5:
                self.enterOuterAlt(localctx, 5)
                self.state = 87
                self.otherToken()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AccessSectionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def accessSpecifier(self):
            return self.getTypedRuleContext(CppDocParser.AccessSpecifierContext,0)


        def COLON(self):
            return self.getToken(CppDocParser.COLON, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_accessSection

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAccessSection" ):
                listener.enterAccessSection(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAccessSection" ):
                listener.exitAccessSection(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAccessSection" ):
                return visitor.visitAccessSection(self)
            else:
                return visitor.visitChildren(self)




    def accessSection(self):

        localctx = CppDocParser.AccessSectionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_accessSection)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 90
            self.accessSpecifier()
            self.state = 91
            self.match(CppDocParser.COLON)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AccessSpecifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PUBLIC(self):
            return self.getToken(CppDocParser.PUBLIC, 0)

        def PRIVATE(self):
            return self.getToken(CppDocParser.PRIVATE, 0)

        def PROTECTED(self):
            return self.getToken(CppDocParser.PROTECTED, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_accessSpecifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAccessSpecifier" ):
                listener.enterAccessSpecifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAccessSpecifier" ):
                listener.exitAccessSpecifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAccessSpecifier" ):
                return visitor.visitAccessSpecifier(self)
            else:
                return visitor.visitChildren(self)




    def accessSpecifier(self):

        localctx = CppDocParser.AccessSpecifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_accessSpecifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 93
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 56) != 0)):
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


    class MethodDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def destructorOrName(self):
            return self.getTypedRuleContext(CppDocParser.DestructorOrNameContext,0)


        def LPAREN(self):
            return self.getToken(CppDocParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(CppDocParser.RPAREN, 0)

        def SEMI(self):
            return self.getToken(CppDocParser.SEMI, 0)

        def modifier(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.ModifierContext)
            else:
                return self.getTypedRuleContext(CppDocParser.ModifierContext,i)


        def typeName(self):
            return self.getTypedRuleContext(CppDocParser.TypeNameContext,0)


        def parameterList(self):
            return self.getTypedRuleContext(CppDocParser.ParameterListContext,0)


        def CONST(self):
            return self.getToken(CppDocParser.CONST, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_methodDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMethodDeclaration" ):
                listener.enterMethodDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMethodDeclaration" ):
                listener.exitMethodDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMethodDeclaration" ):
                return visitor.visitMethodDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def methodDeclaration(self):

        localctx = CppDocParser.MethodDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_methodDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 98
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 704) != 0):
                self.state = 95
                self.modifier()
                self.state = 100
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 102
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,9,self._ctx)
            if la_ == 1:
                self.state = 101
                self.typeName()


            self.state = 104
            self.destructorOrName()
            self.state = 105
            self.match(CppDocParser.LPAREN)
            self.state = 107
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==10:
                self.state = 106
                self.parameterList()


            self.state = 109
            self.match(CppDocParser.RPAREN)
            self.state = 111
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==8:
                self.state = 110
                self.match(CppDocParser.CONST)


            self.state = 113
            self.match(CppDocParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FieldDeclarationContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def typeName(self):
            return self.getTypedRuleContext(CppDocParser.TypeNameContext,0)


        def IDENT(self):
            return self.getToken(CppDocParser.IDENT, 0)

        def SEMI(self):
            return self.getToken(CppDocParser.SEMI, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_fieldDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFieldDeclaration" ):
                listener.enterFieldDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFieldDeclaration" ):
                listener.exitFieldDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFieldDeclaration" ):
                return visitor.visitFieldDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def fieldDeclaration(self):

        localctx = CppDocParser.FieldDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_fieldDeclaration)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 115
            self.typeName()
            self.state = 116
            self.match(CppDocParser.IDENT)
            self.state = 117
            self.match(CppDocParser.SEMI)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParameterListContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def parameter(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.ParameterContext)
            else:
                return self.getTypedRuleContext(CppDocParser.ParameterContext,i)


        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(CppDocParser.COMMA)
            else:
                return self.getToken(CppDocParser.COMMA, i)

        def getRuleIndex(self):
            return CppDocParser.RULE_parameterList

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParameterList" ):
                listener.enterParameterList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParameterList" ):
                listener.exitParameterList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParameterList" ):
                return visitor.visitParameterList(self)
            else:
                return visitor.visitChildren(self)




    def parameterList(self):

        localctx = CppDocParser.ParameterListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_parameterList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 119
            self.parameter()
            self.state = 124
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==20:
                self.state = 120
                self.match(CppDocParser.COMMA)
                self.state = 121
                self.parameter()
                self.state = 126
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParameterContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def typeName(self):
            return self.getTypedRuleContext(CppDocParser.TypeNameContext,0)


        def IDENT(self):
            return self.getToken(CppDocParser.IDENT, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_parameter

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParameter" ):
                listener.enterParameter(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParameter" ):
                listener.exitParameter(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParameter" ):
                return visitor.visitParameter(self)
            else:
                return visitor.visitChildren(self)




    def parameter(self):

        localctx = CppDocParser.ParameterContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_parameter)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 127
            self.typeName()
            self.state = 129
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==10:
                self.state = 128
                self.match(CppDocParser.IDENT)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ModifierContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VIRTUAL(self):
            return self.getToken(CppDocParser.VIRTUAL, 0)

        def STATIC(self):
            return self.getToken(CppDocParser.STATIC, 0)

        def INLINE(self):
            return self.getToken(CppDocParser.INLINE, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_modifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterModifier" ):
                listener.enterModifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitModifier" ):
                listener.exitModifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitModifier" ):
                return visitor.visitModifier(self)
            else:
                return visitor.visitChildren(self)




    def modifier(self):

        localctx = CppDocParser.ModifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_modifier)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 131
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 704) != 0)):
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


    class DestructorOrNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENT(self):
            return self.getToken(CppDocParser.IDENT, 0)

        def TILDE(self):
            return self.getToken(CppDocParser.TILDE, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_destructorOrName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDestructorOrName" ):
                listener.enterDestructorOrName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDestructorOrName" ):
                listener.exitDestructorOrName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitDestructorOrName" ):
                return visitor.visitDestructorOrName(self)
            else:
                return visitor.visitChildren(self)




    def destructorOrName(self):

        localctx = CppDocParser.DestructorOrNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_destructorOrName)
        try:
            self.state = 136
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [10]:
                self.enterOuterAlt(localctx, 1)
                self.state = 133
                self.match(CppDocParser.IDENT)
                pass
            elif token in [26]:
                self.enterOuterAlt(localctx, 2)
                self.state = 134
                self.match(CppDocParser.TILDE)
                self.state = 135
                self.match(CppDocParser.IDENT)
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


    class TypeNameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def IDENT(self):
            return self.getToken(CppDocParser.IDENT, 0)

        def typeSuffix(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.TypeSuffixContext)
            else:
                return self.getTypedRuleContext(CppDocParser.TypeSuffixContext,i)


        def getRuleIndex(self):
            return CppDocParser.RULE_typeName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeName" ):
                listener.enterTypeName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeName" ):
                listener.exitTypeName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeName" ):
                return visitor.visitTypeName(self)
            else:
                return visitor.visitChildren(self)




    def typeName(self):

        localctx = CppDocParser.TypeNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_typeName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 138
            self.match(CppDocParser.IDENT)
            self.state = 142
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & 14680064) != 0):
                self.state = 139
                self.typeSuffix()
                self.state = 144
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeSuffixContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STAR(self):
            return self.getToken(CppDocParser.STAR, 0)

        def AMP(self):
            return self.getToken(CppDocParser.AMP, 0)

        def LT(self):
            return self.getToken(CppDocParser.LT, 0)

        def typeName(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(CppDocParser.TypeNameContext)
            else:
                return self.getTypedRuleContext(CppDocParser.TypeNameContext,i)


        def GT(self):
            return self.getToken(CppDocParser.GT, 0)

        def COMMA(self, i:int=None):
            if i is None:
                return self.getTokens(CppDocParser.COMMA)
            else:
                return self.getToken(CppDocParser.COMMA, i)

        def getRuleIndex(self):
            return CppDocParser.RULE_typeSuffix

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeSuffix" ):
                listener.enterTypeSuffix(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeSuffix" ):
                listener.exitTypeSuffix(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeSuffix" ):
                return visitor.visitTypeSuffix(self)
            else:
                return visitor.visitChildren(self)




    def typeSuffix(self):

        localctx = CppDocParser.TypeSuffixContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_typeSuffix)
        self._la = 0 # Token type
        try:
            self.state = 158
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [21]:
                self.enterOuterAlt(localctx, 1)
                self.state = 145
                self.match(CppDocParser.STAR)
                pass
            elif token in [22]:
                self.enterOuterAlt(localctx, 2)
                self.state = 146
                self.match(CppDocParser.AMP)
                pass
            elif token in [23]:
                self.enterOuterAlt(localctx, 3)
                self.state = 147
                self.match(CppDocParser.LT)
                self.state = 148
                self.typeName()
                self.state = 153
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==20:
                    self.state = 149
                    self.match(CppDocParser.COMMA)
                    self.state = 150
                    self.typeName()
                    self.state = 155
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                self.state = 156
                self.match(CppDocParser.GT)
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


    class OtherTokenContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def OTHER(self):
            return self.getToken(CppDocParser.OTHER, 0)

        def IDENT(self):
            return self.getToken(CppDocParser.IDENT, 0)

        def SEMI(self):
            return self.getToken(CppDocParser.SEMI, 0)

        def COLON(self):
            return self.getToken(CppDocParser.COLON, 0)

        def COMMA(self):
            return self.getToken(CppDocParser.COMMA, 0)

        def LPAREN(self):
            return self.getToken(CppDocParser.LPAREN, 0)

        def RPAREN(self):
            return self.getToken(CppDocParser.RPAREN, 0)

        def LBRACE(self):
            return self.getToken(CppDocParser.LBRACE, 0)

        def RBRACE(self):
            return self.getToken(CppDocParser.RBRACE, 0)

        def STAR(self):
            return self.getToken(CppDocParser.STAR, 0)

        def AMP(self):
            return self.getToken(CppDocParser.AMP, 0)

        def LT(self):
            return self.getToken(CppDocParser.LT, 0)

        def GT(self):
            return self.getToken(CppDocParser.GT, 0)

        def EQ(self):
            return self.getToken(CppDocParser.EQ, 0)

        def TILDE(self):
            return self.getToken(CppDocParser.TILDE, 0)

        def getRuleIndex(self):
            return CppDocParser.RULE_otherToken

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOtherToken" ):
                listener.enterOtherToken(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOtherToken" ):
                listener.exitOtherToken(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOtherToken" ):
                return visitor.visitOtherToken(self)
            else:
                return visitor.visitChildren(self)




    def otherToken(self):

        localctx = CppDocParser.OtherTokenContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_otherToken)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 160
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & 268420096) != 0)):
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






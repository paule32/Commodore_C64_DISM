# Generated from gramm/cc/CppDocParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .CppDocParser import CppDocParser
else:
    from CppDocParser import CppDocParser

# This class defines a complete listener for a parse tree produced by CppDocParser.
class CppDocParserListener(ParseTreeListener):

    # Enter a parse tree produced by CppDocParser#translationUnit.
    def enterTranslationUnit(self, ctx:CppDocParser.TranslationUnitContext):
        pass

    # Exit a parse tree produced by CppDocParser#translationUnit.
    def exitTranslationUnit(self, ctx:CppDocParser.TranslationUnitContext):
        pass


    # Enter a parse tree produced by CppDocParser#declaration.
    def enterDeclaration(self, ctx:CppDocParser.DeclarationContext):
        pass

    # Exit a parse tree produced by CppDocParser#declaration.
    def exitDeclaration(self, ctx:CppDocParser.DeclarationContext):
        pass


    # Enter a parse tree produced by CppDocParser#classDeclaration.
    def enterClassDeclaration(self, ctx:CppDocParser.ClassDeclarationContext):
        pass

    # Exit a parse tree produced by CppDocParser#classDeclaration.
    def exitClassDeclaration(self, ctx:CppDocParser.ClassDeclarationContext):
        pass


    # Enter a parse tree produced by CppDocParser#classKind.
    def enterClassKind(self, ctx:CppDocParser.ClassKindContext):
        pass

    # Exit a parse tree produced by CppDocParser#classKind.
    def exitClassKind(self, ctx:CppDocParser.ClassKindContext):
        pass


    # Enter a parse tree produced by CppDocParser#inheritance.
    def enterInheritance(self, ctx:CppDocParser.InheritanceContext):
        pass

    # Exit a parse tree produced by CppDocParser#inheritance.
    def exitInheritance(self, ctx:CppDocParser.InheritanceContext):
        pass


    # Enter a parse tree produced by CppDocParser#inheritanceItem.
    def enterInheritanceItem(self, ctx:CppDocParser.InheritanceItemContext):
        pass

    # Exit a parse tree produced by CppDocParser#inheritanceItem.
    def exitInheritanceItem(self, ctx:CppDocParser.InheritanceItemContext):
        pass


    # Enter a parse tree produced by CppDocParser#classBody.
    def enterClassBody(self, ctx:CppDocParser.ClassBodyContext):
        pass

    # Exit a parse tree produced by CppDocParser#classBody.
    def exitClassBody(self, ctx:CppDocParser.ClassBodyContext):
        pass


    # Enter a parse tree produced by CppDocParser#classMember.
    def enterClassMember(self, ctx:CppDocParser.ClassMemberContext):
        pass

    # Exit a parse tree produced by CppDocParser#classMember.
    def exitClassMember(self, ctx:CppDocParser.ClassMemberContext):
        pass


    # Enter a parse tree produced by CppDocParser#accessSection.
    def enterAccessSection(self, ctx:CppDocParser.AccessSectionContext):
        pass

    # Exit a parse tree produced by CppDocParser#accessSection.
    def exitAccessSection(self, ctx:CppDocParser.AccessSectionContext):
        pass


    # Enter a parse tree produced by CppDocParser#accessSpecifier.
    def enterAccessSpecifier(self, ctx:CppDocParser.AccessSpecifierContext):
        pass

    # Exit a parse tree produced by CppDocParser#accessSpecifier.
    def exitAccessSpecifier(self, ctx:CppDocParser.AccessSpecifierContext):
        pass


    # Enter a parse tree produced by CppDocParser#methodDeclaration.
    def enterMethodDeclaration(self, ctx:CppDocParser.MethodDeclarationContext):
        pass

    # Exit a parse tree produced by CppDocParser#methodDeclaration.
    def exitMethodDeclaration(self, ctx:CppDocParser.MethodDeclarationContext):
        pass


    # Enter a parse tree produced by CppDocParser#fieldDeclaration.
    def enterFieldDeclaration(self, ctx:CppDocParser.FieldDeclarationContext):
        pass

    # Exit a parse tree produced by CppDocParser#fieldDeclaration.
    def exitFieldDeclaration(self, ctx:CppDocParser.FieldDeclarationContext):
        pass


    # Enter a parse tree produced by CppDocParser#parameterList.
    def enterParameterList(self, ctx:CppDocParser.ParameterListContext):
        pass

    # Exit a parse tree produced by CppDocParser#parameterList.
    def exitParameterList(self, ctx:CppDocParser.ParameterListContext):
        pass


    # Enter a parse tree produced by CppDocParser#parameter.
    def enterParameter(self, ctx:CppDocParser.ParameterContext):
        pass

    # Exit a parse tree produced by CppDocParser#parameter.
    def exitParameter(self, ctx:CppDocParser.ParameterContext):
        pass


    # Enter a parse tree produced by CppDocParser#modifier.
    def enterModifier(self, ctx:CppDocParser.ModifierContext):
        pass

    # Exit a parse tree produced by CppDocParser#modifier.
    def exitModifier(self, ctx:CppDocParser.ModifierContext):
        pass


    # Enter a parse tree produced by CppDocParser#destructorOrName.
    def enterDestructorOrName(self, ctx:CppDocParser.DestructorOrNameContext):
        pass

    # Exit a parse tree produced by CppDocParser#destructorOrName.
    def exitDestructorOrName(self, ctx:CppDocParser.DestructorOrNameContext):
        pass


    # Enter a parse tree produced by CppDocParser#typeName.
    def enterTypeName(self, ctx:CppDocParser.TypeNameContext):
        pass

    # Exit a parse tree produced by CppDocParser#typeName.
    def exitTypeName(self, ctx:CppDocParser.TypeNameContext):
        pass


    # Enter a parse tree produced by CppDocParser#typeSuffix.
    def enterTypeSuffix(self, ctx:CppDocParser.TypeSuffixContext):
        pass

    # Exit a parse tree produced by CppDocParser#typeSuffix.
    def exitTypeSuffix(self, ctx:CppDocParser.TypeSuffixContext):
        pass


    # Enter a parse tree produced by CppDocParser#otherToken.
    def enterOtherToken(self, ctx:CppDocParser.OtherTokenContext):
        pass

    # Exit a parse tree produced by CppDocParser#otherToken.
    def exitOtherToken(self, ctx:CppDocParser.OtherTokenContext):
        pass



del CppDocParser
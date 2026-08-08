# Generated from gramm/cc/CppDocParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .CppDocParser import CppDocParser
else:
    from CppDocParser import CppDocParser

# This class defines a complete generic visitor for a parse tree produced by CppDocParser.

class CppDocParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by CppDocParser#translationUnit.
    def visitTranslationUnit(self, ctx:CppDocParser.TranslationUnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#declaration.
    def visitDeclaration(self, ctx:CppDocParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#classDeclaration.
    def visitClassDeclaration(self, ctx:CppDocParser.ClassDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#classKind.
    def visitClassKind(self, ctx:CppDocParser.ClassKindContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#inheritance.
    def visitInheritance(self, ctx:CppDocParser.InheritanceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#inheritanceItem.
    def visitInheritanceItem(self, ctx:CppDocParser.InheritanceItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#classBody.
    def visitClassBody(self, ctx:CppDocParser.ClassBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#classMember.
    def visitClassMember(self, ctx:CppDocParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#accessSection.
    def visitAccessSection(self, ctx:CppDocParser.AccessSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#accessSpecifier.
    def visitAccessSpecifier(self, ctx:CppDocParser.AccessSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#methodDeclaration.
    def visitMethodDeclaration(self, ctx:CppDocParser.MethodDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#fieldDeclaration.
    def visitFieldDeclaration(self, ctx:CppDocParser.FieldDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#parameterList.
    def visitParameterList(self, ctx:CppDocParser.ParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#parameter.
    def visitParameter(self, ctx:CppDocParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#modifier.
    def visitModifier(self, ctx:CppDocParser.ModifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#destructorOrName.
    def visitDestructorOrName(self, ctx:CppDocParser.DestructorOrNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#typeName.
    def visitTypeName(self, ctx:CppDocParser.TypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#typeSuffix.
    def visitTypeSuffix(self, ctx:CppDocParser.TypeSuffixContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by CppDocParser#otherToken.
    def visitOtherToken(self, ctx:CppDocParser.OtherTokenContext):
        return self.visitChildren(ctx)



del CppDocParser
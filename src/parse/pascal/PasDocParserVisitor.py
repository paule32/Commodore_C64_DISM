# Generated from gramm/pascal/PasDocParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .PasDocParser import PasDocParser
else:
    from PasDocParser import PasDocParser

# This class defines a complete generic visitor for a parse tree produced by PasDocParser.

class PasDocParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PasDocParser#unitFile.
    def visitUnitFile(self, ctx:PasDocParser.UnitFileContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#programHeader.
    def visitProgramHeader(self, ctx:PasDocParser.ProgramHeaderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#unitHeader.
    def visitUnitHeader(self, ctx:PasDocParser.UnitHeaderContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#unitSection.
    def visitUnitSection(self, ctx:PasDocParser.UnitSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#interfaceSection.
    def visitInterfaceSection(self, ctx:PasDocParser.InterfaceSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#implementationSection.
    def visitImplementationSection(self, ctx:PasDocParser.ImplementationSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#usesSection.
    def visitUsesSection(self, ctx:PasDocParser.UsesSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#usesItem.
    def visitUsesItem(self, ctx:PasDocParser.UsesItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#declaration.
    def visitDeclaration(self, ctx:PasDocParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#implementationMethod.
    def visitImplementationMethod(self, ctx:PasDocParser.ImplementationMethodContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#qualifiedIdent.
    def visitQualifiedIdent(self, ctx:PasDocParser.QualifiedIdentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#methodBody.
    def visitMethodBody(self, ctx:PasDocParser.MethodBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#methodBodyToken.
    def visitMethodBodyToken(self, ctx:PasDocParser.MethodBodyTokenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#varSection.
    def visitVarSection(self, ctx:PasDocParser.VarSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#varDeclaration.
    def visitVarDeclaration(self, ctx:PasDocParser.VarDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#constSection.
    def visitConstSection(self, ctx:PasDocParser.ConstSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#constDeclaration.
    def visitConstDeclaration(self, ctx:PasDocParser.ConstDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#constItem.
    def visitConstItem(self, ctx:PasDocParser.ConstItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#constValue.
    def visitConstValue(self, ctx:PasDocParser.ConstValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#sign.
    def visitSign(self, ctx:PasDocParser.SignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#docComment.
    def visitDocComment(self, ctx:PasDocParser.DocCommentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#typeSection.
    def visitTypeSection(self, ctx:PasDocParser.TypeSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#typeDeclaration.
    def visitTypeDeclaration(self, ctx:PasDocParser.TypeDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#unknownTypeDeclaration.
    def visitUnknownTypeDeclaration(self, ctx:PasDocParser.UnknownTypeDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#unknownTypeToken.
    def visitUnknownTypeToken(self, ctx:PasDocParser.UnknownTypeTokenContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#classDeclaration.
    def visitClassDeclaration(self, ctx:PasDocParser.ClassDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#classType.
    def visitClassType(self, ctx:PasDocParser.ClassTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#classBaseList.
    def visitClassBaseList(self, ctx:PasDocParser.ClassBaseListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#classBody.
    def visitClassBody(self, ctx:PasDocParser.ClassBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#classMember.
    def visitClassMember(self, ctx:PasDocParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#recordDeclaration.
    def visitRecordDeclaration(self, ctx:PasDocParser.RecordDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#recordType.
    def visitRecordType(self, ctx:PasDocParser.RecordTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#recordBody.
    def visitRecordBody(self, ctx:PasDocParser.RecordBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#recordMember.
    def visitRecordMember(self, ctx:PasDocParser.RecordMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#arrayDeclaration.
    def visitArrayDeclaration(self, ctx:PasDocParser.ArrayDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#arrayType.
    def visitArrayType(self, ctx:PasDocParser.ArrayTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#arrayIndex.
    def visitArrayIndex(self, ctx:PasDocParser.ArrayIndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#setDeclaration.
    def visitSetDeclaration(self, ctx:PasDocParser.SetDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#setType.
    def visitSetType(self, ctx:PasDocParser.SetTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#enumDeclaration.
    def visitEnumDeclaration(self, ctx:PasDocParser.EnumDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#enumType.
    def visitEnumType(self, ctx:PasDocParser.EnumTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#enumItemTail.
    def visitEnumItemTail(self, ctx:PasDocParser.EnumItemTailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#enumItem.
    def visitEnumItem(self, ctx:PasDocParser.EnumItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#visibilitySection.
    def visitVisibilitySection(self, ctx:PasDocParser.VisibilitySectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#visibility.
    def visitVisibility(self, ctx:PasDocParser.VisibilityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#methodDeclaration.
    def visitMethodDeclaration(self, ctx:PasDocParser.MethodDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#methodDirectiveList.
    def visitMethodDirectiveList(self, ctx:PasDocParser.MethodDirectiveListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#methodKind.
    def visitMethodKind(self, ctx:PasDocParser.MethodKindContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#parameterList.
    def visitParameterList(self, ctx:PasDocParser.ParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#parameterDecl.
    def visitParameterDecl(self, ctx:PasDocParser.ParameterDeclContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#parameterItem.
    def visitParameterItem(self, ctx:PasDocParser.ParameterItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#parameterModifier.
    def visitParameterModifier(self, ctx:PasDocParser.ParameterModifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#returnType.
    def visitReturnType(self, ctx:PasDocParser.ReturnTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#methodDirective.
    def visitMethodDirective(self, ctx:PasDocParser.MethodDirectiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#propertyDeclaration.
    def visitPropertyDeclaration(self, ctx:PasDocParser.PropertyDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#propertyAccessor.
    def visitPropertyAccessor(self, ctx:PasDocParser.PropertyAccessorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#fieldDeclaration.
    def visitFieldDeclaration(self, ctx:PasDocParser.FieldDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#interfaceDeclaration.
    def visitInterfaceDeclaration(self, ctx:PasDocParser.InterfaceDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#interfaceBaseList.
    def visitInterfaceBaseList(self, ctx:PasDocParser.InterfaceBaseListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#interfaceBody.
    def visitInterfaceBody(self, ctx:PasDocParser.InterfaceBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#interfaceMember.
    def visitInterfaceMember(self, ctx:PasDocParser.InterfaceMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#genericParams.
    def visitGenericParams(self, ctx:PasDocParser.GenericParamsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#typeName.
    def visitTypeName(self, ctx:PasDocParser.TypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#genericTypeArgs.
    def visitGenericTypeArgs(self, ctx:PasDocParser.GenericTypeArgsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PasDocParser#otherToken.
    def visitOtherToken(self, ctx:PasDocParser.OtherTokenContext):
        return self.visitChildren(ctx)



del PasDocParser
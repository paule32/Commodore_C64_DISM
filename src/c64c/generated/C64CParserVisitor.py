# Generated from C64CParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .C64CParser import C64CParser
else:
    from C64CParser import C64CParser

# This class defines a complete generic visitor for a parse tree produced by C64CParser.

class C64CParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by C64CParser#translationUnit.
    def visitTranslationUnit(self, ctx:C64CParser.TranslationUnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#externalDeclaration.
    def visitExternalDeclaration(self, ctx:C64CParser.ExternalDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#functionDefinition.
    def visitFunctionDefinition(self, ctx:C64CParser.FunctionDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#functionPrototype.
    def visitFunctionPrototype(self, ctx:C64CParser.FunctionPrototypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#parameterList.
    def visitParameterList(self, ctx:C64CParser.ParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#parameterDeclaration.
    def visitParameterDeclaration(self, ctx:C64CParser.ParameterDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#declaration.
    def visitDeclaration(self, ctx:C64CParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#declarationQualifier.
    def visitDeclarationQualifier(self, ctx:C64CParser.DeclarationQualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#scalarTypedef.
    def visitScalarTypedef(self, ctx:C64CParser.ScalarTypedefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#structuredTypedef.
    def visitStructuredTypedef(self, ctx:C64CParser.StructuredTypedefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#structDeclaration.
    def visitStructDeclaration(self, ctx:C64CParser.StructDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#structMemberDeclaration.
    def visitStructMemberDeclaration(self, ctx:C64CParser.StructMemberDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#initDeclaratorList.
    def visitInitDeclaratorList(self, ctx:C64CParser.InitDeclaratorListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#initDeclarator.
    def visitInitDeclarator(self, ctx:C64CParser.InitDeclaratorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#typeSpecifier.
    def visitTypeSpecifier(self, ctx:C64CParser.TypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#compoundStatement.
    def visitCompoundStatement(self, ctx:C64CParser.CompoundStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#blockItem.
    def visitBlockItem(self, ctx:C64CParser.BlockItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#statement.
    def visitStatement(self, ctx:C64CParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#expressionStatement.
    def visitExpressionStatement(self, ctx:C64CParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#ifStatement.
    def visitIfStatement(self, ctx:C64CParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#whileStatement.
    def visitWhileStatement(self, ctx:C64CParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#doWhileStatement.
    def visitDoWhileStatement(self, ctx:C64CParser.DoWhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#forStatement.
    def visitForStatement(self, ctx:C64CParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#forInitializer.
    def visitForInitializer(self, ctx:C64CParser.ForInitializerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#jumpStatement.
    def visitJumpStatement(self, ctx:C64CParser.JumpStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#assignmentExpression.
    def visitAssignmentExpression(self, ctx:C64CParser.AssignmentExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#lvalue.
    def visitLvalue(self, ctx:C64CParser.LvalueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#assignmentOperator.
    def visitAssignmentOperator(self, ctx:C64CParser.AssignmentOperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#argumentList.
    def visitArgumentList(self, ctx:C64CParser.ArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#expression.
    def visitExpression(self, ctx:C64CParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#logicalOrExpression.
    def visitLogicalOrExpression(self, ctx:C64CParser.LogicalOrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#logicalAndExpression.
    def visitLogicalAndExpression(self, ctx:C64CParser.LogicalAndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#bitwiseOrExpression.
    def visitBitwiseOrExpression(self, ctx:C64CParser.BitwiseOrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#bitwiseXorExpression.
    def visitBitwiseXorExpression(self, ctx:C64CParser.BitwiseXorExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#bitwiseAndExpression.
    def visitBitwiseAndExpression(self, ctx:C64CParser.BitwiseAndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#equalityExpression.
    def visitEqualityExpression(self, ctx:C64CParser.EqualityExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#relationalExpression.
    def visitRelationalExpression(self, ctx:C64CParser.RelationalExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#additiveExpression.
    def visitAdditiveExpression(self, ctx:C64CParser.AdditiveExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#multiplicativeExpression.
    def visitMultiplicativeExpression(self, ctx:C64CParser.MultiplicativeExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#unaryExpression.
    def visitUnaryExpression(self, ctx:C64CParser.UnaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#primaryExpression.
    def visitPrimaryExpression(self, ctx:C64CParser.PrimaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#callExpression.
    def visitCallExpression(self, ctx:C64CParser.CallExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64CParser#integerLiteral.
    def visitIntegerLiteral(self, ctx:C64CParser.IntegerLiteralContext):
        return self.visitChildren(ctx)



del C64CParser
# Generated from /workspace/scratch/bfdb5d095aea/library_work/dBase Lexer + Parser/c64pascal/grammar/C64PascalParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .C64PascalParser import C64PascalParser
else:
    from C64PascalParser import C64PascalParser

# This class defines a complete generic visitor for a parse tree produced by C64PascalParser.

class C64PascalParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by C64PascalParser#compilationUnit.
    def visitCompilationUnit(self, ctx:C64PascalParser.CompilationUnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#programUnit.
    def visitProgramUnit(self, ctx:C64PascalParser.ProgramUnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#block.
    def visitBlock(self, ctx:C64PascalParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#constSection.
    def visitConstSection(self, ctx:C64PascalParser.ConstSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#constDefinition.
    def visitConstDefinition(self, ctx:C64PascalParser.ConstDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#varSection.
    def visitVarSection(self, ctx:C64PascalParser.VarSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#varDeclaration.
    def visitVarDeclaration(self, ctx:C64PascalParser.VarDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#identifierList.
    def visitIdentifierList(self, ctx:C64PascalParser.IdentifierListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#typeIdentifier.
    def visitTypeIdentifier(self, ctx:C64PascalParser.TypeIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#compoundStatement.
    def visitCompoundStatement(self, ctx:C64PascalParser.CompoundStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#statementSequence.
    def visitStatementSequence(self, ctx:C64PascalParser.StatementSequenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#compoundStatementNode.
    def visitCompoundStatementNode(self, ctx:C64PascalParser.CompoundStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#assignmentStatementNode.
    def visitAssignmentStatementNode(self, ctx:C64PascalParser.AssignmentStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#callStatementNode.
    def visitCallStatementNode(self, ctx:C64PascalParser.CallStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#ifStatementNode.
    def visitIfStatementNode(self, ctx:C64PascalParser.IfStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#whileStatementNode.
    def visitWhileStatementNode(self, ctx:C64PascalParser.WhileStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#repeatStatementNode.
    def visitRepeatStatementNode(self, ctx:C64PascalParser.RepeatStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#forStatementNode.
    def visitForStatementNode(self, ctx:C64PascalParser.ForStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#breakStatementNode.
    def visitBreakStatementNode(self, ctx:C64PascalParser.BreakStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#continueStatementNode.
    def visitContinueStatementNode(self, ctx:C64PascalParser.ContinueStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#assignmentStatement.
    def visitAssignmentStatement(self, ctx:C64PascalParser.AssignmentStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#callStatement.
    def visitCallStatement(self, ctx:C64PascalParser.CallStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#ifStatement.
    def visitIfStatement(self, ctx:C64PascalParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#whileStatement.
    def visitWhileStatement(self, ctx:C64PascalParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#repeatStatement.
    def visitRepeatStatement(self, ctx:C64PascalParser.RepeatStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#forStatement.
    def visitForStatement(self, ctx:C64PascalParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#argumentList.
    def visitArgumentList(self, ctx:C64PascalParser.ArgumentListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#expression.
    def visitExpression(self, ctx:C64PascalParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#orExpression.
    def visitOrExpression(self, ctx:C64PascalParser.OrExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#andExpression.
    def visitAndExpression(self, ctx:C64PascalParser.AndExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#comparisonExpression.
    def visitComparisonExpression(self, ctx:C64PascalParser.ComparisonExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#additiveExpression.
    def visitAdditiveExpression(self, ctx:C64PascalParser.AdditiveExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#multiplicativeExpression.
    def visitMultiplicativeExpression(self, ctx:C64PascalParser.MultiplicativeExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#unaryExpression.
    def visitUnaryExpression(self, ctx:C64PascalParser.UnaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#primaryExpression.
    def visitPrimaryExpression(self, ctx:C64PascalParser.PrimaryExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#integerLiteral.
    def visitIntegerLiteral(self, ctx:C64PascalParser.IntegerLiteralContext):
        return self.visitChildren(ctx)



del C64PascalParser
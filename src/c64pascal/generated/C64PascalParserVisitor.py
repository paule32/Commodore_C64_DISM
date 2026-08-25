# Generated from c64pascal/grammar/C64PascalParser.g4 by ANTLR 4.13.2
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


    # Visit a parse tree produced by C64PascalParser#unitUnit.
    def visitUnitUnit(self, ctx:C64PascalParser.UnitUnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#usesClause.
    def visitUsesClause(self, ctx:C64PascalParser.UsesClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#qualifiedIdentifier.
    def visitQualifiedIdentifier(self, ctx:C64PascalParser.QualifiedIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#block.
    def visitBlock(self, ctx:C64PascalParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#declarationSection.
    def visitDeclarationSection(self, ctx:C64PascalParser.DeclarationSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#constSection.
    def visitConstSection(self, ctx:C64PascalParser.ConstSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#constDefinition.
    def visitConstDefinition(self, ctx:C64PascalParser.ConstDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#typeSection.
    def visitTypeSection(self, ctx:C64PascalParser.TypeSectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#typeDefinition.
    def visitTypeDefinition(self, ctx:C64PascalParser.TypeDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#typeName.
    def visitTypeName(self, ctx:C64PascalParser.TypeNameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#typeSpecification.
    def visitTypeSpecification(self, ctx:C64PascalParser.TypeSpecificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#subrangeType.
    def visitSubrangeType(self, ctx:C64PascalParser.SubrangeTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#pointerType.
    def visitPointerType(self, ctx:C64PascalParser.PointerTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#signedIntegerLiteral.
    def visitSignedIntegerLiteral(self, ctx:C64PascalParser.SignedIntegerLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#enumType.
    def visitEnumType(self, ctx:C64PascalParser.EnumTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#recordType.
    def visitRecordType(self, ctx:C64PascalParser.RecordTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#arrayType.
    def visitArrayType(self, ctx:C64PascalParser.ArrayTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#classType.
    def visitClassType(self, ctx:C64PascalParser.ClassTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#classMember.
    def visitClassMember(self, ctx:C64PascalParser.ClassMemberContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#visibilitySpecifier.
    def visitVisibilitySpecifier(self, ctx:C64PascalParser.VisibilitySpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#fieldDeclaration.
    def visitFieldDeclaration(self, ctx:C64PascalParser.FieldDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#propertyDeclaration.
    def visitPropertyDeclaration(self, ctx:C64PascalParser.PropertyDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#propertyIndexParameters.
    def visitPropertyIndexParameters(self, ctx:C64PascalParser.PropertyIndexParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#propertySpecifier.
    def visitPropertySpecifier(self, ctx:C64PascalParser.PropertySpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#propertyAccessor.
    def visitPropertyAccessor(self, ctx:C64PascalParser.PropertyAccessorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#methodDeclaration.
    def visitMethodDeclaration(self, ctx:C64PascalParser.MethodDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#methodDirective.
    def visitMethodDirective(self, ctx:C64PascalParser.MethodDirectiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#globalRoutinePrototype.
    def visitGlobalRoutinePrototype(self, ctx:C64PascalParser.GlobalRoutinePrototypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#globalRoutineDeclaration.
    def visitGlobalRoutineDeclaration(self, ctx:C64PascalParser.GlobalRoutineDeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#externalImportSpecification.
    def visitExternalImportSpecification(self, ctx:C64PascalParser.ExternalImportSpecificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#globalRoutineImplementation.
    def visitGlobalRoutineImplementation(self, ctx:C64PascalParser.GlobalRoutineImplementationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#globalRoutineCallingConvention.
    def visitGlobalRoutineCallingConvention(self, ctx:C64PascalParser.GlobalRoutineCallingConventionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#methodImplementation.
    def visitMethodImplementation(self, ctx:C64PascalParser.MethodImplementationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#routineKind.
    def visitRoutineKind(self, ctx:C64PascalParser.RoutineKindContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#formalParameters.
    def visitFormalParameters(self, ctx:C64PascalParser.FormalParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#formalParameterList.
    def visitFormalParameterList(self, ctx:C64PascalParser.FormalParameterListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#formalParameterGroup.
    def visitFormalParameterGroup(self, ctx:C64PascalParser.FormalParameterGroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#routineBlock.
    def visitRoutineBlock(self, ctx:C64PascalParser.RoutineBlockContext):
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


    # Visit a parse tree produced by C64PascalParser#inheritedStatementNode.
    def visitInheritedStatementNode(self, ctx:C64PascalParser.InheritedStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#callStatementNode.
    def visitCallStatementNode(self, ctx:C64PascalParser.CallStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#raiseStatementNode.
    def visitRaiseStatementNode(self, ctx:C64PascalParser.RaiseStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#tryStatementNode.
    def visitTryStatementNode(self, ctx:C64PascalParser.TryStatementNodeContext):
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


    # Visit a parse tree produced by C64PascalParser#exitStatementNode.
    def visitExitStatementNode(self, ctx:C64PascalParser.ExitStatementNodeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#assignmentStatement.
    def visitAssignmentStatement(self, ctx:C64PascalParser.AssignmentStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#callStatement.
    def visitCallStatement(self, ctx:C64PascalParser.CallStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#raiseStatement.
    def visitRaiseStatement(self, ctx:C64PascalParser.RaiseStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#tryStatement.
    def visitTryStatement(self, ctx:C64PascalParser.TryStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#inheritedStatement.
    def visitInheritedStatement(self, ctx:C64PascalParser.InheritedStatementContext):
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


    # Visit a parse tree produced by C64PascalParser#designator.
    def visitDesignator(self, ctx:C64PascalParser.DesignatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#designatorSuffix.
    def visitDesignatorSuffix(self, ctx:C64PascalParser.DesignatorSuffixContext):
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


    # Visit a parse tree produced by C64PascalParser#inheritedExpression.
    def visitInheritedExpression(self, ctx:C64PascalParser.InheritedExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#typeCastExpression.
    def visitTypeCastExpression(self, ctx:C64PascalParser.TypeCastExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#builtinCastType.
    def visitBuiltinCastType(self, ctx:C64PascalParser.BuiltinCastTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by C64PascalParser#integerLiteral.
    def visitIntegerLiteral(self, ctx:C64PascalParser.IntegerLiteralContext):
        return self.visitChildren(ctx)



del C64PascalParser
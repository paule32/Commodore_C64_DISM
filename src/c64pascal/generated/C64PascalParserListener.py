# Generated from c64pascal/grammar/C64PascalParser.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .C64PascalParser import C64PascalParser
else:
    from C64PascalParser import C64PascalParser

# This class defines a complete listener for a parse tree produced by C64PascalParser.
class C64PascalParserListener(ParseTreeListener):

    # Enter a parse tree produced by C64PascalParser#compilationUnit.
    def enterCompilationUnit(self, ctx:C64PascalParser.CompilationUnitContext):
        pass

    # Exit a parse tree produced by C64PascalParser#compilationUnit.
    def exitCompilationUnit(self, ctx:C64PascalParser.CompilationUnitContext):
        pass


    # Enter a parse tree produced by C64PascalParser#programUnit.
    def enterProgramUnit(self, ctx:C64PascalParser.ProgramUnitContext):
        pass

    # Exit a parse tree produced by C64PascalParser#programUnit.
    def exitProgramUnit(self, ctx:C64PascalParser.ProgramUnitContext):
        pass


    # Enter a parse tree produced by C64PascalParser#unitUnit.
    def enterUnitUnit(self, ctx:C64PascalParser.UnitUnitContext):
        pass

    # Exit a parse tree produced by C64PascalParser#unitUnit.
    def exitUnitUnit(self, ctx:C64PascalParser.UnitUnitContext):
        pass


    # Enter a parse tree produced by C64PascalParser#usesClause.
    def enterUsesClause(self, ctx:C64PascalParser.UsesClauseContext):
        pass

    # Exit a parse tree produced by C64PascalParser#usesClause.
    def exitUsesClause(self, ctx:C64PascalParser.UsesClauseContext):
        pass


    # Enter a parse tree produced by C64PascalParser#qualifiedIdentifier.
    def enterQualifiedIdentifier(self, ctx:C64PascalParser.QualifiedIdentifierContext):
        pass

    # Exit a parse tree produced by C64PascalParser#qualifiedIdentifier.
    def exitQualifiedIdentifier(self, ctx:C64PascalParser.QualifiedIdentifierContext):
        pass


    # Enter a parse tree produced by C64PascalParser#block.
    def enterBlock(self, ctx:C64PascalParser.BlockContext):
        pass

    # Exit a parse tree produced by C64PascalParser#block.
    def exitBlock(self, ctx:C64PascalParser.BlockContext):
        pass


    # Enter a parse tree produced by C64PascalParser#declarationSection.
    def enterDeclarationSection(self, ctx:C64PascalParser.DeclarationSectionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#declarationSection.
    def exitDeclarationSection(self, ctx:C64PascalParser.DeclarationSectionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#constSection.
    def enterConstSection(self, ctx:C64PascalParser.ConstSectionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#constSection.
    def exitConstSection(self, ctx:C64PascalParser.ConstSectionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#constDefinition.
    def enterConstDefinition(self, ctx:C64PascalParser.ConstDefinitionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#constDefinition.
    def exitConstDefinition(self, ctx:C64PascalParser.ConstDefinitionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#typeSection.
    def enterTypeSection(self, ctx:C64PascalParser.TypeSectionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#typeSection.
    def exitTypeSection(self, ctx:C64PascalParser.TypeSectionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#typeDefinition.
    def enterTypeDefinition(self, ctx:C64PascalParser.TypeDefinitionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#typeDefinition.
    def exitTypeDefinition(self, ctx:C64PascalParser.TypeDefinitionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#typeName.
    def enterTypeName(self, ctx:C64PascalParser.TypeNameContext):
        pass

    # Exit a parse tree produced by C64PascalParser#typeName.
    def exitTypeName(self, ctx:C64PascalParser.TypeNameContext):
        pass


    # Enter a parse tree produced by C64PascalParser#typeSpecification.
    def enterTypeSpecification(self, ctx:C64PascalParser.TypeSpecificationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#typeSpecification.
    def exitTypeSpecification(self, ctx:C64PascalParser.TypeSpecificationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#subrangeType.
    def enterSubrangeType(self, ctx:C64PascalParser.SubrangeTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#subrangeType.
    def exitSubrangeType(self, ctx:C64PascalParser.SubrangeTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#pointerType.
    def enterPointerType(self, ctx:C64PascalParser.PointerTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#pointerType.
    def exitPointerType(self, ctx:C64PascalParser.PointerTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#signedIntegerLiteral.
    def enterSignedIntegerLiteral(self, ctx:C64PascalParser.SignedIntegerLiteralContext):
        pass

    # Exit a parse tree produced by C64PascalParser#signedIntegerLiteral.
    def exitSignedIntegerLiteral(self, ctx:C64PascalParser.SignedIntegerLiteralContext):
        pass


    # Enter a parse tree produced by C64PascalParser#enumType.
    def enterEnumType(self, ctx:C64PascalParser.EnumTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#enumType.
    def exitEnumType(self, ctx:C64PascalParser.EnumTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#recordType.
    def enterRecordType(self, ctx:C64PascalParser.RecordTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#recordType.
    def exitRecordType(self, ctx:C64PascalParser.RecordTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#arrayType.
    def enterArrayType(self, ctx:C64PascalParser.ArrayTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#arrayType.
    def exitArrayType(self, ctx:C64PascalParser.ArrayTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#classType.
    def enterClassType(self, ctx:C64PascalParser.ClassTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#classType.
    def exitClassType(self, ctx:C64PascalParser.ClassTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#classMember.
    def enterClassMember(self, ctx:C64PascalParser.ClassMemberContext):
        pass

    # Exit a parse tree produced by C64PascalParser#classMember.
    def exitClassMember(self, ctx:C64PascalParser.ClassMemberContext):
        pass


    # Enter a parse tree produced by C64PascalParser#visibilitySpecifier.
    def enterVisibilitySpecifier(self, ctx:C64PascalParser.VisibilitySpecifierContext):
        pass

    # Exit a parse tree produced by C64PascalParser#visibilitySpecifier.
    def exitVisibilitySpecifier(self, ctx:C64PascalParser.VisibilitySpecifierContext):
        pass


    # Enter a parse tree produced by C64PascalParser#fieldDeclaration.
    def enterFieldDeclaration(self, ctx:C64PascalParser.FieldDeclarationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#fieldDeclaration.
    def exitFieldDeclaration(self, ctx:C64PascalParser.FieldDeclarationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#propertyDeclaration.
    def enterPropertyDeclaration(self, ctx:C64PascalParser.PropertyDeclarationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#propertyDeclaration.
    def exitPropertyDeclaration(self, ctx:C64PascalParser.PropertyDeclarationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#propertyIndexParameters.
    def enterPropertyIndexParameters(self, ctx:C64PascalParser.PropertyIndexParametersContext):
        pass

    # Exit a parse tree produced by C64PascalParser#propertyIndexParameters.
    def exitPropertyIndexParameters(self, ctx:C64PascalParser.PropertyIndexParametersContext):
        pass


    # Enter a parse tree produced by C64PascalParser#propertySpecifier.
    def enterPropertySpecifier(self, ctx:C64PascalParser.PropertySpecifierContext):
        pass

    # Exit a parse tree produced by C64PascalParser#propertySpecifier.
    def exitPropertySpecifier(self, ctx:C64PascalParser.PropertySpecifierContext):
        pass


    # Enter a parse tree produced by C64PascalParser#propertyAccessor.
    def enterPropertyAccessor(self, ctx:C64PascalParser.PropertyAccessorContext):
        pass

    # Exit a parse tree produced by C64PascalParser#propertyAccessor.
    def exitPropertyAccessor(self, ctx:C64PascalParser.PropertyAccessorContext):
        pass


    # Enter a parse tree produced by C64PascalParser#methodDeclaration.
    def enterMethodDeclaration(self, ctx:C64PascalParser.MethodDeclarationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#methodDeclaration.
    def exitMethodDeclaration(self, ctx:C64PascalParser.MethodDeclarationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#methodDirective.
    def enterMethodDirective(self, ctx:C64PascalParser.MethodDirectiveContext):
        pass

    # Exit a parse tree produced by C64PascalParser#methodDirective.
    def exitMethodDirective(self, ctx:C64PascalParser.MethodDirectiveContext):
        pass


    # Enter a parse tree produced by C64PascalParser#globalRoutinePrototype.
    def enterGlobalRoutinePrototype(self, ctx:C64PascalParser.GlobalRoutinePrototypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#globalRoutinePrototype.
    def exitGlobalRoutinePrototype(self, ctx:C64PascalParser.GlobalRoutinePrototypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#globalRoutineDeclaration.
    def enterGlobalRoutineDeclaration(self, ctx:C64PascalParser.GlobalRoutineDeclarationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#globalRoutineDeclaration.
    def exitGlobalRoutineDeclaration(self, ctx:C64PascalParser.GlobalRoutineDeclarationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#globalRoutineImplementation.
    def enterGlobalRoutineImplementation(self, ctx:C64PascalParser.GlobalRoutineImplementationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#globalRoutineImplementation.
    def exitGlobalRoutineImplementation(self, ctx:C64PascalParser.GlobalRoutineImplementationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#routineDirective.
    def enterRoutineDirective(self, ctx:C64PascalParser.RoutineDirectiveContext):
        pass

    # Exit a parse tree produced by C64PascalParser#routineDirective.
    def exitRoutineDirective(self, ctx:C64PascalParser.RoutineDirectiveContext):
        pass


    # Enter a parse tree produced by C64PascalParser#methodImplementation.
    def enterMethodImplementation(self, ctx:C64PascalParser.MethodImplementationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#methodImplementation.
    def exitMethodImplementation(self, ctx:C64PascalParser.MethodImplementationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#routineKind.
    def enterRoutineKind(self, ctx:C64PascalParser.RoutineKindContext):
        pass

    # Exit a parse tree produced by C64PascalParser#routineKind.
    def exitRoutineKind(self, ctx:C64PascalParser.RoutineKindContext):
        pass


    # Enter a parse tree produced by C64PascalParser#formalParameters.
    def enterFormalParameters(self, ctx:C64PascalParser.FormalParametersContext):
        pass

    # Exit a parse tree produced by C64PascalParser#formalParameters.
    def exitFormalParameters(self, ctx:C64PascalParser.FormalParametersContext):
        pass


    # Enter a parse tree produced by C64PascalParser#formalParameterList.
    def enterFormalParameterList(self, ctx:C64PascalParser.FormalParameterListContext):
        pass

    # Exit a parse tree produced by C64PascalParser#formalParameterList.
    def exitFormalParameterList(self, ctx:C64PascalParser.FormalParameterListContext):
        pass


    # Enter a parse tree produced by C64PascalParser#formalParameterGroup.
    def enterFormalParameterGroup(self, ctx:C64PascalParser.FormalParameterGroupContext):
        pass

    # Exit a parse tree produced by C64PascalParser#formalParameterGroup.
    def exitFormalParameterGroup(self, ctx:C64PascalParser.FormalParameterGroupContext):
        pass


    # Enter a parse tree produced by C64PascalParser#routineBlock.
    def enterRoutineBlock(self, ctx:C64PascalParser.RoutineBlockContext):
        pass

    # Exit a parse tree produced by C64PascalParser#routineBlock.
    def exitRoutineBlock(self, ctx:C64PascalParser.RoutineBlockContext):
        pass


    # Enter a parse tree produced by C64PascalParser#varSection.
    def enterVarSection(self, ctx:C64PascalParser.VarSectionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#varSection.
    def exitVarSection(self, ctx:C64PascalParser.VarSectionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#varDeclaration.
    def enterVarDeclaration(self, ctx:C64PascalParser.VarDeclarationContext):
        pass

    # Exit a parse tree produced by C64PascalParser#varDeclaration.
    def exitVarDeclaration(self, ctx:C64PascalParser.VarDeclarationContext):
        pass


    # Enter a parse tree produced by C64PascalParser#identifierList.
    def enterIdentifierList(self, ctx:C64PascalParser.IdentifierListContext):
        pass

    # Exit a parse tree produced by C64PascalParser#identifierList.
    def exitIdentifierList(self, ctx:C64PascalParser.IdentifierListContext):
        pass


    # Enter a parse tree produced by C64PascalParser#typeIdentifier.
    def enterTypeIdentifier(self, ctx:C64PascalParser.TypeIdentifierContext):
        pass

    # Exit a parse tree produced by C64PascalParser#typeIdentifier.
    def exitTypeIdentifier(self, ctx:C64PascalParser.TypeIdentifierContext):
        pass


    # Enter a parse tree produced by C64PascalParser#compoundStatement.
    def enterCompoundStatement(self, ctx:C64PascalParser.CompoundStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#compoundStatement.
    def exitCompoundStatement(self, ctx:C64PascalParser.CompoundStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#statementSequence.
    def enterStatementSequence(self, ctx:C64PascalParser.StatementSequenceContext):
        pass

    # Exit a parse tree produced by C64PascalParser#statementSequence.
    def exitStatementSequence(self, ctx:C64PascalParser.StatementSequenceContext):
        pass


    # Enter a parse tree produced by C64PascalParser#compoundStatementNode.
    def enterCompoundStatementNode(self, ctx:C64PascalParser.CompoundStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#compoundStatementNode.
    def exitCompoundStatementNode(self, ctx:C64PascalParser.CompoundStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#assignmentStatementNode.
    def enterAssignmentStatementNode(self, ctx:C64PascalParser.AssignmentStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#assignmentStatementNode.
    def exitAssignmentStatementNode(self, ctx:C64PascalParser.AssignmentStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#inheritedStatementNode.
    def enterInheritedStatementNode(self, ctx:C64PascalParser.InheritedStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#inheritedStatementNode.
    def exitInheritedStatementNode(self, ctx:C64PascalParser.InheritedStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#callStatementNode.
    def enterCallStatementNode(self, ctx:C64PascalParser.CallStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#callStatementNode.
    def exitCallStatementNode(self, ctx:C64PascalParser.CallStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#ifStatementNode.
    def enterIfStatementNode(self, ctx:C64PascalParser.IfStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#ifStatementNode.
    def exitIfStatementNode(self, ctx:C64PascalParser.IfStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#whileStatementNode.
    def enterWhileStatementNode(self, ctx:C64PascalParser.WhileStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#whileStatementNode.
    def exitWhileStatementNode(self, ctx:C64PascalParser.WhileStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#repeatStatementNode.
    def enterRepeatStatementNode(self, ctx:C64PascalParser.RepeatStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#repeatStatementNode.
    def exitRepeatStatementNode(self, ctx:C64PascalParser.RepeatStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#forStatementNode.
    def enterForStatementNode(self, ctx:C64PascalParser.ForStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#forStatementNode.
    def exitForStatementNode(self, ctx:C64PascalParser.ForStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#breakStatementNode.
    def enterBreakStatementNode(self, ctx:C64PascalParser.BreakStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#breakStatementNode.
    def exitBreakStatementNode(self, ctx:C64PascalParser.BreakStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#continueStatementNode.
    def enterContinueStatementNode(self, ctx:C64PascalParser.ContinueStatementNodeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#continueStatementNode.
    def exitContinueStatementNode(self, ctx:C64PascalParser.ContinueStatementNodeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#assignmentStatement.
    def enterAssignmentStatement(self, ctx:C64PascalParser.AssignmentStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#assignmentStatement.
    def exitAssignmentStatement(self, ctx:C64PascalParser.AssignmentStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#callStatement.
    def enterCallStatement(self, ctx:C64PascalParser.CallStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#callStatement.
    def exitCallStatement(self, ctx:C64PascalParser.CallStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#inheritedStatement.
    def enterInheritedStatement(self, ctx:C64PascalParser.InheritedStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#inheritedStatement.
    def exitInheritedStatement(self, ctx:C64PascalParser.InheritedStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#ifStatement.
    def enterIfStatement(self, ctx:C64PascalParser.IfStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#ifStatement.
    def exitIfStatement(self, ctx:C64PascalParser.IfStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#whileStatement.
    def enterWhileStatement(self, ctx:C64PascalParser.WhileStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#whileStatement.
    def exitWhileStatement(self, ctx:C64PascalParser.WhileStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#repeatStatement.
    def enterRepeatStatement(self, ctx:C64PascalParser.RepeatStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#repeatStatement.
    def exitRepeatStatement(self, ctx:C64PascalParser.RepeatStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#forStatement.
    def enterForStatement(self, ctx:C64PascalParser.ForStatementContext):
        pass

    # Exit a parse tree produced by C64PascalParser#forStatement.
    def exitForStatement(self, ctx:C64PascalParser.ForStatementContext):
        pass


    # Enter a parse tree produced by C64PascalParser#designator.
    def enterDesignator(self, ctx:C64PascalParser.DesignatorContext):
        pass

    # Exit a parse tree produced by C64PascalParser#designator.
    def exitDesignator(self, ctx:C64PascalParser.DesignatorContext):
        pass


    # Enter a parse tree produced by C64PascalParser#designatorSuffix.
    def enterDesignatorSuffix(self, ctx:C64PascalParser.DesignatorSuffixContext):
        pass

    # Exit a parse tree produced by C64PascalParser#designatorSuffix.
    def exitDesignatorSuffix(self, ctx:C64PascalParser.DesignatorSuffixContext):
        pass


    # Enter a parse tree produced by C64PascalParser#argumentList.
    def enterArgumentList(self, ctx:C64PascalParser.ArgumentListContext):
        pass

    # Exit a parse tree produced by C64PascalParser#argumentList.
    def exitArgumentList(self, ctx:C64PascalParser.ArgumentListContext):
        pass


    # Enter a parse tree produced by C64PascalParser#expression.
    def enterExpression(self, ctx:C64PascalParser.ExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#expression.
    def exitExpression(self, ctx:C64PascalParser.ExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#orExpression.
    def enterOrExpression(self, ctx:C64PascalParser.OrExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#orExpression.
    def exitOrExpression(self, ctx:C64PascalParser.OrExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#andExpression.
    def enterAndExpression(self, ctx:C64PascalParser.AndExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#andExpression.
    def exitAndExpression(self, ctx:C64PascalParser.AndExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#comparisonExpression.
    def enterComparisonExpression(self, ctx:C64PascalParser.ComparisonExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#comparisonExpression.
    def exitComparisonExpression(self, ctx:C64PascalParser.ComparisonExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#additiveExpression.
    def enterAdditiveExpression(self, ctx:C64PascalParser.AdditiveExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#additiveExpression.
    def exitAdditiveExpression(self, ctx:C64PascalParser.AdditiveExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#multiplicativeExpression.
    def enterMultiplicativeExpression(self, ctx:C64PascalParser.MultiplicativeExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#multiplicativeExpression.
    def exitMultiplicativeExpression(self, ctx:C64PascalParser.MultiplicativeExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#unaryExpression.
    def enterUnaryExpression(self, ctx:C64PascalParser.UnaryExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#unaryExpression.
    def exitUnaryExpression(self, ctx:C64PascalParser.UnaryExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#primaryExpression.
    def enterPrimaryExpression(self, ctx:C64PascalParser.PrimaryExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#primaryExpression.
    def exitPrimaryExpression(self, ctx:C64PascalParser.PrimaryExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#typeCastExpression.
    def enterTypeCastExpression(self, ctx:C64PascalParser.TypeCastExpressionContext):
        pass

    # Exit a parse tree produced by C64PascalParser#typeCastExpression.
    def exitTypeCastExpression(self, ctx:C64PascalParser.TypeCastExpressionContext):
        pass


    # Enter a parse tree produced by C64PascalParser#builtinCastType.
    def enterBuiltinCastType(self, ctx:C64PascalParser.BuiltinCastTypeContext):
        pass

    # Exit a parse tree produced by C64PascalParser#builtinCastType.
    def exitBuiltinCastType(self, ctx:C64PascalParser.BuiltinCastTypeContext):
        pass


    # Enter a parse tree produced by C64PascalParser#integerLiteral.
    def enterIntegerLiteral(self, ctx:C64PascalParser.IntegerLiteralContext):
        pass

    # Exit a parse tree produced by C64PascalParser#integerLiteral.
    def exitIntegerLiteral(self, ctx:C64PascalParser.IntegerLiteralContext):
        pass



del C64PascalParser
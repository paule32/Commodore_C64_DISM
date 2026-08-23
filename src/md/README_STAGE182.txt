Stage 182 - System.SysUtils: PROPERTY + INHERITED
==================================================

Reported error
--------------

    extraneous input 'Message' expecting ':'

for:

    property Message: String read FMessage;

Root cause
----------
The Stage181 ZIP intentionally retained old generated/*.py files. Those generated
files contain neither RULE_propertyDeclaration nor a PROPERTY lexer token. The
compiler's compatibility probe, however, only tested RULE_subrangeType. That made
incremental parser versions impossible to distinguish reliably.

Stage182 changes
----------------
1. Generated-parser capability tests are now feature-specific:

       propertyDeclaration
       inheritedStatement
       subrangeType

   and relevant lexer tokens are probed independently.

2. If the active generated parser predates PROPERTY, a narrow compatibility
   bridge extracts class properties, blanks only the property source span while
   preserving newlines, parses the rest with the old parser, and re-attaches the
   PropertyDeclaration to the correct class AST.

3. The grammar now has true Object-Pascal INHERITED support:

       INHERITED : 'INHERITED';

       inheritedStatement
           : INHERITED (IDENTIFIER (LPAREN argumentList? RPAREN)?)?
           ;

4. The compiler AST contains InheritedCallStatement. During semantic resolution
   `inherited Create;` selects the direct base class and uses the current Self.
   For the user source this resolves to TObject.Create, never Exception.Create.

5. The compatibility bridge also handles `inherited Create;` when generated/*.py
   has not yet been regenerated.

Expected PE32 assembly
----------------------
Inside Exception.Create:

       call __pas_method_tobject_create

The field assignment remains:

       FMessage := AMessage;

Property semantics
------------------
The declaration:

       property Message: String read FMessage;

is stored as a property of Exception with type String and read accessor FMessage.

ANTLR regeneration
------------------
Recommended after copying Stage182:

       compile.bat

using ANTLR 4.13.2, then completely restart d64_dism.py. Stage182's bridge also
keeps the exact source usable with older generated parser files, but regeneration
is preferred so PROPERTY and INHERITED are handled natively by ANTLR.

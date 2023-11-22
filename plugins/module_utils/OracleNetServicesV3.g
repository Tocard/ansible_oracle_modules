/*

 Copyright 2007 by Nathaniel Harward <nharward@gmail.com>

 ANTLRv3 grammar for Oracle Network Services configuration files

 This grammar can parse entries in an Oracle Network Services configuration
 file (tnsnames.ora, listener.ora, sqlnet.ora, cman.ora, ldap.ora...), based
 on the Oracle 10g document:

 http://download-west.oracle.com/docs/cd/B19306_01/network.102/b14213/syntax.htm

 This grammar does not strictly conform to the document.  In paricular it does
 not enforce that parameters start at column 0, and that continuation lines do
 not start in column 0 -- whitespace is ignored (as are comments).  All other
 rules should be observed.

 The Oracle "spec" above is a little vague as a standalone language/syntax
 definition: I don't see how "NAMES.DIRECTORY_PATH= (TNSNAMES, ONAMES)" is
 valid since ',' is not listed as a delimiter.  Of course I might have just
 misunderstood the document :)  At any rate, if you come across valid syntax
 that this grammar does not allow please let me know so I can post a fix.

*/

grammar OracleNetServicesV3;

options {
    output=AST;
    ASTLabelType=CommonTree; // type of $stat.tree ref etc...
    language=Python;

}

tokens {
    ORAFILE;
    KEYWORD;
}

@lexer::members {
#@Override
def reportError(self, e):
    super(OracleNetServicesV3Lexer, self).reportError(e)

    chp = self._state.tokenStartCharPositionInLine
    chl = self._state.tokenStartLine
    lexer_error_start = "{}:{}".format(chl, chp)
        
    if isinstance(e, NoViableAltException):
        raise ValueError('Lexer error at {} => {}:{}, {}'.format(lexer_error_start, e.line, e.charPositionInLine, e))
    elif isinstance(e, (MissingTokenException,MismatchedTokenException)):
        raise ValueError('Lexer error at {} => {}:{}, expecting {}, {}'.format(lexer_error_start, e.line, e.charPositionInLine, e.expecting, e))
    else:
        raise ValueError('Lexer error')
}

@parser::members {
#@Override
def reportError(self, e):
    super(OracleNetServicesV3Parser, self).reportError(e)
    raise ValueError('Parser error: {}, {}'.format(e, e.token))
}
        
configuration_file
    : ( parameter )*
    EOF
    -> ^(ORAFILE parameter*)
    ;

parameter
    : k=WORD EQUALS ( value
                     | LEFT_PAREN value_list RIGHT_PAREN
                     | parameter_list
                     )
	-> ^(KEYWORD[$k] $k value? LEFT_PAREN? value_list? RIGHT_PAREN? parameter_list?)                      
    ;

parameter_list
	: (LEFT_PAREN parameter RIGHT_PAREN)+
	;

keyword
    : WORD
    ;

value
    : WORD
    | QUOTED_STRING
    ;

value_list
    : value ( COMMA value )*
    ;

QUOTED_STRING
    : SINGLE_QUOTE ( ~( SINGLE_QUOTE ) )* SINGLE_QUOTE
    | DOUBLE_QUOTE ( ~( DOUBLE_QUOTE ) )* DOUBLE_QUOTE
    ;

WORD
    : ( 'A' .. 'Z'
      | 'a' .. 'z'
      | '0' .. '9'
      | '/'
      | '+'
      )
      ( 'A' .. 'Z'
      | 'a' .. 'z'
      | '0' .. '9'
      | '<'
      | '>'
      | '/'
      | '.'
      | ':'
      | ';'
      | '-'
      | '_'
      | '$'
      | '+'
      | '*'
      | '&'
      | '!'
      | '%'
      | '?'
      | '@'
      | '\\' .
      )*
    ;

LEFT_PAREN
    : '('
    ;

RIGHT_PAREN
    : ')'
    ;

EQUALS
    : '='
    ;

COMMA
    : ','
    ;

SINGLE_QUOTE
    : '\''
    ;

DOUBLE_QUOTE
    : '"'
    ;

COMMENT
    : '#' ( ~( '\n' ) )* {$channel=HIDDEN;}
    ;

WHITESPACE
    : ( '\t'
      | ' '
      ) {$channel=HIDDEN;}
    ;

NEWLINE
    : ( '\r' )? '\n' {$channel=HIDDEN;}
    ;


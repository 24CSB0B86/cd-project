"""
Recursive Descent Parser for Mini-Python Compiler
Converts token stream from Lexer into Abstract Syntax Tree (AST)
Week 6-7 Implementation
"""

from typing import List, Optional
from .tokens import Token, TokenType
from .ast_nodes import *


class ParserError(Exception):
    """Exception raised when parser encounters a syntax error"""
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        self.line = token.line
        self.column = token.column
        super().__init__(f"ParserError at line {self.line}, column {self.column}: {message}")


class Parser:
    """Recursive Descent Parser for Mini-Python
    
    Follows the EBNF grammar defined in grammar/mini_python.ebnf
    """
    
    def __init__(self, tokens: List[Token]):
        """Initialize parser with token stream
        
        Args:
            tokens: List of tokens from Lexer
        """
        self.tokens = tokens
        self.current = 0
        
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def current_token(self) -> Token:
        """Get the current token without advancing"""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return self.tokens[-1]  # Return EOF token
    
    def peek(self, offset: int = 1) -> Token:
        """Look ahead at token without consuming it
        
        Args:
            offset: How many tokens ahead to look (default: 1)
        """
        pos = self.current + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # Return EOF token
    
    def advance(self) -> Token:
        """Consume and return current token, move to next"""
        token = self.current_token()
        if self.current < len(self.tokens) - 1:
            self.current += 1
        return token
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types
        
        Args:
            token_types: Variable number of TokenType values to check
            
        Returns:
            True if current token matches any of the types
        """
        current = self.current_token()
        return current.type in token_types
    
    def expect(self, token_type: TokenType, error_msg: Optional[str] = None) -> Token:
        """Consume token if it matches expected type, otherwise raise error
        
        Args:
            token_type: Expected token type
            error_msg: Custom error message (optional)
            
        Returns:
            The consumed token
            
        Raises:
            ParserError: If current token doesn't match expected type
        """
        current = self.current_token()
        if current.type != token_type:
            if error_msg:
                raise ParserError(error_msg, current)
            else:
                raise ParserError(
                    f"Expected {token_type.name}, got {current.type.name}",
                    current
                )
        return self.advance()
    
    def skip_newlines(self):
        """Skip any consecutive NEWLINE tokens"""
        while self.match(TokenType.NEWLINE):
            self.advance()
    
    # ========================================================================
    # Main Parsing Entry Point
    # ========================================================================
    
    def parse(self) -> Program:
        """Parse the entire program
        
        Returns:
            Program AST node containing all statements
        """
        return self.parse_program()
    
    def parse_program(self) -> Program:
        """Parse a program (sequence of statements)
        
        Grammar: program = { statement } ;
        """
        statements = []
        self.skip_newlines()
        
        while not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        # Use position from first statement or (1, 1) for empty program
        line = statements[0].line if statements else 1
        col = statements[0].column if statements else 1
        return Program(statements=statements, line=line, column=col)
    
    # ========================================================================
    # Statement Parsing
    # ========================================================================
    
    def parse_statement(self) -> Optional[Statement]:
        """Parse a single statement
        
        Grammar: statement = assignment | if_stmt | while_stmt | func_def | print_stmt ;
        """
        current = self.current_token()
        
        # Function definition
        if self.match(TokenType.DEF):
            return self.parse_function_def()
        
        # If statement
        elif self.match(TokenType.IF):
            return self.parse_if_statement()
        
        # While loop
        elif self.match(TokenType.WHILE):
            return self.parse_while_statement()
        
        # Return statement
        elif self.match(TokenType.RETURN):
            return self.parse_return_statement()
        
        # Print statement
        elif self.match(TokenType.PRINT):
            return self.parse_print_statement()
        
        # Assignment (must check for identifier followed by =)
        elif self.match(TokenType.IDENTIFIER):
            if self.peek().type == TokenType.ASSIGN:
                return self.parse_assignment()
            else:
                raise ParserError(
                    f"Unexpected identifier '{current.value}' at statement level",
                    current
                )
        
        # Skip empty newlines
        elif self.match(TokenType.NEWLINE):
            self.advance()
            return None
        
        else:
            raise ParserError(
                f"Unexpected token '{current.type.name}' at statement level",
                current
            )
    
    def parse_assignment(self) -> Assignment:
        """Parse variable assignment
        
        Grammar: assignment = identifier , "=" , expression , NEWLINE ;
        """
        id_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()
        self.expect(TokenType.NEWLINE)
        
        return Assignment(
            target=id_token.value,
            value=value,
            line=id_token.line,
            column=id_token.column
        )
    
    def parse_if_statement(self) -> IfStatement:
        """Parse if statement with optional else clause
        
        Grammar: if_stmt = "if" , condition , ":" , block , [ "else" , ":" , block ] ;
        """
        if_token = self.expect(TokenType.IF)
        condition = self.parse_condition()
        self.expect(TokenType.COLON)
        then_block = self.parse_block()
        
        else_block = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.COLON)
            else_block = self.parse_block()
        
        return IfStatement(
            condition=condition,
            then_block=then_block,
            else_block=else_block,
            line=if_token.line,
            column=if_token.column
        )
    
    def parse_while_statement(self) -> WhileStatement:
        """Parse while loop
        
        Grammar: while_stmt = "while" , condition , ":" , block ;
        """
        while_token = self.expect(TokenType.WHILE)
        condition = self.parse_condition()
        self.expect(TokenType.COLON)
        body = self.parse_block()
        
        return WhileStatement(
            condition=condition,
            body=body,
            line=while_token.line,
            column=while_token.column
        )
    
    def parse_function_def(self) -> FunctionDef:
        """Parse function definition
        
        Grammar: func_def = "def" , identifier , "(" , [ params ] , ")" , ":" , block ;
        """
        def_token = self.expect(TokenType.DEF)
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.LPAREN)
        
        # Parse parameter list
        params = []
        if not self.match(TokenType.RPAREN):
            params = self.parse_params()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        body = self.parse_block()
        
        return FunctionDef(
            name=name_token.value,
            params=params,
            body=body,
            line=def_token.line,
            column=def_token.column
        )
    
    def parse_params(self) -> List[str]:
        """Parse function parameter list
        
        Grammar: params = identifier , { "," , identifier } ;
        """
        params = []
        params.append(self.expect(TokenType.IDENTIFIER).value)
        
        while self.match(TokenType.COMMA):
            self.advance()
            params.append(self.expect(TokenType.IDENTIFIER).value)
        
        return params
    
    def parse_return_statement(self) -> ReturnStatement:
        """Parse return statement
        
        Grammar: return_stmt = "return" , [ expression ] , NEWLINE ;
        """
        return_token = self.expect(TokenType.RETURN)
        
        # Check if there's an expression to return
        value = None
        if not self.match(TokenType.NEWLINE):
            value = self.parse_expression()
        
        self.expect(TokenType.NEWLINE)
        
        return ReturnStatement(
            value=value,
            line=return_token.line,
            column=return_token.column
        )
    
    def parse_print_statement(self) -> PrintStatement:
        """Parse print statement
        
        Grammar: print_stmt = "print" , "(" , expression , ")" , NEWLINE ;
        """
        print_token = self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)
        expression = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.NEWLINE)
        
        return PrintStatement(
            expression=expression,
            line=print_token.line,
            column=print_token.column
        )
    
    def parse_block(self) -> Block:
        """Parse indented block of statements
        
        Grammar: block = NEWLINE , INDENT , { statement } , DEDENT ;
        """
        block_start = self.current_token()
        self.expect(TokenType.NEWLINE)
        self.expect(TokenType.INDENT)
        
        statements = []
        while not self.match(TokenType.DEDENT) and not self.match(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        self.expect(TokenType.DEDENT)
        
        return Block(
            statements=statements,
            line=block_start.line,
            column=block_start.column
        )
    
    # ========================================================================
    # Expression Parsing (with operator precedence)
    # ========================================================================
    
    def parse_condition(self) -> Expression:
        """Parse condition (comparison expression)
        
        Grammar: condition = expression , comp_op , expression ;
        """
        left = self.parse_expression()
        
        # Check for comparison operator
        if self.match(TokenType.EQ, TokenType.NEQ, TokenType.LT, 
                     TokenType.GT, TokenType.LTE, TokenType.GTE):
            op_token = self.advance()
            right = self.parse_expression()
            
            return BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        # If no comparison operator, return the expression as-is
        # (useful for boolean expressions like "while True:")
        return left
    
    def parse_expression(self) -> Expression:
        """Parse expression (handles + and - with left associativity)
        
        Grammar: expression = term , { ( "+" | "-" ) , term } ;
        """
        left = self.parse_term()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_term()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_term(self) -> Expression:
        """Parse term (handles * and / with left associativity)
        
        Grammar: term = factor , { ( "*" | "/" ) , factor } ;
        """
        left = self.parse_factor()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            op_token = self.advance()
            right = self.parse_factor()
            left = BinaryOp(
                left=left,
                operator=op_token.value,
                right=right,
                line=op_token.line,
                column=op_token.column
            )
        
        return left
    
    def parse_factor(self) -> Expression:
        """Parse factor (primary expressions, includes unary minus)
        
        Grammar: factor = [ "-" ] , ( identifier | number | string | "(" , expression , ")" ) ;
        """
        current = self.current_token()

        # Unary minus: -x, -5, -(a + b)
        if self.match(TokenType.MINUS):
            op_token = self.advance()
            operand = self.parse_factor()  # recursive so --x also works
            return UnaryOp(
                operator='-',
                operand=operand,
                line=op_token.line,
                column=op_token.column
            )

        # Number literal
        if self.match(TokenType.NUMBER):
            token = self.advance()
            return Literal(
                value=token.value,
                line=token.line,
                column=token.column
            )
        
        # String literal
        elif self.match(TokenType.STRING):
            token = self.advance()
            return Literal(
                value=token.value,
                line=token.line,
                column=token.column
            )
        
        # Identifier or function call
        elif self.match(TokenType.IDENTIFIER):
            token = self.advance()
            
            # Check if it's a function call
            if self.match(TokenType.LPAREN):
                self.advance()
                arguments = []
                
                # Parse arguments
                if not self.match(TokenType.RPAREN):
                    arguments.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        self.advance()
                        arguments.append(self.parse_expression())
                
                self.expect(TokenType.RPAREN)
                
                return FunctionCall(
                    function_name=token.value,
                    arguments=arguments,
                    line=token.line,
                    column=token.column
                )
            else:
                # Just an identifier
                return Identifier(
                    name=token.value,
                    line=token.line,
                    column=token.column
                )
        
        # Parenthesized expression
        elif self.match(TokenType.LPAREN):
            lparen = self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        else:
            raise ParserError(
                f"Expected expression, got {current.type.name}",
                current
            )

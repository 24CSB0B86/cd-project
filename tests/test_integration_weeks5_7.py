"""
Integration tests for Lexer -> Parser pipeline
Tests end-to-end compilation from source code to AST
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.ast_nodes import *


def test_lexer_to_parser_simple():
    """Test simple assignment through full pipeline"""
    code = "x = 42\n"
    
    # Lexer stage
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    # Parser stage
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Verify AST
    assert isinstance(ast, Program)
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], Assignment)


def test_lexer_to_parser_factorial():
    """Test factorial function through full pipeline"""
    code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
    
    # Lexer stage
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    # Verify tokens include INDENT/DEDENT
    token_types = [t.type for t in tokens]
    from compiler.tokens import TokenType
    assert TokenType.INDENT in token_types
    assert TokenType.DEDENT in token_types
    
    # Parser stage
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Verify AST structure
    assert isinstance(ast, Program)
    assert len(ast.statements) == 1
    
    func = ast.statements[0]
    assert isinstance(func, FunctionDef)
    assert func.name == "factorial"
    assert func.params == ["n"]
    
    # Verify function body
    assert isinstance(func.body, Block)
    assert len(func.body.statements) == 2


def test_position_tracking():
    """Test that line/column information is preserved"""
    code = """
def foo():
    x = 5
"""
    
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    func = ast.statements[0]
    # Function should be on line 2 (first non-empty line)
    assert func.line == 2
    
    # Assignment inside function
    assignment = func.body.statements[0]
    assert assignment.line == 3


def test_error_message_includes_position():
    """Test that parser errors reference source code position"""
    code = """
def foo()
    return 42
"""
    
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    
    try:
        ast = parser.parse()
        assert False, "Should have raised ParserError"
    except Exception as e:
        # Error message should mention line number
        assert "line" in str(e).lower()


def test_multiple_statements():
    """Test program with multiple top-level statements"""
    code = """
x = 1
y = 2
z = x + y
"""
    
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    assert len(ast.statements) == 3
    assert all(isinstance(stmt, Assignment) for stmt in ast.statements)


def test_nested_blocks():
    """Test deeply nested block structures"""
    code = """
def outer():
    if True:
        while x > 0:
            x = x - 1
"""
    
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    func = ast.statements[0]
    if_stmt = func.body.statements[0]
    while_stmt = if_stmt.then_block.statements[0]
    
    assert isinstance(func, FunctionDef)
    assert isinstance(if_stmt, IfStatement)
    assert isinstance(while_stmt, WhileStatement)


if __name__ == "__main__":
    print("Running integration tests...")
    test_lexer_to_parser_simple()
    test_lexer_to_parser_factorial()
    test_position_tracking()
    test_error_message_includes_position()
    test_multiple_statements()
    test_nested_blocks()
    print("✓ All integration tests passed!")

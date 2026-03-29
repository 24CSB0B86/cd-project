"""
Week 5: Lexer (Lexical Analyzer) Tests
Tests tokenization, keyword recognition, and indentation handling
Execution Plan Week 5 Deliverable
"""

import pytest
from src.compiler.lexer import Lexer
from src.compiler.tokens import TokenType, Token


class TestBasicTokenization:
    """Test basic tokenization functionality"""
    
    def test_simple_assignment(self):
        """Test tokenizing a simple assignment"""
        code = "x = 5"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        assert len(tokens) == 5  # x, =, 5, NEWLINE, EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == 'x'
        assert tokens[1].type == TokenType.ASSIGN
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == 5
        
    def test_keyword_recognition(self):
        """Test that keywords are recognized correctly"""
        code = "def foo"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        assert tokens[0].type == TokenType.DEF
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == 'foo'
        
    def test_string_literal(self):
        """Test string tokenization"""
        code = 'message = "hello"'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        string_token = tokens[2]
        assert string_token.type == TokenType.STRING
        assert string_token.value == 'hello'


class TestOperators:
    """Test operator tokenization"""
    
    def test_arithmetic_operators(self):
        """Test arithmetic operator tokens"""
        code = "x = a + b - c * d / e"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        operators = [t for t in tokens if t.type in [
            TokenType.PLUS, TokenType.MINUS, 
            TokenType.MULTIPLY, TokenType.DIVIDE
        ]]
        assert len(operators) == 4
        
    def test_comparison_operators(self):
        """Test comparison operator tokens"""
        code = "x == y\ny != z\na < b\nc > d"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        comparison_types = [TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT]
        comparisons = [t for t in tokens if t.type in comparison_types]
        assert len(comparisons) == 4


class TestIndentationHandling:
    """Test Python-style indentation tracking (unique to Python)"""
    
    def test_simple_indent(self):
        """Test single level indentation"""
        code = """
def foo():
    x = 5
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # Check for INDENT token
        indent_tokens = [t for t in tokens if t.type == TokenType.INDENT]
        dedent_tokens = [t for t in tokens if t.type == TokenType.DEDENT]
        
        assert len(indent_tokens) == 1
        assert len(dedent_tokens) == 1
        
    def test_nested_indentation(self):
        """Test nested indentation levels"""
        code = """
def foo():
    if True:
        x = 5
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        indent_tokens = [t for t in tokens if t.type == TokenType.INDENT]
        dedent_tokens = [t for t in tokens if t.type == TokenType.DEDENT]
        
        assert len(indent_tokens) == 2  # Two levels of indentation
        assert len(dedent_tokens) == 2  # Two dedents at end
        
    def test_multiple_dedents(self):
        """Test multiple dedent levels"""
        code = """
def outer():
    if True:
        x = 1
y = 2
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        dedent_tokens = [t for t in tokens if t.type == TokenType.DEDENT]
        assert len(dedent_tokens) == 2  # Dedent from if and from def


class TestLineTracking:
    """Test line and column tracking for error reporting"""
    
    def test_line_numbers(self):
        """Test that line numbers are tracked correctly"""
        code = """
x = 1
y = 2
z = 3
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # Find the identifier tokens
        identifiers = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        
        assert identifiers[0].line == 2  # x
        assert identifiers[1].line == 3  # y
        assert identifiers[2].line == 4  # z
        
    def test_column_tracking(self):
        """Test that column positions are tracked"""
        code = "x = 5"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        assert tokens[0].column == 1  # x starts at column 1
        assert tokens[1].column == 3  # = is at column 3


class TestErrorDetection:
    """Test lexer error detection"""
    
    def test_invalid_character(self):
        """Test that invalid characters raise errors"""
        code = "x = @"  # @ is not a valid character in our subset
        lexer = Lexer(code)
        
        with pytest.raises(SyntaxError):
            lexer.tokenize()
            
    def test_indentation_error(self):
        """Test indentation errors are caught"""
        code = """
def foo():
    x = 1
  y = 2
"""
        lexer = Lexer(code)
        
        with pytest.raises(SyntaxError, match="Indentation Error"):
            lexer.tokenize()


class TestCompletePrograms:
    """Test lexer on complete Mini-Python programs"""
    
    def test_factorial_function(self):
        """Test lexing the factorial function"""
        code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # Verify we have the expected token types
        token_types = [t.type for t in tokens]
        
        assert TokenType.DEF in token_types
        assert TokenType.IF in token_types
        assert TokenType.RETURN in token_types
        assert TokenType.INDENT in token_types
        assert TokenType.DEDENT in token_types
        assert TokenType.EOF in token_types
        
    def test_loop_program(self):
        """Test lexing a program with a while loop"""
        code = """
x = 10
while x > 0:
    print(x)
    x = x - 1
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        # Check for while keyword
        while_tokens = [t for t in tokens if t.type == TokenType.WHILE]
        assert len(while_tokens) == 1
        
        # Check for print keyword
        print_tokens = [t for t in tokens if t.type == TokenType.PRINT]
        assert len(print_tokens) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

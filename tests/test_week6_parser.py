"""
Week 6: Parser (Recursive Descent Syntax Analysis) Tests
Tests AST construction, operator precedence, and statement parsing
Execution Plan Week 6 Deliverable
"""

import pytest
from src.compiler.lexer import Lexer
from src.compiler.parser import Parser, ParserError
from src.compiler.tokens import TokenType
from src.compiler.ast_nodes import *


class TestExpressionParsing:
    """Test expression parsing with correct operator precedence"""
    
    def test_simple_number(self):
        """Test parsing a simple number literal"""
        code = "x = 42\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, Program)
        assert len(ast.statements) == 1
        assert isinstance(ast.statements[0], Assignment)
        assert ast.statements[0].target == "x"
        assert isinstance(ast.statements[0].value, Literal)
        assert ast.statements[0].value.value == 42
    
    def test_simple_addition(self):
        """Test parsing simple addition: x = 2 + 3"""
        code = "x = 2 + 3\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        assert isinstance(assignment.value, BinaryOp)
        assert assignment.value.operator == "+"
        assert isinstance(assignment.value.left, Literal)
        assert assignment.value.left.value == 2
        assert isinstance(assignment.value.right, Literal)
        assert assignment.value.right.value == 3
    
    def test_simple_multiplication(self):
        """Test parsing multiplication: x = 5 * 4"""
        code = "x = 5 * 4\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        assert isinstance(assignment.value, BinaryOp)
        assert assignment.value.operator == "*"
        assert assignment.value.left.value == 5
        assert assignment.value.right.value == 4
    
    def test_operator_precedence(self):
        """Test operator precedence: 2 + 3 * 4 should parse as 2 + (3 * 4)"""
        code = "x = 2 + 3 * 4\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        expr = assignment.value
        
        # Should be: BinaryOp(+, left=2, right=BinaryOp(*, 3, 4))
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"
        assert isinstance(expr.left, Literal)
        assert expr.left.value == 2
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "*"
        assert expr.right.left.value == 3
        assert expr.right.right.value == 4
    
    def test_parenthesized_expression(self):
        """Test parentheses override precedence: (2 + 3) * 4"""
        code = "x = (2 + 3) * 4\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        expr = assignment.value
        
        # Should be: BinaryOp(*, left=BinaryOp(+, 2, 3), right=4)
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "*"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "+"
        assert expr.left.left.value == 2
        assert expr.left.right.value == 3
        assert isinstance(expr.right, Literal)
        assert expr.right.value == 4
    
    def test_nested_expressions(self):
        """Test deeply nested expression: (a + b) * (c - d)"""
        code = "x = (a + b) * (c - d)\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        expr = assignment.value
        
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "*"
        
        # Left side: (a + b)
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "+"
        assert isinstance(expr.left.left, Identifier)
        assert expr.left.left.name == "a"
        
        # Right side: (c - d)
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "-"
        assert isinstance(expr.right.left, Identifier)
        assert expr.right.left.name == "c"
    
    def test_comparison_expression(self):
        """Test comparison in condition: if x == 5"""
        code = """
if x == 5:
    result = 1
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        if_stmt = ast.statements[0]
        assert isinstance(if_stmt, IfStatement)
        assert isinstance(if_stmt.condition, BinaryOp)
        assert if_stmt.condition.operator == "=="
        assert isinstance(if_stmt.condition.left, Identifier)
        assert if_stmt.condition.left.name == "x"
        assert isinstance(if_stmt.condition.right, Literal)
        assert if_stmt.condition.right.value == 5
    
    def test_identifier_expression(self):
        """Test simple identifier: x = y"""
        code = "x = y\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        assert isinstance(assignment.value, Identifier)
        assert assignment.value.name == "y"


class TestStatementParsing:
    """Test statement parsing including control flow"""
    
    def test_simple_assignment(self):
        """Test basic variable assignment"""
        code = "x = 42\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, Program)
        assert len(ast.statements) == 1
        assert isinstance(ast.statements[0], Assignment)
        assert ast.statements[0].target == "x"
    
    def test_print_statement(self):
        """Test print statement"""
        code = 'print("hello")\n'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 1
        assert isinstance(ast.statements[0], PrintStatement)
        assert isinstance(ast.statements[0].expression, Literal)
        assert ast.statements[0].expression.value == "hello"
    
    def test_return_statement(self):
        """Test return statement with value"""
        code = """
def foo():
    return 42
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        func = ast.statements[0]
        assert isinstance(func, FunctionDef)
        assert len(func.body.statements) == 1
        assert isinstance(func.body.statements[0], ReturnStatement)
        assert isinstance(func.body.statements[0].value, Literal)
        assert func.body.statements[0].value.value == 42
    
    def test_simple_if_statement(self):
        """Test if statement without else"""
        code = """
if x == 0:
    return 1
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        if_stmt = ast.statements[0]
        assert isinstance(if_stmt, IfStatement)
        assert isinstance(if_stmt.condition, BinaryOp)
        assert if_stmt.condition.operator == "=="
        assert isinstance(if_stmt.then_block, Block)
        assert len(if_stmt.then_block.statements) == 1
        assert if_stmt.else_block is None
    
    def test_if_else_statement(self):
        """Test if-else statement"""
        code = """
if x == 0:
    return 1
else:
    return 0
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        if_stmt = ast.statements[0]
        assert isinstance(if_stmt, IfStatement)
        assert isinstance(if_stmt.then_block, Block)
        assert isinstance(if_stmt.else_block, Block)
        assert len(if_stmt.else_block.statements) == 1
    
    def test_while_loop(self):
        """Test while loop"""
        code = """
while x > 0:
    x = x - 1
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        while_stmt = ast.statements[0]
        assert isinstance(while_stmt, WhileStatement)
        assert isinstance(while_stmt.condition, BinaryOp)
        assert while_stmt.condition.operator == ">"
        assert isinstance(while_stmt.body, Block)
        assert len(while_stmt.body.statements) == 1
    
    def test_function_definition_no_params(self):
        """Test function definition without parameters"""
        code = """
def foo():
    return 42
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        func = ast.statements[0]
        assert isinstance(func, FunctionDef)
        assert func.name == "foo"
        assert len(func.params) == 0
        assert isinstance(func.body, Block)
    
    def test_function_definition_with_params(self):
        """Test function definition with parameters"""
        code = """
def add(a, b):
    return a + b
"""
        lexer = Lexer (code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        func = ast.statements[0]
        assert isinstance(func, FunctionDef)
        assert func.name == "add"
        assert len(func.params) == 2
        assert func.params == ["a", "b"]
    
    def test_function_call_in_expression(self):
        """Test function call within expression"""
        code = "x = factorial(5)\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        assert isinstance(assignment.value, FunctionCall)
        assert assignment.value.function_name == "factorial"
        assert len(assignment.value.arguments) == 1
        assert isinstance(assignment.value.arguments[0], Literal)
        assert assignment.value.arguments[0].value == 5


class TestNestedBlocks:
    """Test handling of nested indented blocks"""
    
    def test_factorial_function(self):
        """Test parsing the factorial function from Week 5"""
        code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Verify structure
        assert isinstance(ast, Program)
        assert len(ast.statements) == 1
        
        # Verify function definition
        func = ast.statements[0]
        assert isinstance(func, FunctionDef)
        assert func.name == "factorial"
        assert func.params == ["n"]
        
        # Verify body has 2 statements (if and return)
        assert len(func.body.statements) == 2
        assert isinstance(func.body.statements[0], IfStatement)
        assert isinstance(func.body.statements[1], ReturnStatement)
        
        # Verify if statement structure
        if_stmt = func.body.statements[0]
        assert isinstance(if_stmt.condition, BinaryOp)
        assert if_stmt.condition.operator == "=="
        
        # Verify recursive call in return statement
        return_stmt = func.body.statements[1]
        assert isinstance(return_stmt.value, BinaryOp)
        assert return_stmt.value.operator == "*"
        assert isinstance(return_stmt.value.right, FunctionCall)
        assert return_stmt.value.right.function_name == "factorial"
    
    def test_nested_control_flow(self):
        """Test nested if inside while"""
        code = """
while x > 0:
    if x == 5:
        return x
    x = x - 1
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        while_stmt = ast.statements[0]
        assert isinstance(while_stmt, WhileStatement)
        assert len(while_stmt.body.statements) == 2
        assert isinstance(while_stmt.body.statements[0], IfStatement)
        assert isinstance(while_stmt.body.statements[1], Assignment)
    
    def test_multiple_functions(self):
        """Test program with multiple function definitions"""
        code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 2
        assert isinstance(ast.statements[0], FunctionDef)
        assert ast.statements[0].name == "add"
        assert isinstance(ast.statements[1], FunctionDef)
        assert ast.statements[1].name == "subtract"


class TestErrorDetection:
    """Test parser error detection and reporting"""
    
    def test_missing_colon_after_function(self):
        """Test error when colon is missing after function definition"""
        code = """
def foo()
    return 42
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        with pytest.raises(ParserError) as exc_info:
            parser.parse()
        
        assert "Expected COLON" in str(exc_info.value)
    
    def test_missing_colon_after_if(self):
        """Test error when colon is missing after if"""
        code = """
if x == 0
    return 1
"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        with pytest.raises(ParserError) as exc_info:
            parser.parse()
        
        assert "Expected COLON" in str(exc_info.value)
    
    def test_mismatched_parentheses(self):
        """Test error for mismatched parentheses"""
        code = "x = (2 + 3\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        with pytest.raises(ParserError) as exc_info:
            parser.parse()
        
        assert "Expected RPAREN" in str(exc_info.value)
    
    def test_unexpected_token_at_statement_level(self):
        """Test error for unexpected token"""
        code = "+ = 5\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        
        with pytest.raises(ParserError):
            parser.parse()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_program(self):
        """Test parsing empty program"""
        code = "\n\n\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert isinstance(ast, Program)
        assert len(ast.statements) == 0
    
    def test_complex_arithmetic(self):
        """Test complex arithmetic expression"""
        code = "result = (a + b) * c - d / e\n"
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assignment = ast.statements[0]
        # Just verify it parses without error
        assert isinstance(assignment.value, BinaryOp)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

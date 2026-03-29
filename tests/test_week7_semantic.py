"""
Test Suite for Semantic Analyzer
Week 7 Implementation Tests
"""

import pytest
from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer, SemanticError, SymbolType


def analyze_code(code: str) -> SemanticAnalyzer:
    """Helper to analyze code and return analyzer"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return analyzer


class TestSymbolTable:
    """Test symbol table functionality"""
    
    def test_simple_variable_definition(self):
        """Test defining and using a variable"""
        code = """
x = 5
y = x
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        assert analyzer.symbol_table.lookup('x') is not None
        assert analyzer.symbol_table.lookup('y') is not None
        
    def test_undefined_variable(self):
        """Test using undefined variable"""
        code = """
x = y + 1
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 1
        assert "Undefined variable 'y'" in analyzer.errors[0].message
        
    def test_function_scope(self):
        """Test function creates new scope"""
        code = """
def foo(n):
    x = n + 1
    return x

y = 10
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        
        # Function should be defined in global scope
        func_symbol = analyzer.symbol_table.lookup('foo')
        assert func_symbol is not None
        assert func_symbol.symbol_type == SymbolType.FUNCTION
        
    def test_parameter_scope(self):
        """Test function parameters are local to function"""
        code = """
def add(a, b):
    result = a + b
    return result
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        

class TestTypeChecking:
    """Test basic type checking"""
    
    def test_integer_arithmetic(self):
        """Test integer arithmetic type inference"""
        code = """
x = 5
y = 10
z = x + y
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        
        z_symbol = analyzer.symbol_table.lookup('z')
        assert z_symbol.symbol_type == SymbolType.INTEGER
        
    def test_string_literal(self):
        """Test string type inference"""
        code = """
message = "hello"
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        
        msg_symbol = analyzer.symbol_table.lookup('message')
        assert msg_symbol.symbol_type == SymbolType.STRING


class TestErrorDetection:
    """Test semantic error detection"""
    
    def test_duplicate_function_definition(self):
        """Test duplicate function names in same scope"""
        code = """
def foo():
    return 1

def foo():
    return 2
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 1
        assert "already defined" in analyzer.errors[0].message
        
    def test_duplicate_parameter_names(self):
        """Test duplicate parameter names"""
        code = """
def add(x, x):
    return x
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 1
        assert "Duplicate parameter" in analyzer.errors[0].message
        
    def test_undefined_function_call(self):
        """Test calling undefined function"""
        code = """
x = foo()
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 1
        assert "Undefined function 'foo'" in analyzer.errors[0].message
        
    def test_calling_non_function(self):
        """Test calling a variable as function"""
        code = """
x = 5
y = x()
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 1
        assert "not a function" in analyzer.errors[0].message


class TestComplexPrograms:
    """Test semantic analysis on complex programs"""
    
    def test_factorial_function(self):
        """Test factorial function (from Week 6/7 tests)"""
        code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        
        func_symbol = analyzer.symbol_table.lookup('factorial')
        assert func_symbol is not None
        assert func_symbol.symbol_type == SymbolType.FUNCTION
        
    def test_nested_scopes(self):
        """Test nested function scopes"""
        code = """
x = 10

def outer():
    y = 20
    if x == 10:
        z = 30
        result = x + y + z
        return result
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        
    def test_while_loop_with_variables(self):
        """Test while loop variable usage"""
        code = """
x = 10
while x > 0:
    x = x - 1
    print(x)
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 0
        
    def test_undefined_in_nested_scope(self):
        """Test undefined variable in nested scope"""
        code = """
def foo():
    if True:
        x = undefined_var
"""
        analyzer = analyze_code(code)
        assert len(analyzer.errors) == 1
        assert "Undefined variable 'undefined_var'" in analyzer.errors[0].message


class TestDiagnostics:
    """Test diagnostic reporting"""
    
    def test_diagnostic_report_format(self):
        """Test diagnostic report formatting"""
        code = """
x = undefined
y = another_undefined
"""
        analyzer = analyze_code(code)
        report = analyzer.get_diagnostics()
        
        assert "SEMANTIC ERRORS" in report
        assert "undefined" in report
        assert "Line" in report
        
    def test_no_errors_diagnostic(self):
        """Test diagnostic when no errors"""
        code = """
x = 5
y = x + 10
"""
        analyzer = analyze_code(code)
        report = analyzer.get_diagnostics()
        
        assert "No semantic errors" in report or "✓" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

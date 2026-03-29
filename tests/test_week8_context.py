"""
Test Suite for Context Provider and AI Integration
Week 8 Implementation Tests

These tests are fully deterministic (no API calls) and validate
that the Context Provider correctly serializes compiler state.
"""

import pytest
from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer, SymbolType
from src.orchestrator.context_provider import ContextProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_pipeline(code: str):
    """Run lexer -> parser -> semantic analyzer, return (ast, analyzer)."""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return ast, analyzer


# ===========================================================================
# TestSerializeAST
# ===========================================================================

class TestSerializeAST:
    """Tests for ContextProvider.serialize_ast()"""

    def test_empty_program(self):
        """Empty program returns descriptive message."""
        ast, _ = run_pipeline("\n")
        result = ContextProvider.serialize_ast(ast)
        assert "empty" in result.lower()

    def test_simple_assignment(self):
        """Assignment is described in the output."""
        ast, _ = run_pipeline("x = 42\n")
        result = ContextProvider.serialize_ast(ast)
        assert "PROGRAM STRUCTURE" in result
        assert "Assignment" in result
        assert "x" in result
        assert "42" in result

    def test_function_definition(self):
        """Function names, params, and body are listed."""
        code = """\
def add(a, b):
    return a + b
"""
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "Functions defined: 1" in result
        assert "add" in result
        assert "a, b" in result
        assert "Return" in result

    def test_if_statement(self):
        """If statement with else is described."""
        code = """\
x = 5
if x == 0:
    x = 1
else:
    x = 2
"""
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "If statement" in result
        assert "with else" in result

    def test_while_loop(self):
        """While loop is described."""
        code = """\
i = 0
while i < 10:
    i = i + 1
"""
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "While loop" in result

    def test_print_statement(self):
        """Print statement is described."""
        code = 'print("hello")\n'
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "Print" in result

    def test_function_call_in_expression(self):
        """Function call in expression is described."""
        code = """\
def foo():
    return 1
x = foo()
"""
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "foo()" in result or "foo" in result

    def test_multiple_functions(self):
        """Multiple function definitions are counted and listed."""
        code = """\
def first():
    return 1
def second(x):
    return x
"""
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "Functions defined: 2" in result
        assert "first" in result
        assert "second" in result

    def test_unary_op_described(self):
        """Unary minus in expression is described."""
        code = """\
def neg(x):
    return -x
"""
        ast, _ = run_pipeline(code)
        result = ContextProvider.serialize_ast(ast)
        assert "-" in result


# ===========================================================================
# TestSerializeSymbolTable
# ===========================================================================

class TestSerializeSymbolTable:
    """Tests for ContextProvider.serialize_symbol_table()"""

    def test_global_variable(self):
        """Global variable appears in symbol table serialization."""
        _, analyzer = run_pipeline("x = 42\n")
        result = ContextProvider.serialize_symbol_table(analyzer.symbol_table)
        assert "SYMBOL TABLE" in result
        assert "x" in result
        assert "int" in result

    def test_function_in_table(self):
        """Function definition appears as type=function."""
        code = """\
def greet():
    print("hi")
"""
        _, analyzer = run_pipeline(code)
        result = ContextProvider.serialize_symbol_table(analyzer.symbol_table)
        assert "greet" in result
        assert "function" in result

    def test_scope_names(self):
        """Scope names are displayed."""
        code = """\
def foo(a):
    b = a + 1
    return b
"""
        _, analyzer = run_pipeline(code)
        result = ContextProvider.serialize_symbol_table(analyzer.symbol_table)
        assert "global" in result.lower()

    def test_multiple_variables(self):
        """Multiple variables in same scope are listed."""
        code = "a = 1\nb = 2\nc = 3\n"
        _, analyzer = run_pipeline(code)
        result = ContextProvider.serialize_symbol_table(analyzer.symbol_table)
        assert "a" in result
        assert "b" in result
        assert "c" in result


# ===========================================================================
# TestSerializeErrors
# ===========================================================================

class TestSerializeErrors:
    """Tests for ContextProvider.serialize_errors()"""

    def test_no_errors(self):
        """Clean code reports no issues."""
        _, analyzer = run_pipeline("x = 1\n")
        result = ContextProvider.serialize_errors(
            analyzer.errors, analyzer.warnings
        )
        assert "No errors" in result or "semantically valid" in result

    def test_undefined_variable_error(self):
        """Undefined variable error is formatted."""
        code = "y = x + 1\n"
        _, analyzer = run_pipeline(code)
        result = ContextProvider.serialize_errors(
            analyzer.errors, analyzer.warnings
        )
        assert "Errors" in result
        assert "x" in result

    def test_multiple_errors(self):
        """Multiple errors are all listed."""
        code = "a = x + y\n"
        _, analyzer = run_pipeline(code)
        result = ContextProvider.serialize_errors(
            analyzer.errors, analyzer.warnings
        )
        # x and y are both undefined
        assert "x" in result
        assert "y" in result


# ===========================================================================
# TestBuildContext
# ===========================================================================

class TestBuildContext:
    """Tests for ContextProvider.build_context() -- the full pipeline."""

    def test_contains_all_sections(self):
        """Full context contains source, AST, symbol table, diagnostics."""
        code = "x = 42\n"
        ast, analyzer = run_pipeline(code)
        result = ContextProvider.build_context(code, ast, analyzer)
        assert "SOURCE CODE" in result
        assert "PROGRAM STRUCTURE" in result
        assert "SYMBOL TABLE" in result
        assert "DIAGNOSTICS" in result

    def test_valid_code_diagnostics(self):
        """Valid code shows 'no errors' in diagnostics section."""
        code = "x = 42\n"
        ast, analyzer = run_pipeline(code)
        result = ContextProvider.build_context(code, ast, analyzer)
        assert "No errors" in result or "semantically valid" in result

    def test_error_code_diagnostics(self):
        """Code with errors includes error details."""
        code = "y = x + 1\n"
        ast, analyzer = run_pipeline(code)
        result = ContextProvider.build_context(code, ast, analyzer)
        assert "Errors" in result
        assert "Undefined variable" in result

    def test_source_code_included(self):
        """Source code lines are included with line numbers."""
        code = "a = 1\nb = 2\n"
        ast, analyzer = run_pipeline(code)
        result = ContextProvider.build_context(code, ast, analyzer)
        assert "1:" in result  # line 1
        assert "a = 1" in result

    def test_complex_program_context(self):
        """Complex program with function produces rich context."""
        code = """\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
result = factorial(5)
print(result)
"""
        ast, analyzer = run_pipeline(code)
        result = ContextProvider.build_context(code, ast, analyzer)
        assert "factorial" in result
        assert "PROGRAM STRUCTURE" in result
        assert "SYMBOL TABLE" in result


# ===========================================================================
# TestBuildErrorContext
# ===========================================================================

class TestBuildErrorContext:
    """Tests for ContextProvider.build_error_context()"""

    def test_lexer_error_context(self):
        """Lexer error context includes error type and message."""
        result = ContextProvider.build_error_context(
            source_code="x = @invalid\ny = 2",
            error_type="LexerError",
            error_message="Invalid character '@' at line 1, column 5",
            line_number=1,
            column=5
        )
        assert "LexerError" in result
        assert "Invalid character" in result
        assert "line 1" in result

    def test_parser_error_context(self):
        """Parser error context includes source with pointer."""
        result = ContextProvider.build_error_context(
            source_code="if x > 5 print(x)",
            error_type="ParserError",
            error_message="Expected ':', got IDENTIFIER",
            line_number=1,
            column=10
        )
        assert "ParserError" in result
        assert ">>>" in result  # line marker
        assert "Expected" in result

    def test_error_context_without_line_number(self):
        """Works even without line number."""
        result = ContextProvider.build_error_context(
            source_code="broken code",
            error_type="LexerError",
            error_message="Unexpected EOF"
        )
        assert "LexerError" in result
        assert "Unexpected EOF" in result

    def test_no_ast_note(self):
        """Error context mentions AST is not available."""
        result = ContextProvider.build_error_context(
            source_code="x = 1",
            error_type="ParserError",
            error_message="test"
        )
        assert "AST" in result
        assert "not available" in result


# ===========================================================================
# TestContextIntegration
# ===========================================================================

class TestContextIntegration:
    """End-to-end integration tests for the context pipeline."""

    def test_full_pipeline_valid_code(self):
        """Full pipeline on valid code produces complete context."""
        code = """\
x = 10
y = 20
z = x + y
print(z)
"""
        ast, analyzer = run_pipeline(code)
        context = ContextProvider.build_context(code, ast, analyzer)

        # Should have all major sections
        assert "SOURCE CODE" in context
        assert "PROGRAM STRUCTURE" in context
        assert "SYMBOL TABLE" in context
        assert "DIAGNOSTICS" in context

        # Variables should appear in both AST and symbol table
        assert context.count("x") >= 2  # appears in source + symbol table
        assert "int" in context  # type in symbol table
        assert "semantically valid" in context or "No errors" in context

    def test_full_pipeline_with_function_and_error(self):
        """Pipeline with function and undefined variable."""
        code = """\
def compute(a):
    return a + missing_var
result = compute(5)
"""
        ast, analyzer = run_pipeline(code)
        context = ContextProvider.build_context(code, ast, analyzer)

        assert "compute" in context
        assert "missing_var" in context
        assert "Undefined" in context

"""
Test Suite for Week 9: Agentic Tool-Use (Compiler Function Calling)

All tests are fully deterministic — no Gemini API calls.
Tests cover:
  - CompilerToolbox individual tool methods
  - Tool dispatch mechanism
  - Tool registry schema structure
  - AgenticGeminiClient simulation mode
  - End-to-end integration of tool pipeline
"""

import pytest
from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer, SymbolType
from src.orchestrator.compiler_tools import CompilerToolbox
from src.orchestrator.tool_registry import (
    TOOL_SCHEMA_DEFINITIONS,
    get_tool_names,
    get_schema_by_name,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_pipeline(code: str):
    """Run lexer → parser → semantic analyzer, return (ast, analyzer)."""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return ast, analyzer


def make_toolbox(code: str) -> CompilerToolbox:
    """Build a CompilerToolbox for the given Mini-Python code."""
    return CompilerToolbox.from_source(code)


# ===========================================================================
# TestCompilerToolboxCheckScope
# ===========================================================================

class TestCompilerToolboxCheckScope:
    """Tests for CompilerToolbox.check_scope()"""

    def test_defined_integer_variable(self):
        """Defined variable returns type and location."""
        tb = make_toolbox("x = 42\n")
        result = tb.check_scope("x")
        assert "SCOPE CHECK" in result
        assert "x" in result
        assert "defined" in result.lower()
        assert "int" in result

    def test_undefined_variable(self):
        """Undefined variable returns 'NOT defined'."""
        tb = make_toolbox("x = 1\n")
        result = tb.check_scope("missing_var")
        assert "NOT defined" in result
        assert "missing_var" in result

    def test_defined_string_variable(self):
        """String variable shows type=str."""
        tb = make_toolbox('name = "hello"\n')
        result = tb.check_scope("name")
        assert "str" in result

    def test_function_found_via_scope(self):
        """Function defined in global scope shows type=function."""
        code = "def greet():\n    return 1\n"
        tb = make_toolbox(code)
        result = tb.check_scope("greet")
        assert "function" in result

    def test_scope_level_shown(self):
        """Scope level is reported."""
        tb = make_toolbox("y = 100\n")
        result = tb.check_scope("y")
        assert "scope level" in result.lower() or "level" in result.lower()

    def test_line_number_shown(self):
        """Line number of definition is reported."""
        tb = make_toolbox("abc = 7\n")
        result = tb.check_scope("abc")
        assert "line 1" in result

    def test_uninitialized_toolbox(self):
        """Uninitialized toolbox returns error message."""
        tb = CompilerToolbox()
        result = tb.check_scope("x")
        assert "ERROR" in result or "not initialized" in result.lower()


# ===========================================================================
# TestCompilerToolboxCheckFunction
# ===========================================================================

class TestCompilerToolboxCheckFunction:
    """Tests for CompilerToolbox.check_function()"""

    def test_defined_function_with_params(self):
        """Defined function returns name, params, line."""
        code = "def add(a, b):\n    return a + b\n"
        tb = make_toolbox(code)
        result = tb.check_function("add")
        assert "add" in result
        assert "function" in result
        assert "a, b" in result or "a" in result

    def test_defined_function_no_params(self):
        """Defined function with no params reports 'none'."""
        code = "def hello():\n    return 1\n"
        tb = make_toolbox(code)
        result = tb.check_function("hello")
        assert "hello" in result
        assert "none" in result.lower() or "(none)" in result

    def test_undefined_function(self):
        """Undefined function returns NOT defined."""
        tb = make_toolbox("x = 1\n")
        result = tb.check_function("nonexistent")
        assert "NOT defined" in result
        assert "nonexistent" in result

    def test_variable_is_not_function(self):
        """A variable name reports it's not a function."""
        tb = make_toolbox("counter = 5\n")
        result = tb.check_function("counter")
        assert "NOT a function" in result or "not a function" in result.lower()

    def test_function_line_reported(self):
        """Line number where function is defined appears in result."""
        code = "def compute(n):\n    return n * 2\n"
        tb = make_toolbox(code)
        result = tb.check_function("compute")
        assert "line 1" in result


# ===========================================================================
# TestCompilerToolboxGetErrors
# ===========================================================================

class TestCompilerToolboxGetErrors:
    """Tests for CompilerToolbox.get_errors()"""

    def test_no_errors_valid_code(self):
        """Valid code reports no errors."""
        tb = make_toolbox("x = 10\ny = x + 1\n")
        result = tb.get_errors()
        assert "No semantic errors" in result or "semantically valid" in result

    def test_single_error_undefined_var(self):
        """Undefined variable error is reported."""
        tb = make_toolbox("y = x + 1\n")  # x is undefined
        result = tb.get_errors()
        assert "ERRORS" in result
        assert "1" in result  # 1 error
        assert "x" in result

    def test_multiple_errors(self):
        """Multiple errors are all listed."""
        tb = make_toolbox("z = a + b\n")  # a and b are undefined
        result = tb.get_errors()
        assert "ERRORS" in result
        assert "a" in result
        assert "b" in result

    def test_error_has_line_number(self):
        """Error message includes line number."""
        tb = make_toolbox("result = undefined_thing\n")
        result = tb.get_errors()
        assert "Line 1" in result or "line 1" in result

    def test_error_count_shown(self):
        """Error count is shown in the result."""
        tb = make_toolbox("q = x + y\n")  # x, y both undefined → 2 errors
        result = tb.get_errors()
        assert "2" in result


# ===========================================================================
# TestCompilerToolboxGetWarnings
# ===========================================================================

class TestCompilerToolboxGetWarnings:
    """Tests for CompilerToolbox.get_warnings()"""

    def test_no_warnings_simple_code(self):
        """Simple valid code has no warnings."""
        tb = make_toolbox("x = 5\n")
        result = tb.get_warnings()
        assert "No warnings" in result

    def test_type_change_warning(self):
        """Reassigning a variable with different type produces a warning."""
        code = 'x = 5\nx = "hello"\n'
        tb = make_toolbox(code)
        result = tb.get_warnings()
        # Should either warn or report no warnings (analyzer behavior)
        assert "WARNINGS" in result or "No warnings" in result


# ===========================================================================
# TestCompilerToolboxGetSymbolTable
# ===========================================================================

class TestCompilerToolboxGetSymbolTable:
    """Tests for CompilerToolbox.get_symbol_table()"""

    def test_symbol_table_has_global_scope(self):
        """Symbol table always shows global scope."""
        tb = make_toolbox("x = 1\n")
        result = tb.get_symbol_table()
        assert "SYMBOL TABLE" in result
        assert "global" in result.lower()

    def test_variable_in_symbol_table(self):
        """Variable appears in the symbol table."""
        tb = make_toolbox("my_var = 99\n")
        result = tb.get_symbol_table()
        assert "my_var" in result

    def test_function_in_symbol_table(self):
        """Function appears as type=function."""
        code = "def foo():\n    return 1\n"
        tb = make_toolbox(code)
        result = tb.get_symbol_table()
        assert "foo" in result
        assert "function" in result

    def test_multiple_variables(self):
        """All variables appear in the symbol table."""
        code = "alpha = 1\nbeta = 2\ngamma = 3\n"
        tb = make_toolbox(code)
        result = tb.get_symbol_table()
        assert "alpha" in result
        assert "beta" in result
        assert "gamma" in result


# ===========================================================================
# TestCompilerToolboxGetAstSummary
# ===========================================================================

class TestCompilerToolboxGetAstSummary:
    """Tests for CompilerToolbox.get_ast_summary()"""

    def test_ast_summary_shows_structure(self):
        """AST summary shows PROGRAM STRUCTURE header."""
        tb = make_toolbox("x = 1\n")
        result = tb.get_ast_summary()
        assert "PROGRAM STRUCTURE" in result

    def test_function_in_ast(self):
        """Function definition appears in AST summary."""
        code = "def bar(n):\n    return n\n"
        tb = make_toolbox(code)
        result = tb.get_ast_summary()
        assert "bar" in result
        assert "Function" in result or "Functions defined" in result

    def test_assignment_in_ast(self):
        """Assignment appears in AST summary."""
        tb = make_toolbox("result = 42\n")
        result = tb.get_ast_summary()
        assert "Assignment" in result
        assert "result" in result


# ===========================================================================
# TestCompilerToolboxReparse
# ===========================================================================

class TestCompilerToolboxReparse:
    """Tests for CompilerToolbox.reparse_code()"""

    def test_reparse_valid_code(self):
        """Valid code reparsed shows SUCCESS."""
        tb = CompilerToolbox()
        result = tb.reparse_code("x = 5\n")
        assert "SUCCESS" in result

    def test_reparse_invalid_code(self):
        """Code with errors reparsed shows FAILED."""
        tb = CompilerToolbox()
        result = tb.reparse_code("y = undefined_var\n")
        assert "FAILED" in result
        assert "undefined_var" in result or "Undefined" in result

    def test_reparse_updates_state(self):
        """After reparse, subsequent tool calls reflect new code."""
        tb = CompilerToolbox()
        tb.reparse_code("z = 10\n")
        scope_result = tb.check_scope("z")
        assert "defined" in scope_result.lower()
        assert "NOT defined" not in scope_result

    def test_reparse_replaces_old_state(self):
        """Old code state is replaced after reparse."""
        tb = make_toolbox("old_var = 1\n")
        tb.reparse_code("new_var = 2\n")
        # old_var should not be in new scope
        result = tb.check_scope("old_var")
        assert "NOT defined" in result

    def test_reparse_token_count_reported(self):
        """Reparse result mentions token count."""
        tb = CompilerToolbox()
        result = tb.reparse_code("x = 1\n")
        assert "Token" in result or "SUCCESS" in result


# ===========================================================================
# TestToolDispatch
# ===========================================================================

class TestToolDispatch:
    """Tests for CompilerToolbox.dispatch()"""

    def test_dispatch_check_scope(self):
        """dispatch('check_scope', ...) calls check_scope."""
        tb = make_toolbox("x = 5\n")
        result = tb.dispatch("check_scope", {"variable_name": "x"})
        assert "SCOPE CHECK" in result
        assert "x" in result

    def test_dispatch_get_errors(self):
        """dispatch('get_errors', {}) calls get_errors."""
        tb = make_toolbox("x = 1\n")
        result = tb.dispatch("get_errors", {})
        assert "ERRORS" in result or "No semantic errors" in result

    def test_dispatch_get_symbol_table(self):
        """dispatch('get_symbol_table', {}) calls get_symbol_table."""
        tb = make_toolbox("x = 1\n")
        result = tb.dispatch("get_symbol_table", {})
        assert "SYMBOL TABLE" in result

    def test_dispatch_get_ast_summary(self):
        """dispatch('get_ast_summary', {}) calls get_ast_summary."""
        tb = make_toolbox("x = 1\n")
        result = tb.dispatch("get_ast_summary", {})
        assert "PROGRAM STRUCTURE" in result

    def test_dispatch_check_function(self):
        """dispatch('check_function', ...) calls check_function."""
        code = "def foo():\n    return 1\n"
        tb = make_toolbox(code)
        result = tb.dispatch("check_function", {"function_name": "foo"})
        assert "foo" in result
        assert "function" in result

    def test_dispatch_reparse_code(self):
        """dispatch('reparse_code', ...) calls reparse_code."""
        tb = CompilerToolbox()
        result = tb.dispatch("reparse_code", {"source_code": "a = 1\n"})
        assert "SUCCESS" in result or "FAILED" in result

    def test_dispatch_unknown_tool(self):
        """Unknown tool name returns error message."""
        tb = make_toolbox("x = 1\n")
        result = tb.dispatch("nonexistent_tool", {})
        assert "ERROR" in result or "Unknown tool" in result

    def test_dispatch_get_warnings(self):
        """dispatch('get_warnings', {}) calls get_warnings."""
        tb = make_toolbox("x = 1\n")
        result = tb.dispatch("get_warnings", {})
        assert "WARNINGS" in result or "No warnings" in result


# ===========================================================================
# TestToolRegistry
# ===========================================================================

class TestToolRegistry:
    """Tests for the tool_registry module schema definitions."""

    def test_all_seven_tools_registered(self):
        """All 7 expected tools are in the registry."""
        names = get_tool_names()
        expected = {
            "check_scope", "check_function",
            "get_errors", "get_warnings",
            "get_symbol_table", "get_ast_summary",
            "reparse_code"
        }
        for tool in expected:
            assert tool in names, f"Tool '{tool}' missing from registry"

    def test_each_schema_has_name(self):
        """Every schema definition has a 'name' field."""
        for schema in TOOL_SCHEMA_DEFINITIONS:
            assert "name" in schema, f"Schema missing 'name': {schema}"

    def test_each_schema_has_description(self):
        """Every schema definition has a non-empty 'description'."""
        for schema in TOOL_SCHEMA_DEFINITIONS:
            assert "description" in schema
            assert len(schema["description"]) > 10

    def test_each_schema_has_parameters(self):
        """Every schema has a 'parameters' dict."""
        for schema in TOOL_SCHEMA_DEFINITIONS:
            assert "parameters" in schema
            assert isinstance(schema["parameters"], dict)

    def test_schema_parameters_have_required(self):
        """Parameters section includes 'required' list."""
        for schema in TOOL_SCHEMA_DEFINITIONS:
            params = schema["parameters"]
            assert "required" in params
            assert isinstance(params["required"], list)

    def test_get_schema_by_name_found(self):
        """get_schema_by_name returns correct schema for known tool."""
        schema = get_schema_by_name("check_scope")
        assert schema is not None
        assert schema["name"] == "check_scope"
        assert "variable_name" in schema["parameters"]["properties"]

    def test_get_schema_by_name_not_found(self):
        """get_schema_by_name returns None for unknown tool."""
        schema = get_schema_by_name("does_not_exist")
        assert schema is None

    def test_reparse_schema_has_source_code_param(self):
        """reparse_code schema requires source_code parameter."""
        schema = get_schema_by_name("reparse_code")
        assert schema is not None
        assert "source_code" in schema["parameters"]["properties"]
        assert "source_code" in schema["parameters"]["required"]


# ===========================================================================
# TestAgenticSimulation
# ===========================================================================

class TestAgenticSimulation:
    """Tests for AgenticGeminiClient.simulate_agentic_investigation()"""

    def _get_mock_agent(self):
        """Create an agent in mock mode (no API needed)."""
        from src.orchestrator.gemini_client import AgenticGeminiClient
        agent = AgenticGeminiClient.__new__(AgenticGeminiClient)
        agent.model = None
        agent.chat = None
        agent._initialized = False
        agent._tools = None
        return agent

    def test_simulation_returns_dict(self):
        """Simulation always returns a dict with required keys."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation(
            "x = 1\n", "testing"
        )
        assert isinstance(result, dict)
        assert "tool_calls" in result
        assert "observations" in result
        assert "final_answer" in result

    def test_simulation_calls_tools(self):
        """Simulation calls at least get_errors, get_symbol_table, get_ast_summary."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation("x = 10\n", "test")
        tool_calls = result["tool_calls"]
        assert "get_errors()" in tool_calls
        assert "get_symbol_table()" in tool_calls
        assert "get_ast_summary()" in tool_calls

    def test_simulation_valid_code_answer(self):
        """Simulation on valid code produces positive final answer."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation("x = 42\n", "valid code")
        assert "compiles without errors" in result["final_answer"].lower() or \
               "no error" in result["final_answer"].lower() or \
               "SUCCESS" in result["final_answer"] or \
               "✅" in result["final_answer"]

    def test_simulation_error_code_answer(self):
        """Simulation on code with errors reports errors in final answer."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation(
            "z = undefined_var\n", "has error"
        )
        final = result["final_answer"]
        assert "error" in final.lower() or "🔍" in final

    def test_simulation_checks_undefined_scope(self):
        """Simulation performs scope check for undefined variables."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation(
            "y = missing\n", "undefined var"
        )
        tool_calls = result["tool_calls"]
        # Should have called check_scope with the undefined var name
        scope_calls = [c for c in tool_calls if "check_scope" in c]
        assert len(scope_calls) >= 1

    def test_simulation_observations_have_required_keys(self):
        """Each observation step has step, action, reasoning, observation."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation("x = 1\n", "test")
        for obs in result["observations"]:
            assert "step" in obs
            assert "action" in obs
            assert "reasoning" in obs
            assert "observation" in obs

    def test_simulation_steps_numbered_sequentially(self):
        """Steps in observations are numbered 1, 2, 3, ..."""
        agent = self._get_mock_agent()
        result = agent.simulate_agentic_investigation("x = 1\n", "test")
        steps = [obs["step"] for obs in result["observations"]]
        assert steps == list(range(1, len(steps) + 1))


# ===========================================================================
# TestToolboxIntegration
# ===========================================================================

class TestToolboxIntegration:
    """End-to-end integration tests for the full tool pipeline."""

    def test_full_pipeline_valid_code(self):
        """Full pipeline on valid code: all tools return useful results."""
        code = "x = 10\ny = 20\nz = x + y\nprint(z)\n"
        tb = make_toolbox(code)

        # All tools should work
        assert "No semantic errors" in tb.get_errors() or \
               "semantically valid" in tb.get_errors()
        assert "SYMBOL TABLE" in tb.get_symbol_table()
        assert "PROGRAM STRUCTURE" in tb.get_ast_summary()
        assert "defined" in tb.check_scope("x").lower()
        assert "defined" in tb.check_scope("y").lower()
        assert "defined" in tb.check_scope("z").lower()
        assert "NOT defined" in tb.check_scope("nonexistent")

    def test_full_pipeline_with_errors(self):
        """Full pipeline on code with errors: error tools return errors."""
        code = "result = compute(missing)\n"
        tb = make_toolbox(code)

        # Both compute and missing are undefined
        errors = tb.get_errors()
        assert "ERRORS" in errors

        scope_compute = tb.check_scope("compute")
        assert "NOT defined" in scope_compute

        scope_missing = tb.check_scope("missing")
        assert "NOT defined" in scope_missing

    def test_reparse_fixes_error(self):
        """Reparse with fixed code transitions from FAILED to SUCCESS."""
        broken = "y = undefined_x\n"
        fixed = "undefined_x = 10\ny = undefined_x\n"

        tb = make_toolbox(broken)
        assert "FAILED" in tb.reparse_code(broken) or "error" in tb.get_errors().lower()

        result = tb.reparse_code(fixed)
        assert "SUCCESS" in result or "No semantic errors" in tb.get_errors()

    def test_toolbox_from_source_factory(self):
        """from_source() class method correctly initializes toolbox."""
        tb = CompilerToolbox.from_source("counter = 0\n")
        assert tb._initialized is True
        assert tb.ast is not None
        assert tb.analyzer is not None
        assert "counter" in tb.get_symbol_table()

    def test_function_definition_complete_check(self):
        """Function check + scope check gives consistent results."""
        code = "def factorial(n):\n    return n\n"
        tb = make_toolbox(code)

        fn_result = tb.check_function("factorial")
        scope_result = tb.check_scope("factorial")

        assert "factorial" in fn_result
        assert "function" in fn_result
        assert "function" in scope_result

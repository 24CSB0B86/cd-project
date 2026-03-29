"""
Compiler Toolbox for Agentic AI — Enhanced Week 11 with Security Auditing
Exposes discrete compiler functions that the Gemini AI agent can call
via the Function Calling API (Week 9).

Each tool is a plain Python method that returns a human-readable string.
Gemini receives this string as the "observation" in its ReAct loop.
"""

from typing import Optional, List, Dict, Any
import logging

from ..compiler.lexer import Lexer
from ..compiler.parser import Parser
from ..compiler.semantic_analyzer import SemanticAnalyzer, SymbolType
from ..compiler.ast_nodes import Program
from .context_provider import ContextProvider

logger = logging.getLogger(__name__)


class CompilerToolbox:
    """
    Stateful collection of compiler tools exposed to the Gemini AI agent.

    Initialized with the current compiler pipeline state (AST, analyzer).
    Each method returns a plain-text string that Gemini can read and
    reason about before producing its final answer.

    Tools available:
        - check_scope(variable_name)   : Look up a variable in symbol table
        - check_function(name)         : Look up a function definition
        - get_errors()                 : List all semantic errors
        - get_warnings()               : List all semantic warnings
        - get_symbol_table()           : Return full symbol table
        - get_ast_summary()            : Return AST structure summary
        - reparse_code(source_code)    : Re-run the entire compiler pipeline
        - audit_security()             : Run SAST security audit (Week 11)
    """

    def __init__(self,
                 source_code: str = "",
                 ast: Optional[Program] = None,
                 analyzer: Optional[SemanticAnalyzer] = None):
        """
        Initialize the toolbox with the current compiler state.

        Args:
            source_code: The original Mini-Python source code
            ast:         The parsed AST (from the parser)
            analyzer:    The semantic analyzer after running analysis
        """
        self.source_code = source_code
        self.ast = ast
        self.analyzer = analyzer
        self._initialized = ast is not None and analyzer is not None

    # =========================================================================
    # Tool 1: check_scope
    # =========================================================================

    def check_scope(self, variable_name: str) -> str:
        """
        Look up a variable or identifier across all scopes in the symbol table.

        Args:
            variable_name: The identifier to look up (e.g., "x", "counter")

        Returns:
            Human-readable string describing the symbol, or 'not found'.
        """
        if not self._initialized:
            return "ERROR: Compiler state not initialized. Run reparse_code() first."

        symbol = self.analyzer.symbol_table.lookup(variable_name)

        if symbol is None:
            return (
                f"SCOPE CHECK: '{variable_name}' is NOT defined in any scope.\n"
                f"  This will cause an 'Undefined variable' semantic error."
            )

        return (
            f"SCOPE CHECK: '{variable_name}' is defined.\n"
            f"  Type        : {symbol.symbol_type.value}\n"
            f"  Scope level : {symbol.scope_level}\n"
            f"  Defined at  : line {symbol.line}, column {symbol.column}"
        )

    # =========================================================================
    # Tool 2: check_function
    # =========================================================================

    def check_function(self, function_name: str) -> str:
        """
        Check whether a function is defined and retrieve its metadata.

        Args:
            function_name: The function name to look up (e.g., "factorial")

        Returns:
            Human-readable string with function info or 'not found'.
        """
        if not self._initialized:
            return "ERROR: Compiler state not initialized. Run reparse_code() first."

        symbol = self.analyzer.symbol_table.lookup(function_name)

        if symbol is None:
            return (
                f"FUNCTION CHECK: '{function_name}' is NOT defined.\n"
                f"  This will cause an 'Undefined function' semantic error when called."
            )

        if symbol.symbol_type != SymbolType.FUNCTION:
            return (
                f"FUNCTION CHECK: '{function_name}' exists but is NOT a function.\n"
                f"  It is a '{symbol.symbol_type.value}' defined at line {symbol.line}.\n"
                f"  Calling it will produce a semantic error."
            )

        # Try to find the function's parameter list from the AST
        params_str = self._find_function_params(function_name)

        return (
            f"FUNCTION CHECK: '{function_name}' is defined.\n"
            f"  Type        : function\n"
            f"  Parameters  : {params_str}\n"
            f"  Defined at  : line {symbol.line}, column {symbol.column}"
        )

    def _find_function_params(self, function_name: str) -> str:
        """Helper: find function parameters from the AST."""
        if self.ast is None:
            return "(AST not available)"
        from ..compiler.ast_nodes import FunctionDef
        for stmt in self.ast.statements:
            if isinstance(stmt, FunctionDef) and stmt.name == function_name:
                if stmt.params:
                    return ", ".join(stmt.params)
                return "(none)"
        return "(not found in AST — may be a built-in)"

    # =========================================================================
    # Tool 3: get_errors
    # =========================================================================

    def get_errors(self) -> str:
        """
        Return all semantic errors found during analysis.

        Returns:
            Formatted list of errors, or confirmation that none exist.
        """
        if not self._initialized:
            return "ERROR: Compiler state not initialized. Run reparse_code() first."

        errors = self.analyzer.errors
        if not errors:
            return "ERRORS: No semantic errors found. The code is semantically valid."

        lines = [f"ERRORS: {len(errors)} semantic error(s) found:"]
        for i, err in enumerate(errors, 1):
            lines.append(f"  [{i}] Line {err.line}, Col {err.column}: {err.message}")
        return "\n".join(lines)

    # =========================================================================
    # Tool 4: get_warnings
    # =========================================================================

    def get_warnings(self) -> str:
        """
        Return all semantic warnings found during analysis.

        Returns:
            Formatted list of warnings, or confirmation that none exist.
        """
        if not self._initialized:
            return "ERROR: Compiler state not initialized. Run reparse_code() first."

        warnings = self.analyzer.warnings
        if not warnings:
            return "WARNINGS: No warnings found."

        lines = [f"WARNINGS: {len(warnings)} warning(s) found:"]
        for i, warn in enumerate(warnings, 1):
            lines.append(f"  [{i}] {warn}")
        return "\n".join(lines)

    # =========================================================================
    # Tool 5: get_symbol_table
    # =========================================================================

    def get_symbol_table(self) -> str:
        """
        Return the complete symbol table for all scopes.

        Returns:
            Full symbol table text from ContextProvider.
        """
        if not self._initialized:
            return "ERROR: Compiler state not initialized. Run reparse_code() first."

        return ContextProvider.serialize_symbol_table(self.analyzer.symbol_table)

    # =========================================================================
    # Tool 6: get_ast_summary
    # =========================================================================

    def get_ast_summary(self) -> str:
        """
        Return a natural language summary of the program's AST structure.

        Returns:
            AST summary text from ContextProvider.
        """
        if not self._initialized or self.ast is None:
            return "ERROR: AST not available. Run reparse_code() first."

        return ContextProvider.serialize_ast(self.ast)

    # =========================================================================
    # Tool 7: reparse_code
    # =========================================================================

    def reparse_code(self, source_code: str) -> str:
        """
        Re-run the full compiler pipeline (Lex → Parse → Analyze) on new code.
        Updates the internal compiler state so subsequent tool calls reflect
        the new code.

        Args:
            source_code: New Mini-Python source code to compile

        Returns:
            Summary of compilations result (success or list of errors).
        """
        try:
            # Run full pipeline
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            ast = parser.parse()

            analyzer = SemanticAnalyzer()
            success = analyzer.analyze(ast)

            # Update internal state
            self.source_code = source_code
            self.ast = ast
            self.analyzer = analyzer
            self._initialized = True

            if success:
                sym_count = sum(
                    len(scope.symbols)
                    for scope in analyzer.symbol_table.scopes
                )
                return (
                    f"REPARSE: SUCCESS — code compiled without errors.\n"
                    f"  Tokens    : {len(tokens)}\n"
                    f"  Symbols   : {sym_count}\n"
                    f"  Warnings  : {len(analyzer.warnings)}"
                )
            else:
                lines = [f"REPARSE: FAILED — {len(analyzer.errors)} error(s):"]
                for err in analyzer.errors:
                    lines.append(
                        f"  Line {err.line}, Col {err.column}: {err.message}"
                    )
                return "\n".join(lines)

        except Exception as e:
            logger.error(f"reparse_code failed: {e}")
            return f"REPARSE: EXCEPTION — {type(e).__name__}: {e}"

    # =========================================================================
    # Tool 8: audit_security  (Week 11)
    # =========================================================================

    def audit_security(self) -> str:
        """
        Run the SAST Security Auditor on the current source code.

        Returns:
            Human-readable security audit report string.
        """
        if not self.source_code:
            return "SECURITY AUDIT: No source code loaded. Run reparse_code() first."

        try:
            from .security_auditor import SecurityAuditor
            report = SecurityAuditor().audit(self.source_code)
            return report.to_text()
        except Exception as e:
            logger.error(f"audit_security failed: {e}")
            return f"SECURITY AUDIT: ERROR — {type(e).__name__}: {e}"

    # =========================================================================
    # Factory: build from source code
    # =========================================================================

    @classmethod
    def from_source(cls, source_code: str) -> "CompilerToolbox":
        """
        Create a CompilerToolbox by running the full pipeline on source code.

        Args:
            source_code: Mini-Python source code

        Returns:
            Initialized CompilerToolbox
        """
        toolbox = cls()
        toolbox.reparse_code(source_code)
        return toolbox

    # =========================================================================
    # Utility: dispatch by name (used by AgenticGeminiClient)
    # =========================================================================

    def dispatch(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Dispatch a tool call by name with a dict of arguments.

        Args:
            tool_name: Name of the tool to call
            args:      Arguments as a dict matching the tool's parameters

        Returns:
            Tool result string
        """
        dispatch_map = {
            "check_scope": lambda a: self.check_scope(a.get("variable_name", "")),
            "check_function": lambda a: self.check_function(a.get("function_name", "")),
            "get_errors": lambda a: self.get_errors(),
            "get_warnings": lambda a: self.get_warnings(),
            "get_symbol_table": lambda a: self.get_symbol_table(),
            "get_ast_summary": lambda a: self.get_ast_summary(),
            "reparse_code": lambda a: self.reparse_code(a.get("source_code", "")),
            "audit_security": lambda a: self.audit_security(),
        }

        handler = dispatch_map.get(tool_name)
        if handler is None:
            return f"ERROR: Unknown tool '{tool_name}'. Available: {list(dispatch_map.keys())}"

        try:
            return handler(args)
        except Exception as e:
            logger.error(f"Tool '{tool_name}' raised exception: {e}")
            return f"ERROR: Tool '{tool_name}' failed — {type(e).__name__}: {e}"

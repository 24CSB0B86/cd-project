"""
Context Provider for Gemini AI Integration
Serializes compiler internal state (AST, Symbol Table, Errors) into
natural language descriptions that Gemini can reason about.
Week 8 Implementation
"""

from typing import List, Optional
from ..compiler.ast_nodes import *
from ..compiler.semantic_analyzer import (
    SemanticAnalyzer, SemanticError, SymbolTable, Scope, Symbol, SymbolType
)


class ContextProvider:
    """
    Converts compiler pipeline output into structured natural language
    context for the Gemini AI agent.
    
    The context helps Gemini understand:
    - What the program does (AST summary)
    - What variables/functions exist (Symbol Table)
    - What errors were found (Semantic diagnostics)
    """

    # ========================================================================
    # AST Serialization
    # ========================================================================

    @staticmethod
    def serialize_ast(ast: Program) -> str:
        """
        Convert AST into a human-readable natural language summary.
        
        Args:
            ast: The root Program node from the parser
            
        Returns:
            Multi-line string describing the program structure
        """
        if not ast or not ast.statements:
            return "The program is empty (no statements)."

        lines = ["PROGRAM STRUCTURE:"]
        
        functions = []
        global_statements = []
        
        for stmt in ast.statements:
            if isinstance(stmt, FunctionDef):
                functions.append(stmt)
            else:
                global_statements.append(stmt)
        
        # Summarize functions
        if functions:
            lines.append(f"  Functions defined: {len(functions)}")
            for func in functions:
                params_str = ", ".join(func.params) if func.params else "none"
                body_count = len(func.body.statements) if func.body else 0
                lines.append(f"    - {func.name}({params_str}) [line {func.line}, {body_count} statements]")
                
                # Describe function body at high level
                for body_stmt in (func.body.statements if func.body else []):
                    desc = ContextProvider._describe_statement(body_stmt, indent=6)
                    if desc:
                        lines.append(desc)
        
        # Summarize global statements
        if global_statements:
            lines.append(f"  Global statements: {len(global_statements)}")
            for stmt in global_statements:
                desc = ContextProvider._describe_statement(stmt, indent=4)
                if desc:
                    lines.append(desc)
        
        return "\n".join(lines)
    
    @staticmethod
    def _describe_statement(stmt: Statement, indent: int = 4) -> str:
        """Generate a one-line description of a statement."""
        pad = " " * indent
        
        if isinstance(stmt, Assignment):
            expr_desc = ContextProvider._describe_expression(stmt.value)
            return f"{pad}- Assignment: {stmt.target} = {expr_desc} [line {stmt.line}]"
        
        elif isinstance(stmt, IfStatement):
            cond_desc = ContextProvider._describe_expression(stmt.condition)
            has_else = "with else" if stmt.else_block else "without else"
            return f"{pad}- If statement: condition ({cond_desc}), {has_else} [line {stmt.line}]"
        
        elif isinstance(stmt, WhileStatement):
            cond_desc = ContextProvider._describe_expression(stmt.condition)
            return f"{pad}- While loop: condition ({cond_desc}) [line {stmt.line}]"
        
        elif isinstance(stmt, ReturnStatement):
            if stmt.value:
                val_desc = ContextProvider._describe_expression(stmt.value)
                return f"{pad}- Return: {val_desc} [line {stmt.line}]"
            return f"{pad}- Return (no value) [line {stmt.line}]"
        
        elif isinstance(stmt, PrintStatement):
            expr_desc = ContextProvider._describe_expression(stmt.expression)
            return f"{pad}- Print: {expr_desc} [line {stmt.line}]"
        
        elif isinstance(stmt, FunctionDef):
            params_str = ", ".join(stmt.params) if stmt.params else "none"
            return f"{pad}- Function: {stmt.name}({params_str}) [line {stmt.line}]"
        
        return f"{pad}- Unknown statement [line {stmt.line}]"
    
    @staticmethod
    def _describe_expression(expr: Expression) -> str:
        """Generate a concise description of an expression."""
        if isinstance(expr, Literal):
            if isinstance(expr.value, str):
                return f'string "{expr.value}"'
            return str(expr.value)
        
        elif isinstance(expr, Identifier):
            return expr.name
        
        elif isinstance(expr, BinaryOp):
            left = ContextProvider._describe_expression(expr.left)
            right = ContextProvider._describe_expression(expr.right)
            return f"{left} {expr.operator} {right}"
        
        elif isinstance(expr, UnaryOp):
            operand = ContextProvider._describe_expression(expr.operand)
            return f"{expr.operator}{operand}"
        
        elif isinstance(expr, FunctionCall):
            args = ", ".join(
                ContextProvider._describe_expression(a) for a in expr.arguments
            )
            return f"{expr.function_name}({args})"
        
        return "<?>"

    # ========================================================================
    # Symbol Table Serialization
    # ========================================================================

    @staticmethod
    def serialize_symbol_table(symbol_table: SymbolTable) -> str:
        """
        Convert the symbol table (scope stack) into readable text.
        
        Args:
            symbol_table: The SymbolTable from the semantic analyzer
            
        Returns:
            Multi-line string listing all scopes and their symbols
        """
        if not symbol_table.scopes:
            return "SYMBOL TABLE: (empty)"
        
        lines = ["SYMBOL TABLE:"]
        
        for scope in symbol_table.scopes:
            lines.append(f"  Scope: {scope.name} (level {scope.level})")
            
            if not scope.symbols:
                lines.append("    (no symbols)")
            else:
                for name, symbol in scope.symbols.items():
                    lines.append(
                        f"    - {name}: type={symbol.symbol_type.value}, "
                        f"defined at line {symbol.line}, col {symbol.column}"
                    )
        
        return "\n".join(lines)

    # ========================================================================
    # Error / Warning Serialization
    # ========================================================================

    @staticmethod
    def serialize_errors(errors: List[SemanticError],
                         warnings: Optional[List[str]] = None) -> str:
        """
        Format semantic errors and warnings for AI consumption.
        
        Args:
            errors: List of SemanticError objects
            warnings: Optional list of warning strings
            
        Returns:
            Formatted error/warning summary
        """
        if not errors and not warnings:
            return "DIAGNOSTICS: No errors or warnings detected. The code is semantically valid."
        
        lines = ["DIAGNOSTICS:"]
        
        if errors:
            lines.append(f"  Errors ({len(errors)}):")
            for err in errors:
                lines.append(
                    f"    - Line {err.line}, Col {err.column}: {err.message}"
                )
        
        if warnings:
            lines.append(f"  Warnings ({len(warnings)}):")
            for warn in warnings:
                lines.append(f"    - {warn}")
        
        return "\n".join(lines)

    # ========================================================================
    # Full Context Builder
    # ========================================================================

    @staticmethod
    def build_context(source_code: str,
                      ast: Program,
                      analyzer: SemanticAnalyzer) -> str:
        """
        Build the complete context string for Gemini from all pipeline outputs.
        
        This is the main entry point used by the enhanced Gemini client.
        
        Args:
            source_code: The original Mini-Python source code
            ast: The parsed AST
            analyzer: The semantic analyzer (after analysis)
            
        Returns:
            Complete context string ready for injection into Gemini prompt
        """
        sections = []
        
        # 1. Source Code
        sections.append("SOURCE CODE:")
        for i, line in enumerate(source_code.strip().splitlines(), 1):
            sections.append(f"  {i}: {line}")
        
        # 2. AST Summary
        sections.append("")
        sections.append(ContextProvider.serialize_ast(ast))
        
        # 3. Symbol Table
        sections.append("")
        sections.append(ContextProvider.serialize_symbol_table(analyzer.symbol_table))
        
        # 4. Diagnostics
        sections.append("")
        sections.append(ContextProvider.serialize_errors(
            analyzer.errors, analyzer.warnings
        ))
        
        return "\n".join(sections)

    @staticmethod
    def build_error_context(source_code: str,
                            error_type: str,
                            error_message: str,
                            line_number: Optional[int] = None,
                            column: Optional[int] = None) -> str:
        """
        Build context for lexer/parser-level errors (before semantic analysis).
        
        Args:
            source_code: The original source code
            error_type: e.g., "LexerError", "ParserError"
            error_message: The error description
            line_number: Line where the error occurred
            column: Column where the error occurred
            
        Returns:
            Context string describing the error for Gemini
        """
        sections = []
        
        # Source code with line numbers
        sections.append("SOURCE CODE:")
        for i, line in enumerate(source_code.strip().splitlines(), 1):
            marker = " >>>" if (line_number and i == line_number) else "    "
            sections.append(f"  {i}{marker}: {line}")
        
        # Error details
        sections.append("")
        sections.append("COMPILATION ERROR:")
        sections.append(f"  Type: {error_type}")
        sections.append(f"  Message: {error_message}")
        if line_number:
            sections.append(f"  Location: line {line_number}" +
                          (f", column {column}" if column else ""))
        
        # Provide the grammar rules for reference
        sections.append("")
        sections.append("NOTE: This error occurred during the front-end compilation phase "
                       "(before semantic analysis). The AST and Symbol Table are not available.")
        
        return "\n".join(sections)

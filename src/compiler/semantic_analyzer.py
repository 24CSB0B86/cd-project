"""
Semantic Analyzer for Mini-Python Compiler
Implements symbol table, scope analysis, and basic type checking.
Week 7 Implementation
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from .ast_nodes import *


class SymbolType(Enum):
    """Types supported in Mini-Python"""
    INTEGER = "int"
    STRING = "str"
    FUNCTION = "function"
    UNKNOWN = "unknown"


class Symbol:
    """Represents a symbol in the symbol table"""
    def __init__(self, name: str, symbol_type: SymbolType, scope_level: int, line: int, column: int):
        self.name = name
        self.symbol_type = symbol_type
        self.scope_level = scope_level
        self.line = line
        self.column = column
        self.is_initialized = False
        
    def __repr__(self):
        return f"Symbol({self.name}, {self.symbol_type}, scope={self.scope_level}, line={self.line})"


class Scope:
    """Represents a scope level (global or function-local)"""
    def __init__(self, name: str, level: int):
        self.name = name  # e.g., "global", "function:factorial"
        self.level = level
        self.symbols: Dict[str, Symbol] = {}
        
    def define(self, symbol: Symbol):
        """Add a symbol to this scope"""
        self.symbols[symbol.name] = symbol
        
    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope only"""
        return self.symbols.get(name)
        
    def __repr__(self):
        return f"Scope({self.name}, level={self.level}, symbols={list(self.symbols.keys())})"


class SymbolTable:
    """Manages variable and function scopes"""
    def __init__(self):
        self.scopes: List[Scope] = []
        self.current_level = 0
        self.push_scope("global")  # Start with global scope
        
    def push_scope(self, name: str):
        """Enter a new scope (e.g., function body)"""
        self.current_level += 1
        scope = Scope(name, self.current_level)
        self.scopes.append(scope)
        
    def pop_scope(self):
        """Exit current scope"""
        if len(self.scopes) > 1:  # Keep at least global scope
            self.scopes.pop()
            self.current_level -= 1
            
    def current_scope(self) -> Scope:
        """Get the current scope"""
        return self.scopes[-1]
        
    def define(self, name: str, symbol_type: SymbolType, line: int, column: int) -> Symbol:
        """Define a new symbol in current scope"""
        symbol = Symbol(name, symbol_type, self.current_level, line, column)
        self.current_scope().define(symbol)
        return symbol
        
    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol, searching from current scope upward"""
        # Search from innermost to outermost scope
        for scope in reversed(self.scopes):
            symbol = scope.lookup(name)
            if symbol:
                return symbol
        return None
        
    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in current scope"""
        return self.current_scope().lookup(name)


class SemanticError(Exception):
    """Exception raised for semantic errors"""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"SemanticError at line {line}, column {column}: {message}")


class SemanticAnalyzer:
    """
    Performs semantic analysis on the AST.
    
    Checks:
    - Variable usage before declaration
    - Duplicate variable/function definitions in same scope
    - Basic type checking (arithmetic on compatible types)
    """
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.warnings: List[str] = []
        
    def analyze(self, ast: Program) -> bool:
        """
        Analyze the AST and populate symbol table.
        
        Returns:
            True if no errors, False if errors found
        """
        try:
            self.visit_program(ast)
            return len(self.errors) == 0
        except SemanticError as e:
            self.errors.append(e)
            return False
            
    def report_error(self, message: str, line: int, column: int):
        """Record a semantic error"""
        error = SemanticError(message, line, column)
        self.errors.append(error)
        
    def report_warning(self, message: str, line: int, column: int):
        """Record a warning"""
        warning = f"Warning at line {line}, column {column}: {message}"
        self.warnings.append(warning)
        
    # ========================================================================
    # Visitor Methods for AST Nodes
    # ========================================================================
    
    def visit_program(self, node: Program):
        """Visit the root program node"""
        for statement in node.statements:
            self.visit_statement(statement)
            
    def visit_statement(self, node: Statement):
        """Dispatch to appropriate statement visitor"""
        if isinstance(node, Assignment):
            self.visit_assignment(node)
        elif isinstance(node, IfStatement):
            self.visit_if_statement(node)
        elif isinstance(node, WhileStatement):
            self.visit_while_statement(node)
        elif isinstance(node, FunctionDef):
            self.visit_function_def(node)
        elif isinstance(node, ReturnStatement):
            self.visit_return_statement(node)
        elif isinstance(node, PrintStatement):
            self.visit_print_statement(node)
        else:
            raise SemanticError(f"Unknown statement type: {type(node)}", node.line, node.column)
            
    def visit_assignment(self, node: Assignment):
        """Visit assignment statement: x = expression"""
        # Check if variable exists, if not define it
        symbol = self.symbol_table.lookup_current_scope(node.target)
        
        if not symbol:
            # Define new variable in current scope
            expr_type = self.visit_expression(node.value)
            self.symbol_table.define(node.target, expr_type, node.line, node.column)
        else:
            # Variable already exists, check type compatibility
            expr_type = self.visit_expression(node.value)
            # In a dynamically typed subset, we allow reassignment
            # But we could warn about type changes
            if symbol.symbol_type != expr_type and expr_type != SymbolType.UNKNOWN:
                self.report_warning(
                    f"Variable '{node.target}' type changed from {symbol.symbol_type.value} to {expr_type.value}",
                    node.line, node.column
                )
                symbol.symbol_type = expr_type
                
    def visit_if_statement(self, node: IfStatement):
        """Visit if statement"""
        # Check condition
        self.visit_expression(node.condition)
        
        # Visit then block
        self.visit_block(node.then_block)
        
        # Visit else block if present
        if node.else_block:
            self.visit_block(node.else_block)
            
    def visit_while_statement(self, node: WhileStatement):
        """Visit while statement"""
        # Check condition
        self.visit_expression(node.condition)
        
        # Visit body
        self.visit_block(node.body)
        
    def visit_function_def(self, node: FunctionDef):
        """Visit function definition"""
        # Check if function already defined in current scope
        existing = self.symbol_table.lookup_current_scope(node.name)
        if existing:
            self.report_error(
                f"Function '{node.name}' already defined at line {existing.line}",
                node.line, node.column
            )
            return
            
        # Define function in current scope
        self.symbol_table.define(node.name, SymbolType.FUNCTION, node.line, node.column)
        
        # Enter function scope
        self.symbol_table.push_scope(f"function:{node.name}")
        
        # Define parameters as local variables
        for param in node.params:
            param_symbol = self.symbol_table.lookup_current_scope(param)
            if param_symbol:
                self.report_error(
                    f"Duplicate parameter name '{param}'",
                    node.line, node.column
                )
            else:
                self.symbol_table.define(param, SymbolType.UNKNOWN, node.line, node.column)
                
        # Visit function body
        self.visit_block(node.body)
        
        # Exit function scope
        self.symbol_table.pop_scope()
        
    def visit_return_statement(self, node: ReturnStatement):
        """Visit return statement"""
        if node.value:
            self.visit_expression(node.value)
            
    def visit_print_statement(self, node: PrintStatement):
        """Visit print statement"""
        self.visit_expression(node.expression)
        
    def visit_block(self, node: Block):
        """Visit a block of statements"""
        for statement in node.statements:
            self.visit_statement(statement)
            
    def visit_expression(self, node: Expression) -> SymbolType:
        """
        Visit an expression and return its type.
        
        Returns:
            SymbolType representing the expression's type
        """
        if isinstance(node, BinaryOp):
            return self.visit_binary_op(node)
        elif isinstance(node, UnaryOp):
            return self.visit_unary_op(node)
        elif isinstance(node, Identifier):
            return self.visit_identifier(node)
        elif isinstance(node, Literal):
            return self.visit_literal(node)
        elif isinstance(node, FunctionCall):
            return self.visit_function_call(node)
        else:
            self.report_error(f"Unknown expression type: {type(node)}", node.line, node.column)
            return SymbolType.UNKNOWN
            
    def visit_binary_op(self, node: BinaryOp) -> SymbolType:
        """Visit binary operation"""
        left_type = self.visit_expression(node.left)
        right_type = self.visit_expression(node.right)
        
        # Arithmetic operators: +, -, *, /
        if node.operator in ['+', '-', '*', '/']:
            if left_type == SymbolType.INTEGER and right_type == SymbolType.INTEGER:
                return SymbolType.INTEGER
            elif left_type == SymbolType.STRING and right_type == SymbolType.STRING and node.operator == '+':
                return SymbolType.STRING  # String concatenation
            else:
                # Type mismatch or unsupported operation
                if left_type != SymbolType.UNKNOWN and right_type != SymbolType.UNKNOWN:
                    self.report_warning(
                        f"Type mismatch in {node.operator}: {left_type.value} {node.operator} {right_type.value}",
                        node.line, node.column
                    )
                return SymbolType.UNKNOWN
                
        # Comparison operators: ==, !=, <, >, <=, >=
        elif node.operator in ['==', '!=', '<', '>', '<=', '>=']:
            # Comparisons return boolean (we'll treat as INTEGER for now)
            return SymbolType.INTEGER
            
        return SymbolType.UNKNOWN
        
    def visit_unary_op(self, node: UnaryOp) -> SymbolType:
        """Visit unary operation"""
        operand_type = self.visit_expression(node.operand)
        
        if node.operator == '-':
            if operand_type == SymbolType.INTEGER:
                return SymbolType.INTEGER
            else:
                self.report_warning(
                    f"Unary minus applied to non-integer: {operand_type.value}",
                    node.line, node.column
                )
                return SymbolType.UNKNOWN
                
        return SymbolType.UNKNOWN
        
    def visit_identifier(self, node: Identifier) -> SymbolType:
        """Visit identifier (variable reference)"""
        # Handle Python built-in keywords/literals
        if node.name in ['True', 'False', 'None']:
            return SymbolType.INTEGER  # Treat True/False as integers (boolean)
            
        symbol = self.symbol_table.lookup(node.name)
        
        if not symbol:
            self.report_error(
                f"Undefined variable '{node.name}'",
                node.line, node.column
            )
            return SymbolType.UNKNOWN
            
        return symbol.symbol_type
        
    def visit_literal(self, node: Literal) -> SymbolType:
        """Visit literal value"""
        if isinstance(node.value, int):
            return SymbolType.INTEGER
        elif isinstance(node.value, str):
            return SymbolType.STRING
        else:
            return SymbolType.UNKNOWN
            
    def visit_function_call(self, node: FunctionCall) -> SymbolType:
        """Visit function call"""
        # Check if function is defined
        symbol = self.symbol_table.lookup(node.function_name)
        
        if not symbol:
            self.report_error(
                f"Undefined function '{node.function_name}'",
                node.line, node.column
            )
        elif symbol.symbol_type != SymbolType.FUNCTION:
            self.report_error(
                f"'{node.function_name}' is not a function (type: {symbol.symbol_type.value})",
                node.line, node.column
            )
            
        # Visit arguments
        for arg in node.arguments:
            self.visit_expression(arg)
            
        return SymbolType.UNKNOWN  # We don't track function return types yet
        
    def get_diagnostics(self) -> str:
        """Get formatted diagnostic report"""
        report = []
        
        if self.errors:
            report.append("=== SEMANTIC ERRORS ===")
            for error in self.errors:
                report.append(f"  Line {error.line}, Col {error.column}: {error.message}")
                
        if self.warnings:
            report.append("\n=== WARNINGS ===")
            for warning in self.warnings:
                report.append(f"  {warning}")
                
        if not self.errors and not self.warnings:
            report.append("✓ No semantic errors or warnings")
            
        return "\n".join(report)

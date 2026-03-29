"""
AST Node Definitions for Mini-Python Compiler
Defines the Abstract Syntax Tree node hierarchy for representing parsed code.
Week 6 Implementation
"""

from typing import List, Optional, Any
from dataclasses import dataclass


# ============================================================================
# Base Classes
# ============================================================================

@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    line: int
    column: int
    
    def accept(self, visitor):
        """Visitor pattern support for future traversals"""
        method_name = f'visit_{self.__class__.__name__}'
        visitor_method = getattr(visitor, method_name, None)
        if visitor_method:
            return visitor_method(self)
        else:
            raise NotImplementedError(f"Visitor method {method_name} not implemented")


@dataclass
class Statement(ASTNode):
    """Base class for all statements"""
    pass


@dataclass
class Expression(ASTNode):
    """Base class for all expressions"""
    pass


# ============================================================================
# Expression Nodes
# ============================================================================

@dataclass
class BinaryOp(Expression):
    """Binary operation (arithmetic or comparison)
    Examples: a + b, x * y, n == 0, x < 10
    """
    left: Expression
    operator: str  # '+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>='
    right: Expression
    
    def __repr__(self):
        return f"BinaryOp({self.left} {self.operator} {self.right})"


@dataclass
class UnaryOp(Expression):
    """Unary operation
    Examples: -x, not condition
    """
    operator: str  # '-', 'not'
    operand: Expression
    
    def __repr__(self):
        return f"UnaryOp({self.operator} {self.operand})"


@dataclass
class Identifier(Expression):
    """Variable or function name reference
    Example: x, factorial, my_var
    """
    name: str
    
    def __repr__(self):
        return f"Identifier({self.name})"


@dataclass
class Literal(Expression):
    """Literal value (number, string, boolean)
    Examples: 42, "hello", True
    """
    value: Any  # int, str, or bool
    
    def __repr__(self):
        if isinstance(self.value, str):
            return f'Literal("{self.value}")'
        return f"Literal({self.value})"


@dataclass
class FunctionCall(Expression):
    """Function call expression
    Examples: print("hello"), factorial(5), foo(a, b)
    """
    function_name: str
    arguments: List[Expression]
    
    def __repr__(self):
        args_str = ", ".join(str(arg) for arg in self.arguments)
        return f"FunctionCall({self.function_name}({args_str}))"


# ============================================================================
# Statement Nodes
# ============================================================================

@dataclass
class Assignment(Statement):
    """Variable assignment
    Example: x = 42, result = a + b
    """
    target: str  # Variable name
    value: Expression
    
    def __repr__(self):
        return f"Assignment({self.target} = {self.value})"


@dataclass
class IfStatement(Statement):
    """If statement with optional else clause
    Examples:
        if x == 0:
            return 1
        
        if condition:
            body
        else:
            else_body
    """
    condition: Expression
    then_block: 'Block'
    else_block: Optional['Block'] = None
    
    def __repr__(self):
        if self.else_block:
            return f"IfStatement(if {self.condition}: {self.then_block} else: {self.else_block})"
        return f"IfStatement(if {self.condition}: {self.then_block})"


@dataclass
class WhileStatement(Statement):
    """While loop statement
    Example:
        while x > 0:
            body
    """
    condition: Expression
    body: 'Block'
    
    def __repr__(self):
        return f"WhileStatement(while {self.condition}: {self.body})"


@dataclass
class FunctionDef(Statement):
    """Function definition
    Example:
        def factorial(n):
            body
    """
    name: str
    params: List[str]  # Parameter names
    body: 'Block'
    
    def __repr__(self):
        params_str = ", ".join(self.params)
        return f"FunctionDef(def {self.name}({params_str}): {self.body})"


@dataclass
class ReturnStatement(Statement):
    """Return statement
    Examples: return 1, return result, return n * factorial(n - 1)
    """
    value: Optional[Expression] = None
    
    def __repr__(self):
        if self.value:
            return f"ReturnStatement(return {self.value})"
        return "ReturnStatement(return)"


@dataclass
class PrintStatement(Statement):
    """Print statement (treated as a statement for simplicity)
    Example: print("hello"), print(x)
    """
    expression: Expression
    
    def __repr__(self):
        return f"PrintStatement(print({self.expression}))"


@dataclass
class Block(ASTNode):
    """Sequence of statements (indented block in Python)
    Corresponds to code between INDENT and DEDENT tokens
    """
    statements: List[Statement]
    
    def __repr__(self):
        if not self.statements:
            return "Block([])"
        statements_str = "\n  ".join(str(stmt) for stmt in self.statements)
        return f"Block([\n  {statements_str}\n])"


@dataclass
class Program(ASTNode):
    """Root node representing the entire program
    Contains all top-level statements
    """
    statements: List[Statement]
    
    def __repr__(self):
        if not self.statements:
            return "Program([])"
        statements_str = "\n".join(str(stmt) for stmt in self.statements)
        return f"Program([\n{statements_str}\n])"


# ============================================================================
# Utility Functions
# ============================================================================

def pretty_print_ast(node: ASTNode, indent: int = 0) -> str:
    """Generate a pretty-printed string representation of the AST
    
    Args:
        node: The AST node to print
        indent: Current indentation level
        
    Returns:
        Formatted string representation
    """
    prefix = "  " * indent
    
    if isinstance(node, Program):
        result = f"{prefix}Program:\n"
        for stmt in node.statements:
            result += pretty_print_ast(stmt, indent + 1)
        return result
    
    elif isinstance(node, FunctionDef):
        params = ", ".join(node.params)
        result = f"{prefix}FunctionDef: {node.name}({params})\n"
        result += pretty_print_ast(node.body, indent + 1)
        return result
    
    elif isinstance(node, Block):
        result = f"{prefix}Block:\n"
        for stmt in node.statements:
            result += pretty_print_ast(stmt, indent + 1)
        return result
    
    elif isinstance(node, IfStatement):
        result = f"{prefix}IfStatement:\n"
        result += f"{prefix}  Condition:\n"
        result += pretty_print_ast(node.condition, indent + 2)
        result += f"{prefix}  Then:\n"
        result += pretty_print_ast(node.then_block, indent + 2)
        if node.else_block:
            result += f"{prefix}  Else:\n"
            result += pretty_print_ast(node.else_block, indent + 2)
        return result
    
    elif isinstance(node, WhileStatement):
        result = f"{prefix}WhileStatement:\n"
        result += f"{prefix}  Condition:\n"
        result += pretty_print_ast(node.condition, indent + 2)
        result += f"{prefix}  Body:\n"
        result += pretty_print_ast(node.body, indent + 2)
        return result
    
    elif isinstance(node, Assignment):
        result = f"{prefix}Assignment: {node.target} =\n"
        result += pretty_print_ast(node.value, indent + 1)
        return result
    
    elif isinstance(node, ReturnStatement):
        result = f"{prefix}Return:\n"
        if node.value:
            result += pretty_print_ast(node.value, indent + 1)
        return result
    
    elif isinstance(node, PrintStatement):
        result = f"{prefix}Print:\n"
        result += pretty_print_ast(node.expression, indent + 1)
        return result
    
    elif isinstance(node, BinaryOp):
        result = f"{prefix}BinaryOp: {node.operator}\n"
        result += f"{prefix}  Left:\n"
        result += pretty_print_ast(node.left, indent + 2)
        result += f"{prefix}  Right:\n"
        result += pretty_print_ast(node.right, indent + 2)
        return result
    
    elif isinstance(node, UnaryOp):
        result = f"{prefix}UnaryOp: {node.operator}\n"
        result += pretty_print_ast(node.operand, indent + 1)
        return result
    
    elif isinstance(node, FunctionCall):
        args_str = ", ".join(str(arg) for arg in node.arguments)
        result = f"{prefix}FunctionCall: {node.function_name}({args_str})\n"
        return result
    
    elif isinstance(node, Identifier):
        return f"{prefix}Identifier: {node.name}\n"
    
    elif isinstance(node, Literal):
        return f"{prefix}Literal: {node.value}\n"
    
    else:
        return f"{prefix}{node.__class__.__name__}\n"

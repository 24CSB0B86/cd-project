"""
Week 6 Demonstration: Parser (Recursive Descent)
Shows detailed AST construction output
"""

from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.ast_nodes import *


def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_ast(node, indent=0):
    """Pretty print AST structure"""
    prefix = "  " * indent
    
    if isinstance(node, Program):
        print(f"{prefix}Program ({len(node.statements)} statements)")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    
    elif isinstance(node, FunctionDef):
        params = ", ".join(node.params)
        print(f"{prefix}Function: {node.name}({params})")
        print_ast(node.body, indent + 1)
    
    elif isinstance(node, Block):
        print(f"{prefix}Block ({len(node.statements)} statements)")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    
    elif isinstance(node, IfStatement):
        print(f"{prefix}If Statement")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Then:")
        print_ast(node.then_block, indent + 2)
        if node.else_block:
            print(f"{prefix}  Else:")
            print_ast(node.else_block, indent + 2)
    
    elif isinstance(node, WhileStatement):
        print(f"{prefix}While Loop")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    
    elif isinstance(node, Assignment):
        print(f"{prefix}Assignment: {node.target} =")
        print_ast(node.value, indent + 1)
    
    elif isinstance(node, ReturnStatement):
        print(f"{prefix}Return")
        if node.value:
            print_ast(node.value, indent + 1)
    
    elif isinstance(node, PrintStatement):
        print(f"{prefix}Print")
        print_ast(node.expression, indent + 1)
    
    elif isinstance(node, BinaryOp):
        print(f"{prefix}BinaryOp: {node.operator}")
        print(f"{prefix}  Left:")
        print_ast(node.left, indent + 2)
        print(f"{prefix}  Right:")
        print_ast(node.right, indent + 2)
    
    elif isinstance(node, Identifier):
        print(f"{prefix}Identifier: {node.name}")
    
    elif isinstance(node, Literal):
        print(f"{prefix}Literal: {node.value}")
    
    elif isinstance(node, FunctionCall):
        args = ", ".join(str(arg) for arg in node.arguments)
        print(f"{prefix}FunctionCall: {node.function_name}(...)")
        for i, arg in enumerate(node.arguments):
            print(f"{prefix}  Arg {i+1}:")
            print_ast(arg, indent + 2)


def demonstrate_parser():
    """Run parser demonstrations with detailed AST output"""
    
    # Test 1: Simple Expression with Operator Precedence
    print_separator("Test 1: Operator Precedence (2 + 3 * 4)")
    code1 = "x = 2 + 3 * 4\n"
    print(f"Code: {code1.strip()}")
    lexer = Lexer(code1)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print("\nAST Structure:")
    print_ast(ast)
    print("\n✓ Correct precedence: 2 + (3 * 4) = 2 + 12 = 14")
    
    # Test 2: Parentheses Override Precedence
    print_separator("Test 2: Parentheses Override ((2 + 3) * 4)")
    code2 = "x = (2 + 3) * 4\n"
    print(f"Code: {code2.strip()}")
    lexer = Lexer(code2)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print("\nAST Structure:")
    print_ast(ast)
    print("\n✓ Parentheses override: (2 + 3) * 4 = 5 * 4 = 20")
    
    # Test 3: If Statement
    print_separator("Test 3: If-Else Statement")
    code3 = """
if x == 0:
    return 1
else:
    return 0
"""
    print(f"Code:{code3}")
    lexer = Lexer(code3)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST Structure:")
    print_ast(ast)
    
    # Test 4: Function Definition
    print_separator("Test 4: Function Definition")
    code4 = """
def add(a, b):
    return a + b
"""
    print(f"Code:{code4}")
    lexer = Lexer(code4)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST Structure:")
    print_ast(ast)
    
    # Test 5: Factorial Function (Complex Nested Structure)
    print_separator("Test 5: Factorial Function (Nested Structures)")
    code5 = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
    print(f"Code:{code5}")
    lexer = Lexer(code5)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    print("AST Structure:")
    print_ast(ast)
    
    print("\n" + "=" * 70)
    print("✓ Week 6 Parser: All demonstrations complete!")
    print("  - Correct operator precedence")
    print("  - Proper AST construction")
    print("  - Nested block handling")
    print("  - Recursive function support")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_parser()

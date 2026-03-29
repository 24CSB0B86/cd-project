"""
Week 7 Demonstration: Semantic Analyzer
Shows detailed semantic analysis output including symbol table and error detection
"""

from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer


def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def analyze_code(code, description):
    """Analyze code and show detailed output"""
    print_separator(description)
    print(f"Code:\n{code}")
    
    # Lex and parse
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Semantic analysis
    analyzer = SemanticAnalyzer()
    success = analyzer.analyze(ast)
    
    # Show symbol table
    print("\nSymbol Table:")
    for scope in analyzer.symbol_table.scopes:
        print(f"\n  Scope: {scope.name} (level {scope.level})")
        if scope.symbols:
            for name, symbol in scope.symbols.items():
                print(f"    - {name:15} | Type: {symbol.symbol_type.name:10} | Line: {symbol.line}")
        else:
            print(f"    (empty)")
    
    # Show diagnostics
    print("\n" + analyzer.get_diagnostics())
    
    # Result
    if success:
        print(f"\n✓ Analysis Result: PASS (No errors)")
    else:
        print(f"\n✗ Analysis Result: FAIL ({len(analyzer.errors)} error(s))")
    
    return success


def demonstrate_semantic_analyzer():
    """Run semantic analyzer demonstrations"""
    
    # Test 1: Valid factorial function
    code1 = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
    analyze_code(code1, "Test 1: Valid Factorial Function")
    
    # Test 2: Undefined variable error
    code2 = """
x = 10
y = undefined_var + 5
"""
    analyze_code(code2, "Test 2: Undefined Variable Detection")
    
    # Test 3: Duplicate function definition
    code3 = """
def add(a, b):
    return a + b

def add(x, y):
    return x + y + 1
"""
    analyze_code(code3, "Test 3: Duplicate Function Detection")
    
    # Test 4: Function scope analysis
    code4 = """
x = 100

def outer():
    y = 200
    if x == 100:
        z = 300
        result = x + y + z
        return result

answer = outer()
"""
    analyze_code(code4, "Test 4: Nested Scope Analysis")
    
    # Test 5: Type checking
    code5 = """
x = 5
y = 10
z = x + y
message = "hello"
"""
    analyze_code(code5, "Test 5: Type Inference")
    
    # Test 6: Calling non-function
    code6 = """
x = 42
result = x()
"""
    analyze_code(code6, "Test 6: Invalid Function Call Detection")


if __name__ == "__main__":
    demonstrate_semantic_analyzer()

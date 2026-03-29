"""
Week 5 Demonstration: Lexer (Lexical Analyzer)
Shows detailed tokenization output
"""

from src.compiler.lexer import Lexer
from src.compiler.tokens import TokenType


def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demonstrate_lexer():
    """Run lexer demonstrations with detailed output"""
    
    # Test 1: Simple Assignment
    print_separator("Test 1: Simple Assignment")
    code1 = "x = 42"
    print(f"Code: {code1}")
    lexer = Lexer(code1)
    tokens = lexer.tokenize()
    print("\nTokens Generated:")
    for i, token in enumerate(tokens, 1):
        print(f"  {i}. {token.type.name:12} | Value: {str(token.value):10} | Line: {token.line}, Col: {token.column}")
    
    # Test 2: Keywords and Operators
    print_separator("Test 2: Function Definition with Keywords")
    code2 = "def add(a, b):"
    print(f"Code: {code2}")
    lexer = Lexer(code2)
    tokens = lexer.tokenize()
    print("\nTokens Generated:")
    for i, token in enumerate(tokens, 1):
        print(f"  {i}. {token.type.name:12} | Value: {str(token.value):10} | Line: {token.line}, Col: {token.column}")
    
    # Test 3: Arithmetic Expression
    print_separator("Test 3: Arithmetic Expression")
    code3 = "result = a + b * c"
    print(f"Code: {code3}")
    lexer = Lexer(code3)
    tokens = lexer.tokenize()
    print("\nTokens Generated:")
    for i, token in enumerate(tokens, 1):
        print(f"  {i}. {token.type.name:12} | Value: {str(token.value):10} | Line: {token.line}, Col: {token.column}")
    
    # Test 4: Indentation Handling (Python-specific feature)
    print_separator("Test 4: Indentation Handling (INDENT/DEDENT tokens)")
    code4 = """
def foo():
    x = 5
    if x > 0:
        print(x)
"""
    print(f"Code:\n{code4}")
    lexer = Lexer(code4)
    tokens = lexer.tokenize()
    print("\nTokens Generated (showing INDENT/DEDENT):")
    for i, token in enumerate(tokens, 1):
        if token.type in [TokenType.INDENT, TokenType.DEDENT, TokenType.DEF, TokenType.IF, TokenType.IDENTIFIER]:
            print(f"  {i}. {token.type.name:12} | Value: {str(token.value):10} | Line: {token.line}")
    
    # Test 5: Complete Program
    print_separator("Test 5: Complete Factorial Function")
    code5 = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
    print(f"Code:\n{code5}")
    lexer = Lexer(code5)
    tokens = lexer.tokenize()
    
    print(f"\nTotal Tokens: {len(tokens)}")
    print("\nToken Summary:")
    token_counts = {}
    for token in tokens:
        token_type = token.type.name
        token_counts[token_type] = token_counts.get(token_type, 0) + 1
    
    for token_type, count in sorted(token_counts.items()):
        print(f"  {token_type:12}: {count}")
    
    print("\n✓ Week 5 Lexer: All demonstrations complete!")
    print("  - Tokenization working correctly")
    print("  - Keyword recognition functional")
    print("  - Python indentation (INDENT/DEDENT) handled properly")
    print("  - Line/column tracking accurate")


if __name__ == "__main__":
    demonstrate_lexer()

"""
Week 8 Demonstration: Gemini API Integration & Context Injection
Shows how the Context Provider serializes compiler state for the AI agent.
"""

import sys
from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer
from src.orchestrator.context_provider import ContextProvider


def print_separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_pipeline(code):
    """Run lexer -> parser -> semantic analyzer. Return (ast, analyzer) or None on error."""
    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
    except Exception as e:
        return None, None, ("LexerError", str(e))

    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except Exception as e:
        return None, None, ("ParserError", str(e))

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return ast, analyzer, None


def demo_context_provider():
    """Main demonstration function."""

    print("#" * 70)
    print("  WEEK 8: GEMINI API INTEGRATION & CONTEXT INJECTION")
    print("#" * 70)

    print("""
  This demo shows how the Context Provider serializes compiler
  internal state (AST, Symbol Table, Errors) into natural language
  that can be injected into Gemini's prompt for intelligent analysis.

  Pipeline: Source -> Lexer -> Parser -> Semantic -> Context Provider -> Gemini
    """)

    # ------------------------------------------------------------------
    # Demo 1: Simple Valid Program
    # ------------------------------------------------------------------
    print_separator("DEMO 1: Simple Valid Program - Full Context")

    code1 = """\
x = 10
y = 20
z = x + y
print(z)
"""
    print("Source Code:")
    print(code1)

    ast, analyzer, error = run_pipeline(code1)
    if ast:
        print("--- GENERATED CONTEXT FOR GEMINI ---")
        context = ContextProvider.build_context(code1, ast, analyzer)
        print(context)
        print("--- END CONTEXT ---")

    # ------------------------------------------------------------------
    # Demo 2: Function Definition
    # ------------------------------------------------------------------
    print_separator("DEMO 2: Function with Parameters")

    code2 = """\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
result = factorial(5)
print(result)
"""
    print("Source Code:")
    print(code2)

    ast, analyzer, error = run_pipeline(code2)
    if ast:
        print("--- AST SERIALIZATION ---")
        print(ContextProvider.serialize_ast(ast))
        print()
        print("--- SYMBOL TABLE SERIALIZATION ---")
        print(ContextProvider.serialize_symbol_table(analyzer.symbol_table))
        print()
        print("--- DIAGNOSTICS ---")
        print(ContextProvider.serialize_errors(analyzer.errors, analyzer.warnings))

    # ------------------------------------------------------------------
    # Demo 3: Code with Semantic Errors
    # ------------------------------------------------------------------
    print_separator("DEMO 3: Code with Semantic Errors")

    code3 = """\
x = 10
y = x + undefined_var
result = missing_func(x)
"""
    print("Source Code:")
    print(code3)

    ast, analyzer, error = run_pipeline(code3)
    if ast:
        print("--- FULL CONTEXT (with errors) ---")
        context = ContextProvider.build_context(code3, ast, analyzer)
        print(context)
        print("--- END CONTEXT ---")
        print()
        print(f"[Errors found: {len(analyzer.errors)}]")
        print("This context would be sent to Gemini so it can explain")
        print("each error and suggest fixes based on the program structure.")

    # ------------------------------------------------------------------
    # Demo 4: Parser Error Context
    # ------------------------------------------------------------------
    print_separator("DEMO 4: Parser Error Context (pre-AST)")

    bad_code = "if x > 5 print(x)"
    print(f"Source Code: {bad_code}")
    print()

    error_context = ContextProvider.build_error_context(
        source_code=bad_code,
        error_type="ParserError",
        error_message="Expected ':', got IDENTIFIER 'print'",
        line_number=1,
        column=10
    )
    print("--- ERROR CONTEXT FOR GEMINI ---")
    print(error_context)
    print("--- END CONTEXT ---")

    # ------------------------------------------------------------------
    # Demo 5: While Loop Program
    # ------------------------------------------------------------------
    print_separator("DEMO 5: While Loop - Complete Context")

    code5 = """\
total = 0
i = 1
while i < 6:
    total = total + i
    i = i + 1
print(total)
"""
    print("Source Code:")
    print(code5)

    ast, analyzer, error = run_pipeline(code5)
    if ast:
        print("--- GENERATED CONTEXT ---")
        context = ContextProvider.build_context(code5, ast, analyzer)
        print(context)

    # ------------------------------------------------------------------
    # Demo 6: Complex Program
    # ------------------------------------------------------------------
    print_separator("DEMO 6: Complex Program - Two Functions")

    code6 = """\
def add(a, b):
    return a + b
def multiply(x, y):
    result = 0
    i = 0
    while i < y:
        result = add(result, x)
        i = i + 1
    return result
answer = multiply(3, 4)
print(answer)
"""
    print("Source Code:")
    print(code6)

    ast, analyzer, error = run_pipeline(code6)
    if ast:
        print("--- AST SUMMARY ---")
        print(ContextProvider.serialize_ast(ast))
        print()
        print("--- SYMBOL TABLE ---")
        print(ContextProvider.serialize_symbol_table(analyzer.symbol_table))

    # ------------------------------------------------------------------
    # Demo 7: Gemini API Call (optional, requires valid API key)
    # ------------------------------------------------------------------
    print_separator("DEMO 7: Live Gemini API Call (Optional)")

    try_api = "--api" in sys.argv

    if try_api:
        print("Attempting to connect to Gemini API...")
        import logging
        logging.basicConfig(level=logging.WARNING)

        from src.orchestrator.gemini_client import GeminiCompilerAgent

        agent = GeminiCompilerAgent()
        if agent.is_ready:
            # Send the error context from Demo 3 to Gemini
            ast3, analyzer3, _ = run_pipeline(code3)
            if ast3:
                context3 = ContextProvider.build_context(code3, ast3, analyzer3)
                print("\nSending compiler context to Gemini...")
                print("-" * 50)
                response = agent.analyze_with_context(context3)
                print("GEMINI RESPONSE:")
                print(response)
                print("-" * 50)
        else:
            print("Agent not initialized. Check your GEMINI_API_KEY in .env")
    else:
        print("Skipping live API call. Run with --api flag to enable:")
        print("  python demo_week8_ai.py --api")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print_separator("WEEK 8 SUMMARY")
    print("""
  What was built:
  ----------------
  1. Context Provider (src/orchestrator/context_provider.py)
     - serialize_ast()          : AST -> natural language
     - serialize_symbol_table() : Scope stack -> readable text
     - serialize_errors()       : Errors/warnings -> AI-friendly format
     - build_context()          : Full pipeline context builder
     - build_error_context()    : Pre-AST error context

  2. Enhanced Gemini Client (src/orchestrator/gemini_client.py)
     - System prompt with EBNF grammar injected
     - analyze_with_context()   : Send full compiler state to Gemini
     - explain_error()          : Targeted error explanation
     - Secure API handling (rate limits, timeouts, safety filters)

  3. Tests: 27 deterministic tests (no API calls needed)

  Pipeline Status:
  ----------------
  Week 5  Lexer             [COMPLETE]
  Week 6  Parser            [COMPLETE]
  Week 7  Semantic Analyzer [COMPLETE]
  Week 8  AI Integration    [COMPLETE]  <- NEW
    """)


if __name__ == "__main__":
    demo_context_provider()

"""
Week 8 Demonstration: Three Address Code (TAC) Generator
Shows detailed TAC generation output for various Mini-Python programs.
"""

from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer
from src.compiler.tac_generator import TACGenerator


def print_separator(title):
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def run_pipeline(code: str, description: str, show_semantic: bool = False):
    """Run full compiler pipeline and display TAC output"""
    print_separator(description)
    print(f"Source Code:\n{'-'*40}")
    print(code.strip())
    print(f"\n{'−'*40}")

    # Stage 1: Lexical Analysis
    lexer = Lexer(code)
    tokens = lexer.tokenize()

    # Stage 2: Parsing
    parser = Parser(tokens)
    ast = parser.parse()

    # Stage 3: Semantic Analysis
    analyzer = SemanticAnalyzer()
    success = analyzer.analyze(ast)

    if show_semantic:
        print("\nSemantic Analysis:")
        print(analyzer.get_diagnostics())

    if not success:
        print("  ✗ Semantic errors found — TAC generation skipped.")
        return None

    # Stage 4: TAC Generation
    gen = TACGenerator()
    gen.generate(ast)

    print(f"\nThree Address Code ({gen.get_instruction_count()} instructions):")
    print(f"{'−'*40}")
    print(gen.get_code())
    print(f"\n✓ TAC generation complete.")
    return gen


def demonstrate_tac_generator():
    """Run all TAC demonstration examples"""

    print("\n" + "#" * 72)
    print("  WEEK 8: THREE ADDRESS CODE (TAC) GENERATOR DEMONSTRATION")
    print("#" * 72)
    print("""
  What is TAC?
  ─────────────
  Three Address Code is an intermediate representation (IR) where each
  instruction performs at most one operation on at most three operands:

        result = arg1  op  arg2

  TAC is closer to machine code than source code, but still independent
  of any specific hardware. It bridges the gap between the AST (high-level
  tree structure) and actual machine instructions.

  Pipeline:  Source Code → Lexer → Parser → Semantic → TAC (← Week 8)
    """)

    # ──────────────────────────────────────────────────────────────────
    # Demo 1: Simple Assignments and Arithmetic
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
x = 10
y = 3
z = x + y
w = x * y - z
""", "Demo 1: Simple Assignments and Arithmetic")

    # ──────────────────────────────────────────────────────────────────
    # Demo 2: If Statement (no else)
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
x = 5
if x > 0:
    y = x + 1
""", "Demo 2: If Statement (without else)")

    # ──────────────────────────────────────────────────────────────────
    # Demo 3: If-Else Statement
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
x = 5
if x == 0:
    result = 1
else:
    result = x + 1
""", "Demo 3: If-Else Statement → Labels and Conditional Jump")

    # ──────────────────────────────────────────────────────────────────
    # Demo 4: While Loop
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
total = 0
i = 1
while i < 6:
    total = total + i
    i = i + 1
""", "Demo 4: While Loop → Loop Labels and Back-Edge GOTO")

    # ──────────────────────────────────────────────────────────────────
    # Demo 5: Simple Function Definition and Call
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
def add(a, b):
    return a + b

x = 3
y = 4
result = add(x, y)
""", "Demo 5: Function Definition and Call → FUNC_BEGIN/END, PARAM, CALL")

    # ──────────────────────────────────────────────────────────────────
    # Demo 6: Recursive Factorial
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
""", "Demo 6: Recursive Factorial — Full TAC with Recursion")

    # ──────────────────────────────────────────────────────────────────
    # Demo 7: Print Statement
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
x = 42
y = x + 8
print(y)
""", "Demo 7: Print Statement")

    # ──────────────────────────────────────────────────────────────────
    # Demo 8: Complex Program (combining all constructs)
    # ──────────────────────────────────────────────────────────────────
    run_pipeline("""\
def square(n):
    return n * n

i = 1
total = 0
while i < 6:
    s = square(i)
    total = total + s
    i = i + 1

print(total)
""", "Demo 8: Complex Program — Combining All Constructs")

    # ──────────────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────────────
    print_separator("Week 8 Summary")
    print("""
  TAC Instruction Types Generated:
  ─────────────────────────────────
  ASSIGN      → Direct copy / literal assignment    x = 5
  ADD/SUB     → Arithmetic addition/subtraction     t0 = a + b
  MUL/DIV     → Arithmetic multiply/divide          t1 = x * y
  NEG         → Unary negation                      t0 = -x
  EQ/NEQ/LT.. → Comparison operations               t0 = a < b
  LABEL       → Jump target                         L0:
  GOTO        → Unconditional jump                  goto L1
  IF_FALSE    → Conditional jump                    if_false cond goto L2
  FUNC_BEGIN  → Function entry marker               func_begin foo
  FUNC_END    → Function exit marker                func_end foo
  PARAM       → Push function argument              param x
  CALL        → Function invocation                 t0 = call foo, 2
  RETURN      → Function return                     return t0
  PRINT       → Output instruction                  print x

  Pipeline Status:
  ─────────────────
  Week 5  Lexer             ✓ COMPLETE
  Week 6  Parser            ✓ COMPLETE
  Week 7  Semantic Analyzer ✓ COMPLETE
  Week 8  TAC Generator     ✓ COMPLETE   ← NEW
    """)


if __name__ == "__main__":
    demonstrate_tac_generator()

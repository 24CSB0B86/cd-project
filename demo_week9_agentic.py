"""
Demo Script: Week 9 — Agentic Tool-Use (Gemini Function Calling)
=================================================================

Demonstrates the ReAct (Reason → Act → Observe) agentic loop where
the Gemini AI agent autonomously calls compiler tools to investigate
code errors before producing a final answer.

Usage:
    python demo_week9_agentic.py           # Offline simulation (no API key)
    python demo_week9_agentic.py --api     # Live Gemini API (requires .env)
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator.compiler_tools import CompilerToolbox
from src.orchestrator.tool_registry import get_tool_names, TOOL_SCHEMA_DEFINITIONS


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def header(title: str):
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def subheader(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def show_tool_result(tool_call: str, result: str):
    print(f"\n  🔧 Tool Called: {tool_call}")
    for line in result.splitlines():
        print(f"     {line}")


# ---------------------------------------------------------------------------
# Demo 1: Compiler Toolbox Basics
# ---------------------------------------------------------------------------

def demo_toolbox_basics():
    header("DEMO 1: CompilerToolbox — Direct Tool Calls")

    code = """\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
result = factorial(5)
print(result)
"""
    print("\n  Source Code:")
    for i, line in enumerate(code.strip().splitlines(), 1):
        print(f"    {i}: {line}")

    subheader("Building toolbox from source...")
    tb = CompilerToolbox.from_source(code)
    print("  ✅ Compiler pipeline completed\n")

    subheader("Tool 1: get_errors()")
    print("  " + tb.get_errors())

    subheader("Tool 2: get_symbol_table()")
    for line in tb.get_symbol_table().splitlines():
        print("  " + line)

    subheader("Tool 3: get_ast_summary()")
    for line in tb.get_ast_summary().splitlines():
        print("  " + line)

    subheader("Tool 4: check_scope('result')")
    print("  " + tb.check_scope("result"))

    subheader("Tool 5: check_function('factorial')")
    print("  " + tb.check_function("factorial"))

    subheader("Tool 6: check_scope('undefined_var')")
    print("  " + tb.check_scope("undefined_var"))


# ---------------------------------------------------------------------------
# Demo 2: Discovering Errors via Tools
# ---------------------------------------------------------------------------

def demo_error_investigation():
    header("DEMO 2: Investigating Code with Errors via Tools")

    code = """\
def compute(a, b):
    total = a + b
    return total * scale_factor
result = compute(x, 10)
print(result)
"""
    print("\n  Source Code (WITH BUGS):")
    for i, line in enumerate(code.strip().splitlines(), 1):
        print(f"    {i}: {line}")

    tb = CompilerToolbox.from_source(code)

    subheader("Step 1 → Agent calls: get_errors()")
    print("   Reasoning: Let me first check what errors exist.")
    result = tb.get_errors()
    show_tool_result("get_errors()", result)

    subheader("Step 2 → Agent calls: check_scope('scale_factor')")
    print("  Reasoning: 'scale_factor' is mentioned in an error. Is it defined?")
    result = tb.check_scope("scale_factor")
    show_tool_result("check_scope('scale_factor')", result)

    subheader("Step 3 → Agent calls: check_scope('x')")
    print("   Reasoning: 'x' is referenced. Is it in scope?")
    result = tb.check_scope("x")
    show_tool_result("check_scope('x')", result)

    subheader("Step 4 → Agent calls: check_function('compute')")
    print("   Reasoning: verify compute is defined before checking call.")
    result = tb.check_function("compute")
    show_tool_result("check_function('compute')", result)

    subheader("Step 5 → Agent calls: reparse_code(fixed_version)")
    fixed_code = """\
scale_factor = 2
x = 5
def compute(a, b):
    total = a + b
    return total * scale_factor
result = compute(x, 10)
print(result)
"""
    print("   Reasoning: I'll add the missing definitions and verify the fix.")
    result = tb.reparse_code(fixed_code)
    show_tool_result(f"reparse_code(fixed_version)", result)

    print("\n   After investigation, the agent identified 2 undefined variables")
    print("     (scale_factor, x) and verified the fix compiles successfully.")


# ---------------------------------------------------------------------------
# Demo 3: Tool Registry Overview
# ---------------------------------------------------------------------------

def demo_tool_registry():
    header("DEMO 3: Tool Registry — Available Compiler Tools")

    tools = get_tool_names()
    print(f"\n  Total tools registered: {len(tools)}\n")

    for schema in TOOL_SCHEMA_DEFINITIONS:
        print(f"   {schema['name']}")
        # First sentence of description
        desc = schema['description'].split('.')[0]
        print(f"     {desc}.")
        params = schema['parameters'].get('properties', {})
        if params:
            for param_name, param_def in params.items():
                print(f"     → Param: {param_name} ({param_def.get('type', 'any')})")
        else:
            print(f"     → No parameters")
        print()


# ---------------------------------------------------------------------------
# Demo 4: Dispatch Mechanism
# ---------------------------------------------------------------------------

def demo_dispatch():
    header("DEMO 4: Tool Dispatch Mechanism")

    print("\n  The CompilerToolbox.dispatch() method routes Gemini's function")
    print("  calls to the correct Python method automatically.\n")

    code = "x = 10\ndef add(a, b):\n    return a + b\n"
    tb = CompilerToolbox.from_source(code)

    test_calls = [
        ("check_scope", {"variable_name": "x"}),
        ("check_function", {"function_name": "add"}),
        ("get_errors", {}),
        ("get_warnings", {}),
    ]

    for tool_name, args in test_calls:
        result = tb.dispatch(tool_name, args)
        args_str = ", ".join(f"{k}='{v}'" for k, v in args.items()) if args else ""
        print(f"  dispatch('{tool_name}', {{{args_str}}})")
        # Show first line of result
        print(f"    → {result.splitlines()[0]}")
        print()


# ---------------------------------------------------------------------------
# Demo 5: Simulated Agentic Investigation (no API)
# ---------------------------------------------------------------------------

def demo_simulated_agentic():
    header("DEMO 5: Simulated Agentic ReAct Loop (No API Required)")

    print("\n  This simulates the full ReAct (Reason → Act → Observe) loop")
    print("  that the Gemini agent uses when function calling is enabled.\n")

    # Import here to avoid initialization side effects
    from src.orchestrator.gemini_client import AgenticGeminiClient

    agent = AgenticGeminiClient.__new__(AgenticGeminiClient)
    agent.model = None
    agent.chat = None
    agent._initialized = False
    agent._tools = None

    code = "total = price * quantity + missing_discount\n"

    print(f"  Code: {code.strip()}")
    print(f"  Issue: 'price', 'quantity', 'missing_discount' are all undefined\n")

    result = agent.simulate_agentic_investigation(code, "Multiple undefined variables")

    print(f"   Tool Calls Made ({len(result['tool_calls'])}):")
    for call in result['tool_calls']:
        print(f"    • {call}")

    print(f"\n   Step-by-Step Observations:\n")
    for obs in result['observations']:
        print(f"  Step {obs['step']}: {obs['action']}")
        print(f"    Reasoning: {obs['reasoning']}")
        first_line = obs['observation'].splitlines()[0]
        print(f"    Result:    {first_line}")
        print()

    print(f"   Final Answer:")
    for line in result['final_answer'].splitlines():
        print(f"    {line}")


# ---------------------------------------------------------------------------
# Demo 6: Live Gemini API (optional)
# ---------------------------------------------------------------------------

def demo_live_api():
    header("DEMO 6: Live Gemini API — Agentic Investigation")

    print("\n  Initializing AgenticGeminiClient with live Gemini API...")
    try:
        from src.orchestrator.gemini_client import AgenticGeminiClient
        from src.orchestrator.context_provider import ContextProvider
        from src.compiler.lexer import Lexer
        from src.compiler.parser import Parser
        from src.compiler.semantic_analyzer import SemanticAnalyzer

        agent = AgenticGeminiClient()
        if not agent.is_ready:
            print("  ❌ Agent not initialized. Check GEMINI_API_KEY in .env")
            return

        print("  ✅ Agent ready!\n")

        # Build compiler state
        code = """\
def greet(name):
    message = "Hello, " + name
    return message
output = greet(user_name)
print(output)
"""
        print("  Source Code:")
        for i, line in enumerate(code.strip().splitlines(), 1):
            print(f"    {i}: {line}")

        print("\n  Building compiler context...")
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        context = ContextProvider.build_context(code, ast, analyzer)

        print("  Sending to Gemini with function calling enabled...")
        print("  (Agent will call compiler tools to investigate)\n")

        from src.orchestrator.compiler_tools import CompilerToolbox
        toolbox = CompilerToolbox(code, ast, analyzer)
        response = agent.investigate_with_tools(code, context, toolbox)

        print("  .0 Gemini's Investigation Result:")
        print("  " + "─" * 58)
        for line in response.splitlines():
            print(f"  {line}")

    except Exception as e:
        print(f"  ❌ Error: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    use_api = "--api" in sys.argv

    print("\n" + "█" * 70)
    print("  Project 83: Agentic AI Compiler Assistant")
    print("  Week 9 Demo — Agentic Tool-Use (Function Calling)")
    print("█" * 70)

    demo_toolbox_basics()
    demo_error_investigation()
    demo_tool_registry()
    demo_dispatch()
    demo_simulated_agentic()

    if use_api:
        demo_live_api()
    else:
        print("\n" + "─" * 70)
        print("  ℹ️  To run the live Gemini API demo:")
        print("     python demo_week9_agentic.py --api")
        print("─" * 70)

    print("\n" + "█" * 70)
    print("  Week 9 Demo Complete!")
    print("  Next: Week 10 — Conversational Debugging Interface")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()

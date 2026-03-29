"""
Demo Script: Week 10 — Conversational Debugging Interface
==========================================================

Demonstrates the multi-turn chatbot for interactive, step-by-step
compiler error explanation: a conversational AI that lets users paste
Mini-Python code, ask follow-up questions, and iteratively fix their code.

Usage:
    python demo_week10_chat.py           # Offline simulation (no API key)
    python demo_week10_chat.py --api     # Live Gemini API (requires .env)
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator.conversation_manager import ChatSession
from src.orchestrator.chat_interface import ConversationalDebugger


# ─────────────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────────────

def header(title: str) -> None:
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def subheader(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def show_exchange(user_msg: str, assistant_msg: str) -> None:
    print(f"\n  👤 User: {user_msg}")
    print(f"\n  🤖 Assistant:")
    for line in assistant_msg.splitlines():
        print(f"     {line}")


# ─────────────────────────────────────────────────────────────────────────────
# Demo 1: ChatSession Basics
# ─────────────────────────────────────────────────────────────────────────────

def demo_session_basics() -> None:
    header("DEMO 1: ChatSession — State Management Basics")

    code = """\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
result = factorial(5)
print(result)
"""
    print("\n  Source Code (valid):")
    for i, line in enumerate(code.strip().splitlines(), 1):
        print(f"    {i}: {line}")

    subheader("Creating ChatSession from source code...")
    session = ChatSession(code)

    print(f"\n  ✅ Session compiled: {session.is_compiled}")
    print(f"  ❌ Has errors      : {session.has_errors}")
    print(f"  🔢 Error count     : {session.error_count}")

    subheader("Adding messages manually...")
    session.add_user_message("What does this code do?")
    session.add_assistant_message("This code computes factorial(5) recursively and prints the result.")
    session.add_user_message("Is it correct?")
    session.add_assistant_message("Yes! The code compiles with no semantic errors.")

    print(f"\n  Turn count    : {session.get_turn_count()}")
    print(f"  History items : {len(session.get_history())}")
    print(f"\n  Last user msg : {session.get_last_user_message()}")

    subheader("Formatted History:")
    print(session.format_history_for_display())

    subheader("Session Summary:")
    print(session.summarize_session())

    subheader("Testing clear_history()...")
    session.clear_history()
    print(f"  After clear — turn count: {session.get_turn_count()}")
    print(f"  Compiler state preserved: {session.is_compiled}")


# ─────────────────────────────────────────────────────────────────────────────
# Demo 2: Multi-Turn Conversation with Error Code
# ─────────────────────────────────────────────────────────────────────────────

def demo_multi_turn_conversation() -> None:
    header("DEMO 2: Multi-Turn Conversational Debugging (Offline Simulation)")

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

    debugger = ConversationalDebugger(use_api=False)

    subheader("Turn 0: Starting session (initial greeting)...")
    session = debugger.start_session(code)
    initial = session.get_last_assistant_message()
    print("\n  🤖 Assistant (initial):")
    for line in initial.splitlines():
        print(f"     {line}")

    subheader("Turn 1: User asks about errors...")
    resp = debugger.send_message(session, "What errors are there?")
    show_exchange("What errors are there?", resp)

    subheader("Turn 2: User asks how to fix...")
    resp = debugger.send_message(session, "How do I fix this?")
    show_exchange("How do I fix this?", resp)

    subheader("Turn 3: User asks about symbol table...")
    resp = debugger.send_message(session, "What variables are in the symbol table?")
    show_exchange("What variables are in the symbol table?", resp)

    print(f"\n  📊 Session Turns : {session.get_turn_count()}")
    print(f"  📝 History items : {len(session.get_history())}")


# ─────────────────────────────────────────────────────────────────────────────
# Demo 3: Follow-up Question Handling
# ─────────────────────────────────────────────────────────────────────────────

def demo_follow_up_questions() -> None:
    header("DEMO 3: Follow-Up Question Handling")

    code = "x = 10\ny = z + 5\nprint(y)\n"

    print(f"\n  Code: {code.strip()}")
    print("  Issue: 'z' is undefined\n")

    debugger = ConversationalDebugger(use_api=False)
    session = debugger.start_session(code)

    questions = [
        "What kind of error is this?",
        "What is the symbol table?",
        "What is the AST structure?",
        "What warnings are there?",
    ]

    for q in questions:
        subheader(f"Follow-up: \"{q}\"")
        resp = debugger.send_message(session, q)
        print(f"  🤖 Response (first 3 lines):")
        for line in resp.splitlines()[:3]:
            print(f"     {line}")

    print(f"\n  Total turns: {session.get_turn_count()}")


# ─────────────────────────────────────────────────────────────────────────────
# Demo 4: Code Refresh Mid-Session
# ─────────────────────────────────────────────────────────────────────────────

def demo_code_refresh() -> None:
    header("DEMO 4: Code Refresh Mid-Session (refresh_context)")

    buggy_code = "total = price * quantity\nprint(total)\n"
    fixed_code = "price = 5\nquantity = 3\ntotal = price * quantity\nprint(total)\n"

    print("  Buggy code:")
    for i, line in enumerate(buggy_code.strip().splitlines(), 1):
        print(f"    {i}: {line}")

    subheader("Session 1: Initial compile (with errors)...")
    session = ChatSession(buggy_code)
    print(f"  Errors found: {session.error_count}")
    for err in session.analyzer.errors:
        print(f"    • Line {err.line}: {err.message}")

    subheader("User applies fix — calling refresh_context()...")
    print("\n  Fixed code:")
    for i, line in enumerate(fixed_code.strip().splitlines(), 1):
        print(f"    {i}: {line}")
    msg = session.refresh_context(fixed_code)
    print(f"\n  ✅ Result: {msg}")
    print(f"  Errors after fix: {session.error_count}")

    subheader("Gemini-compatible history format:")
    session.add_user_message("I fixed the code, any more issues?")
    session.add_assistant_message("No more errors! The code compiles successfully now.")
    gemini_hist = session.build_gemini_history()
    print(f"  History entries: {len(gemini_hist)}")
    for entry in gemini_hist:
        print(f"    role={entry['role']} | text={entry['parts'][0]['text'][:50]}...")


# ─────────────────────────────────────────────────────────────────────────────
# Demo 5: Session Summary
# ─────────────────────────────────────────────────────────────────────────────

def demo_session_summary() -> None:
    header("DEMO 5: Session Summary & Gemini History Format")

    code = "a = 1\nb = a + 2\nc = b * good_val\nprint(c)\n"

    debugger = ConversationalDebugger(use_api=False)
    session = debugger.start_session(code)

    # Simulate a full conversation
    exchanges = [
        ("What went wrong?", None),
        ("How do I fix line 3?", None),
        ("What variables are defined?", None),
        ("Is 'a' in scope?", None),
    ]
    for user_q, _ in exchanges:
        debugger.send_message(session, user_q)

    subheader("Final Session Summary:")
    print(f"\n{session.summarize_session()}")

    subheader("Gemini Chat History Format (first 2 entries):")
    gemini_hist = session.build_gemini_history()
    print(f"  Total history entries: {len(gemini_hist)}")
    for entry in gemini_hist[:4]:
        print(f"    [{entry['role']}] {entry['parts'][0]['text'][:60].strip()}...")


# ─────────────────────────────────────────────────────────────────────────────
# Demo 6: Live Gemini API (optional)
# ─────────────────────────────────────────────────────────────────────────────

def demo_live_api() -> None:
    header("DEMO 6: Live Gemini API — Conversational Debugging")

    print("\n  Initialising ConversationalDebugger with live Gemini API...")
    try:
        debugger = ConversationalDebugger(use_api=True)
        if not debugger.is_online:
            print("  ❌ Agent not initialised. Check GEMINI_API_KEY in .env")
            return

        print("  ✅ Agent ready!\n")

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

        print("\n  Starting session (Gemini will analyse with full ReAct loop)...")
        session = debugger.start_session(code)

        initial = session.get_last_assistant_message()
        print("\n  🤖 Initial Analysis:")
        print("  " + "─" * 58)
        for line in initial.splitlines():
            print(f"  {line}")

        # Follow-up question
        print("\n  Sending follow-up: 'How do I fix this?'")
        resp = debugger.send_message(session, "How do I fix the undefined variable error?")
        print("\n  🤖 Follow-up Response:")
        print("  " + "─" * 58)
        for line in resp.splitlines():
            print(f"  {line}")

        print(f"\n  Conversation turns: {session.get_turn_count()}")

    except Exception as e:
        print(f"  ❌ Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    use_api = "--api" in sys.argv
    use_interactive = "--interactive" in sys.argv or "-i" in sys.argv

    print("\n" + "█" * 70)
    print("  Project 83: Agentic AI Compiler Assistant")
    print("  Week 10 Demo — Conversational Debugging Interface")
    print("█" * 70)

    if use_interactive:
        # Full interactive CLI mode
        debugger = ConversationalDebugger(use_api=use_api)
        debugger.run_cli()
        return

    demo_session_basics()
    demo_multi_turn_conversation()
    demo_follow_up_questions()
    demo_code_refresh()
    demo_session_summary()

    if use_api:
        demo_live_api()
    else:
        print("\n" + "─" * 70)
        print("  ℹ️  To run the live Gemini API demo:")
        print("     python demo_week10_chat.py --api")
        print("  ℹ️  To run interactive CLI chatbot:")
        print("     python demo_week10_chat.py --interactive")
        print("─" * 70)

    print("\n" + "█" * 70)
    print("  Week 10 Demo Complete!")
    print("  Project 83: Conversational Debugging Interface — DONE")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()

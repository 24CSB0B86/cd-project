"""
Chat Interface for Conversational Debugging
Provides the ConversationalDebugger (AI orchestration) and CLI loop.
Week 10 Implementation - Conversational Debugging Interface
"""

import os
import sys
import logging
from typing import Optional

from .conversation_manager import ChatSession

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CLI display helpers
# ─────────────────────────────────────────────────────────────────────────────

def _banner(title: str, width: int = 68) -> str:
    return f"\n{'═' * width}\n  {title}\n{'═' * width}"


def _divider(width: int = 68) -> str:
    return "─" * width


def _print_response(text: str) -> None:
    print(f"\n  🤖 Assistant:\n  {'─' * 60}")
    for line in text.splitlines():
        print(f"  {line}")
    print(f"  {'─' * 60}\n")


# ─────────────────────────────────────────────────────────────────────────────
# ConversationalDebugger
# ─────────────────────────────────────────────────────────────────────────────

class ConversationalDebugger:
    """
    Orchestrates a multi-turn Conversational Debugging session.

    Wraps ChatSession (state management) and AgenticGeminiClient (AI layer).
    Supports both live Gemini API mode and offline simulation mode.

    Week 10 Implementation.
    """

    # System suffix injected on the first turn to set conversational tone
    INITIAL_SUFFIX = (
        "\n\nPlease greet the user, briefly describe the compilation result, "
        "and invite follow-up questions. Keep the tone conversational and friendly."
    )

    def __init__(self, use_api: bool = False):
        """
        Initialize the ConversationalDebugger.

        Args:
            use_api: If True, initialise AgenticGeminiClient for live API calls.
                     If False, run in offline simulation mode.
        """
        self.use_api = use_api
        self._agent = None

        if use_api:
            try:
                from .gemini_client import AgenticGeminiClient
                self._agent = AgenticGeminiClient()
                if not self._agent.is_ready:
                    logger.warning(
                        "AgenticGeminiClient not ready — falling back to offline mode."
                    )
                    self._agent = None
                    self.use_api = False
            except Exception as e:
                logger.error(f"Could not initialise AgenticGeminiClient: {e}")
                self.use_api = False

    @property
    def is_online(self) -> bool:
        """True if the Gemini API agent is initialised and ready."""
        return self.use_api and self._agent is not None and self._agent.is_ready

    # ─────────────────────────────────────────────────────────────────────────
    # Session management
    # ─────────────────────────────────────────────────────────────────────────

    def start_session(self, source_code: str) -> ChatSession:
        """
        Create and initialise a ChatSession for the given source code.

        Runs the compiler pipeline, builds context, and adds an initial
        assistant greeting (simulated or via live API).

        Args:
            source_code: Mini-Python source code to analyse.

        Returns:
            An initialised ChatSession ready for conversation.
        """
        session = ChatSession(source_code)
        initial_prompt = self._build_initial_prompt(session)

        # Get initial assistant message
        initial_response = self._respond(session, initial_prompt, is_initial=True)
        session.add_user_message(initial_prompt)
        session.add_assistant_message(initial_response)

        return session

    # ─────────────────────────────────────────────────────────────────────────
    # Messaging
    # ─────────────────────────────────────────────────────────────────────────

    def send_message(self, session: ChatSession, user_input: str) -> str:
        """
        Process a user's follow-up message and return the assistant's reply.

        Updates the session history with both the user message and the reply.

        Args:
            session:    The active ChatSession.
            user_input: The user's question or command text.

        Returns:
            The assistant's response string.
        """
        session.add_user_message(user_input)
        response = self._respond(session, user_input, is_initial=False)
        session.add_assistant_message(response)
        return response

    def _respond(self, session: ChatSession, prompt: str,
                 is_initial: bool = False) -> str:
        """Route the prompt to the live API or the offline simulator."""
        if self.is_online:
            return self._live_respond(session, prompt, is_initial)
        return self.simulate_response(session, prompt, is_initial)

    def _live_respond(self, session: ChatSession, prompt: str,
                      is_initial: bool = False) -> str:
        """
        Send a message to the live Gemini API within the conversation context.

        On the first turn, uses investigate_with_tools() for the full ReAct loop.
        On follow-up turns, uses a context-aware prompt with chat history.

        Args:
            session:    The current ChatSession.
            prompt:     The message/question to send.
            is_initial: True for the first turn (triggers full investigation).

        Returns:
            The Gemini API response text.
        """
        try:
            if is_initial:
                # Full agentic investigation on first turn
                return self._agent.investigate_with_tools(
                    session.source_code,
                    session.context_string,
                    session.toolbox,
                )
            else:
                # Follow-up turns: inject history for continuity
                history_text = session.format_history_for_display()
                follow_up_prompt = (
                    f"The user has a follow-up question.\n\n"
                    f"CONVERSATION SO FAR:\n{history_text}\n\n"
                    f"COMPILER CONTEXT (current state):\n{session.context_string}\n\n"
                    f"USER'S NEW QUESTION: {prompt}\n\n"
                    f"Please answer helpfully, referencing the code and compiler state."
                )
                return self._agent._safe_send(follow_up_prompt)
        except Exception as e:
            logger.error(f"Live API call failed: {e}")
            return f"[API Error] {e} — falling back to offline mode."

    def simulate_response(self, session: ChatSession, prompt: str,
                          is_initial: bool = False) -> str:
        """
        Generate a deterministic simulated response WITHOUT calling the API.

        Useful for testing and offline demos.  Analyses the compiler state and
        the user's prompt keywords to produce a relevant, human-readable reply.

        Args:
            session:    The current ChatSession (compiler state used).
            prompt:     The user message / question text.
            is_initial: True for the greeting/initial analysis turn.

        Returns:
            A simulated assistant response string.
        """
        if is_initial:
            return self._simulate_initial(session)
        return self._simulate_followup(session, prompt)

    def _simulate_initial(self, session: ChatSession) -> str:
        """Simulated greeting and initial analysis response."""
        if not session.is_compiled:
            return (
                "👋 Hello! I'm your AI Compiler Assistant.\n"
                "It looks like no code has been loaded yet. "
                "Use /code <your code> to paste some Mini-Python code and I'll analyse it!"
            )

        error_count = session.error_count
        lines = [
            "👋 Hello! I'm your AI Compiler Assistant for **Project 83**.",
            "",
            f"I've analysed your Mini-Python code ({len(session.source_code.splitlines())} line(s)).",
        ]

        if error_count == 0:
            lines += [
                "✅ **Great news** — your code compiled successfully with no errors!",
                "",
                "I can help you with:",
                "  • Understanding what your code does",
                "  • Reviewing the symbol table or AST structure",
                "  • Suggesting improvements",
                "",
                "What would you like to know?",
            ]
        else:
            errors = session.analyzer.errors
            lines += [
                f"❌ Found **{error_count} semantic error(s)**. Here's a quick summary:",
                "",
            ]
            for i, err in enumerate(errors[:5], 1):
                lines.append(f"  [{i}] Line {err.line}: {err.message}")
            if error_count > 5:
                lines.append(f"  ... and {error_count - 5} more.")
            lines += [
                "",
                "Ask me about any error and I'll explain it and suggest a fix!",
                "Or type `/errors` to see the full error list.",
            ]

        return "\n".join(lines)

    def _simulate_followup(self, session: ChatSession, prompt: str) -> str:
        """Simulated follow-up response based on keyword matching."""
        p = prompt.lower()

        # Error queries
        if any(kw in p for kw in ["error", "wrong", "problem", "issue", "bug"]):
            if session.has_errors:
                errors = session.analyzer.errors
                lines = [f"Here are the {len(errors)} semantic error(s) found:\n"]
                for i, err in enumerate(errors, 1):
                    lines.append(f"  [{i}] **Line {err.line}, Col {err.column}**: {err.message}")
                lines += ["", "Each error is a place where the compiler couldn't verify your code's correctness."]
                return "\n".join(lines)
            return "✅ Good news! There are currently **no errors** in your code."

        # Symbol / variable queries
        if any(kw in p for kw in ["variable", "symbol", "scope", "defined", "declared"]):
            if session.toolbox:
                table = session.toolbox.get_symbol_table()
                return f"Here's the full symbol table for the current code:\n\n{table}"
            return "No compiler state available. Please load some code first."

        # AST / structure queries
        if any(kw in p for kw in ["ast", "structure", "tree", "function", "statement"]):
            if session.toolbox:
                ast_summary = session.toolbox.get_ast_summary()
                return f"Here's the program structure (AST summary):\n\n{ast_summary}"
            return "No AST available. Please load some code first."

        # Fix / how to fix
        if any(kw in p for kw in ["fix", "how", "correct", "solve", "repair"]):
            if session.has_errors:
                err = session.analyzer.errors[0]
                return (
                    f"To fix **Line {err.line}**: `{err.message}`\n\n"
                    f"1. Look at the variable or function name mentioned in the error.\n"
                    f"2. Make sure it is **defined before it is used**.\n"
                    f"3. Use `/code <fixed_code>` to reload and re-analyse the fixed version.\n\n"
                    f"Would you like me to suggest a specific fix for this error?"
                )
            return "Your code looks correct! No fixes needed right now."

        # History
        if any(kw in p for kw in ["history", "conversation", "what did", "previous"]):
            history = session.format_history_for_display()
            return f"Here's our conversation so far:\n\n{history}"

        # Warnings
        if "warning" in p:
            if session.toolbox:
                return session.toolbox.get_warnings()
            return "No compiler state available."

        # Default fallback
        turn = session.get_turn_count()
        return (
            f"Thanks for your question (turn {turn})! "
            f"I'm analysing your code. Here's the current status:\n\n"
            f"  • Errors   : {session.error_count}\n"
            f"  • Warnings : {len(session.analyzer.warnings) if session.analyzer else 0}\n"
            f"  • Lines    : {len(session.source_code.splitlines())}\n\n"
            f"Could you be more specific? For example:\n"
            f"  • Ask about a specific error line\n"
            f"  • Ask 'how do I fix this?'\n"
            f"  • Ask 'what does the symbol table look like?'"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # CLI Loop
    # ─────────────────────────────────────────────────────────────────────────

    def run_cli(self) -> None:
        """
        Run the interactive multi-turn CLI debugging chatbot.

        Commands:
            /code <snippet>  — Load new code (single-line) and refresh
            /errors          — Show current error list
            /symbols         — Show symbol table
            /history         — Show full conversation history
            /summary         — Show session summary
            /clear           — Clear conversation history
            /help            — Show command list
            /quit            — Exit the chatbot

        Multi-line code: type /code then paste, end with a blank line.
        """
        print(_banner("Project 83: Conversational AI Compiler Debugger — Week 10"))
        mode = "🌐 LIVE API" if self.is_online else "💻 OFFLINE SIMULATION"
        print(f"  Mode: {mode}")
        print(f"  Type /help for commands. Type /quit to exit.\n")

        # Get initial code from the user
        print("  Paste your Mini-Python code below. End with a blank line:\n")
        code_lines = []
        while True:
            try:
                line = input("  > ")
            except (EOFError, KeyboardInterrupt):
                print("\n  Goodbye! 👋")
                return
            if line == "" and code_lines:
                break
            code_lines.append(line)

        if not code_lines:
            print("  No code entered. Goodbye!")
            return

        source_code = "\n".join(code_lines)
        print(f"\n  Compiling and starting session...")
        session = self.start_session(source_code)

        # Show initial assistant message
        initial_msg = session.get_last_assistant_message()
        if initial_msg:
            _print_response(initial_msg)

        # ── Main conversation loop ──────────────────────────────────────────
        while True:
            try:
                user_input = input("  You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            # ── Built-in CLI commands ───────────────────────────────────────
            if user_input.startswith("/"):
                parts = user_input.split(None, 1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "/quit":
                    print(session.summarize_session())
                    print("\n  Goodbye! 👋\n")
                    break

                elif cmd == "/help":
                    print("\n  Available commands:")
                    print("    /code <snippet>  — Load new single-line code snippet")
                    print("    /errors          — Show current errors")
                    print("    /symbols         — Show symbol table")
                    print("    /history         — Show conversation history")
                    print("    /summary         — Show session summary")
                    print("    /clear           — Clear conversation history")
                    print("    /quit            — Exit\n")

                elif cmd == "/errors":
                    if session.toolbox:
                        print(f"\n  {session.toolbox.get_errors()}\n")
                    else:
                        print("  No compiler state loaded.\n")

                elif cmd == "/symbols":
                    if session.toolbox:
                        for ln in session.toolbox.get_symbol_table().splitlines():
                            print(f"  {ln}")
                        print()
                    else:
                        print("  No compiler state loaded.\n")

                elif cmd == "/history":
                    print(f"\n{session.format_history_for_display()}")

                elif cmd == "/summary":
                    print(f"\n{session.summarize_session()}\n")

                elif cmd == "/clear":
                    session.clear_history()
                    print("  ✅ Conversation history cleared.\n")

                elif cmd == "/code":
                    if arg:
                        msg = session.refresh_context(arg)
                        print(f"\n  {msg}\n")
                    else:
                        print("  Usage: /code <your mini-python code>\n")

                else:
                    print(f"  Unknown command: {cmd}. Type /help for options.\n")

            else:
                # Regular question — send to AI
                response = self.send_message(session, user_input)
                _print_response(response)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _build_initial_prompt(self, session: ChatSession) -> str:
        """Build the first-turn prompt from compiler context."""
        if not session.is_compiled:
            return "I have no code to analyse yet."

        error_part = ""
        if session.has_errors:
            errors_text = "\n".join(
                f"  Line {e.line}: {e.message}"
                for e in session.analyzer.errors
            )
            error_part = f"\n\nSemantic errors found:\n{errors_text}"

        return (
            f"Please analyse the following Mini-Python code.\n\n"
            f"COMPILER CONTEXT:\n{session.context_string}"
            f"{error_part}"
            f"{self.INITIAL_SUFFIX}"
        )

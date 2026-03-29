"""
Test Suite: Week 10 — Conversational Debugging Interface
=========================================================
25 deterministic tests — zero Gemini API calls required.

Test classes:
  TestChatSession           (8)  — State management, history, refresh
  TestConversationalDebugger(7)  — start_session, send_message, simulate
  TestSessionSummary        (4)  — summarize_session, history format
  TestChatIntegration       (6)  — Full offline conversation flows

Run: python -m pytest tests/test_week10_chat.py -v
"""

import sys
import os
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator.conversation_manager import ChatSession, ChatMessage
from src.orchestrator.chat_interface import ConversationalDebugger


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: sample code snippets
# ─────────────────────────────────────────────────────────────────────────────

VALID_CODE = """\
def add(a, b):
    return a + b
result = add(3, 4)
print(result)
"""

ERROR_CODE = """\
def compute(a, b):
    total = a + b
    return total * scale_factor
result = compute(x, 10)
print(result)
"""

SINGLE_ERROR_CODE = "x = 10\ny = z + 5\nprint(y)\n"


# ─────────────────────────────────────────────────────────────────────────────
# TestChatSession
# ─────────────────────────────────────────────────────────────────────────────

class TestChatSession:
    """Tests for ChatSession state management (no API)."""

    def test_session_compiles_valid_code(self):
        """ChatSession with valid code should compile without errors."""
        session = ChatSession(VALID_CODE)
        assert session.is_compiled is True
        assert session.has_errors is False
        assert session.error_count == 0

    def test_session_detects_errors(self):
        """ChatSession with buggy code should detect semantic errors."""
        session = ChatSession(ERROR_CODE)
        assert session.is_compiled is True
        assert session.has_errors is True
        assert session.error_count >= 1

    def test_session_empty_code(self):
        """ChatSession with empty code should not crash."""
        session = ChatSession("")
        assert session.is_compiled is False
        assert session.has_errors is False

    def test_add_user_message(self):
        """add_user_message appends a user turn to history."""
        session = ChatSession(VALID_CODE)
        session.add_user_message("Hello, what does this code do?")
        history = session.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert "Hello" in history[0]["content"]

    def test_add_assistant_message(self):
        """add_assistant_message appends an assistant turn to history."""
        session = ChatSession(VALID_CODE)
        session.add_assistant_message("Your code is correct!")
        history = session.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert "correct" in history[0]["content"]

    def test_turn_count_increments_on_user_messages(self):
        """get_turn_count should count only user messages."""
        session = ChatSession(VALID_CODE)
        assert session.get_turn_count() == 0
        session.add_user_message("Q1")
        assert session.get_turn_count() == 1
        session.add_assistant_message("A1")
        assert session.get_turn_count() == 1   # assistant doesn't add to turn count
        session.add_user_message("Q2")
        assert session.get_turn_count() == 2

    def test_clear_history_preserves_compiler_state(self):
        """clear_history resets messages but keeps compiler state."""
        session = ChatSession(VALID_CODE)
        session.add_user_message("Q1")
        session.add_assistant_message("A1")
        session.clear_history()
        assert session.get_turn_count() == 0
        assert len(session.get_history()) == 0
        assert session.is_compiled is True     # compiler state preserved

    def test_refresh_context_fixes_errors(self):
        """refresh_context with valid code should clear errors."""
        session = ChatSession(SINGLE_ERROR_CODE)
        assert session.has_errors is True
        fixed = "x = 10\nz = 3\ny = z + 5\nprint(y)\n"
        result = session.refresh_context(fixed)
        assert session.has_errors is False
        assert "✅" in result or "success" in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# TestConversationalDebugger
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationalDebugger:
    """Tests for ConversationalDebugger (offline simulation mode)."""

    def test_debugger_initializes_offline(self):
        """ConversationalDebugger in offline mode should not need API."""
        debugger = ConversationalDebugger(use_api=False)
        assert debugger.is_online is False

    def test_start_session_returns_chat_session(self):
        """start_session should return a compiled ChatSession."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        assert isinstance(session, ChatSession)
        assert session.is_compiled is True

    def test_start_session_adds_initial_assistant_message(self):
        """start_session should populate history with an initial assistant message."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        history = session.get_history()
        # Should have user prompt + assistant greeting
        roles = [m["role"] for m in history]
        assert "assistant" in roles
        last_asst = session.get_last_assistant_message()
        assert last_asst is not None
        assert len(last_asst) > 0

    def test_send_message_appends_to_history(self):
        """send_message should add user + assistant messages to history."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        initial_count = len(session.get_history())
        debugger.send_message(session, "Is the code correct?")
        assert len(session.get_history()) == initial_count + 2  # +user +assistant

    def test_simulate_response_error_query(self):
        """simulate_response with error keyword should mention errors."""
        debugger = ConversationalDebugger(use_api=False)
        session = ChatSession(ERROR_CODE)
        resp = debugger.simulate_response(session, "What errors are there?")
        assert "error" in resp.lower() or "line" in resp.lower()

    def test_simulate_response_symbol_query(self):
        """simulate_response with 'symbol' keyword should return symbol table."""
        debugger = ConversationalDebugger(use_api=False)
        session = ChatSession(VALID_CODE)
        resp = debugger.simulate_response(session, "Show me the symbol table")
        assert "SYMBOL TABLE" in resp or "symbol" in resp.lower()

    def test_simulate_response_initial_greeting(self):
        """simulate_response for initial turn should include a greeting."""
        debugger = ConversationalDebugger(use_api=False)
        session = ChatSession(VALID_CODE)
        resp = debugger.simulate_response(session, "Hello", is_initial=True)
        # Greeting should mention assistant identity
        assert "assistant" in resp.lower() or "hello" in resp.lower() or "hi" in resp.lower() or "👋" in resp


# ─────────────────────────────────────────────────────────────────────────────
# TestSessionSummary
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionSummary:
    """Tests for summarize_session and format_history_for_display."""

    def test_summary_contains_turn_count(self):
        """summarize_session should report correct turn count."""
        session = ChatSession(VALID_CODE)
        session.add_user_message("Q1")
        session.add_assistant_message("A1")
        summary = session.summarize_session()
        assert "1" in summary  # 1 turn

    def test_summary_reflects_error_state(self):
        """summarize_session should reflect remaining errors."""
        session = ChatSession(ERROR_CODE)
        summary = session.summarize_session()
        assert "error" in summary.lower()

    def test_format_history_empty(self):
        """format_history_for_display on empty session returns fallback."""
        session = ChatSession(VALID_CODE)
        formatted = session.format_history_for_display()
        assert "No messages" in formatted or len(formatted) > 0

    def test_build_gemini_history_role_mapping(self):
        """build_gemini_history should map 'assistant' → 'model' for Gemini."""
        session = ChatSession(VALID_CODE)
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")
        gemini_hist = session.build_gemini_history()
        roles = [entry["role"] for entry in gemini_hist]
        assert "user" in roles
        assert "model" in roles
        assert "assistant" not in roles


# ─────────────────────────────────────────────────────────────────────────────
# TestChatIntegration
# ─────────────────────────────────────────────────────────────────────────────

class TestChatIntegration:
    """Full offline conversation flow integration tests."""

    def test_full_conversation_valid_code(self):
        """Full offline session with valid code should show no errors."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        assert session.error_count == 0
        resp = debugger.send_message(session, "Is my code correct?")
        assert resp is not None
        assert len(resp) > 0

    def test_full_conversation_with_errors(self):
        """Full offline session with errors should surface them."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(ERROR_CODE)
        assert session.error_count >= 1
        resp = debugger.send_message(session, "What errors do I have?")
        # Response should mention error or line
        assert "error" in resp.lower() or "line" in resp.lower()

    def test_multi_turn_history_grows(self):
        """Sending multiple messages should grow history correctly."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        initial_count = len(session.get_history())
        for i in range(3):
            debugger.send_message(session, f"Question {i}")
        assert len(session.get_history()) == initial_count + 6  # 3 user + 3 assistant

    def test_code_refresh_mid_conversation(self):
        """refresh_context mid-conversation should update error state."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(SINGLE_ERROR_CODE)
        assert session.has_errors is True

        debugger.send_message(session, "What's wrong?")

        fixed = "x = 10\nz = 3\ny = z + 5\nprint(y)\n"
        session.refresh_context(fixed)
        assert session.has_errors is False

        resp = debugger.send_message(session, "Any more errors?")
        assert resp is not None

    def test_session_turn_count_accurate(self):
        """Turn count should reflect only user messages sent."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        # start_session adds 1 user + 1 assistant
        initial_turns = session.get_turn_count()
        debugger.send_message(session, "Q1")
        debugger.send_message(session, "Q2")
        assert session.get_turn_count() == initial_turns + 2

    def test_ast_query_returns_structure(self):
        """Asking about AST should return program structure info."""
        debugger = ConversationalDebugger(use_api=False)
        session = debugger.start_session(VALID_CODE)
        resp = debugger.send_message(session, "What is the AST structure?")
        assert "PROGRAM STRUCTURE" in resp or "function" in resp.lower() or "statement" in resp.lower()

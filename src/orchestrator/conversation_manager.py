"""
Conversation Manager for Conversational Debugging Interface
Manages multi-turn chat history and compiler state for a debugging session.
Week 10 Implementation - Conversational Debugging Interface
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single message in a conversation turn."""
    role: str          # "user" or "assistant"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """Convert to a plain dict (compatible with Gemini history format)."""
        return {"role": self.role, "content": self.content}


class ChatSession:
    """
    Manages a single multi-turn debugging conversation for one code snippet.

    Responsibilities:
    - Maintain ordered message history (user + assistant turns)
    - Hold compiled compiler state (AST, analyzer, toolbox, context string)
    - Allow mid-session code refresh (re-run full pipeline on new code)
    - Provide formatted output for display and logging

    Design: deliberately free of Gemini API calls so it is fully testable.
    The AI layer (ConversationalDebugger) calls this for state management.
    """

    def __init__(self, source_code: str = ""):
        """
        Initialize a chat session and optionally compile the source code.

        Args:
            source_code: The initial Mini-Python source code to analyze.
                         If empty, session starts with no compiler state.
        """
        self.source_code: str = source_code
        self._history: List[ChatMessage] = []

        # Compiler state (populated by _compile)
        self.ast = None
        self.analyzer = None
        self.toolbox = None
        self.context_string: str = ""
        self._compiled: bool = False

        if source_code.strip():
            self._compile(source_code)

    # =========================================================================
    # Compilation / Context
    # =========================================================================

    def _compile(self, source_code: str) -> bool:
        """
        Run the full compiler pipeline and update internal state.

        Args:
            source_code: Mini-Python source to compile.

        Returns:
            True if semantic analysis succeeded (no errors), False otherwise.
        """
        try:
            from ..compiler.lexer import Lexer
            from ..compiler.parser import Parser
            from ..compiler.semantic_analyzer import SemanticAnalyzer
            from .compiler_tools import CompilerToolbox
            from .context_provider import ContextProvider

            lexer = Lexer(source_code)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            ast = parser.parse()

            analyzer = SemanticAnalyzer()
            success = analyzer.analyze(ast)

            self.source_code = source_code
            self.ast = ast
            self.analyzer = analyzer
            self.toolbox = CompilerToolbox(source_code, ast, analyzer)
            self.context_string = ContextProvider.build_context(source_code, ast, analyzer)
            self._compiled = True

            logger.info(
                f"ChatSession compiled: success={success}, "
                f"errors={len(analyzer.errors)}, warnings={len(analyzer.warnings)}"
            )
            return success

        except Exception as e:
            logger.error(f"ChatSession._compile failed: {e}")
            self._compiled = False
            return False

    def refresh_context(self, new_code: str) -> str:
        """
        Re-compile the session with new source code (e.g. after a fix).

        Args:
            new_code: Revised Mini-Python source code.

        Returns:
            A human-readable summary of the compilation result.
        """
        success = self._compile(new_code)
        error_count = len(self.analyzer.errors) if self.analyzer else 0
        warning_count = len(self.analyzer.warnings) if self.analyzer else 0

        if success:
            return (
                f"✅ Code refreshed — compiled successfully. "
                f"({warning_count} warning(s))"
            )
        else:
            return (
                f"❌ Code refreshed — {error_count} error(s) found. "
                f"Use /errors to see them."
            )

    @property
    def is_compiled(self) -> bool:
        """True if the session has a valid compiled compiler state."""
        return self._compiled

    @property
    def error_count(self) -> int:
        """Number of semantic errors in the current compiler state."""
        if self.analyzer:
            return len(self.analyzer.errors)
        return 0

    @property
    def has_errors(self) -> bool:
        """True if the current compiler state has semantic errors."""
        return self.error_count > 0

    # =========================================================================
    # History Management
    # =========================================================================

    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Append a user message to the conversation history.

        Args:
            content:  The user's message text.
            metadata: Optional extra data (e.g., {"command": "/code"}).
        """
        self._history.append(
            ChatMessage(role="user", content=content, metadata=metadata or {})
        )

    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Append an assistant (AI) message to the conversation history.

        Args:
            content:  The assistant's response text.
            metadata: Optional extra data (e.g., {"tool_calls": [...]}).
        """
        self._history.append(
            ChatMessage(role="assistant", content=content, metadata=metadata or {})
        )

    def get_history(self) -> List[Dict[str, str]]:
        """
        Return the conversation history as a list of plain dicts.

        Returns:
            List of {"role": ..., "content": ...} dicts — compatible with
            the Gemini chat history format.
        """
        return [msg.to_dict() for msg in self._history]

    def get_turn_count(self) -> int:
        """
        Return the number of complete turns (user + assistant pairs).

        A 'turn' is counted as each user message (questions asked so far).
        """
        return sum(1 for msg in self._history if msg.role == "user")

    def clear_history(self) -> None:
        """
        Clear all conversation messages.
        Compiler state (AST, analyzer, toolbox) is preserved.
        """
        self._history.clear()
        logger.info("ChatSession: history cleared.")

    def get_last_assistant_message(self) -> Optional[str]:
        """
        Return the content of the most recent assistant message, or None.
        """
        for msg in reversed(self._history):
            if msg.role == "assistant":
                return msg.content
        return None

    def get_last_user_message(self) -> Optional[str]:
        """
        Return the content of the most recent user message, or None.
        """
        for msg in reversed(self._history):
            if msg.role == "user":
                return msg.content
        return None

    # =========================================================================
    # Display / Formatting
    # =========================================================================

    def format_history_for_display(self) -> str:
        """
        Return a human-readable, formatted conversation history string.
        """
        if not self._history:
            return "(No messages yet)"

        lines = []
        for i, msg in enumerate(self._history, 1):
            role_label = "👤 You" if msg.role == "user" else "🤖 Assistant"
            lines.append(f"[{i}] {role_label}:")
            for line in msg.content.splitlines():
                lines.append(f"    {line}")
            lines.append("")
        return "\n".join(lines)

    def summarize_session(self) -> str:
        """
        Return a concise summary of this debugging session.
        """
        turns = self.get_turn_count()
        error_status = (
            f"{self.error_count} error(s) remaining"
            if self.has_errors
            else "no errors"
        )
        lines = [
            "─── Session Summary ───────────────────────────────────────",
            f"  Turns completed  : {turns}",
            f"  Compiler status  : {error_status}",
            f"  Source lines     : {len(self.source_code.splitlines())}",
            f"  History messages : {len(self._history)}",
            "────────────────────────────────────────────────────────────",
        ]
        return "\n".join(lines)

    def build_gemini_history(self) -> List[Dict[str, Any]]:
        """
        Build a Gemini-compatible chat history list for multi-turn context.

        Maps "user" → "user" and "assistant" → "model" (Gemini convention).

        Returns:
            List of {"role": ..., "parts": [{"text": ...}]} dicts.
        """
        history = []
        for msg in self._history:
            gemini_role = "model" if msg.role == "assistant" else "user"
            history.append({
                "role": gemini_role,
                "parts": [{"text": msg.content}]
            })
        return history

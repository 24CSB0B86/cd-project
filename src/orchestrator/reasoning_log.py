"""
Reasoning Log — Week 13 XAI Layer
==================================
Structured audit trail that records every step of the AI agent's
ReAct (Reason + Act) loop, making decisions traceable and explainable.

Usage:
    log = ReasoningLog()
    log.record(EntryType.THOUGHT, "Checking scope for 'scale'")
    log.record(EntryType.ACTION, "check_scope", payload={"variable": "scale"})
    log.record(EntryType.OBSERVATION, "Result: 'scale' not in any scope")
    log.record(EntryType.FINDING, "Undefined variable", ast_node="Identifier",
               line=2, col=19)
    print(log.to_text())
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Entry types
# ---------------------------------------------------------------------------

class EntryType(str, Enum):
    THOUGHT     = "THOUGHT"
    ACTION      = "ACTION"
    OBSERVATION = "OBSERVATION"
    FINDING     = "FINDING"
    SUGGESTION  = "SUGGESTION"
    SECURITY    = "SECURITY"


# ---------------------------------------------------------------------------
# Log entry dataclass
# ---------------------------------------------------------------------------

@dataclass
class LogEntry:
    """A single timestamped entry in the reasoning log."""
    entry_type: EntryType
    message: str
    timestamp: float = field(default_factory=time.time)
    payload: Optional[Dict[str, Any]] = None
    ast_node: Optional[str] = None
    line: Optional[int] = None
    col: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.entry_type.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "ast_node": self.ast_node,
            "line": self.line,
            "col": self.col,
        }


# ---------------------------------------------------------------------------
# ReasoningLog
# ---------------------------------------------------------------------------

class ReasoningLog:
    """
    Structured audit trail for an AI debugging session.

    Records every Thought, Action, Observation, Finding, Suggestion, and
    Security event in sequential order, providing full traceability of the
    agent's decision process.

    Attributes:
        session_id : Unique identifier for this log session.
        entries    : Ordered list of LogEntry objects.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or str(uuid.uuid4())[:8]
        self.entries: List[LogEntry] = []
        self._start_time: float = time.time()

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(
        self,
        entry_type: EntryType,
        message: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
        ast_node: Optional[str] = None,
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> LogEntry:
        """
        Append a new entry to the log.

        Args:
            entry_type : One of the EntryType enum values.
            message    : Human-readable description of the event.
            payload    : Optional dict of structured data (tool args, results).
            ast_node   : AST node type that triggered this entry (e.g. 'Identifier').
            line       : Source line number associated with this entry.
            col        : Source column number associated with this entry.

        Returns:
            The newly created LogEntry.
        """
        entry = LogEntry(
            entry_type=entry_type,
            message=message,
            payload=payload,
            ast_node=ast_node,
            line=line,
            col=col,
        )
        self.entries.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def thought(self, message: str) -> LogEntry:
        """Record a THOUGHT step."""
        return self.record(EntryType.THOUGHT, message)

    def action(self, tool_name: str, args: Optional[Dict] = None) -> LogEntry:
        """Record an ACTION (tool call)."""
        msg = f"{tool_name}({', '.join(f'{k}={v!r}' for k, v in (args or {}).items())})"
        return self.record(EntryType.ACTION, msg, payload=args)

    def observation(self, result: str) -> LogEntry:
        """Record an OBSERVATION (tool result)."""
        return self.record(EntryType.OBSERVATION, result)

    def finding(
        self, message: str,
        ast_node: Optional[str] = None,
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> LogEntry:
        """Record a FINDING (diagnostic conclusion)."""
        return self.record(
            EntryType.FINDING, message,
            ast_node=ast_node, line=line, col=col
        )

    def suggestion(self, message: str) -> LogEntry:
        """Record a SUGGESTION (AI-generated fix recommendation)."""
        return self.record(EntryType.SUGGESTION, message)

    def security(
        self, message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
    ) -> LogEntry:
        """Record a SECURITY finding."""
        return self.record(EntryType.SECURITY, message, line=line, col=col)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_findings(self) -> List[LogEntry]:
        """Return only FINDING-type entries."""
        return [e for e in self.entries if e.entry_type == EntryType.FINDING]

    def get_security_entries(self) -> List[LogEntry]:
        """Return only SECURITY-type entries."""
        return [e for e in self.entries if e.entry_type == EntryType.SECURITY]

    def summary(self) -> Dict[str, int]:
        """Return counts per entry type."""
        counts: Dict[str, int] = {t.value: 0 for t in EntryType}
        for entry in self.entries:
            counts[entry.entry_type.value] += 1
        return counts

    def elapsed_seconds(self) -> float:
        """Elapsed wall-clock time since the log was created."""
        return time.time() - self._start_time

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def __len__(self) -> int:
        return len(self.entries)

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def to_text(self) -> str:
        """
        Return the full log as a human-readable plain-text string.

        Example output::

            [THOUGHT]   Checking scope for variable 'scale'
            [ACTION]    check_scope(variable_name='scale')
            [OBSERVE]   SCOPE CHECK: 'scale' is NOT defined in any scope.
            [FINDING]   Undefined variable 'scale' at Line 2, Col 19 (AST: Identifier)
        """
        if not self.entries:
            return "(empty reasoning log)"

        _LABELS = {
            EntryType.THOUGHT:     "[THOUGHT]  ",
            EntryType.ACTION:      "[ACTION]   ",
            EntryType.OBSERVATION: "[OBSERVE]  ",
            EntryType.FINDING:     "[FINDING]  ",
            EntryType.SUGGESTION:  "[SUGGEST]  ",
            EntryType.SECURITY:    "[SECURITY] ",
        }

        lines_out = [
            f"┌─ ReasoningLog  session={self.session_id}  entries={len(self.entries)} ─",
        ]
        for i, entry in enumerate(self.entries, 1):
            label = _LABELS.get(entry.entry_type, "[?]       ")
            loc = ""
            if entry.line:
                loc = f"  [L{entry.line}{',' + f'C{entry.col}' if entry.col else ''}]"
            node = f"  ast:{entry.ast_node}" if entry.ast_node else ""
            lines_out.append(f"  {i:02d}. {label} {entry.message}{loc}{node}")

        elapsed = self.elapsed_seconds()
        counts = self.summary()
        active = ", ".join(f"{k}={v}" for k, v in counts.items() if v > 0)
        lines_out.append(f"└─ elapsed={elapsed:.3f}s  {active}")
        return "\n".join(lines_out)

    def to_json(self) -> List[Dict[str, Any]]:
        """Return the log as a list of dicts (suitable for JSON serialization / Streamlit)."""
        return [e.to_dict() for e in self.entries]

    def __repr__(self) -> str:
        return f"ReasoningLog(session={self.session_id!r}, entries={len(self.entries)})"

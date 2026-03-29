"""
AST Annotator — Week 13 XAI Layer
=====================================
Cross-references ReasoningLog FINDING entries with AST nodes (by line/col)
and applies colour annotations to the ASTVisualizer.

Usage:
    annotator = ASTAnnotator(ast_root, reasoning_log)
    annotator.annotate(visualizer)
    # Now visualizer nodes are coloured by severity
    print(visualizer.to_text_tree())
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .reasoning_log import ReasoningLog, EntryType, LogEntry
from .ast_visualizer import (
    ASTVisualizer,
    COLOUR_CLEAN,
    COLOUR_WARNING,
    COLOUR_ERROR,
    COLOUR_CRITICAL,
)


# Severity → colour mapping
SEVERITY_COLOURS = {
    "CRITICAL": COLOUR_CRITICAL,
    "HIGH":     COLOUR_ERROR,
    "MEDIUM":   COLOUR_WARNING,
    "LOW":      COLOUR_WARNING,
    "ERROR":    COLOUR_ERROR,
    "WARNING":  COLOUR_WARNING,
}


class ASTAnnotator:
    """
    Applies diagnostic colour annotations to an :class:`ASTVisualizer` by
    cross-referencing a :class:`ReasoningLog`.

    The annotator builds a registry mapping (line, col) → AST node during a
    single depth-first traversal, then for each FINDING / SECURITY entry in
    the log, looks up the corresponding node and sets its colour on the
    visualizer.

    Args:
        root_node  : Root AST node (same value passed to ASTVisualizer).
        log        : ReasoningLog whose FINDING/SECURITY entries drive annotations.
    """

    def __init__(self, root_node: Any, log: ReasoningLog):
        self.root = root_node
        self.log = log
        # Registry: (line, col) → node object; col=None means any col at that line
        self._registry: Dict[Tuple[int, Optional[int]], Any] = {}
        self._build_registry(self.root)

    # ------------------------------------------------------------------
    # Registry construction
    # ------------------------------------------------------------------

    def _build_registry(self, node: Any) -> None:
        """DFS traversal to populate (line, col) → node registry."""
        if node is None:
            return
        line = getattr(node, "line", None)
        col  = getattr(node, "column", None) or getattr(node, "col", None)
        if line is not None:
            self._registry[(line, col)] = node
            self._registry[(line, None)] = node   # line-only fallback
        for child in self._children_of(node):
            self._build_registry(child)

    def _children_of(self, node: Any) -> List[Any]:
        """Extract child nodes (mirrors ASTVisualizer._children_of)."""
        children: List[Any] = []
        for attr in (
            "statements", "body", "params",
            "left", "right", "operand",
            "condition", "then_branch", "else_branch",
            "args", "value", "target",
            "init", "test", "update",
            "orelse", "elseifs",
        ):
            child = getattr(node, attr, None)
            if child is None:
                continue
            if isinstance(child, list):
                for c in child:
                    if c is not None and not isinstance(c, (str, int, float, bool)):
                        children.append(c)
            elif not isinstance(child, (str, int, float, bool)):
                children.append(child)
        return children

    # ------------------------------------------------------------------
    # Annotation
    # ------------------------------------------------------------------

    def annotate(self, visualizer: ASTVisualizer) -> int:
        """
        Apply colour annotations to *visualizer* based on the log's findings.

        Args:
            visualizer : The ASTVisualizer to colour.

        Returns:
            Number of nodes annotated.
        """
        visualizer.clear_annotations()
        annotated = 0
        for entry in self.log.entries:
            if entry.entry_type not in (EntryType.FINDING, EntryType.SECURITY):
                continue
            node = self._lookup_node(entry.line, entry.col)
            if node is None:
                continue
            colour = self._colour_for_entry(entry)
            visualizer.annotate_node(id(node), colour)
            annotated += 1
        return annotated

    def annotated_nodes(self) -> List[Tuple[Any, str]]:
        """
        Return a list of (node, colour) tuples for all annotatable findings
        without modifying a visualizer.
        """
        result: List[Tuple[Any, str]] = []
        for entry in self.log.entries:
            if entry.entry_type not in (EntryType.FINDING, EntryType.SECURITY):
                continue
            node = self._lookup_node(entry.line, entry.col)
            if node is not None:
                result.append((node, self._colour_for_entry(entry)))
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _lookup_node(
        self, line: Optional[int], col: Optional[int]
    ) -> Optional[Any]:
        """Find the AST node at (line, col), falling back to line-only."""
        if line is None:
            return None
        node = self._registry.get((line, col))
        if node is None:
            node = self._registry.get((line, None))
        return node

    @staticmethod
    def _colour_for_entry(entry: LogEntry) -> str:
        """Determine node fill colour from a log entry."""
        # Check payload for severity key
        if entry.payload:
            sev = entry.payload.get("severity", "").upper()
            if sev in SEVERITY_COLOURS:
                return SEVERITY_COLOURS[sev]
        # Security entries → CRITICAL colour
        if entry.entry_type == EntryType.SECURITY:
            return COLOUR_CRITICAL
        # FINDING without explicit severity → ERROR colour
        return COLOUR_ERROR

    def registry_size(self) -> int:
        """Number of unique (line, col) positions in the registry."""
        return len(self._registry)

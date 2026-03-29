"""
AST Visualizer — Week 13 XAI Layer
====================================
Converts the compiler's Abstract Syntax Tree into a Graphviz DOT graph
(rendered as SVG / PNG) or, when Graphviz is unavailable, a plain-text
indented tree.

Usage:
    from src.orchestrator.ast_visualizer import ASTVisualizer
    from src.compiler.lexer import Lexer
    from src.compiler.parser import Parser

    tokens = Lexer(source_code).tokenize()
    ast    = Parser(tokens).parse()

    viz = ASTVisualizer(ast)
    print(viz.to_text_tree())          # always works
    svg_path = viz.render('output')    # requires graphviz binary
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Node colour palette (used when annotations are applied)
# ---------------------------------------------------------------------------

COLOUR_CLEAN    = "#d4edda"   # green  — no findings
COLOUR_WARNING  = "#fff3cd"   # yellow — warnings
COLOUR_ERROR    = "#f8d7da"   # red    — semantic errors
COLOUR_CRITICAL = "#f5c6cb"   # deep red — CRITICAL security


# ---------------------------------------------------------------------------
# ASTVisualizer
# ---------------------------------------------------------------------------

class ASTVisualizer:
    """
    Renders a Mini-Python AST as a directed graph.

    By default produces a plain-text indented tree. If the `graphviz`
    Python package (and its binary) are available, it can also produce
    SVG / PNG output via :meth:`render`.

    Args:
        root_node : The root AST node returned by the Parser.
        title     : Optional graph title shown in the output.
    """

    def __init__(self, root_node: Any, title: str = "Mini-Python AST"):
        self.root = root_node
        self.title = title
        self._counter = 0
        self._node_annotations: dict[int, str] = {}   # id(node) → colour hex

    # ------------------------------------------------------------------
    # Annotation API (used by ASTAnnotator)
    # ------------------------------------------------------------------

    def annotate_node(self, node_id: int, colour: str) -> None:
        """Set background colour for a specific node (identified by id())."""
        self._node_annotations[node_id] = colour

    def clear_annotations(self) -> None:
        """Remove all colour annotations."""
        self._node_annotations.clear()

    # ------------------------------------------------------------------
    # Plain-text tree (always available)
    # ------------------------------------------------------------------

    def to_text_tree(self) -> str:
        """
        Return an indented text representation of the AST.

        Example::

            Program
              FunctionDef: compute
                params: ['a', 'b']
                ReturnStatement
                  BinaryOp: +
                    Identifier: a
                    Identifier: b

        Returns:
            Multi-line string.
        """
        lines: List[str] = [f"[AST] {self.title}"]
        self._text_visit(self.root, lines, indent=0)
        return "\n".join(lines)

    def _text_visit(self, node: Any, lines: List[str], indent: int) -> None:
        if node is None:
            return
        prefix = "  " * indent
        label = self._node_label(node)
        lines.append(f"{prefix}{label}")
        for child in self._children_of(node):
            self._text_visit(child, lines, indent + 1)

    # ------------------------------------------------------------------
    # Graphviz rendering (requires graphviz package + binary)
    # ------------------------------------------------------------------

    def render(self, output_path: str = "ast_output", fmt: str = "svg") -> Optional[str]:
        """
        Render the AST as a Graphviz graph and save to *output_path*.*fmt*.

        Args:
            output_path : File path without extension (e.g. ``'ast_output'``).
            fmt         : Output format — ``'svg'`` (default) or ``'png'``.

        Returns:
            Path to the rendered file, or ``None`` if Graphviz is unavailable.
        """
        try:
            import graphviz  # type: ignore
        except ImportError:
            return None

        try:
            dot = graphviz.Digraph(
                name=self.title,
                format=fmt,
                graph_attr={"rankdir": "TB", "fontname": "Helvetica"},
                node_attr={"shape": "box", "style": "filled,rounded",
                           "fillcolor": COLOUR_CLEAN, "fontname": "Helvetica",
                           "fontsize": "10"},
                edge_attr={"arrowsize": "0.7"},
            )
            self._counter = 0
            self._gv_visit(dot, self.root, parent_id=None)
            return dot.render(output_path, cleanup=True)
        except Exception:
            # Graphviz binary not installed or other rendering error
            return None

    def _gv_visit(self, dot: Any, node: Any, parent_id: Optional[str]) -> str:
        node_id = f"n{self._counter}"
        self._counter += 1
        label = self._node_label(node)
        colour = self._node_annotations.get(id(node), COLOUR_CLEAN)
        dot.node(node_id, label=repr(label), fillcolor=colour)
        if parent_id is not None:
            dot.edge(parent_id, node_id)
        for child in self._children_of(node):
            self._gv_visit(dot, child, node_id)
        return node_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _node_label(self, node: Any) -> str:
        """Build a concise label for a node."""
        class_name = type(node).__name__
        parts = [class_name]
        for attr in ("name", "op", "value"):
            val = getattr(node, attr, None)
            if val is not None:
                parts.append(str(val))
                break
        line = getattr(node, "line", None)
        if line:
            parts.append(f"L{line}")
        return " | ".join(parts)

    def _children_of(self, node: Any) -> List[Any]:
        """
        Return the child nodes of a given AST node.
        Mirrors the node types defined in ``src/compiler/ast_nodes.py``.
        """
        children: List[Any] = []
        # Common child attribute names used across all Mini-Python AST nodes
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

    def node_count(self) -> int:
        """Count total AST nodes via DFS."""
        count = [0]

        def _count(node: Any) -> None:
            if node is None:
                return
            count[0] += 1
            for child in self._children_of(node):
                _count(child)

        _count(self.root)
        return count[0]

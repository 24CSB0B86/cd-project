"""
test_week13_xai.py — Week 13: Explainability & Traceability (XAI)
=================================================================
33 deterministic tests for ReasoningLog, ASTVisualizer, ASTAnnotator.
Zero API calls required.
"""

import pytest
from src.orchestrator.reasoning_log import ReasoningLog, EntryType, LogEntry
from src.orchestrator.ast_visualizer import ASTVisualizer, COLOUR_CLEAN, COLOUR_ERROR
from src.orchestrator.ast_annotator import ASTAnnotator


# ── Shared fixtures ─────────────────────────────────────────────────────────

def make_ast(source: str = "x = 1\ny = x + 2"):
    from src.compiler.lexer import Lexer
    from src.compiler.parser import Parser
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


@pytest.fixture
def simple_ast():
    return make_ast()


@pytest.fixture
def empty_log():
    return ReasoningLog(session_id="test-empty")


@pytest.fixture
def populated_log():
    log = ReasoningLog(session_id="test-pop")
    log.thought("Checking scope for variable 'scale'")
    log.action("check_scope", {"variable_name": "scale"})
    log.observation("SCOPE CHECK: 'scale' is NOT defined in any scope.")
    log.finding("Undefined variable 'scale'", ast_node="Identifier", line=2, col=5)
    log.suggestion("Add 'scale' as a parameter or define it before use.")
    log.security("Potentially unsafe pattern detected", line=3)
    return log


# ── ReasoningLog — basic operations ──────────────────────────────────────────

class TestReasoningLogBasic:
    def test_empty_log_is_empty(self, empty_log):
        assert empty_log.is_empty()
        assert len(empty_log) == 0

    def test_session_id_set(self, empty_log):
        assert empty_log.session_id == "test-empty"

    def test_session_id_auto(self):
        log = ReasoningLog()
        assert len(log.session_id) > 0

    def test_record_thought(self, empty_log):
        entry = empty_log.record(EntryType.THOUGHT, "test thought")
        assert isinstance(entry, LogEntry)
        assert entry.entry_type == EntryType.THOUGHT
        assert entry.message == "test thought"
        assert len(empty_log) == 1

    def test_record_action_with_payload(self, empty_log):
        entry = empty_log.action("check_scope", {"variable_name": "x"})
        assert entry.entry_type == EntryType.ACTION
        assert entry.payload == {"variable_name": "x"}

    def test_record_finding_with_location(self, empty_log):
        entry = empty_log.finding("Error msg", ast_node="Identifier", line=5, col=3)
        assert entry.line == 5
        assert entry.col == 3
        assert entry.ast_node == "Identifier"

    def test_record_security(self, empty_log):
        entry = empty_log.security("CRITICAL: eval detected", line=2)
        assert entry.entry_type == EntryType.SECURITY
        assert entry.line == 2


# ── ReasoningLog — querying ──────────────────────────────────────────────────

class TestReasoningLogQuerying:
    def test_get_findings_returns_only_findings(self, populated_log):
        findings = populated_log.get_findings()
        assert all(e.entry_type == EntryType.FINDING for e in findings)

    def test_get_findings_count(self, populated_log):
        findings = populated_log.get_findings()
        assert len(findings) == 1

    def test_get_security_entries(self, populated_log):
        security = populated_log.get_security_entries()
        assert len(security) == 1
        assert security[0].entry_type == EntryType.SECURITY

    def test_summary_counts(self, populated_log):
        s = populated_log.summary()
        assert s["THOUGHT"] == 1
        assert s["ACTION"] == 1
        assert s["OBSERVATION"] == 1
        assert s["FINDING"] == 1
        assert s["SUGGESTION"] == 1
        assert s["SECURITY"] == 1

    def test_total_entries(self, populated_log):
        assert len(populated_log) == 6


# ── ReasoningLog — formatting ────────────────────────────────────────────────

class TestReasoningLogFormatting:
    def test_to_text_non_empty(self, populated_log):
        text = populated_log.to_text()
        assert len(text) > 0
        assert "THOUGHT" in text or "OBSERVE" in text

    def test_to_text_empty_log(self, empty_log):
        text = empty_log.to_text()
        assert "empty" in text.lower()

    def test_to_json_returns_list(self, populated_log):
        data = populated_log.to_json()
        assert isinstance(data, list)
        assert len(data) == 6

    def test_to_json_has_type_field(self, populated_log):
        data = populated_log.to_json()
        for entry in data:
            assert "type" in entry
            assert "message" in entry

    def test_repr(self, populated_log):
        r = repr(populated_log)
        assert "ReasoningLog" in r
        assert "test-pop" in r


# ── ASTVisualizer ────────────────────────────────────────────────────────────

class TestASTVisualizer:
    def test_text_tree_non_empty(self, simple_ast):
        viz = ASTVisualizer(simple_ast)
        text = viz.to_text_tree()
        assert len(text) > 0

    def test_text_tree_contains_program(self, simple_ast):
        viz = ASTVisualizer(simple_ast)
        text = viz.to_text_tree()
        assert "Program" in text

    def test_node_count_positive(self, simple_ast):
        viz = ASTVisualizer(simple_ast)
        count = viz.node_count()
        assert count > 0

    def test_annotate_node(self, simple_ast):
        viz = ASTVisualizer(simple_ast)
        viz.annotate_node(id(simple_ast), COLOUR_ERROR)
        assert id(simple_ast) in viz._node_annotations

    def test_clear_annotations(self, simple_ast):
        viz = ASTVisualizer(simple_ast)
        viz.annotate_node(id(simple_ast), COLOUR_ERROR)
        viz.clear_annotations()
        assert len(viz._node_annotations) == 0

    def test_render_returns_none_gracefully(self, simple_ast):
        """render() should return None if graphviz is unavailable, not raise."""
        viz = ASTVisualizer(simple_ast)
        # We don't assert the return value since graphviz may or may not be installed
        result = viz.render("/tmp/test_ast_output")
        assert result is None or isinstance(result, str)

    def test_custom_title(self, simple_ast):
        viz = ASTVisualizer(simple_ast, title="Test AST")
        text = viz.to_text_tree()
        assert "Test AST" in text


# ── ASTAnnotator ─────────────────────────────────────────────────────────────

class TestASTAnnotator:
    def test_registry_built(self, simple_ast, populated_log):
        annotator = ASTAnnotator(simple_ast, populated_log)
        assert annotator.registry_size() > 0

    def test_annotate_returns_count(self, simple_ast, populated_log):
        viz = ASTVisualizer(simple_ast)
        annotator = ASTAnnotator(simple_ast, populated_log)
        n = annotator.annotate(viz)
        assert isinstance(n, int)
        assert n >= 0

    def test_annotate_clears_previous(self, simple_ast, populated_log):
        viz = ASTVisualizer(simple_ast)
        viz.annotate_node(999, COLOUR_ERROR)   # stale annotation
        annotator = ASTAnnotator(simple_ast, populated_log)
        annotator.annotate(viz)
        # The stale id=999 should be gone after clear_annotations()
        assert 999 not in viz._node_annotations

    def test_annotated_nodes_returns_list(self, simple_ast, populated_log):
        annotator = ASTAnnotator(simple_ast, populated_log)
        nodes = annotator.annotated_nodes()
        assert isinstance(nodes, list)

    def test_empty_log_no_annotations(self, simple_ast, empty_log):
        viz = ASTVisualizer(simple_ast)
        annotator = ASTAnnotator(simple_ast, empty_log)
        n = annotator.annotate(viz)
        assert n == 0
        assert len(viz._node_annotations) == 0


# ── XAI Integration test ─────────────────────────────────────────────────────

class TestXAIIntegration:
    def test_full_xai_pipeline(self):
        """
        Full XAI pipeline: compile code → build log → visualize → annotate.
        """
        source = "def add(a, b):\n    return a + b + missing_var"
        from src.compiler.lexer import Lexer
        from src.compiler.parser import Parser
        from src.compiler.semantic_analyzer import SemanticAnalyzer

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        log = ReasoningLog(session_id="xai-test")
        for err in analyzer.errors:
            log.finding(
                err.message,
                ast_node="Identifier",
                line=err.line,
                col=err.column,
            )

        viz = ASTVisualizer(ast, title="Integration Test AST")
        annotator = ASTAnnotator(ast, log)
        n = annotator.annotate(viz)

        text = viz.to_text_tree()
        assert "Program" in text
        log_text = log.to_text()
        assert "FINDING" in log_text
        assert isinstance(n, int)

    def test_log_json_serializable(self, populated_log):
        import json
        data = populated_log.to_json()
        json_str = json.dumps(data)
        assert len(json_str) > 0

    def test_log_elapsed_positive(self, populated_log):
        elapsed = populated_log.elapsed_seconds()
        assert elapsed >= 0

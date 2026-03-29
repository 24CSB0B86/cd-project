"""
demo_week13_xai.py — Week 13: Explainability & Traceability (XAI) Demo
========================================================================
Shows the ReasoningLog, ASTVisualizer, and ASTAnnotator in action.

Usage:
    python demo_week13_xai.py
"""

from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer
from src.orchestrator.reasoning_log import ReasoningLog, EntryType
from src.orchestrator.ast_visualizer import ASTVisualizer
from src.orchestrator.ast_annotator import ASTAnnotator
from src.orchestrator.compiler_tools import CompilerToolbox

# ── Demo source code ──────────────────────────────────────────────────────

DEMO_CODE = """\
def compute(a, b):
    result = a + b + scale
    return result

total = compute(3, 4)
"""

DEMO_CLEAN = """\
def compute(a, b):
    result = a + b
    return result

total = compute(3, 4)
"""


def demo_reasoning_log():
    print("=" * 62)
    print("  DEMO 1: ReasoningLog — AI Audit Trail")
    print("=" * 62)

    log = ReasoningLog(session_id="demo-01")
    log.thought("Analysing errors in the submitted code...")
    log.action("get_errors", {})
    log.observation("ERRORS: 1 semantic error — 'scale' is not defined (Line 2, Col 19)")
    log.thought("Checking if 'scale' is in any scope...")
    log.action("check_scope", {"variable_name": "scale"})
    log.observation("SCOPE CHECK: 'scale' is NOT defined in any scope.")
    log.finding(
        "Undefined variable 'scale' — not found in global or local scope",
        ast_node="Identifier",
        line=2,
        col=19,
    )
    log.suggestion(
        "Add 'scale' as a parameter: def compute(a, b, scale): or define it before use."
    )

    print(log.to_text())
    print(f"\nSummary: {log.summary()}")
    print(f"Findings: {len(log.get_findings())}")


def demo_ast_visualizer():
    print("\n" + "=" * 62)
    print("  DEMO 2: ASTVisualizer — Parse Tree Rendering")
    print("=" * 62)

    tokens = Lexer(DEMO_CLEAN).tokenize()
    ast    = Parser(tokens).parse()
    viz    = ASTVisualizer(ast, title="compute() AST")

    print(viz.to_text_tree())
    print(f"\nTotal AST nodes: {viz.node_count()}")

    # Try Graphviz
    svg_path = viz.render("demo_ast_output")
    if svg_path:
        print(f"✅ AST rendered to SVG: {svg_path}")
    else:
        print("ℹ️  Graphviz binary not installed — text tree shown above.")


def demo_ast_annotator():
    print("\n" + "=" * 62)
    print("  DEMO 3: ASTAnnotator — Diagnostic Node Highlighting")
    print("=" * 62)

    # Compile the broken code
    tokens   = Lexer(DEMO_CODE).tokenize()
    ast      = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # Build the reasoning log from real compiler errors
    log = ReasoningLog(session_id="demo-03")
    for err in analyzer.errors:
        log.finding(
            err.message,
            ast_node="Identifier",
            line=err.line,
            col=err.column,
        )

    # Annotate
    viz       = ASTVisualizer(ast, title="Annotated AST — Error Highlighting")
    annotator = ASTAnnotator(ast, log)
    n         = annotator.annotate(viz)

    print(viz.to_text_tree())
    print(f"\nNodes annotated (highlighted): {n}")
    print(f"Annotation registry size      : {annotator.registry_size()}")
    print(f"Annotated (node, colour) pairs: {annotator.annotated_nodes()}")


def demo_full_xai_pipeline():
    print("\n" + "=" * 62)
    print("  DEMO 4: Full XAI Pipeline (Compile → Log → Annotate)")
    print("=" * 62)

    toolbox = CompilerToolbox.from_source(DEMO_CODE)
    errors  = toolbox.get_errors()
    sast    = toolbox.audit_security()

    log = ReasoningLog(session_id="demo-04")
    log.thought("Running full compiler pipeline on submitted code...")
    log.action("get_errors", {})
    log.observation(errors)
    log.action("audit_security", {})
    log.observation(sast)

    if "error" in errors.lower():
        log.finding("Semantic errors detected — see above for details", line=2)
    if "CLEAN" not in sast:
        log.security("Security issues detected by SAST engine")
    log.suggestion("Fix all FINDING-marked lines before submitting for review.")

    print(log.to_text())
    print("\n✅ Full XAI pipeline complete.")


if __name__ == "__main__":
    demo_reasoning_log()
    demo_ast_visualizer()
    demo_ast_annotator()
    demo_full_xai_pipeline()
    print("\n" + "=" * 62)
    print("  ✅ Week 13 XAI Demo Complete")
    print("=" * 62)

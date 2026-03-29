"""
demo_week16_live.py — Week 16: Final Live Demonstration
=========================================================
An end-to-end CLI demonstration script that incorporates the entire
Project 83 pipeline: Parsing → Semantic Analysis → SAST Security → 
AI Conversational Debugging → XAI Reasoning Logs → Visual AST.

Usage:
    python demo_week16_live.py
"""

import sys
import time

from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer
from src.orchestrator.security_auditor import SecurityAuditor
from src.orchestrator.reasoning_log import ReasoningLog
from src.orchestrator.ast_visualizer import ASTVisualizer
from src.orchestrator.ast_annotator import ASTAnnotator
from src.orchestrator.chat_interface import ConversationalDebugger


SCENARIO_1_CODE = """\
# Scenario 1: Mixed Errors & Security Threats
def process_data(user_input):
    # This acts as a logic bomb
    if user_input == "DROP TABLE":
        dummy = exec(user_input)
    
    # Semantic error: undefined variable
    result = eval(user_input) + missing_variable
    return result

final_result = process_data("data")
"""

def print_header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def main():
    print_header("Project 83 — Final Live CLI Demonstration (Week 16)")
    print("  Pipeline Initialising...")
    time.sleep(1)

    # 1. Provide the Code
    print("\n[1] Source Code Submitted:")
    print("─" * 40)
    for i, line in enumerate(SCENARIO_1_CODE.splitlines(), 1):
        print(f"{i:2d} | {line}")
    print("─" * 40)
    time.sleep(1.5)

    # 2. Run standard compiler pipeline
    print("\n[2] Running Front-End Compiler Pipeline (Lexer → Parser → Semantic)...")
    try:
        tokens = Lexer(SCENARIO_1_CODE).tokenize()
        ast = Parser(tokens).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        print(f"  ✅ Parsed {len(tokens)} tokens into AST.")
        if analyzer.errors:
            print(f"  ❌ Discovered {len(analyzer.errors)} semantic error(s).")
    except Exception as e:
        print(f"  💥 Fatal compiler crash: {e}")
        sys.exit(1)
    
    time.sleep(1.5)

    # 3. Security Auditor (SAST)
    print("\n[3] Running Static Application Security Testing (SAST) Engine...")
    report = SecurityAuditor().audit(SCENARIO_1_CODE)
    print(f"  => {report.summary}")
    for finding in report.findings:
        print(f"     • [{finding.severity}] Line {finding.line}: {finding.message}")
    
    time.sleep(1.5)

    # 4. XAI System & Annotations
    print("\n[4] Generating Explainable AI (XAI) Reasoning Log & Syntax Tree...")
    log = ReasoningLog(session_id="FINAL-DEMO")
    
    # Inject standard findings into log
    for err in analyzer.errors:
        log.finding(f"Semantic Error: {err.message}", line=err.line, col=err.column)
    for f in report.findings:
        log.security(f"[{f.severity}] {f.category} - {f.message}", line=f.line)
    log.thought("All static and security passes complete.")
    log.suggestion("Rewrite 'eval' and remove 'os.system' to secure the script. Define 'missing_variable'.")

    # Annotate the tree
    viz = ASTVisualizer(ast, title="Scenario 1 Annotated AST")
    annotator = ASTAnnotator(ast, log)
    annotated_count = annotator.annotate(viz)
    
    print(f"\n  ReasoningLog Audit Trail:")
    print(log.to_text())
    
    print(f"\n  Annotated AST (Terminal Fallback View):")
    print(viz.to_text_tree())
    print(f"  (Annotated {annotated_count} specific problematic nodes with XAI flags)")
    
    time.sleep(1.5)

    # 5. Bring in the AI Assistant
    print("\n[5] Launching Conversational Debugging Assistant...")
    debugger = ConversationalDebugger(use_api=False)  # Run in deterministic offline mode
    session = debugger.start_session(SCENARIO_1_CODE)
    
    print("\n🤖 Assistant (Initial Analysis):")
    print("─" * 60)
    print(session.get_last_assistant_message())
    print("─" * 60)

    time.sleep(1.5)

    # Simulate multi-turn
    print("\n👤 User: How do I fix the security issues?")
    response = debugger.send_message(session, "How do I fix the security issues (eval)?")
    print("\n🤖 Assistant (Simulated Advice):")
    print("─" * 60)
    print(response)
    print("─" * 60)
    
    print("\n✅ Final live pipeline demonstration complete.")

if __name__ == "__main__":
    main()

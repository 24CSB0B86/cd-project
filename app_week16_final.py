"""
Final Week 16 Streamlit App — Fully Integrated Project 83 Pipeline
Includes: AI Chat, Security Audit, Benchmarking, and Explainable AI (XAI).
Run: streamlit run app_week16_final.py
"""

import sys
import os
import time
import streamlit as st
from dotenv import load_dotenv

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from src.orchestrator.conversation_manager import ChatSession
from src.orchestrator.chat_interface import ConversationalDebugger

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Compiler Debugger — Final Project 83",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e2e8f0;
}

#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
.stDeployButton { display: none; }

.stApp { background: #0d1117 !important; }
.main .block-container {
    background: transparent !important;
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1300px;
}

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

.sb-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 0 1rem 1.25rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1.25rem;
}
.sb-brand-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #10b981, #7c3aed);
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 16px; flex-shrink: 0;
}
.sb-brand-title { font-size: 0.92rem; font-weight: 700; color: #f0f6fc !important; }
.sb-brand-sub { font-size: 0.68rem; color: #7d8590 !important; letter-spacing: 0.04em; text-transform: uppercase; }

.sb-mode-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; padding: 5px 12px; border-radius: 20px; margin-bottom: 1rem;
}
.sb-mode-badge.api { background: rgba(34,197,94,0.12); color: #4ade80 !important; border: 1px solid rgba(34,197,94,0.25); }
.sb-mode-badge.offline { background: rgba(251,191,36,0.12); color: #fbbf24 !important; border: 1px solid rgba(251,191,36,0.25); }
.sb-mode-dot { width: 6px; height: 6px; border-radius: 50%; animation: pulse-dot 1.8s ease-in-out infinite; }
.sb-mode-badge.api .sb-mode-dot { background: #4ade80; }
.sb-mode-badge.offline .sb-mode-dot { background: #fbbf24; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.3} }

.sb-section-label {
    font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: #7d8590 !important; font-weight: 600;
    margin: 1rem 0 0.5rem 0; padding: 0 0.25rem;
}
.sb-stat-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 8px; border-radius: 6px; font-size: 0.82rem; margin-bottom: 3px;
    background: rgba(255,255,255,0.03);
}
.sb-stat-row .stat-key { color: #8b949e !important; }
.sb-stat-row .stat-val { color: #e2e8f0 !important; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

.pipeline-step { display:flex; align-items:center; gap:8px; padding:5px 8px; border-radius:6px; font-size:0.75rem; margin-bottom:3px; }
.pipeline-step.active { background:rgba(16, 185, 129, 0.12); color:#10b981 !important; font-weight:600; }
.pipeline-step.done { color:#6e7681 !important; }
.pipeline-dot { width:5px; height:5px; border-radius:50%; flex-shrink:0; }
.pipeline-step.active .pipeline-dot { background:#10b981; }
.pipeline-step.done  .pipeline-dot  { background:#3d444d; }

/* ─── Top Bar ─── */
.top-bar {
    background: linear-gradient(135deg, #0d1a16 0%, #151a22 60%, #1a1025 100%);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 14px; padding: 20px 28px; margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
    position: relative; overflow: hidden;
}
.top-bar::before {
    content: ''; position: absolute; top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(16,185,129,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.top-bar-title {
    font-size: 1.4rem; font-weight: 800;
    background: linear-gradient(90deg, #e2e8f0, #a7f3d0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.01em; line-height: 1.2;
}
.top-bar-sub { font-size: 0.75rem; color: #7d8590; letter-spacing: 0.05em; text-transform:uppercase; margin-top:4px; }
.top-bar-badge {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 6px 16px; border-radius: 20px;
    background: rgba(16, 185, 129, 0.15); color: #6ee7b7;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] { background: #161b22 !important; border-radius: 10px; padding: 4px; gap: 4px; }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #8b949e !important;
    border-radius: 8px !important; padding: 10px 20px !important;
    font-size: 0.88rem !important; font-weight: 600 !important;
    border: none !important; transition: all 0.18s !important;
}
.stTabs [aria-selected="true"] {
    background: #21293c !important; color: #e2e8f0 !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.3) !important; border-bottom: 2px solid #6366f1 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }

/* ─── Metric Cards ─── */
.metric-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.metric-card {
    background:#161b22; border:1px solid rgba(255,255,255,0.06);
    border-radius:12px; padding:16px 18px; text-align:center;
    transition:transform 0.18s ease;
    position:relative; overflow:hidden;
}
.metric-card::after {
    content:''; position:absolute; top:0; left:0; right:0; height:2px; border-radius:12px 12px 0 0;
}
.metric-card.errors::after   { background:linear-gradient(90deg,#f87171,#ef4444); }
.metric-card.warnings::after { background:linear-gradient(90deg,#fbbf24,#f59e0b); }
.metric-card.turns::after    { background:linear-gradient(90deg,#34d399,#10b981); }
.metric-card.security::after { background:linear-gradient(90deg,#f97316,#dc2626); }
.metric-card.latency::after  { background:linear-gradient(90deg,#818cf8,#6366f1); }
.metric-card .val { font-size:2rem; font-weight:800; font-family:'JetBrains Mono',monospace; line-height:1; margin-bottom:6px; }
.metric-card.errors .val   { color:#f87171; }
.metric-card.warnings .val { color:#fbbf24; }
.metric-card.turns .val    { color:#34d399; }
.metric-card.security .val { color:#f97316; }
.metric-card.latency .val  { color:#a5b4fc; }
.metric-card .lbl { font-size:0.67rem; letter-spacing:0.1em; text-transform:uppercase; color:#7d8590; font-weight:500; }

/* ─── Code Boxes & Empty States ─── */
.streamlit-expanderHeader {
    background: #161b22 !important; border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important; color: #c9d1d9 !important; font-weight: 600 !important;
}
.streamlit-expanderContent { background: #161b22 !important; border: 1px solid rgba(255,255,255,0.06) !important; border-top: none !important;}
.stTextArea textarea {
    background: #0d1117 !important; border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.84rem !important;
}
.empty-state { text-align:center; padding:50px 20px; border:1px dashed rgba(99,102,241,0.2); border-radius:16px; background:rgba(99,102,241,0.03); margin:12px 0; }
.empty-state-icon { font-size:3rem; margin-bottom:16px; opacity:0.6; }
.empty-state-title { font-size:1rem; font-weight:600; color:#8b949e; margin-bottom:8px; }

/* ─── Security Findings ─── */
.sec-finding {
    border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; border-left: 4px solid; background: #161b22;
}
.sec-finding.CRITICAL { border-color:#dc2626; }
.sec-finding.HIGH     { border-color:#ea580c; }
.sec-finding.MEDIUM   { border-color:#eab308; }
.sec-finding.LOW      { border-color:#22c55e; }
.sec-finding-badge { font-size:0.65rem; font-weight:700; padding:2px 9px; border-radius:12px; margin-right:8px; }
.sec-finding.CRITICAL .sec-finding-badge { background:rgba(220,38,38,0.25); color:#fca5a5; }

/* ─── XAI Logs ─── */
.xai-log-box {
    background: #10141f; border-left: 3px solid #818cf8; padding: 15px;
    border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;
    white-space: pre-wrap; color: #c9d1d9; max-height: 400px; overflow-y: auto;
}
.section-label { font-size:0.75rem; letter-spacing:0.1em; text-transform:uppercase; color:#8b949e; font-weight:700; border-bottom:1px solid #30363d; padding-bottom:8px; margin-bottom:15px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Init
# ─────────────────────────────────────────────────────────────────────────────
def _api_available() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())

def _init():
    defaults = {
        "chat_session": None, "debugger": None,
        "code_loaded": False, "current_code": "", "_textarea_value": "",
        "sec_audit_code": "", "sec_audit_result": None,
        "bench_results": None, "xai_log": None, "xai_ast": None, "messages": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "🌐 Web Mode (API)" if _api_available() else "🌐 Web Mode (Offline)"

_init()

MODES = ["🌐 Web Mode (API)", "🌐 Web Mode (Offline)"]
app_mode  = st.session_state.get("app_mode", MODES[0])
use_api   = "(API)" in app_mode
mode_label= "API" if use_api else "OFFLINE"
mode_class= "api" if use_api else "offline"


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sb-brand">
      <div class="sb-brand-icon">🧠</div>
      <div>
        <div class="sb-brand-title">Project 83</div>
        <div class="sb-brand-sub">Final 16-Week Pipeline</div>
      </div>
    </div>
    <div style="padding:0 0.5rem;margin-bottom:1rem;">
      <div class="sb-mode-badge {mode_class}">
        <span class="sb-mode-dot"></span>{mode_label} Enabled
      </div>
    </div>
    <div class="sb-section-label" style="padding:0 0.5rem;">Interface Mode</div>
    """, unsafe_allow_html=True)

    st.selectbox("Mode:", MODES, key="app_mode", label_visibility="collapsed")

    s: ChatSession = st.session_state.chat_session
    if s:
        st.markdown(f"""
        <div class="sb-section-label" style="padding:0 0.5rem;margin-top:1.25rem;">Live Context</div>
        <div style="padding:0 0.25rem;">
          <div class="sb-stat-row"><span class="stat-key">Errors</span><span class="stat-val">{s.error_count}</span></div>
          <div class="sb-stat-row"><span class="stat-key">Tokens parsed</span><span class="stat-val">{len(s.toolbox.analyzer.symbol_table.scopes) if s.toolbox else 0}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section-label" style="padding:0 0.5rem;margin-top:1.5rem;">Pipeline Evolution</div>', unsafe_allow_html=True)
    pipeline = [
        ("Wk5–Wk7", "Front-end Compiler"),
        ("Wk8–Wk9", "Gemini AI & Agentic Tools"),
        ("Wk10", "Chat Debugger Web V1"),
        ("Wk11", "Security Auditing SAST"),
        ("Wk12", "Benchmarking Engine"),
        ("Wk13", "Explainability (XAI)"),
        ("Wk16", "Final 100% Integration"),
    ]
    for i, (week, name) in enumerate(pipeline):
        cls = "active" if i == 6 else "done"
        st.markdown(f"""
        <div class="pipeline-step {cls}" style="padding-left:0.75rem;">
          <span class="pipeline-dot"></span>
          <span style="font-size:0.65rem;opacity:0.6;min-width:45px;">{week}</span>
          <span>{name}</span>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Top bar
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="top-bar">
  <div>
    <div class="top-bar-title">Agentic AI Compiler Assistant</div>
    <div class="top-bar-sub">Final Demo &mdash; Chat, SAST, Benchmarks, XAI Traceability</div>
  </div>
  <div class="top-bar-badge">FINAL RELEASE</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_debug, tab_security, tab_benchmarks, tab_xai = st.tabs([
    "🔬 Debug Chat", "🛡️ Security Audit", "📊 Benchmarks (W12)", "🧠 Explainable AI (W13)"
])

# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — Debug Chat (Core Interface)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_debug:
    SAMPLES = {
        "— select a sample —": "",
        "✅ Safe Recursive Fibonacci": "def fib(n):\n    if n < 2:\n        return n\n    return fib(n-1) + fib(n-2)\nprint(fib(5))",
        "❌ Semantic Error": "def add(a, b):\n    return a + b + missing\nresult = add(1, 2)",
        "🛡️ SAST Security Threat": "user_input = '1'\nresult = eval(user_input)\nimport os",
    }
    
    def _on_sample_change():
        sel = st.session_state.get("sample_sel", "")
        if SAMPLES.get(sel):
            st.session_state["_textarea_value"] = SAMPLES[sel]

    with st.expander("📝 Compiler Code Editor", expanded=not st.session_state.code_loaded):
        st.selectbox("Load a sample:", list(SAMPLES.keys()), key="sample_sel", on_change=_on_sample_change)
        code_input = st.text_area(
            "Source code:", value=st.session_state["_textarea_value"], height=200,
            label_visibility="collapsed")
        
        col1, col2 = st.columns([3, 1])
        if col1.button("⚙️ Compile & Run Full Pipeline", use_container_width=True):
            if code_input.strip():
                with st.spinner("Compiling Lexer->Parser->Semantic->XAI..."):
                    debugger = ConversationalDebugger(use_api=use_api)
                    session  = debugger.start_session(code_input.strip())
                    st.session_state.debugger = debugger
                    st.session_state.chat_session = session
                    st.session_state.current_code = code_input.strip()
                    st.session_state.code_loaded  = True
                    
                    # Compute XAI directly so it's available in the other tab
                    try:
                        from src.compiler.lexer import Lexer
                        from src.compiler.parser import Parser
                        from src.compiler.semantic_analyzer import SemanticAnalyzer
                        from src.orchestrator.reasoning_log import ReasoningLog
                        from src.orchestrator.ast_visualizer import ASTVisualizer
                        from src.orchestrator.ast_annotator import ASTAnnotator
                        from src.orchestrator.security_auditor import SecurityAuditor
                        
                        toks = Lexer(code_input.strip()).tokenize()
                        ast = Parser(toks).parse()
                        analyzer = SemanticAnalyzer()
                        analyzer.analyze(ast)
                        sast = SecurityAuditor().audit(code_input.strip())
                        
                        log = ReasoningLog(session_id="FINAL-GUI")
                        for err in analyzer.errors:
                            log.finding(f"Semantic Error: {err.message}", line=err.line)
                        for f in sast.findings:
                            log.security(f"[{f.severity}] {f.category}", line=f.line)
                            
                        viz = ASTVisualizer(ast, "XAI Annotated Tree")
                        ASTAnnotator(ast, log).annotate(viz)
                        
                        st.session_state.xai_log = log.to_text()
                        st.session_state.xai_ast = viz.to_text_tree()
                    except Exception as e:
                        st.session_state.xai_log = f"Error generating XAI: {e}"
                        st.session_state.xai_ast = "Cannot visualize AST due to syntax error"
                st.rerun()

    if st.session_state.chat_session:
        s = st.session_state.chat_session
        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card errors"><div class="val">{s.error_count}</div><div class="lbl">Semantic Errors</div></div>
            <div class="metric-card warnings"><div class="val">{len(s.analyzer.warnings) if s.analyzer else 0}</div><div class="lbl">Warnings</div></div>
            <div class="metric-card security"><div class="val">{len(st.session_state.chat_session.get_history())}</div><div class="lbl">Chat Msgs</div></div>
            <div class="metric-card latency"><div class="val">&lt;5 ms</div><div class="lbl">Offline Latency</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<p class="section-label">💬 AI Diagnostic Conversation</p>', unsafe_allow_html=True)
        if len(s.get_history()) > 0:
            for msg in s.get_history()[-4:]:  # Show last 4 messages 
                role = msg["role"]
                text = msg["content"]
                bg = "rgba(99,102,241,0.15)" if role == "assistant" else "rgba(255,255,255,0.05)"
                border = "#6366f1" if role == "assistant" else "transparent"
                st.markdown(f"""
                <div style="background:{bg}; border-left: 3px solid {border}; padding:15px; border-radius:8px; margin-bottom:10px;">
                <strong style="color:#a5b4fc;">{'🤖 AI Debugger' if role == 'assistant' else '👱 User'}:</strong><br>
                <div style="white-space:pre-wrap; font-size: 0.9rem; margin-top:5px;">{text.replace('<', '&lt;')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        ui = st.chat_input("Ask the Gemini Compiler Assistant about the code...")
        if ui:
            with st.spinner("Agentic reasoning..."):
                response = st.session_state.debugger.send_message(s, ui)
            st.rerun()
    else:
        st.info("Paste code and click **Compile & Run Full Pipeline** to start.", icon="👆")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — Security Audit (From Week 11)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_security:
    st.markdown('<p class="section-label">Static Application Security Testing</p>', unsafe_allow_html=True)
    if st.session_state.code_loaded:
        from src.orchestrator.security_auditor import SecurityAuditor
        report = SecurityAuditor().audit(st.session_state.current_code)
        
        if report.is_safe:
            st.success("✅ SAST Scan Passed. No critical threats detected in the code.")
        else:
            st.error(f"🚨 SAST Scan Failed. Found {len(report.findings)} security vulnerabilities.")
            
        for f in report.findings:
            col = "CRITICAL" if f.severity == "CRITICAL" else "HIGH" if f.severity == "HIGH" else "MEDIUM"
            st.markdown(f"""
            <div class="sec-finding {col}">
                <span class="sec-finding-badge">{f.severity}</span>
                <span style="font-size:0.8rem;color:#8b949e">Line {f.line} &nbsp;|&nbsp; {f.category}</span>
                <div style="color:#e2e8f0;margin-top:5px;font-size:0.9rem;">{f.message}</div>
                <div style="font-family:'JetBrains Mono',monospace;color:#fca5a5;background:rgba(0,0,0,0.3);padding:5px;margin-top:5px;">↳ {f.snippet.replace('<','&lt;')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Run the compiler on Tab 1 first to view security audits.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — Benchmarks (From Week 12)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_benchmarks:
    st.markdown('<p class="section-label">Compiler Pipeline Latency & Memory</p>', unsafe_allow_html=True)
    if st.button("🚀 Run Live Benchmark Matrix"):
        from src.benchmarks.benchmark_suite import BenchmarkSuite
        with st.spinner("Running 50 iterations of deterministic latency tests..."):
            suite = BenchmarkSuite(st.session_state.get('current_code', 'x=1') if st.session_state.code_loaded else "def f():\n  pass", iterations=50)
            res = suite.run_all()
            st.session_state.bench_results = res
            
    if st.session_state.bench_results:
        st.success("Benchmark completed across 50 iterations.")
        data = []
        for r in st.session_state.bench_results:
            data.append({"Stage": r.stage, "Mean Latency (ms)": round(r.mean_ms, 3), "Peak Memory (KB)": round(r.peak_kb, 1)})
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Click 'Run Live Benchmark Matrix' to execute pipeline latency tests.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 4 — Explainable AI (From Week 13)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_xai:
    st.markdown('<p class="section-label">XAI Traceability & Graph Audit</p>', unsafe_allow_html=True)
    if st.session_state.code_loaded and st.session_state.xai_log:
        st.markdown("**1. ReasoningLog (Auditable ReAct Trace)** : Interpretable logic sequence")
        st.markdown(f'<div class="xai-log-box">{st.session_state.xai_log}</div>', unsafe_allow_html=True)
        
        st.markdown("<br>**2. Abstract Syntax Tree (Diagnostic Node Highlighting)** : Structural view", unsafe_allow_html=True)
        st.markdown(f'<div class="xai-log-box">{st.session_state.xai_ast}</div>', unsafe_allow_html=True)
    else:
        st.info("Compile code with errors/security issues in Tab 1 to generate XAI logs.")

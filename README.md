# Project 83: Agentic AI Compiler Assistant

A **Mini-Python Compiler** enhanced with a **Gemini AI Agent** that provides intelligent error explanations, targeted diagnostics, code suggestions, and **Security Risk Auditing (SAST)** — built from scratch over 11 weeks as part of a Compiler Design project.

---

## 📌 Project Overview

| Item | Detail |
|---|---|
| **Language** | Python 3.12 |
| **AI Backend** | Google Gemini API (`gemini-2.5-flash`) |
| **Status** | ✅ Complete (Week 16) — 392 tests passing |
| **Pipeline** | Source → Lexer → Parser → Semantic → SecurityAuditor → Toolbox → XAI (Reasoning/AST) → AgenticGemini → ChatSession → ConversationalDebugger |

---

## 🗂️ Folder Structure

```
CD-Project/
├── .env.example              # Template for API keys (copy to .env)
├── .gitignore                # Excludes .env, __pycache__, venv/
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── project_status.md         # Detailed progress tracker
│
├── src/
│   ├── compiler/             # Front-end compiler (built from scratch)
│   │   ├── tokens.py         # TokenType enum definitions
│   │   ├── lexer.py          # Regex-based lexical analyzer (INDENT/DEDENT support)
│   │   ├── ast_nodes.py      # AST node hierarchy (16 node types)
│   │   ├── parser.py         # Recursive descent parser
│   │   ├── semantic_analyzer.py  # Symbol table, scope & type checking
│   │   └── tac_generator.py  # [BONUS] Three Address Code generator
│   └── orchestrator/         # AI layer (Gemini integration)
│       ├── gemini_client.py      # GeminiCompilerAgent + AgenticGeminiClient
│       ├── context_provider.py   # Serializes AST/SymbolTable for AI
│       ├── compiler_tools.py     # [Week 9/11] 8 compiler tools incl. audit_security
│       ├── tool_registry.py      # [Week 9/11] Gemini function declaration schemas
│       ├── conversation_manager.py # [Week 10] ChatSession multi-turn state
│       ├── chat_interface.py     # [Week 10] ConversationalDebugger + CLI
│       ├── security_auditor.py   # [Week 11] Pure-Python SAST engine
│       └── security_agent.py     # [Week 11] Gemini security wrapper
│
├── tests/
│   ├── test_week5_lexer.py       # 13 tests — Lexer
│   ├── test_week6_parser.py      # 27 tests — Parser
│   ├── test_week7_semantic.py    # 16 tests — Semantic Analyzer
│   ├── test_week8_context.py     # 27 tests — Context Provider (AI)
│   ├── test_week8_tac.py         # 39 tests — TAC Generator (Bonus)
│   ├── test_week9_tools.py       # 59 tests — Agentic Tools
│   ├── test_week10_chat.py       # 25 tests — Conversational Interface
│   ├── test_week11_security.py   # 52 tests — Security Risk Auditing
│   ├── test_week12_benchmarks.py # 38 tests — Benchmarking & Accuracy
│   ├── test_week13_xai.py        # 33 tests — Explainability & Traceability
│   ├── test_week14_e2e.py        # 57 tests — E2E & Bug Squashing
│   └── test_integration_weeks5_7.py  # 6 integration tests
│
├── grammar/
│   └── mini_python.ebnf      # EBNF grammar definition
│
├── docs/
│   ├── DetailedExecutionPlanandReport.tex
│   ├── ProjectDescriptionMethodologicalApproach.tex
│   └── prompts.md
│
├── reports/
│   ├── week_01_report.tex ... week_16_report.tex
│   ├── SRS_latex.tex
│   ├── literature_review.tex
│   └── comprehensive_project_overview.tex
│
└── demo scripts
    ├── demo_week5_lexer.py
    ├── demo_week6_parser.py
    ├── demo_week7_semantic.py
    ├── demo_week8_ai.py
    ├── demo_week8_tac.py
    ├── demo_week9_agentic.py
    ├── demo_week10_chat.py
    ├── demo_week11_security.py
    ├── demo_week12_benchmark.py
    ├── demo_week13_xai.py
    └── demo_week16_live.py
```

---

## 🚀 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd CD-Project
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file (copy from `.env.example`) and add your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=models/gemini-2.5-flash
```
> ⚠️ **Never commit your `.env` file.** It is listed in `.gitignore`.

---

## 🧪 Running Tests

```bash
# Run all 392 tests
python -m pytest tests/ -v

# Run tests for a specific week
python -m pytest tests/test_week5_lexer.py -v
python -m pytest tests/test_week6_parser.py -v
python -m pytest tests/test_week7_semantic.py -v
python -m pytest tests/test_week8_context.py -v
python -m pytest tests/test_week9_tools.py -v
python -m pytest tests/test_week10_chat.py -v
python -m pytest tests/test_week11_security.py -v
```

---

## 🎬 Demo Scripts

```bash
python demo_week5_lexer.py       # Lexer demo
python demo_week6_parser.py      # Parser + AST demo
python demo_week7_semantic.py    # Semantic analysis demo
python demo_week8_ai.py          # AI context demo (mock mode)
python demo_week8_ai.py --api    # AI context demo (live Gemini API)
python demo_week8_tac.py         # Three Address Code demo (bonus)
python demo_week9_agentic.py          # Agentic tool-use demo (offline)
python demo_week9_agentic.py --api    # Agentic tool-use demo (live Gemini API)
python demo_week10_chat.py            # Conversational debugging demo (offline)
python demo_week10_chat.py --api      # Conversational demo (live Gemini API)
python demo_week10_chat.py --interactive  # Full interactive CLI chatbot
python demo_week11_security.py        # Security audit demo (SAST, no API needed)
python demo_week12_benchmark.py       # Performance & Latency benchmarks
python demo_week13_xai.py             # Traceability logs & Annotated AST tree
python demo_week16_live.py            # Final comprehensive CLI E2E demonstration
streamlit run app_week11_streamlit.py # Security Audit + Chat web UI
```

---

## 📋 Week-by-Week Progress

| Week | Deliverable | Status |
|------|-------------|--------|
| 1 | Project definition, grammar (EBNF) | ✅ Done |
| 2 | Gemini API setup, environment | ✅ Done |
| 3 | Software Requirements Specification | ✅ Done |
| 4 | Architecture design | ✅ Done |
| 5 | Lexer (tokenizer) | ✅ Done — 13 tests |
| 6 | Parser (recursive descent) + AST | ✅ Done — 27 tests |
| 7 | Semantic Analyzer (symbol table) | ✅ Done — 16 tests |
| 8 | Gemini API integration + Context Provider | ✅ Done — 27 tests |
| 9 | Agentic Tool-Use (Function Calling) | ✅ Done — 59 tests |
| 10 | Conversational Debugging Interface | ✅ Done — 25 tests |
| 11 | Security Risk Auditing Agent (SAST) | ✅ Done — 52 tests |
| 12 | Performance Benchmarking & Accuracy Evaluation | ✅ Done — 38 tests |
| 13 | Explainability & Traceability (XAI) | ✅ Done — 33 tests |
| 14 | Integration Testing & Bug Squashing | ✅ Done — 57 tests |
| 15 | Documentation & Finalization | ✅ Done |
| 16 | Final Live Demonstration & Submission | ✅ Done |

---

## 🔑 Key Design Decisions

- **Regex-based Lexer**: Handles Python-style significant whitespace via INDENT/DEDENT tokens.
- **Recursive Descent Parser**: Manually implemented (no parser generator) for learning and full control.
- **Context Provider**: Serializes the compiler's internal state (AST, Symbol Table, errors) into natural language before sending to Gemini — giving the AI true understanding of the code structure.
- **TAC Generator**: Bonus intermediate code generation (21 op-codes) for further backend processing.
- **SAST Engine**: Pure-Python Static Application Security Testing — no API needed, 100% deterministic, detects eval/exec RCE, Prompt Injection in comments, Logic Bombs, and infinite recursion.
- **Graceful AI Degradation**: The `SecurityAgent` always runs SAST first; Gemini deep-analysis is optional and degrades gracefully when the API key is absent.

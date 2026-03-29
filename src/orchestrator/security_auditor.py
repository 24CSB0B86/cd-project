"""
Security Risk Auditing Engine — Week 11
Static Application Security Testing (SAST) for Mini-Python source code.

Detects:
  - Unsafe builtins  : eval(), exec(), __import__(), compile(), os.system()
  - Dangerous imports: import os, import subprocess, import sys
  - Prompt Injection : injection keywords hidden in code comments
  - Logic Bombs      : time/date-triggered conditional heuristics
  - Infinite recursion heuristic: a function calling itself with no guard

No Gemini API calls — all analysis is pure Python regex + heuristics.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class SecurityFinding:
    """A single security issue found in source code."""
    severity: str          # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    category: str          # see CATEGORY_* constants below
    line: int              # 1-indexed line number
    column: int            # 1-indexed column number
    message: str           # human-readable description
    snippet: str           # the offending source line (stripped)

    # Category constants
    CATEGORY_UNSAFE_BUILTIN    = "UNSAFE_BUILTIN"
    CATEGORY_DANGEROUS_IMPORT  = "DANGEROUS_IMPORT"
    CATEGORY_PROMPT_INJECTION  = "PROMPT_INJECTION"
    CATEGORY_LOGIC_BOMB        = "LOGIC_BOMB"
    CATEGORY_INFINITE_RECURSION = "INFINITE_RECURSION"


@dataclass
class AuditReport:
    """Complete security audit results for a source file."""
    findings: List[SecurityFinding] = field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        """True only when there are no CRITICAL or HIGH findings."""
        return not any(
            f.severity in ("CRITICAL", "HIGH") for f in self.findings
        )

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "CRITICAL")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "HIGH")

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "MEDIUM")

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "LOW")

    @property
    def summary(self) -> str:
        if not self.findings:
            return "✅ CLEAN — No security threats detected."
        parts = []
        if self.critical_count:
            parts.append(f"{self.critical_count} CRITICAL")
        if self.high_count:
            parts.append(f"{self.high_count} HIGH")
        if self.medium_count:
            parts.append(f"{self.medium_count} MEDIUM")
        if self.low_count:
            parts.append(f"{self.low_count} LOW")
        label = "UNSAFE" if not self.is_safe else "CAUTION"
        return f"🚨 {label} — {len(self.findings)} finding(s): {', '.join(parts)}"

    def to_text(self) -> str:
        """Format the full report as a human-readable string."""
        lines = [
            "═" * 60,
            "  SECURITY AUDIT REPORT — Week 11 SAST Engine",
            "═" * 60,
            f"  Status  : {self.summary}",
            f"  Safe    : {'YES' if self.is_safe else 'NO'}",
            f"  Findings: {len(self.findings)}",
            "─" * 60,
        ]
        if not self.findings:
            lines.append("  No security issues found.\n")
        else:
            for i, f in enumerate(self.findings, 1):
                sev_icon = {
                    "CRITICAL": "🔴", "HIGH": "🟠",
                    "MEDIUM": "🟡", "LOW": "🟢"
                }.get(f.severity, "⚪")
                lines.append(
                    f"  [{i}] {sev_icon} {f.severity} — {f.category}"
                )
                lines.append(f"       Line {f.line}, Col {f.column}")
                lines.append(f"       {f.message}")
                lines.append(f"       ↳ `{f.snippet}`")
                lines.append("")
        lines.append("═" * 60)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# SecurityAuditor
# ---------------------------------------------------------------------------

class SecurityAuditor:
    """
    Static Application Security Testing (SAST) engine for Mini-Python code.

    Usage:
        auditor = SecurityAuditor()
        report  = auditor.audit(source_code)
        print(report.to_text())
    """

    # ── Unsafe builtin patterns ──────────────────────────────────────────
    UNSAFE_BUILTINS = [
        (r"\beval\s*\(",           "CRITICAL", "eval() executes arbitrary code — severe RCE risk"),
        (r"\bexec\s*\(",           "CRITICAL", "exec() executes arbitrary code — severe RCE risk"),
        (r"\bcompile\s*\(",        "HIGH",     "compile() can build and run arbitrary bytecode"),
        (r"\b__import__\s*\(",     "CRITICAL", "__import__() bypasses normal import safety guards"),
        (r"\bos\.system\s*\(",     "HIGH",     "os.system() executes shell commands — command injection risk"),
        (r"\bos\.popen\s*\(",      "HIGH",     "os.popen() opens a shell pipe — command injection risk"),
        (r"\bsubprocess\.",        "HIGH",     "subprocess module executes external processes"),
        (r"\bpickle\.loads\s*\(",  "HIGH",     "pickle.loads() deserialises untrusted data — RCE risk"),
        (r"\bopen\s*\(",           "MEDIUM",   "open() reads/writes files — verify path is not user-controlled"),
        (r"\bgetattr\s*\(",        "LOW",      "getattr() may bypass attribute access controls"),
        (r"\bsetattr\s*\(",        "LOW",      "setattr() may corrupt object state unexpectedly"),
    ]

    # ── Dangerous import patterns ────────────────────────────────────────
    DANGEROUS_IMPORTS = [
        (r"^\s*import\s+os\b",          "HIGH",   "import os — grants shell/filesystem access"),
        (r"^\s*import\s+subprocess\b",  "HIGH",   "import subprocess — allows external process execution"),
        (r"^\s*import\s+sys\b",         "MEDIUM", "import sys — grants interpreter introspection"),
        (r"^\s*import\s+ctypes\b",      "CRITICAL","import ctypes — direct C memory access, very dangerous"),
        (r"^\s*import\s+socket\b",      "MEDIUM", "import socket — opens network access"),
        (r"^\s*from\s+os\s+import",     "HIGH",   "from os import — grants shell/filesystem access"),
        (r"^\s*from\s+subprocess",      "HIGH",   "from subprocess — allows external process execution"),
    ]

    # ── Prompt Injection keywords in comments ────────────────────────────
    # Attackers embed these in code comments to hijack AI assistants
    PROMPT_INJECTION_KEYWORDS = [
        "ignore previous",
        "ignore all previous",
        "disregard",
        "forget previous",
        "system:",
        "override",
        "new instructions",
        "act as",
        "you are now",
        "jailbreak",
        "do anything now",
        "dan mode",
        "ignore instructions",
        "bypass",
        "prompt injection",
    ]

    # ── Logic bomb heuristics ────────────────────────────────────────────
    # Patterns that suggest time/date triggered payloads
    LOGIC_BOMB_PATTERNS = [
        (
            r"(datetime|date|time|now)\s*\(?\)?\s*[<>=!]=?\s*['\"\d]",
            "HIGH",
            "Time/date comparison detected — possible Logic Bomb trigger condition"
        ),
        (
            r"os\.getenv\s*\(.*\)\s*==",
            "HIGH",
            "Environment variable equality check — possible Logic Bomb (env-triggered payload)"
        ),
        (
            r"if\s+.*\b(today|now|current_date|timestamp)\b.*:",
            "MEDIUM",
            "Conditional on time variable — possible Logic Bomb heuristic"
        ),
        (
            r"(DELETE|DROP|TRUNCATE|FORMAT|ERASE|WIPE)\s*\(",
            "CRITICAL",
            "Destructive operation call detected — possible Logic Bomb payload"
        ),
        (
            r"os\.(remove|unlink|rmdir|system)\s*\(",
            "HIGH",
            "File/directory deletion call — possible Logic Bomb destructive payload"
        ),
    ]

    # ── Simple infinite recursion heuristic ─────────────────────────────
    # Detects: def foo(...): ... foo(...) with no apparent if/return guard
    _FUNC_DEF_RE    = re.compile(r"^\s*def\s+(\w+)\s*\(")
    _FUNC_CALL_RE   = re.compile(r"\b(\w+)\s*\(")

    # ────────────────────────────────────────────────────────────────────

    def audit(self, source_code: str) -> AuditReport:
        """
        Run the full SAST scan on source_code.

        Args:
            source_code: Mini-Python source code string

        Returns:
            AuditReport with all findings.
        """
        report = AuditReport()
        lines = source_code.splitlines()

        self._scan_unsafe_builtins(lines, report)
        self._scan_dangerous_imports(lines, report)
        self._scan_prompt_injection(lines, report)
        self._scan_logic_bombs(lines, report)
        self._scan_infinite_recursion(lines, report)

        logger.info(
            f"Security audit complete: {len(report.findings)} finding(s), "
            f"safe={report.is_safe}"
        )
        return report

    # ── Scanner: Unsafe builtins ─────────────────────────────────────────

    def _scan_unsafe_builtins(self, lines: List[str], report: AuditReport):
        for lineno, line in enumerate(lines, 1):
            # Skip pure comment lines for builtin checks
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Remove inline comments for matching
            code_part = re.sub(r"#.*$", "", line)
            for pattern, severity, message in self.UNSAFE_BUILTINS:
                match = re.search(pattern, code_part)
                if match:
                    report.findings.append(SecurityFinding(
                        severity=severity,
                        category=SecurityFinding.CATEGORY_UNSAFE_BUILTIN,
                        line=lineno,
                        column=match.start() + 1,
                        message=message,
                        snippet=stripped[:120],
                    ))
                    break  # one finding per line per category

    # ── Scanner: Dangerous imports ───────────────────────────────────────

    def _scan_dangerous_imports(self, lines: List[str], report: AuditReport):
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern, severity, message in self.DANGEROUS_IMPORTS:
                match = re.search(pattern, line)
                if match:
                    report.findings.append(SecurityFinding(
                        severity=severity,
                        category=SecurityFinding.CATEGORY_DANGEROUS_IMPORT,
                        line=lineno,
                        column=match.start() + 1,
                        message=message,
                        snippet=stripped[:120],
                    ))
                    break

    # ── Scanner: Prompt injection in comments ────────────────────────────

    def _scan_prompt_injection(self, lines: List[str], report: AuditReport):
        comment_re = re.compile(r"#(.*)")
        for lineno, line in enumerate(lines, 1):
            m = comment_re.search(line)
            if not m:
                continue
            comment_text = m.group(1).lower()
            for keyword in self.PROMPT_INJECTION_KEYWORDS:
                if keyword in comment_text:
                    col = line.index("#") + 1
                    report.findings.append(SecurityFinding(
                        severity="HIGH",
                        category=SecurityFinding.CATEGORY_PROMPT_INJECTION,
                        line=lineno,
                        column=col,
                        message=(
                            f"Prompt Injection keyword '{keyword}' found in comment — "
                            "may attempt to manipulate AI assistant behaviour"
                        ),
                        snippet=line.strip()[:120],
                    ))
                    break  # one finding per comment line

    # ── Scanner: Logic bombs ─────────────────────────────────────────────

    def _scan_logic_bombs(self, lines: List[str], report: AuditReport):
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            code_part = re.sub(r"#.*$", "", line)
            for pattern, severity, message in self.LOGIC_BOMB_PATTERNS:
                match = re.search(pattern, code_part, re.IGNORECASE)
                if match:
                    report.findings.append(SecurityFinding(
                        severity=severity,
                        category=SecurityFinding.CATEGORY_LOGIC_BOMB,
                        line=lineno,
                        column=match.start() + 1,
                        message=message,
                        snippet=stripped[:120],
                    ))
                    break

    # ── Scanner: Infinite recursion heuristic ────────────────────────────

    def _scan_infinite_recursion(self, lines: List[str], report: AuditReport):
        """
        Heuristic: detect a function that calls itself without a visible
        if/return guard on the recursive call line.
        """
        i = 0
        while i < len(lines):
            line = lines[i]
            m = self._FUNC_DEF_RE.match(line)
            if m:
                func_name = m.group(1)
                # Collect function body lines
                body_start = i + 1
                body_lines = []
                j = body_start
                while j < len(lines):
                    bl = lines[j]
                    # Dedented back to top level → end of function
                    if bl.strip() and not bl.startswith(" ") and not bl.startswith("\t"):
                        break
                    body_lines.append((j + 1, bl))
                    j += 1

                # Check for recursive call
                has_guard   = False
                recursive_lineno = None
                recursive_snippet = None
                for (blineno, bline) in body_lines:
                    bstripped = bline.strip()
                    if bstripped.startswith("#"):
                        continue
                    if re.search(rf"\b{re.escape(func_name)}\s*\(", bline):
                        recursive_lineno  = blineno
                        recursive_snippet = bstripped
                    if re.match(r"\s*if\b", bline) or re.match(r"\s*return\b", bline):
                        has_guard = True

                if recursive_lineno and not has_guard:
                    report.findings.append(SecurityFinding(
                        severity="MEDIUM",
                        category=SecurityFinding.CATEGORY_INFINITE_RECURSION,
                        line=recursive_lineno,
                        column=1,
                        message=(
                            f"Function '{func_name}' calls itself recursively with no "
                            "visible base-case guard — possible infinite recursion / stack overflow"
                        ),
                        snippet=(recursive_snippet or "")[:120],
                    ))
                i = j
            else:
                i += 1


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def audit_source(source_code: str) -> AuditReport:
    """
    Convenience wrapper: run a full security audit and return the report.

    Args:
        source_code: Mini-Python source code

    Returns:
        AuditReport
    """
    return SecurityAuditor().audit(source_code)

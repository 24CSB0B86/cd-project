"""
Security Agent — Week 11
Gemini-powered wrapper around the SAST SecurityAuditor engine.

Provides AI-enhanced explanations of security findings and can suggest
safe rewrites of dangerous code patterns.

Falls back gracefully to SAST-only mode if no API key is configured.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SecurityAgent:
    """
    AI-powered Security Risk Auditing Agent.

    Workflow:
      1. Run the pure-Python SecurityAuditor (always, no API needed)
      2. If Gemini API is available, send findings to AI for deep explanation
      3. Return a rich, structured audit result

    Usage:
        agent = SecurityAgent()
        report_text = agent.audit_with_ai(source_code)
    """

    SECURITY_SYSTEM_PROMPT = """\
You are a Security Risk Auditing Agent integrated into a Mini-Python compiler.
Your role is to analyse Static Application Security Testing (SAST) findings
and explain them clearly to a student developer.

RULES:
1. For each finding, explain WHY it is dangerous (use concrete attack scenarios).
2. Show a SAFE rewrite of the flagged code in a code block.
3. Reference the OWASP Top 10 for LLM or standard Python security best practices.
4. Be educational and encouraging — your goal is to teach, not alarm.
5. Prioritise CRITICAL findings first.
"""

    def __init__(self):
        """Initialise the security agent, attempting Gemini connection."""
        self._gemini_ready = False
        self._gemini_agent = None

        try:
            from .gemini_client import GeminiCompilerAgent
            import os
            if os.getenv("GEMINI_API_KEY", "").strip():
                self._gemini_agent = GeminiCompilerAgent()
                self._gemini_ready = self._gemini_agent.is_ready
        except Exception as e:
            logger.warning(f"SecurityAgent: Gemini not available ({e})")

    @property
    def has_ai(self) -> bool:
        """True if the Gemini API is available for deep analysis."""
        return self._gemini_ready

    # =========================================================================
    # Main Public Method
    # =========================================================================

    def audit_with_ai(self, source_code: str) -> str:
        """
        Run SAST scan, then optionally enhance findings with AI explanation.

        Args:
            source_code: Mini-Python source code to audit

        Returns:
            Human-readable security report string
        """
        from .security_auditor import SecurityAuditor
        auditor = SecurityAuditor()
        report = auditor.audit(source_code)

        # Always produce the SAST report
        sast_text = report.to_text()

        if not report.findings:
            return sast_text

        if not self._gemini_ready or self._gemini_agent is None:
            return sast_text + (
                "\n\n[AI Analysis] Gemini API not configured. "
                "Set GEMINI_API_KEY in .env for deep AI explanations.\n"
            )

        # Build AI prompt from findings
        findings_summary = "\n".join(
            f"  [{i}] {f.severity} — {f.category} at line {f.line}: {f.message}"
            for i, f in enumerate(report.findings, 1)
        )

        prompt = f"""\
The following Mini-Python code was scanned by our SAST engine and these
security findings were detected. Please provide deep explanations and safe fixes.

SOURCE CODE:
```python
{source_code}
```

SAST FINDINGS:
{findings_summary}

Please:
1. Explain each finding with a real-world attack scenario.
2. Show a safe rewrite for each finding.
3. Give a one-paragraph security assessment overall.
"""
        try:
            ai_text = self._gemini_agent._safe_send(prompt)
            return sast_text + "\n\n" + "=" * 60 + "\n  AI SECURITY ANALYSIS\n" + "=" * 60 + "\n" + ai_text
        except Exception as e:
            logger.error(f"SecurityAgent AI call failed: {e}")
            return sast_text + f"\n\n[AI Analysis Error] {e}\n"

    # =========================================================================
    # Suggest Safe Fix (single finding)
    # =========================================================================

    def generate_safe_fix(self, source_code: str, finding_index: int = 0) -> str:
        """
        Ask Gemini to rewrite the flagged snippet without the dangerous pattern.

        Args:
            source_code:   The Mini-Python source code
            finding_index: Which finding to fix (0-indexed)

        Returns:
            Suggested safe rewrite string, or SAST fallback if no API.
        """
        from .security_auditor import SecurityAuditor
        report = SecurityAuditor().audit(source_code)

        if not report.findings:
            return "No security findings — code is already safe."

        if finding_index >= len(report.findings):
            finding_index = 0

        f = report.findings[finding_index]

        if not self._gemini_ready or self._gemini_agent is None:
            return (
                f"[SAST Finding] {f.severity} — {f.category}\n"
                f"Line {f.line}: {f.message}\n"
                f"Snippet: {f.snippet}\n\n"
                "[AI fix not available — set GEMINI_API_KEY for suggestions]"
            )

        prompt = f"""\
The following Mini-Python code contains a security vulnerability:

FINDING: [{f.severity}] {f.category}
Location: Line {f.line}
Issue: {f.message}
Offending code: {f.snippet}

FULL SOURCE:
```python
{source_code}
```

Please rewrite ONLY the dangerous line/section with a safe equivalent.
Show the before and after in code blocks and explain the change.
"""
        try:
            return self._gemini_agent._safe_send(prompt)
        except Exception as e:
            return f"[API Error] {e}"

    # =========================================================================
    # Convenience: SAST-only (no API)
    # =========================================================================

    @staticmethod
    def quick_audit(source_code: str) -> str:
        """
        Fast SAST-only audit (no Gemini API).

        Args:
            source_code: Mini-Python code to check

        Returns:
            Report text string
        """
        from .security_auditor import SecurityAuditor
        return SecurityAuditor().audit(source_code).to_text()

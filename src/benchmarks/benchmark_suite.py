"""
Benchmark Suite — Week 12
==========================
Measures end-to-end pipeline latency (per stage) and memory footprint
for the Project 83 compiler + AI assistant.

All benchmarks are API-free and fully deterministic.

Usage:
    suite = BenchmarkSuite(source_code)
    results = suite.run_all()
    suite.print_report(results)
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """Timing and memory statistics for a single pipeline stage."""
    stage: str
    mean_ms: float
    min_ms: float
    max_ms: float
    peak_kb: float
    iterations: int

    def __str__(self) -> str:
        return (
            f"  {self.stage:<30} "
            f"mean={self.mean_ms:6.3f}ms  "
            f"min={self.min_ms:6.3f}ms  "
            f"max={self.max_ms:6.3f}ms  "
            f"peak={self.peak_kb:.1f}KB  "
            f"(n={self.iterations})"
        )


# ---------------------------------------------------------------------------
# BenchmarkSuite
# ---------------------------------------------------------------------------

class BenchmarkSuite:
    """
    Benchmarks each stage of the Mini-Python compiler pipeline.

    Args:
        source_code : Mini-Python source to benchmark against.
        iterations  : Number of timing repetitions (default: 100).
    """

    def __init__(self, source_code: str, iterations: int = 100):
        self.source = source_code
        self.iterations = iterations
        self._results: List[BenchmarkResult] = []

    # ------------------------------------------------------------------
    # Core timing primitive
    # ------------------------------------------------------------------

    def time_stage(
        self, stage_name: str, fn: Callable, iterations: Optional[int] = None
    ) -> BenchmarkResult:
        """
        Time *fn* for *iterations* runs and record peak memory.

        Args:
            stage_name : Human-readable label.
            fn         : Zero-argument callable to benchmark.
            iterations : Override default iteration count.

        Returns:
            BenchmarkResult with mean/min/max ms and peak KB.
        """
        n = iterations if iterations is not None else self.iterations
        times_ms: List[float] = []

        # Warm-up
        try:
            fn()
        except Exception:
            pass

        tracemalloc.start()
        for _ in range(n):
            t0 = time.perf_counter()
            try:
                fn()
            except Exception:
                pass
            times_ms.append((time.perf_counter() - t0) * 1000)
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return BenchmarkResult(
            stage=stage_name,
            mean_ms=sum(times_ms) / len(times_ms),
            min_ms=min(times_ms),
            max_ms=max(times_ms),
            peak_kb=peak_bytes / 1024,
            iterations=n,
        )

    # ------------------------------------------------------------------
    # Individual stage benchmarks
    # ------------------------------------------------------------------

    def benchmark_lexer(self) -> BenchmarkResult:
        """Benchmark the Lexer tokenization stage."""
        from src.compiler.lexer import Lexer

        def _run():
            Lexer(self.source).tokenize()

        return self.time_stage("Lexer.tokenize()", _run)

    def benchmark_parser(self) -> BenchmarkResult:
        """Benchmark the Parser AST construction stage."""
        from src.compiler.lexer import Lexer
        from src.compiler.parser import Parser

        # Pre-compute tokens so we benchmark parser only
        tokens = Lexer(self.source).tokenize()

        def _run():
            Parser(list(tokens)).parse()

        return self.time_stage("Parser.parse()", _run)

    def benchmark_semantic(self) -> BenchmarkResult:
        """Benchmark the Semantic Analyzer stage."""
        from src.compiler.lexer import Lexer
        from src.compiler.parser import Parser
        from src.compiler.semantic_analyzer import SemanticAnalyzer

        tokens = Lexer(self.source).tokenize()
        ast = Parser(list(tokens)).parse()

        def _run():
            SemanticAnalyzer().analyze(ast)

        return self.time_stage("SemanticAnalyzer.analyze()", _run)

    def benchmark_context_provider(self) -> BenchmarkResult:
        """Benchmark the ContextProvider serialization stage."""
        from src.compiler.lexer import Lexer
        from src.compiler.parser import Parser
        from src.compiler.semantic_analyzer import SemanticAnalyzer
        from src.orchestrator.context_provider import ContextProvider

        tokens = Lexer(self.source).tokenize()
        ast = Parser(list(tokens)).parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        def _run():
            ContextProvider.build_context(ast, analyzer.symbol_table, analyzer.errors)

        return self.time_stage("ContextProvider.build_context()", _run)

    def benchmark_sast(self) -> BenchmarkResult:
        """Benchmark the SAST security auditor."""
        from src.orchestrator.security_auditor import SecurityAuditor

        auditor = SecurityAuditor()

        def _run():
            auditor.audit(self.source)

        return self.time_stage("SecurityAuditor.audit()", _run)

    def benchmark_full_pipeline(self) -> BenchmarkResult:
        """Benchmark the complete front-end pipeline (no AI)."""
        from src.orchestrator.compiler_tools import CompilerToolbox

        def _run():
            CompilerToolbox.from_source(self.source)

        return self.time_stage("Full pipeline (no AI)", _run)

    # ------------------------------------------------------------------
    # Run all
    # ------------------------------------------------------------------

    def run_all(self) -> List[BenchmarkResult]:
        """
        Run all stage benchmarks in order and return results.

        Returns:
            List of BenchmarkResult objects.
        """
        benchmarks = [
            self.benchmark_lexer,
            self.benchmark_parser,
            self.benchmark_semantic,
            self.benchmark_context_provider,
            self.benchmark_sast,
            self.benchmark_full_pipeline,
        ]
        self._results = []
        for fn in benchmarks:
            try:
                result = fn()
                self._results.append(result)
            except Exception as exc:
                # Create a placeholder so the suite always returns a full list
                self._results.append(BenchmarkResult(
                    stage=fn.__name__,
                    mean_ms=-1.0, min_ms=-1.0, max_ms=-1.0,
                    peak_kb=-1.0, iterations=0,
                ))
        return self._results

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    @staticmethod
    def print_report(results: List[BenchmarkResult]) -> None:
        """Print a formatted benchmark report to stdout."""
        print("=" * 72)
        print("  Project 83 — Pipeline Benchmark Report")
        print("=" * 72)
        for r in results:
            if r.mean_ms < 0:
                print(f"  {r.stage:<30} ERROR (stage failed)")
            else:
                print(str(r))
        total = sum(r.mean_ms for r in results if r.mean_ms >= 0)
        print("-" * 72)
        print(f"  {'Total (no AI):':<30} {total:6.3f}ms (mean)")
        print("=" * 72)

    def summary_dict(self, results: Optional[List[BenchmarkResult]] = None) -> Dict[str, float]:
        """Return a simple {stage: mean_ms} dictionary."""
        res = results or self._results
        return {r.stage: r.mean_ms for r in res}


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def run_pipeline_benchmark(source_code: str, iterations: int = 100) -> List[BenchmarkResult]:
    """
    Run the full benchmark suite on *source_code*.

    Args:
        source_code : Mini-Python source code string.
        iterations  : Timing repetitions per stage.

    Returns:
        List of :class:`BenchmarkResult`.
    """
    suite = BenchmarkSuite(source_code, iterations=iterations)
    results = suite.run_all()
    BenchmarkSuite.print_report(results)
    return results

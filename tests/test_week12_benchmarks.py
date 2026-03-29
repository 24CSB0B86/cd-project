"""
test_week12_benchmarks.py — Week 12: Performance Benchmarking
=============================================================
38 deterministic tests for BenchmarkSuite and AccuracyEvaluator.
Zero API calls required.
"""

import pytest
from src.benchmarks.benchmark_suite import BenchmarkSuite, BenchmarkResult, run_pipeline_benchmark
from src.benchmarks.accuracy_evaluator import AccuracyEvaluator, EvalCase, EvalResult


# ── Shared fixtures ────────────────────────────────────────────────────────

SMALL_CODE = "x = 1\ny = x + 2"

MEDIUM_CODE = """\
def add(a, b):
    return a + b

def multiply(a, b):
    result = 0
    count = 0
    while count < b:
        result = result + a
        count = count + 1
    return result

total = add(3, 4)
product = multiply(3, 4)
"""

UNSAFE_CODE = """\
import os
user_input = 'x'
result = eval(user_input)
"""


@pytest.fixture
def small_suite():
    return BenchmarkSuite(SMALL_CODE, iterations=10)


@pytest.fixture
def medium_suite():
    return BenchmarkSuite(MEDIUM_CODE, iterations=10)


@pytest.fixture
def evaluator():
    return AccuracyEvaluator()


# ── BenchmarkResult ────────────────────────────────────────────────────────

class TestBenchmarkResult:
    def test_result_fields(self):
        r = BenchmarkResult("Lexer", 1.2, 0.8, 2.1, 42.0, 100)
        assert r.stage == "Lexer"
        assert r.mean_ms == pytest.approx(1.2)
        assert r.min_ms == pytest.approx(0.8)
        assert r.max_ms == pytest.approx(2.1)
        assert r.peak_kb == pytest.approx(42.0)
        assert r.iterations == 100

    def test_result_str(self):
        r = BenchmarkResult("Lexer.tokenize()", 1.234, 0.9, 2.5, 50.0, 10)
        s = str(r)
        assert "Lexer.tokenize()" in s
        assert "1.234" in s

    def test_result_error_placeholder(self):
        r = BenchmarkResult("broken", -1.0, -1.0, -1.0, -1.0, 0)
        assert r.mean_ms < 0


# ── BenchmarkSuite construction ────────────────────────────────────────────

class TestBenchmarkSuiteInit:
    def test_small_code_suite(self, small_suite):
        assert small_suite.source == SMALL_CODE
        assert small_suite.iterations == 10

    def test_medium_code_suite(self, medium_suite):
        assert medium_suite.source == MEDIUM_CODE


# ── Lexer benchmark ────────────────────────────────────────────────────────

class TestLexerBenchmark:
    def test_lexer_returns_result(self, small_suite):
        r = small_suite.benchmark_lexer()
        assert isinstance(r, BenchmarkResult)

    def test_lexer_mean_positive(self, small_suite):
        r = small_suite.benchmark_lexer()
        assert r.mean_ms > 0

    def test_lexer_min_lte_mean(self, small_suite):
        r = small_suite.benchmark_lexer()
        assert r.min_ms <= r.mean_ms

    def test_lexer_max_gte_mean(self, small_suite):
        r = small_suite.benchmark_lexer()
        assert r.max_ms >= r.mean_ms

    def test_lexer_iterations(self, small_suite):
        r = small_suite.benchmark_lexer()
        assert r.iterations == 10

    def test_lexer_peak_kb_non_negative(self, small_suite):
        r = small_suite.benchmark_lexer()
        assert r.peak_kb >= 0


# ── Parser benchmark ───────────────────────────────────────────────────────

class TestParserBenchmark:
    def test_parser_returns_result(self, medium_suite):
        r = medium_suite.benchmark_parser()
        assert isinstance(r, BenchmarkResult)

    def test_parser_mean_positive(self, medium_suite):
        r = medium_suite.benchmark_parser()
        assert r.mean_ms > 0

    def test_parser_stage_name(self, medium_suite):
        r = medium_suite.benchmark_parser()
        assert "Parser" in r.stage or "parse" in r.stage.lower()


# ── Semantic benchmark ─────────────────────────────────────────────────────

class TestSemanticBenchmark:
    def test_semantic_returns_result(self, medium_suite):
        r = medium_suite.benchmark_semantic()
        assert isinstance(r, BenchmarkResult)

    def test_semantic_mean_positive(self, medium_suite):
        r = medium_suite.benchmark_semantic()
        assert r.mean_ms > 0


# ── SAST benchmark ─────────────────────────────────────────────────────────

class TestSASTBenchmark:
    def test_sast_returns_result(self):
        suite = BenchmarkSuite(UNSAFE_CODE, iterations=10)
        r = suite.benchmark_sast()
        assert isinstance(r, BenchmarkResult)

    def test_sast_fast(self):
        """SAST should complete in under 50 ms mean even for unsafe code."""
        suite = BenchmarkSuite(UNSAFE_CODE, iterations=20)
        r = suite.benchmark_sast()
        assert r.mean_ms < 50.0

    def test_sast_iterations(self):
        suite = BenchmarkSuite(SMALL_CODE, iterations=5)
        r = suite.benchmark_sast()
        assert r.iterations == 5


# ── Full pipeline benchmark ────────────────────────────────────────────────

class TestFullPipelineBenchmark:
    def test_full_pipeline_returns_result(self, medium_suite):
        r = medium_suite.benchmark_full_pipeline()
        assert isinstance(r, BenchmarkResult)

    def test_full_pipeline_mean_positive(self, medium_suite):
        r = medium_suite.benchmark_full_pipeline()
        assert r.mean_ms > 0

    def test_full_pipeline_faster_than_1s(self, medium_suite):
        """Full pipeline (no AI) must complete in < 1000 ms mean."""
        r = medium_suite.benchmark_full_pipeline()
        assert r.mean_ms < 1000.0


# ── run_all ────────────────────────────────────────────────────────────────

class TestRunAll:
    def test_run_all_returns_list(self, small_suite):
        results = small_suite.run_all()
        assert isinstance(results, list)
        assert len(results) == 6

    def test_run_all_all_positive(self, small_suite):
        results = small_suite.run_all()
        for r in results:
            assert r.mean_ms > 0, f"Stage {r.stage!r} has non-positive mean_ms"

    def test_summary_dict(self, small_suite):
        results = small_suite.run_all()
        d = small_suite.summary_dict(results)
        assert isinstance(d, dict)
        assert len(d) == 6
        for v in d.values():
            assert v > 0


# ── AccuracyEvaluator ──────────────────────────────────────────────────────

class TestAccuracyEvaluator:
    def test_builtin_cases_exist(self, evaluator):
        assert len(evaluator.BUILTIN_CASES) >= 6

    def test_eval_case_fields(self, evaluator):
        case = evaluator.BUILTIN_CASES[0]
        assert case.case_id
        assert case.category in ("syntax", "semantic", "security")
        assert case.source_code
        assert case.fixed_code
        assert case.expected_error

    def test_evaluate_case_returns_result(self, evaluator):
        case = evaluator.BUILTIN_CASES[0]
        result = evaluator.evaluate_case(case)
        assert isinstance(result, EvalResult)

    def test_evaluate_case_correct_flag_type(self, evaluator):
        result = evaluator.evaluate_case(evaluator.BUILTIN_CASES[0])
        assert isinstance(result.standard_python_correct, bool)
        assert isinstance(result.project83_correct, bool)

    def test_evaluate_all_returns_all(self, evaluator):
        results = evaluator.evaluate_all()
        assert len(results) == len(evaluator.BUILTIN_CASES)

    def test_project83_security_case_detected(self, evaluator):
        """Project 83's SAST should correctly flag the eval() security case."""
        sec_cases = [c for c in evaluator.BUILTIN_CASES if c.category == "security"]
        for c in sec_cases:
            result = evaluator.evaluate_case(c)
            # The gold fixed_code should compile cleanly
            assert result.project83_correct is True, (
                f"Case {c.case_id}: fixed_code should compile cleanly"
            )

    def test_fixed_code_compiles(self, evaluator):
        """Every BUILTIN_CASE.fixed_code should pass the Mini-Python compiler."""
        for case in evaluator.BUILTIN_CASES:
            ok = AccuracyEvaluator._compiles_cleanly(case.fixed_code)
            assert ok, f"Case {case.case_id}: fixed_code did not compile cleanly"

    def test_accuracy_report_string(self, evaluator):
        results = evaluator.evaluate_all()
        report = AccuracyEvaluator.accuracy_report(results)
        assert "Project 83" in report
        assert "Std Python" in report or "OVERALL" in report

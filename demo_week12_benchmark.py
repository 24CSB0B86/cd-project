"""
demo_week12_benchmark.py — Week 12: Performance Benchmarking Demo
==================================================================
Runs the full benchmark suite and accuracy evaluator on representative
Mini-Python programs from small to large.

Usage:
    python demo_week12_benchmark.py
"""

from src.benchmarks.benchmark_suite import BenchmarkSuite, run_pipeline_benchmark
from src.benchmarks.accuracy_evaluator import AccuracyEvaluator

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

LARGE_CODE = """\
def factorial(n):
    if n < 2:
        return 1
    return n

def fibonacci(n):
    if n < 2:
        return n
    a = 0
    b = 1
    count = 2
    while count < n:
        temp = a + b
        a = b
        b = temp
        count = count + 1
    return b

def is_prime(n):
    if n < 2:
        return 0
    divisor = 2
    while divisor < n:
        if n == divisor:
            return 0
        divisor = divisor + 1
    return 1

result1 = factorial(10)
result2 = fibonacci(20)
result3 = is_prime(17)
"""

SIZES = [("Small", SMALL_CODE), ("Medium", MEDIUM_CODE), ("Large", LARGE_CODE)]


def main():
    print("\n" + "=" * 70)
    print("  Project 83 — Week 12: Performance Benchmarking Demo")
    print("=" * 70)

    # ── Stage latency benchmarks per size ─────────────────────────────────
    for label, code in SIZES:
        print(f"\n{'─'*70}")
        print(f"  [{label}] {len(code.splitlines())} lines, {len(code)} chars")
        print(f"{'─'*70}")
        suite = BenchmarkSuite(code, iterations=50)
        results = suite.run_all()
        BenchmarkSuite.print_report(results)

    # ── Accuracy evaluation ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  Diagnostic Accuracy Comparison")
    print("=" * 70)
    evaluator = AccuracyEvaluator()
    results = evaluator.evaluate_all()
    print(AccuracyEvaluator.accuracy_report(results))

    print("\nDetailed case results:")
    for r in results:
        std = "✅" if r.standard_python_correct else "❌"
        p83 = "✅" if r.project83_correct else "❌"
        print(f"  [{r.case.case_id}] {r.case.description}")
        print(f"         Standard Python: {std}   Project 83: {p83}")

    print("\n✅ Week 12 benchmark demo complete.")


if __name__ == "__main__":
    main()

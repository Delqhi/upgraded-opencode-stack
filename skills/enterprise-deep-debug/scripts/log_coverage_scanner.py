#!/usr/bin/env python3
"""Scans a codebase and grades its logging coverage like a professor grading a thesis.

Produces a per-file and per-function report showing:
- Functions with ZERO log statements (grade F)
- Functions with entry-only logging (grade D)
- Functions with entry+exit logging (grade C)
- Functions with entry+exit+error logging (grade B)
- Functions with entry+exit+error+args+return logging (grade A)
- Functions with timing + correlation IDs (grade A+)

Usage:
    python3 log_coverage_scanner.py <path> [--format json|table|markdown] [--min-grade C] [--fail-under 60]
"""

import ast
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

GRADE_WEIGHTS = {"F": 0, "D": 25, "C": 50, "B": 75, "A": 90, "A+": 100}
LOG_PATTERNS = {
    "entry": ["enter", "start", "begin", "called", "invoked", ">>"],
    "exit": ["exit", "end", "finish", "return", "complete", "<<", "elapsed"],
    "error": ["error", "exception", "fail", "traceback", "exc_info", "stack"],
    "args": ["args=", "kwargs=", "param", "input", "request"],
    "return_val": ["return=", "result=", "output=", "response=", "ret="],
    "timing": ["elapsed", "duration", "perf_counter", "time.time", "timer", "took"],
    "correlation": ["correlation", "trace_id", "span_id", "request_id", "x-request"],
}


@dataclass
class FunctionCoverage:
    name: str
    file: str
    lineno: int
    end_lineno: int
    total_lines: int
    log_statements: int
    has_entry: bool = False
    has_exit: bool = False
    has_error: bool = False
    has_args: bool = False
    has_return_val: bool = False
    has_timing: bool = False
    has_correlation: bool = False
    grade: str = "F"
    score: int = 0


@dataclass
class FileCoverage:
    path: str
    total_functions: int = 0
    graded_functions: List[FunctionCoverage] = field(default_factory=list)
    average_score: float = 0.0
    grade: str = "F"


class LogCoverageAnalyzer(ast.NodeVisitor):
    def __init__(self, source_lines: List[str], filepath: str):
        self.source_lines = source_lines
        self.filepath = filepath
        self.functions: List[FunctionCoverage] = []

    def _extract_log_calls(self, node: ast.FunctionDef) -> List[str]:
        log_lines = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_str = ""
                if isinstance(child.func, ast.Attribute):
                    attr = child.func.attr
                    if attr in (
                        "debug",
                        "info",
                        "warning",
                        "error",
                        "critical",
                        "exception",
                        "log",
                    ):
                        start = child.lineno - 1
                        end = getattr(child, "end_lineno", child.lineno)
                        call_str = " ".join(self.source_lines[start:end]).lower()
                        log_lines.append(call_str)
                elif isinstance(child.func, ast.Name):
                    if child.func.id == "print":
                        start = child.lineno - 1
                        end = getattr(child, "end_lineno", child.lineno)
                        call_str = " ".join(self.source_lines[start:end]).lower()
                        log_lines.append(call_str)
        return log_lines

    def _check_patterns(self, log_lines: List[str], category: str) -> bool:
        patterns = LOG_PATTERNS.get(category, [])
        for line in log_lines:
            for pattern in patterns:
                if pattern in line:
                    return True
        return False

    def _grade_function(self, fc: FunctionCoverage) -> None:
        if fc.log_statements == 0:
            fc.grade = "F"
            fc.score = 0
            return

        score = 0
        if fc.has_entry:
            score += 20
        if fc.has_exit:
            score += 20
        if fc.has_error:
            score += 20
        if fc.has_args:
            score += 15
        if fc.has_return_val:
            score += 10
        if fc.has_timing:
            score += 10
        if fc.has_correlation:
            score += 5

        fc.score = min(score, 100)

        if score >= 95:
            fc.grade = "A+"
        elif score >= 80:
            fc.grade = "A"
        elif score >= 60:
            fc.grade = "B"
        elif score >= 40:
            fc.grade = "C"
        elif score >= 20:
            fc.grade = "D"
        else:
            fc.grade = "F"

    def _analyze_function(self, node: ast.FunctionDef):
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            return
        if (
            len(node.body) == 1
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            return

        log_lines = self._extract_log_calls(node)
        end_lineno = getattr(node, "end_lineno", node.lineno)

        fc = FunctionCoverage(
            name=node.name,
            file=self.filepath,
            lineno=node.lineno,
            end_lineno=end_lineno,
            total_lines=end_lineno - node.lineno,
            log_statements=len(log_lines),
            has_entry=self._check_patterns(log_lines, "entry"),
            has_exit=self._check_patterns(log_lines, "exit"),
            has_error=self._check_patterns(log_lines, "error"),
            has_args=self._check_patterns(log_lines, "args"),
            has_return_val=self._check_patterns(log_lines, "return_val"),
            has_timing=self._check_patterns(log_lines, "timing"),
            has_correlation=self._check_patterns(log_lines, "correlation"),
        )
        self._grade_function(fc)
        self.functions.append(fc)

    def visit_FunctionDef(self, node):
        self._analyze_function(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


def scan_file(filepath: Path) -> Optional[FileCoverage]:
    try:
        source = filepath.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        return None

    analyzer = LogCoverageAnalyzer(source_lines, str(filepath))
    analyzer.visit(tree)

    if not analyzer.functions:
        return None

    fc = FileCoverage(
        path=str(filepath),
        total_functions=len(analyzer.functions),
        graded_functions=analyzer.functions,
    )

    if analyzer.functions:
        fc.average_score = sum(f.score for f in analyzer.functions) / len(
            analyzer.functions
        )
        if fc.average_score >= 90:
            fc.grade = "A"
        elif fc.average_score >= 75:
            fc.grade = "B"
        elif fc.average_score >= 50:
            fc.grade = "C"
        elif fc.average_score >= 25:
            fc.grade = "D"
        else:
            fc.grade = "F"

    return fc


def format_table(results: List[FileCoverage], show_functions: bool = True) -> str:
    lines = []
    lines.append(f"{'FILE':<60} {'FUNCS':>5} {'AVG':>5} {'GRADE':>5}")
    lines.append("-" * 80)

    total_funcs = 0
    total_score = 0.0
    grade_counts = {"F": 0, "D": 0, "C": 0, "B": 0, "A": 0, "A+": 0}

    for fc in sorted(results, key=lambda x: x.average_score):
        lines.append(
            f"{fc.path:<60} {fc.total_functions:>5} {fc.average_score:>5.0f} {fc.grade:>5}"
        )
        total_funcs += fc.total_functions
        total_score += fc.average_score * fc.total_functions

        if show_functions:
            for func in sorted(fc.graded_functions, key=lambda f: f.score):
                flags = ""
                flags += "E" if func.has_entry else "."
                flags += "X" if func.has_exit else "."
                flags += "R" if func.has_error else "."
                flags += "A" if func.has_args else "."
                flags += "V" if func.has_return_val else "."
                flags += "T" if func.has_timing else "."
                flags += "C" if func.has_correlation else "."
                lines.append(
                    f"  L{func.lineno:<5} {func.name:<50} [{flags}] {func.grade:>3} ({func.score})"
                )
                grade_counts[func.grade] = grade_counts.get(func.grade, 0) + 1

    overall = total_score / total_funcs if total_funcs else 0

    lines.append("")
    lines.append("=" * 80)
    lines.append(
        f"TOTAL: {len(results)} files, {total_funcs} functions, overall score: {overall:.1f}/100"
    )
    lines.append(
        f"Grade distribution: "
        + " | ".join(f"{g}:{c}" for g, c in sorted(grade_counts.items()))
    )
    lines.append(
        f"Legend: E=Entry X=Exit R=Error A=Args V=ReturnVal T=Timing C=Correlation"
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Grade logging coverage of a Python codebase"
    )
    parser.add_argument("path", help="Python file or directory")
    parser.add_argument(
        "--format", choices=["json", "table", "markdown"], default="table"
    )
    parser.add_argument(
        "--min-grade", default="F", help="Only show functions at or below this grade"
    )
    parser.add_argument(
        "--fail-under", type=float, default=0, help="Exit 1 if overall score < this"
    )
    parser.add_argument(
        "--no-functions", action="store_true", help="Hide per-function details"
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path} does not exist", file=sys.stderr)
        sys.exit(1)

    py_files = []
    if path.is_file():
        py_files = [path]
    else:
        py_files = sorted(path.rglob("*.py"))
        py_files = [
            f
            for f in py_files
            if not any(
                skip in str(f)
                for skip in [
                    "node_modules",
                    ".venv",
                    "__pycache__",
                    "dist/",
                    ".git/",
                    "migrations/",
                ]
            )
        ]

    results = []
    for pf in py_files:
        fc = scan_file(pf)
        if fc:
            min_grade_threshold = GRADE_WEIGHTS.get(args.min_grade, 0)
            if args.min_grade != "F":
                fc.graded_functions = [
                    f for f in fc.graded_functions if f.score <= min_grade_threshold
                ]
            if fc.graded_functions or args.min_grade == "F":
                results.append(fc)

    if args.format == "json":
        print(json.dumps([asdict(r) for r in results], indent=2))
    elif args.format == "markdown":
        print("# Log Coverage Report\n")
        print(format_table(results, not args.no_functions))
    else:
        print(format_table(results, not args.no_functions))

    total_funcs = sum(r.total_functions for r in results)
    total_score = sum(r.average_score * r.total_functions for r in results)
    overall = total_score / total_funcs if total_funcs else 0

    if overall < args.fail_under:
        print(
            f"\nFAIL: Overall score {overall:.1f} < threshold {args.fail_under}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

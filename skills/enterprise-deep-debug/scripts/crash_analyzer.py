#!/usr/bin/env python3
"""Automated crash dump and traceback analysis.

Parses Python tracebacks, log files, and crash dumps. Extracts:
- Full call chain with file:line references
- Exception type and message
- Local variable context (if available in enhanced tracebacks)
- Recurring crash patterns (same exception at same location)
- Timeline of crashes from log files
- Suggested root cause based on exception taxonomy

Usage:
    python3 crash_analyzer.py <logfile_or_traceback> [--format json|report] [--correlate <dir>]
    python3 crash_analyzer.py /tmp/local_fast_runner8.log --format report
    python3 crash_analyzer.py --stdin < traceback.txt
    echo "Traceback ..." | python3 crash_analyzer.py --stdin
"""

import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime

TB_START_RE = re.compile(r"^Traceback \(most recent call last\):")
TB_FILE_RE = re.compile(r'^\s+File "(.+?)", line (\d+), in (.+?)$')
TB_CODE_RE = re.compile(r"^\s+\S")
TB_EXC_RE = re.compile(
    r"^(\w+(?:\.\w+)*(?:Error|Exception|Warning|Fault|Exit|Interrupt|Timeout)\w*):?\s*(.*)"
)
TB_EXC_BARE_RE = re.compile(r"^(\w+(?:\.\w+)*)\s*$")
TIMESTAMP_PATTERNS = [
    re.compile(r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]"),
    re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)"),
    re.compile(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"),
]

EXCEPTION_TAXONOMY = {
    "KeyError": {
        "category": "data",
        "common_cause": "Missing key in dictionary",
        "severity": "medium",
    },
    "IndexError": {
        "category": "data",
        "common_cause": "List index out of bounds",
        "severity": "medium",
    },
    "TypeError": {
        "category": "contract",
        "common_cause": "Wrong argument type or None propagation",
        "severity": "high",
    },
    "AttributeError": {
        "category": "contract",
        "common_cause": "Accessing attribute on None or wrong type",
        "severity": "high",
    },
    "ValueError": {
        "category": "data",
        "common_cause": "Invalid value for operation",
        "severity": "medium",
    },
    "FileNotFoundError": {
        "category": "environment",
        "common_cause": "Missing file or wrong path",
        "severity": "high",
    },
    "PermissionError": {
        "category": "environment",
        "common_cause": "Insufficient file/resource permissions",
        "severity": "high",
    },
    "ConnectionError": {
        "category": "network",
        "common_cause": "Network connectivity or service down",
        "severity": "critical",
    },
    "TimeoutError": {
        "category": "resource",
        "common_cause": "Operation exceeded time limit",
        "severity": "high",
    },
    "MemoryError": {
        "category": "resource",
        "common_cause": "Out of memory",
        "severity": "critical",
    },
    "ImportError": {
        "category": "dependency",
        "common_cause": "Missing module or circular import",
        "severity": "high",
    },
    "ModuleNotFoundError": {
        "category": "dependency",
        "common_cause": "Package not installed",
        "severity": "high",
    },
    "RuntimeError": {
        "category": "logic",
        "common_cause": "Invalid runtime state",
        "severity": "high",
    },
    "AssertionError": {
        "category": "logic",
        "common_cause": "Failed assertion / test failure",
        "severity": "medium",
    },
    "StopIteration": {
        "category": "logic",
        "common_cause": "Iterator exhausted unexpectedly",
        "severity": "low",
    },
    "OSError": {
        "category": "environment",
        "common_cause": "OS-level error (disk, network, process)",
        "severity": "high",
    },
    "JSONDecodeError": {
        "category": "data",
        "common_cause": "Invalid JSON input",
        "severity": "medium",
    },
    "UnicodeDecodeError": {
        "category": "data",
        "common_cause": "Wrong encoding for text data",
        "severity": "medium",
    },
    "InvalidStateError": {
        "category": "async",
        "common_cause": "Asyncio state machine violation",
        "severity": "high",
    },
    "websockets.exceptions.InvalidStatus": {
        "category": "network",
        "common_cause": "WebSocket connection rejected",
        "severity": "high",
    },
}


@dataclass
class StackFrame:
    file: str
    line: int
    function: str
    code: str = ""


@dataclass
class CrashEvent:
    exception_type: str
    exception_message: str
    frames: List[StackFrame] = field(default_factory=list)
    timestamp: Optional[str] = None
    category: str = "unknown"
    severity: str = "unknown"
    common_cause: str = ""
    root_frame: Optional[StackFrame] = None
    context_lines: List[str] = field(default_factory=list)


def extract_timestamp(line: str) -> Optional[str]:
    for pat in TIMESTAMP_PATTERNS:
        m = pat.search(line)
        if m:
            return m.group(1)
    return None


def parse_tracebacks(text: str) -> List[CrashEvent]:
    lines = text.splitlines()
    crashes: List[CrashEvent] = []
    i = 0
    while i < len(lines):
        if TB_START_RE.match(lines[i]):
            ts = None
            for back in range(max(0, i - 5), i):
                ts = extract_timestamp(lines[back])
                if ts:
                    break

            frames: List[StackFrame] = []
            context: List[str] = [lines[i]]
            i += 1
            while i < len(lines):
                fm = TB_FILE_RE.match(lines[i])
                if fm:
                    frame = StackFrame(
                        file=fm.group(1), line=int(fm.group(2)), function=fm.group(3)
                    )
                    context.append(lines[i])
                    i += 1
                    if (
                        i < len(lines)
                        and TB_CODE_RE.match(lines[i])
                        and not TB_FILE_RE.match(lines[i])
                    ):
                        frame.code = lines[i].strip()
                        context.append(lines[i])
                        i += 1
                    frames.append(frame)
                else:
                    break

            exc_type = "UnknownException"
            exc_msg = ""
            if i < len(lines):
                em = TB_EXC_RE.match(lines[i])
                if em:
                    exc_type = em.group(1)
                    exc_msg = em.group(2).strip()
                    context.append(lines[i])
                    i += 1
                else:
                    bm = TB_EXC_BARE_RE.match(lines[i])
                    if bm:
                        exc_type = bm.group(1)
                        context.append(lines[i])
                        i += 1

            tax = EXCEPTION_TAXONOMY.get(exc_type.split(".")[-1], {})
            crash = CrashEvent(
                exception_type=exc_type,
                exception_message=exc_msg,
                frames=frames,
                timestamp=ts,
                category=tax.get("category", "unknown"),
                severity=tax.get("severity", "unknown"),
                common_cause=tax.get("common_cause", ""),
                root_frame=frames[-1] if frames else None,
                context_lines=context,
            )
            crashes.append(crash)
        else:
            i += 1

    return crashes


def find_crash_patterns(crashes: List[CrashEvent]) -> Dict:
    location_counts: Counter = Counter()
    type_counts: Counter = Counter()
    category_counts: Counter = Counter()

    for c in crashes:
        type_counts[c.exception_type] += 1
        category_counts[c.category] += 1
        if c.root_frame:
            loc = f"{c.root_frame.file}:{c.root_frame.line}:{c.root_frame.function}"
            location_counts[loc] += 1

    return {
        "total_crashes": len(crashes),
        "unique_exception_types": len(type_counts),
        "top_exception_types": type_counts.most_common(10),
        "top_crash_locations": location_counts.most_common(10),
        "category_breakdown": dict(category_counts),
        "recurring_crashes": [
            (loc, count) for loc, count in location_counts.items() if count > 1
        ],
    }


def correlate_with_source(crashes: List[CrashEvent], source_dir: Path) -> List[Dict]:
    correlations = []
    for crash in crashes:
        if not crash.root_frame:
            continue
        src_file = source_dir / crash.root_frame.file
        if not src_file.exists():
            for candidate in source_dir.rglob(Path(crash.root_frame.file).name):
                src_file = candidate
                break

        if src_file.exists():
            try:
                src_lines = src_file.read_text(encoding="utf-8").splitlines()
                line_idx = crash.root_frame.line - 1
                start = max(0, line_idx - 5)
                end = min(len(src_lines), line_idx + 6)
                context = {i + 1: src_lines[i] for i in range(start, end)}
                correlations.append(
                    {
                        "crash": crash.exception_type,
                        "file": str(src_file),
                        "line": crash.root_frame.line,
                        "function": crash.root_frame.function,
                        "source_context": context,
                        "has_logging": any(
                            "log" in l.lower() or "print(" in l
                            for l in context.values()
                        ),
                    }
                )
            except Exception:
                pass

    return correlations


def format_report(
    crashes: List[CrashEvent], patterns: Dict, correlations: List[Dict] = None
) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("CRASH ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append(f"Total crashes found: {patterns['total_crashes']}")
    lines.append(f"Unique exception types: {patterns['unique_exception_types']}")
    lines.append("")

    lines.append("--- TOP EXCEPTION TYPES ---")
    for exc_type, count in patterns["top_exception_types"]:
        tax = EXCEPTION_TAXONOMY.get(exc_type.split(".")[-1], {})
        lines.append(
            f"  {count:>3}x  {exc_type:<40} [{tax.get('category', '?'):>12}] {tax.get('severity', '?'):>8}"
        )

    lines.append("")
    lines.append("--- TOP CRASH LOCATIONS ---")
    for loc, count in patterns["top_crash_locations"]:
        lines.append(f"  {count:>3}x  {loc}")

    if patterns["recurring_crashes"]:
        lines.append("")
        lines.append("--- RECURRING CRASHES (potential systematic bugs) ---")
        for loc, count in patterns["recurring_crashes"]:
            lines.append(f"  {count:>3}x  {loc}")

    lines.append("")
    lines.append("--- CRASH TIMELINE ---")
    for i, crash in enumerate(crashes, 1):
        ts = crash.timestamp or "unknown"
        root = (
            f"{crash.root_frame.file}:{crash.root_frame.line}"
            if crash.root_frame
            else "?"
        )
        lines.append(
            f"  #{i:>3}  [{ts}] {crash.exception_type}: {crash.exception_message[:60]}"
        )
        lines.append(
            f"        at {root} in {crash.root_frame.function if crash.root_frame else '?'}"
        )
        if crash.common_cause:
            lines.append(f"        likely: {crash.common_cause}")
        lines.append("")

    if correlations:
        lines.append("--- SOURCE CORRELATIONS ---")
        for corr in correlations:
            has_log = "YES" if corr["has_logging"] else "NO (needs logging!)"
            lines.append(
                f"  {corr['crash']} at {corr['file']}:{corr['line']} in {corr['function']}"
            )
            lines.append(f"    Logging present: {has_log}")
            for ln, code in sorted(corr["source_context"].items()):
                marker = ">>>" if ln == corr["line"] else "   "
                lines.append(f"    {marker} {ln:>4}: {code}")
            lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Automated crash dump and traceback analysis"
    )
    parser.add_argument(
        "logfile", nargs="?", help="Log file or traceback file to analyze"
    )
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--format", choices=["json", "report"], default="report")
    parser.add_argument(
        "--correlate", help="Source directory to correlate crashes with"
    )
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.logfile:
        text = Path(args.logfile).read_text(encoding="utf-8", errors="replace")
    else:
        parser.print_help()
        sys.exit(1)

    crashes = parse_tracebacks(text)
    patterns = find_crash_patterns(crashes)

    correlations = None
    if args.correlate:
        correlations = correlate_with_source(crashes, Path(args.correlate))

    if args.format == "json":
        output = {
            "crashes": [asdict(c) for c in crashes],
            "patterns": {
                **patterns,
                "top_exception_types": [
                    {"type": t, "count": c} for t, c in patterns["top_exception_types"]
                ],
                "top_crash_locations": [
                    {"location": l, "count": c}
                    for l, c in patterns["top_crash_locations"]
                ],
                "recurring_crashes": [
                    {"location": l, "count": c}
                    for l, c in patterns["recurring_crashes"]
                ],
            },
            "correlations": correlations or [],
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(format_report(crashes, patterns, correlations))

    if not crashes:
        print("No tracebacks found in input.", file=sys.stderr)


if __name__ == "__main__":
    main()

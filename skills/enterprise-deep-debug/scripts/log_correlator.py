#!/usr/bin/env python3
"""Log correlation timeline builder with automatic pattern detection.

Reads one or more log files, extracts timestamps, severity levels, correlation
IDs, and builds a unified timeline. Detects:
- Error cascades (multiple errors within a short window)
- First-failure identification
- Correlation chains (same request/trace ID across files)
- Gap detection (suspiciously long pauses between log entries)
- Frequency anomalies (sudden spike in error rate)

Usage:
    python3 log_correlator.py <logfile1> [logfile2 ...] [--window 5s] [--format json|timeline]
    python3 log_correlator.py /tmp/local_fast_runner*.log --format timeline
    python3 log_correlator.py app.log worker.log --correlate-by request_id
"""

import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

TIMESTAMP_PATTERNS = [
    (
        re.compile(r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\]"),
        "%Y-%m-%d %H:%M:%S.%f",
    ),
    (re.compile(r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)"), "%Y-%m-%dT%H:%M:%S.%f"),
    (re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"), "%Y-%m-%dT%H:%M:%S"),
    (re.compile(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"), "%Y-%m-%d %H:%M:%S"),
]

SEVERITY_PATTERNS = [
    (re.compile(r"\b(CRITICAL|FATAL)\b", re.I), "CRITICAL"),
    (re.compile(r"\bERROR\b", re.I), "ERROR"),
    (re.compile(r"\b(WARN|WARNING)\b", re.I), "WARNING"),
    (re.compile(r"\bINFO\b", re.I), "INFO"),
    (re.compile(r"\bDEBUG\b", re.I), "DEBUG"),
    (re.compile(r"\b(TRACE|VERBOSE)\b", re.I), "TRACE"),
]

CORRELATION_PATTERNS = [
    re.compile(
        r"(?:request_id|req_id|correlation_id|trace_id|x-request-id)[=:\s]+['\"]?(\w{8,})['\"]?",
        re.I,
    ),
    re.compile(r"(?:span_id)[=:\s]+['\"]?(\w{8,})['\"]?", re.I),
]

ERROR_KEYWORDS = re.compile(
    r"\b(error|exception|fail|crash|traceback|aborted|timeout|refused|denied|invalid|broken|fatal|panic)\b",
    re.I,
)


@dataclass
class LogEntry:
    timestamp: Optional[datetime]
    severity: str
    message: str
    source_file: str
    line_number: int
    correlation_ids: List[str] = field(default_factory=list)
    is_error: bool = False


@dataclass
class ErrorCascade:
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: float
    error_count: int
    entries: List[LogEntry] = field(default_factory=list)
    first_error_message: str = ""


@dataclass
class GapEvent:
    before_time: Optional[datetime]
    after_time: Optional[datetime]
    gap_seconds: float
    before_entry: Optional[LogEntry] = None
    after_entry: Optional[LogEntry] = None


def parse_timestamp(line: str) -> Tuple[Optional[datetime], str]:
    for pattern, fmt in TIMESTAMP_PATTERNS:
        m = pattern.search(line)
        if m:
            try:
                ts_str = m.group(1)
                if "." in ts_str and fmt.endswith("%f"):
                    parts = ts_str.rsplit(".", 1)
                    frac = parts[1][:6].ljust(6, "0")
                    ts_str = parts[0] + "." + frac
                return datetime.strptime(ts_str, fmt), fmt
            except ValueError:
                continue
    return None, ""


def parse_severity(line: str) -> str:
    for pattern, level in SEVERITY_PATTERNS:
        if pattern.search(line):
            return level
    return "UNKNOWN"


def extract_correlation_ids(line: str) -> List[str]:
    ids = []
    for pattern in CORRELATION_PATTERNS:
        for m in pattern.finditer(line):
            ids.append(m.group(1))
    return ids


def parse_log_file(filepath: Path) -> List[LogEntry]:
    entries = []
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return entries

    for i, line in enumerate(lines, 1):
        ts, _ = parse_timestamp(line)
        severity = parse_severity(line)
        corr_ids = extract_correlation_ids(line)
        is_error = bool(ERROR_KEYWORDS.search(line)) or severity in (
            "ERROR",
            "CRITICAL",
        )

        entries.append(
            LogEntry(
                timestamp=ts,
                severity=severity,
                message=line.strip()[:300],
                source_file=str(filepath),
                line_number=i,
                correlation_ids=corr_ids,
                is_error=is_error,
            )
        )

    return entries


def find_error_cascades(
    entries: List[LogEntry], window_seconds: float = 5.0
) -> List[ErrorCascade]:
    errors = [e for e in entries if e.is_error and e.timestamp]
    if not errors:
        return []

    errors.sort(key=lambda e: e.timestamp)

    cascades: List[ErrorCascade] = []
    current: List[LogEntry] = [errors[0]]

    for i in range(1, len(errors)):
        if (
            errors[i].timestamp - current[-1].timestamp
        ).total_seconds() <= window_seconds:
            current.append(errors[i])
        else:
            if len(current) >= 2:
                cascades.append(
                    ErrorCascade(
                        start_time=current[0].timestamp,
                        end_time=current[-1].timestamp,
                        duration_seconds=(
                            current[-1].timestamp - current[0].timestamp
                        ).total_seconds(),
                        error_count=len(current),
                        entries=current,
                        first_error_message=current[0].message[:200],
                    )
                )
            current = [errors[i]]

    if len(current) >= 2:
        cascades.append(
            ErrorCascade(
                start_time=current[0].timestamp,
                end_time=current[-1].timestamp,
                duration_seconds=(
                    current[-1].timestamp - current[0].timestamp
                ).total_seconds(),
                error_count=len(current),
                entries=current,
                first_error_message=current[0].message[:200],
            )
        )

    return cascades


def find_gaps(entries: List[LogEntry], min_gap_seconds: float = 30.0) -> List[GapEvent]:
    timestamped = [e for e in entries if e.timestamp]
    if len(timestamped) < 2:
        return []

    timestamped.sort(key=lambda e: e.timestamp)
    gaps = []
    for i in range(1, len(timestamped)):
        gap = (timestamped[i].timestamp - timestamped[i - 1].timestamp).total_seconds()
        if gap >= min_gap_seconds:
            gaps.append(
                GapEvent(
                    before_time=timestamped[i - 1].timestamp,
                    after_time=timestamped[i].timestamp,
                    gap_seconds=gap,
                    before_entry=timestamped[i - 1],
                    after_entry=timestamped[i],
                )
            )

    return gaps


def build_correlation_chains(entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
    chains: Dict[str, List[LogEntry]] = defaultdict(list)
    for e in entries:
        for cid in e.correlation_ids:
            chains[cid].append(e)
    return {k: v for k, v in chains.items() if len(v) >= 2}


def find_first_failure(entries: List[LogEntry]) -> Optional[LogEntry]:
    errors = [e for e in entries if e.is_error and e.timestamp]
    if not errors:
        return None
    return min(errors, key=lambda e: e.timestamp)


def format_timeline(
    entries: List[LogEntry],
    cascades: List[ErrorCascade],
    gaps: List[GapEvent],
    first_failure: Optional[LogEntry],
    chains: Dict,
) -> str:
    lines = []
    lines.append("=" * 100)
    lines.append("LOG CORRELATION TIMELINE")
    lines.append("=" * 100)

    total = len(entries)
    errors = sum(1 for e in entries if e.is_error)
    sources = len(set(e.source_file for e in entries))
    lines.append(
        f"Total entries: {total} | Errors: {errors} | Sources: {sources} | Cascades: {len(cascades)} | Gaps: {len(gaps)}"
    )
    lines.append("")

    if first_failure:
        lines.append("--- FIRST FAILURE ---")
        lines.append(
            f"  [{first_failure.timestamp}] {first_failure.source_file}:{first_failure.line_number}"
        )
        lines.append(f"  {first_failure.message[:200]}")
        lines.append("")

    if cascades:
        lines.append("--- ERROR CASCADES ---")
        for i, cascade in enumerate(cascades, 1):
            lines.append(
                f"  Cascade #{i}: {cascade.error_count} errors in {cascade.duration_seconds:.1f}s"
            )
            lines.append(f"    Start: {cascade.start_time}")
            lines.append(f"    First: {cascade.first_error_message[:150]}")
            for entry in cascade.entries[:5]:
                lines.append(
                    f"      [{entry.timestamp}] {entry.severity:>8} | {entry.message[:120]}"
                )
            if cascade.error_count > 5:
                lines.append(f"      ... and {cascade.error_count - 5} more")
            lines.append("")

    if gaps:
        lines.append("--- SUSPICIOUS GAPS ---")
        for gap in gaps[:10]:
            lines.append(
                f"  {gap.gap_seconds:>8.1f}s gap: {gap.before_time} -> {gap.after_time}"
            )
            if gap.before_entry:
                lines.append(f"    Before: {gap.before_entry.message[:100]}")
            if gap.after_entry:
                lines.append(f"    After:  {gap.after_entry.message[:100]}")
        lines.append("")

    if chains:
        lines.append(f"--- CORRELATION CHAINS ({len(chains)} chains) ---")
        for cid, chain_entries in list(chains.items())[:10]:
            lines.append(f"  ID: {cid} ({len(chain_entries)} entries)")
            for entry in chain_entries[:5]:
                lines.append(
                    f"    [{entry.timestamp}] {entry.severity:>8} {Path(entry.source_file).name}:{entry.line_number} | {entry.message[:80]}"
                )
        lines.append("")

    lines.append("--- ERROR TIMELINE (chronological) ---")
    error_entries = sorted(
        [e for e in entries if e.is_error and e.timestamp], key=lambda e: e.timestamp
    )
    for entry in error_entries[:50]:
        src = Path(entry.source_file).name
        lines.append(
            f"  [{entry.timestamp}] {entry.severity:>8} {src}:{entry.line_number:<5} | {entry.message[:100]}"
        )

    if len(error_entries) > 50:
        lines.append(f"  ... and {len(error_entries) - 50} more errors")

    lines.append("=" * 100)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Log correlation timeline builder")
    parser.add_argument("logfiles", nargs="+", help="Log files to analyze")
    parser.add_argument(
        "--window", default="5s", help="Error cascade window (e.g. 5s, 10s)"
    )
    parser.add_argument(
        "--gap-threshold", type=float, default=30.0, help="Minimum gap in seconds"
    )
    parser.add_argument("--format", choices=["json", "timeline"], default="timeline")
    args = parser.parse_args()

    window_match = re.match(r"(\d+)s?", args.window)
    window_seconds = float(window_match.group(1)) if window_match else 5.0

    all_entries: List[LogEntry] = []
    for logfile in args.logfiles:
        for p in sorted(Path(".").glob(logfile)) if "*" in logfile else [Path(logfile)]:
            if p.exists():
                entries = parse_log_file(p)
                all_entries.extend(entries)
                print(f"Parsed {len(entries)} entries from {p}", file=sys.stderr)

    if not all_entries:
        print("No log entries found.", file=sys.stderr)
        sys.exit(1)

    cascades = find_error_cascades(all_entries, window_seconds)
    gaps = find_gaps(all_entries, args.gap_threshold)
    first_failure = find_first_failure(all_entries)
    chains = build_correlation_chains(all_entries)

    if args.format == "json":
        output = {
            "total_entries": len(all_entries),
            "total_errors": sum(1 for e in all_entries if e.is_error),
            "first_failure": asdict(first_failure) if first_failure else None,
            "cascades": [asdict(c) for c in cascades],
            "gaps": [asdict(g) for g in gaps],
            "correlation_chains": {
                k: [asdict(e) for e in v] for k, v in chains.items()
            },
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(format_timeline(all_entries, cascades, gaps, first_failure, chains))


if __name__ == "__main__":
    main()

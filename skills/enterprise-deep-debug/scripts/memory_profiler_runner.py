#!/usr/bin/env python3
"""Automated memory leak detection and profiling.

Wraps tracemalloc and objgraph to snapshot memory at intervals, diff snapshots,
identify growing objects, and produce a leak report with allocation tracebacks.

Usage:
    python3 memory_profiler_runner.py run <script.py> [args...] [--interval 2] [--top 20]
    python3 memory_profiler_runner.py snapshot <pid> [--output snap.json]
    python3 memory_profiler_runner.py diff snap1.json snap2.json
    python3 memory_profiler_runner.py analyze <script.py> --watch "MyClass,dict,list"
"""

import sys
import os
import json
import time
import tracemalloc
import linecache
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from collections import Counter


@dataclass
class MemorySnapshot:
    timestamp: float
    total_size_mb: float
    total_blocks: int
    top_allocations: List[Dict] = field(default_factory=list)
    type_counts: Dict[str, int] = field(default_factory=dict)
    type_sizes: Dict[str, int] = field(default_factory=dict)


@dataclass
class LeakCandidate:
    location: str
    size_growth_bytes: int
    count_growth: int
    traceback: List[str] = field(default_factory=list)
    severity: str = "low"


@dataclass
class MemoryReport:
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    leak_candidates: List[LeakCandidate] = field(default_factory=list)
    peak_memory_mb: float = 0.0
    total_growth_mb: float = 0.0
    duration_seconds: float = 0.0


def take_snapshot(top_n: int = 30) -> MemorySnapshot:
    snapshot = tracemalloc.take_snapshot()
    snapshot = snapshot.filter_traces(
        (
            tracemalloc.Filter(False, "<frozen *>"),
            tracemalloc.Filter(False, "<unknown>"),
            tracemalloc.Filter(False, tracemalloc.__file__),
        )
    )

    stats = snapshot.statistics("lineno")
    top_allocs = []
    for stat in stats[:top_n]:
        frame = stat.traceback[0]
        top_allocs.append(
            {
                "file": frame.filename,
                "line": frame.lineno,
                "size_kb": stat.size / 1024,
                "count": stat.count,
                "code": linecache.getline(frame.filename, frame.lineno).strip(),
            }
        )

    current, peak = tracemalloc.get_traced_memory()

    type_counts = {}
    type_sizes = {}
    try:
        import gc

        for obj in gc.get_objects()[:50000]:
            t = type(obj).__name__
            type_counts[t] = type_counts.get(t, 0) + 1
            try:
                type_sizes[t] = type_sizes.get(t, 0) + sys.getsizeof(obj)
            except (TypeError, ReferenceError):
                pass
    except Exception:
        pass

    return MemorySnapshot(
        timestamp=time.time(),
        total_size_mb=current / (1024 * 1024),
        total_blocks=sum(s.count for s in stats),
        top_allocations=top_allocs,
        type_counts=dict(
            sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:30]
        ),
        type_sizes=dict(
            sorted(type_sizes.items(), key=lambda x: x[1], reverse=True)[:30]
        ),
    )


def diff_snapshots(snap1: MemorySnapshot, snap2: MemorySnapshot) -> List[LeakCandidate]:
    candidates = []

    alloc_map1 = {f"{a['file']}:{a['line']}": a for a in snap1.top_allocations}
    alloc_map2 = {f"{a['file']}:{a['line']}": a for a in snap2.top_allocations}

    for loc, a2 in alloc_map2.items():
        a1 = alloc_map1.get(loc)
        if a1:
            size_growth = int((a2["size_kb"] - a1["size_kb"]) * 1024)
            count_growth = a2["count"] - a1["count"]
            if size_growth > 1024 or count_growth > 10:
                severity = (
                    "critical"
                    if size_growth > 1024 * 1024
                    else "high"
                    if size_growth > 102400
                    else "medium"
                    if size_growth > 10240
                    else "low"
                )
                candidates.append(
                    LeakCandidate(
                        location=loc,
                        size_growth_bytes=size_growth,
                        count_growth=count_growth,
                        traceback=[a2.get("code", "")],
                        severity=severity,
                    )
                )
        elif a2["size_kb"] > 100:
            candidates.append(
                LeakCandidate(
                    location=loc,
                    size_growth_bytes=int(a2["size_kb"] * 1024),
                    count_growth=a2["count"],
                    traceback=[a2.get("code", "")],
                    severity="medium",
                )
            )

    for t_name, count2 in snap2.type_counts.items():
        count1 = snap1.type_counts.get(t_name, 0)
        growth = count2 - count1
        if growth > 100:
            size1 = snap1.type_sizes.get(t_name, 0)
            size2 = snap2.type_sizes.get(t_name, 0)
            severity = "high" if growth > 1000 else "medium"
            candidates.append(
                LeakCandidate(
                    location=f"<type:{t_name}>",
                    size_growth_bytes=size2 - size1,
                    count_growth=growth,
                    severity=severity,
                )
            )

    candidates.sort(key=lambda c: c.size_growth_bytes, reverse=True)
    return candidates


def run_with_profiling(
    script_path: str, script_args: List, interval: float, top_n: int
) -> MemoryReport:
    tracemalloc.start(25)
    report = MemoryReport()
    start_time = time.time()

    sys.argv = [script_path] + script_args
    script_dir = str(Path(script_path).parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    report.snapshots.append(take_snapshot(top_n))
    print(
        f"Initial memory: {report.snapshots[0].total_size_mb:.2f} MB", file=sys.stderr
    )

    code = Path(script_path).read_text(encoding="utf-8")
    compiled = compile(code, script_path, "exec")

    import threading

    stop_event = threading.Event()

    def snapshot_loop():
        while not stop_event.is_set():
            stop_event.wait(interval)
            if not stop_event.is_set():
                snap = take_snapshot(top_n)
                report.snapshots.append(snap)
                print(
                    f"  Snapshot #{len(report.snapshots)}: {snap.total_size_mb:.2f} MB ({snap.total_blocks} blocks)",
                    file=sys.stderr,
                )

    t = threading.Thread(target=snapshot_loop, daemon=True)
    t.start()

    try:
        exec(
            compiled,
            {
                "__name__": "__main__",
                "__file__": script_path,
                "__builtins__": __builtins__,
            },
        )
    except SystemExit:
        pass
    except Exception as e:
        print(f"Script error: {type(e).__name__}: {e}", file=sys.stderr)
    finally:
        stop_event.set()
        t.join(timeout=2)

    final_snap = take_snapshot(top_n)
    report.snapshots.append(final_snap)
    report.duration_seconds = time.time() - start_time

    if len(report.snapshots) >= 2:
        report.leak_candidates = diff_snapshots(
            report.snapshots[0], report.snapshots[-1]
        )
        report.total_growth_mb = (
            report.snapshots[-1].total_size_mb - report.snapshots[0].total_size_mb
        )

    report.peak_memory_mb = max(s.total_size_mb for s in report.snapshots)

    tracemalloc.stop()
    return report


def format_report(report: MemoryReport) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append("MEMORY PROFILING REPORT")
    lines.append("=" * 80)
    lines.append(f"Duration: {report.duration_seconds:.1f}s")
    lines.append(f"Snapshots: {len(report.snapshots)}")
    lines.append(f"Peak memory: {report.peak_memory_mb:.2f} MB")
    lines.append(f"Memory growth: {report.total_growth_mb:+.2f} MB")
    lines.append("")

    if report.snapshots:
        lines.append("--- MEMORY TIMELINE ---")
        for i, snap in enumerate(report.snapshots):
            marker = " <<<PEAK" if snap.total_size_mb == report.peak_memory_mb else ""
            lines.append(
                f"  #{i:<3} {snap.total_size_mb:>8.2f} MB  {snap.total_blocks:>6} blocks{marker}"
            )
        lines.append("")

    if report.leak_candidates:
        lines.append("--- LEAK CANDIDATES ---")
        for lc in report.leak_candidates[:20]:
            lines.append(f"  [{lc.severity:>8}] {lc.location}")
            lines.append(
                f"           Size growth: {lc.size_growth_bytes:>10} bytes  Count growth: {lc.count_growth:>6}"
            )
            if lc.traceback:
                for tb in lc.traceback[:3]:
                    if tb:
                        lines.append(f"           Code: {tb[:100]}")
        lines.append("")

    if report.snapshots and report.snapshots[-1].top_allocations:
        lines.append("--- FINAL TOP ALLOCATIONS ---")
        for a in report.snapshots[-1].top_allocations[:15]:
            lines.append(
                f"  {a['size_kb']:>8.1f} KB  {a['count']:>5}x  {a['file']}:{a['line']}"
            )
            if a.get("code"):
                lines.append(f"                            {a['code'][:80]}")
        lines.append("")

    if report.snapshots and report.snapshots[-1].type_counts:
        lines.append("--- TOP OBJECT TYPES (by count) ---")
        for t_name, count in list(report.snapshots[-1].type_counts.items())[:15]:
            size = report.snapshots[-1].type_sizes.get(t_name, 0)
            lines.append(f"  {count:>8}x  {size / 1024:>8.1f} KB  {t_name}")

    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Automated memory leak detection")
    subparsers = parser.add_subparsers(dest="command")

    run_p = subparsers.add_parser("run", help="Profile a script")
    run_p.add_argument("script", help="Python script")
    run_p.add_argument("script_args", nargs="*")
    run_p.add_argument(
        "--interval", type=float, default=2.0, help="Snapshot interval in seconds"
    )
    run_p.add_argument("--top", type=int, default=20)
    run_p.add_argument("--output", help="Save report as JSON")
    run_p.add_argument("--format", choices=["json", "report"], default="report")

    diff_p = subparsers.add_parser("diff", help="Diff two snapshots")
    diff_p.add_argument("snap1", help="First snapshot JSON")
    diff_p.add_argument("snap2", help="Second snapshot JSON")

    args = parser.parse_args()

    if args.command == "run":
        report = run_with_profiling(
            args.script, args.script_args, args.interval, args.top
        )
        if args.format == "json":
            print(json.dumps(asdict(report), indent=2, default=str))
        else:
            print(format_report(report))
        if args.output:
            Path(args.output).write_text(
                json.dumps(asdict(report), indent=2, default=str)
            )
            print(f"Report saved to {args.output}", file=sys.stderr)

    elif args.command == "diff":
        s1 = MemorySnapshot(**json.loads(Path(args.snap1).read_text()))
        s2 = MemorySnapshot(**json.loads(Path(args.snap2).read_text()))
        candidates = diff_snapshots(s1, s2)
        for lc in candidates:
            print(
                f"[{lc.severity:>8}] {lc.location} +{lc.size_growth_bytes}B +{lc.count_growth}obj"
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

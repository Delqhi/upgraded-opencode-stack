#!/usr/bin/env python3
"""Automatic flamegraph generation via cProfile + flamegraph conversion.

Profiles a Python script and converts the output into flamegraph-compatible
format (collapsed stacks). Can also generate SVG flamegraphs if flamegraph.pl
or py-spy is available.

Usage:
    python3 flamegraph_runner.py run <script.py> [args...] [--output profile.svg]
    python3 flamegraph_runner.py run app.py --top 30 --format collapsed
    python3 flamegraph_runner.py convert profile.prof --format collapsed
    python3 flamegraph_runner.py hotspots <script.py> --top 20
"""

import sys
import os
import cProfile
import pstats
import io
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from collections import defaultdict


@dataclass
class HotspotEntry:
    function: str
    file: str
    line: int
    total_time: float
    cumulative_time: float
    calls: int
    time_per_call_ms: float
    pct_of_total: float


@dataclass
class ProfileReport:
    total_time: float
    total_calls: int
    hotspots: List[HotspotEntry] = field(default_factory=list)
    call_tree_depth: int = 0
    collapsed_stacks: str = ""


def profile_script(script_path: str, script_args: List[str]) -> pstats.Stats:
    sys.argv = [script_path] + script_args
    script_dir = str(Path(script_path).parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    profiler = cProfile.Profile()

    code = Path(script_path).read_text(encoding="utf-8")
    compiled = compile(code, script_path, "exec")

    profiler.enable()
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
        profiler.disable()

    return pstats.Stats(profiler)


def stats_to_hotspots(stats: pstats.Stats, top_n: int = 30) -> List[HotspotEntry]:
    stats.sort_stats("cumulative")

    buf = io.StringIO()
    stats.stream = buf
    stats.print_stats(top_n * 2)
    buf.seek(0)

    hotspots = []
    total_time = stats.total_tt

    for key, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, lineno, func_name = key
        if filename.startswith("<") or "/lib/python" in filename:
            continue

        hotspots.append(
            HotspotEntry(
                function=func_name,
                file=filename,
                line=lineno,
                total_time=tt,
                cumulative_time=ct,
                calls=nc,
                time_per_call_ms=(tt / nc * 1000) if nc > 0 else 0,
                pct_of_total=(ct / total_time * 100) if total_time > 0 else 0,
            )
        )

    hotspots.sort(key=lambda h: h.cumulative_time, reverse=True)
    return hotspots[:top_n]


def stats_to_collapsed_stacks(stats: pstats.Stats) -> str:
    stacks = defaultdict(int)

    for key, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, lineno, func_name = key
        if filename.startswith("<"):
            continue

        short_file = Path(filename).name
        self_label = f"{short_file}:{func_name}"

        for caller_key, caller_count in callers.items():
            c_file, c_line, c_func = caller_key
            c_short = Path(c_file).name
            caller_label = f"{c_short}:{c_func}"
            stack_key = f"{caller_label};{self_label}"
            count = caller_count[0] if isinstance(caller_count, tuple) else caller_count
            weight = max(1, int(tt * 1000000))
            stacks[stack_key] += weight

        if not callers:
            stacks[self_label] += max(1, int(tt * 1000000))

    lines = []
    for stack, weight in sorted(stacks.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"{stack} {weight}")

    return "\n".join(lines)


def try_generate_svg(collapsed: str, output_path: str) -> bool:
    flamegraph_pl = None
    for candidate in [
        "/usr/local/bin/flamegraph.pl",
        "/opt/homebrew/bin/flamegraph.pl",
        os.path.expanduser("~/bin/flamegraph.pl"),
    ]:
        if Path(candidate).exists():
            flamegraph_pl = candidate
            break

    if not flamegraph_pl:
        try:
            result = subprocess.run(
                ["which", "flamegraph.pl"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                flamegraph_pl = result.stdout.strip()
        except Exception:
            pass

    if flamegraph_pl:
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".collapsed", delete=False
            ) as f:
                f.write(collapsed)
                f.flush()
                result = subprocess.run(
                    ["perl", flamegraph_pl, f.name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    Path(output_path).write_text(result.stdout)
                    os.unlink(f.name)
                    return True
                os.unlink(f.name)
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["which", "py-spy"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(
                "py-spy available but requires live process. Use: py-spy record -o output.svg -- python script.py",
                file=sys.stderr,
            )
    except Exception:
        pass

    return False


def format_report(report: ProfileReport) -> str:
    lines = []
    lines.append("=" * 90)
    lines.append("PROFILING REPORT (FLAMEGRAPH-READY)")
    lines.append("=" * 90)
    lines.append(f"Total time: {report.total_time:.4f}s")
    lines.append(f"Total calls: {report.total_calls}")
    lines.append("")

    lines.append("--- HOTSPOTS (sorted by cumulative time) ---")
    lines.append(
        f"{'%':>6} {'cum_s':>8} {'self_s':>8} {'calls':>8} {'ms/call':>8}  function"
    )
    lines.append("-" * 90)

    for h in report.hotspots:
        short_file = Path(h.file).name if not h.file.startswith("<") else h.file
        lines.append(
            f"{h.pct_of_total:>5.1f}% {h.cumulative_time:>8.4f} {h.total_time:>8.4f} {h.calls:>8} {h.time_per_call_ms:>8.3f}  {short_file}:{h.line} {h.function}"
        )

    lines.append("")
    lines.append("--- COLLAPSED STACKS (pipe to flamegraph.pl for SVG) ---")
    collapsed_lines = report.collapsed_stacks.split("\n")
    for cl in collapsed_lines[:30]:
        lines.append(f"  {cl}")
    if len(collapsed_lines) > 30:
        lines.append(f"  ... and {len(collapsed_lines) - 30} more stacks")

    lines.append("=" * 90)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Automatic flamegraph generation")
    subparsers = parser.add_subparsers(dest="command")

    run_p = subparsers.add_parser("run", help="Profile a script")
    run_p.add_argument("script", help="Python script")
    run_p.add_argument("script_args", nargs="*")
    run_p.add_argument("--top", type=int, default=30)
    run_p.add_argument("--output", help="Output SVG or collapsed stacks file")
    run_p.add_argument(
        "--format", choices=["report", "collapsed", "json", "svg"], default="report"
    )
    run_p.add_argument("--save-prof", help="Save raw profile data to .prof file")

    hotspot_p = subparsers.add_parser("hotspots", help="Quick hotspot analysis")
    hotspot_p.add_argument("script", help="Python script")
    hotspot_p.add_argument("script_args", nargs="*")
    hotspot_p.add_argument("--top", type=int, default=20)

    convert_p = subparsers.add_parser(
        "convert", help="Convert .prof to collapsed stacks"
    )
    convert_p.add_argument("prof_file", help=".prof file from cProfile")
    convert_p.add_argument(
        "--format", choices=["collapsed", "json"], default="collapsed"
    )

    args = parser.parse_args()

    if args.command == "run":
        print(f"Profiling {args.script}...", file=sys.stderr)
        stats = profile_script(args.script, args.script_args)

        if args.save_prof:
            stats.dump_stats(args.save_prof)
            print(f"Raw profile saved to {args.save_prof}", file=sys.stderr)

        report = ProfileReport(
            total_time=stats.total_tt,
            total_calls=stats.total_calls,
            hotspots=stats_to_hotspots(stats, args.top),
            collapsed_stacks=stats_to_collapsed_stacks(stats),
        )

        if args.format == "svg" and args.output:
            collapsed_path = args.output.replace(".svg", ".collapsed")
            Path(collapsed_path).write_text(report.collapsed_stacks)
            if try_generate_svg(report.collapsed_stacks, args.output):
                print(f"Flamegraph SVG saved to {args.output}", file=sys.stderr)
            else:
                print(
                    f"Collapsed stacks saved to {collapsed_path} (pipe to flamegraph.pl for SVG)",
                    file=sys.stderr,
                )
        elif args.format == "collapsed":
            print(report.collapsed_stacks)
        elif args.format == "json":
            print(json.dumps(asdict(report), indent=2))
        else:
            print(format_report(report))

    elif args.command == "hotspots":
        stats = profile_script(args.script, args.script_args)
        hotspots = stats_to_hotspots(stats, args.top)
        print(f"\nTop {args.top} hotspots (total {stats.total_tt:.4f}s):")
        for h in hotspots:
            short = Path(h.file).name
            print(
                f"  {h.pct_of_total:>5.1f}%  {h.cumulative_time:>7.4f}s  {h.calls:>6}x  {short}:{h.line} {h.function}"
            )

    elif args.command == "convert":
        stats = pstats.Stats(args.prof_file)
        collapsed = stats_to_collapsed_stacks(stats)
        if args.format == "json":
            hotspots = stats_to_hotspots(stats, 50)
            print(
                json.dumps(
                    {"hotspots": [asdict(h) for h in hotspots], "collapsed": collapsed},
                    indent=2,
                )
            )
        else:
            print(collapsed)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

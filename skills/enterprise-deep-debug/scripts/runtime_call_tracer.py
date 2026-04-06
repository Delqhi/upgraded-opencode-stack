#!/usr/bin/env python3
"""Runtime function call trace recorder using sys.settrace / sys.setprofile.

Attaches to a running Python process or instruments a script to record every
function call with arguments, return values, timing, and call depth. Produces
a hierarchical call tree or flat log.

Usage:
    python3 runtime_call_tracer.py run <script.py> [args...] [--max-depth 10] [--output trace.json]
    python3 runtime_call_tracer.py run app.py --filter "mymodule" --max-calls 10000
    python3 runtime_call_tracer.py analyze trace.json --format tree|flamegraph|stats
"""

import sys
import os
import json
import time
import argparse
import threading
import traceback as tb_module
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from collections import defaultdict, Counter
from contextlib import contextmanager

MAX_ARG_REPR_LEN = 200
MAX_RETURN_REPR_LEN = 200


@dataclass
class CallRecord:
    function: str
    module: str
    file: str
    line: int
    depth: int
    timestamp: float
    duration: float = 0.0
    args_repr: str = ""
    return_repr: str = ""
    exception: str = ""
    children_count: int = 0
    call_id: int = 0


class CallTracer:
    def __init__(
        self,
        max_depth: int = 50,
        max_calls: int = 100000,
        filter_modules: Optional[List[str]] = None,
        exclude_stdlib: bool = True,
    ):
        self.max_depth = max_depth
        self.max_calls = max_calls
        self.filter_modules = filter_modules
        self.exclude_stdlib = exclude_stdlib
        self.records: List[CallRecord] = []
        self.call_stack: List[CallRecord] = []
        self.depth = 0
        self.call_count = 0
        self.lock = threading.Lock()
        self._stdlib_prefixes = self._get_stdlib_prefixes()
        self._call_id = 0

    def _get_stdlib_prefixes(self) -> tuple:
        import sysconfig

        paths = []
        for name in ("stdlib", "platstdlib", "purelib", "platlib"):
            p = sysconfig.get_path(name)
            if p:
                paths.append(p)
        paths.append(os.path.dirname(os.__file__))
        return tuple(set(paths))

    def _should_trace(self, filename: str, module_name: str) -> bool:
        if self.call_count >= self.max_calls:
            return False
        if self.exclude_stdlib and filename.startswith(self._stdlib_prefixes):
            return False
        if filename.startswith("<"):
            return False
        if self.filter_modules:
            return any(f in module_name or f in filename for f in self.filter_modules)
        return True

    def _safe_repr(self, obj, max_len: int = MAX_ARG_REPR_LEN) -> str:
        try:
            r = repr(obj)
            if len(r) > max_len:
                return r[:max_len] + "..."
            return r
        except Exception:
            return f"<repr failed: {type(obj).__name__}>"

    def trace_calls(self, frame, event, arg):
        filename = frame.f_code.co_filename
        func_name = frame.f_code.co_name
        module = frame.f_globals.get("__name__", "")

        if not self._should_trace(filename, module):
            return None

        if event == "call":
            if self.depth >= self.max_depth:
                return None

            self.depth += 1
            self._call_id += 1

            args_repr = ""
            try:
                local_vars = frame.f_locals
                arg_names = frame.f_code.co_varnames[: frame.f_code.co_argcount]
                arg_parts = []
                for name in arg_names[:8]:
                    if name in local_vars:
                        arg_parts.append(
                            f"{name}={self._safe_repr(local_vars[name], 100)}"
                        )
                args_repr = ", ".join(arg_parts)
                if len(args_repr) > MAX_ARG_REPR_LEN:
                    args_repr = args_repr[:MAX_ARG_REPR_LEN] + "..."
            except Exception:
                pass

            record = CallRecord(
                function=func_name,
                module=module,
                file=filename,
                line=frame.f_lineno,
                depth=self.depth,
                timestamp=time.perf_counter(),
                args_repr=args_repr,
                call_id=self._call_id,
            )
            self.call_stack.append(record)
            self.call_count += 1
            return self.trace_calls

        elif event == "return":
            if self.call_stack:
                record = self.call_stack.pop()
                record.duration = time.perf_counter() - record.timestamp
                record.return_repr = self._safe_repr(arg, MAX_RETURN_REPR_LEN)
                with self.lock:
                    self.records.append(record)
            self.depth = max(0, self.depth - 1)
            return None

        elif event == "exception":
            if self.call_stack:
                exc_type, exc_value, exc_tb = arg
                self.call_stack[-1].exception = f"{exc_type.__name__}: {exc_value}"
            return self.trace_calls

        return self.trace_calls

    def get_stats(self) -> Dict:
        func_times: Dict[str, float] = defaultdict(float)
        func_counts: Counter = Counter()
        func_errors: Counter = Counter()

        for r in self.records:
            key = f"{r.module}.{r.function}"
            func_times[key] += r.duration
            func_counts[key] += 1
            if r.exception:
                func_errors[key] += 1

        slowest = sorted(func_times.items(), key=lambda x: x[1], reverse=True)[:20]
        most_called = func_counts.most_common(20)
        most_errors = func_errors.most_common(10)

        return {
            "total_calls": len(self.records),
            "total_time": sum(func_times.values()),
            "unique_functions": len(func_counts),
            "slowest_functions": [
                {
                    "func": f,
                    "total_time": t,
                    "calls": func_counts[f],
                    "avg_time": t / func_counts[f],
                }
                for f, t in slowest
            ],
            "most_called": [{"func": f, "calls": c} for f, c in most_called],
            "most_errors": [{"func": f, "errors": c} for f, c in most_errors],
            "max_depth_reached": max((r.depth for r in self.records), default=0),
        }


def format_call_tree(records: List[CallRecord], max_lines: int = 500) -> str:
    lines = []
    for r in records[:max_lines]:
        indent = "  " * (r.depth - 1) + "|-- " if r.depth > 0 else ""
        duration = f"{r.duration * 1000:.2f}ms" if r.duration > 0 else ""
        err = f" !! {r.exception}" if r.exception else ""
        ret = (
            f" -> {r.return_repr[:50]}"
            if r.return_repr and r.return_repr != "None"
            else ""
        )
        args = f"({r.args_repr[:80]})" if r.args_repr else "()"
        lines.append(f"{indent}{r.module}.{r.function}{args}{ret}{err}  [{duration}]")
    if len(records) > max_lines:
        lines.append(f"... and {len(records) - max_lines} more calls")
    return "\n".join(lines)


def format_flamegraph(records: List[CallRecord]) -> str:
    stacks: Counter = Counter()
    for r in records:
        stack_key = f"{r.module}.{r.function}"
        stacks[stack_key] += max(1, int(r.duration * 1000000))

    lines = []
    for stack, weight in stacks.most_common():
        lines.append(f"{stack} {weight}")
    return "\n".join(lines)


def run_script(script_path: str, script_args: List[str], tracer: CallTracer) -> int:
    sys.argv = [script_path] + script_args
    script_dir = str(Path(script_path).parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    script_globals = {
        "__name__": "__main__",
        "__file__": script_path,
        "__builtins__": __builtins__,
    }

    code = Path(script_path).read_text(encoding="utf-8")
    compiled = compile(code, script_path, "exec")

    sys.settrace(tracer.trace_calls)
    try:
        exec(compiled, script_globals)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print(f"Script raised: {type(e).__name__}: {e}", file=sys.stderr)
        tb_module.print_exc()
        return 1
    finally:
        sys.settrace(None)


def main():
    parser = argparse.ArgumentParser(description="Runtime function call trace recorder")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Trace a Python script")
    run_parser.add_argument("script", help="Python script to trace")
    run_parser.add_argument("script_args", nargs="*", help="Script arguments")
    run_parser.add_argument("--max-depth", type=int, default=30)
    run_parser.add_argument("--max-calls", type=int, default=50000)
    run_parser.add_argument(
        "--filter", nargs="+", help="Only trace modules containing these strings"
    )
    run_parser.add_argument("--output", help="Output trace to JSON file")
    run_parser.add_argument(
        "--format", choices=["tree", "stats", "flamegraph", "json"], default="stats"
    )

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a saved trace")
    analyze_parser.add_argument("trace_file", help="JSON trace file")
    analyze_parser.add_argument(
        "--format", choices=["tree", "stats", "flamegraph"], default="stats"
    )

    args = parser.parse_args()

    if args.command == "run":
        if not Path(args.script).exists():
            print(f"Script not found: {args.script}", file=sys.stderr)
            sys.exit(1)

        tracer = CallTracer(
            max_depth=args.max_depth,
            max_calls=args.max_calls,
            filter_modules=args.filter,
        )

        print(
            f"Tracing {args.script} (max_depth={args.max_depth}, max_calls={args.max_calls})...",
            file=sys.stderr,
        )
        exit_code = run_script(args.script, args.script_args, tracer)
        print(
            f"Script exited with code {exit_code}. Recorded {len(tracer.records)} calls.",
            file=sys.stderr,
        )

        if args.output:
            with open(args.output, "w") as f:
                json.dump([asdict(r) for r in tracer.records], f, indent=2)
            print(f"Trace saved to {args.output}", file=sys.stderr)

        if args.format == "tree":
            print(format_call_tree(tracer.records))
        elif args.format == "flamegraph":
            print(format_flamegraph(tracer.records))
        elif args.format == "json":
            print(json.dumps(tracer.get_stats(), indent=2))
        else:
            stats = tracer.get_stats()
            print(f"\n{'=' * 80}")
            print("CALL TRACE STATISTICS")
            print(f"{'=' * 80}")
            print(f"Total calls: {stats['total_calls']}")
            print(f"Total time: {stats['total_time']:.4f}s")
            print(f"Unique functions: {stats['unique_functions']}")
            print(f"Max depth: {stats['max_depth_reached']}")
            print(f"\n--- SLOWEST FUNCTIONS ---")
            for f in stats["slowest_functions"]:
                print(
                    f"  {f['total_time'] * 1000:>8.2f}ms ({f['calls']:>5}x, avg {f['avg_time'] * 1000:.2f}ms)  {f['func']}"
                )
            print(f"\n--- MOST CALLED ---")
            for f in stats["most_called"]:
                print(f"  {f['calls']:>6}x  {f['func']}")
            if stats["most_errors"]:
                print(f"\n--- MOST ERRORS ---")
                for f in stats["most_errors"]:
                    print(f"  {f['errors']:>6}x  {f['func']}")

    elif args.command == "analyze":
        records_data = json.loads(Path(args.trace_file).read_text())
        records = [CallRecord(**r) for r in records_data]
        if args.format == "tree":
            print(format_call_tree(records))
        elif args.format == "flamegraph":
            print(format_flamegraph(records))
        else:
            tracer = CallTracer()
            tracer.records = records
            stats = tracer.get_stats()
            print(json.dumps(stats, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

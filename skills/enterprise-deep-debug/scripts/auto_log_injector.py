#!/usr/bin/env python3
"""AST-based automatic log injection for Python codebases.

Parses Python files, injects structured logging at every function entry/exit,
captures arguments, return values, exceptions, and timing. Outputs transformed
code or a diff. Uses only stdlib (ast module).

Usage:
    python3 auto_log_injector.py <path> [--dry-run] [--diff] [--min-lines 3] [--skip-private] [--output-dir <dir>]
    python3 auto_log_injector.py src/  --diff          # show diff for entire directory
    python3 auto_log_injector.py app.py                # inject and overwrite in-place
    python3 auto_log_injector.py app.py --dry-run      # print transformed code to stdout
"""

import ast
import sys
import os
import textwrap
import difflib
import argparse
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional

IMPORT_BLOCK = textwrap.dedent("""\
    import logging as _ali_logging
    import time as _ali_time
    import traceback as _ali_traceback
    import functools as _ali_functools
    _ali_logger = _ali_logging.getLogger(__name__)
    if not _ali_logger.handlers:
        _ali_handler = _ali_logging.StreamHandler()
        _ali_handler.setFormatter(_ali_logging.Formatter(
            '[%(asctime)s.%(msecs)03d] %(levelname)-5s %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'))
        _ali_logger.addHandler(_ali_handler)
        _ali_logger.setLevel(_ali_logging.DEBUG)
""")

WRAPPER_TEMPLATE = textwrap.dedent("""\
    _ali_t0 = _ali_time.perf_counter()
    _ali_logger.debug("ENTER %s | args=%s kwargs=%s", {func_name!r}, {args_repr}, {kwargs_repr})
    try:
        {original_body}
    except BaseException as _ali_exc:
        _ali_logger.error("EXCEPTION %s | %s: %s | elapsed=%.4fs",
            {func_name!r}, type(_ali_exc).__name__, _ali_exc,
            _ali_time.perf_counter() - _ali_t0)
        _ali_logger.debug("TRACEBACK %s |\\n%s", {func_name!r}, _ali_traceback.format_exc())
        raise
""")

RETURN_LOG = '_ali_logger.debug("EXIT %s | return=%r | elapsed=%.4fs", {func_name!r}, {ret_var}, _ali_time.perf_counter() - _ali_t0)'


class LogInjectorTransformer(ast.NodeTransformer):
    def __init__(self, skip_private: bool = False, min_lines: int = 1):
        self.skip_private = skip_private
        self.min_lines = min_lines
        self.stats = {
            "functions_found": 0,
            "functions_injected": 0,
            "functions_skipped": 0,
        }

    def _should_skip(self, node: ast.FunctionDef) -> bool:
        if (
            self.skip_private
            and node.name.startswith("_")
            and not node.name.startswith("__")
        ):
            return True
        body_lines = (node.end_lineno or node.lineno) - node.lineno
        if body_lines < self.min_lines:
            return True
        if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Expr)):
            if isinstance(node.body[0], ast.Expr) and isinstance(
                node.body[0].value, (ast.Constant, ast.JoinedStr)
            ):
                return True
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in (
                "property",
                "staticmethod",
                "classmethod",
                "abstractmethod",
            ):
                pass
            if isinstance(dec, ast.Attribute) and dec.attr == "_ali_injected":
                return True
        return False

    def _build_args_repr(self, node: ast.FunctionDef) -> Tuple[str, str]:
        args = node.args
        positional_names = [
            a.arg for a in args.args if a.arg != "self" and a.arg != "cls"
        ]
        if positional_names:
            args_parts = ", ".join(f"'{n}': {n}" for n in positional_names[:8])
            args_repr = "{" + args_parts + "}"
        else:
            args_repr = "{}"

        if args.kwonlyargs:
            kw_parts = ", ".join(f"'{a.arg}': {a.arg}" for a in args.kwonlyargs[:5])
            kwargs_repr = "{" + kw_parts + "}"
        else:
            kwargs_repr = "{}"

        if args.vararg:
            args_repr = f"{{**{args_repr}, '*args_len': len({args.vararg.arg})}}"
        if args.kwarg:
            kwargs_repr = (
                f"{{**{kwargs_repr}, '**kwargs_keys': list({args.kwarg.arg}.keys())}}"
            )

        return args_repr, kwargs_repr

    def _already_injected(self, node: ast.FunctionDef) -> bool:
        if not node.body:
            return False
        first = node.body[0]
        if isinstance(first, ast.Assign):
            for target in first.targets:
                if isinstance(target, ast.Name) and target.id == "_ali_t0":
                    return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        self.stats["functions_found"] += 1

        if self._should_skip(node) or self._already_injected(node):
            self.stats["functions_skipped"] += 1
            return node

        args_repr, kwargs_repr = self._build_args_repr(node)
        func_name = node.name

        entry_log = ast.parse(
            textwrap.dedent(f"""\
_ali_t0 = _ali_time.perf_counter()
_ali_logger.debug("ENTER %s | args=%s kwargs=%s", {func_name!r}, {args_repr}, {kwargs_repr})
""")
        ).body

        new_body = []
        docstring = None
        start_idx = 0
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            docstring = node.body[0]
            start_idx = 1

        if docstring:
            new_body.append(docstring)

        new_body.extend(entry_log)

        exit_log_code = f'_ali_logger.debug("EXIT %s | elapsed=%.4fs", {func_name!r}, _ali_time.perf_counter() - _ali_t0)'

        wrapped_body = node.body[start_idx:]

        new_wrapped = []
        for stmt in wrapped_body:
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                ret_var = f"_ali_ret_{func_name}"
                assign = ast.parse(f"{ret_var} = None").body[0]
                assign.value = stmt.value
                ret_log = ast.parse(
                    f'_ali_logger.debug("EXIT %s | return=%r | elapsed=%.4fs", {func_name!r}, {ret_var}, _ali_time.perf_counter() - _ali_t0)'
                ).body[0]
                new_return = ast.parse(f"return {ret_var}").body[0]
                new_wrapped.extend([assign, ret_log, new_return])
            else:
                new_wrapped.append(stmt)

        try_body = new_wrapped if new_wrapped else [ast.parse("pass").body[0]]

        except_handler = ast.parse(
            textwrap.dedent(f"""\
try:
    pass
except BaseException as _ali_exc:
    _ali_logger.error("EXCEPTION %s | %s: %s | elapsed=%.4fs", {func_name!r}, type(_ali_exc).__name__, _ali_exc, _ali_time.perf_counter() - _ali_t0)
    _ali_logger.debug("TRACEBACK %s |\\n%s", {func_name!r}, _ali_traceback.format_exc())
    raise
""")
        ).body[0]
        except_handler.body = try_body

        final_exit = ast.parse(
            textwrap.dedent(f"""\
try:
    pass
finally:
    pass
""")
        ).body[0]
        final_exit.body = [except_handler]
        final_exit.finalbody = ast.parse(exit_log_code).body

        new_body.append(final_exit)

        node.body = new_body
        ast.fix_missing_locations(node)
        self.stats["functions_injected"] += 1
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


def inject_file(
    filepath: Path, skip_private: bool, min_lines: int
) -> Tuple[str, str, dict]:
    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        return source, source, {"error": str(e)}

    transformer = LogInjectorTransformer(skip_private=skip_private, min_lines=min_lines)
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    has_import = "_ali_logging" in source
    new_source = ast.unparse(new_tree)

    if not has_import and transformer.stats["functions_injected"] > 0:
        new_source = IMPORT_BLOCK + "\n" + new_source

    return source, new_source, transformer.stats


def process_path(path: Path, args) -> dict:
    total_stats = {
        "files": 0,
        "functions_found": 0,
        "functions_injected": 0,
        "functions_skipped": 0,
        "errors": 0,
    }

    py_files: List[Path] = []
    if path.is_file() and path.suffix == ".py":
        py_files = [path]
    elif path.is_dir():
        py_files = sorted(path.rglob("*.py"))
        py_files = [
            f
            for f in py_files
            if "node_modules" not in str(f)
            and ".venv" not in str(f)
            and "__pycache__" not in str(f)
            and "dist" not in str(f)
            and ".git" not in str(f)
        ]

    for pf in py_files:
        total_stats["files"] += 1
        original, transformed, stats = inject_file(
            pf, args.skip_private, args.min_lines
        )

        if "error" in stats:
            total_stats["errors"] += 1
            print(f"ERROR {pf}: {stats['error']}", file=sys.stderr)
            continue

        total_stats["functions_found"] += stats.get("functions_found", 0)
        total_stats["functions_injected"] += stats.get("functions_injected", 0)
        total_stats["functions_skipped"] += stats.get("functions_skipped", 0)

        if original == transformed:
            continue

        if args.diff:
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                transformed.splitlines(keepends=True),
                fromfile=f"a/{pf}",
                tofile=f"b/{pf}",
            )
            sys.stdout.writelines(diff)
        elif args.dry_run:
            print(f"# === {pf} ===")
            print(transformed)
        else:
            if args.output_dir:
                out = Path(args.output_dir) / pf.relative_to(
                    path if path.is_dir() else path.parent
                )
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(transformed, encoding="utf-8")
                print(
                    f"INJECTED {pf} -> {out} ({stats['functions_injected']} functions)"
                )
            else:
                backup = pf.with_suffix(pf.suffix + ".pre_inject")
                if not backup.exists():
                    backup.write_text(original, encoding="utf-8")
                pf.write_text(transformed, encoding="utf-8")
                print(
                    f"INJECTED {pf} ({stats['functions_injected']} functions, backup: {backup})"
                )

    return total_stats


def main():
    parser = argparse.ArgumentParser(
        description="AST-based automatic log injection for Python"
    )
    parser.add_argument("path", help="Python file or directory to inject")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print transformed code to stdout"
    )
    parser.add_argument("--diff", action="store_true", help="Show unified diff")
    parser.add_argument(
        "--min-lines", type=int, default=1, help="Skip functions shorter than N lines"
    )
    parser.add_argument(
        "--skip-private",
        action="store_true",
        help="Skip single-underscore private functions",
    )
    parser.add_argument(
        "--output-dir", help="Write transformed files to this directory"
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path} does not exist", file=sys.stderr)
        sys.exit(1)

    stats = process_path(path, args)
    print(f"\n=== INJECTION SUMMARY ===", file=sys.stderr)
    print(f"Files scanned:       {stats['files']}", file=sys.stderr)
    print(f"Functions found:     {stats['functions_found']}", file=sys.stderr)
    print(f"Functions injected:  {stats['functions_injected']}", file=sys.stderr)
    print(f"Functions skipped:   {stats['functions_skipped']}", file=sys.stderr)
    print(f"Errors:              {stats['errors']}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Correlates error lines with git blame to find who introduced bugs and when.

Given a list of file:line references (from crash reports, tracebacks, or grep output),
runs git blame on each and builds a report showing:
- Who last touched each error-relevant line
- When each line was last modified
- The commit that introduced it
- Whether the line was recently changed (potential regression)
- Aggregated author/commit statistics

Usage:
    python3 git_blame_correlator.py <repo_dir> --lines "file.py:42" "other.py:100"
    python3 git_blame_correlator.py <repo_dir> --crash-report /tmp/crash_analysis.json
    python3 git_blame_correlator.py <repo_dir> --traceback /tmp/runner.log
    python3 git_blame_correlator.py . --grep-pattern "TODO|FIXME|HACK|BUG"
"""

import subprocess
import sys
import json
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta

BLAME_RE = re.compile(
    r"^(\^?\w+)\s+"
    r"(?:\((.+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+[+-]\d{4})\s+(\d+)\))"
    r"\s?(.*)"
)

BLAME_PORCELAIN_COMMIT_RE = re.compile(r"^(\w{40})\s+(\d+)\s+(\d+)")


@dataclass
class BlameLine:
    file: str
    line: int
    commit: str
    author: str
    date: str
    code: str
    days_ago: int = 0
    is_recent: bool = False


@dataclass
class BlameReport:
    entries: List[BlameLine] = field(default_factory=list)
    author_counts: Dict[str, int] = field(default_factory=dict)
    commit_counts: Dict[str, int] = field(default_factory=dict)
    recent_changes: List[BlameLine] = field(default_factory=list)
    oldest_entry: Optional[BlameLine] = None
    newest_entry: Optional[BlameLine] = None


def run_git_blame(repo_dir: Path, filepath: str, line: int) -> Optional[BlameLine]:
    rel_path = filepath
    if Path(filepath).is_absolute():
        try:
            rel_path = str(Path(filepath).relative_to(repo_dir))
        except ValueError:
            rel_path = filepath

    full_path = repo_dir / rel_path
    if not full_path.exists():
        return None

    start = max(1, line)
    end = line

    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{start},{end}", "--date=iso", str(rel_path)],
            capture_output=True,
            text=True,
            cwd=str(repo_dir),
            timeout=10,
        )
        if result.returncode != 0:
            return None

        for out_line in result.stdout.splitlines():
            m = BLAME_RE.match(out_line)
            if m:
                commit = m.group(1)
                author = m.group(2).strip()
                date_str = m.group(3).strip()
                code = m.group(5)

                try:
                    dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
                    days_ago = (datetime.now() - dt).days
                except ValueError:
                    days_ago = -1

                return BlameLine(
                    file=rel_path,
                    line=line,
                    commit=commit,
                    author=author,
                    date=date_str,
                    code=code.strip(),
                    days_ago=days_ago,
                    is_recent=days_ago <= 7,
                )

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def parse_file_line_refs(refs: List[str]) -> List[Tuple[str, int]]:
    result = []
    for ref in refs:
        parts = ref.rsplit(":", 1)
        if len(parts) == 2:
            try:
                result.append((parts[0], int(parts[1])))
            except ValueError:
                pass
    return result


def extract_refs_from_traceback(text: str) -> List[Tuple[str, int]]:
    tb_re = re.compile(r'File "(.+?)", line (\d+)')
    return [(m.group(1), int(m.group(2))) for m in tb_re.finditer(text)]


def grep_for_patterns(repo_dir: Path, pattern: str) -> List[Tuple[str, int]]:
    try:
        result = subprocess.run(
            [
                "grep",
                "-rnE",
                pattern,
                "--include=*.py",
                "--include=*.ts",
                "--include=*.js",
                "--include=*.tsx",
                "--include=*.jsx",
                ".",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo_dir),
            timeout=30,
        )
        refs = []
        for line in result.stdout.splitlines()[:200]:
            parts = line.split(":", 2)
            if len(parts) >= 2:
                try:
                    filepath = parts[0].lstrip("./")
                    lineno = int(parts[1])
                    refs.append((filepath, lineno))
                except ValueError:
                    pass
        return refs
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def build_blame_report(
    repo_dir: Path, refs: List[Tuple[str, int]], recent_days: int = 7
) -> BlameReport:
    report = BlameReport()
    author_counter: Counter = Counter()
    commit_counter: Counter = Counter()

    for filepath, line in refs:
        blame = run_git_blame(repo_dir, filepath, line)
        if blame:
            blame.is_recent = blame.days_ago <= recent_days and blame.days_ago >= 0
            report.entries.append(blame)
            author_counter[blame.author] += 1
            commit_counter[blame.commit] += 1
            if blame.is_recent:
                report.recent_changes.append(blame)

    report.author_counts = dict(author_counter.most_common(20))
    report.commit_counts = dict(commit_counter.most_common(20))

    if report.entries:
        valid = [e for e in report.entries if e.days_ago >= 0]
        if valid:
            report.oldest_entry = max(valid, key=lambda e: e.days_ago)
            report.newest_entry = min(valid, key=lambda e: e.days_ago)

    return report


def format_report(report: BlameReport) -> str:
    lines = []
    lines.append("=" * 90)
    lines.append("GIT BLAME CORRELATION REPORT")
    lines.append("=" * 90)
    lines.append(f"Total lines analyzed: {len(report.entries)}")
    lines.append(f"Recent changes (<=7d): {len(report.recent_changes)}")
    lines.append("")

    if report.recent_changes:
        lines.append("--- RECENT CHANGES (potential regressions) ---")
        for bl in sorted(report.recent_changes, key=lambda x: x.days_ago):
            lines.append(
                f"  {bl.days_ago:>3}d ago  {bl.file}:{bl.line:<5}  {bl.author:<20}  {bl.commit[:8]}  {bl.code[:50]}"
            )
        lines.append("")

    lines.append("--- AUTHOR HOTSPOTS ---")
    for author, count in report.author_counts.items():
        lines.append(f"  {count:>4}x  {author}")
    lines.append("")

    lines.append("--- COMMIT HOTSPOTS ---")
    for commit, count in list(report.commit_counts.items())[:15]:
        lines.append(f"  {count:>4}x  {commit}")
    lines.append("")

    lines.append("--- ALL BLAME ENTRIES ---")
    for bl in report.entries:
        marker = " ***RECENT***" if bl.is_recent else ""
        lines.append(
            f"  {bl.file}:{bl.line:<5}  {bl.days_ago:>5}d  {bl.author:<20}  {bl.commit[:8]}  {bl.code[:40]}{marker}"
        )

    lines.append("=" * 90)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Correlate error lines with git blame")
    parser.add_argument("repo_dir", help="Git repository directory")
    parser.add_argument(
        "--lines", nargs="+", help="file:line references (e.g. 'app.py:42')"
    )
    parser.add_argument(
        "--crash-report", help="JSON crash report from crash_analyzer.py"
    )
    parser.add_argument("--traceback", help="Log file containing tracebacks")
    parser.add_argument(
        "--grep-pattern", help="Grep pattern to find lines (e.g. 'TODO|FIXME')"
    )
    parser.add_argument(
        "--recent-days", type=int, default=7, help="Days threshold for 'recent'"
    )
    parser.add_argument("--format", choices=["json", "report"], default="report")
    args = parser.parse_args()

    repo_dir = Path(args.repo_dir).resolve()
    refs: List[Tuple[str, int]] = []

    if args.lines:
        refs = parse_file_line_refs(args.lines)
    elif args.crash_report:
        data = json.loads(Path(args.crash_report).read_text())
        for crash in data.get("crashes", []):
            for frame in crash.get("frames", []):
                refs.append((frame["file"], frame["line"]))
    elif args.traceback:
        text = Path(args.traceback).read_text(errors="replace")
        refs = extract_refs_from_traceback(text)
    elif args.grep_pattern:
        refs = grep_for_patterns(repo_dir, args.grep_pattern)
    else:
        parser.print_help()
        sys.exit(1)

    if not refs:
        print("No file:line references found.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(refs)} references...", file=sys.stderr)
    report = build_blame_report(repo_dir, refs, args.recent_days)

    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, default=str))
    else:
        print(format_report(report))


if __name__ == "__main__":
    main()

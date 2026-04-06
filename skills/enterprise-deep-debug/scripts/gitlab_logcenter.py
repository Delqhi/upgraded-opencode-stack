#!/usr/bin/env python3
"""
GitLab LogCenter Manager - Enterprise Deep Debug Skill
=====================================================
Infinite-capacity log storage via auto-rotating private GitLab repos.

Architecture:
  Each project gets: <project>-logcenter-001, -002, -003, ...
  Auto-rotates when a repo approaches the storage limit (default 9GB).
  All logs, screenshots, videos, reports go to GitLab instead of local disk.
  Every A2A agent can read/write via this script.

Usage:
  gitlab_logcenter.py init      --project <name>
  gitlab_logcenter.py upload    --project <name> --file <path> [--category logs|video|screenshots|browser|reports] [--tags t1,t2] [--description "..."]
  gitlab_logcenter.py upload    --project <name> --stdin --name <filename> [--category ...]
  gitlab_logcenter.py status    --project <name>
  gitlab_logcenter.py search    --project <name> --query <text>
  gitlab_logcenter.py list      --project <name> [--category <cat>] [--date YYYY-MM-DD]
  gitlab_logcenter.py rotate    --project <name>
  gitlab_logcenter.py download  --project <name> --path <repo_path> --output <local_path>
  gitlab_logcenter.py get-active --project <name>

Environment:
  GITLAB_LOGCENTER_TOKEN     GitLab API token (REQUIRED - store in SIN-Passwordmanager!)
  GITLAB_LOGCENTER_URL       GitLab API base (default: https://gitlab.com/api/v4)
  GITLAB_LOGCENTER_LIMIT_GB  Storage limit per repo in GB before rotation (default: 9)
  GITLAB_LOGCENTER_NS        Namespace/group ID or path (optional, personal ns by default)
"""

import argparse
import base64
import datetime
import hashlib
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_API_URL = "https://gitlab.com/api/v4"
DEFAULT_LIMIT_GB = 9  # user claims 10GB free/project; 9GB gives safety margin
CHUNK_SIZE = 30 * 1024 * 1024  # 30 MB per API commit (base64 inflates ~33%)
CATEGORIES = ("logs", "video", "screenshots", "browser", "reports", "misc")
VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ts_short() -> str:
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def _date_dir() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _guess_mime(filepath: str) -> str:
    mt, _ = mimetypes.guess_type(filepath)
    return mt or "application/octet-stream"


def _env(key: str, default: str = "") -> str:
    """Read env var, also check ~/.config/opencode/gitlab_logcenter.env"""
    val = os.environ.get(key, "")
    if val:
        return val
    env_file = os.path.expanduser("~/.config/opencode/gitlab_logcenter.env")
    if os.path.isfile(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    return default


# ---------------------------------------------------------------------------
# GitLab API Client
# ---------------------------------------------------------------------------


class GitLabAPI:
    """Thin wrapper around GitLab REST API v4 using only stdlib."""

    def __init__(self, token: str, base_url: str = DEFAULT_API_URL):
        self.token = token
        self.base_url = base_url.rstrip("/")
        if not self.token:
            raise RuntimeError(
                "GITLAB_LOGCENTER_TOKEN not set. "
                "Set env var or create ~/.config/opencode/gitlab_logcenter.env"
            )

    # -- low level ---------------------------------------------------------

    def _req(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        params: dict | None = None,
        raw_response: bool = False,
    ) -> dict | bytes | list:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("PRIVATE-TOKEN", self.token)
        if body:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
                if raw_response:
                    return raw
                if not raw:
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitLab API {method} {path} -> {e.code}: {err_body}"
            ) from e

    def get(self, path, **kw):
        return self._req("GET", path, **kw)

    def post(self, path, data=None, **kw):
        return self._req("POST", path, data=data, **kw)

    def put(self, path, data=None, **kw):
        return self._req("PUT", path, data=data, **kw)

    def delete(self, path, **kw):
        return self._req("DELETE", path, **kw)

    # -- projects ----------------------------------------------------------

    def create_project(
        self, name: str, description: str = "", namespace_id: int | None = None
    ) -> dict:
        payload: dict = {
            "name": name,
            "visibility": "private",
            "description": description,
            "initialize_with_readme": True,
            "default_branch": "main",
        }
        if namespace_id:
            payload["namespace_id"] = namespace_id
        return self.post("/projects", data=payload)

    def find_projects(self, search: str, owned: bool = True) -> list:
        params = {
            "search": search,
            "owned": str(owned).lower(),
            "per_page": "100",
            "order_by": "name",
            "sort": "asc",
        }
        return self.get("/projects", params=params)

    def get_project(self, project_id: int, statistics: bool = False) -> dict:
        params = {}
        if statistics:
            params["statistics"] = "true"
        return self.get(f"/projects/{project_id}", params=params)

    # -- commits / files ---------------------------------------------------

    def create_commit(
        self, project_id: int, branch: str, message: str, actions: list[dict]
    ) -> dict:
        return self.post(
            f"/projects/{project_id}/repository/commits",
            data={
                "branch": branch,
                "commit_message": message,
                "actions": actions,
            },
        )

    def get_tree(
        self,
        project_id: int,
        path: str = "",
        recursive: bool = False,
        per_page: int = 100,
        page: int = 1,
    ) -> list:
        params = {"per_page": str(per_page), "page": str(page)}
        if path:
            params["path"] = path
        if recursive:
            params["recursive"] = "true"
        return self.get(f"/projects/{project_id}/repository/tree", params=params)

    def get_file(self, project_id: int, file_path: str, ref: str = "main") -> dict:
        encoded = urllib.parse.quote(file_path, safe="")
        return self.get(
            f"/projects/{project_id}/repository/files/{encoded}", params={"ref": ref}
        )

    def get_file_raw(self, project_id: int, file_path: str, ref: str = "main") -> bytes:
        encoded = urllib.parse.quote(file_path, safe="")
        return self.get(
            f"/projects/{project_id}/repository/files/{encoded}/raw",
            params={"ref": ref},
            raw_response=True,
        )

    def search_blobs(self, project_id: int, query: str, per_page: int = 20) -> list:
        return self.get(
            f"/projects/{project_id}/search",
            params={"scope": "blobs", "search": query, "per_page": str(per_page)},
        )


# ---------------------------------------------------------------------------
# LogCenter Manager
# ---------------------------------------------------------------------------


class LogCenter:
    """Manages the lifecycle of logcenter repos for a project."""

    def __init__(
        self,
        api: GitLabAPI,
        project_name: str,
        limit_gb: float = DEFAULT_LIMIT_GB,
        namespace_id: int | None = None,
    ):
        self.api = api
        self.project_name = project_name
        self.limit_bytes = int(limit_gb * 1024 * 1024 * 1024)
        self.namespace_id = namespace_id
        self._cache_repos: list[dict] | None = None

    # -- repo discovery ----------------------------------------------------

    def _repo_prefix(self) -> str:
        return f"{self.project_name}-logcenter-"

    def _parse_number(self, name: str) -> int | None:
        m = re.search(r"-logcenter-(\d{3,})$", name)
        return int(m.group(1)) if m else None

    def list_repos(self, force_refresh: bool = False) -> list[dict]:
        if self._cache_repos is not None and not force_refresh:
            return self._cache_repos
        prefix = self._repo_prefix()
        all_projects = self.api.find_projects(prefix)
        repos = []
        for p in all_projects:
            if p.get("name", "").startswith(prefix):
                num = self._parse_number(p["name"])
                if num is not None:
                    repos.append({**p, "_lc_number": num})
        repos.sort(key=lambda r: r["_lc_number"])
        self._cache_repos = repos
        return repos

    def get_active_repo(self) -> dict | None:
        repos = self.list_repos()
        return repos[-1] if repos else None

    def _next_number(self) -> int:
        repos = self.list_repos()
        if not repos:
            return 1
        return repos[-1]["_lc_number"] + 1

    # -- storage -----------------------------------------------------------

    def check_storage(self, repo: dict) -> dict:
        proj = self.api.get_project(repo["id"], statistics=True)
        stats = proj.get("statistics", {})
        used = stats.get("repository_size", 0) + stats.get("lfs_objects_size", 0)
        return {
            "project_id": repo["id"],
            "name": repo["name"],
            "repository_size": stats.get("repository_size", 0),
            "lfs_objects_size": stats.get("lfs_objects_size", 0),
            "total_used": used,
            "limit": self.limit_bytes,
            "usage_pct": round(used / self.limit_bytes * 100, 2)
            if self.limit_bytes
            else 0,
            "needs_rotation": used >= self.limit_bytes,
        }

    # -- init / rotate -----------------------------------------------------

    def init(self) -> dict:
        repos = self.list_repos(force_refresh=True)
        if repos:
            active = repos[-1]
            print(
                f"[logcenter] Already initialized: {active['name']} (#{active['_lc_number']})"
            )
            return active
        return self._create_repo(1)

    def rotate(self) -> dict:
        num = self._next_number()
        print(f"[logcenter] Rotating to {self._repo_prefix()}{num:03d}")
        repo = self._create_repo(num)
        self._cache_repos = None  # invalidate cache
        return repo

    def _create_repo(self, number: int) -> dict:
        name = f"{self._repo_prefix()}{number:03d}"
        desc = (
            f"LogCenter #{number} for project '{self.project_name}'. "
            f"Auto-managed by enterprise-deep-debug skill. "
            f"Created: {_ts()}"
        )
        print(f"[logcenter] Creating GitLab repo: {name}")
        proj = self.api.create_project(
            name, description=desc, namespace_id=self.namespace_id
        )
        # Wait for repo to be ready
        time.sleep(2)
        # Update README with logcenter info
        readme_content = (
            f"# {name}\n\n"
            f"**LogCenter** for project `{self.project_name}` (volume #{number})\n\n"
            f"Auto-managed by `enterprise-deep-debug` skill.\n\n"
            f"## Directory Structure\n"
            f"```\n"
            f"logs/          - Application logs, crash logs, runner logs\n"
            f"video/         - Screen recordings, CDP screencast captures\n"
            f"screenshots/   - Browser screenshots, UI captures\n"
            f"browser/       - CDP console, network, performance logs\n"
            f"reports/       - Crash analysis, RCA reports, coverage reports\n"
            f"misc/          - Other artifacts\n"
            f"```\n\n"
            f"## Storage\n"
            f"- Limit: {self.limit_bytes / (1024**3):.1f} GB per volume\n"
            f"- When full, auto-rotates to `{self._repo_prefix()}{number + 1:03d}`\n\n"
            f"Created: {_ts()}\n"
        )
        try:
            self.api.create_commit(
                proj["id"],
                "main",
                f"[logcenter] Initialize {name}",
                [
                    {
                        "action": "update",
                        "file_path": "README.md",
                        "content": readme_content,
                    },
                ],
            )
        except Exception as e:
            print(f"[logcenter] Warning: Could not update README: {e}")
        proj["_lc_number"] = number
        print(f"[logcenter] Created: {name} (id={proj['id']})")
        return proj

    # -- ensure active (auto-rotate if needed) -----------------------------

    def ensure_active(self) -> dict:
        repo = self.get_active_repo()
        if repo is None:
            return self.init()
        storage = self.check_storage(repo)
        if storage["needs_rotation"]:
            print(
                f"[logcenter] Repo {repo['name']} is {storage['usage_pct']:.1f}% full, rotating..."
            )
            return self.rotate()
        return repo

    # -- upload ------------------------------------------------------------

    def upload_file(
        self,
        filepath: str,
        category: str = "logs",
        tags: list[str] | None = None,
        description: str = "",
        custom_name: str | None = None,
    ) -> dict:
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        repo = self.ensure_active()
        file_size = os.path.getsize(filepath)
        filename = custom_name or os.path.basename(filepath)
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
        ts = _ts_short()
        date_dir = _date_dir()
        repo_path = f"{category}/{date_dir}/{ts}_{safe_name}"
        meta_path = f"{category}/{date_dir}/{ts}_{safe_name}.meta.json"

        with open(filepath, "rb") as f:
            file_data = f.read()

        checksum = _sha256(file_data)
        mime = _guess_mime(filepath)

        meta = {
            "uploaded_at": _ts(),
            "category": category,
            "original_name": filename,
            "original_path": os.path.abspath(filepath),
            "repo_path": repo_path,
            "size_bytes": file_size,
            "checksum_sha256": checksum,
            "content_type": mime,
            "tags": tags or [],
            "description": description,
            "agent": os.environ.get("AGENT_NAME", "unknown"),
            "project": self.project_name,
            "logcenter": repo["name"],
            "logcenter_number": repo.get("_lc_number", 0),
        }

        if file_size <= CHUNK_SIZE:
            # Single commit
            b64 = base64.b64encode(file_data).decode("ascii")
            actions = [
                {
                    "action": "create",
                    "file_path": repo_path,
                    "content": b64,
                    "encoding": "base64",
                },
                {
                    "action": "create",
                    "file_path": meta_path,
                    "content": json.dumps(meta, indent=2),
                },
            ]
            commit_msg = f"[logcenter] {category}: {safe_name} ({file_size} bytes)"
            self.api.create_commit(repo["id"], "main", commit_msg, actions)
            print(f"[logcenter] Uploaded: {repo_path} ({file_size} bytes)")
        else:
            # Chunked upload for large files
            print(f"[logcenter] Large file ({file_size} bytes), chunking...")
            chunk_count = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
            parts = []
            for i in range(chunk_count):
                start = i * CHUNK_SIZE
                end = min(start + CHUNK_SIZE, file_size)
                chunk = file_data[start:end]
                part_path = f"{repo_path}.part{i + 1:03d}"
                b64 = base64.b64encode(chunk).decode("ascii")
                actions = [
                    {
                        "action": "create",
                        "file_path": part_path,
                        "content": b64,
                        "encoding": "base64",
                    },
                ]
                commit_msg = (
                    f"[logcenter] {category}: {safe_name} part {i + 1}/{chunk_count}"
                )
                self.api.create_commit(repo["id"], "main", commit_msg, actions)
                parts.append({"part": i + 1, "path": part_path, "size": end - start})
                print(f"  Part {i + 1}/{chunk_count}: {end - start} bytes")

                # Check if we need rotation mid-upload
                if i < chunk_count - 1:
                    storage = self.check_storage(repo)
                    if storage["needs_rotation"]:
                        print("[logcenter] Mid-upload rotation needed!")
                        repo = self.rotate()

            # Upload manifest + metadata
            meta["chunks"] = parts
            meta["chunk_count"] = chunk_count
            manifest_path = f"{repo_path}.manifest.json"
            self.api.create_commit(
                repo["id"],
                "main",
                f"[logcenter] {category}: {safe_name} manifest",
                [
                    {
                        "action": "create",
                        "file_path": manifest_path,
                        "content": json.dumps(meta, indent=2),
                    },
                    {
                        "action": "create",
                        "file_path": meta_path,
                        "content": json.dumps(meta, indent=2),
                    },
                ],
            )
            print(
                f"[logcenter] Uploaded (chunked): {repo_path} ({file_size} bytes, {chunk_count} parts)"
            )

        return meta

    def upload_bytes(
        self,
        data: bytes,
        name: str,
        category: str = "logs",
        tags: list[str] | None = None,
        description: str = "",
    ) -> dict:
        """Upload raw bytes without a local file."""
        repo = self.ensure_active()
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
        ts = _ts_short()
        date_dir = _date_dir()
        repo_path = f"{category}/{date_dir}/{ts}_{safe_name}"
        meta_path = f"{category}/{date_dir}/{ts}_{safe_name}.meta.json"

        checksum = _sha256(data)
        mime = _guess_mime(name)

        meta = {
            "uploaded_at": _ts(),
            "category": category,
            "original_name": name,
            "original_path": "stdin" if not hasattr(data, "name") else "",
            "repo_path": repo_path,
            "size_bytes": len(data),
            "checksum_sha256": checksum,
            "content_type": mime,
            "tags": tags or [],
            "description": description,
            "agent": os.environ.get("AGENT_NAME", "unknown"),
            "project": self.project_name,
            "logcenter": repo["name"],
        }

        if len(data) <= CHUNK_SIZE:
            b64 = base64.b64encode(data).decode("ascii")
            self.api.create_commit(
                repo["id"],
                "main",
                f"[logcenter] {category}: {safe_name}",
                [
                    {
                        "action": "create",
                        "file_path": repo_path,
                        "content": b64,
                        "encoding": "base64",
                    },
                    {
                        "action": "create",
                        "file_path": meta_path,
                        "content": json.dumps(meta, indent=2),
                    },
                ],
            )
        else:
            # chunk the bytes
            chunk_count = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
            parts = []
            for i in range(chunk_count):
                start = i * CHUNK_SIZE
                end = min(start + CHUNK_SIZE, len(data))
                chunk = data[start:end]
                part_path = f"{repo_path}.part{i + 1:03d}"
                b64 = base64.b64encode(chunk).decode("ascii")
                self.api.create_commit(
                    repo["id"],
                    "main",
                    f"[logcenter] {category}: {safe_name} part {i + 1}/{chunk_count}",
                    [
                        {
                            "action": "create",
                            "file_path": part_path,
                            "content": b64,
                            "encoding": "base64",
                        },
                    ],
                )
                parts.append({"part": i + 1, "path": part_path, "size": end - start})
            meta["chunks"] = parts
            meta["chunk_count"] = chunk_count
            self.api.create_commit(
                repo["id"],
                "main",
                f"[logcenter] {category}: {safe_name} manifest",
                [
                    {
                        "action": "create",
                        "file_path": f"{repo_path}.manifest.json",
                        "content": json.dumps(meta, indent=2),
                    },
                    {
                        "action": "create",
                        "file_path": meta_path,
                        "content": json.dumps(meta, indent=2),
                    },
                ],
            )

        print(f"[logcenter] Uploaded: {repo_path} ({len(data)} bytes)")
        return meta

    # -- status ------------------------------------------------------------

    def status(self) -> dict:
        repos = self.list_repos(force_refresh=True)
        if not repos:
            return {
                "project": self.project_name,
                "initialized": False,
                "repos": [],
                "total_repos": 0,
            }

        repo_infos = []
        total_used = 0
        for r in repos:
            try:
                st = self.check_storage(r)
                repo_infos.append(st)
                total_used += st["total_used"]
            except Exception as e:
                repo_infos.append({"name": r["name"], "error": str(e)})

        active = repos[-1]
        return {
            "project": self.project_name,
            "initialized": True,
            "active_repo": active["name"],
            "active_repo_id": active["id"],
            "total_repos": len(repos),
            "total_used_bytes": total_used,
            "total_used_human": _human_size(total_used),
            "repos": repo_infos,
        }

    # -- search ------------------------------------------------------------

    def search(self, query: str, max_results: int = 50) -> list:
        repos = self.list_repos()
        results = []
        for r in repos:
            try:
                hits = self.api.search_blobs(r["id"], query, per_page=20)
                for h in hits:
                    results.append(
                        {
                            "repo": r["name"],
                            "path": h.get("path", ""),
                            "filename": h.get("filename", ""),
                            "data": h.get("data", "")[:500],  # truncate
                            "startline": h.get("startline", 0),
                        }
                    )
                    if len(results) >= max_results:
                        break
            except Exception:
                pass
            if len(results) >= max_results:
                break
        return results

    # -- list --------------------------------------------------------------

    def list_entries(
        self,
        category: str | None = None,
        date: str | None = None,
        repo_name: str | None = None,
    ) -> list:
        repos = self.list_repos()
        if repo_name:
            repos = [r for r in repos if r["name"] == repo_name]

        entries = []
        for r in repos:
            try:
                path = ""
                if category:
                    path = category
                    if date:
                        path = f"{category}/{date}"
                tree = self.api.get_tree(
                    r["id"], path=path, recursive=True, per_page=100
                )
                for item in tree:
                    if item.get("type") == "blob" and not item["name"].endswith(
                        ".meta.json"
                    ):
                        entries.append(
                            {
                                "repo": r["name"],
                                "repo_id": r["id"],
                                "path": item["path"],
                                "name": item["name"],
                            }
                        )
            except Exception:
                pass
        return entries

    # -- download ----------------------------------------------------------

    def download(
        self, repo_path: str, output_path: str, repo_name: str | None = None
    ) -> str:
        repos = self.list_repos()
        if repo_name:
            repos = [r for r in repos if r["name"] == repo_name]

        for r in repos:
            try:
                raw = self.api.get_file_raw(r["id"], repo_path)
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(raw)
                print(f"[logcenter] Downloaded: {repo_path} -> {output_path}")
                return output_path
            except Exception:
                continue
        raise FileNotFoundError(f"File not found in any logcenter repo: {repo_path}")


def _human_size(nbytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


# ---------------------------------------------------------------------------
# Python API for other scripts (import-friendly)
# ---------------------------------------------------------------------------


def get_logcenter(project_name: str) -> LogCenter:
    """Factory: create a LogCenter instance from environment."""
    token = _env("GITLAB_LOGCENTER_TOKEN")
    base_url = _env("GITLAB_LOGCENTER_URL", DEFAULT_API_URL)
    limit_gb = float(_env("GITLAB_LOGCENTER_LIMIT_GB", str(DEFAULT_LIMIT_GB)))
    ns_raw = _env("GITLAB_LOGCENTER_NS", "")
    ns_id = int(ns_raw) if ns_raw.isdigit() else None
    api = GitLabAPI(token, base_url)
    return LogCenter(api, project_name, limit_gb=limit_gb, namespace_id=ns_id)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        prog="gitlab_logcenter",
        description="GitLab LogCenter - infinite log storage via auto-rotating repos",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize logcenter for a project")
    p_init.add_argument("--project", required=True, help="Project name")

    # upload
    p_up = sub.add_parser("upload", help="Upload a file to logcenter")
    p_up.add_argument("--project", required=True)
    p_up.add_argument("--file", help="Local file path")
    p_up.add_argument("--stdin", action="store_true", help="Read from stdin")
    p_up.add_argument("--name", help="Filename (required with --stdin)")
    p_up.add_argument("--category", default="logs", choices=CATEGORIES)
    p_up.add_argument("--tags", default="", help="Comma-separated tags")
    p_up.add_argument("--description", default="")

    # status
    p_st = sub.add_parser("status", help="Show logcenter status")
    p_st.add_argument("--project", required=True)
    p_st.add_argument("--json", action="store_true", help="Output as JSON")

    # search
    p_sr = sub.add_parser("search", help="Search across logcenter repos")
    p_sr.add_argument("--project", required=True)
    p_sr.add_argument("--query", required=True)
    p_sr.add_argument("--max", type=int, default=50)

    # list
    p_ls = sub.add_parser("list", help="List logcenter entries")
    p_ls.add_argument("--project", required=True)
    p_ls.add_argument("--category", choices=CATEGORIES)
    p_ls.add_argument("--date", help="Filter by date YYYY-MM-DD")
    p_ls.add_argument("--repo", help="Filter by specific repo name")

    # rotate
    p_rot = sub.add_parser("rotate", help="Force rotate to new logcenter repo")
    p_rot.add_argument("--project", required=True)

    # download
    p_dl = sub.add_parser("download", help="Download a file from logcenter")
    p_dl.add_argument("--project", required=True)
    p_dl.add_argument("--path", required=True, help="File path in repo")
    p_dl.add_argument("--output", required=True, help="Local output path")
    p_dl.add_argument("--repo", help="Specific repo name")

    # get-active
    p_ga = sub.add_parser("get-active", help="Print the active logcenter repo name/id")
    p_ga.add_argument("--project", required=True)

    args = parser.parse_args()
    lc = get_logcenter(args.project)

    if args.command == "init":
        repo = lc.init()
        print(
            json.dumps(
                {
                    "name": repo["name"],
                    "id": repo["id"],
                    "web_url": repo.get("web_url", ""),
                },
                indent=2,
            )
        )

    elif args.command == "upload":
        tags = (
            [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        )
        if args.stdin:
            if not args.name:
                parser.error("--name required with --stdin")
            data = sys.stdin.buffer.read()
            meta = lc.upload_bytes(
                data,
                args.name,
                category=args.category,
                tags=tags,
                description=args.description,
            )
        elif args.file:
            meta = lc.upload_file(
                args.file,
                category=args.category,
                tags=tags,
                description=args.description,
            )
        else:
            parser.error("--file or --stdin required")
        print(json.dumps(meta, indent=2))

    elif args.command == "status":
        st = lc.status()
        if getattr(args, "json", False):
            print(json.dumps(st, indent=2))
        else:
            if not st["initialized"]:
                print(
                    f"[logcenter] Project '{args.project}' not initialized. Run: gitlab_logcenter.py init --project {args.project}"
                )
            else:
                print(f"Project:      {st['project']}")
                print(f"Active Repo:  {st['active_repo']}")
                print(f"Total Repos:  {st['total_repos']}")
                print(f"Total Used:   {st['total_used_human']}")
                print()
                for r in st["repos"]:
                    if "error" in r:
                        print(f"  {r['name']}: ERROR - {r['error']}")
                    else:
                        print(
                            f"  {r['name']}: {_human_size(r['total_used'])} / {_human_size(r['limit'])} ({r['usage_pct']}%)"
                        )

    elif args.command == "search":
        results = lc.search(args.query, max_results=args.max)
        if not results:
            print(f"[logcenter] No results for '{args.query}'")
        else:
            for r in results:
                print(f"\n--- {r['repo']} :: {r['path']} (line {r['startline']}) ---")
                print(r["data"])

    elif args.command == "list":
        entries = lc.list_entries(
            category=args.category, date=args.date, repo_name=args.repo
        )
        if not entries:
            print("[logcenter] No entries found")
        else:
            for e in entries:
                print(f"  [{e['repo']}] {e['path']}")

    elif args.command == "rotate":
        repo = lc.rotate()
        print(
            json.dumps(
                {
                    "name": repo["name"],
                    "id": repo["id"],
                    "web_url": repo.get("web_url", ""),
                },
                indent=2,
            )
        )

    elif args.command == "download":
        lc.download(args.path, args.output, repo_name=args.repo)

    elif args.command == "get-active":
        repo = lc.get_active_repo()
        if repo:
            print(
                json.dumps(
                    {
                        "name": repo["name"],
                        "id": repo["id"],
                        "web_url": repo.get("web_url", ""),
                        "number": repo.get("_lc_number", 0),
                    },
                    indent=2,
                )
            )
        else:
            print("[logcenter] Not initialized")
            sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GitLab Storage Manager — Extended from gitlab_logcenter.py
===========================================================
Unendlicher Speicher via GitLab-Repos für die gesamte SIN-Flotte.

Erweitert gitlab_logcenter.py um:
- Machine-Links (OCI VM, HF VMs, Mac)
- Storage-Register (WAS liegt WO und WARUM)
- Auto-Cleanup für alte Dateien
- Batch-Upload für ganze Verzeichnisse
- Docker-Image Export/Upload

Usage:
  gitlab_storage_manager.py init         --project <name> [--visibility private|public]
  gitlab_storage_manager.py upload       --project <name> --file <pfad> [--category <kat>]
  gitlab_storage_manager.py upload-dir   --project <name> --dir <pfad> [--category <kat>]
  gitlab_storage_manager.py status       --project <name> [--json]
  gitlab_storage_manager.py search       --project <name> --query <text>
  gitlab_storage_manager.py list         --project <name> [--category <kat>]
  gitlab_storage_manager.py download     --project <name> --path <repo_pfad> --output <lokal>
  gitlab_storage_manager.py rotate       --project <name>
  gitlab_storage_manager.py get-active   --project <name>
  gitlab_storage_manager.py register     --project <name> --purpose <zweck> [--machine <host>]
  gitlab_storage_manager.py link-machine --machine <host> --project <name> --sync-dir <local_dir>
  gitlab_storage_manager.py cleanup      --project <name> --older-than <days>
  gitlab_storage_manager.py migrate      --project <name> --from-dir <pfad> [--dry-run]

Environment:
  GITLAB_LOGCENTER_TOKEN     GitLab API token (REQUIRED)
  GITLAB_LOGCENTER_URL       GitLab API base (default: https://gitlab.com/api/v4)
  GITLAB_STORAGE_LIMIT_GB    Storage limit per repo in GB before rotation (default: 9)
"""

import argparse
import datetime
import json
import os
import sys
import time

# Add parent directory to path so we can import gitlab_logcenter
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PARENT_DIR, "enterprise-deep-debug", "scripts"))

# Import existing LogCenter
_import_paths = [
    os.path.expanduser("~/.config/opencode/skills/enterprise-deep-debug/scripts"),
    os.path.join(PARENT_DIR, "enterprise-deep-debug", "scripts"),
]
for _ip in _import_paths:
    if _ip not in sys.path:
        sys.path.insert(0, _ip)

try:
    from gitlab_logcenter import (
        LogCenter,
        GitLabAPI,
        _env,
        _ts,
        _ts_short,
        _date_dir,
        _sha256,
        _human_size,
        DEFAULT_API_URL,
        DEFAULT_LIMIT_GB,
        get_logcenter,
        CATEGORIES,
    )
except ImportError:
    print(
        "[ERROR] gitlab_logcenter.py not found. Ensure enterprise-deep-debug skill is installed."
    )
    sys.exit(1)

# Extended categories beyond logcenter
EXTENDED_CATEGORIES = tuple(
    list(CATEGORIES) + ["docker-images", "backups", "agent-artifacts"]
)
STORAGE_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(STORAGE_SKILL_DIR, "config")
REGISTRY_FILE = os.path.join(CONFIG_DIR, "storage-registry.json")
MACHINE_LINKS_FILE = os.path.join(CONFIG_DIR, "machine-links.json")


# ---------------------------------------------------------------------------
# Storage Registry Manager
# ---------------------------------------------------------------------------


class StorageRegistry:
    """Manages the storage-registry.json — knows WAS liegt WO und WARUM."""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.registry = self._load()

    def _load(self) -> list:
        if os.path.isfile(REGISTRY_FILE):
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(self.registry, f, indent=2)

    def register(
        self,
        project: str,
        repo_name: str,
        repo_id: int,
        visibility: str,
        purpose: str,
        owner_machine: str,
        categories: list[str],
    ):
        """Register a storage repo in the registry."""
        entry = {
            "project": project,
            "repo_name": repo_name,
            "repo_id": repo_id,
            "visibility": visibility,
            "purpose": purpose,
            "owner_machine": owner_machine,
            "categories": categories,
            "created_at": _ts(),
            "size_limit_gb": 9,
            "current_size_gb": 0,
            "files_count": 0,
        }
        # Update if exists
        for i, e in enumerate(self.registry):
            if e["repo_name"] == repo_name:
                self.registry[i] = entry
                self._save()
                return entry
        self.registry.append(entry)
        self.register(
            project="unknown",
            repo_name=repo_name,
            repo_id=0,
            visibility="private",
            purpose="Auto-registered",
            owner_machine="unknown",
            categories=["misc"],
        )


# ---------------------------------------------------------------------------
# Machine Links Manager
# ---------------------------------------------------------------------------


class MachineLinks:
    """Manages machine-links.json — welche Maschine nutzt welche Repos."""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.links = self._load()

    def _load(self) -> dict:
        if os.path.isfile(MACHINE_LINKS_FILE):
            with open(MACHINE_LINKS_FILE, "r") as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(MACHINE_LINKS_FILE, "w") as f:
            json.dump(self.links, f, indent=2)

    def link_machine(
        self, machine: str, project: str, sync_dir: str, category: str = "misc"
    ):
        """Link a machine's directory to a storage project."""
        if machine not in self.links:
            self.links[machine] = {"projects": [], "sync_dirs": {}}
        if project not in self.links[machine]["projects"]:
            self.links[machine]["projects"].append(project)
        self.links[machine]["sync_dirs"][sync_dir] = category
        self._save()
        return self.links[machine]

    def get_machine(self, machine: str) -> dict:
        return self.links.get(machine, {})

    def get_all(self) -> dict:
        return self.links


# ---------------------------------------------------------------------------
# Extended Storage Manager (builds on LogCenter)
# ---------------------------------------------------------------------------


class GitLabStorageManager(LogCenter):
    """Extended LogCenter with storage registry, machine links, batch ops."""

    def __init__(
        self,
        api: GitLabAPI,
        project_name: str,
        limit_gb: float = DEFAULT_LIMIT_GB,
        namespace_id: int | None = None,
        visibility: str = "private",
    ):
        super().__init__(api, project_name, limit_gb, namespace_id)
        self.visibility = visibility
        self.registry = StorageRegistry()
        self.machine_links = MachineLinks()

    def ensure_active(self) -> dict:
        """Ensure active repo, auto-register in storage registry."""
        repo = super().ensure_active()
        self.registry.register(
            project=self.project_name,
            repo_name=repo["name"],
            repo_id=repo["id"],
            visibility=self.visibility,
            purpose=f"Storage for {self.project_name}",
            owner_machine=_env("HOSTNAME", "unknown"),
            categories=list(EXTENDED_CATEGORIES),
        )
        return repo

    def _create_repo(self, number: int) -> dict:
        """Override to create with configurable visibility."""
        name = f"{self._repo_prefix()}{number:03d}"
        desc = (
            f"Storage #{number} for project '{self.project_name}'. "
            f"Auto-managed by gitlab-storage skill. "
            f"Created: {_ts()}"
        )
        print(
            f"[gitlab-storage] Creating GitLab repo: {name} (visibility={self.visibility})"
        )

        payload = {
            "name": name,
            "visibility": self.visibility,
            "description": desc,
            "initialize_with_readme": True,
            "default_branch": "main",
        }
        if self.namespace_id:
            payload["namespace_id"] = self.namespace_id

        proj = self.api.post("/projects", data=payload)
        time.sleep(2)

        readme = (
            f"# {name}\n\n"
            f"**Storage** for project `{self.project_name}` (volume #{number})\n\n"
            f"Managed by `gitlab-storage` skill.\n\n"
            f"## Categories\n"
            f"```\n"
            f"logs/            - Application and system logs\n"
            f"video/           - Screen recordings, CDP screencasts\n"
            f"screenshots/     - Browser and UI screenshots\n"
            f"browser/         - CDP console, network, performance logs\n"
            f"reports/         - Crash analysis, RCA reports\n"
            f"docker-images/   - Exported Docker images\n"
            f"backups/         - Database and config backups\n"
            f"agent-artifacts/ - Agent build outputs, test results\n"
            f"misc/            - Other files\n"
            f"```\n\n"
            f"## Storage\n"
            f"- Limit: {self.limit_bytes / (1024**3):.1f} GB per volume\n"
            f"- Auto-rotates to `{self._repo_prefix()}{number + 1:03d}` when full\n\n"
            f"Created: {_ts()}\n"
        )
        try:
            self.api.create_commit(
                proj["id"],
                "main",
                f"[storage] Initialize {name}",
                [{"action": "update", "file_path": "README.md", "content": readme}],
            )
        except Exception as e:
            print(f"[gitlab-storage] Warning: Could not update README: {e}")

        proj["_lc_number"] = number
        print(
            f"[gitlab-storage] Created: {name} (id={proj['id']}, visibility={self.visibility})"
        )
        return proj

    def upload_file(
        self,
        filepath: str,
        category: str = "logs",
        tags: list[str] | None = None,
        description: str = "",
    ) -> dict:
        """Upload file with auto-registration."""
        if category not in EXTENDED_CATEGORIES:
            print(
                f"[gitlab-storage] Warning: Unknown category '{category}', using 'misc'"
            )
            category = "misc"
        meta = super().upload_file(filepath, category, tags, description)
        repo = self.get_active_repo()
        if repo:
            self.registry.register(
                project=self.project_name,
                repo_name=repo["name"],
                repo_id=repo["id"],
                visibility=self.visibility,
                purpose=f"Storage for {self.project_name}",
                owner_machine=_env("HOSTNAME", "unknown"),
                categories=list(EXTENDED_CATEGORIES),
            )
        return meta

    def upload_directory(
        self,
        dirpath: str,
        category: str = "misc",
        tags: list[str] | None = None,
        description: str = "",
        exclude_patterns: list[str] | None = None,
    ) -> list:
        """Upload all files in a directory recursively."""
        if not os.path.isdir(dirpath):
            raise NotADirectoryError(f"Directory not found: {dirpath}")

        uploaded = []
        exclude = exclude_patterns or [".git", "node_modules", "__pycache__", ".venv"]

        for root, dirs, files in os.walk(dirpath):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in exclude]
            for fname in files:
                fpath = os.path.join(root, fname)
                if any(pat in fpath for pat in exclude):
                    continue
                try:
                    meta = self.upload_file(fpath, category, tags, description)
                    uploaded.append(meta)
                except Exception as e:
                    print(f"[gitlab-storage] Warning: Failed to upload {fpath}: {e}")

        print(f"[gitlab-storage] Uploaded {len(uploaded)} files from {dirpath}")
        return uploaded

    def cleanup_old_files(self, days: int, category: str | None = None) -> list:
        """Find files older than N days."""
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime(
            "%Y-%m-%d"
        )
        entries = self.list_entries(category=category)
        old = []
        for e in entries:
            # Parse date from path: category/YYYY-MM-DD/...
            parts = e["path"].split("/")
            if len(parts) >= 2:
                try:
                    file_date = parts[1]
                    if file_date < cutoff:
                        old.append(e)
                except ValueError:
                    pass
        return old

    def migrate_directory(
        self, dirpath: str, category: str = "misc", dry_run: bool = False
    ) -> list:
        """Migrate a directory to GitLab storage."""
        if dry_run:
            print(f"[gitlab-storage] DRY RUN: Would upload {dirpath} to {category}")
            count = sum(len(files) for _, _, files in os.walk(dirpath))
            print(f"  Files to upload: {count}")
            return []
        return self.upload_directory(dirpath, category, description="Auto-migrated")

    def status_extended(self) -> dict:
        """Extended status with registry info."""
        st = self.status()
        st["registry_entries"] = self.registry.get_by_project(self.project_name)
        st["machine_links"] = self.machine_links.get_all()
        return st


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_storage_manager(
    project_name: str, visibility: str = "private"
) -> GitLabStorageManager:
    """Factory: create a GitLabStorageManager from environment."""
    token = _env("GITLAB_LOGCENTER_TOKEN")
    base_url = _env("GITLAB_LOGCENTER_URL", DEFAULT_API_URL)
    limit_gb = float(
        _env(
            "GITLAB_STORAGE_LIMIT_GB",
            _env("GITLAB_LOGCENTER_LIMIT_GB", str(DEFAULT_LIMIT_GB)),
        )
    )
    ns_raw = _env("GITLAB_LOGCENTER_NS", "")
    ns_id = int(ns_raw) if ns_raw.isdigit() else None
    api = GitLabAPI(token, base_url)
    return GitLabStorageManager(
        api, project_name, limit_gb=limit_gb, namespace_id=ns_id, visibility=visibility
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        prog="gitlab_storage_manager",
        description="GitLab Storage Manager — unendlicher Speicher für die SIN-Flotte",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Initialize storage for a project")
    p_init.add_argument("--project", required=True)
    p_init.add_argument(
        "--visibility", default="private", choices=["private", "public"]
    )

    # upload
    p_up = sub.add_parser("upload", help="Upload a file")
    p_up.add_argument("--project", required=True)
    p_up.add_argument("--file", required=True)
    p_up.add_argument("--category", default="misc", choices=EXTENDED_CATEGORIES)
    p_up.add_argument("--tags", default="")
    p_up.add_argument("--description", default="")

    # upload-dir
    p_updir = sub.add_parser("upload-dir", help="Upload a directory recursively")
    p_updir.add_argument("--project", required=True)
    p_updir.add_argument("--dir", required=True)
    p_updir.add_argument("--category", default="misc", choices=EXTENDED_CATEGORIES)
    p_updir.add_argument("--tags", default="")
    p_updir.add_argument("--description", default="")
    p_updir.add_argument(
        "--exclude", default="", help="Comma-separated exclude patterns"
    )

    # status
    p_st = sub.add_parser("status", help="Show storage status")
    p_st.add_argument("--project", required=True)
    p_st.add_argument("--json", action="store_true")

    # search
    p_sr = sub.add_parser("search", help="Search files")
    p_sr.add_argument("--project", required=True)
    p_sr.add_argument("--query", required=True)
    p_sr.add_argument("--max", type=int, default=50)

    # list
    p_ls = sub.add_parser("list", help="List files")
    p_ls.add_argument("--project", required=True)
    p_ls.add_argument("--category", choices=EXTENDED_CATEGORIES)
    p_ls.add_argument("--date")
    p_ls.add_argument("--repo")

    # download
    p_dl = sub.add_parser("download", help="Download a file")
    p_dl.add_argument("--project", required=True)
    p_dl.add_argument("--path", required=True)
    p_dl.add_argument("--output", required=True)
    p_dl.add_argument("--repo")

    # rotate
    p_rot = sub.add_parser("rotate", help="Force rotate to new repo")
    p_rot.add_argument("--project", required=True)

    # get-active
    p_ga = sub.add_parser("get-active", help="Print active repo")
    p_ga.add_argument("--project", required=True)

    # register
    p_reg = sub.add_parser("register", help="Register storage purpose in registry")
    p_reg.add_argument("--project", required=True)
    p_reg.add_argument("--purpose", required=True)
    p_reg.add_argument("--machine", default="")

    # link-machine
    p_link = sub.add_parser(
        "link-machine", help="Link a machine's directory to storage"
    )
    p_link.add_argument("--machine", required=True)
    p_link.add_argument("--project", required=True)
    p_link.add_argument("--sync-dir", required=True)
    p_link.add_argument("--category", default="misc", choices=EXTENDED_CATEGORIES)

    # cleanup
    p_clean = sub.add_parser("cleanup", help="Find old files")
    p_clean.add_argument("--project", required=True)
    p_clean.add_argument("--older-than", type=int, required=True)
    p_clean.add_argument("--category", choices=EXTENDED_CATEGORIES)

    # migrate
    p_mig = sub.add_parser("migrate", help="Migrate a directory to GitLab storage")
    p_mig.add_argument("--project", required=True)
    p_mig.add_argument("--from-dir", required=True)
    p_mig.add_argument("--category", default="misc", choices=EXTENDED_CATEGORIES)
    p_mig.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    visibility = getattr(args, "visibility", "private")
    sm = get_storage_manager(args.project, visibility=visibility)

    if args.command == "init":
        repo = sm.init()
        sm.registry.register(
            project=args.project,
            repo_name=repo["name"],
            repo_id=repo["id"],
            visibility=visibility,
            purpose=f"Storage for {args.project}",
            owner_machine=_env("HOSTNAME", "unknown"),
            categories=list(EXTENDED_CATEGORIES),
        )
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
        meta = sm.upload_file(
            args.file, category=args.category, tags=tags, description=args.description
        )
        print(json.dumps(meta, indent=2))

    elif args.command == "upload-dir":
        tags = (
            [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        )
        exclude = (
            [p.strip() for p in args.exclude.split(",") if p.strip()]
            if args.exclude
            else None
        )
        metas = sm.upload_directory(
            args.dir,
            category=args.category,
            tags=tags,
            description=args.description,
            exclude_patterns=exclude,
        )
        print(json.dumps({"uploaded_count": len(metas)}, indent=2))

    elif args.command == "status":
        st = sm.status_extended()
        if getattr(args, "json", False):
            print(json.dumps(st, indent=2))
        else:
            if not st["initialized"]:
                print(
                    f"[gitlab-storage] Project '{args.project}' not initialized. Run: gitlab_storage_manager.py init --project {args.project}"
                )
            else:
                print(f"Project:      {st['project']}")
                print(f"Active Repo:  {st['active_repo']}")
                print(f"Total Repos:  {st['total_repos']}")
                print(f"Total Used:   {st['total_used_human']}")
                if st.get("registry_entries"):
                    print(f"\nRegistry Entries: {len(st['registry_entries'])}")
                    for e in st["registry_entries"]:
                        print(
                            f"  {e['repo_name']}: {e['current_size_gb']} GB ({e['files_count']} files) — {e['purpose']}"
                        )

    elif args.command == "search":
        results = sm.search(args.query, max_results=args.max)
        if not results:
            print(f"[gitlab-storage] No results for '{args.query}'")
        else:
            for r in results:
                print(f"\n--- {r['repo']} :: {r['path']} (line {r['startline']}) ---")
                print(r["data"])

    elif args.command == "list":
        entries = sm.list_entries(
            category=args.category, date=args.date, repo_name=args.repo
        )
        if not entries:
            print("[gitlab-storage] No entries found")
        else:
            for e in entries:
                print(f"  [{e['repo']}] {e['path']}")

    elif args.command == "download":
        sm.download(args.path, args.output, repo_name=args.repo)

    elif args.command == "rotate":
        repo = sm.rotate()
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

    elif args.command == "get-active":
        repo = sm.get_active_repo()
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
            print("[gitlab-storage] Not initialized")
            sys.exit(1)

    elif args.command == "register":
        sm.registry.register(
            project=args.project,
            repo_name="manual",
            repo_id=0,
            visibility="private",
            purpose=args.purpose,
            owner_machine=args.machine or _env("HOSTNAME", "unknown"),
            categories=list(EXTENDED_CATEGORIES),
        )
        print(f"[gitlab-storage] Registered purpose: {args.purpose}")

    elif args.command == "link-machine":
        result = sm.machine_links.link_machine(
            args.machine, args.project, args.sync_dir, args.category
        )
        print(json.dumps(result, indent=2))

    elif args.command == "cleanup":
        old = sm.cleanup_old_files(args.older_than, category=args.category)
        if not old:
            print(f"[gitlab-storage] No files older than {args.older_than} days")
        else:
            print(f"Found {len(old)} files older than {args.older_than} days:")
            for e in old[:20]:
                print(f"  [{e['repo']}] {e['path']}")

    elif args.command == "migrate":
        result = sm.migrate_directory(
            args.from_dir, category=args.category, dry_run=args.dry_run
        )
        if args.dry_run:
            pass
        else:
            print(json.dumps({"migrated_count": len(result)}, indent=2))


if __name__ == "__main__":
    main()

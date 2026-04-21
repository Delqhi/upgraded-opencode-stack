#!/usr/bin/env python3
"""
Box Storage Client - Enterprise Deep Debug Skill
=================================================
Replacement for gitlab_logcenter.py using A2A-SIN-Box-Storage service.

All logs, screenshots, videos, reports are uploaded to Box.com via the
room-09-box-storage service.

Compatibility: Provides the same interface as gitlab_logcenter.py for
backward compatibility.

Environment:
  BOX_STORAGE_URL       Box Storage service base URL (default: http://room-09-box-storage:3000)
  BOX_STORAGE_API_KEY   API key for Box Storage service (REQUIRED)

Usage:
  from box_storage import get_logcenter
  lc = get_logcenter("sin-solver")
  lc.upload_file("/tmp/crash.log", category="logs", tags=["error"])
"""

import os
import json
import mimetypes
import requests
from typing import Optional, List, Dict, Any

BOX_STORAGE_URL = os.getenv("BOX_STORAGE_URL", "http://room-09-box-storage:3000")
BOX_STORAGE_API_KEY = os.getenv("BOX_STORAGE_API_KEY")


class BoxStorageClient:
    """Compatibility wrapper around A2A-SIN-Box-Storage API."""

    def __init__(self, project: str):
        self.project = project
        self.base_url = BOX_STORAGE_URL.rstrip("/")
        self.api_key = BOX_STORAGE_API_KEY
        if not self.api_key:
            raise RuntimeError(
                "BOX_STORAGE_API_KEY not set. Set env var or create ~/.config/opencode/box-storage.env"
            )

    def upload_file(
        self, filepath: str, category: str = "logs", tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload a file to Box.com storage."""
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = os.path.basename(filepath)
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type is None:
            mime_type = "application/octet-stream"

        with open(filepath, "rb") as f:
            files = {"file": (filename, f, mime_type)}
            headers = {"X-Box-Storage-Key": self.api_key}
            response = requests.post(
                f"{self.base_url}/api/v1/upload", headers=headers, files=files
            )
            response.raise_for_status()
            data = response.json()

        # Normalize response to match expected format
        return {
            "id": data["file"]["id"],
            "name": data["file"]["name"],
            "url": data["file"]["cdnUrl"],
            "size": data["file"]["size"],
            "category": category,
            "tags": tags or [],
            "project": self.project,
            "uploaded_at": data["file"]["uploadedAt"],
        }

    def upload_bytes(
        self,
        data: bytes,
        filename: str,
        category: str = "logs",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Upload raw bytes to Box.com storage."""
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"

        files = {"file": (filename, data, mime_type)}
        headers = {"X-Box-Storage-Key": self.api_key}
        response = requests.post(
            f"{self.base_url}/api/v1/upload", headers=headers, files=files
        )
        response.raise_for_status()
        data_resp = response.json()

        return {
            "id": data_resp["file"]["id"],
            "name": data_resp["file"]["name"],
            "url": data_resp["file"]["cdnUrl"],
            "size": data_resp["file"]["size"],
            "category": category,
            "tags": tags or [],
            "project": self.project,
            "uploaded_at": data_resp["file"]["uploadedAt"],
        }

    def list_files(
        self, category: Optional[str] = None, date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in storage. Not fully implemented for Box (no list API in service)."""
        raise NotImplementedError("list_files not implemented in Box Storage client")

    def download_file(self, path: str, output: str) -> None:
        """Download a file from storage by file ID or path."""
        raise NotImplementedError("download_file not implemented in Box Storage client")

    def get_active_repo(self) -> str:
        """Return the active storage repository identifier."""
        return "box-storage"


def get_logcenter(project: str):
    """Factory function to get a storage client for the given project."""
    return BoxStorageClient(project)

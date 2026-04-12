"""Safe policy filenames under content/policy/."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException

_SAFE_MD = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*\.md$")


def policy_file(policy_dir: Path, name: str) -> Path:
    """Resolve a basename under policy_dir; reject traversal."""
    base = Path(name).name.strip()
    if not base:
        raise HTTPException(status_code=400, detail="Invalid name")
    if ".." in name or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not base.endswith(".md"):
        base = f"{base}.md"
    if not _SAFE_MD.match(base):
        raise HTTPException(
            status_code=400,
            detail="Name must be like shipping.md (alphanumeric, dash, underscore)",
        )
    return (policy_dir / base).resolve()


def must_be_under(policy_dir: Path, path: Path) -> None:
    root = policy_dir.resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path escapes policy directory")

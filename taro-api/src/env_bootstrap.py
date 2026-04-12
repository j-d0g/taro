"""Load layered env files: taro-api/config/.env then repo .config/.env (overrides)."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_app_dotenv(*, api_root: Path | None = None) -> None:
    """
    Default api_root is the taro-api directory (parent of this file's src/).
    Call with api_root= from schema/seed.py where __file__ lives under schema/.
    """
    if api_root is None:
        api_root = Path(__file__).resolve().parent.parent
    repo_root = api_root.parent
    cfg = api_root / "config" / ".env"
    if cfg.is_file():
        load_dotenv(cfg)
    user = repo_root / ".config" / ".env"
    if user.is_file():
        load_dotenv(user, override=True)

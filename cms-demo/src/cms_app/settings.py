"""Load config from environment and optional taro-api / repo-root .env for subprocess ingest."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

# cms-demo/src/cms_app/settings.py -> cms-demo root
_CMS_DEMO_ROOT = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _CMS_DEMO_ROOT.parent
_TARO_API = _REPO_ROOT / "taro-api"

# Load cms-demo/.env first (if present)
load_dotenv(_CMS_DEMO_ROOT / ".env")


def _default_policy_dir() -> Path:
    return (_TARO_API / "content" / "policy").resolve()


def _policy_dir_from_env() -> Path:
    """Use TARO_CONTENT_POLICY_DIR if set and valid; else sibling taro-api/content/policy."""
    default = _default_policy_dir()
    raw = os.getenv("TARO_CONTENT_POLICY_DIR", "").strip()
    if not raw:
        return default
    p = Path(raw).expanduser().resolve()
    if p.is_dir():
        return p
    # Common mistake: copying .env.example placeholders like /absolute/path/to/...
    import warnings

    warnings.warn(
        f"TARO_CONTENT_POLICY_DIR is not a directory ({p}); using default {default}. "
        "Fix or remove TARO_CONTENT_POLICY_DIR in cms-demo/.env.",
        UserWarning,
        stacklevel=2,
    )
    return default


def _taro_python() -> Path:
    """Resolve taro-api/.venv/bin/python without following the bin/python symlink.

    On macOS, ``.venv/bin/python`` often symlinks to ``/Library/Frameworks/.../python3.11``.
    ``Path.resolve()`` collapses to that path; the subprocess then runs *without* the venv's
    site-packages (missing surrealdb, etc.). Use ``.absolute()`` for interpreter paths.
    """
    import warnings

    venv_root = (_TARO_API / ".venv").resolve()
    venv_root_abs = venv_root.absolute()

    default = (venv_root / "bin" / "python").absolute()
    for name in ("python", "python3", "python3.11"):
        candidate = (venv_root / "bin" / name).absolute()
        if candidate.is_file():
            default = candidate
            break

    raw = os.getenv("TARO_PYTHON", "").strip()
    if not raw:
        return default

    p = Path(raw).expanduser().absolute()
    try:
        if p.is_file():
            p.relative_to(venv_root_abs)
            return p
    except ValueError:
        pass
    except OSError:
        pass

    if default.is_file():
        warnings.warn(
            f"TARO_PYTHON={p} is not inside {venv_root_abs} (e.g. Framework python or wrong path). "
            f"Using project venv: {default}. Remove TARO_PYTHON from cms-demo/.env to silence.",
            UserWarning,
            stacklevel=2,
        )
        return default
    if p.is_file():
        warnings.warn(f"taro-api/.venv missing; using TARO_PYTHON={p}", UserWarning, stacklevel=2)
        return p
    warnings.warn(f"TARO_PYTHON invalid; using {default}", UserWarning, stacklevel=2)
    return default


class Settings:
    cms_admin_token: str
    taro_content_policy_dir: Path
    taro_python: Path
    taro_api_base: str
    taro_src_dir: Path
    taro_api_root: Path
    cms_host: str
    cms_port: int
    publish_mode: str  # direct | enqueue
    ingest_webhook_secret: str

    def __init__(self) -> None:
        self.cms_admin_token = os.getenv("CMS_ADMIN_TOKEN", "").strip()
        self.taro_content_policy_dir = _policy_dir_from_env()
        self.taro_python = _taro_python()
        self.taro_api_base = os.getenv("TARO_API_BASE", "http://localhost:8002").rstrip("/")
        self.taro_api_root = _TARO_API.resolve()
        self.taro_src_dir = (self.taro_api_root / "src").resolve()
        self.cms_host = os.getenv("CMS_HOST", "0.0.0.0")
        self.cms_port = int(os.getenv("CMS_PORT", "8088"))
        self.publish_mode = os.getenv("PUBLISH_MODE", "direct").strip().lower()
        self.ingest_webhook_secret = os.getenv("INGEST_WEBHOOK_SECRET", "").strip()

    def subprocess_env(self) -> dict[str, str]:
        """Merge process env with taro-api/config/.env and repo .config/.env for OPENAI_API_KEY etc."""
        env = dict(os.environ)
        for p in (self.taro_api_root / "config" / ".env", _REPO_ROOT / ".config" / ".env"):
            if p.is_file():
                for k, v in dotenv_values(p).items():
                    if v is not None and str(v) != "":
                        env[str(k)] = str(v)
        return env


@lru_cache
def get_settings() -> Settings:
    return Settings()

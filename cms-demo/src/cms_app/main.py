"""FastAPI CMS: edit policy markdown (Layer 1) and publish via Taro ingestion (Layer 3)."""

from __future__ import annotations

import asyncio
import re
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from cms_app.paths import must_be_under, policy_file
from cms_app.settings import Settings, get_settings

_CMS_ROOT = Path(__file__).resolve().parent.parent.parent
_STATIC = _CMS_ROOT / "static"


class BodyPut(BaseModel):
    content: str


def verify_token(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(None),
) -> None:
    if not settings.cms_admin_token:
        raise HTTPException(status_code=503, detail="CMS_ADMIN_TOKEN not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization")
    token = authorization[7:].strip()
    if token != settings.cms_admin_token:
        raise HTTPException(status_code=401, detail="Invalid token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Taro policy CMS (demo)", lifespan=lifespan)

if _STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


@app.get("/")
async def index():
    index_path = _STATIC / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=500, detail="static/index.html missing")
    return FileResponse(index_path)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "taro-cms-demo"}


@app.get("/api/policies", dependencies=[Depends(verify_token)])
async def list_policies(settings: Settings = Depends(get_settings)):
    d = settings.taro_content_policy_dir
    if not d.is_dir():
        raise HTTPException(
            status_code=503,
            detail=(
                f"Policy directory missing or unreachable: {d}. "
                "Unset TARO_CONTENT_POLICY_DIR in cms-demo/.env to use ../taro-api/content/policy, "
                "or set it to the real absolute path."
            ),
        )
    names = sorted(p.name for p in d.iterdir() if p.is_file() and p.suffix.lower() == ".md")
    return {"files": names, "policy_dir": str(d)}


@app.get("/api/policies/{name}", dependencies=[Depends(verify_token)])
async def get_policy(name: str, settings: Settings = Depends(get_settings)):
    path = policy_file(settings.taro_content_policy_dir, name)
    must_be_under(settings.taro_content_policy_dir, path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return {"name": path.name, "content": path.read_text(encoding="utf-8")}


@app.put("/api/policies/{name}", dependencies=[Depends(verify_token)])
async def put_policy(name: str, body: BodyPut, settings: Settings = Depends(get_settings)):
    path = policy_file(settings.taro_content_policy_dir, name)
    must_be_under(settings.taro_content_policy_dir, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(body.content, encoding="utf-8")
    tmp.replace(path)
    return {"saved": True, "name": path.name}


@app.post("/api/publish/{name}", dependencies=[Depends(verify_token)])
async def publish(name: str, settings: Settings = Depends(get_settings)):
    path = policy_file(settings.taro_content_policy_dir, name)
    must_be_under(settings.taro_content_policy_dir, path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found; save first")

    if settings.publish_mode == "enqueue":
        return await _publish_enqueue(path, settings)
    return await _publish_direct(path, settings)


def _publish_hint(ok: bool, err_s: str) -> str:
    if ok or not err_s:
        return ""
    if "No module named" in err_s:
        m = re.search(r"No module named '([^']+)'", err_s)
        mod = m.group(1) if m else "?"
        if mod == "loguru":
            return (
                "Ingest subprocess must use taro-api/.venv (not /Library/Frameworks or Homebrew python). "
                "Remove TARO_PYTHON from cms-demo/.env or set it to …/taro-api/.venv/bin/python."
            )
        return (
            f"Missing module '{mod}'. Run: cd taro-api && .venv/bin/python -m pip install -r requirements.txt "
            "(cms-demo/.env TARO_PYTHON must be that same .venv/bin/python)."
        )
    if "ProxyError" in err_s or ("403 Forbidden" in err_s and "openai" in err_s.lower()):
        return (
            "OpenAI HTTP failed (proxy). Try: unset HTTP_PROXY HTTPS_PROXY ALL_PROXY before starting CMS, "
            "or allowlist api.openai.com."
        )
    if "Connect call failed" in err_s or "Connection refused" in err_s:
        if any(x in err_s for x in ("8001", "8000", "Surreal", "surreal")):
            return "SurrealDB not running or wrong port. Start: cd taro-api && make surrealdb — match SURREALDB_URL in .env."
    if "Incorrect API key" in err_s or "invalid_api_key" in err_s:
        return "Invalid OPENAI_API_KEY — set in taro-api/config/.env or repo .config/.env."
    return ""


def _ingest_child_env(settings: Settings) -> dict[str, str]:
    """Inherit taro/.config secrets but drop vars that break the taro venv (e.g. CMS PYTHONPATH, Conda PYTHONHOME)."""
    env = dict(settings.subprocess_env())
    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSAFEPATH",
        "__PYVENV_LAUNCHER__",
    ):
        env.pop(key, None)
    # Point activation hints at taro-api venv so mixed conda + venv shells behave.
    env["VIRTUAL_ENV"] = str(settings.taro_api_root / ".venv")
    return env


async def _publish_direct(path: Path, settings: Settings) -> dict:
    if not settings.taro_python.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"TARO_PYTHON not found: {settings.taro_python}",
        )
    # -E: ignore inherited PYTHON* (conda/Cursor PYTHONPATH) so taro-api/.venv site-packages wins
    cmd = [
        str(settings.taro_python),
        "-E",
        "-m",
        "ingestion.cli",
        "ingest-file",
        str(path),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(settings.taro_src_dir),
        env=_ingest_child_env(settings),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    out_s = out.decode(errors="replace").strip()
    err_s = err.decode(errors="replace").strip()
    ok = proc.returncode == 0
    hint = _publish_hint(ok, err_s)
    result: dict = {
        "ok": ok,
        "mode": "direct",
        "returncode": proc.returncode,
        "stdout": out_s,
        "stderr": err_s,
    }
    if hint:
        result["hint"] = hint
    result["python_used"] = str(settings.taro_python)
    return result


async def _publish_enqueue(path: Path, settings: Settings) -> dict:
    if not settings.ingest_webhook_secret:
        raise HTTPException(
            status_code=503,
            detail="INGEST_WEBHOOK_SECRET required for PUBLISH_MODE=enqueue",
        )
    rel = path.relative_to(settings.taro_api_root / "content")
    source_key = str(rel).replace("\\", "/")

    url = f"{settings.taro_api_base}/ingest/policy"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                url,
                json={"source_key": source_key, "op": "upsert"},
                headers={"X-Ingest-Token": settings.ingest_webhook_secret},
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Ingest HTTP failed: {e}") from e

    enqueue_body = {"status_code": r.status_code, "text": r.text[:2000]}
    if r.status_code not in (200, 201):
        return {"ok": False, "mode": "enqueue", "enqueue": enqueue_body}

    drain_cmd = [str(settings.taro_python), "-E", "-m", "ingestion.cli", "drain"]
    proc = await asyncio.create_subprocess_exec(
        *drain_cmd,
        cwd=str(settings.taro_src_dir),
        env=_ingest_child_env(settings),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return {
        "ok": proc.returncode == 0 and r.status_code < 400,
        "mode": "enqueue",
        "enqueue": enqueue_body,
        "drain_returncode": proc.returncode,
        "drain_stdout": out.decode(errors="replace").strip(),
        "drain_stderr": err.decode(errors="replace").strip(),
    }


def main():
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "cms_app.main:app",
        host=s.cms_host,
        port=s.cms_port,
        reload=False,
    )


if __name__ == "__main__":
    main()

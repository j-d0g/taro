# CMS demo (self-hosted)

Small **FastAPI + static** admin to edit **`taro-api/content/policy/*.md`** (FAQ RAG **Layer 1**) and **publish** into Taro ingestion (**Layer 3**). Lives in **`cms-demo/`** only; delete this folder and core Taro is unchanged.

## Relationship to Taro

| Piece | Location |
|-------|----------|
| Commerce + agent API | [`../taro-api/`](../taro-api/) |
| Shop frontend | [`../taro-web/`](../taro-web/) |
| **This CMS** | `cms-demo/` |

Detailed plan + **6-layer FAQ RAG mapping**: [`../docs/internal/cms-demo-plan.md`](../docs/internal/cms-demo-plan.md).

## Setup

1. Copy [`.env.example`](.env.example) to **`.env`** in `cms-demo/` and set **`CMS_ADMIN_TOKEN`** (long random string).
2. Optional: set **`TARO_CONTENT_POLICY_DIR`** and **`TARO_PYTHON`** if your paths differ from the default sibling `../taro-api/`.
3. Install deps (reuse Taro’s venv or create `cms-demo/.venv`):

   ```bash
   cd cms-demo
   ../taro-api/.venv/bin/python -m pip install -r requirements.txt
   ```

4. **SurrealDB + Taro** must be running for **publish** to succeed (`ingest-file` needs DB + `OPENAI_API_KEY`). Subprocess env merges **`taro-api/config/.env`** and **repo `/.config/.env`** so keys match `make ingest-policy`.

## Run

```bash
cd cms-demo
cp .env.example .env   # first time; edit CMS_ADMIN_TOKEN
make serve
```

Open **http://localhost:8088** — paste the same token into the UI (stored in `localStorage`). **Save** writes markdown; **Publish** runs ingestion for that file.

Manual equivalent:

```bash
cd cms-demo
export PYTHONPATH=src
export CMS_ADMIN_TOKEN=your-secret
../taro-api/.venv/bin/python -m uvicorn cms_app.main:app --host 0.0.0.0 --port 8088
```

## API (Bearer `CMS_ADMIN_TOKEN`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | No auth |
| GET | `/api/policies` | List `*.md` in policy dir |
| GET | `/api/policies/{name}` | Read file body |
| PUT | `/api/policies/{name}` | Body `{"content":"..."}` |
| POST | `/api/publish/{name}` | Direct ingest or enqueue (see `.env`) |

## Optional Layer 2 (queue + drain)

See [`LAYER2.md`](LAYER2.md) for **`PUBLISH_MODE=enqueue`**.

## Troubleshooting

### Publish shows `ModuleNotFoundError: No module named 'loguru'`

The ingest subprocess uses **`TARO_PYTHON`** (default: `../taro-api/.venv/bin/python`). Install Taro deps into that venv:

```bash
cd ../taro-api && .venv/bin/python -m pip install -r requirements.txt
```

If you use **Conda**, inherited **`PYTHONPATH` / `PYTHONHOME`** from the parent shell could confuse the child interpreter; the CMS strips those for ingest (see `_ingest_child_env` in `src/cms_app/main.py`). Restart **`make serve`** in `cms-demo` after pulling updates.

## Removal

Delete **`cms-demo/`**; Taro and `taro-web` behave as before.

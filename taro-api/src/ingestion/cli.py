"""CLI: ingest policy files directly or enqueue events for the worker."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from ingestion.events import IngestionEvent
from ingestion.processor import ingest_policy_dir, ingest_policy_file
from ingestion.queue import get_queue


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Taro policy ingestion (Layers 2–3)")
    sub = parser.add_subparsers(dest="cmd")

    p_all = sub.add_parser("ingest-all", help="Chunk, hash, embed all markdown under content/policy/")
    p_all.add_argument("--policy-dir", type=Path, default=None)

    p_one = sub.add_parser("ingest-file", help="Ingest a single markdown file")
    p_one.add_argument("path", type=Path)
    p_one.add_argument("--source-key", default=None)

    p_enq = sub.add_parser("enqueue", help="Enqueue upsert/delete events (uses INGESTION_BACKEND)")
    p_enq.add_argument("source_key")
    p_enq.add_argument("--delete", action="store_true")

    p_drain = sub.add_parser("drain", help="Process queued events once (file/redis backends)")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1

    if args.cmd == "ingest-all":
        rows = await ingest_policy_dir(args.policy_dir)
        print(json.dumps(rows, indent=2))
        return 0

    if args.cmd == "ingest-file":
        r = await ingest_policy_file(args.path, source_key=args.source_key)
        print(json.dumps(r, indent=2))
        return 0

    if args.cmd == "enqueue":
        ev = IngestionEvent(source_key=args.source_key, op="delete" if args.delete else "upsert")
        q = get_queue()
        await q.enqueue(ev)
        print(f"Enqueued: {ev.to_json()}")
        return 0

    if args.cmd == "drain":
        from ingestion.worker import handle_event

        q = get_queue()
        n = 0
        while True:
            ev = await q.dequeue(timeout_sec=1.0)
            if not ev:
                break
            out = await handle_event(ev)
            print(json.dumps(out, indent=2))
            n += 1
        print(f"Processed {n} event(s).", file=sys.stderr)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))

"""Run: python -m ingestion.run_worker [--once]"""

import asyncio
import sys

from ingestion.worker import run_worker_loop

if __name__ == "__main__":
    once = "--once" in sys.argv
    asyncio.run(run_worker_loop(once=once))

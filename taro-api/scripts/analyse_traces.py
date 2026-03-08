#!/usr/bin/env python3
"""
Taro.ai LangSmith Trace Analyser

Pulls recent traces from LangSmith, classifies successes/failures,
and prints basic statistics. Designed as the first step in the
observability -> self-improvement pipeline.

Usage:
    python scripts/analyse_traces.py                  # last 24h
    python scripts/analyse_traces.py --hours 72       # last 3 days
    python scripts/analyse_traces.py --limit 50       # cap at 50 runs

Requires:
    LANGSMITH_API_KEY and LANGSMITH_PROJECT env vars (loaded from config/.env)
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load .env from config directory
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed; rely on shell env vars


def get_langsmith_client():
    """Create a LangSmith client, or return None if not configured."""
    api_key = os.getenv("LANGSMITH_API_KEY", "")
    if not api_key or api_key.startswith("lsv2_pt_xxx"):
        print("[WARN] LANGSMITH_API_KEY not configured (placeholder or missing).")
        print("       Set it in taro-api/config/.env to enable trace analysis.")
        return None

    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    try:
        from langsmith import Client

        client = Client(api_url=endpoint, api_key=api_key)
        return client
    except ImportError:
        print("[ERROR] langsmith package not installed. Run: pip install langsmith")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to create LangSmith client: {e}")
        return None


def list_recent_runs(client, project_name: str, hours: int = 24, limit: int = 200):
    """Fetch recent root-level runs from LangSmith.

    Returns a list of Run objects (top-level traces only).
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    runs = list(
        client.list_runs(
            project_name=project_name,
            is_root=True,
            start_time=since,
            limit=limit,
        )
    )
    return runs


def classify_run(run) -> str:
    """Classify a run as 'success', 'error', or 'no_output'.

    Classification rules:
    - If run.error is set -> 'error'
    - If run has no output or empty output -> 'no_output'
    - Otherwise -> 'success'
    """
    if run.error:
        return "error"
    if not run.outputs:
        return "no_output"
    return "success"


def compute_stats(runs) -> dict:
    """Compute summary statistics from a list of runs.

    Returns dict with counts, token totals, and latency info.
    """
    stats = {
        "total_runs": len(runs),
        "successes": 0,
        "errors": 0,
        "no_output": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_latency_s": 0.0,
        "error_messages": [],
        "tool_usage": {},
    }

    for run in runs:
        category = classify_run(run)
        stats[category if category != "success" else "successes"] += 1

        # Token counts (may be None)
        if hasattr(run, "total_tokens") and run.total_tokens:
            stats["total_tokens"] += run.total_tokens
        if hasattr(run, "prompt_tokens") and run.prompt_tokens:
            stats["prompt_tokens"] += run.prompt_tokens
        if hasattr(run, "completion_tokens") and run.completion_tokens:
            stats["completion_tokens"] += run.completion_tokens

        # Latency
        if run.start_time and run.end_time:
            latency = (run.end_time - run.start_time).total_seconds()
            stats["total_latency_s"] += latency

        # Collect error messages
        if run.error:
            stats["error_messages"].append(
                {"run_id": str(run.id), "error": run.error[:200]}
            )

        # Track run name frequency
        name = run.name or "unknown"
        stats["tool_usage"][name] = stats["tool_usage"].get(name, 0) + 1

    return stats


def print_report(stats: dict, hours: int):
    """Print a human-readable report to stdout."""
    total = stats["total_runs"]
    if total == 0:
        print(f"\nNo runs found in the last {hours} hours.")
        return

    success_rate = (stats["successes"] / total) * 100 if total > 0 else 0
    avg_latency = stats["total_latency_s"] / total if total > 0 else 0

    print("\n" + "=" * 60)
    print(f"  Taro.ai Trace Analysis -- Last {hours} hours")
    print("=" * 60)

    print(f"\n  Total runs:       {total}")
    print(f"  Successes:        {stats['successes']} ({success_rate:.1f}%)")
    print(f"  Errors:           {stats['errors']}")
    print(f"  No output:        {stats['no_output']}")

    print(f"\n  Total tokens:     {stats['total_tokens']:,}")
    print(f"  Prompt tokens:    {stats['prompt_tokens']:,}")
    print(f"  Completion tokens:{stats['completion_tokens']:,}")

    print(f"\n  Avg latency:      {avg_latency:.1f}s")
    print(f"  Total latency:    {stats['total_latency_s']:.1f}s")

    if stats["tool_usage"]:
        print("\n  Run names:")
        for name, count in sorted(
            stats["tool_usage"].items(), key=lambda x: -x[1]
        ):
            print(f"    {name}: {count}")

    if stats["error_messages"]:
        print(f"\n  Recent errors ({len(stats['error_messages'])}):")
        for err in stats["error_messages"][:5]:
            print(f"    [{err['run_id'][:8]}] {err['error']}")

    print("\n" + "=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyse LangSmith traces for Taro.ai")
    parser.add_argument(
        "--hours", type=int, default=24, help="Look back N hours (default: 24)"
    )
    parser.add_argument(
        "--limit", type=int, default=200, help="Max runs to fetch (default: 200)"
    )
    parser.add_argument(
        "--project",
        type=str,
        default=os.getenv("LANGSMITH_PROJECT", "taro"),
        help="LangSmith project name (default: from env or 'taro')",
    )
    args = parser.parse_args()

    client = get_langsmith_client()
    if client is None:
        sys.exit(1)

    print(f"Fetching runs from project '{args.project}' (last {args.hours}h, limit {args.limit})...")

    try:
        runs = list_recent_runs(
            client,
            project_name=args.project,
            hours=args.hours,
            limit=args.limit,
        )
    except Exception as e:
        print(f"[ERROR] Failed to fetch runs: {e}")
        sys.exit(1)

    stats = compute_stats(runs)
    print_report(stats, args.hours)


if __name__ == "__main__":
    main()

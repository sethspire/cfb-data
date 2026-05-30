#!/usr/bin/env python3
"""Backfill historical CFB data via the deployed Chalice endpoint.

Requires the Chalice app to be deployed first. Makes POST requests to
the /ingest/{entity} endpoint for each year and entity.

Usage:
    uv run python scripts/remote_backfill.py \
      --endpoint-url https://abc123.execute-api.us-east-1.amazonaws.com/dev \
      --api-secret supersecret \
      --start-year 1876
"""

import argparse
import json
import os
import time
import sys
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter

from ingestion.cfbd_ingest.services.dates import current_season


CHECKPOINT_FILE = Path(__file__).parent / ".remote_backfill_checkpoint.json"


SEASONAL_ENTITIES = ["teams", "games", "drives", "plays"]
STATIC_ENTITIES = ["conferences", "venues"]


def load_checkpoint(path: Path) -> dict | None:
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_checkpoint(path: Path, year: int):
    path.write_text(json.dumps({"last_year": year}))


def post_with_retry(
    session: requests.Session,
    url: str,
    secret: str | None,
    params: dict | None,
    max_retries: int,
) -> bool:
    headers = {}
    if secret:
        headers["x-api-key"] = secret

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            r = session.post(url, headers=headers, params=params, timeout=30)
            if r.status_code == 200:
                return True

            if r.status_code in (403, 404):
                print(f"  Client error {r.status_code} — skipping")
                return False

            last_error = f"HTTP {r.status_code}"
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  {last_error} — retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)

        except requests.RequestException as e:
            last_error = str(e)
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  Network error — retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)

    print(f"  Failed after {max_retries + 1} attempts: {last_error}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Backfill CFB data via deployed endpoint")
    parser.add_argument("--endpoint-url", required=True, help="Base URL of the deployed Chalice app")
    parser.add_argument("--api-secret", help="X-Api-Key header value (optional)")
    parser.add_argument("--start-year", type=int, default=1876, help="Start year (default: 1876)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between years (default: 0.5)")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries per request (default: 3)")
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_FILE), help="Checkpoint file path")
    args = parser.parse_args()

    endpoint_url = args.endpoint_url.rstrip("/")
    secret = args.api_secret or os.environ.get("API_SECRET")
    checkpoint_path = Path(args.checkpoint_path)

    session = requests.Session()
    adapter = HTTPAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    end = current_season()
    start = args.start_year

    checkpoint = load_checkpoint(checkpoint_path)
    if checkpoint:
        start = max(start, checkpoint["last_year"] + 1)
        print(f"Resuming from year {start} (checkpoint: {checkpoint['last_year']})")

    for entity in STATIC_ENTITIES:
        print(f"Ingesting {entity}...")
        ok = post_with_retry(session, f"{endpoint_url}/ingest/{entity}", secret, None, args.max_retries)
        if not ok:
            print(f"  Fatal: {entity} failed — aborting")
            sys.exit(1)

    for year in range(start, end + 1):
        print(f"Year {year}...")
        all_ok = True
        for entity in SEASONAL_ENTITIES:
            params = {"season": str(year), "season_type": "both"}
            ok = post_with_retry(session, f"{endpoint_url}/ingest/{entity}", secret, params, args.max_retries)
            if not ok:
                all_ok = False

        if all_ok:
            save_checkpoint(checkpoint_path, year)
            print(f"  Done")
        else:
            print(f"  Partial failure — checkpoint not advanced")

        if args.delay:
            time.sleep(args.delay)

    if checkpoint_path.exists():
        checkpoint_path.unlink()
    print("Backfill complete!")


if __name__ == "__main__":
    main()

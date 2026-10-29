"""Fetch a bounded GH Archive extract from ClickHouse's public read-only demo.

The four weekly queries stay below the demo's 10,000-row response limit.
Only fields needed for network analysis are fetched; no comment text is copied.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen


ENDPOINT = "https://sql-clickhouse.clickhouse.com/"
WINDOWS = [
    ("2025-01-01 00:00:00", "2025-01-08 00:00:00"),
    ("2025-01-08 00:00:00", "2025-01-15 00:00:00"),
    ("2025-01-15 00:00:00", "2025-01-22 00:00:00"),
    ("2025-01-22 00:00:00", "2025-02-01 00:00:00"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/raw-events.jsonl"))
    args = parser.parse_args()
    template = Path(__file__).with_name("events.sql").read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    credential = base64.b64encode(b"demo:").decode("ascii")
    total = 0
    with args.output.open("w", encoding="utf-8") as out:
        for start, end in WINDOWS:
            sql = template.replace("{{START}}", start).replace("{{END}}", end)
            request = Request(
                ENDPOINT,
                data=sql.encode("utf-8"),
                headers={"Authorization": f"Basic {credential}"},
                method="POST",
            )
            with urlopen(request, timeout=120) as response:
                rows = response.read().decode("utf-8").splitlines()
            for line in rows:
                event = json.loads(line)
                if not (start[:10] <= event["event_time_utc"][:10] < end[:10]):
                    raise ValueError(f"Event outside queried window: {event['event_time_utc']}")
                out.write(json.dumps(event, ensure_ascii=False) + "\n")
            total += len(rows)
            print(f"{start[:10]} to {end[:10]}: {len(rows)} rows", flush=True)
    print(f"Saved {total} public event rows to {args.output}")


if __name__ == "__main__":
    main()

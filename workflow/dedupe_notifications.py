#!/usr/bin/env python3
"""De-duplicate notifications.jsonl.

Entries are unique by (csv_source, diff_preview); the entry with the oldest
timestamp is kept. The relative order of the kept entries is preserved.

Usage: dedupe_notifications.py [path]   (default: notifications.jsonl)
"""
import json
import sys
from pathlib import Path


def dedupe(lines):
    """Return the lines to keep, in original order."""
    oldest = {}  # key -> (timestamp, index)
    parsed = []
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            parsed.append(None)
            continue
        key = (entry.get("csv_source"), entry.get("diff_preview"))
        ts = entry.get("timestamp") or ""
        parsed.append((key, ts))
        # Strictly older wins; ties keep the earlier line in the file.
        if key not in oldest or ts < oldest[key][0]:
            oldest[key] = (ts, i)
    keep = {idx for _, idx in oldest.values()}
    return [
        line for i, line in enumerate(lines)
        if parsed[i] is None or i in keep
    ]


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "notifications.jsonl")
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    kept = dedupe(lines)
    path.write_text("".join(l + "\n" for l in kept), encoding="utf-8")
    print(f"{path}: {len(lines)} -> {len(kept)} entries "
          f"({len(lines) - len(kept)} duplicates removed)")


if __name__ == "__main__":
    main()

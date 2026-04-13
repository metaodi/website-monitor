#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate a static website and RSS feed from notification logs.

Usage:
  generate_site.py [--output <output-dir>] [--base-url <base-url>] [--max-items <n>]
  generate_site.py (-h | --help)

Options:
  -h, --help                    Show this screen.
  -o, --output <output-dir>     Output directory for generated site [default: docs].
  -b, --base-url <base-url>     Base URL for the site [default: https://metaodi.github.io/website-monitor].
  -m, --max-items <n>           Maximum number of items in RSS feed [default: 100].
"""

import json
import csv
import os
import html
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
NOTIFICATIONS_FILE = REPO_DIR / "notifications.jsonl"
CSV_DIR = REPO_DIR / "csv"


def load_notifications():
    """Load all notification entries from the JSONL file."""
    entries = []
    if not NOTIFICATIONS_FILE.exists():
        return entries
    with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    # Sort by timestamp descending (newest first)
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries


def get_csv_sources():
    """Get list of CSV source names from the csv directory."""
    sources = []
    if CSV_DIR.exists():
        for f in sorted(CSV_DIR.iterdir()):
            if f.suffix == ".csv" and f.name != "test.csv":
                sources.append(f.stem)
    return sources


def format_timestamp(iso_timestamp):
    """Format an ISO timestamp for display."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return iso_timestamp


def format_rfc822(iso_timestamp):
    """Format an ISO timestamp as RFC 822 for RSS."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except (ValueError, TypeError):
        return ""


def generate_html(entries, csv_sources, output_dir, base_url):
    """Generate index.html with notification list."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build source filter links
    source_links = ['<a href="index.html">All</a>']
    for source in csv_sources:
        source_links.append(
            f'<a href="index-{html.escape(source)}.html">'
            f"{html.escape(source)}</a>"
        )
    source_nav = " · ".join(source_links)

    # Generate main page + per-source pages
    pages = [("index.html", entries, None)]
    for source in csv_sources:
        filtered = [e for e in entries if e.get("csv_source") == source]
        pages.append((f"index-{source}.html", filtered, source))

    for filename, page_entries, source_filter in pages:
        title = "Website Monitor"
        if source_filter:
            title += f" – {source_filter}"

        rows = []
        for entry in page_entries:
            ts = html.escape(format_timestamp(entry.get("timestamp", "")))
            label = html.escape(entry.get("label", ""))
            url = html.escape(entry.get("url", ""))
            source = html.escape(entry.get("csv_source", ""))
            diff = html.escape(entry.get("diff_preview", ""))

            diff_html = ""
            if diff:
                diff_html = f'<pre class="diff">{diff}</pre>'

            rows.append(
                f"""<article>
  <time>{ts}</time>
  <span class="source">{source}</span>
  <h2><a href="{url}">{label}</a></h2>
  {diff_html}
</article>"""
            )

        if not rows:
            content = "<p>No notifications yet.</p>"
        else:
            content = "\n".join(rows)

        page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="{base_url}/feed.xml">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           max-width: 800px; margin: 0 auto; padding: 1rem; color: #333; background: #fafafa; }}
    header {{ margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid #e0e0e0; }}
    header h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
    nav {{ font-size: 0.9rem; margin-bottom: 0.5rem; }}
    nav a {{ color: #0366d6; text-decoration: none; }}
    nav a:hover {{ text-decoration: underline; }}
    .feed-link {{ font-size: 0.85rem; }}
    .feed-link a {{ color: #e36209; }}
    article {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 6px;
               padding: 1rem; margin-bottom: 1rem; }}
    article time {{ font-size: 0.85rem; color: #666; }}
    article .source {{ font-size: 0.8rem; color: #fff; background: #0366d6;
                       border-radius: 3px; padding: 0.1rem 0.4rem; margin-left: 0.5rem; }}
    article h2 {{ font-size: 1.1rem; margin: 0.4rem 0; }}
    article h2 a {{ color: #0366d6; text-decoration: none; }}
    article h2 a:hover {{ text-decoration: underline; }}
    .diff {{ background: #f6f8fa; border: 1px solid #e0e0e0; border-radius: 4px;
             padding: 0.75rem; font-size: 0.8rem; overflow-x: auto;
             white-space: pre-wrap; word-break: break-word; margin-top: 0.5rem; }}
    footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e0e0e0;
              font-size: 0.8rem; color: #666; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(title)}</h1>
    <nav>{source_nav}</nav>
    <div class="feed-link">📡 <a href="{base_url}/feed.xml">RSS Feed</a></div>
  </header>
  <main>
    {content}
  </main>
  <footer>
    Last updated: {now} ·
    <a href="https://github.com/metaodi/website-monitor">Source on GitHub</a>
  </footer>
</body>
</html>"""

        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page_html)


def generate_rss(entries, output_dir, base_url, max_items):
    """Generate RSS 2.0 feed."""
    now = format_rfc822(datetime.now(timezone.utc).isoformat())
    feed_entries = entries[:max_items]

    items = []
    for entry in feed_entries:
        title = xml_escape(entry.get("label", ""))
        link = xml_escape(entry.get("url", ""))
        source = xml_escape(entry.get("csv_source", ""))
        pub_date = format_rfc822(entry.get("timestamp", ""))
        diff = entry.get("diff_preview", "")

        description = f"Website changed: {title} ({source})"
        if diff:
            description += f"\n\n{diff}"
        description = xml_escape(description)

        guid_input = f"{entry.get('timestamp', '')}|{entry.get('label', '')}|{entry.get('url', '')}"
        guid_hash = hashlib.sha256(guid_input.encode("utf-8")).hexdigest()[:16]

        items.append(
            f"""    <item>
      <title>🟢 {title}</title>
      <link>{link}</link>
      <description>{description}</description>
      <pubDate>{pub_date}</pubDate>
      <category>{source}</category>
      <guid isPermaLink="false">{guid_hash}</guid>
    </item>"""
        )

    items_xml = "\n".join(items)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Website Monitor</title>
    <link>{xml_escape(base_url)}</link>
    <description>Notifications from website-monitor: tracked websites that have changed.</description>
    <language>de-ch</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{xml_escape(base_url)}/feed.xml" rel="self" type="application/rss+xml"/>
{items_xml}
  </channel>
</rss>"""

    output_path = output_dir / "feed.xml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rss)


def main():
    from docopt import docopt

    arguments = docopt(__doc__)
    output_dir = Path(arguments["--output"])
    base_url = arguments["--base-url"].rstrip("/")
    max_items = int(arguments["--max-items"])

    output_dir.mkdir(parents=True, exist_ok=True)

    entries = load_notifications()
    csv_sources = get_csv_sources()

    generate_html(entries, csv_sources, output_dir, base_url)
    generate_rss(entries, output_dir, base_url, max_items)

    print(f"Generated site in {output_dir}/")
    print(f"  - {len(entries)} notification(s)")
    print(f"  - {len(csv_sources)} source(s): {', '.join(csv_sources)}")


if __name__ == "__main__":
    main()

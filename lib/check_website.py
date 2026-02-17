#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check websites for changes

Usage:
  check_website.py --db <path-to-db-file> [--verbose] [--no-verify]
  check_website.py (-h | --help)
  check_website.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -d, --db <path-to-db-file>    URL of the website to monitor.
  --verbose                     Option to enable more verbose output.
  --no-verify                   Option to disable SSL verification for requests.
"""


import os
import sys
import logging
import sqlite3
import traceback
import json
import hashlib
import requests
import urllib3
from pathlib import Path
from docopt import docopt
from dotenv import load_dotenv, find_dotenv

from . import website_hash as wh


load_dotenv(find_dotenv())
arguments = docopt(__doc__, version="Check websites for changes 1.0")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_TO")
TEXTS_DIR = Path(__file__).parent.parent / "texts"


def send_telegram_message(token, chat_id, message):
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
    }
    headers = {"Content-type": "application/json"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data=json.dumps(params), headers=headers)
    r.raise_for_status()


def sanitize_label_for_filename(label):
    """Convert a label to a safe filename."""
    # Replace spaces and special characters with underscores
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in label)
    # Remove consecutive underscores
    safe_name = "_".join(filter(None, safe_name.split("_")))
    return safe_name.lower()


loglevel = logging.INFO
if arguments["--verbose"]:
    loglevel = logging.DEBUG

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=loglevel,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.captureWarnings(True)
log = logging.getLogger(__name__)

conn = None
try:
    conn = sqlite3.connect(arguments["--db"])
    conn.row_factory = sqlite3.Row

    verify = not arguments["--no-verify"]

    if not verify:
        urllib3.disable_warnings()

    cur = conn.cursor()
    cur.execute("SELECT * FROM website")
    rows = cur.fetchall()
    
    # Ensure texts directory exists
    TEXTS_DIR.mkdir(exist_ok=True)
    
    for row in rows:
        try:
            r = dict(row)
            log.info(f"Checking website {r['url']}")

            error_count = int(r["error_count"])
            label = r["label"]
            
            # Get the text file path for this website
            filename = sanitize_label_for_filename(label) + ".txt"
            text_file = TEXTS_DIR / filename
            
            # Get new text from website
            new_text = wh.get_website_text(r["url"], r["selector"], verify, r["type"])
            log.debug(f"  New text length: {len(new_text)}")
            
            # Read old text if it exists
            old_text = ""
            if text_file.exists():
                with open(text_file, "r") as f:
                    old_text = f.read()
                log.debug(f"  Old text length: {len(old_text)}")
            else:
                log.info(f"  No previous text found for {label}, creating new file")
            
            # Compare texts
            if old_text == new_text:
                # nothing changed
                log.info("  Text unchanged. Continue...")
                continue
            
            log.info("  ***Text changed!***")
            
            # Save new text
            with open(text_file, "w") as f:
                f.write(new_text)
            
            msg = f"🟢 Website changed: [{row['label']}]({row['url']})"
            send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)
            
            # Update hash in database for backward compatibility
            new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()
            update_sql = "UPDATE website set hash = ?, error_count = 0 WHERE selector = ? AND url = ?"
            cur.execute(update_sql, [new_hash, row["selector"], row["url"]])
        except Exception as e:
            print("Error: %s" % e, file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

            if error_count > 1:
                send_telegram_message(
                    TELEGRAM_TOKEN,
                    TELEGRAM_CHAT_ID,
                    f"🟠 Failed to get website: [{row['label']}]({row['url']}))\nError: {e}",
                )
            error_sql = (
                "UPDATE website set error_count = 0 WHERE selector = ? AND url = ?"
            )
            cur.execute(error_sql, [row["selector"], row["url"]])
            continue
    conn.commit()
except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

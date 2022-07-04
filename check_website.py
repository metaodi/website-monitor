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
import time
import logging
import sqlite3
import traceback
import requests
from docopt import docopt
from dotenv import load_dotenv, find_dotenv

import website_hash as wh


load_dotenv(find_dotenv())
arguments = docopt(__doc__, version='Check websites for changes 1.0')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_TO')

def send_telegram_message(token, chat_id, message):
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": 'MarkdownV2',
    }
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, params=params)
    r.raise_for_status()

loglevel = logging.INFO
if arguments['--verbose']:
    loglevel = logging.DEBUG

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=loglevel,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.captureWarnings(True)
log = logging.getLogger(__name__)

conn = None
try:
    conn = sqlite3.connect(arguments['--db'])
    conn.row_factory = sqlite3.Row

    verify = not arguments['--no-verify']

    if not verify:
        import urllib3
        urllib3.disable_warnings()

    cur = conn.cursor()
    cur.execute("SELECT * FROM website")
    rows = cur.fetchall()
    for row in rows:
        try:
            r = dict(row)
            old_hash = r['hash']
            log.info(f"Old hash: {old_hash}")
            
            log.info(f"Checking website {r['url']}...")
            new_hash = wh.get_website_hash(r['url'], r['selector'], verify, r['type'])
            log.info(f"New hash: {new_hash}")
            if old_hash == new_hash:
                 # nothing changed
                 continue
            log.info(f"Hash changed!")
            msg = f"🟢 Website changed: [{row['label']}]({row['url']})"
            send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)
            update_sql = ('UPDATE website set hash = ? WHERE selector = ? AND url = ?')
            cur.execute(update_sql, [new_hash, row['selector'], row['url']])
        except Exception as e:
            print("Error: %s" % e, file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            send_telegram_message(
                TELEGRAM_TOKEN,
                TELEGRAM_CHAT_ID,
                f"🟠 Failed to get website: [{row['label']}]({row['url']}))\nError: {e}"
            )
            continue
    conn.commit()
except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

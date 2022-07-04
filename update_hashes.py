#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update websites hashes

Usage:
  update_hashes.py --db <path-to-db-file> [--verbose] [--no-verify]
  update_hashes.py (-h | --help)
  update_hashes.py --version

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
import json
import requests
from docopt import docopt
from dotenv import load_dotenv, find_dotenv

import website_hash as wh


load_dotenv(find_dotenv())
arguments = docopt(__doc__, version='Update website hashes 1.0')

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
            log.info(f"Checking website {r['url']}")

            old_hash = r['hash']
            new_hash = wh.get_website_hash(r['url'], r['selector'], verify, r['type'])
            log.info(f"  Old hash: {old_hash}")
            log.info(f"  New hash: {new_hash}")
            if old_hash == new_hash:
                 # nothing changed
                 log.info(f"  Hash unchanged. Continue...")
                 continue
            log.info(f"  ***Hash changed!***")
            update_sql = ('UPDATE website set hash = ? WHERE selector = ? AND url = ?')
            cur.execute(update_sql, [new_hash, row['selector'], row['url']])
        except Exception as e:
            print("Error: %s" % e, file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            continue
    conn.commit()
except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

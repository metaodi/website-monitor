#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update website hash

Usage:
  update_hash.py --db <path-to-db-file> --old <old-hash> --new <new-hash> [--verbose]
  update_hash.py (-h | --help)
  update_hash.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -d, --db <path-to-db-file>    Path to the SQLite DB.
  -n, --new <new-hash>          New hash of the watched selector.
  -o, --old <old-hash>          Old hash of the watched selector.
  --verbose                     Option to enable more verbose output.
"""


import os
import sys
import time
import logging
import sqlite3
import traceback
from docopt import docopt
from dotenv import load_dotenv, find_dotenv


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
    
    new_hash = arguments['--new']
    old_hash = arguments['--old']

    cur = conn.cursor()
    try:
        update_sql = ('UPDATE website set hash = ?, error_count = 0 WHERE hash = ?')
        cur.execute(update_sql, [new_hash, old_hash])
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.commit()
except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

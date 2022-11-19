#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check websites for changes

Usage:
  build_matrix.py --db <path-to-db-file>
  build_matrix.py (-h | --help)
  build_matrix.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -d, --db <path-to-db-file>    URL of the website to monitor.
"""


import os
import sys
import time
import sqlite3
import traceback
import json
import urllib
import requests
from docopt import docopt


arguments = docopt(__doc__, version='Create JSON for dynamic build matrix 1.0')

conn = None
try:
    conn = sqlite3.connect(arguments['--db'])
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.execute("SELECT * FROM website where active = 'yes'")
    rows = cur.fetchall()
    config = [dict(r) for r in rows]
    matrix = {'include': config}
    print(json.dumps(matrix))

except Exception as e:
    print("Error: %s" % e, file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    sys.exit(1)

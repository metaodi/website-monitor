# -*- coding: utf-8 -*-
"""Monitor changes on a website

Usage:
  monitor.py --url <url-of-website> [--selector <css-selector>] [--wait <seconds>] [--verbose] [--no-verify]
  monitor.py (-h | --help)
  monitor.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -u, --url <url-of-website>    URL of the website to monitor.
  -s, --selector <css-selector> CSS selector to check for changes [default: body].
  -w, --wait <seconds>          Number of seconds to wait until the URL is checked again [default: 30].
  --verbose                     Option to enable more verbose output.
  --no-verify                   Option to disable SSL verification for requests.
"""


import time
import logging
from docopt import docopt
import urllib3
from lib import website_hash as wh


arguments = docopt(__doc__, version="Monitor changes on a website 1.0")

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

url = arguments["--url"]
selector = arguments["--selector"]
verify = not arguments["--no-verify"]

if not verify:
    urllib3.disable_warnings()


wait = int(arguments["--wait"])
old_hash = ""
while True:
    new_hash = wh.get_website_hash(url, selector, verify)
    log.info(f"Hash: {new_hash}")
    if old_hash != new_hash:
        log.info("Hash changed!")
    old_hash = new_hash
    log.debug(f"Wait for {wait} seconds...")
    time.sleep(wait)

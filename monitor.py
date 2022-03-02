# -*- coding: utf-8 -*-
"""Monitor changes on a website

Usage:
  monitor.py --url <url-of-website> [--selector <css-selector>] [--wait <number-of-seconds>] [--verbose] [--no-verify]
  monitor.py (-h | --help)
  monitor.py --version

Options:
  -h, --help                     Show this screen.
  --version                      Show version.
  -u, --url <url-of-website>     URL of the website to monitor.
  -s, --selector <css-selector>  CSS selector to check for changes [default: body].
  -w, --wait <number-of-seconds> Number of seconds to wait until the URL is checked again [default: 30].
  --verbose                      Option to enable more verbose output.
  --no-verify                    Option to disable SSL verification for requests.
"""


import hashlib
import time
import logging
from win10toast import ToastNotifier
from bs4 import BeautifulSoup
from docopt import docopt
import download as dl

arguments = docopt(__doc__, version='Monitor changes on a website 1.0')

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

url = arguments['--url']
selector = arguments['--selector']
verify = not arguments['--no-verify']

if not verify:
    import urllib3
    urllib3.disable_warnings()
    
wait = int(arguments['--wait'])
old_hash = ''
while True:
    content = dl.download_content(url, verify=verify)
    soup = BeautifulSoup(content, 'html.parser')
    as_list = soup.select_one(selector)
    log.debug(as_list.prettify())
    new_hash = hashlib.sha256(str(as_list).encode('utf-8')).hexdigest()
    log.info(f"Hash: {new_hash}")
    if old_hash != new_hash:
        log.info(f"Hash changed!")
        toast = ToastNotifier()
        toast.show_toast("Website changed", "Content of css selector changed", duration=20)
    old_hash = new_hash
    time.sleep(wait)






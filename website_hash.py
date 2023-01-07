#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hash of a website selector

Usage:
  website_hash.py --url <url-of-website> [--selector <css-selector>] [--type <type>] [--verbose] [--no-verify]
  website_hash.py (-h | --help)
  website_hash.py --version

Options:
  -h, --help                    Show this screen.
  --version                     Show version.
  -u, --url <url-of-website>    URL of the website to monitor.
  -s, --selector <css-selector> CSS selector to check for changes [default: body].
  -t, --type <type>             Type of website, one [default: static].
  --verbose                     Option to enable more verbose output.
  --no-verify                   Option to disable SSL verification for requests.
"""


import hashlib
import time
import logging
from bs4 import BeautifulSoup
from docopt import docopt
import download as dl

log = logging.getLogger(__name__)

def get_website_hash(url, selector, verify, dl_type='static'):
    if dl_type == 'static':
        content = dl.download_content(url, verify=verify)
    elif dl_type == 'dynamic':
        content = dl.download_with_selenium(url, selector)
    else:
        raise Exception(f"Invalid type: {dl_type}")
    soup = BeautifulSoup(content, 'html.parser')
    as_list = soup.select(selector)
    if as_list:
        log.debug([i.prettify() for i in as_list])
    source_list = [i.prettify() for i in as_list or []]
    source_list.sort()
    source_text = " ".join(source_list)
    new_hash = hashlib.sha256(source_text.encode('utf-8')).hexdigest()
    return new_hash


if __name__ == "__main__":
    arguments = docopt(__doc__, version='Get hash of website 1.0')

    loglevel = logging.INFO
    if arguments['--verbose']:
        loglevel = logging.DEBUG

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=loglevel,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.captureWarnings(True)


    url = arguments['--url']
    selector = arguments['--selector']
    dl_type = arguments['--type']
    verify = not arguments['--no-verify']

    if not verify:
        import urllib3
        urllib3.disable_warnings()

    new_hash = get_website_hash(url, selector, verify, dl_type)
    log.info(f"Hash: {new_hash}")
    print(new_hash)
    

